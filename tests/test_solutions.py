from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.executor import run_tests
from app.tasks import tasks_by_id

SOLUTIONS = {
    "integer-10": """
n = int(input())
print(n % 10)
print((n // 10) % 10)
""",
    "if-02": """
n = int(input())
print(n + 1 if n > 0 else n - 2)
""",
    "for-18": """
a = float(input())
n = int(input())
total = 0.0
sign = 1
power = 1.0
for _ in range(n + 1):
    total += sign * power
    sign = -sign
    power *= a
print(total)
""",
    "proc-14": """
for _ in range(2):
    a = float(input())
    b = float(input())
    c = float(input())
    print(c, a, b)
""",
    "series-06": """
n = int(input())
values = list(map(float, input().split()))
parts = [x - int(x) for x in values]
product = 1.0
for x in parts:
    product *= x
print(*parts)
print(product)
""",
}


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        teacher_token="test",
        run_timeout_seconds=1,
        run_budget_seconds=4,
        open_browser=False,
    )


@pytest.mark.parametrize("task_id,code", SOLUTIONS.items())
def test_reference_style_solutions_pass_hidden_tests(
    task_id: str, code: str, settings: Settings
) -> None:
    task = tasks_by_id()[task_id]
    outcome = run_tests(code, task.tests, settings)
    assert outcome.solved, (task_id, outcome)
