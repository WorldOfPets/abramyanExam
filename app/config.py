"""Runtime configuration for the exam application."""

from __future__ import annotations

import os
import secrets
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        candidate = Path(sys.executable).resolve().parent / "exam-data"
    else:
        candidate = Path.cwd() / "exam-data"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate
    except OSError:
        fallback = Path.home() / ".local" / "share" / "abramyan-exam"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _load_teacher_token(data_dir: Path) -> str:
    token = os.environ.get("EXAM_TEACHER_TOKEN", "").strip()
    if token:
        return token
    token_file = data_dir / ".teacher-token"
    if token_file.exists():
        existing = token_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    token = secrets.token_urlsafe(18)
    token_file.write_text(token + "\n", encoding="utf-8")
    try:
        token_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return token


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=_default_data_dir)
    host: str = "127.0.0.1"
    port: int = 8000
    exam_minutes: float = 25.0
    attempts_per_task: int = 10
    run_timeout_seconds: float = 2.0
    run_budget_seconds: float = 8.0
    heartbeat_grace_seconds: float = 35.0
    max_code_chars: int = 20_000
    max_output_chars: int = 65_536
    teacher_token: str = ""
    open_browser: bool = field(default_factory=lambda: _bool_env("EXAM_OPEN_BROWSER", getattr(sys, "frozen", False)))
    log_level: str = "info"

    def __post_init__(self) -> None:
        if not self.teacher_token:
            object.__setattr__(self, "teacher_token", _load_teacher_token(self.data_dir))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "exam.sqlite3"

    @property
    def exam_seconds(self) -> float:
        return self.exam_minutes * 60

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.environ.get("EXAM_DATA_DIR") or _default_data_dir()).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            data_dir=data_dir,
            host=os.environ.get("EXAM_HOST", "127.0.0.1"),
            port=int(os.environ.get("EXAM_PORT", "8000")),
            exam_minutes=float(os.environ.get("EXAM_MINUTES", "25")),
            attempts_per_task=int(os.environ.get("EXAM_ATTEMPTS", "10")),
            run_timeout_seconds=float(os.environ.get("EXAM_RUN_TIMEOUT", "2")),
            run_budget_seconds=float(os.environ.get("EXAM_RUN_BUDGET", "8")),
            heartbeat_grace_seconds=float(os.environ.get("EXAM_HEARTBEAT_GRACE", "35")),
            max_code_chars=int(os.environ.get("EXAM_MAX_CODE_CHARS", "20000")),
            max_output_chars=int(os.environ.get("EXAM_MAX_OUTPUT_CHARS", "65536")),
            teacher_token=_load_teacher_token(data_dir),
            open_browser=_bool_env("EXAM_OPEN_BROWSER", getattr(sys, "frozen", False)),
            log_level=os.environ.get("EXAM_LOG_LEVEL", "info"),
        )
