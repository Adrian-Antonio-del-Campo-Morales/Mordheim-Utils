"""Pipeline guards over the knowledge base as a whole.

Each section keeps the contract of one former single-purpose file: name
normalization, the single ``effect`` prose key, one Spanish
translation per English text, canonical YAML formatting, the staged-binding
registry, and the canonical equipment absences/artefact locales.
"""
from __future__ import annotations

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
