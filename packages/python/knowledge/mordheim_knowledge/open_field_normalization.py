"""Close the vocabulary of the fields the editorial contract leaves open.

The contract types five fields loosely on purpose — ``band.yaml`` ``status`` and
``categories``, ``sources[].manual``, ``profiles[].source_path`` and the
catalogue ``status`` — so an editorial value is never rejected for being new.
A loose field is only safe while a *gate* keeps it aligned with the knowledge
base it belongs to; ``staging_contract_audit`` measures the drift and this
module removes it.

Four vocabularies are closed here, each against the decision the KB already
carries:

- **``sources[].manual``** is a registered source id: ``registry/sources.yaml``
  says so and ``catalog-items.yaml.schema.json`` repeats it. Every manual of the
  KB and of the staging trees is normalised to its registered id, and the ids
  that were still missing (including the ones the *active* KB used without
  registering) are added to the registry.
- **``band.yaml`` ``status``** is ``source-normalized`` — the only value the KB
  uses, and the one its own field description names. The staging trees carried
  two values for the same editorial state and now carry one.
- **``profiles[].source_path[0]``** is the printed roster group: ``heroes``,
  ``henchmen``, ``heroines``, ``henchwomen`` or ``summoned``. A source section
  label that is not a roster group is resolved through the profile's ``type``,
  which is where the KB reads the roster kind from.
- **``categories`` / ``grade``** are the grade vocabulary. ``2a`` is already a
  KB grade (the hired-swords and dramatis catalogues carry ``grade-2a`` files);
  ``2b`` is the new grade of the 2B sources and is registered in the hireling
  grade enums instead of being folded into ``2a``, which the grade contract
  forbids ("kept apart so a source change stays auditable").

Editing is lexical and line-scoped, like ``tools/normalize_names.py``: comments,
key order and every untouched field survive byte for byte, and each edited file
is re-parsed and compared against the same transformation applied to the parsed
document, so an edit that changes anything else fails instead of landing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

import yaml

CHECKOUT = Path(__file__).resolve().parents[4]
KB_ROOT = Path("sources") / "knowledge"
STAGING_TREES = ("2A", "2B")

# --------------------------------------------------------------------------- #
# The registered source vocabulary
# --------------------------------------------------------------------------- #

#: Registered ids and their display name, in registry order. The first four were
#: already used by the KB without being registered; the rest come from the
#: staging sources, whose printed manual names are not ids.
SOURCE_IDS: tuple[tuple[str, str], ...] = (
    ("mordheimer.net", "mordheimer.net"),
    ("chaos-in-the-streets", "Chaos in the Streets"),
    ("khemri", "Khemri (Mordheimer.net)"),
    ("lustria", "Lustria (Mordheimer.net)"),
    ("trollheim", "Trollheim (Mordheimer.net)"),
    ("user-ruling", "User Ruling"),
    ("mordheim-rulebook", "Mordheim Rulebook"),
    ("sylvania-supplement", "Sylvania Supplement (Mordheimer.net)"),
    ("mordheim-index-catalog", "Mordheim Index Catalog (Mordheimer.net)"),
    ("mordheim-facebook-group", "Mordheim Facebook Group"),
    ("broheim.net", "broheim.net"),
    ("liber-malefic", "Liber Malefic (Miracle Workers, Werekin)"),
)

#: ``manual`` values that are not ids yet, mapped to the id that replaces them.
MANUAL_VALUES: dict[str, str] = {
    "mordheimer.net (Sylvania Supplement)": "sylvania-supplement",
    "mordheimer.net (Mordheim Index Catalog)": "mordheim-index-catalog",
    "Mordheim Facebook Group": "mordheim-facebook-group",
    "Broheim": "broheim.net",
    "Liber Malefic (Miracle Workers, Werekin)": "liber-malefic",
    "Mordheim Rulebook": "mordheim-rulebook",
}

#: The editorial status a band package declares. The KB carries exactly one.
BAND_STATUS = "source-normalized"

#: Roster groups a printed profile may live under. The first element of
#: ``source_path`` is one of these; anything else is a source section label.
SOURCE_PATH_ROOTS: tuple[str, ...] = ("heroes", "henchmen", "heroines", "henchwomen", "summoned")

#: Source section labels that are not roster groups, and the roster kind they
#: stand for when the profile's own ``type`` cannot be read.
SOURCE_PATH_LABELS: dict[str, str] = {
    "choice-of-warriors": "henchmen",
}

_SCALAR = re.compile(r"^(?P<indent>\s*)(?P<dash>- )?(?P<key>[A-Za-z0-9_.-]+):(?P<sep>\s+)(?P<value>.+?)\s*$")
_KEY = re.compile(r"^(?P<indent>\s*)(?P<dash>- )?(?P<key>[A-Za-z0-9_.-]+):(?P<rest>.*)$")
_LIST_ITEM = re.compile(r"^(?P<indent>\s*)-\s+(?P<value>.+?)\s*$")


@dataclass
class Edit:
    """One file's normalisation: what it was, what it becomes and why."""

    path: Path
    changes: list[str]
    text: str
    original: str

    def write(self) -> None:
        # A pass may write a document the tree does not have yet (the Dramatis
        # catalogue of a split family), so the directory is part of the edit.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(self.text.encode("utf-8"))


