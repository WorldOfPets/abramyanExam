"""FastAPI routes and application factory."""

from __future__ import annotations

import asyncio
import csv
import io
import secrets
import threading
import time
import webbrowser
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import Settings
from app.db import Repository
from app.exam import build_exam_view, build_result_view, start_exam
from app.executor import run_tests
from app.paths import resource_path
from app.tasks import tasks_by_id

COOKIE_NAME = "abramyan_exam"
TEMPLATE_DIR = resource_path("app", "templates")
STATIC_DIR = resource_path("app", "static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


class CodePayload(BaseModel):
    task_id: str = Field(min_length=1, max_length=40)
    code: str = Field(default="", max_length=100_000)


class ViolationPayload(BaseModel):
    reason: str = Field(default="tab_switch", max_length=40)


STATUS_LABELS = {
    "active": "Идёт экзамен",
    "finished": "Завершён",
    "banned": "Забанен",
}
REASON_LABELS = {
    "tab_switch": "переключение вкладки",
    "page_closed": "закрытие или уход со страницы",
    "browser_closed": "потеря связи с браузером",
    "heartbeat_lost": "потеря связи с браузером",
}


def _public_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::"} else host


def _format_ts(value: float | None) -> str:
    if not value:
        return "—"
    return datetime.fromtimestamp(value).strftime("%d.%m.%Y %H:%M:%S")


def _csv_safe(value: object) -> object:
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return value


templates.env.filters["ts"] = _format_ts
templates.env.globals["status_labels"] = STATUS_LABELS
templates.env.globals["reason_labels"] = REASON_LABELS


def _set_session_cookie(response: Response, session_id: str, token: str, settings: Settings) -> None:
    response.set_cookie(
        COOKIE_NAME,
        f"{session_id}.{token}",
        max_age=int(settings.exam_seconds) + 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )


def _session_from_cookie(request: Request, session_id: str) -> dict[str, Any] | None:
    raw = request.cookies.get(COOKIE_NAME, "")
    if "." not in raw:
        return None
    cookie_id, token = raw.split(".", 1)
    if cookie_id != session_id:
        return None
    repo: Repository = request.app.state.repo
    row = repo.authenticate(session_id, token)
    return dict(row) if row is not None else None


def _require_session(request: Request, session_id: str) -> dict[str, Any]:
    session = _session_from_cookie(request, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой попытке")
    return session


def _require_teacher(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    token = request.query_params.get("token") or request.headers.get("x-teacher-token", "")
    if not secrets.compare_digest(token, settings.teacher_token):
        raise HTTPException(status_code=404, detail="Not found")
    return settings


def _json_state(repo: Repository, session: dict[str, Any], settings: Settings) -> dict[str, Any]:
    session_tasks = repo.get_session_tasks(session["id"])
    remaining = max(0, int(session["deadline"] - time.time()))
    return {
        "status": session["status"],
        "remaining_seconds": remaining,
        "score": session["score"],
        "total": session["total_tasks"],
        "tasks": [
            {
                "id": row["task_id"],
                "attempts_used": row["attempts_used"],
                "attempts_left": max(0, settings.attempts_per_task - row["attempts_used"]),
                "best_passed": row["best_passed"],
                "solved": bool(row["solved"]),
            }
            for row in session_tasks
        ],
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    repo = Repository(settings.db_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        stop = asyncio.Event()

        async def sweeper() -> None:
            while not stop.is_set():
                try:
                    await asyncio.to_thread(
                        repo.sweep, time.time(), settings.heartbeat_grace_seconds
                    )
                except Exception:  # noqa: BLE001, S110 - keep the sweep loop alive
                    pass
                try:
                    await asyncio.wait_for(stop.wait(), timeout=2.0)
                except TimeoutError:
                    pass

        task = asyncio.create_task(sweeper())
        public_host = _public_host(settings.host)
        print(f"Экзамен:          http://{public_host}:{settings.port}/")
        print(f"Преподаватель:    http://{public_host}:{settings.port}/teacher?token={settings.teacher_token}")
        print(f"Данные:           {settings.data_dir}")
        try:
            yield
        finally:
            stop.set()
            await task

    application = FastAPI(
        title="Экзамен по задачнику Абрамяна",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.repo = repo
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @application.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if not request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        return response

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> Response:
        raw = request.cookies.get(COOKIE_NAME, "")
        if "." in raw:
            cookie_id, _ = raw.split(".", 1)
            session = _session_from_cookie(request, cookie_id)
            if session and session["status"] == "active" and session["deadline"] > time.time():
                return RedirectResponse(f"/exam/{cookie_id}", status_code=303)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "title": "Экзамен по программированию",
                "error": request.query_params.get("error"),
                "blocks": [
                    ("Integer", "целые числа и деление нацело"),
                    ("If", "условный оператор"),
                    ("For", "цикл с параметром"),
                    ("Proc", "процедуры и функции"),
                    ("Series", "последовательности"),
                ],
            },
        )

    @application.post("/start")
    async def start(request: Request) -> Response:
        form = await request.form()
        student_name = str(form.get("name", "")).strip()
        consent = form.get("consent")
        if not (1 <= len(student_name) <= 100):
            return RedirectResponse("/?error=name", status_code=303)
        if not consent:
            return RedirectResponse("/?error=consent", status_code=303)
        client_ip = request.client.host if request.client else None
        session_id, token = start_exam(
            repo, settings, student_name, client_ip, at=time.time()
        )
        response = RedirectResponse(f"/exam/{session_id}", status_code=303)
        _set_session_cookie(response, session_id, token, settings)
        return response

    @application.get("/exam/{session_id}", response_class=HTMLResponse)
    async def exam_page(request: Request, session_id: str) -> Response:
        session = _require_session(request, session_id)
        if session["status"] == "banned":
            return RedirectResponse(f"/banned/{session_id}", status_code=303)
        if session["status"] != "active":
            return RedirectResponse(f"/result/{session_id}", status_code=303)
        if session["deadline"] <= time.time():
            repo.finish_session(session_id, "timeout")
            return RedirectResponse(f"/result/{session_id}", status_code=303)
        session_tasks = repo.get_session_tasks(session_id)
        view = build_exam_view(session, session_tasks, settings, at=time.time())
        config = {
            "sessionId": session_id,
            "remainingSeconds": view["remaining_seconds"],
            "attemptsPerTask": settings.attempts_per_task,
            "maxCodeChars": settings.max_code_chars,
            "stateUrl": f"/api/exam/{session_id}/state",
            "saveUrl": f"/api/exam/{session_id}/save",
            "runUrl": f"/api/exam/{session_id}/run",
            "finishUrl": f"/api/exam/{session_id}/finish",
            "violationUrl": f"/api/exam/{session_id}/violation",
            "resultUrl": f"/result/{session_id}",
            "bannedUrl": f"/banned/{session_id}",
            "studentName": session["student_name"],
            "totalTasks": session["total_tasks"],
            "tasks": [
                {
                    "id": task["id"],
                    "solved": task["solved"],
                    "attemptsLeft": task["attempts_left"],
                    "totalTests": task["total_tests"],
                }
                for task in view["tasks"]
            ],
        }
        return templates.TemplateResponse(
            request,
            "exam.html",
            {
                "title": "Экзамен",
                "view": view,
                "config": config,
                "student_name": session["student_name"],
            },
        )

    @application.get("/api/exam/{session_id}/state")
    async def exam_state(request: Request, session_id: str) -> JSONResponse:
        session = _require_session(request, session_id)
        if session["status"] == "active" and session["deadline"] <= time.time():
            repo.finish_session(session_id, "timeout")
            session = dict(repo.get_session(session_id))  # type: ignore[arg-type]
        elif session["status"] == "active":
            repo.touch(session_id)
        return JSONResponse(_json_state(repo, session, settings))

    @application.post("/api/exam/{session_id}/save")
    async def save_code(request: Request, session_id: str, payload: CodePayload) -> JSONResponse:
        session = _require_session(request, session_id)
        if session["status"] != "active":
            return JSONResponse({"error": "not_active", "status": session["status"]}, status_code=409)
        if session["deadline"] <= time.time():
            repo.finish_session(session_id, "timeout")
            return JSONResponse({"error": "timeout", "status": "finished"}, status_code=409)
        task_row = repo.get_session_task(session_id, payload.task_id)
        if task_row is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        code = payload.code
        if len(code) > settings.max_code_chars:
            return JSONResponse(
                {"error": "code_too_long", "limit": settings.max_code_chars}, status_code=413
            )
        repo.save_code(session_id, payload.task_id, code)
        return JSONResponse({"ok": True, "saved_at": time.time()})

    @application.post("/api/exam/{session_id}/run")
    def run_code(request: Request, session_id: str, payload: CodePayload) -> JSONResponse:
        session = _require_session(request, session_id)
        if session["status"] != "active":
            return JSONResponse({"error": "not_active", "status": session["status"]}, status_code=409)
        if session["deadline"] <= time.time():
            repo.finish_session(session_id, "timeout")
            return JSONResponse({"error": "timeout", "status": "finished"}, status_code=409)
        task_row = repo.get_session_task(session_id, payload.task_id)
        if task_row is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        code = payload.code
        if not code.strip():
            return JSONResponse({"error": "empty_code"}, status_code=400)
        if len(code) > settings.max_code_chars:
            return JSONResponse(
                {"error": "code_too_long", "limit": settings.max_code_chars}, status_code=413
            )
        task = tasks_by_id()[payload.task_id]
        attempt, error = repo.consume_attempt(
            session_id, payload.task_id, time.time(), settings.attempts_per_task
        )
        if error is not None:
            if error == "timeout":
                repo.finish_session(session_id, "timeout")
            return JSONResponse(
                {"error": error, "attempts_left": 0 if error == "attempts_exhausted" else None},
                status_code=429 if error == "attempts_exhausted" else 409,
            )
        assert attempt is not None
        repo.save_code(session_id, payload.task_id, code)
        outcome = run_tests(code, task.tests, settings)
        repo.record_result(
            session_id,
            payload.task_id,
            attempt=attempt,
            passed=outcome.passed,
            total=outcome.total,
            error_kind=outcome.error_kind,
            duration_ms=outcome.duration_ms,
            code=code,
        )
        task_row = repo.get_session_task(session_id, payload.task_id)
        session = repo.get_session(session_id)
        return JSONResponse(
            {
                "passed": outcome.passed,
                "total": outcome.total,
                "solved": outcome.solved,
                "attempts_left": max(0, settings.attempts_per_task - int(task_row["attempts_used"])),
                "attempts_used": int(task_row["attempts_used"]),
                "error_kind": outcome.error_kind,
                "duration_ms": outcome.duration_ms,
                "score": int(session["score"]) if session else 0,
                "status": session["status"] if session else "active",
            }
        )

    @application.post("/api/exam/{session_id}/finish")
    async def finish(request: Request, session_id: str) -> JSONResponse:
        session = _require_session(request, session_id)
        if session["status"] == "active":
            reason = "timeout" if session["deadline"] <= time.time() else "submitted"
            repo.finish_session(session_id, reason)
            session = dict(repo.get_session(session_id))  # type: ignore[arg-type]
        return JSONResponse(
            {
                "status": session["status"],
                "score": session["score"],
                "redirect": f"/result/{session_id}" if session["status"] != "banned" else f"/banned/{session_id}",
            }
        )

    @application.post("/api/exam/{session_id}/violation")
    async def violation(request: Request, session_id: str) -> Response:
        session = _require_session(request, session_id)
        if session["status"] != "active":
            return Response(status_code=204)
        reason = "tab_switch"
        try:
            raw = await request.body()
            if raw:
                payload = ViolationPayload.model_validate_json(raw)
                reason = payload.reason
        except (ValueError, TypeError):
            reason = "tab_switch"
        if reason not in {"tab_switch", "page_closed", "browser_closed", "heartbeat_lost"}:
            reason = "tab_switch"
        repo.ban_session(session_id, reason)
        return Response(status_code=204)

    @application.get("/result/{session_id}", response_class=HTMLResponse)
    async def result_page(request: Request, session_id: str) -> Response:
        session = _require_session(request, session_id)
        if session["status"] == "banned":
            return RedirectResponse(f"/banned/{session_id}", status_code=303)
        if session["status"] == "active":
            return RedirectResponse(f"/exam/{session_id}", status_code=303)
        view = build_result_view(session, repo.get_session_tasks(session_id))
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "title": "Результат",
                "view": view,
                "student_name": session["student_name"],
                "finish_reason": session["finish_reason"],
                "attempts_per_task": settings.attempts_per_task,
            },
        )

    @application.get("/banned/{session_id}", response_class=HTMLResponse)
    async def banned_page(request: Request, session_id: str) -> Response:
        session = _require_session(request, session_id)
        if session["status"] != "banned":
            return RedirectResponse(
                f"/result/{session_id}" if session["status"] == "finished" else f"/exam/{session_id}",
                status_code=303,
            )
        return templates.TemplateResponse(
            request,
            "banned.html",
            {
                "title": "Экзамен аннулирован",
                "session": session,
                "student_name": session["student_name"],
                "reason": REASON_LABELS.get(session["ban_reason"], session["ban_reason"]),
            },
        )

    @application.get("/teacher", response_class=HTMLResponse)
    async def teacher(request: Request) -> Response:
        _require_teacher(request)
        sessions = repo.list_sessions()
        mapping = repo.session_tasks_for_many([row["id"] for row in sessions])
        catalogue = tasks_by_id()
        rows = []
        for session in sessions:
            task_rows = []
            for item in mapping[session["id"]]:
                task = catalogue[item["task_id"]]
                task_rows.append(
                    {
                        "code": task.code,
                        "title": task.title,
                        "attempts_used": item["attempts_used"],
                        "best_passed": item["best_passed"],
                        "total_tests": item["total_tests"],
                        "solved": bool(item["solved"]),
                    }
                )
            rows.append(
                {
                    "session": dict(session),
                    "tasks": task_rows,
                    "status_label": STATUS_LABELS.get(session["status"], session["status"]),
                    "reason": REASON_LABELS.get(session["ban_reason"], session["ban_reason"] or "—"),
                }
            )
        return templates.TemplateResponse(
            request,
            "teacher.html",
            {
                "title": "Результаты экзамена",
                "rows": rows,
                "total": len(rows),
                "token": request.query_params.get("token", ""),
            },
        )

    @application.get("/teacher/export.csv")
    async def export_csv(request: Request) -> StreamingResponse:
        _require_teacher(request)
        sessions = repo.list_sessions()
        mapping = repo.session_tasks_for_many([row["id"] for row in sessions])
        catalogue = tasks_by_id()
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(
            [
                "id",
                "student",
                "started_at",
                "finished_at",
                "status",
                "score",
                "reason",
                "task_1",
                "passed_1",
                "task_2",
                "passed_2",
                "task_3",
                "passed_3",
                "task_4",
                "passed_4",
                "task_5",
                "passed_5",
            ]
        )
        for session in sessions:
            row = [
                session["id"],
                _csv_safe(session["student_name"]),
                _format_ts(session["started_at"]),
                _format_ts(session["finished_at"]),
                STATUS_LABELS.get(session["status"], session["status"]),
                session["score"],
                REASON_LABELS.get(session["ban_reason"], session["ban_reason"] or ""),
            ]
            for item in mapping[session["id"]]:
                row.extend([catalogue[item["task_id"]].code, f"{item['best_passed']}/{item['total_tests']}"])
            writer.writerow(row)
        data = "\ufeff" + buffer.getvalue()
        headers = {"Content-Disposition": "attachment; filename=exam-results.csv"}
        return StreamingResponse(iter([data]), media_type="text/csv; charset=utf-8", headers=headers)

    return application


app = create_app()


def run() -> None:
    settings: Settings = app.state.settings
    url = f"http://{_public_host(settings.host)}:{settings.port}/"
    if settings.open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        loop="asyncio",
        http="h11",
        ws="none",
    )


if __name__ == "__main__":
    run()
