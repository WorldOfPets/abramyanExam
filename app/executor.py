"""Run student code in an isolated helper process."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.grading import compare_output

RUNNER_NAME = "exam-runner"


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int

    @property
    def error_kind(self) -> str | None:
        if self.timed_out:
            return "timeout"
        if self.returncode == 0:
            return None
        if self.returncode == 65:
            return "not_allowed_or_syntax"
        if self.returncode == 67:
            return "output_limit"
        return "runtime"


@dataclass(frozen=True)
class TestOutcome:
    passed: int
    total: int
    error_kind: str | None
    duration_ms: int
    first_failure: dict[str, object] | None = None
    failed_tests: tuple[int, ...] = ()
    error_message: str | None = None

    @property
    def solved(self) -> bool:
        return self.passed == self.total


def _brief(text: str, limit: int = 320) -> str:
    cleaned = (text or "").replace("\r\n", "\n").strip("\n")
    if len(cleaned) > limit:
        return cleaned[:limit] + "\n…"
    return cleaned


def _error_line(stderr: str) -> str | None:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    if not lines:
        return None
    return _brief(lines[-1], 180)


def _failure(
    number: int,
    reason: str,
    case: dict[str, str],
    actual: str,
    message: str | None = None,
) -> dict[str, object]:
    return {
        "number": number,
        "reason": reason,
        "input": _brief(case["input"]),
        "expected": _brief(case["output"]),
        "actual": _brief(actual),
        "message": message,
    }


def runner_command() -> list[str]:
    override = os.environ.get("EXAM_RUNNER", "").strip()
    if override:
        return [override]
    if getattr(sys, "frozen", False):
        bundle = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        runner = bundle / RUNNER_NAME
        if not runner.exists():
            raise RuntimeError("exam-runner helper is missing from the bundle")
        try:
            runner.chmod(0o755)
        except OSError:
            pass
        return [str(runner)]
    return [sys.executable, "-I", str(Path(__file__).with_name("sandbox_runner.py"))]


def _minimal_env(workdir: Path) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": str(workdir),
        "TMPDIR": str(workdir),
        "TMP": str(workdir),
        "TEMP": str(workdir),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if os.name == "nt":
        for key in ("SYSTEMROOT", "WINDIR", "COMSPEC"):
            if key in os.environ:
                env[key] = os.environ[key]
    return env


def _kill(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except OSError:
        try:
            process.kill()
        except OSError:
            pass


def execute_code(
    code: str,
    input_data: str,
    settings: Settings,
    timeout: float | None = None,
) -> ExecutionResult:
    timeout = settings.run_timeout_seconds if timeout is None else timeout
    command = runner_command()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="exam-run-") as tmp:
        workdir = Path(tmp)
        code_path = workdir / "solution.py"
        input_path = workdir / "input.txt"
        code_path.write_text(code, encoding="utf-8")
        input_path.write_text(input_data, encoding="utf-8")
        kwargs: dict[str, object] = {}
        if os.name == "posix":
            kwargs["start_new_session"] = True
        elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        process = subprocess.Popen(
            [*command, str(code_path), str(input_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workdir,
            env=_minimal_env(workdir),
            **kwargs,
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill(process)
            stdout, stderr = process.communicate()
        duration_ms = int((time.monotonic() - started) * 1000)
    return ExecutionResult(
        returncode=process.returncode,
        stdout=stdout.decode("utf-8", errors="replace")[: settings.max_output_chars],
        stderr=stderr.decode("utf-8", errors="replace")[: settings.max_output_chars],
        timed_out=timed_out,
        duration_ms=duration_ms,
    )


def run_tests(
    code: str,
    tests: Iterable[dict[str, str]],
    settings: Settings,
) -> TestOutcome:
    cases = list(tests)
    total = len(cases)
    passed = 0
    error_kind: str | None = None
    error_message: str | None = None
    first_failure: dict[str, object] | None = None
    failed_tests: list[int] = []
    started = time.monotonic()
    for index, case in enumerate(cases, start=1):
        elapsed = time.monotonic() - started
        remaining_budget = settings.run_budget_seconds - elapsed
        if remaining_budget <= 0.05:
            error_kind = "timeout"
            error_message = "Исчерпан общий лимит времени на запуск."
            failed_tests.extend(range(index, total + 1))
            if first_failure is None:
                first_failure = _failure(index, "timeout", case, "", error_message)
            break
        result = execute_code(
            code,
            case["input"],
            settings,
            timeout=min(settings.run_timeout_seconds, remaining_budget),
        )
        if result.timed_out:
            error_kind = "timeout"
            error_message = "Превышено время выполнения одного теста."
            failed_tests.extend(range(index, total + 1))
            first_failure = first_failure or _failure(
                index, "timeout", case, result.stdout, error_message
            )
            break
        if result.returncode != 0:
            error_kind = result.error_kind
            error_message = _error_line(result.stderr)
            failed_tests.extend(range(index, total + 1))
            first_failure = first_failure or _failure(
                index, "error", case, result.stdout, error_message
            )
            break
        if compare_output(case["output"], result.stdout):
            passed += 1
        else:
            error_kind = error_kind or "wrong_answer"
            failed_tests.append(index)
            first_failure = first_failure or _failure(
                index, "wrong_answer", case, result.stdout
            )
    duration_ms = int((time.monotonic() - started) * 1000)
    return TestOutcome(
        passed=passed,
        total=total,
        error_kind=error_kind,
        duration_ms=duration_ms,
        first_failure=first_failure,
        failed_tests=tuple(failed_tests),
        error_message=error_message,
    )


def find_runner() -> Path | None:
    """Expose the resolved helper path for diagnostics and tests."""
    parts = runner_command()
    if len(parts) == 1:
        return Path(parts[0])
    return Path(parts[-1])
