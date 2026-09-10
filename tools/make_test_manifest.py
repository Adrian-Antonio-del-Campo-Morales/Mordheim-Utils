"""Generate the desktop→web test traceability manifest.

web-test-migration-plan.md §Matriz: every applicable desktop test gets one
row with a web disposition (M/A/U/I/S/X), a web target, an owner and — for
exclusions — a documented reason. Rows are enumerated programmatically via
``pytest --collect-only`` so the manifest can never drift from the real
desktop net (1172+ cases), then classified by per-file family rules.

Determinism: output is byte-stable (sorted rows, no timestamps) so the
Python/TS gates can verify regeneration identity.

Usage:
    python tools/make_test_manifest.py                # write manifest
    python tools/make_test_manifest.py --stdout      # print instead
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "web" / "parity" / "campaign-test-manifest.json"

COLLECT_RE = re.compile(r"^(tests/[A-Za-z0-9_/]+\.py)::(.+)$")

# --- classification table (file basename → family rules) --------------------
# disposition: M domain TS | U UI React | I interop Py↔TS | S shared KB/contract
#              | X excluded (reason required)
FAMILY_RULES: dict[str, tuple[str, str, str]] = {
    # file basename: (disposition, desktop_category, owner)
    "test_advancement_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_audit_regressions.py": ("M", "domain-regression", "333333"),
    "test_battle_creation.py": ("M", "domain-sequence", "333333"),
    "test_campaign_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_dice_resolution.py": ("M", "domain-sequence", "333333"),
    "test_draft.py": ("M", "domain-sequence", "333333"),
    "test_economy_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_equipment_editor.py": ("M", "domain-sequence", "333333"),
    "test_exploration_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_extended_audit_regressions.py": ("M", "domain-regression", "333333"),
    "test_third_audit_regressions.py": ("M", "domain-regression", "333333"),
    "test_gui_interaction_regressions.py": ("U", "desktop-ui", "REPO REWORK 2"),
    "test_hire_eligibility.py": ("M", "domain-rule", "333333"),
    "test_injury_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_knowledge_port.py": ("S", "shared-kb", "Agent 0"),
    "test_malformed_save_matrix.py": ("S", "shared-contract", "Agent 0"),
    "test_out_of_action_tracking.py": ("M", "domain-rule", "333333"),
    "test_persistence.py": ("I", "interop-roundtrip", "Agent 0"),
    "test_post_battle_advancements.py": ("M", "domain-sequence", "333333"),
    "test_post_battle_engine.py": ("M", "domain-sequence", "333333"),
    "test_post_battle_resolution.py": ("M", "domain-sequence", "333333"),
    "test_rules_catalogue.py": ("S", "shared-kb", "Agent 0"),
    "test_undo.py": ("M", "domain-sequence", "333333"),
    "test_variable_prices_and_restrictions.py": ("M", "domain-rule", "333333"),
    "test_warband_pdf.py": ("X", "desktop-pdf", "nobody"),
}

PDF_REASON = (
    "PDF export has no web equivalent (plan §Alcance exclusion); web review/"
    "export semantics are covered by the U/A rows of the review flow"
)

# tests/ui files are all desktop Tkinter UI behaviour → U, except the
# Combat Lab / Tkinter-only files with no web equivalent (correction
# requested by REPO REWORK 2 in the coordination log, per plan §Alcance).
UI_DISPOSITION = ("U", "desktop-ui", "REPO REWORK 2")
UI_EXCLUSIONS: dict[str, tuple[str, str, str]] = {
    name: ("X", "combat-lab-or-tkinter-only", "nobody")
    for name in (
        "test_execution.py",        # imports mordheim_combat_lab
        "test_motta.py",            # imports mordheim_combat
        "test_catalogue.py",        # imports mordheim_core
        "test_workbooks.py",        # Combat Lab workbooks
        "test_free_selection.py",   # Combat Lab free selection
        "test_improvements.py",     # Combat Lab improvements
        "test_preferences.py",      # Tkinter preferences persistence
        "test_app_preferences.py",  # Tkinter app preferences
        "test_no_untranslated_literals.py",  # Tkinter STRINGS scan
    )
}
UI_EXCLUSION_REASON = "Combat Lab / Tkinter-only, no web equivalent (plan §Alcance exclusion)"


def _family(file: str) -> str:
    name = Path(file).name
    if file.startswith("tests/ui/"):
        return name.removesuffix(".py").removesuffix("_regressions").removesuffix("test_")
    base = name.removesuffix(".py").removeprefix("test_")
    for suffix in ("_sequence_matrix", "_matrix", "_regressions"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base


def _web_target(disposition: str, file: str) -> str | None:
    fam = _family(file)
    if disposition == "M":
        return f"packages/typescript/domain/campaign/{fam}.test.ts"
    if disposition == "U":
        return f"apps/warband-manager-web/src/features/campaign/{fam}.test.tsx"
    if disposition == "I":
        return f"tests/web/parity/{fam}_interop_test.py"
    if disposition == "S":
        return f"tests/web/parity/vectors/{fam}.json"
    return None  # X


def collect_desktop_tests() -> list[tuple[str, str]]:
    """Enumerate (file, test_id) for the desktop campaign + UI nets."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/campaign", "tests/ui",
         "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    pairs: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        m = COLLECT_RE.match(line.strip())
        if m:
            pairs.append((m.group(1).replace("\\", "/"), m.group(2)))
    if not pairs:
        raise SystemExit("pytest --collect-only returned no tests; aborting")
    return sorted(pairs)


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for file, test in collect_desktop_tests():
        basename = Path(file).name
        if file.startswith("tests/ui/"):
            exclusion = UI_EXCLUSIONS.get(basename)
            if exclusion is not None:
                disposition, category, owner = exclusion
                reason = UI_EXCLUSION_REASON
            else:
                disposition, category, owner = UI_DISPOSITION
                reason = None
        else:
            rule = FAMILY_RULES.get(basename)
            if rule is None:
                raise SystemExit(
                    f"unclassified desktop test file: {file} — add it to "
                    f"FAMILY_RULES in tools/make_test_manifest.py"
                )
            disposition, category, owner = rule
            reason = PDF_REASON if disposition == "X" else None
        rows.append({
            "source_file": file,
            "source_test": test,
            "behavior_id": f"desktop.{_family(file)}",
            "desktop_category": category,
            "web_disposition": disposition,
            "web_target": _web_target(disposition, file),
            "owner": owner,
            "status": "pending",
            "parity_vector": None,
            "exclusion_reason": reason,
        })
    rows.sort(key=lambda r: (r["source_file"], r["source_test"]))
    return rows


def build_manifest() -> dict:
    rows = build_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["web_disposition"]] = counts.get(row["web_disposition"], 0) + 1
    return {
        "plan": "web-test-migration-plan.md",
        "generated_by": "tools/make_test_manifest.py",
        "deterministic": True,
        "sources": ["tests/campaign", "tests/ui"],
        "counts": dict(sorted(counts.items())),
        "total": len(rows),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout", action="store_true", help="print JSON instead of writing the manifest")
    args = parser.parse_args()
    manifest = build_manifest()
    text = json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
    if args.stdout:
        sys.stdout.write(text)
        return 0
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {MANIFEST_PATH.relative_to(ROOT)} ({manifest['total']} rows, counts={manifest['counts']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
