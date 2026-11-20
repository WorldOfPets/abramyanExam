from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.executor import execute_code, run_tests
from app.tasks import tasks_by_id


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        teacher_token="test",
        run_timeout_seconds=1,
        run_budget_seconds=3,
        open_browser=False,
    )


def test_correct_solution_passes_all_tests(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    code = "l = int(input())\nprint(l // 100)\n"
    outcome = run_tests(code, task.tests, settings)
    assert outcome.passed == outcome.total
    assert outcome.solved


def test_wrong_solution_fails(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    outcome = run_tests("print(1)\n", task.tests, settings)
    assert outcome.passed < outcome.total
    assert outcome.error_kind == "wrong_answer"


def test_infinite_loop_times_out(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    outcome = run_tests("while True:\n    pass\n", task.tests, settings)
    assert outcome.passed == 0
    assert outcome.error_kind == "timeout"


def test_forbidden_import_is_blocked(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    outcome = run_tests("import os\nprint(os.getcwd())\n", task.tests, settings)
    assert outcome.passed == 0
    assert outcome.error_kind == "not_allowed_or_syntax"


def test_prompts_do_not_pollute_output(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    code = "l = int(input('Введите L: '))\nprint('Ответ:', l // 100)\n"
    outcome = run_tests(code, task.tests, settings)
    assert outcome.passed == 0  # "Ответ:" is an extra token, and that is intentional.
    good = "l = int(input('Введите L: '))\nprint(l // 100)\n"
    assert run_tests(good, task.tests, settings).solved


def test_math_import_is_allowed(settings: Settings) -> None:
    task = tasks_by_id()["proc-03"]
    code = (
        "import math\n"
        "a = float(input()); b = float(input()); c = float(input()); d = float(input())\n"
        "for x, y in ((a, b), (a, c), (a, d)):\n"
        "    print((x + y) / 2)\n"
        "    print(math.sqrt(x * y))\n"
    )
    assert run_tests(code, task.tests, settings).solved


def test_output_limit(settings: Settings) -> None:
    task = tasks_by_id()["integer-01"]
    code = "print('x' * 200000)\n"
    outcome = run_tests(code, task.tests, settings)
    assert outcome.passed == 0
    assert outcome.error_kind == "output_limit"


def test_empty_stdin_is_eof(settings: Settings) -> None:
    result = execute_code("print(input())", "", settings)
    assert result.returncode != 0
