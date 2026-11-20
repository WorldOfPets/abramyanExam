"""Exam session orchestration and template view models."""

from __future__ import annotations

import random
import secrets
from typing import Any

from app.config import Settings
from app.db import Repository
from app.tasks import BLOCK_ORDER, Task, tasks_by_block, tasks_by_id

BLOCK_ICONS = {
    "integer": "01",
    "if": "02",
    "for": "03",
    "proc": "04",
    "series": "05",
}


def choose_tasks(rng: random.Random | None = None) -> list[Task]:
    """Pick exactly one random task from each of the five blocks."""
    randomizer = rng or secrets.SystemRandom()
    selected: list[Task] = []
    for block in BLOCK_ORDER:
        selected.append(randomizer.choice(tasks_by_block()[block]))
    return selected


def start_exam(
    repository: Repository,
    settings: Settings,
    student_name: str,
    client_ip: str | None,
    at: float,
) -> tuple[str, str]:
    tasks = choose_tasks()
    return repository.create_session(
        student_name=student_name.strip(),
        tasks=tasks,
        started_at=at,
        deadline=at + settings.exam_seconds,
        client_ip=client_ip,
    )


def public_task(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "code": task.code,
        "block": task.block,
        "block_title": task.block_title,
        "number": task.number,
        "title": task.title,
        "statement": task.statement,
        "input_format": task.input_format,
        "output_format": task.output_format,
        "sample_input": task.sample_input,
        "sample_output": task.sample_output,
        "total_tests": task.total_tests,
    }


def build_exam_view(
    session: dict[str, Any] | Any,
    session_tasks: list[Any],
    settings: Settings,
    at: float,
) -> dict[str, Any]:
    catalogue = tasks_by_id()
    tasks = []
    for row in session_tasks:
        task = catalogue[row["task_id"]]
        tasks.append(
            {
                **public_task(task),
                "position": row["position"],
                "attempts_used": row["attempts_used"],
                "attempts_left": max(0, settings.attempts_per_task - row["attempts_used"]),
                "best_passed": row["best_passed"],
                "solved": bool(row["solved"]),
                "saved_code": row["code"],
                "icon": BLOCK_ICONS.get(task.block, "•"),
            }
        )
    remaining = max(0, int(session["deadline"] - at))
    return {
        "session": dict(session),
        "tasks": tasks,
        "remaining_seconds": remaining,
        "attempts_per_task": settings.attempts_per_task,
        "exam_seconds": int(settings.exam_seconds),
        "solved_count": sum(1 for task in tasks if task["solved"]),
    }


def build_result_view(
    session: dict[str, Any] | Any,
    session_tasks: list[Any],
) -> dict[str, Any]:
    catalogue = tasks_by_id()
    rows = []
    for row in session_tasks:
        task = catalogue[row["task_id"]]
        rows.append(
            {
                "task": public_task(task),
                "attempts_used": row["attempts_used"],
                "best_passed": row["best_passed"],
                "total_tests": row["total_tests"],
                "solved": bool(row["solved"]),
                "code": row["code"],
            }
        )
    return {
        "session": dict(session),
        "rows": rows,
        "solved_count": sum(1 for row in rows if row["solved"]),
        "total": len(rows),
    }
