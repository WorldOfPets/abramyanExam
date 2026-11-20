(() => {
  "use strict";

  const configNode = document.getElementById("exam-config");
  if (!configNode) return;
  const cfg = JSON.parse(configNode.textContent);

  const state = {
    finished: false,
    navigating: false,
    banSent: false,
    fullscreenArmed: false,
    focusArmedAt: 0,
    deadline: Date.now() + cfg.remainingSeconds * 1000,
    current: null,
    solved: {},
    attempts: {},
    totals: {},
    saveTimers: new Map(),
    saveChains: new Map(),
  };

  const editors = new Map();
  const PY_HINTS = [
    "input", "print", "int", "float", "str", "len", "range", "list", "map",
    "sum", "min", "max", "abs", "round", "pow", "divmod", "sorted", "enumerate",
    "zip", "math", "sqrt", "pi", "if", "elif", "else", "for", "while", "def",
    "return", "True", "False", "None", "and", "or", "not", "in", "is", "break",
    "continue", "try", "except", "pass", "import", "from",
  ];

  for (const task of cfg.tasks) {
    state.solved[task.id] = Boolean(task.solved);
    state.attempts[task.id] = Number(task.attemptsLeft);
    state.totals[task.id] = Number(task.totalTests);
  }

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const timerEl = $("#timer");
  const timerStat = $("#timer-stat");
  const solvedCounter = $("#solved-counter");
  const finishModal = $("#finish-modal");
  const fullscreenGate = $("#fullscreen-gate");
  const fullscreenButton = $("#enter-fullscreen");
  const fullscreenError = $("#fullscreen-error");

  const ERROR_TEXT = {
    timeout: "Превышено время выполнения.",
    output_limit: "Слишком большой вывод программы.",
    not_allowed_or_syntax: "Синтаксическая ошибка или запрещённая конструкция.",
    runtime: "Ошибка выполнения программы.",
    wrong_answer: "Ответ не совпал с ожидаемым.",
  };

  function formatTime(seconds) {
    const safe = Math.max(0, Math.floor(seconds));
    const minutes = Math.floor(safe / 60);
    const rest = safe % 60;
    return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  }

  function tick() {
    if (state.finished || state.navigating) return;
    const remaining = (state.deadline - Date.now()) / 1000;
    timerEl.textContent = formatTime(remaining);
    timerStat.classList.toggle("warning", remaining <= 300);
    if (remaining <= 0) expire();
  }

  function updateAttempts(taskId) {
    const left = state.attempts[taskId];
    const badge = document.querySelector(`[data-attempts="${taskId}"] b`);
    if (badge) badge.textContent = String(left);
    updateRunButton(taskId);
  }

  function updateRunButton(taskId) {
    const button = document.querySelector(`[data-run="${taskId}"]`);
    if (!button) return;
    if (state.solved[taskId]) {
      button.disabled = true;
      button.textContent = "Задача решена";
      return;
    }
    if (state.attempts[taskId] <= 0) {
      button.disabled = true;
      button.textContent = "Попытки закончились";
      return;
    }
    button.disabled = false;
    button.textContent = "Запустить код";
  }

  function setSolved(taskId, solved) {
    state.solved[taskId] = solved;
    const panel = document.querySelector(`[data-task-panel="${taskId}"]`);
    if (panel) panel.dataset.solved = solved ? "1" : "0";
    const dot = document.querySelector(`[data-task-state="${taskId}"]`);
    if (dot) dot.classList.toggle("solved", solved);
    const count = Object.values(state.solved).filter(Boolean).length;
    solvedCounter.textContent = `${count} / ${cfg.totalTasks}`;
    updateRunButton(taskId);
  }

  function showAllSolved() {
    if (document.querySelector(".all-solved")) return;
    const currentPanel = document.querySelector(`[data-task-panel="${state.current}"] [data-result="${state.current}"]`);
    if (!currentPanel) return;
    const line = document.createElement("div");
    line.className = "result-line ok all-solved";
    line.textContent = "Все пять задач решены. Можно завершать экзамен.";
    currentPanel.appendChild(line);
  }

  function writeResult(taskId, text, kind) {
    const box = document.querySelector(`[data-result="${taskId}"]`);
    if (!box) return;
    box.textContent = "";
    const line = document.createElement("div");
    line.className = `result-line ${kind || ""}`.trim();
    line.textContent = text;
    box.appendChild(line);
  }

  function addFailureField(parent, label, value, className = "") {
    const field = document.createElement("div");
    field.className = `failure-field ${className}`.trim();
    const title = document.createElement("span");
    title.textContent = label;
    const pre = document.createElement("pre");
    pre.textContent = value === "" || value === null || value === undefined ? "(пусто)" : String(value);
    field.append(title, pre);
    parent.appendChild(field);
  }

  function renderRunResult(taskId, data) {
    const box = document.querySelector(`[data-result="${taskId}"]`);
    if (!box) return;
    box.textContent = "";

    const summary = document.createElement("div");
    summary.className = `result-line ${data.error_kind ? "bad" : "warn"}`;
    summary.textContent = `Пройдено ${data.passed} из ${data.total} тестов.`;
    box.appendChild(summary);

    const errorText = data.error_message
      || (data.error_kind && data.error_kind !== "wrong_answer"
        ? ERROR_TEXT[data.error_kind]
        : null);
    if (errorText) {
      const message = document.createElement("div");
      message.className = "result-line bad";
      message.textContent = `Ошибка: ${errorText}`;
      box.appendChild(message);
    }

    if (Array.isArray(data.failed_tests) && data.failed_tests.length) {
      const failed = document.createElement("div");
      failed.className = "result-line warn";
      failed.textContent = `Провалены тесты: ${data.failed_tests.join(", ")}.`;
      box.appendChild(failed);
    }

    const failure = data.first_failure;
    if (failure) {
      const reasons = {
        wrong_answer: "неверный ответ",
        timeout: "превышено время",
        error: "ошибка выполнения",
      };
      const details = document.createElement("details");
      details.className = "failure-details";
      details.open = true;
      const caption = document.createElement("summary");
      caption.textContent = `Тест ${failure.number}: ${reasons[failure.reason] || "провал"}`;
      const body = document.createElement("div");
      body.className = "failure-body";
      addFailureField(body, "Ввод", failure.input);
      addFailureField(body, "Ожидалось", failure.expected, "expected");
      addFailureField(body, "Получено", failure.actual, "actual");
      const note = document.createElement("p");
      note.className = "failure-note";
      note.textContent = "Показан только первый проваленный тест. Остальные тесты остаются скрытыми.";
      body.appendChild(note);
      details.append(caption, body);
      box.appendChild(details);
    }

    if (Number(data.attempts_left) <= 0 && !data.solved) {
      const empty = document.createElement("div");
      empty.className = "result-line bad";
      empty.textContent = "Попытки запуска закончились.";
      box.appendChild(empty);
    }
  }

  function activateTask(taskId) {
    if (state.current && state.current !== taskId) {
      queueSave(state.current, true);
    }
    state.current = taskId;
    $$("[data-task-tab]").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.taskTab === taskId);
    });
    $$("[data-task-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.taskPanel === taskId);
    });
    focusEditor(taskId);
  }

  function codeFor(taskId) {
    const editor = editors.get(taskId);
    if (editor) return editor.getValue();
    const textarea = document.querySelector(`[data-code="${taskId}"]`);
    return textarea ? textarea.value : "";
  }

  function focusEditor(taskId) {
    if (!state.fullscreenArmed) return;
    const editor = editors.get(taskId);
    if (editor) {
      requestAnimationFrame(() => {
        editor.refresh();
        editor.focus();
      });
      return;
    }
    const textarea = document.querySelector(`[data-code="${taskId}"]`);
    if (textarea) textarea.focus({ preventScroll: true });
  }

  function updateCursor(taskId, editor) {
    const label = document.querySelector(`[data-cursor="${taskId}"]`);
    if (!label) return;
    const cursor = editor.getCursor();
    label.textContent = `${cursor.line + 1}:${cursor.ch + 1}`;
  }

  function pythonHint(editor) {
    const cursor = editor.getCursor();
    const before = editor.getLine(cursor.line).slice(0, cursor.ch);
    const match = before.match(/[A-Za-z_]\w*$/);
    if (!match) return null;
    const word = match[0];
    const list = PY_HINTS.filter((hint) =>
      hint.toLowerCase().startsWith(word.toLowerCase())
    );
    if (!list.length) return null;
    return {
      list,
      from: { line: cursor.line, ch: cursor.ch - word.length },
      to: cursor,
    };
  }

  function showHints(taskId) {
    const editor = editors.get(taskId);
    if (!editor) return;
    editor.focus();
    editor.showHint({ hint: pythonHint, completeSingle: false });
  }

  function setupEditors() {
    if (!window.CodeMirror) return;
    $$("[data-code]").forEach((textarea) => {
      const taskId = textarea.dataset.code;
      const editor = window.CodeMirror.fromTextArea(textarea, {
        mode: "python",
        theme: "exam-dark",
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        smartIndent: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        styleActiveLine: true,
        lineWrapping: false,
        scrollbarStyle: "native",
        viewportMargin: 20,
        extraKeys: {
          Tab: (cm) => {
            if (cm.somethingSelected()) cm.indentSelection("add");
            else cm.replaceSelection("    ", "end");
          },
          "Shift-Tab": (cm) => cm.indentSelection("subtract"),
          "Ctrl-Enter": () => runTask(taskId),
          "Cmd-Enter": () => runTask(taskId),
          "Ctrl-Space": (cm) => cm.showHint({ hint: pythonHint, completeSingle: false }),
          "Ctrl-/": "toggleComment",
          "Cmd-/": "toggleComment",
          "Ctrl-F": "find",
          "Cmd-F": "find",
          "Ctrl-G": "findNext",
          "Shift-Ctrl-G": "findPrev",
        },
      });
      editor.on("change", () => queueSave(taskId));
      editor.on("cursorActivity", () => updateCursor(taskId, editor));
      const input = editor.getInputField();
      if (input) input.setAttribute("aria-label", `Код решения ${taskId}`);
      editors.set(taskId, editor);
      updateCursor(taskId, editor);
    });
    requestAnimationFrame(() => editors.forEach((editor) => editor.refresh()));
  }

  function setSaveStatus(taskId, text, saving = false) {
    const el = document.querySelector(`[data-save-status="${taskId}"]`);
    if (!el) return;
    el.textContent = text;
    el.classList.toggle("saving", saving);
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data = {};
    try {
      data = await response.json();
    } catch (_) {}
    return { response, data };
  }

  async function saveCode(taskId) {
    if (state.finished) return;
    const code = codeFor(taskId);
    if (code.length > cfg.maxCodeChars) {
      setSaveStatus(taskId, "слишком длинный код");
      return;
    }
    setSaveStatus(taskId, "сохранение…", true);
    try {
      const { response, data } = await postJson(cfg.saveUrl, { task_id: taskId, code });
      if (response.status === 403) return redirectToBanned();
      if (!response.ok) {
        if (data.status === "banned") return redirectToBanned();
        if (data.status === "finished") return redirectToResult();
        setSaveStatus(taskId, "не сохранено");
        return;
      }
      setSaveStatus(taskId, "сохранено");
    } catch (_) {
      setSaveStatus(taskId, "нет связи");
    }
  }

  function queueSave(taskId, immediate = false) {
    const existing = state.saveTimers.get(taskId);
    if (existing) clearTimeout(existing);
    if (immediate) {
      state.saveTimers.delete(taskId);
      saveCode(taskId);
      return;
    }
    const timer = setTimeout(() => {
      state.saveTimers.delete(taskId);
      saveCode(taskId);
    }, 700);
    state.saveTimers.set(taskId, timer);
  }

  async function runTask(taskId) {
    if (!state.fullscreenArmed || state.finished || state.solved[taskId] || state.attempts[taskId] <= 0) return;
    const code = codeFor(taskId);
    if (!code.trim()) {
      writeResult(taskId, "Сначала напишите решение.", "warn");
      return;
    }
    if (code.length > cfg.maxCodeChars) {
      writeResult(taskId, `Код длиннее ${cfg.maxCodeChars} символов.`, "warn");
      return;
    }
    const button = document.querySelector(`[data-run="${taskId}"]`);
    if (button) {
      button.disabled = true;
      button.textContent = "Проверяем…";
    }
    writeResult(taskId, "Выполняем скрытые тесты…", "warn");

    try {
      const { response, data } = await postJson(cfg.runUrl, { task_id: taskId, code });
      if (response.status === 403) return redirectToBanned();

      if (data.status === "banned") return redirectToBanned();
      if (data.status === "finished" || data.error === "timeout") {
        state.navigating = true;
        return window.location.replace(cfg.resultUrl);
      }
      if (response.status === 429 && data.error === "attempts_exhausted") {
        state.attempts[taskId] = 0;
        updateAttempts(taskId);
        writeResult(taskId, "Попытки запуска закончились.", "bad");
        return;
      }
      if (!response.ok) {
        writeResult(taskId, "Не удалось выполнить проверку. Попробуйте ещё раз.", "bad");
        return;
      }

      state.attempts[taskId] = Number(data.attempts_left);
      state.totals[taskId] = Number(data.total);
      updateAttempts(taskId);
      if (data.solved) {
        setSolved(taskId, true);
        writeResult(taskId, `Задача решена: ${data.passed} из ${data.total} тестов.`, "ok");
        if (Object.values(state.solved).filter(Boolean).length === cfg.totalTasks) {
          showAllSolved();
        }
        queueSave(taskId, true);
        return;
      }

      renderRunResult(taskId, data);
      queueSave(taskId, true);
    } catch (_) {
      writeResult(taskId, "Нет связи с сервером проверки. Попробуйте ещё раз.", "bad");
    } finally {
      if (!state.solved[taskId]) updateRunButton(taskId);
    }
  }

  function redirectToResult() {
    if (state.navigating) return;
    state.navigating = true;
    window.location.replace(cfg.resultUrl);
  }

  function redirectToBanned() {
    if (state.navigating) return;
    state.navigating = true;
    window.location.replace(cfg.bannedUrl);
  }

  async function syncState() {
    if (state.finished || state.navigating) return;
    try {
      const response = await fetch(cfg.stateUrl, {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (response.status === 403) return redirectToBanned();
      if (!response.ok) return;
      const data = await response.json();
      if (data.status === "banned") return redirectToBanned();
      if (data.status === "finished") return redirectToResult();
      state.deadline = Date.now() + Number(data.remaining_seconds) * 1000;
      for (const task of data.tasks) {
        if (task.solved && !state.solved[task.id]) setSolved(task.id, true);
        state.attempts[task.id] = Number(task.attempts_left);
        updateAttempts(task.id);
      }
      if (Number(data.remaining_seconds) <= 0) expire();
    } catch (_) {
      // The server-side heartbeat monitor handles a lost connection.
    }
  }

  async function finishExam() {
    if (!state.fullscreenArmed || state.finished) return;
    await Promise.all(
      cfg.tasks.map(async (task) => {
        try {
          await postJson(cfg.saveUrl, {
            task_id: task.id,
            code: codeFor(task.id),
          });
        } catch (_) {
          // The last autosave is still a valid fallback.
        }
      })
    );
    state.finished = true;
    state.navigating = true;
    if (finishModal) finishModal.hidden = true;
    try {
      const { data } = await postJson(cfg.finishUrl, {});
      const target = data.redirect || cfg.resultUrl;
      window.location.replace(target);
    } catch (_) {
      window.location.replace(cfg.resultUrl);
    }
  }

  function expire() {
    if (state.finished || state.navigating) return;
    state.finished = true;
    state.navigating = true;
    fetch(cfg.finishUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: "{}",
      keepalive: true,
    }).finally(() => window.location.replace(cfg.resultUrl));
  }

  function sendViolation(reason) {
    if (state.finished || state.navigating || state.banSent) return;
    state.banSent = true;
    const payload = JSON.stringify({ reason });
    try {
      const blob = new Blob([payload], { type: "application/json" });
      navigator.sendBeacon(cfg.violationUrl, blob);
    } catch (_) {}
    fetch(cfg.violationUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true,
    }).catch(() => {});
    setTimeout(() => {
      state.navigating = true;
      window.location.replace(cfg.bannedUrl);
    }, 120);
  }

  function handleVisibility() {
    if (document.visibilityState === "hidden" && !state.finished && !state.navigating) {
      sendViolation("tab_switch");
    }
  }

  function handlePageHide() {
    if (state.finished || state.navigating || state.banSent) return;
    const payload = JSON.stringify({ reason: "page_closed" });
    try {
      navigator.sendBeacon(cfg.violationUrl, new Blob([payload], { type: "application/json" }));
    } catch (_) {}
    // Keep the latest code if the browser still allows a keepalive request.
    if (state.current) {
      try {
        fetch(cfg.saveUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task_id: state.current, code: codeFor(state.current) }),
          keepalive: true,
        }).catch(() => {});
      } catch (_) {}
    }
  }

  // ---------------------------------------------------------------- fullscreen
  function currentFullscreenElement() {
    return document.fullscreenElement || document.webkitFullscreenElement || null;
  }

  function fullscreenRequest() {
    const root = document.documentElement;
    return root.requestFullscreen || root.webkitRequestFullscreen || null;
  }

  function armFullscreen() {
    state.fullscreenArmed = true;
    state.focusArmedAt = Date.now();
    if (fullscreenGate) fullscreenGate.hidden = true;
    if (fullscreenError) fullscreenError.textContent = "";
    document.querySelector(".exam-topbar")?.removeAttribute("inert");
    document.querySelector(".exam-layout")?.removeAttribute("inert");
    focusEditor(state.current);
    lockKeyboard();
  }

  function lockKeyboard() {
    try {
      if (navigator.keyboard && typeof navigator.keyboard.lock === "function") {
        navigator.keyboard.lock().catch(() => {});
      }
    } catch (_) {
      // Keyboard Lock is unavailable on insecure origins; focus-loss ban remains.
    }
  }

  function handleWindowBlur() {
    if (!state.fullscreenArmed || state.finished || state.navigating || state.banSent) return;
    if (Date.now() - state.focusArmedAt < 1200) return;
    sendViolation("focus_lost");
  }

  function checkWindowFocus() {
    if (!state.fullscreenArmed || state.finished || state.navigating || state.banSent) return;
    if (Date.now() - state.focusArmedAt < 1200) return;
    if (!document.hasFocus()) sendViolation("focus_lost");
  }

  const ALLOWED_CTRL_KEYS = new Set([
    "a", "c", "v", "x", "z", "y", "f", "g", "space", "enter",
    "backspace", "delete", "arrowleft", "arrowright", "home", "end", "/", ".",
  ]);

  function isBlockedShortcut(event) {
    const key = event.key;
    const lower = key === " " ? "space" : key.toLowerCase();
    if (/^f\d{1,2}$/i.test(key)) return true;
    if (key === "Meta" || key === "ContextMenu" || lower === "printscreen") return true;

    if (event.altKey && !event.ctrlKey && !event.metaKey) {
      return ["tab", "f4", "space", "enter", "arrowleft", "arrowright"].includes(lower);
    }

    if (event.ctrlKey || event.metaKey) {
      if (event.altKey) return false; // AltGr must keep working for keyboard layouts.
      if (event.shiftKey) {
        return !["z", "g", "arrowleft", "arrowright", "home", "end"].includes(lower);
      }
      return !ALLOWED_CTRL_KEYS.has(lower);
    }
    return false;
  }

  function handleKeyDown(event) {
    if (!isBlockedShortcut(event)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  async function enterFullscreen() {
    const request = fullscreenRequest();
    if (!request || document.fullscreenEnabled === false) {
      if (fullscreenError) {
        fullscreenError.textContent = "Этот браузер не поддерживает полноэкранный режим. Откройте экзамен в актуальном Chrome, Edge или Firefox.";
      }
      return;
    }
    if (fullscreenError) fullscreenError.textContent = "";
    fullscreenButton.disabled = true;
    try {
      const attempt = request.call(document.documentElement);
      await Promise.race([
        attempt && typeof attempt.then === "function" ? attempt : Promise.resolve(),
        new Promise((resolve) => setTimeout(resolve, 1500)),
      ]);
      if (currentFullscreenElement()) {
        armFullscreen();
      } else if (fullscreenError) {
        fullscreenError.textContent = "Не удалось войти в полноэкранный режим. Разрешите его в браузере и нажмите кнопку ещё раз.";
      }
    } catch (_) {
      if (fullscreenError) {
        fullscreenError.textContent = "Браузер не разрешил полноэкранный режим. Разрешите его и нажмите кнопку ещё раз.";
      }
    } finally {
      fullscreenButton.disabled = false;
    }
  }

  function handleFullscreenChange() {
    if (currentFullscreenElement()) {
      armFullscreen();
      return;
    }
    if (!state.fullscreenArmed || state.finished || state.navigating || state.banSent) return;
    sendViolation("fullscreen_exit");
  }

  // ---------------------------------------------------------------- wiring
  $$("[data-task-tab]").forEach((tab) => {
    tab.addEventListener("click", () => activateTask(tab.dataset.taskTab));
  });

  $$("[data-code]").forEach((editor) => {
    const taskId = editor.dataset.code;
    editor.addEventListener("input", () => queueSave(taskId));
    editor.addEventListener("keydown", (event) => {
      if (event.key === "Tab") {
        event.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.setRangeText("    ", start, end, "end");
        queueSave(taskId);
      }
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        runTask(taskId);
      }
    });
  });

  $$("[data-run]").forEach((button) => {
    button.addEventListener("click", () => runTask(button.dataset.run));
  });

  $$("[data-hint]").forEach((button) => {
    button.addEventListener("click", () => showHints(button.dataset.hint));
  });

  const finishButton = $("#finish-button");
  if (finishButton) {
    finishButton.addEventListener("click", () => {
      finishModal.hidden = false;
      $("#confirm-finish").focus();
    });
  }
  $("#cancel-finish").addEventListener("click", () => {
    finishModal.hidden = true;
  });
  $("#confirm-finish").addEventListener("click", finishExam);

  document.addEventListener("visibilitychange", handleVisibility);
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
  document.addEventListener("keydown", handleKeyDown, true);
  document.addEventListener("contextmenu", (event) => event.preventDefault());
  window.addEventListener("blur", handleWindowBlur);
  window.addEventListener("pagehide", handlePageHide);
  window.addEventListener("focus", syncState);
  if (fullscreenButton) fullscreenButton.addEventListener("click", enterFullscreen);
  setInterval(checkWindowFocus, 1000);

  document.querySelector(".exam-topbar")?.setAttribute("inert", "");
  document.querySelector(".exam-layout")?.setAttribute("inert", "");
  setupEditors();
  state.current = cfg.tasks[0] ? cfg.tasks[0].id : null;
  if (state.current) activateTask(state.current);
  if (currentFullscreenElement()) {
    armFullscreen();
  } else if (!fullscreenRequest() || document.fullscreenEnabled === false) {
    if (fullscreenError) {
      fullscreenError.textContent = "Этот браузер не поддерживает полноэкранный режим. Откройте экзамен в актуальном Chrome, Edge или Firefox.";
    }
  }
  tick();
  setInterval(tick, 250);
  syncState();
  setInterval(syncState, 5000);
})();
