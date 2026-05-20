"""pylint-per-file-ignores plugin."""

from __future__ import annotations

import glob
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
        checker.__class__.add_message = _add_message  # type: ignore[method-assign]


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


def _apply_argument(rules: list[str], pattern: str, linter: PyLinter) -> None:
    if not rules:
        linter.add_message(
            "config-parse-error", args=f"No rules specified for file pattern {pattern}"
        )
    files = [Path(file).absolute() for file in glob.glob(pattern, recursive=True)]
    _augment_add_message(linter, rules=rules, files=files)


def load_configuration(linter: PyLinter) -> None:
    """Load the configuration."""
    input_string: str = linter.config.per_file_ignores.replace("\n", ",")
    parts = [part.strip() for part in input_string.split(",") if part.strip()]

    current_pattern = None
    current_rules = []
    seen_patterns = set()
    for part in parts:
        if ":" not in part:
            current_rules.append(part)
            continue

        # we found a new file pattern
        if current_pattern is not None:  # we had a previous file pattern
            _apply_argument(current_rules, current_pattern, linter)
            # reset state
            current_rules = []
            current_pattern = None

        current_pattern, rule = part.split(":", 1)
        if current_pattern in seen_patterns:
            linter.add_message(
                "config-parse-error", args=f"Duplicate file pattern {current_pattern}"
            )
        seen_patterns.add(current_pattern)
        if current_pattern.startswith("\n"):
            current_pattern = current_pattern[1:]
        if rule:
            current_rules.append(rule.strip())

    if current_pattern is not None:
        _apply_argument(current_rules, current_pattern, linter)
