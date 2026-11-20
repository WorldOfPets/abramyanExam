"""Task catalogue loaded from the generated JSON file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.paths import resource_path

BLOCK_ORDER = ("integer", "if", "for", "proc", "series")
BLOCK_TITLES = {
    "integer": "Целые числа",
    "if": "Условный оператор",
    "for": "Цикл с параметром",
    "proc": "Процедуры и функции",
    "series": "Последовательности",
}


@dataclass(frozen=True)
class Task:
    id: str
    block: str
    block_title: str
    number: int
    code: str
    title: str
    statement: str
    input_format: str
    output_format: str
    sample_input: str
    sample_output: str
    tests: tuple[dict[str, str], ...]

    @property
    def total_tests(self) -> int:
        return len(self.tests)


@lru_cache(maxsize=1)
def all_tasks() -> tuple[Task, ...]:
    path = resource_path("app", "content", "tasks.json")
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    tasks = tuple(
        Task(
            id=item["id"],
            block=item["block"],
            block_title=item["block_title"],
            number=item["number"],
            code=item["code"],
            title=item["title"],
            statement=item["statement"],
            input_format=item["input_format"],
            output_format=item["output_format"],
            sample_input=item["sample_input"],
            sample_output=item["sample_output"],
            tests=tuple(item["tests"]),
        )
        for item in raw
    )
    return tasks


@lru_cache(maxsize=1)
def tasks_by_id() -> dict[str, Task]:
    return {task.id: task for task in all_tasks()}


@lru_cache(maxsize=1)
def tasks_by_block() -> dict[str, tuple[Task, ...]]:
    return {
        block: tuple(task for task in all_tasks() if task.block == block)
        for block in BLOCK_ORDER
    }
