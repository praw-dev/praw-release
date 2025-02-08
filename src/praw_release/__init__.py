"""Tool to help facilitate prawcore and PRAW releases."""

import argparse
import sys
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
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    bump_parser = subparsers.add_parser("bump")
    bump_parser.add_argument("--changes_file", default=CHANGES_FILENAME, type=argparse.FileType("r+"))
    bump_parser.add_argument("package_name")
    bump_parser.add_argument("version")
    bump_parser.add_argument("version_file", type=argparse.FileType("r+"))
    bump_parser.set_defaults(command=command_bump)

    changes_parser = subparsers.add_parser("changes")
    changes_parser.add_argument("--changes_file", default=CHANGES_FILENAME, type=argparse.FileType("r"))
    changes_parser.add_argument("version")
    changes_parser.set_defaults(command=command_changes)

    extract_parser = subparsers.add_parser("extract-version")
    extract_parser.set_defaults(command=command_extract_version)

    arguments = parser.parse_args()

    command = arguments.command
    command_arguments = vars(arguments)
    del command_arguments["command"]
    return 0 if command(**command_arguments) else 1
