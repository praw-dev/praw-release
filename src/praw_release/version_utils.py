"""Functions pertaining to package version number."""

import re
import sys
from datetime import UTC, datetime
from typing import TextIO

import packaging.version

CHANGELOG_HEADER = "Change Log\n==========\n\n{} follows `semantic versioning <https://semver.org/>`_.\n\n"
UNRELEASED_HEADER = "Unreleased\n----------\n\n"
VERSION_RE = re.compile(r'__version__ = "([^"]+)"')


def calculate_development_version(*, version_file: TextIO) -> str | None:
    """Bump to the next development version."""
    match = re.search('__version__ = "([^"]+)"', version_file.read())
    version_file.seek(0)
    assert isinstance(match, re.Match), "no version string found"
    if (parsed_version := valid_version(match.group(1))) is None:
        return None

    if parsed_version.is_devrelease:
        pre = "".join(str(x) for x in parsed_version.pre) if parsed_version.pre else ""
        assert isinstance(parsed_version.dev, int)
        development_version = f"{parsed_version.base_version}{pre}.dev{parsed_version.dev + 1}"
    elif parsed_version.is_prerelease:
        development_version = f"{parsed_version}.dev0"
    else:
        development_version = f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.micro + 1}.dev0"

    return development_version


def update_changes(*, changes_file: TextIO, package_name: str, version: packaging.version.Version) -> bool:
    """Update unreleased changelog entry to be for ``version``."""
    changelog_header = CHANGELOG_HEADER.format(package_name)
    content = changes_file.read()
    changes_file.seek(0)

    expected_header = f"{changelog_header}{UNRELEASED_HEADER}"
    if not content.startswith(expected_header):
        sys.stderr.write("Unexpected CHANGES header\n")
        return False

    date_string = datetime.now(tz=UTC).date().strftime("%Y/%m/%d")
    version_line = f"{version} ({date_string})\n"
    version_header = f"{version_line}{'-' * len(version_line[:-1])}\n\n"

    changes_file.write(f"{changelog_header}{version_header}{content[len(expected_header) :]}")
    return True


def update_changes_with_unreleased(*, changes_file: TextIO, package_name: str) -> bool:
    """Add Unreleased section to top of changes_file."""
    changelog_header = CHANGELOG_HEADER.format(package_name)
    content = changes_file.read()
    changes_file.seek(0)

    if not content.startswith(changelog_header):
        sys.stderr.write(f"Unexpected header in {changes_file.name}\n")
        return False
    new_header = f"{changelog_header}{UNRELEASED_HEADER}"
    if content.startswith(new_header):
        sys.stderr.write(f"{changes_file.name} already contains Unreleased header\n")
        return False

    changes_file.write(f"{new_header}{content[len(changelog_header) :]}")
    return True


def update_package_version(*, version: packaging.version.Version, version_file: TextIO) -> bool:
    """Update the version number in the package."""
    content = version_file.read()
    version_file.seek(0)

    if (match := VERSION_RE.search(content)) is None:
        return False

    if (current_version := valid_version(match.group(1))) is None:
        return False

    if version <= current_version:
        sys.stderr.write(f"Cannot bump version from {current_version} to {version}\n")
        return False

    version_file.write(VERSION_RE.sub(f'__version__ = "{version}"', content))
    version_file.truncate()
    return True


def valid_version(version: str, /) -> packaging.version.Version | None:
    """Return a Version object if version string is valid."""
    try:
        parsed_version = packaging.version.parse(version)
    except packaging.version.InvalidVersion:
        sys.stderr.write(f"invalid version {version}\n")
        return None
    if parsed_version.local or parsed_version.is_postrelease or parsed_version.epoch:
        sys.stderr.write("epoch, local, and post release version parts are not supported\n")
        return None
    return parsed_version
