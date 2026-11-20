from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.db import Repository
from app.exam import build_exam_view, choose_tasks, start_exam
from app.grading import compare_output
from app.tasks import BLOCK_ORDER


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path, teacher_token="test-token")


@pytest.fixture
def repo(settings: Settings) -> Repository:
    return Repository(settings.db_path)


def test_choose_tasks_one_per_block() -> None:
    tasks = choose_tasks()
    assert len(tasks) == 5
    assert {task.block for task in tasks} == set(BLOCK_ORDER)


def test_session_authentication_and_view(repo: Repository, settings: Settings) -> None:
    session_id, token = start_exam(repo, settings, "  Анна  ", "127.0.0.1", at=1000.0)
    session = repo.authenticate(session_id, token)
    assert session is not None
    assert session["student_name"] == "Анна"
    assert session["status"] == "active"
    assert repo.authenticate(session_id, "wrong") is None

    tasks = repo.get_session_tasks(session_id)
    assert len(tasks) == 5
    view = build_exam_view(session, tasks, settings, at=1010.0)
    assert view["remaining_seconds"] == 30 * 60 - 10
    assert all(task["attempts_left"] == 10 for task in view["tasks"])
    assert all("tests" not in task for task in view["tasks"])


def test_attempts_and_scoring(repo: Repository, settings: Settings) -> None:
    session_id, _ = start_exam(repo, settings, "Иван", None, at=1000.0)
    task_id = repo.get_session_tasks(session_id)[0]["task_id"]

    attempt, error = repo.consume_attempt(session_id, task_id, 1001.0, 10)
    assert (attempt, error) == (1, None)
    repo.record_result(
        session_id,
        task_id,
        attempt=attempt or 0,
        passed=3,
        total=8,
        error_kind="wrong_answer",
        duration_ms=120,
        code="print(1)",
        at=1001.5,
    )
    row = repo.get_session_task(session_id, task_id)
    assert row is not None
    assert row["attempts_used"] == 1
    assert row["best_passed"] == 3
    assert row["solved"] == 0
    assert repo.get_session(session_id)["score"] == 0

    attempt, error = repo.consume_attempt(session_id, task_id, 1002.0, 10)
    repo.record_result(
        session_id,
        task_id,
        attempt=attempt or 0,
        passed=8,
        total=8,
        error_kind=None,
        duration_ms=120,
        code="print(2)",
        at=1002.5,
    )
    assert repo.get_session_task(session_id, task_id)["solved"] == 1
    assert repo.get_session(session_id)["score"] == 1

    attempt, error = repo.consume_attempt(session_id, task_id, 1003.0, 10)
    assert attempt is None
    assert error == "solved"


def test_attempt_limit(repo: Repository, settings: Settings) -> None:
    session_id, _ = start_exam(repo, settings, "Пётр", None, at=1000.0)
    task_id = repo.get_session_tasks(session_id)[0]["task_id"]
    for _ in range(3):
        attempt, error = repo.consume_attempt(session_id, task_id, 1001.0, 3)
        assert error is None
        assert attempt is not None
    attempt, error = repo.consume_attempt(session_id, task_id, 1001.0, 3)
    assert attempt is None
    assert error == "attempts_exhausted"


def test_finish_and_ban(repo: Repository, settings: Settings) -> None:
    session_id, _ = start_exam(repo, settings, "Ольга", None, at=1000.0)
    repo.finish_session(session_id, "submitted", at=1100.0)
    session = repo.get_session(session_id)
    assert session["status"] == "finished"
    assert session["finish_reason"] == "submitted"

    other_id, _ = start_exam(repo, settings, "Сергей", None, at=1000.0)
    repo.ban_session(other_id, "tab_switch", at=1010.0)
    other = repo.get_session(other_id)
    assert other["status"] == "banned"
    assert other["ban_reason"] == "tab_switch"


def test_sweep_expires_and_bans(repo: Repository, settings: Settings) -> None:
    expired_id, _ = start_exam(repo, settings, "A", None, at=1000.0)
    repo.sweep(at=2900.0, grace_seconds=35.0)
    assert repo.get_session(expired_id)["status"] == "finished"
    assert repo.get_session(expired_id)["finish_reason"] == "timeout"

    stale_id, _ = start_exam(repo, settings, "B", None, at=3000.0)
    repo.touch(stale_id, at=3500.0)
    repo.sweep(at=3600.0, grace_seconds=35.0)
    assert repo.get_session(stale_id)["status"] == "banned"
    assert repo.get_session(stale_id)["ban_reason"] == "browser_closed"


def test_output_comparison() -> None:
    assert compare_output("1 2 3", "1\n2 3\n")
    assert compare_output("1.0 2.5", "1 2.500000")
    assert compare_output("True", "True")
    assert not compare_output("True", "False")
    assert not compare_output("1 2", "1 2 3")
    assert not compare_output("1.0", "1.1")
    assert not compare_output("1", "1\nподсказка")
