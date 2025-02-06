import sys
from io import StringIO
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest

from praw_release import command_bump, command_changes, main
from tests.test_version_utils import UNRELEASED_CHANGES
from tests.utils import NamedStringIO


def test_command_bump(capsys: pytest.CaptureFixture) -> None:
    assert command_bump(changes_file=StringIO(UNRELEASED_CHANGES), package_name="mypackage", version="1.1", version_file=StringIO('__version__ = "1.0"'))
    assert capsys.readouterr().out == "1.1\n"


def test_command_bump__invalid_changes_file(capsys: pytest.CaptureFixture) -> None:
    assert not command_bump(changes_file=StringIO(), package_name="mypackage", version="1.0.1", version_file=StringIO('__version__ = "1.0"'))
    assert capsys.readouterr().err == "Unexpected CHANGES header\n"


def test_command_bump__invalid_version(capsys: pytest.CaptureFixture) -> None:
    assert not command_bump(changes_file=StringIO(), package_name="mypackage", version="notvalid", version_file=StringIO())
    assert capsys.readouterr().err == "invalid version notvalid\n"


def test_command_bump__invalid_version_file() -> None:
    assert not command_bump(changes_file=StringIO(), package_name="mypackage", version="1.0", version_file=NamedStringIO())


def test_command_bump__unreleased__invalid_changes_file(capsys: pytest.CaptureFixture) -> None:
    assert not command_bump(changes_file=NamedStringIO(), package_name="mypackage", version="unreleased", version_file=StringIO('__version__ = "1.0"'))
    assert capsys.readouterr().err == "Unexpected header in __init__.py\n"


def test_command_bump__unreleased__invalid_version(capsys: pytest.CaptureFixture) -> None:
    assert not command_bump(changes_file=StringIO(), package_name="mypackage", version="unreleased", version_file=StringIO('__version__ = "notvalid"'))
    assert capsys.readouterr().err == "invalid version notvalid\n"


def test_command_changes(capsys: pytest.CaptureFixture) -> None:
    assert command_changes(changes_file=NamedStringIO("A\n=\n1\n-\n", name="CHANGES.rst"), version="1")
    assert capsys.readouterr().out == "1\n-\n"


def test_command_changes__version_not_found(capsys: pytest.CaptureFixture) -> None:
    assert not command_changes(changes_file=NamedStringIO(name="CHANGES.rst"), version="notfound")
    assert capsys.readouterr().err == "No CHANGES.rst entry for notfound\n"


def test_main__changes__fails(capsys: pytest.CaptureFixture) -> None:
    with NamedTemporaryFile() as changes_file, patch.object(sys, "argv", ["progname", "changes", "--changes_file", changes_file.name, "1.0"]):
        assert main() == 1
    assert capsys.readouterr().err == f"No {changes_file.name} entry for 1.0\n"


def test_main__extract_version(capsys: pytest.CaptureFixture) -> None:
    with patch.object(sys, "argv", ["progname", "extract-version"]), patch.object(sys, "stdin", StringIO("Bump to v1.0.1c10\n")):
        assert main() == 0
    assert capsys.readouterr().out == "1.0.1c10"


def test_main__extract_version__not_found(capsys: pytest.CaptureFixture) -> None:
    with patch.object(sys, "argv", ["progname", "extract-version"]), patch.object(sys, "stdin", StringIO("One line")):
        assert main() == 1
    assert capsys.readouterr().err == "Commit message does not begin with `Bump to v`.\nMessage:\n\nOne line"


def test_main__no_command(capsys: pytest.CaptureFixture) -> None:
    with patch.object(sys, "argv", ["progname"]), pytest.raises(SystemExit):
        main()
    assert capsys.readouterr().err == "usage: progname [-h] {bump,changes,extract-version} ...\nprogname: error: the following arguments are required: {bump,changes,extract-version}\n"
