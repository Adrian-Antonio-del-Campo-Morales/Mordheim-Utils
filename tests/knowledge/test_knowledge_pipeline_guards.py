"""Pipeline guards over the knowledge base as a whole.

Each section keeps the contract of one former single-purpose file: name
normalization, the single ``effect`` prose key, one Spanish
translation per English text, canonical YAML formatting, the staged-binding
registry, and the canonical equipment absences/artefact locales.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = ROOT / "sources" / "knowledge"
CAMPAIGN = KB_ROOT / "catalog" / "campaign" / "exploration-and-income.yaml"


# ---------------------------------------------------------------------------
# Capitalization policy
# ---------------------------------------------------------------------------
def test_kb_names_are_normalized() -> None:
    tool = ROOT / "tools" / "knowledge" / "maintenance" / "normalize_names.py"
    result = subprocess.run(
        [sys.executable, str(tool), "--check", str(KB_ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        "normalize_names --check reported files needing normalization:\n"
        + (result.stdout or result.stderr)
    )


# ---------------------------------------------------------------------------
# Rule prose has exactly one key: ``effect``
# ---------------------------------------------------------------------------
def _keys(node) -> set:
    if isinstance(node, dict):
        result = set(node)
        for value in node.values():
            result |= _keys(value)
        return result
    if isinstance(node, list):
        result = set()
        for value in node:
            result |= _keys(value)
        return result
    return set()


def test_no_summary_key_survives_in_the_knowledge_base() -> None:
    offenders: list[str] = []
    for path in sorted(KB_ROOT.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if document is None:
            continue
        if "summary" in _keys(document):
            offenders.append(path.relative_to(KB_ROOT).as_posix())
    assert offenders == [], (
        "the rule-prose key is `effect`; these files still carry a `summary` "
        f"key: {offenders}"
    )


# ---------------------------------------------------------------------------
# One English text maps to one Spanish text
# ---------------------------------------------------------------------------
FIELD_FAMILIES = (
    ("effect", "effect_i18n"),
    ("note", "note_i18n"),
    ("name", "name_i18n"),
)


def _normalize(text: str) -> str:
    """Collapse whitespace so folded YAML scalars compare equal."""
    return " ".join(str(text).split())


class _FamilyTracker:
    """Collects ES renderings per normalized EN text for one field family."""

    def __init__(self, field: str, i18n_field: str) -> None:
        self.field = field
        self.i18n_field = i18n_field
        self.en_to_es: dict[str, set[str]] = defaultdict(set)
        self.en_translated: dict[str, str] = {}
        self.en_untranslated: dict[str, str] = {}
        self.findings: list[str] = []

    def observe(self, node: dict, origin: str) -> None:
        en = node.get(self.field)
        if not isinstance(en, str) or not en:
            return
        key = _normalize(en)
        label = node.get("id") or node.get("name") or "?"
        i18n = node.get(self.i18n_field) if isinstance(node.get(self.i18n_field), dict) else None
        es = i18n.get("es") if i18n else None
        if isinstance(es, str) and es:
            es_value = _normalize(es)
            seen = self.en_to_es[key]
            if es_value not in seen:
                if seen:
                    self.findings.append(
                        f"{origin} ({label}): English {self.field} {key[:90]!r} already "
                        f"translated as {sorted(seen)[0][:90]!r} — this copy uses {es_value[:90]!r}"
                    )
                seen.add(es_value)
            self.en_translated.setdefault(key, f"{origin} ({label})")
            self.en_untranslated.pop(key, None)
        else:
            if key in self.en_translated:
                self.findings.append(
                    f"{origin} ({label}): English {self.field} {key[:90]!r} has no "
                    f"{self.i18n_field}.es while {self.en_translated[key]} translates it"
                )
            else:
                self.en_untranslated.setdefault(key, f"{origin} ({label})")


def test_same_english_text_always_gets_the_same_spanish_translation() -> None:
    trackers = [_FamilyTracker(field, i18n_field) for field, i18n_field in FIELD_FAMILIES]

    def walk(node, origin: str) -> None:
        if isinstance(node, dict):
            for tracker in trackers:
                tracker.observe(node, origin)
            for value in node.values():
                walk(value, origin)
        elif isinstance(node, list):
            for item in node:
                walk(item, origin)

    for kb_file in sorted(KB_ROOT.rglob("*.yaml")):
        doc = yaml.safe_load(kb_file.read_text(encoding="utf-8"))
        if doc is None:
            continue
        walk(doc, str(kb_file.relative_to(KB_ROOT)))

    findings = [finding for tracker in trackers for finding in tracker.findings]
    assert not findings, (
        f"{len(findings)} inconsistent translation(s) "
        "(same English text, different or missing Spanish):\n" + "\n".join(findings)
    )


# ---------------------------------------------------------------------------
# Canonical YAML formatting
# ---------------------------------------------------------------------------
LONG_LINE = (
    "The banished Seer may not be hired by any warband whose current roster already "
    "holds a Hired Sword of the Elven kind, and the pack keeps both."
)


def test_yaml_formatting_is_canonical() -> None:
    tool = ROOT / "tools" / "knowledge" / "maintenance" / "format_yaml.py"
    assert KB_ROOT.is_dir(), "Canonical KB directory is missing"
    result = subprocess.run(
        [sys.executable, str(tool), "--check", str(KB_ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        "format_yaml --check failed on knowledge:\n" + (result.stdout or result.stderr)
    )
    for line in (result.stdout or "").splitlines():
        if line.startswith("WARN ") and ": non-LF line endings " in line:
            warnings.warn(line, UserWarning)
    summary = (result.stdout or "").strip().splitlines()[-1]
    assert "0 would change" in summary, (
        "Canonical YAML needs reformatting "
        f"(run: python tools/knowledge/maintenance/format_yaml.py --write {KB_ROOT.relative_to(ROOT)}):\n"
        + (result.stdout or result.stderr)
    )


def run_tool(*arguments: str) -> subprocess.CompletedProcess:
    tool = ROOT / "tools" / "knowledge" / "maintenance" / "format_yaml.py"
    return subprocess.run(
        [sys.executable, str(tool), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


@pytest.mark.parametrize("ending", ["\r\n", "\r", "mixed"])
@pytest.mark.parametrize("other_change", [False, True])
def test_line_endings_warn_without_hiding_other_formatting(tmp_path: Path, ending: str, other_change: bool) -> None:
    path = tmp_path / "endings.yaml"
    document = "id: example\neffect: A short effect.\n"
    original = document.replace("\n", "\r\n", 1) if ending == "mixed" else document.replace("\n", ending)
    if other_change:
        original = original.replace("id: example", "id: example  ")
    path.write_bytes(original.encode("utf-8"))

    checked = run_tool("--check", str(path))
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert "WARN " in checked.stdout and ": non-LF line endings " in checked.stdout
    assert f"{int(other_change)} would change" in checked.stdout
    assert path.read_bytes() == original.encode("utf-8")

    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr
    assert path.read_bytes() == document.encode("utf-8")
    assert "0 would change" in run_tool("--check", str(path)).stdout


def test_a_folded_block_written_as_one_line_is_rewrapped(tmp_path: Path) -> None:
    path = tmp_path / "staged.yaml"
    path.write_text(
        "catalog: campaign-magic\n"
        "lores:\n"
        "  - id: lore.fire\n"
        "    effect: >-\n"
        f"      {LONG_LINE}\n"
        "    effect_i18n:\n"
        "      es: >-\n"
        f"        {LONG_LINE}\n",
        encoding="utf-8",
        newline="\n",
    )
    before = yaml.safe_load(path.read_text(encoding="utf-8"))

    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr

    text = path.read_text(encoding="utf-8")
    assert max(len(line) for line in text.splitlines()) <= 100
    assert yaml.safe_load(text) == before
    assert "0 would change" in run_tool("--check", str(path)).stdout


def test_a_folded_block_keeps_paragraphs_when_wrapped(tmp_path: Path) -> None:
    path = tmp_path / "paragraphs.yaml"
    document = (
        "lores:\n"
        "  - id: lore.fire\n"
        "    effect: >-\n"
        f"      {LONG_LINE}\n"
        "\n"
        "      A second paragraph the block keeps apart.\n"
    )
    path.write_text(document, encoding="utf-8", newline="\n")

    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr
    formatted = path.read_text(encoding="utf-8")
    assert yaml.safe_load(formatted) == yaml.safe_load(document)
    assert max(map(len, formatted.splitlines())) <= 120
    assert "0 would change" in run_tool("--check", str(path)).stdout


@pytest.mark.parametrize("document", [
    f"notes: {LONG_LINE}\n",
    f"notes_i18n:\n  es: {LONG_LINE}\n",
    f"notes:\n- {LONG_LINE}\n",
    f"effect_i18n: {{es: '{LONG_LINE}'}}\n",
    f'notes_i18n:\n  es: "{LONG_LINE}      preserved spaces\\nAnother paragraph."\n',
    f"binding: {{kind: profile, parameters: {{description: '{LONG_LINE}', enabled: true}}}}\n",
])
def test_remaining_long_yaml_values_are_wrapped_without_changing_data(tmp_path: Path, document: str) -> None:
    path = tmp_path / "long-values.yaml"
    path.write_bytes(document.encode("utf-8"))
    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr
    formatted = path.read_text(encoding="utf-8")
    assert yaml.safe_load(formatted) == yaml.safe_load(document)
    assert max(map(len, formatted.splitlines())) <= 120
    assert "0 would change" in run_tool("--check", str(path)).stdout


def test_wrapping_preserves_anchors_aliases_and_comments(tmp_path: Path) -> None:
    document = (
        f"original: &prose '{LONG_LINE}'\n"
        "copy: *prose\n"
        "settings: {enabled: true, # Keep this comment.\n"
        f"  description: '{LONG_LINE}'}}\n"
        f"notes: {LONG_LINE} # Keep this comment too.\n"
    )
    path = tmp_path / "comments.yaml"
    path.write_bytes(document.encode("utf-8"))
    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr
    formatted = path.read_text(encoding="utf-8")
    assert yaml.safe_load(formatted) == yaml.safe_load(document)
    assert "&prose" in formatted and "*prose" in formatted
    assert "# Keep this comment." in formatted
    assert "# Keep this comment too." in formatted


# ---------------------------------------------------------------------------
# Staged-binding registry
# ---------------------------------------------------------------------------
REGISTRY = KB_ROOT / "registry" / "bindings.yaml"
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
    ids = _binding_ids(sorted(glob.glob(str(KB_ROOT / "bands" / "*" / "*" / "special-rules.yaml"))))
    for path in glob.glob(str(KB_ROOT / "catalog" / "mechanics" / "*.yaml")):
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
    schema_doc = _docs(KB_ROOT / "registry" / "runtime-schema.yaml")[0]
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


# ---------------------------------------------------------------------------
# Canonical equipment absences and artefact locales
# ---------------------------------------------------------------------------
ABSENT_ITEM_IDS = frozenset({
    "ancestral_claw", "anointed_bolts", "carronade",
    "carronade_cannonball", "carronade_chain", "carronade_grapeshot",
    "dispelling_scroll", "feather_headdress", "hochland_long_rifle",
    "horned_rat_amulet", "icon_of_manann", "jungle_roast", "magic_tattoo",
    "magic_tattoos", "pirate_flag", "poison_darts", "poisoned_darts",
    "sacrifice_dagger", "scourge", "shrunken_head", "spider_amulet", "whip",
})

MAGICAL_ARTEFACTS = {
    "campaign.magical-artefact.boots-and-rope-of-pieter": "Las Botas y la Cuerda de Pieter",
    "campaign.magical-artefact.count-of-ventimiglias-misericordia": "La Misericordia del Conde de Ventimiglia",
    "campaign.magical-artefact.attlas-plate-mail": "Coraza de Placas de Att'la",
    "campaign.magical-artefact.bow-of-seeking": "Arco Buscador",
    "campaign.magical-artefact.executioners-hood": "Capucha del Verdugo",
    "campaign.magical-artefact.all-seeing-eye-of-numas": "Ojo que Todo lo Ve de Numas",
}


def _walk_rows(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_rows(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_rows(value)


def _kb_items() -> dict[str, dict]:
    items: dict[str, dict] = {}
    for path in sorted((KB_ROOT / "catalog" / "items").glob("*.yaml")):
        for row in _walk_rows(yaml.safe_load(path.read_text(encoding="utf-8"))):
            if isinstance(row.get("id"), str):
                items.setdefault(row["id"], row)
    return items


def test_canonical_absence_is_real() -> None:
    items = _kb_items()
    missing = sorted(ABSENT_ITEM_IDS - set(items))
    assert not missing, f"rows not found in the canonical KB: {missing}"

    for item_id in sorted(ABSENT_ITEM_IDS):
        row = items[item_id]
        assert row.get("combat_status") == "out_of_scope", f"{item_id} is no longer out_of_scope"
        assert not row.get("effect") and not row.get("effect_i18n"), (
            f"{item_id} now publishes an effect: the specific absence notice must be "
            "replaced by the real description"
        )


def test_magical_artefacts_publish_both_locales() -> None:
    rows = {
        row["id"]: row
        for row in _walk_rows(yaml.safe_load(CAMPAIGN.read_text(encoding="utf-8")))
        if isinstance(row.get("id"), str)
    }
    for artefact_id, spanish in MAGICAL_ARTEFACTS.items():
        row = rows.get(artefact_id)
        assert row, f"{artefact_id} missing from the campaign catalogue"
        assert row.get("result_i18n", {}).get("es") == spanish, f"{artefact_id} Spanish name"
        assert row.get("effect"), f"{artefact_id} English effect"
        assert row.get("effect_i18n", {}).get("es"), f"{artefact_id} Spanish effect"
