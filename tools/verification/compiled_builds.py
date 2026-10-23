"""Frozen ``compile_fighter`` results keyed by their complete build (common loader).

Test preparations keep their original builders and post-compile transformations.
The compilation itself is replaced by a lookup in a frozen document; this module
is the only consumer-side reader of that document.

Interface (stable for fixtures and for the snapshot generator)
--------------------------------------------------------------

``build_request(build, root=None)``
    Canonical identity of a compilation: ``{"build": <all FighterBuild fields>,
    "root": <repository-relative root or None>}``.  It keeps every field, so
    ``None`` versus ``()`` and any other value difference stay distinct.
    Equality is canonical (``canonical_json``), so a tuple field and its JSON
    list are one request.  An internal root is stored as a normalized POSIX
    path relative to the repository, never as the checkout location; a root
    outside the repository raises ``CompiledBuildError``.

``build_key(build, root=None)``
    SHA-256 of the canonical request.  Generation and lookup both go through
    this identity; neither side re-implements nor post-processes it.

``load_builds(path) -> BuildSnapshots``
    Reads and validates a frozen document.  A missing file, an unknown schema or
    version, a mismatched entry key, a root that is not ``null`` or a normalized
    repository-relative path, or a mismatched document fingerprint raises
    ``CompiledBuildError``.

``BuildSnapshots.fighter(build, root=None) -> CompiledFighter``
    Returns the stored fighter for exactly that request, normalizing the root
    exactly as generation did.  ``snapshots.fighter`` is the drop-in replacement
    for the ``compile_fighter(build, root)`` callable passed to the original
    helpers; consumers pass the complete ``FighterBuild``.  An absent entry
    raises ``MissingCompiledBuild`` with its key; no build is compiled and no
    similar build is substituted.

``encode_entry(build, fighter, root=None)`` / ``encode_document(entries)``
    Generation side of the same format: ``(key, entry)`` and the canonical
    document.  Serialization is the existing codec (``canonical_json``,
    ``encode_compiled_fighter``); this module adds no second encoding system.

Document format (UTF-8 JSON, canonical, no timestamps)
------------------------------------------------------

::

    {
      "schema": "mordheim-compiled-builds",
      "schema_version": 1,
      "entries": {
        "<sha256 of the canonical request>": {
          "request": {"build": {...}, "root": "sources/knowledge"},
          "fighter": {...}                     # encode_compiled_fighter output
        }
      },
      "fingerprints": {"entries_sha256": "<sha256 of schema+version+entries>"}
    }

``request.root`` is ``null`` for the default root, ``"."`` for the repository
root itself, or a normalized POSIX path relative to the repository (for example
``"sources/knowledge"``).  The identity therefore does not depend on where the
checkout lives: a document generated in one copy resolves in another.
``root=None`` stays distinct from any explicit root, and two different internal
roots stay distinct.  A root outside the repository is rejected explicitly
rather than collapsed to a name or ignored, because it has no portable identity.
This module imports neither the construction compiler nor the knowledge base; a
missing entry is never compiled.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable
from typing import Mapping

from mordheim_core.models import CompiledFighter
from mordheim_core.models import FighterBuild
from tools.verification.compiled_cases import CompiledCaseError
from tools.verification.compiled_cases import canonical_json
from tools.verification.compiled_cases import decode_compiled_fighter
from tools.verification.compiled_cases import encode_compiled_fighter


SCHEMA = "mordheim-compiled-builds"
SCHEMA_VERSION = 1

#: The identity of an internal compilation root is relative to this checkout-independent root.
REPO_ROOT = Path(__file__).resolve().parents[2]

_DOCUMENT_FIELDS = frozenset({"schema", "schema_version", "entries", "fingerprints"})
_ENTRY_FIELDS = frozenset({"request", "fighter"})
_REQUEST_FIELDS = frozenset({"build", "root"})


class CompiledBuildError(ValueError):
    """A frozen build document, or one of its entries, is invalid."""

    def __init__(self, key: str, field: str, reason: str):
        self.key = key
        self.field = field
        self.reason = reason
        super().__init__(f"{key}: {field}: {reason}")


class MissingCompiledBuild(CompiledBuildError):
    """The requested compilation is not in the frozen document."""

    def __init__(self, key: str, request: Mapping[str, object], available: int):
        self.request = request
        self.available = available
        super().__init__(
            key, "entries",
            f"no frozen FighterBuild for this request; {available} entries available "
            "(nothing was compiled and no similar build was substituted)",
        )


def _fail(key: str, field: str, reason: str) -> None:
    raise CompiledBuildError(key, field, reason)


def _mapping(value: object, key: str, field: str) -> Mapping:
    if not isinstance(value, dict):
        _fail(key, field, f"expected an object, got {type(value).__name__}")
    return value


def _exact_keys(raw: Mapping, expected: frozenset[str], key: str, field: str) -> None:
    unknown = sorted(set(raw) - expected)
    missing = sorted(expected - set(raw))
    if unknown:
        _fail(key, field, "unknown field(s): " + ", ".join(unknown))
    if missing:
        _fail(key, field, "missing field(s): " + ", ".join(missing))


def _relative_root(path: Path) -> str:
    """A POSIX path relative to the repository, or an explicit error."""
    repository = os.path.normcase(os.fspath(Path(REPO_ROOT).resolve()))
    candidate = os.path.normcase(os.fspath(path))
    if candidate == repository:
        return "."
    prefix = repository.rstrip(os.sep) + os.sep
    if not candidate.startswith(prefix):
        raise CompiledBuildError(
            "<request>", "root",
            f"compilation root {os.fspath(path)!r} is outside the repository; "
            "only repository-internal roots have a portable identity",
        )
    return os.fspath(path)[len(prefix):].replace(os.sep, "/")


def _resolve_root(root) -> str | None:
    """Normalize a compilation root so its identity is checkout-independent."""
    if root is None:
        return None
    try:
        path = Path(root).resolve()
    except (TypeError, ValueError, OSError) as error:
        raise CompiledBuildError("<request>", "root", str(error)) from error
    return _relative_root(path)


def _stored_root(value, key: str) -> None:
    """A frozen root must be ``null`` or a normalized repository-relative path."""
    if value is None:
        return
    if not isinstance(value, str) or not value:
        _fail(key, "request.root", "expected a repository-relative path or null")
    if value == ".":
        return
    parts = value.split("/")
    if ("\\" in value or value.startswith("/") or len(value) > 1 and value[1] == ":"
            or any(part in ("", ".", "..") for part in parts)):
        _fail(key, "request.root", "expected a normalized repository-relative path")


def build_request(build: FighterBuild, root=None) -> dict[str, object]:
    """The complete, canonical identity of one compilation."""
    try:
        fields = asdict(build)
    except TypeError as error:
        raise CompiledBuildError("<request>", "build", str(error)) from error
    try:
        canonical_json(fields)
    except CompiledCaseError as error:
        raise CompiledBuildError("<request>", "build", error.reason) from error
    return {"build": fields, "root": _resolve_root(root)}


def build_key(build: FighterBuild, root=None) -> str:
    """The document key for this exact request."""
    return hashlib.sha256(
        canonical_json(build_request(build, root)).encode("utf-8")
    ).hexdigest()


def encode_entry(build: FighterBuild, fighter: CompiledFighter, root=None) -> tuple[str, dict]:
    """``(key, entry)`` for one frozen compilation."""
    request = build_request(build, root)
    return build_key(build, root), {
        "request": request,
        "fighter": encode_compiled_fighter(fighter),
    }


def _entries_fingerprint(entries: Mapping[str, Mapping]) -> str:
    return hashlib.sha256(canonical_json({
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "entries": entries,
    }).encode("utf-8")).hexdigest()


def encode_document(entries: Iterable[tuple[FighterBuild, CompiledFighter, object]]) -> dict:
    """Build the canonical document from ``(build, fighter, root)`` triples."""
    frozen: dict[str, dict] = {}
    for build, fighter, root in entries:
        key, entry = encode_entry(build, fighter, root)
        if key in frozen:
            _fail(key, "entries", "duplicate key")
        frozen[key] = entry
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "entries": frozen,
        "fingerprints": {"entries_sha256": _entries_fingerprint(frozen)},
    }


class BuildSnapshots:
    """Validated frozen builds; ``fighter()`` is the ``compile_fighter`` replacement."""

    def __init__(self, entries: Mapping[str, Mapping], *, path: str = "<document>"):
        self._entries = entries
        self.path = path

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._entries

    def fighter(self, build: FighterBuild, root=None) -> CompiledFighter:
        """Return exactly the stored fighter; never compile or approximate."""
        request = build_request(build, root)
        key = build_key(build, root)
        try:
            entry = self._entries[key]
        except KeyError:
            raise MissingCompiledBuild(key, request, len(self._entries)) from None
        return decode_compiled_fighter(entry["fighter"], key, "fighter")


def load_builds(path) -> BuildSnapshots:
    """Load and validate a frozen build document."""
    location = Path(path)
    try:
        text = location.read_text(encoding="utf-8")
    except OSError as error:
        raise CompiledBuildError("<document>", "path", f"cannot read {location}: {error}") from error
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise CompiledBuildError("<document>", "json", str(error)) from error
    data = _mapping(raw, "<document>", "document")
    _exact_keys(data, _DOCUMENT_FIELDS, "<document>", "document")
    if data["schema"] != SCHEMA:
        _fail("<document>", "schema", f"expected {SCHEMA!r}")
    if data["schema_version"] != SCHEMA_VERSION:
        _fail("<document>", "schema_version", f"expected {SCHEMA_VERSION}")
    raw_entries = _mapping(data["entries"], "<document>", "entries")
    entries: dict[str, Mapping] = {}
    for key, raw_entry in raw_entries.items():
        entry = _mapping(raw_entry, key, "entry")
        _exact_keys(entry, _ENTRY_FIELDS, key, "entry")
        request = _mapping(entry["request"], key, "request")
        _exact_keys(request, _REQUEST_FIELDS, key, "request")
        _stored_root(request["root"], key)
        expected = hashlib.sha256(canonical_json(request).encode("utf-8")).hexdigest()
        if expected != key:
            _fail(key, "request", "entry key does not match its request")
        if not isinstance(entry["fighter"], dict):
            _fail(key, "fighter", "expected an object")
        entries[key] = entry
    fingerprints = _mapping(data["fingerprints"], "<document>", "fingerprints")
    _exact_keys(fingerprints, frozenset({"entries_sha256"}), "<document>", "fingerprints")
    if fingerprints["entries_sha256"] != _entries_fingerprint(entries):
        _fail("<document>", "fingerprints", "stored fingerprint does not match the entries")
    return BuildSnapshots(entries, path=str(location))
