"""external.test_2b_staging: guards for the isolated Grade 2b staging area.

The staging tree in ``sources/2B`` must never leak into the active knowledge
base, and every manifest row must stay consistent with the band packages on
disk. These tests pass while staging is empty (pre-discovery); they tighten
automatically as ``manifest.yaml`` and band packages appear.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "sources" / "2B"
KNOWLEDGE = ROOT / "sources" / "knowledge"
INGEST = ROOT / "tools" / "knowledge" / "ingest_2b.py"

BAND_DOCUMENTS = ("band.yaml", "profiles.yaml", "equipment-access.yaml", "special-rules.yaml")

STATUS_ORDER = (
    "discovered", "pdf-verified", "text-extracted", "modeled",
    "english-reviewed", "translated", "validated", "promotable",
)


def manifest_rows() -> list[dict]:
    path = STAGING / "manifest.yaml"
    if not path.exists():
        return []
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return document.get("bands") or []


def package_status() -> dict[str, str]:
    """Band package directory -> manifest status.

    A manifest row describes one source document; when that document prints more
    than one warband list, the row lists every package it produced under
    ``packages`` (defaulting to the row id itself).
    """
    out: dict[str, str] = {}
    for row in manifest_rows():
        status = str(row.get("status"))
        for package in row.get("packages") or [row.get("id")]:
            if package:
                out[str(package)] = status
    return out


def test_staging_is_isolated_from_active_kb() -> None:
    """sources/knowledge must not contain or reference the staging tree."""
    assert not (KNOWLEDGE / "2B").exists()
    for path in KNOWLEDGE.rglob("*.yaml"):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "sources/2B" not in text, f"active KB references staging: {path}"


def test_active_band_ids_do_not_collide_with_staging() -> None:
    """Any band modeled in staging must not overwrite an active band id."""
    staging_dirs = STAGING / "bands" / "mordheim"
    if not staging_dirs.exists():
        return
    active = {path.parent.name for path in (KNOWLEDGE / "bands" / "mordheim").glob("*/band.yaml")}
    for band_dir in staging_dirs.iterdir():
        if not band_dir.is_dir():
            continue
        assert band_dir.name not in active, f"staging band collides with active KB: {band_dir.name}"


def test_active_collection_count_is_unchanged() -> None:
    """The active mordheim collection must stay at 48 bands during staging."""
    count = len(list((KNOWLEDGE / "bands" / "mordheim").glob("*/band.yaml")))
    assert count == 48, f"active mordheim collection changed: {count} bands"


def test_staging_uses_the_same_document_contract() -> None:
    """Band packages claimed as modeled or beyond carry the four canonical docs.

    The manifest status is the source of truth: a directory may lag behind
    while another worker is transcribing, and an in-progress package is not
    an error until its manifest row claims 'modeled' or later.
    """
    rows = package_status()
    staging_dirs = STAGING / "bands" / "mordheim"
    if not staging_dirs.exists():
        return
    for band_dir in sorted(staging_dirs.iterdir()):
        if not band_dir.is_dir():
            continue
        status = rows.get(band_dir.name)
        if status not in {"modeled", "english-reviewed", "translated", "validated", "promotable"}:
            continue
        for document in BAND_DOCUMENTS:
            assert (band_dir / document).exists(), f"{band_dir.name}: missing {document}"


def test_every_staging_package_is_declared_by_a_manifest_row() -> None:
    """No band package may exist outside the manifest's declared rows."""
    declared = set(package_status())
    staging_dirs = STAGING / "bands" / "mordheim"
    if not staging_dirs.exists():
        return
    for band_dir in sorted(staging_dirs.iterdir()):
        if band_dir.is_dir():
            assert band_dir.name in declared, (
                f"{band_dir.name}: package is not declared by any manifest row "
                f"(add it to that row's 'packages')"
            )


def test_manifest_rows_are_well_formed() -> None:
    """Manifest rows have known statuses, unique ids, and blockers only when blocked."""
    rows = manifest_rows()
    if not rows:
        return
    seen: set[str] = set()
    for row in rows:
        band_id = str(row.get("id") or "")
        assert band_id, "manifest row without id"
        assert band_id not in seen, f"duplicate manifest id: {band_id}"
        seen.add(band_id)
        assert row.get("status") in STATUS_ORDER, f"{band_id}: unknown status {row.get('status')!r}"
        if row.get("status") != "discovered":
            assert row.get("sha256"), f"{band_id}: no sha256 despite status {row.get('status')}"
        if row.get("blockers"):
            assert row.get("status") not in {"validated", "promotable"}, (
                f"{band_id}: status {row.get('status')} must be blocker-free"
            )


