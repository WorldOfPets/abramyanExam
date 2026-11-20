"""SQLite persistence for exam sessions, attempts and proctoring events."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.tasks import Task

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL,
    student_name TEXT NOT NULL,
    started_at REAL NOT NULL,
    deadline REAL NOT NULL,
    finished_at REAL,
    status TEXT NOT NULL DEFAULT 'active',
    finish_reason TEXT,
    ban_reason TEXT,
    banned_at REAL,
    last_seen REAL NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    total_tasks INTEGER NOT NULL DEFAULT 5,
    client_ip TEXT,
    tab_id TEXT
);

CREATE TABLE IF NOT EXISTS session_tasks (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    block TEXT NOT NULL,
    position INTEGER NOT NULL,
    code TEXT NOT NULL DEFAULT '',
    attempts_used INTEGER NOT NULL DEFAULT 0,
    best_passed INTEGER NOT NULL DEFAULT 0,
    total_tests INTEGER NOT NULL,
    solved INTEGER NOT NULL DEFAULT 0,
    updated_at REAL NOT NULL,
    PRIMARY KEY (session_id, task_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    total INTEGER NOT NULL,
    error_kind TEXT,
    duration_ms INTEGER NOT NULL,
    created_at REAL NOT NULL,
    code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    detail TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status, last_seen);
CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
"""


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def now() -> float:
    return time.time()


