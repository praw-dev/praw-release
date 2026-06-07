"""Tool to help facilitate prawcore and PRAW releases."""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO

from praw_release.changes_utils import extract_version_changes
from praw_release.version_utils import (
    calculate_development_version,
    update_changes,
    update_changes_with_unreleased,
    update_package_version,
    valid_version,
)

CHANGES_FILENAME = "CHANGES.rst"
COMMIT_PREFIX = "Bump to v"


def command_bump(*, changes_file: TextIO, package_name: str, version: str, version_file: TextIO) -> bool:
    """Validate version string and update the code and CHANGELOG using the desired version."""
    unreleased = False
    if version == "unreleased":
        unreleased = True
        if (development_version := calculate_development_version(version_file=version_file)) is None:
            return False
        version = development_version

    if (normalized_version := valid_version(version)) is None:
        return False

    if not update_package_version(version=normalized_version, version_file=version_file):
        sys.stderr.write(f"Failed to update version in {version_file.name}\n")
        return False

    success = (
        update_changes_with_unreleased(changes_file=changes_file, package_name=package_name)
        if unreleased
        else update_changes(changes_file=changes_file, package_name=package_name, version=normalized_version)
    )
    if success:
        sys.stdout.write(f"{normalized_version}\n")
    return success


def command_changes(changes_file: TextIO, version: str) -> bool:
    """Output the changes entry for the provided version."""
    changes = extract_version_changes(source=changes_file.read(), version=version)
    if changes is None:
        sys.stderr.write(f"No {changes_file.name} entry for {version}\n")
        return False
    sys.stdout.write(changes)
    return True


def command_extract_version() -> bool:
    """Output version from commit_message."""
    line = sys.stdin.readline()
    if not line.startswith(COMMIT_PREFIX):
        sys.stderr.write(f"Commit message does not begin with `{COMMIT_PREFIX}`.\nMessage:\n\n{line}")
        return False
    sys.stdout.write(line[len(COMMIT_PREFIX) : -1])
    return True


def main() -> int:
    """Provide the entrypoint into the CLI."""
    parser = argparse.ArgumentParser(prog="praw-release")
    subparsers = parser.add_subparsers(required=True)

    bump_parser = subparsers.add_parser("bump")
    bump_parser.add_argument("--changes_file", default=CHANGES_FILENAME)
    bump_parser.add_argument("package_name")
    bump_parser.add_argument("version")
    bump_parser.add_argument("version_file")
    bump_parser.set_defaults(command=command_bump, file_modes={"changes_file": "r+", "version_file": "r+"})

    changes_parser = subparsers.add_parser("changes")
    changes_parser.add_argument("--changes_file", default=CHANGES_FILENAME)
    changes_parser.add_argument("version")
    changes_parser.set_defaults(command=command_changes, file_modes={"changes_file": "r"})

    extract_parser = subparsers.add_parser("extract-version")
    extract_parser.set_defaults(command=command_extract_version, file_modes={})

    command_arguments = vars(parser.parse_args())
    command = command_arguments.pop("command")
    file_modes = command_arguments.pop("file_modes")

    # Open file arguments after parsing; argparse.FileType (deprecated in Python 3.14)
    # opened them at parse time, leaking handles and truncating files on later errors.
    with contextlib.ExitStack() as stack:
        for name, mode in file_modes.items():
            path = command_arguments[name]
            try:
                command_arguments[name] = stack.enter_context(Path(path).open(mode))
            except OSError as exception:
                parser.error(f"can't open {path!r}: {exception}")
        return 0 if command(**command_arguments) else 1
