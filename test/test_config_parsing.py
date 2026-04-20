"""Tests for config parsing."""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any, cast

import pytest
from pytest_fixture_classes import fixture_class

A_PY_PATTERN = re.compile(r"a\.py:(.*)")


@fixture_class(name="runner")
class Runner:
    datadir: Path

    def __call__(self, test_folder: str) -> dict[str, Any]:
        """Run pylint on a.py and b.py in the given test folder."""
        cwd = self.datadir / test_folder
        self._copy_source_files(cwd)
        return self._run_pylint(cwd)

    def _copy_source_files(self, cwd: Path) -> None:
        for source_file in (self.datadir / "source_files").iterdir():
            shutil.copy(source_file, cwd / source_file.name)

    @staticmethod
    def _run_pylint(cwd: Path) -> dict[str, Any]:
        result = subprocess.run(
            ["pylint", "-f", "json2", "a.py", "b.py"],
            text=True,
            capture_output=True,
            cwd=cwd,
            check=False,
        )
        return cast(dict[str, Any], json.loads(result.stdout))


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


@dataclasses.dataclass
class PylintrcTestCase:

    @dataclasses.dataclass
    class Descriptor:
        """Describes the configuration style covered by the test case.

        Attributes:
            multiple_directives: Whether there are multiple directives (`True`) or just one (`False`).
            multiple_message_ids: Whether there are multiple message IDs within a given directive (`True`) or just one (`False`).
            multiline_message_ids: Whether message IDs within a given directive are separated by a comma and a newline (`True`) or just a comma (`False`).
            comma_after_each_directive: Whether there is a trailing comma after the last message ID in each directive.
        """

        multiple_directives: bool
        multiple_message_ids: bool
        multiline_message_ids: bool
        comma_after_each_directive: bool

    descriptor: Descriptor
    messages_control_content: str
    a_expected: list[str]
    b_expected: list[str]

    @property
    def id(self):
        descriptor = self.descriptor
        id_parts = [
            (
                "multiple_directives"
                if descriptor.multiple_directives
                else "single_directive"
            ),
            (
                "multiple_message_ids"
                if descriptor.multiple_message_ids
                else "single_message_ids"
            ),
            (
                "multiple_lines_message_ids"
                if descriptor.multiline_message_ids
                else "single_line_message_ids"
            ),
            (
                "comma_after_each_directive"
                if descriptor.comma_after_each_directive
                else "no_comma_after_each_directive"
            ),
        ]
        return "__".join(id_parts)


PYLINTRC_CASES = [
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=True,
            multiple_message_ids=True,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                     unused-import,
                b.py:C0103,
            """),
        a_expected=["invalid-name"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=True,
            multiple_message_ids=True,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                     unused-import,
            """),
        a_expected=["invalid-name"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=True,
            multiple_message_ids=False,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                b.py:C0103,
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=True,
            multiple_message_ids=False,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=False,
            multiple_message_ids=True,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,unused-import,
                b.py:C0103,
            """),
        a_expected=["invalid-name"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=False,
            multiple_message_ids=True,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,unused-import,
            """),
        a_expected=["invalid-name"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=False,
            multiple_message_ids=False,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                b.py:C0103,
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=True,
            multiline_message_ids=False,
            multiple_message_ids=False,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=True,
            multiple_message_ids=True,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                     unused-import
                b.py:C0103
            """),
        a_expected=["invalid-name"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=True,
            multiple_message_ids=True,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,
                     unused-import
            """),
        a_expected=["invalid-name"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=True,
            multiple_message_ids=False,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring
                b.py:C0103
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=True,
            multiple_message_ids=False,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=False,
            multiple_message_ids=True,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,unused-import
                b.py:C0103
            """),
        a_expected=["invalid-name"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=False,
            multiple_message_ids=True,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring,unused-import
            """),
        a_expected=["invalid-name"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=False,
            multiple_message_ids=False,
            multiple_directives=True,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring
                b.py:C0103
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["missing-module-docstring"],
    ),
    PylintrcTestCase(
        descriptor=PylintrcTestCase.Descriptor(
            comma_after_each_directive=False,
            multiline_message_ids=False,
            multiple_message_ids=False,
            multiple_directives=False,
        ),
        messages_control_content=textwrap.dedent("""\
            per-file-ignores =
                a.py:missing-module-docstring
            """),
        a_expected=["invalid-name", "unused-import"],
        b_expected=["invalid-name", "missing-module-docstring"],
    ),
]


@pytest.mark.parametrize("case", PYLINTRC_CASES, ids=lambda c: c.id)
def test_config_pylintrc(runner: Runner, case: PylintrcTestCase) -> None:
    """Test per-file-ignores config parsed from .pylintrc."""
    cwd = runner.datadir / "test_config_pylintrc"
    pylintrc = cwd / ".pylintrc"
    original_content = pylintrc.read_text()

    content = textwrap.dedent("""\
        [MAIN]
        load-plugins = pylint_per_file_ignores

        [MESSAGES CONTROL]
        """) + case.messages_control_content

    try:
        pylintrc.write_text(content)
        result = runner("test_config_pylintrc")

        assert _get_symbols(result, "a") == case.a_expected
        assert _get_symbols(result, "b") == case.b_expected
    finally:
        pylintrc.write_text(original_content)


def test_config_setup_cfg(runner: Runner) -> None:
    """Test per-file-ignores config parsed from setup.cfg."""
    result = runner("test_config_setup_cfg")

    assert _get_symbols(result, "a") == ["invalid-name"]
    assert _get_symbols(result, "b") == ["missing-module-docstring"]
