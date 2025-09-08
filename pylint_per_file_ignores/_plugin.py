"""pylint-per-file-ignores plugin."""

from __future__ import annotations

import glob
import re
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pylint import utils
from pylint.checkers import BaseChecker
from pylint.exceptions import UnknownMessageError
from pylint.lint import PyLinter
from pylint.message import MessageDefinition


def _get_checker_by_msg(linter: PyLinter, rule: str) -> BaseChecker:
    for checker in linter.get_checkers():
        for key, value in checker.msgs.items():
            if rule in [key, value[1]]:
                return checker
    raise UnknownMessageError(f"Unknown message {rule}")


def _augment_add_message(
    linter: PyLinter, *, rules: list[str], files: list[Path]
) -> None:
    checkers: dict[BaseChecker, list[MessageDefinition]] = defaultdict(list)
    for rule in rules:
        defs = linter.msgs_store.get_message_definitions(rule)
        checkers[_get_checker_by_msg(linter, rule)].extend(defs)

    for checker, messages in checkers.items():
        add_message_method = checker.__class__.add_message

        def _add_message(
            *args: Any,
            ppfi_messages: list[MessageDefinition] = messages,
            ppfi_func: Callable[..., None] = add_message_method,
            **kwargs: Any,
        ) -> None:
            assert linter.current_file
            if Path(linter.current_file).absolute() in files and any(
                msg in ppfi_messages
                for msg in linter.msgs_store.get_message_definitions(args[1])
            ):
                return
            ppfi_func(*args, **kwargs)

        # use the class to avoid issues with parallel execution
        checker.__class__.add_message = _add_message  # type:ignore[method-assign]


class PerFileIgnoresChecker(BaseChecker):
    """pylint-per-file-ignores plugin."""

    options = (
        (
            "per-file-ignores",
            {
                "default": "",
                "type": "string",
                "metavar": "<str>",
                "help": "Newline-separated list of ignores",
            },
        ),
    )


def register(linter: PyLinter) -> None:
    """Register the plugin."""
    linter.register_checker(PerFileIgnoresChecker(linter))


def _parse_string(input_string: str) -> list[str]:
    if "\n" not in input_string:
        # Config rules from pyproject.toml are supplied as a flat string.
        # E.g. "a/foo*.py:W123,C0456,b/bar*.py:C1312"
        # Introduce newlines between rules to be able to use pylint parsing utility.
        input_string = re.sub(r",([^,:]+:)", r"\n\1", input_string)

    return utils._splitstrip(input_string, sep="\n")


def load_configuration(linter: PyLinter) -> None:
    """Load the configuration."""
    config = dict(
        config_item.split(":")
        for config_item in _parse_string(linter.config.per_file_ignores)
    )

    for pattern, rules_str in config.items():
        if pattern.startswith("\n"):
            pattern = pattern[1:]
        files = [Path(file).absolute() for file in glob.glob(pattern, recursive=True)]
        rules = list(filter(None, (rule.strip() for rule in rules_str.split(","))))
        _augment_add_message(linter, rules=rules, files=files)
