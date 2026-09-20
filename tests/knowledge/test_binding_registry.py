"""CI gate: a staged warband may not introduce an unregistered binding id.

The KB's binding vocabulary is whatever the active KB bands and the mechanics
catalogue declare. A staged rule whose ``binding.id`` is not in that vocabulary
is either a mistake (a typo, or a KB binding under a new name) or a genuinely
new mechanic — and a genuinely new mechanic must be declared, with its English
definition and Spanish translation, in ``registry/bindings.yaml`` before it can
ship. This gate enforces exactly that, so the registry cannot silently lag
behind the staging trees.

It also keeps the registry honest: an entry that resolves to nothing, that no
staged rule actually uses, or that the KB has since absorbed (promotion) fails
instead of rotting.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "sources" / "knowledge"
REGISTRY = KB / "registry" / "bindings.yaml"
TREES = ("2A", "2B")
ENTRY_KEYS = {"id", "kind", "status", "definition", "definition_i18n", "introduced_by",
              "source", "kb_equivalents_checked", "notes"}


def _docs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [d for d in yaml.safe_load_all(handle) if isinstance(d, dict)]


def _binding_ids(paths: list[str]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        for doc in _docs(Path(path)):
            for rule in doc.get("rules") or []:
                for effect in (rule.get("runtime") or {}).get("effects") or []:
                    binding = effect.get("binding") if isinstance(effect, dict) else None
                    if isinstance(binding, dict) and binding.get("id"):
                        ids.add(str(binding["id"]))
    return ids


def kb_binding_ids() -> set[str]:
    """Binding ids the active KB already uses (bands + mechanics catalogue)."""
    ids = _binding_ids(sorted(glob.glob(str(KB / "bands" / "*" / "*" / "special-rules.yaml"))))
    for path in glob.glob(str(KB / "catalog" / "mechanics" / "*.yaml")):
        for doc in _docs(Path(path)):
            for entry in doc.get("mechanics") or []:
                if isinstance(entry, dict) and entry.get("id"):
                    ids.add(str(entry["id"]))
    return ids


def staged_bindings() -> list[dict]:
    """Every (band, rule, binding id) a staged tree declares."""
    out: list[dict] = []
    for tree in TREES:
        pattern = str(ROOT / "sources" / tree / "bands" / "*" / "*" / "special-rules.yaml")
        for path in sorted(glob.glob(pattern)):
            band = os.path.basename(os.path.dirname(path))
            for doc in _docs(Path(path)):
                for rule in doc.get("rules") or []:
                    for effect in (rule.get("runtime") or {}).get("effects") or []:
                        binding = effect.get("binding") if isinstance(effect, dict) else None
                        if isinstance(binding, dict) and binding.get("id"):
                            out.append({"tree": tree, "band": band,
                                        "rule": str(rule.get("id")),
                                        "binding": str(binding["id"]),
                                        "kind": str(binding.get("kind"))})
    return out


def load_registry() -> dict[str, dict]:
    assert REGISTRY.exists(), (
        f"{REGISTRY.relative_to(ROOT)} is missing; staged bindings need a registry to resolve against"
    )
    entries = {}
    for doc in _docs(REGISTRY):
        for entry in doc.get("bindings") or []:
            if isinstance(entry, dict) and entry.get("id"):
                entries[str(entry["id"])] = entry
    return entries


def binding_kinds() -> set[str]:
    """The binding-kind vocabulary, read from runtime-schema wherever it nests."""
    schema_doc = _docs(KB / "registry" / "runtime-schema.yaml")[0]
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "binding_kinds" and isinstance(value, list):
                    found.update(str(item) for item in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema_doc)
    return found


def test_registry_is_well_formed() -> None:
    kinds = binding_kinds()
    for binding_id, entry in load_registry().items():
        missing = ENTRY_KEYS - set(entry)
        assert not missing, f"{binding_id}: registry entry is missing {sorted(missing)}"
        assert entry["kind"] in kinds, (
            f"{binding_id}: kind {entry['kind']!r} is not a runtime-schema binding kind {sorted(kinds)}"
        )
        assert str(entry["definition"]).strip(), f"{binding_id}: empty definition"
        spanish = (entry["definition_i18n"] or {}).get("es")
        assert spanish and str(spanish).strip(), f"{binding_id}: definition_i18n.es is required"
        assert entry["kb_equivalents_checked"], (
            f"{binding_id}: kb_equivalents_checked must record the KB bindings compared"
        )


def test_every_staged_binding_is_registered() -> None:
    registered = set(load_registry())
    known = kb_binding_ids() | registered
    unregistered = sorted({(row["tree"], row["band"], row["rule"], row["binding"])
                           for row in staged_bindings() if row["binding"] not in known})
    assert not unregistered, (
        "staged rules use binding ids that are neither used by the KB nor declared in "
        "sources/knowledge/registry/bindings.yaml:\n"
        + "\n".join(f"  {tree}/{band} {rule}: {binding}" for tree, band, rule, binding in unregistered)
        + "\nRegister the binding (id, kind, status, definition, definition_i18n.es, "
          "introduced_by, source, kb_equivalents_checked) or reuse the KB's own id."
    )


def test_registry_entries_resolve_and_are_not_stale() -> None:
    duplicates = [row for row in staged_bindings() if row["binding"] in load_registry()]
    kb_ids = kb_binding_ids()
    for binding_id, entry in load_registry().items():
        introduced = entry["introduced_by"] or {}
        tree, band, rule = introduced.get("tree"), introduced.get("band"), introduced.get("rule")
        package = ROOT / "sources" / str(tree) / "bands" / "mordheim" / str(band) / "special-rules.yaml"
        if package.exists():
            rule_ids = {str(r.get("id")) for doc in _docs(package) for r in doc.get("rules") or []}
            assert rule in rule_ids, (
                f"{binding_id}: introduced_by.rule {rule!r} does not exist in {band}"
            )
            assert any(row["binding"] == binding_id and row["band"] == band for row in duplicates), (
                f"{binding_id}: registered for {band} but that package no longer uses the binding"
            )
        assert binding_id not in kb_ids or entry.get("status") != "pending-promotion", (
            f"{binding_id}: the KB already uses this binding; retire the registry entry "
            f"(promotion absorbed it)"
        )
