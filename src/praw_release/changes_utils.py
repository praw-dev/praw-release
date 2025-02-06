"""Functions pertaining to CHANGES.rst files."""

import docutils.nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser
from docutils.utils import new_document


def _get_entry_slice(*, document: docutils.nodes.document, version: str) -> slice | None:
    """Return the line numbers that encompass the version's changelog entry."""
    start_line = None
    end_line = None
    if not document.children:
        return None

    for node in document.children[0].children:
        if not isinstance(node, docutils.nodes.section):
            continue

        title = node.children[0]
        assert isinstance(title, docutils.nodes.title)
        assert isinstance(title.line, int)

        if start_line is None:
            first_token = title.rawsource.split(None, 1)[0]
            if first_token == version:
                start_line = title.line - 2
        elif start_line is not None:
            end_line = title.line - 3
            break

    if start_line is None:
        return None

    return slice(start_line, end_line)


def _parse_rst(text: str, /) -> docutils.nodes.document:
    """Parse ``text`` as reStructuredText."""
    settings = get_default_settings(Parser)
    settings.report_level = 4
    Parser().parse(text, document := new_document("<rst-doc>", settings=settings))
    return document


def extract_version_changes(*, source: str, version: str) -> str | None:
    """Return the changes entry for the provided version."""
    entry_slice = _get_entry_slice(document=_parse_rst(source), version=version)
    if entry_slice is None:
        return None
    return "".join(source.splitlines(keepends=True)[entry_slice])
