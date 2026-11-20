from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.exam import start_exam
from app.main import COOKIE_NAME, create_app
from app.tasks import tasks_by_id


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        teacher_token="teacher-token",
        exam_minutes=25,
        attempts_per_task=2,
        run_timeout_seconds=1,
        run_budget_seconds=3,
        open_browser=False,
    )


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def _start(client: TestClient, name: str = "Анна Петрова") -> tuple[str, dict]:
    response = client.post(
        "/start",
        data={"name": name, "consent": "yes"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/exam/")
    page = client.get(location)
    assert page.status_code == 200
    match = re.search(r'id="exam-config">(.*?)</script>', page.text, re.S)
    assert match
    return location.rsplit("/", 1)[-1], json.loads(match.group(1))


def test_index_and_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    page = client.get("/")
    assert page.status_code == 200
    assert "Начать экзамен" in page.text


def test_start_requires_consent(client: TestClient) -> None:
    response = client.post("/start", data={"name": "Анна"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/?error=consent")


def test_exam_page_has_five_tasks_without_hidden_tests(client: TestClient) -> None:
    session_id, config = _start(client)
    assert len(config["tasks"]) == 5
    assert config["remainingSeconds"] > 1400
    page = client.get(f"/exam/{session_id}")
    assert page.status_code == 200
    assert "Скрытые тесты" not in page.text
    assert '"tests"' not in page.text
    first_code = tasks_by_id()[config["tasks"][0]["id"]].code
    assert f"# {first_code}" in page.text


def test_state_and_save(client: TestClient) -> None:
    session_id, config = _start(client)
    task_id = config["tasks"][0]["id"]
    response = client.post(
        f"/api/exam/{session_id}/save",
        json={"task_id": task_id, "code": "n = int(input())\nprint(n)\n"},
    )
    assert response.status_code == 200
    state = client.get(f"/api/exam/{session_id}/state").json()
    assert state["status"] == "active"
    assert state["remaining_seconds"] > 0
    assert len(state["tasks"]) == 5


def test_run_counts_attempts_and_rejects_after_limit(client: TestClient) -> None:
    session_id, config = _start(client)
    task_id = config["tasks"][0]["id"]
    first = client.post(
        f"/api/exam/{session_id}/run",
        json={"task_id": task_id, "code": "print(1)"},
    )
    assert first.status_code == 200
    payload = first.json()
    assert payload["attempts_left"] == 1
    assert payload["total"] >= 6
    second = client.post(
        f"/api/exam/{session_id}/run",
        json={"task_id": task_id, "code": "print(1)"},
    )
    assert second.status_code == 200
    third = client.post(
        f"/api/exam/{session_id}/run",
        json={"task_id": task_id, "code": "print(1)"},
    )
    assert third.status_code == 429
    assert third.json()["error"] == "attempts_exhausted"


def test_correct_run_solves_task(client: TestClient, settings: Settings) -> None:
    app = client.app
    catalogue = tasks_by_id()
    chosen = [catalogue[key] for key in ("integer-01", "if-01", "for-01", "proc-01", "series-01")]
    session_id, token = app.state.repo.create_session(
        "Анна",
        chosen,
        started_at=time.time(),
        deadline=time.time() + 1500,
        client_ip=None,
    )
    client.cookies.set(COOKIE_NAME, f"{session_id}.{token}")
    code = "l = int(input())\nprint(l // 100)\n"
    response = client.post(
        f"/api/exam/{session_id}/run",
        json={"task_id": "integer-01", "code": code},
    )
    assert response.status_code == 200
    assert response.json()["solved"] is True
    assert response.json()["passed"] == 8
    state = client.get(f"/api/exam/{session_id}/state").json()
    assert state["score"] == 1
    again = client.post(
        f"/api/exam/{session_id}/run",
        json={"task_id": "integer-01", "code": code},
    )
    assert again.status_code == 409
    assert again.json()["error"] == "solved"


def test_violation_bans_session(client: TestClient) -> None:
    session_id, _ = _start(client)
    response = client.post(f"/api/exam/{session_id}/violation", json={"reason": "tab_switch"})
    assert response.status_code == 204
    page = client.get(f"/banned/{session_id}")
    assert page.status_code == 200
    assert "дисквалифицирована" in page.text
    state = client.get(f"/api/exam/{session_id}/state").json()
    assert state["status"] == "banned"


def test_finish_and_result(client: TestClient) -> None:
    session_id, _ = _start(client)
    response = client.post(f"/api/exam/{session_id}/finish", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "finished"
    page = client.get(f"/result/{session_id}")
    assert page.status_code == 200
    assert "задач решено" in page.text


def test_cookie_is_required(client: TestClient) -> None:
    session_id, _ = _start(client)
    client.cookies.delete(COOKIE_NAME)
    response = client.get(f"/exam/{session_id}")
    assert response.status_code == 403


def test_teacher_page_and_csv(client: TestClient) -> None:
    _start(client)
    response = client.get("/teacher?token=teacher-token")
    assert response.status_code == 200
    assert "Анна Петрова" in response.text
    csv_response = client.get("/teacher/export.csv?token=teacher-token")
    assert csv_response.status_code == 200
    assert "student" in csv_response.text
    assert "Анна Петрова" in csv_response.text
    assert client.get("/teacher?token=wrong").status_code == 404


def test_timeout_finishes_session(settings: Settings) -> None:
    short = Settings(
        data_dir=settings.data_dir,
        teacher_token=settings.teacher_token,
        exam_minutes=0.001,
        open_browser=False,
    )
    app = create_app(short)
    with TestClient(app) as client:
        session_id, token = start_exam(
            app.state.repo, short, "Анна", None, at=time.time() - 1.0
        )
        client.cookies.set(COOKIE_NAME, f"{session_id}.{token}")
        state = client.get(f"/api/exam/{session_id}/state").json()
        assert state["status"] == "finished"
        page = client.get(f"/result/{session_id}")
        assert page.status_code == 200
        assert "Время вышло" in page.text
