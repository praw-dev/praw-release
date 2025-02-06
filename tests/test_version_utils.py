from datetime import UTC, datetime
from io import StringIO
from unittest.mock import Mock, patch

import packaging.version
import pytest

from praw_release.version_utils import (
    calculate_development_version,
    update_changes,
    update_changes_with_unreleased,
    update_package_version,
    valid_version,
)
from tests.utils import NamedStringIO

UNRELEASED_CHANGES = "Change Log\n==========\n\nmypackage follows `semantic versioning <https://semver.org/>`_.\n\nUnreleased\n----------\n\n"


def test_calculate_development_version() -> None:
    assert calculate_development_version(version_file=StringIO('__version__ = "invalid"')) is None
    assert calculate_development_version(version_file=StringIO('__version__ = "1.0dev0"')) == "1.0.dev1"
    assert calculate_development_version(version_file=StringIO('__version__ = "1.0a0.dev0"')) == "1.0a0.dev1"
    assert calculate_development_version(version_file=StringIO('__version__ = "1.0a0"')) == "1.0a0.dev0"
    assert calculate_development_version(version_file=StringIO('__version__ = "1.0"')) == "1.0.1.dev0"


def test_valid_version() -> None:
    assert str(valid_version("1.1.1")) == "1.1.1"
    assert str(valid_version("0!1.1.1")) == "1.1.1"


def test_valid_version__invalid(capsys: pytest.CaptureFixture) -> None:
    for invalid_version in ("1!1.0", "1.0post0", "1.0+0"):
        assert valid_version(invalid_version) is None
        assert capsys.readouterr().err == "epoch, local, and post release version parts are not supported\n"

    assert valid_version("notvalid") is None
    assert capsys.readouterr().err == "invalid version notvalid\n"


@patch("praw_release.version_utils.datetime")
def test_update_changes(mock_datetime: Mock) -> None:
    mock_datetime.now.return_value = datetime(2025, 1, 1, tzinfo=UTC)

    changes_file = StringIO(f"{UNRELEASED_CHANGES}ABC")
    assert update_changes(changes_file=changes_file, package_name="mypackage", version=packaging.version.parse("1.0"))
    assert changes_file.getvalue() == "Change Log\n==========\n\nmypackage follows `semantic versioning <https://semver.org/>`_.\n\n1.0 (2025/01/01)\n----------------\n\nABC"
    mock_datetime.now.assert_called_once()


def test_update_changes__unexpected_changes(capsys: pytest.CaptureFixture) -> None:
    changes_file = StringIO("invalid changes files")
    assert not update_changes(changes_file=changes_file, package_name="mypackage", version=packaging.version.parse("1.0"))
    assert changes_file.getvalue() == "invalid changes files"
    assert capsys.readouterr().err == "Unexpected CHANGES header\n"


def test_update_changes_with_unreleased() -> None:
    changes_file = StringIO("Change Log\n==========\n\nmypackage follows `semantic versioning <https://semver.org/>`_.\n\nABC")
    assert update_changes_with_unreleased(changes_file=changes_file, package_name="mypackage")
    assert changes_file.getvalue() == f"{UNRELEASED_CHANGES}ABC"


def test_update_changes_with_unreleased__already_unreleased(capsys: pytest.CaptureFixture) -> None:
    changes_file = NamedStringIO(UNRELEASED_CHANGES)
    assert not update_changes_with_unreleased(changes_file=changes_file, package_name="mypackage")
    assert changes_file.getvalue() == UNRELEASED_CHANGES
    assert capsys.readouterr().err == "__init__.py already contains Unreleased header\n"


def test_update_changes_with_unreleased__unexpected_changes(capsys: pytest.CaptureFixture) -> None:
    changes_file = NamedStringIO("invalid changes files")
    assert not update_changes_with_unreleased(changes_file=changes_file, package_name="mypackage")
    assert changes_file.getvalue() == "invalid changes files"
    assert capsys.readouterr().err == "Unexpected header in __init__.py\n"


def test_update_package_version() -> None:
    version_file = StringIO('a\n__version__ = "1.0"\nb\n')
    assert update_package_version(version=packaging.version.parse("1.1"), version_file=version_file)
    assert version_file.getvalue() == 'a\n__version__ = "1.1"\nb\n'


def test_update_package_version__truncate() -> None:
    version_file = StringIO('a\n__version__ = "1.0dev0"\nb\n')
    assert update_package_version(version=packaging.version.parse("1.1"), version_file=version_file)
    assert version_file.getvalue() == 'a\n__version__ = "1.1"\nb\n'


def test_update_package_version__fail_to_lower_version(capsys: pytest.CaptureFixture) -> None:
    version_file = StringIO('a\n__version__ = "1.0"\nb\n')
    assert not update_package_version(version=packaging.version.parse("1.0rc1"), version_file=version_file)
    assert version_file.getvalue() == 'a\n__version__ = "1.0"\nb\n'
    assert capsys.readouterr().err == "Cannot bump version from 1.0 to 1.0rc1\n"


def test_update_package_version__fail_to_update_same_version(capsys: pytest.CaptureFixture) -> None:
    version_file = StringIO('a\n__version__ = "1.0"\nb\n')
    assert not update_package_version(version=packaging.version.parse("1.0"), version_file=version_file)
    assert version_file.getvalue() == 'a\n__version__ = "1.0"\nb\n'
    assert capsys.readouterr().err == "Cannot bump version from 1.0 to 1.0\n"


def test_update_package_version__invalid_existing_version_string() -> None:
    version_file = StringIO('a\n__version__ = "notvalid"\nb\n')
    assert not update_package_version(version=packaging.version.parse("1.1"), version_file=version_file)
    assert version_file.getvalue() == 'a\n__version__ = "notvalid"\nb\n'


def test_update_package_version__no_version_string() -> None:
    version_file = StringIO("some\ntext")
    assert not update_package_version(version=packaging.version.parse("1.1"), version_file=version_file)
    assert version_file.getvalue() == "some\ntext"
