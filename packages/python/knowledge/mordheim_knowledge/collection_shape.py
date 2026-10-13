"""The collection shape the knowledge base writes: block, never non-empty flow.

A key the KB writes in block form (`source_path`, `equipment_lists`, `rule_ids`,
`skill_access`, and the mappings `source`, `characteristics`, `name_i18n`,
`combat_traits`) must not be published as a non-empty flow collection: `[a, b]`
or `{a: 1}` is a shape the contract does not keep, while the empty `[]` / `{}`
is. This module is that reading — the constants and the scanner — and it is what
`staging_contract_audit` asks about a catalogue document.

The block lived in `staging_promotion.py` while the staging trees existed; it
moved here when they were retired (2026-10-08), because the reading is about the
knowledge base's own shape and not about a promotion. `shape_pass`, the writer
that rewrote a staged document into this shape, was retired with the trees.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from mordheim_knowledge import open_field_normalization as lexical


# --------------------------------------------------------------------------- #
# The collection shape: the keys the KB writes in block form
# --------------------------------------------------------------------------- #

#: Keys the knowledge base writes as a *block* sequence. Measured over the KB (and
#: over the retired staging trees, which matched), it keeps these four in block
#: form and never writes a non-empty flow sequence — ``source_path``,
#: ``equipment_lists``, ``rule_ids``, ``skill_access`` — while an empty list is
#: ``[]``, which the KB also writes.
BLOCK_SEQUENCE_KEYS: tuple[str, ...] = ("source_path", "equipment_lists", "rule_ids", "skill_access")

#: Keys the knowledge base writes as a *block* mapping: ``name_i18n`` 3 742,
#: ``source`` 2 290, ``characteristics`` 666 and ``combat_traits`` (``{}`` 437
#: times, the rest anchored block mappings). A staged ``{...}`` is the one shape
#: of these keys the KB does not have.
BLOCK_MAPPING_KEYS: tuple[str, ...] = ("source", "characteristics", "name_i18n", "combat_traits")

#: Every key a promotion copy has to write in block form before it merges.
BLOCK_COLLECTION_KEYS: tuple[str, ...] = BLOCK_SEQUENCE_KEYS + BLOCK_MAPPING_KEYS

_FLOW_VALUE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):\s*(?P<value>[\[\{].*)$")


@dataclass(frozen=True)
class FlowCollection:
    """A non-empty flow collection under a key the KB writes in block form."""

    line: int
    end: int
    key: str
    sequence: bool
    body: str


def _value_position(text: str, position: int) -> bool:
    """Whether the quote at ``position`` opens a scalar rather than sits inside one."""
    for earlier in range(position - 1, -1, -1):
        character = text[earlier]
        if character.isspace():
            continue
        return character in ":,{["
    return True


def _flow_span(lines: list[str], start: int, column: int) -> tuple[int, int] | None:
    """``(line, column)`` of the bracket that closes the collection opened here.

    Quotes are tracked because the staged flows carry single-quoted URLs: a `]`
    inside one is text, not the end of the collection.
    """
    depth = 0
    quote: str | None = None
    for index in range(start, len(lines)):
        line = lines[index]
        position = column if index == start else 0
        while position < len(line):
            character = line[position]
            if quote is not None:
                if character == quote:
                    quote = None
            elif character in "'\"" and _value_position(line, position):
                quote = character
            elif character in "[{":
                depth += 1
            elif character in "]}":
                depth -= 1
                if depth == 0:
                    return index, position
            position += 1
    return None


def _one_line(text: str) -> str:
    """A flow body that spans lines, on one line, with quoted text left as it is.

    A line break inside a quoted scalar folds to a space in YAML, so collapsing
    the run of whitespace a break introduces — and nothing else — keeps the
    value; a quoted URL keeps its interior spacing byte for byte.
    """
    out: list[str] = []
    quote: str | None = None
    pending = False
    for position, character in enumerate(text):
        if quote is not None:
            if character == "\n":
                out.append(" ")
                pending = True
            elif pending and character.isspace():
                continue
            else:
                pending = False
                out.append(character)
                if character == quote:
                    quote = None
            continue
        if character.isspace():
            pending = True
            continue
        if pending:
            out.append(" ")
            pending = False
        if character in "'\"" and _value_position(text, position):
            quote = character
        out.append(character)
    return "".join(out).strip()


def _split_flow(body: str) -> list[str]:
    """The top-level entries of a flow collection body, verbatim.

    A comma inside a quoted scalar or a nested collection is part of the entry.
    """
    entries: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    for position, character in enumerate(body):
        if quote is not None:
            current.append(character)
            if character == quote:
                quote = None
            continue
        if character in "'\"" and _value_position(body, position):
            quote = character
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
        elif character == "," and depth == 0:
            entries.append("".join(current))
            current = []
            continue
        current.append(character)
    entries.append("".join(current))
    return [entry.strip() for entry in entries if entry.strip()]


def _flow_entry(entry: str) -> tuple[str, str]:
    """``(key, value)`` of a flow mapping entry, the value verbatim."""
    depth = 0
    quote: str | None = None
    for position, character in enumerate(entry):
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in "'\"" and _value_position(entry, position):
            quote = character
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
        elif character == ":" and depth == 0:
            return entry[:position].strip(), entry[position + 1 :].strip()
    return entry.strip(), ""


def _block_collection(line: str, collection: FlowCollection) -> list[str]:
    """The block collection carrying the same entries, in the KB's shape.

    A block sequence puts its dashes at the indent of its key — measured over
    every block sequence of the three trees, that delta is always zero — and a
    block mapping puts its children two columns in.
    """
    indent = line[: len(line) - len(line.lstrip())]
    ending = lexical.line_ending(line)
    block = [f"{indent}{collection.key}:{ending}"]
    if collection.sequence:
        return block + [f"{indent}- {entry}{ending}" for entry in _split_flow(collection.body)]
    for entry in _split_flow(collection.body):
        name, value = _flow_entry(entry)
        block.append(f"{indent}  {name}:{' ' + value if value else ''}{ending}")
    return block


def flow_collections(text: str) -> list[FlowCollection]:
    """Every non-empty flow collection under a key the KB writes in block form.

    An *empty* collection is not returned: ``[]`` and ``{}`` are the shape the KB
    itself uses for "nothing", so they are already canonical.
    """
    found: list[FlowCollection] = []
    lines = lexical.lines(text)
    for index, line in enumerate(lines):
        match = _FLOW_VALUE.match(line)
        if match is None or match.group("key") not in BLOCK_COLLECTION_KEYS:
            continue
        span = _flow_span(lines, index, match.start("value"))
        if span is None:
            raise ValueError(f"unterminated flow collection at line {index + 1}: {line.strip()!r}")
        end, column = span
        opening = match.start("value")
        if end == index:
            body = lines[index][opening + 1 : column]
        else:
            body = "\n".join([lines[index][opening + 1 :], *lines[index + 1 : end], lines[end][:column]])
        flat = _one_line(body)
        if not flat or flat.startswith("#"):
            continue
        found.append(
            FlowCollection(index, end, match.group("key"), match.group("value").lstrip()[0] == "[", flat)
        )
    return found