class Repository:
    """Small synchronous repository.

    A process-local lock serialises writes; the app runs as a single worker so
    this is enough to keep attempt counters and state transitions consistent.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=15000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self._connection() as connection:
            connection.executescript(SCHEMA)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
            }
            if "tab_id" not in columns:
                connection.execute("ALTER TABLE sessions ADD COLUMN tab_id TEXT")

    # ------------------------------------------------------------------ sessions
    def create_session(
        self,
        student_name: str,
        tasks: Iterable[Task],
        started_at: float,
        deadline: float,
        client_ip: str | None,
    ) -> tuple[str, str]:
        session_id = secrets.token_hex(12)
        token = secrets.token_urlsafe(32)
        task_list = list(tasks)
        with self._lock, self._connection() as connection:
            connection.execute(
                "INSERT INTO sessions (id, token_hash, student_name, started_at, deadline, "
                "last_seen, total_tasks, client_ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    hash_token(token),
                    student_name,
                    started_at,
                    deadline,
                    started_at,
                    len(task_list),
                    client_ip,
                ),
            )
            for position, task in enumerate(task_list):
                connection.execute(
                    "INSERT INTO session_tasks (session_id, task_id, block, position, "
                    "total_tests, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (session_id, task.id, task.block, position, task.total_tests, started_at),
                )
            connection.execute(
                "INSERT INTO events (session_id, kind, detail, created_at) VALUES (?, ?, ?, ?)",
                (session_id, "started", None, started_at),
            )
        return session_id, token

    def get_session(self, session_id: str) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()

    def authenticate(self, session_id: str, token: str) -> sqlite3.Row | None:
        row = self.get_session(session_id)
        if row is None:
            return None
        if not secrets.compare_digest(row["token_hash"], hash_token(token)):
            return None
        return row

    def get_session_tasks(self, session_id: str) -> list[sqlite3.Row]:
        with self._connection() as connection:
            return list(
                connection.execute(
                    "SELECT * FROM session_tasks WHERE session_id = ? ORDER BY position",
                    (session_id,),
                )
            )

    def get_session_task(self, session_id: str, task_id: str) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute(
                "SELECT * FROM session_tasks WHERE session_id = ? AND task_id = ?",
                (session_id, task_id),
            ).fetchone()

    def touch(self, session_id: str, at: float | None = None) -> None:
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE sessions SET last_seen = ? WHERE id = ? AND status = 'active'",
                (at, session_id),
            )

    def bind_tab(
        self, session_id: str, tab_id: str, at: float | None = None
    ) -> str:
        """Bind a session to the first browser tab that talks to it.

        A second tab with a different random ID is an attempt to run the same
        exam twice; the caller turns ``duplicate_tab`` into a ban.
        """
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session = connection.execute(
                "SELECT status, tab_id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if session is None:
                connection.rollback()
                return "not_found"
            if session["status"] != "active":
                connection.rollback()
                return str(session["status"])
            current = session["tab_id"]
            if current is None:
                connection.execute(
                    "UPDATE sessions SET tab_id = ?, last_seen = ? WHERE id = ?",
                    (tab_id, at, session_id),
                )
                connection.commit()
                return "ok"
            if not secrets.compare_digest(str(current), tab_id):
                connection.rollback()
                return "duplicate_tab"
            connection.execute(
                "UPDATE sessions SET last_seen = ? WHERE id = ?", (at, session_id)
            )
            connection.commit()
            return "ok"

    def save_code(self, session_id: str, task_id: str, code: str, at: float | None = None) -> None:
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE session_tasks SET code = ?, updated_at = ? "
                "WHERE session_id = ? AND task_id = ?",
                (code, at, session_id, task_id),
            )
            connection.execute(
                "UPDATE sessions SET last_seen = ? WHERE id = ? AND status = 'active'",
                (at, session_id),
            )

    def add_event(self, session_id: str, kind: str, detail: str | None = None) -> None:
        with self._lock, self._connection() as connection:
            connection.execute(
                "INSERT INTO events (session_id, kind, detail, created_at) VALUES (?, ?, ?, ?)",
                (session_id, kind, detail, now()),
            )

    # ------------------------------------------------------------------ attempts
    def consume_attempt(
        self,
        session_id: str,
        task_id: str,
        at: float,
        max_attempts: int,
    ) -> tuple[int | None, str | None]:
        """Reserve one attempt.

        Returns ``(attempt_number, error)``. The attempt is consumed even if the
        submitted program later crashes or times out.
        """
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session = connection.execute(
                "SELECT status, deadline FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if session is None:
                connection.rollback()
                return None, "not_found"
            if session["status"] != "active":
                connection.rollback()
                return None, "not_active"
            if session["deadline"] <= at:
                connection.rollback()
                return None, "timeout"
            task = connection.execute(
                "SELECT attempts_used, solved FROM session_tasks "
                "WHERE session_id = ? AND task_id = ?",
                (session_id, task_id),
            ).fetchone()
            if task is None:
                connection.rollback()
                return None, "task_not_found"
            if task["solved"]:
                connection.rollback()
                return None, "solved"
            if task["attempts_used"] >= max_attempts:
                connection.rollback()
                return None, "attempts_exhausted"
            attempt = int(task["attempts_used"]) + 1
            connection.execute(
                "UPDATE session_tasks SET attempts_used = ?, updated_at = ? "
                "WHERE session_id = ? AND task_id = ?",
                (attempt, at, session_id, task_id),
            )
            connection.execute(
                "UPDATE sessions SET last_seen = ? WHERE id = ?", (at, session_id)
            )
            connection.commit()
            return attempt, None

    def record_result(
        self,
        session_id: str,
        task_id: str,
        attempt: int,
        passed: int,
        total: int,
        error_kind: str | None,
        duration_ms: int,
        code: str,
        at: float | None = None,
    ) -> None:
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO runs (session_id, task_id, attempt, passed, total, error_kind, "
                "duration_ms, created_at, code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, task_id, attempt, passed, total, error_kind, duration_ms, at, code),
            )
            connection.execute(
                "UPDATE session_tasks SET best_passed = MAX(best_passed, ?), "
                "solved = CASE WHEN ? = total_tests THEN 1 ELSE solved END, "
                "code = ?, updated_at = ? WHERE session_id = ? AND task_id = ?",
                (passed, passed, code, at, session_id, task_id),
            )
            connection.execute(
                "UPDATE sessions SET score = "
                "(SELECT COUNT(*) FROM session_tasks WHERE session_id = ? AND solved = 1) "
                "WHERE id = ?",
                (session_id, session_id),
            )
            connection.commit()

    def finish_session(self, session_id: str, reason: str, at: float | None = None) -> None:
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE sessions SET status = 'finished', finished_at = ?, finish_reason = ?, "
                "score = (SELECT COUNT(*) FROM session_tasks WHERE session_id = ? AND solved = 1) "
                "WHERE id = ? AND status = 'active'",
                (at, reason, session_id, session_id),
            )

    def ban_session(self, session_id: str, reason: str, at: float | None = None) -> None:
        at = now() if at is None else at
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE sessions SET status = 'banned', banned_at = ?, ban_reason = ?, "
                "finished_at = ?, finish_reason = 'banned', "
                "score = (SELECT COUNT(*) FROM session_tasks WHERE session_id = ? AND solved = 1) "
                "WHERE id = ? AND status = 'active'",
                (at, reason, at, session_id, session_id),
            )
            connection.execute(
                "INSERT INTO events (session_id, kind, detail, created_at) VALUES (?, ?, ?, ?)",
                (session_id, "banned", reason, at),
            )

    # ------------------------------------------------------------------ sweep/results
    def sweep(self, at: float, grace_seconds: float) -> None:
        with self._lock, self._connection() as connection:
            expired = list(
                connection.execute(
                    "SELECT id FROM sessions WHERE status = 'active' AND deadline <= ?", (at,)
                )
            )
            stale = list(
                connection.execute(
                    "SELECT id FROM sessions WHERE status = 'active' AND last_seen < ?",
                    (at - grace_seconds,),
                )
            )
        for row in expired:
            self.finish_session(row["id"], "timeout", at)
        for row in stale:
            if row["id"] in {item["id"] for item in expired}:
                continue
            self.ban_session(row["id"], "browser_closed", at)

    def list_sessions(self, limit: int = 500) -> list[sqlite3.Row]:
        with self._connection() as connection:
            return list(
                connection.execute(
                    "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
                )
            )

    def session_tasks_for_many(self, session_ids: list[str]) -> dict[str, list[sqlite3.Row]]:
        if not session_ids:
            return {}
        placeholders = ",".join("?" for _ in session_ids)
        with self._connection() as connection:
            rows = list(
                connection.execute(
                    f"SELECT * FROM session_tasks WHERE session_id IN ({placeholders}) "
                    "ORDER BY session_id, position",
                    session_ids,
                )
            )
        result: dict[str, list[sqlite3.Row]] = {session_id: [] for session_id in session_ids}
        for row in rows:
            result[row["session_id"]].append(row)
        return result

    def count_runs(self, session_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS n FROM runs WHERE session_id = ?", (session_id,)
            ).fetchone()
            return int(row["n"]) if row else 0


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row}
