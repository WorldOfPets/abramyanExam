from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.tasks import BLOCK_ORDER, all_tasks, tasks_by_block

BUILDER = Path(__file__).resolve().parents[1] / "app" / "content" / "build_tests.py"


@pytest.fixture(scope="module")
def builder():
    spec = importlib.util.spec_from_file_location("task_builder", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("build_integer", "build_if", "build_for", "build_proc", "build_series"):
        getattr(module, name)()
    return module


def test_catalogue_has_20_tasks_in_each_block() -> None:
    assert len(all_tasks()) == 100
    for block in BLOCK_ORDER:
        tasks = tasks_by_block()[block]
        assert len(tasks) == 20, block
        assert [task.number for task in tasks] == list(range(1, 21)), block


def test_every_task_has_statement_sample_and_hidden_tests() -> None:
    for task in all_tasks():
        assert task.title
        assert len(task.statement) > 20, task.id
        assert task.input_format and task.output_format
        assert task.sample_input and task.sample_output
        assert len(task.tests) >= 6, task.id
        for case in task.tests:
            assert case["input"] is not None
            assert case["output"] != "", task.id


def test_hidden_tests_are_unique_per_task() -> None:
    for task in all_tasks():
        inputs = [case["input"] for case in task.tests]
        assert len(inputs) == len(set(inputs)), task.id


def test_reference_solutions_reproduce_stored_expected_outputs(builder) -> None:
    specs = {spec["id"]: spec for spec in builder.SPECS}
    assert set(specs) == {task.id for task in all_tasks()}
    for task in all_tasks():
        spec = specs[task.id]
        for case in task.tests:
            produced = spec["ref"](case["input"]).strip("\n")
            assert produced == case["output"], (task.id, case["input"])
        sample = spec["ref"](task.sample_input).strip("\n")
        assert sample == task.sample_output, task.id


@pytest.mark.parametrize("block", BLOCK_ORDER)
def test_block_metadata(block: str) -> None:
    tasks = tasks_by_block()[block]
    assert all(task.block == block for task in tasks)
    assert all(task.code for task in tasks)
    assert all(task.total_tests >= 6 for task in tasks)
