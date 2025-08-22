"""Tests for pylint_per_file_ignores/_plugin.py."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pytest_fixture_classes import fixture_class


@fixture_class(name="runner")
class Runner:
    datadir: Path

    def __call__(self, test_folder: str, *args: str) -> dict[str, Any]:
        """Run pylint with the given arguments."""
        result = subprocess.run(
            ["pylint", *args, "-f", "json2"],
            text=True,
            capture_output=True,
            cwd=self.datadir / test_folder,
            check=False,
        )
        return json.loads(result.stdout)


def _find_errors(result: dict[str, Any], name: str) -> list[str]:
    return [
        message["symbol"] for message in result["messages"] if name == message["module"]
    ]


def test_no_config(runner: Runner) -> None:
    result = runner("test_no_config", "my_code.py")
    assert len(result["messages"]) == 2


def test_with_pyproject_toml(runner: Runner) -> None:
    result = runner("test_with_pyproject_toml", "a", "b")

    assert _find_errors(result, "a.some_a") == ["import-error"]
    assert _find_errors(result, "b.some_b") == ["missing-module-docstring"]


def test_with_multi_job(runner: Runner) -> None:
    result = runner("test_multi_job", "tests", "project")

    assert _find_errors(result, "tests.test_main") == ["missing-module-docstring"]


def test_with_rcfile(runner: Runner) -> None:
    result = runner("test_with_rcfile", "a", "b")

    assert _find_errors(result, "a.some_a") == ["import-error"]
    assert _find_errors(result, "b.some_b") == ["missing-module-docstring"]
