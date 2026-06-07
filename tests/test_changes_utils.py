from praw_release.changes_utils import extract_version_changes

EXAMPLE_DOCUMENT = """Title
=====

Unreleased
----------

5.0.1
-----
latest release

5.0 (other info)
----------------
a
b
c

last
----"""


OVERLINED_DOCUMENT = """############
 Change Log
############

mypackage follows `semantic versioning <https://semver.org/>`_.

********************
 1.1.0 (2026/06/07)
********************

**Added**

- New feature.

********************
 1.0.0 (2025/01/01)
********************

**Fixed**

- A fix.
"""


def test_extract_version_changes__empty_source() -> None:
    assert extract_version_changes(source="", version="Unreleased") is None


def test_extract_version_changes__no_title() -> None:
    assert extract_version_changes(source="1.0\n---", version="1.0") is None
    assert extract_version_changes(source="\n1.0\n---", version="1.0") is None


def test_extract_version_changes__first_version() -> None:
    changes = extract_version_changes(source=EXAMPLE_DOCUMENT, version="Unreleased")
    assert changes is not None
    assert not changes


def test_extract_version_changes__last_version() -> None:
    changes = extract_version_changes(source=EXAMPLE_DOCUMENT, version="last")
    assert changes is not None
    assert not changes


def test_extract_version_changes__overlined_sections() -> None:
    assert extract_version_changes(source=OVERLINED_DOCUMENT, version="1.1.0") == "**Added**\n\n- New feature.\n"
    assert extract_version_changes(source=OVERLINED_DOCUMENT, version="1.0.0") == "**Fixed**\n\n- A fix.\n"


def test_extract_version_changes__single_section() -> None:
    for source in ("Title\n=====\n1.0\n---", "Title\n=====\n1.0\n---\n\n\n"):
        changes = extract_version_changes(source=source, version="1.0")
        assert changes is not None
        assert not changes


def test_extract_version_changes__version_with_earlier_prefix_match() -> None:
    assert extract_version_changes(source=EXAMPLE_DOCUMENT, version="5.0") == "a\nb\nc\n"


def test_extract_version_changes__version_not_found() -> None:
    for invalid_version in ("1.0", "unreleased", "5.0 (other info)"):
        assert extract_version_changes(source=EXAMPLE_DOCUMENT, version=invalid_version) is None