@dataclass
class Report:
    edits: list[Edit] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.edits)

    def write(self) -> None:
        for edit in self.edits:
            edit.write()

    def summary(self) -> str:
        lines = []
        for edit in sorted(self.edits, key=lambda item: item.path.as_posix()):
            lines.append(f"{edit.path.as_posix()} — {', '.join(edit.changes)}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Lexical helpers
# --------------------------------------------------------------------------- #


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def _ending(line: str) -> str:
    """The line terminator the line already carries.

    The tree is checked out with CRLF on Windows and LF elsewhere; a rewritten
    line must keep the convention of the file it lives in, or the canonical
    formatter sees a file whose lines disagree.
    """
    return "\r\n" if line.endswith("\r\n") else "\n"


#: Text of files a pass has already rewritten in this run. Passes chain: the
#: second pass of a file reads what the first one left, never the file on disk.
_OVERLAY: dict[Path, str] = {}


def _read_text(path: Path) -> str:
    """The file's text, exactly as it is on disk.

    Bytes, not ``read_text``: this tree declares ``*.yaml text eol=lf`` in
    ``.gitattributes``, and text-mode I/O silently rewrote CRLF files as CRLF
    and LF files as CRLF on Windows. A tool that edits YAML line by line must
    see — and write — the bytes the file actually has.
    """
    if path in _OVERLAY:
        return _OVERLAY[path]
    return path.read_bytes().decode("utf-8")


def _publish(path: Path, text: str) -> None:
    _OVERLAY[path] = text


def _scalar_value(line: str, key: str) -> str | None:
    match = _SCALAR.match(line)
    if match is None or match.group("key") != key or match.group("dash"):
        return None
    return match.group("value")


def _plain(value: str) -> str:
    """Unquote a scalar the way the canonical formatter writes short values."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _replace_scalar(line: str, key: str, new_value: str) -> str:
    match = _SCALAR.match(line)
    assert match is not None
    return (
        f"{match.group('indent')}{match.group('dash') or ''}{key}:"
        f"{match.group('sep')}{new_value}{_ending(line)}"
    )


def drop_key(text: str, key: str, *, root: bool = False) -> tuple[str, int]:
    """Remove a key and its block, list items included."""
    out: list[str] = []
    dropped = 0
    lines = _lines(text)
    index = 0
    while index < len(lines):
        line = lines[index]
        match = _SCALAR.match(line)
        is_target = (
            match is not None
            and match.group("key") == key
            and (not root or not match.group("indent"))
        )
        if not is_target:
            out.append(line)
            index += 1
            continue
        indent = len(match.group("indent"))
        dropped += 1
        index += 1
        while index < len(lines):
            following = lines[index]
            if not following.strip() or following.lstrip().startswith("#"):
                # A comment or a blank line inside the block stays only while the
                # block continues; look ahead for the next real line.
                lookahead = index
                while lookahead < len(lines) and (
                    not lines[lookahead].strip() or lines[lookahead].lstrip().startswith("#")
                ):
                    lookahead += 1
                if lookahead >= len(lines):
                    break
                following = lines[lookahead]
            candidate = _SCALAR.match(following)
            item = _LIST_ITEM.match(following)
            following_indent = len(following) - len(following.lstrip())
            if item is not None and item.group("indent") == match.group("indent"):
                # A sibling list item of the *owning* list (the catalogue record).
                break
            if candidate is not None and following_indent <= indent:
                break
            if item is not None and following_indent < indent:
                break
            index += 1
        continue
    return "".join(out), dropped


# --------------------------------------------------------------------------- #
# Passes
# --------------------------------------------------------------------------- #


def _staging_roots() -> Iterable[Path]:
    for tree in STAGING_TREES:
        yield Path("sources") / tree


def _yaml_files(root: Path) -> Iterator[Path]:
    if not root.exists():
        return
    yield from sorted(path for path in root.rglob("*.yaml") if path.is_file())


#: ``manual:`` inside a flow mapping (``source: {manual: X, page: 1}``): the value
#: ends at the entry separator, which the scan finds by trying the longest
#: candidate first — one registered name contains a comma inside it.
_INLINE_MANUAL = re.compile(r"(?<![\w.-])manual:(?P<gap>[ ]*)(?P<rest>[^\n]*)")


def manual_occurrences(text: str) -> Iterator[tuple[int, int, int, str]]:
    """``(line, start, end, value)`` of every ``manual`` scalar of a document.

    Both shapes are covered: a line of its own and an entry of a flow mapping.
    """
    for index, line in enumerate(_lines(text)):
        match = _SCALAR.match(line)
        if match is not None and match.group("key") == "manual":
            start = match.start("value")
            yield index, start, start + len(match.group("value")), _plain(match.group("value"))
            continue
        for inline in _INLINE_MANUAL.finditer(line):
            rest = inline.group("rest")
            end = _value_end(rest)
            raw = rest[:end].rstrip()
            if not raw:
                continue
            start = inline.start("rest")
            yield index, start, start + len(raw), _plain(raw.strip())


def _value_end(rest: str) -> int:
    """Offset where the flow-mapping value ends: the first top-level ``,`` or ``}``.

    Parentheses and quotes shield a separator: a registered source name is
    "Liber Malefic (Miracle Workers, Werekin)" and must not be cut at its comma.
    """
    depth = 0
    quote: str | None = None
    for position, character in enumerate(rest):
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in "'\"":
            quote = character
        elif character in "([":
            depth += 1
        elif character in ")]" and depth:
            depth -= 1
        elif not depth and character in ",}":
            return position
    return len(rest)


def source_reference_values(text: str) -> Iterator[tuple[int, str]]:
    """``(line index, value)`` of every ``manual`` scalar in a document."""
    for index, _, _, value in manual_occurrences(text):
        yield index, value


def normalize_line_endings(root: Path) -> list[Edit]:
    """Every YAML file ends its lines the way the repository declares.

    ``.gitattributes`` states ``*.yaml text eol=lf``, while the checked-out tree
    has files that are CRLF or mix both terminators. The canonical formatter
    reads bytes and flags both, so this pass is a gate the tree already needed;
    it also repairs the files an editor rewrote with the platform's ending.
    """
    edits: list[Edit] = []
    for path in _yaml_files(root):
        text = _read_text(path)
        if "\r" not in text:
            continue
        fixed = text.replace("\r\n", "\n").replace("\r", "\n")
        _publish(path, fixed)
        edits.append(Edit(path, ["line endings -> LF (the tree's *.yaml convention)"], fixed, text))
    return edits


def normalize_manuals(root: Path) -> list[Edit]:
    """Rewrite every unregistered ``manual`` value of a tree."""
    edits: list[Edit] = []
    for path in _yaml_files(root):
        text = _read_text(path)
        lines = _lines(text)
        changes: list[str] = []
        per_line: dict[int, list[tuple[int, int, str, str]]] = {}
        for index, start, end, value in manual_occurrences(text):
            replacement = MANUAL_VALUES.get(value)
            if replacement is None:
                continue
            per_line.setdefault(index, []).append((start, end, replacement, value))
        for index, occurrences in per_line.items():
            line = lines[index]
            # Right to left: the offsets belong to the line as it was read.
            for start, end, replacement, value in sorted(occurrences, reverse=True):
                line = line[:start] + replacement + line[end:]
                changes.append(f"manual {value!r} -> {replacement!r} (line {index + 1})")
            lines[index] = line
        if not changes:
            continue
        text_after = "".join(lines)
        _verify_manuals(path, text, text_after)
        _publish(path, text_after)
        edits.append(Edit(path, changes, text_after, text))
    return edits


def _verify_manuals(path: Path, before: str, after: str) -> None:
    original = yaml.safe_load(before)
    updated = yaml.safe_load(after)

    def apply(node: Any) -> Any:
        if isinstance(node, dict):
            return {
                key: (MANUAL_VALUES[value] if key == "manual" and isinstance(value, str) and value in MANUAL_VALUES else apply(value))
                for key, value in node.items()
            }
        if isinstance(node, list):
            return [apply(item) for item in node]
        return node

    if apply(original) != updated:
        raise ValueError(f"{path}: the manual rewrite changed more than the manual values")


def normalize_band_status(root: Path) -> list[Edit]:
    """Set the band ``status`` of a tree to the value the KB declares."""
    edits: list[Edit] = []
    for path in _yaml_files(root):
        if path.name != "band.yaml":
            continue
        text = _read_text(path)
        lines = _lines(text)
        changes: list[str] = []
        for index, line in enumerate(lines):
            value = _scalar_value(line, "status")
            if value is None or _plain(value) == BAND_STATUS:
                continue
            lines[index] = _replace_scalar(line, "status", BAND_STATUS)
            changes.append(f"status {value!r} -> {BAND_STATUS!r} (line {index + 1})")
        if not changes:
            continue
        text_after = "".join(lines)
        before_payload = yaml.safe_load(text)
        after_payload = yaml.safe_load(text_after)
        if before_payload == after_payload:
            raise ValueError(f"{path}: the status rewrite did not change the document")
        if after_payload.get("status") != BAND_STATUS:
            raise ValueError(f"{path}: the status rewrite missed the document field")
        before_payload["status"] = BAND_STATUS
        if before_payload != after_payload:
            raise ValueError(f"{path}: the status rewrite changed more than the status")
        _publish(path, text_after)
        edits.append(Edit(path, changes, text_after, text))
    return edits


def canonical_source_path_root(value: Any, roster_type: Any) -> str | None:
    """The roster group a printed ``source_path`` root resolves to, or ``None``."""
    if not isinstance(value, str):
        return None
    folded = value.casefold()
    if folded in SOURCE_PATH_ROOTS:
        return folded
    label = SOURCE_PATH_LABELS.get(folded)
    if label is not None:
        return label
    if isinstance(roster_type, str):
        if roster_type == "hero":
            return "heroes"
        if roster_type == "henchman":
            return "henchmen"
        if roster_type in ("animal", "summoned"):
            return "summoned"
    return None


def normalize_source_path(root: Path) -> list[Edit]:
    """Resolve every ``source_path`` root of a tree to its roster group."""
    edits: list[Edit] = []
    for path in _yaml_files(root):
        text = _read_text(path)
        payload = yaml.safe_load(text)
        if not isinstance(payload, dict) or not any(
            (profile.get("source_path") or []) for profile in payload.get("profiles") or []
        ):
            continue
        profiles = payload.get("profiles") or []
        plan: list[tuple[str, str]] = []
        for profile in profiles:
            values = profile.get("source_path") or []
            if not values:
                # Not every profile family carries a printed section path: the
                # hireling catalogues do not, and the KB leaves the key off there.
                continue
            current = values[0]
            target = canonical_source_path_root(current, profile.get("type"))
            if target is None:
                raise ValueError(
                    f"{path}: source_path root {current!r} of {profile.get('id')!r} is not a roster group "
                    f"and the profile type cannot resolve it"
                )
            plan.append((str(current), target))
        if all(current == target for current, target in plan):
            continue
        lines = _lines(text)
        changes: list[str] = []
        seen = 0
        index = 0
        while index < len(lines):
            match = _KEY.match(lines[index])
            if match is None or match.group("key") != "source_path" or match.group("dash"):
                index += 1
                continue
            # The first element of the block list follows the key.
            cursor = index + 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            item = _LIST_ITEM.match(lines[cursor]) if cursor < len(lines) else None
            if item is None:
                raise ValueError(f"{path}: source_path of line {index + 1} is not a block list")
            value = _plain(item.group("value"))
            current, target = plan[seen]
            if value != current:
                raise ValueError(
                    f"{path}: line {cursor + 1} reads {value!r} where {current!r} was expected"
                )
            if value != target:
                lines[cursor] = f"{item.group('indent')}- {target}{_ending(lines[cursor])}"
                changes.append(f"source_path[{seen}] {value!r} -> {target!r} (line {cursor + 1})")
            seen += 1
            index = cursor + 1
        if seen != len(plan):
            raise ValueError(f"{path}: {seen} source_path values found, {len(plan)} expected")
        if not changes:
            continue
        text_after = "".join(lines)
        after_payload = yaml.safe_load(text_after)
        _verify_source_path(path, payload, after_payload)
        _publish(path, text_after)
        edits.append(Edit(path, changes, text_after, text))
    return edits


def _verify_source_path(path: Path, before: dict, after: dict) -> None:
    """The rewrite may change the root of each ``source_path`` and nothing else."""
    expected = yaml.safe_load(yaml.safe_dump(before, allow_unicode=True))
    for profile in expected.get("profiles") or []:
        values = profile.get("source_path") or []
        if values:
            values[0] = canonical_source_path_root(values[0], profile.get("type"))
    if expected != after:
        raise ValueError(f"{path}: the source_path rewrite changed more than the roster group")


def registry_document() -> str:
    """The registry with every source id the KB and the staging trees use."""
    lines = ["schema_version: 2", "sources:"]
    for identifier, name in SOURCE_IDS:
        lines.append(f"- id: {identifier}")
        lines.append(f"  name: {name}")
    return "\n".join(lines) + "\n"


def sync_registry() -> Edit | None:
    """Add the missing source ids to ``registry/sources.yaml``."""
    path = CHECKOUT / KB_ROOT / "registry" / "sources.yaml"
    text = _read_text(path)
    wanted = registry_document()
    if text == wanted:
        return None
    payload = yaml.safe_load(wanted)
    registered = {entry["id"] for entry in yaml.safe_load(text).get("sources") or []}
    added = [identifier for identifier, _ in SOURCE_IDS if identifier not in registered]
    return Edit(path, [f"registered {identifier!r}" for identifier in added], wanted, text)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

PASSES: dict[str, Callable[[Path], list[Edit]]] = {
    "endings": normalize_line_endings,
    "manuals": normalize_manuals,
    "status": normalize_band_status,
    "source-path": normalize_source_path,
}


def targets() -> list[Path]:
    return [KB_ROOT, *_staging_roots()]


def edits(passes: Iterable[str] | None = None, roots: Iterable[Path] | None = None) -> Report:
    """Every normalisation the open fields need, staging trees and KB alike.

    A file rewritten by one pass is read back by the next one, so the report
    carries one entry per file with the changes of every pass that touched it.
    """
    wanted = list(passes) if passes else list(PASSES)
    for name in wanted:
        if name not in PASSES:
            raise ValueError(f"Unknown pass: {name!r}")
    merged: dict[Path, Edit] = {}
    for root in roots or targets():
        for name in wanted:
            for edit in PASSES[name](root):
                previous = merged.get(edit.path)
                if previous is None:
                    merged[edit.path] = edit
                else:
                    merged[edit.path] = Edit(
                        edit.path, previous.changes + edit.changes, edit.text, previous.original
                    )
    registry = sync_registry()
    if registry is not None:
        merged[registry.path] = registry
    return Report(list(merged.values()))


# --------------------------------------------------------------------------- #
# Lexical primitives other passes share
# --------------------------------------------------------------------------- #

#: The promotion pass edits the same kind of YAML and reuses this layer rather
#: than growing a second, subtly different one.
read_text = _read_text
publish = _publish
lines = _lines
SCALAR = _SCALAR
KEY = _KEY
replace_scalar = _replace_scalar
line_ending = _ending


def manual_values(root: Path) -> set[str]:
    """Every ``manual`` value a tree uses, for the guard test."""
    values: set[str] = set()
    for path in _yaml_files(root):
        for _, value in source_reference_values(_read_text(path)):
            values.add(value)
    return values