def test_modeled_bands_have_consistent_references() -> None:
    """Roster, rule and equipment references inside a modeled band resolve.

    Like the document-contract test, this only applies to bands whose
    manifest row claims 'modeled' or beyond; in-progress packages are
    skipped while the transcribing worker is still writing.
    """
    rows = package_status()
    staging_dirs = STAGING / "bands" / "mordheim"
    if not staging_dirs.exists():
        return
    active_items = set()
    for path in (KNOWLEDGE / "catalog/items").glob("*.yaml"):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        active_items |= {
            str(item["id"]) for item in document.get("items") or ()
            if isinstance(item, dict) and item.get("id")
        }
    provisional_items = STAGING / "catalog/items"
    if provisional_items.exists():
        for path in provisional_items.rglob("*.yaml"):
            document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            active_items |= {
                str(item["id"]) for item in document.get("items") or ()
                if isinstance(item, dict) and item.get("id")
            }

    kb_rule_ids = set()
    for path in (KNOWLEDGE / "catalog/rules").glob("*.yaml"):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("rules", "conditions"):
            kb_rule_ids |= {
                str(rule["id"]) for rule in document.get(key) or ()
                if isinstance(rule, dict) and rule.get("id")
            }

    for band_dir in sorted(staging_dirs.iterdir()):
        if not band_dir.is_dir():
            continue
        status = rows.get(band_dir.name)
        if status not in {"modeled", "english-reviewed", "translated", "validated", "promotable"}:
            continue
        band = yaml.safe_load((band_dir / "band.yaml").read_text(encoding="utf-8")) or {}
        profiles_doc = yaml.safe_load((band_dir / "profiles.yaml").read_text(encoding="utf-8")) or {}
        rules_doc = yaml.safe_load((band_dir / "special-rules.yaml").read_text(encoding="utf-8")) or {}

        if band.get("grade") != "2b" or "2b" not in (band.get("categories") or []):
            raise AssertionError(f"{band_dir.name}: band.yaml must carry grade 2b / categories [2b]")
        if band.get("ruleset") != "mordheim":
            raise AssertionError(f"{band_dir.name}: ruleset must be mordheim")

        profile_ids = {str(p.get("id") or "") for p in profiles_doc.get("profiles") or ()}
        profile_ids.discard("")
        for member in (band.get("roster") or {}).get("members") or ():
            profile_id = str(member.get("profile_id") or "")
            assert profile_id in profile_ids, (
                f"{band_dir.name}: roster references unknown profile {profile_id!r}"
            )

        rule_ids = {str(r.get("id") or "") for r in rules_doc.get("rules") or ()}
        rule_ids.discard("")
        for owner in [band, *(band.get("variants") or ())]:
            for rule_id in owner.get("rule_ids") or ():
                assert rule_id in rule_ids, (
                    f"{band_dir.name}: rule_ids reference unknown rule {rule_id!r}"
                )
        for rule in rules_doc.get("rules") or ():
            if rule.get("rule_ref"):
                assert rule["rule_ref"] in kb_rule_ids, (
                    f"{band_dir.name}: rule {rule.get('id')!r} rule_ref {rule['rule_ref']!r} not in active KB"
                )
                continue
            assert rule.get("effect"), f"{band_dir.name}: rule {rule.get('id')!r} has no effect"
            for profile_id in (rule.get("applies_to") or {}).get("profile_ids") or ():
                assert profile_id in profile_ids, (
                    f"{band_dir.name}: rule {rule.get('id')!r} applies to unknown profile {profile_id!r}"
                )

        equipment_doc = (
            yaml.safe_load((band_dir / "equipment-access.yaml").read_text(encoding="utf-8")) or {}
        )
        for equipment_list in equipment_doc.get("equipment_lists") or ():
            list_id = str(equipment_list.get("id") or "?")
            for entry in equipment_list.get("items") or ():
                if not isinstance(entry, dict):
                    continue
                item_id = str(entry.get("item_id") or "")
                assert item_id in active_items, (
                    f"{band_dir.name}: equipment list {list_id!r} references "
                    f"unknown item {item_id!r}"
                )


def test_ingest_tool_validate_passes() -> None:
    """The staging tool's own validator agrees with these tests."""
    result = subprocess.run(
        [sys.executable, str(INGEST), "validate"],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )
    assert result.returncode == 0, f"ingest_2b validate failed:\n{result.stdout}\n{result.stderr}"
