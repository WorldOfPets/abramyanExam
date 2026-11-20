(() => {
  "use strict";

  const configNode = document.getElementById("exam-config");
  if (!configNode) return;
  const cfg = JSON.parse(configNode.textContent);

  const state = {
    finished: false,
    navigating: false,
    banSent: false,
    deadline: Date.now() + cfg.remainingSeconds * 1000,
    current: null,
    solved: {},
    attempts: {},
    totals: {},
    saveTimers: new Map(),
    saveChains: new Map(),
  };

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
    const editor = document.querySelector(`[data-code="${taskId}"]`);
    if (editor) editor.focus({ preventScroll: true });
  }

  function codeFor(taskId) {
    const editor = document.querySelector(`[data-code="${taskId}"]`);
    return editor ? editor.value : "";
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
    if (state.finished || state.solved[taskId] || state.attempts[taskId] <= 0) return;
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

      const lines = [];
      lines.push(`Пройдено ${data.passed} из ${data.total} тестов.`);
      if (data.error_kind && ERROR_TEXT[data.error_kind]) {
        lines.push(ERROR_TEXT[data.error_kind]);
      }
      if (state.attempts[taskId] <= 0) {
        lines.push("Попытки запуска закончились.");
      }
      writeResult(taskId, lines.join(" "), data.error_kind ? "bad" : "warn");
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
    if (state.finished) return;
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
  window.addEventListener("pagehide", handlePageHide);
  window.addEventListener("focus", syncState);

  state.current = cfg.tasks[0] ? cfg.tasks[0].id : null;
  if (state.current) activateTask(state.current);
  tick();
  setInterval(tick, 250);
  syncState();
  setInterval(syncState, 5000);
})();
