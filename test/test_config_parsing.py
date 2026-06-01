"""Tests for config parsing."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
from pytest_fixture_classes import fixture_class

A_PY_PATTERN = re.compile(r"a\.py:(.*)")


def _run_pylint(test_folder: str, datadir: Path) -> str:
    cwd = datadir / test_folder

    for source_file in (datadir / "source_files").iterdir():
        shutil.copy(source_file, cwd / source_file.name)

    result = subprocess.run(
        ["pylint", "-f", "json2", "a.py", "b.py"],
        text=True,
        capture_output=True,
        cwd=cwd,
        check=False,
    )
    return result.stderr or result.stdout


@fixture_class(name="runner")
class Runner:
    datadir: Path

    def __call__(self, test_folder: str) -> dict[str, Any]:
        result = _run_pylint(test_folder, self.datadir)
        return cast(dict[str, Any], json.loads(result))


@fixture_class(name="error_runner")
class ErrorRunner:
    datadir: Path

    def __call__(self, test_folder: str, error_message: str) -> None:
        result = _run_pylint(test_folder, self.datadir)
        assert error_message in result


def _get_symbols(result: dict[str, Any], module: str) -> list[str]:
    return sorted(
        message["symbol"]
        for message in result["messages"]
        if message["module"] == module
    )


def test_without_per_file_ignores(runner: Runner) -> None:
    """Verify that without per-file-ignores all violations are reported."""
    result = runner("test_without_per_file_ignores")

    assert _get_symbols(result, "a") == [
        "invalid-name",
        "missing-module-docstring",
        "unused-import",
    ]
    assert _get_symbols(result, "b") == ["invalid-name", "missing-module-docstring"]


def test_config_pyproject_toml(runner: Runner) -> None:
    """Test per-file-ignores config parsed from pyproject.toml."""
    result = runner("test_config_pyproject_toml")

    assert _get_symbols(result, "a") == ["invalid-name"]
    assert _get_symbols(result, "b") == ["missing-module-docstring"]


@pytest.mark.parametrize("trailing_comma", [True, False])
def test_config_pylintrc(runner: Runner, *, trailing_comma: bool) -> None:
    """Test per-file-ignores config parsed from .pylintrc."""
    cwd = runner.datadir / "test_config_pylintrc"
    if trailing_comma:
        pylintrc = cwd / ".pylintrc"
        content = pylintrc.read_text()
        content = A_PY_PATTERN.sub(r"a.py:\1,", content)
        pylintrc.write_text(content)

    result = runner("test_config_pylintrc")

    assert _get_symbols(result, "a") == ["invalid-name"]
    assert _get_symbols(result, "b") == ["missing-module-docstring"]


@pytest.mark.parametrize("trailing_comma", [True, False])
def test_config_pylintrc_multiline(runner: Runner, *, trailing_comma: bool) -> None:
    """Test per-file-ignores config parsed from .pylintrc with multiline settings."""
    cwd = runner.datadir / "test_config_pylintrc_multiline"
    if trailing_comma:
        pylintrc = cwd / ".pylintrc"
        content = pylintrc.read_text()
        content = content.replace("unused-import", "unused-import,")
        pylintrc.write_text(content)

    result = runner("test_config_pylintrc_multiline")

    assert _get_symbols(result, "a") == ["invalid-name"]
    assert _get_symbols(result, "b") == ["missing-module-docstring"]


def test_config_pylintrc_empty_rules(error_runner: ErrorRunner) -> None:
    """Test per-file-ignores config parsed from .pylintrc with empty rules."""
    error_runner(
        "test_config_pylintrc_empty_rules",
        error_message="No rules specified for file pattern",
    )


def test_config_pylintrc_duplicate_pattern(error_runner: ErrorRunner) -> None:
    """Test per-file-ignores config parsed from .pylintrc with duplicate patterns."""
    error_runner(
        "test_config_pylintrc_duplicate_pattern",
        error_message="Duplicate file pattern a.py",
    )


def test_config_setup_cfg(runner: Runner) -> None:
    """Test per-file-ignores config parsed from setup.cfg."""
    result = runner("test_config_setup_cfg")

    assert _get_symbols(result, "a") == ["invalid-name"]
    assert _get_symbols(result, "b") == ["missing-module-docstring"]
