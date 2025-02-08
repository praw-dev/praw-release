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


def test_extract_version_changes__empty_source() -> None:
    assert extract_version_changes(source="", version="Unreleased") is None


def test_extract_version_changes__no_title() -> None:
    assert extract_version_changes(source="1.0\n---", version="1.0") is None
    assert extract_version_changes(source="\n1.0\n---", version="1.0") is None


def test_extract_version_changes__first_version() -> None:
    assert extract_version_changes(source=EXAMPLE_DOCUMENT, version="Unreleased") == "Unreleased\n----------\n"


def test_extract_version_changes__last_version() -> None:
    assert extract_version_changes(source=EXAMPLE_DOCUMENT, version="last") == "last\n----"


def test_extract_version_changes__single_section() -> None:
    assert extract_version_changes(source="Title\n=====\n1.0\n---", version="1.0") == "1.0\n---"
    assert extract_version_changes(source="Title\n=====\n1.0\n---\n\n\n", version="1.0") == "1.0\n---\n\n\n"


def test_extract_version_changes__version_with_earlier_prefix_match() -> None:
    assert (
        extract_version_changes(source=EXAMPLE_DOCUMENT, version="5.0")
        == "5.0 (other info)\n----------------\na\nb\nc\n"
    )


def test_extract_version_changes__version_not_found() -> None:
    for invalid_version in ("1.0", "unreleased", "5.0 (other info)"):
        assert extract_version_changes(source=EXAMPLE_DOCUMENT, version=invalid_version) is None
