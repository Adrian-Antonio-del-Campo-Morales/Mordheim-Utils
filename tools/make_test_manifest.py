"""Generate the desktop→web test traceability manifest.

Every applicable desktop test gets one
row with a web disposition (M/A/U/I/S/X), a web target, an owner and — for
exclusions — a documented reason. Rows are enumerated programmatically via
``pytest --collect-only`` so the manifest can never drift from the current
desktop campaign and UI test net, then classified by per-file family rules.

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
    "test_gui_interaction_regressions.py": ("U", "desktop-ui", "desktop-web-parity"),
    "test_hire_eligibility.py": ("M", "domain-rule", "333333"),
    "test_injury_sequence_matrix.py": ("M", "domain-sequence", "333333"),
    "test_knowledge_port.py": ("S", "shared-kb", "shared-parity"),
    "test_malformed_save_matrix.py": ("S", "shared-contract", "shared-parity"),
    "test_out_of_action_tracking.py": ("M", "domain-rule", "333333"),
    "test_persistence.py": ("I", "interop-roundtrip", "shared-parity"),
    "test_post_battle_advancements.py": ("M", "domain-sequence", "333333"),
    "test_post_battle_engine.py": ("M", "domain-sequence", "333333"),
    "test_post_battle_resolution.py": ("M", "domain-sequence", "333333"),
    "test_rules_catalogue.py": ("S", "shared-kb", "shared-parity"),
    "test_undo.py": ("M", "domain-sequence", "333333"),
    "test_variable_prices_and_restrictions.py": ("M", "domain-rule", "333333"),
    "test_warband_pdf.py": ("X", "desktop-pdf", "nobody"),
}

PDF_REASON = (
    "PDF export has no desktop/web one-to-one parity requirement; web review/"
    "export semantics are covered by the U/A rows of the review flow"
)

# These desktop interactions have no one-to-one browser equivalent yet. They
# remain traceable, but cannot honestly be marked implemented by a React test.
UI_PARTIAL_FOLLOW_UP = (
    "Port each applicable browser interaction to a real React seam, or record "
    "a product-approved exclusion for the Tkinter-only interaction."
)

IMPLEMENTED_UI_TESTS: dict[tuple[str, str], str] = {
    ("tests/campaign/test_gui_interaction_regressions.py", test): "apps/warband-manager-web/src/architecture/product-app-session.test.tsx"
    for test in (
        "test_close_application_respects_unsaved_decision[False]",
        "test_close_application_respects_unsaved_decision[True]",
        "test_failed_save_does_not_mark_clean",
        "test_save_and_close_stays_when_save_cancelled[None]",
        "test_save_and_close_stays_when_save_cancelled[saved1]",
    )
}
IMPLEMENTED_UI_TESTS.update({
    ("tests/campaign/test_gui_interaction_regressions.py", test):
        "apps/warband-manager-web/src/architecture/product-app-session.test.tsx"
    for test in (
        "test_loading_same_file_after_save_reads_fresh_contents",
        "test_unsaved_guard[False-None-True]",
        "test_unsaved_guard[None-None-False]",
        "test_unsaved_guard[True-None-False]",
        "test_unsaved_guard[True-saved-True]",
    )
})
IMPLEMENTED_UI_TESTS[(
    "tests/campaign/test_gui_interaction_regressions.py",
    "test_dirty_includes_battle_draft_but_not_navigation",
)] = "packages/typescript/application/campaign/service.test.ts"
IMPLEMENTED_UI_TESTS.update({
    ("tests/campaign/test_variable_prices_and_restrictions.py", test):
        "packages/typescript/domain/campaign/kernel/hireling-hire.test.ts"
    for test in (
        "test_variable_hiring_fee_is_parsed_and_needs_a_roll",
        "test_variable_hiring_fee_charges_base_plus_roll",
        "test_variable_hiring_fee_rejects_rolls_below_the_dice_count",
    )
})
IMPLEMENTED_UI_TESTS.update({
    ("tests/campaign/test_gui_interaction_regressions.py", test):
        "packages/typescript/application/campaign/features/searches/search-workflow.test.ts"
    for test in (
        "test_failed_rare_purchase_keeps_search_available",
        "test_rare_search_cannot_be_consumed_twice",
    )
})
IMPLEMENTED_UI_TESTS.update({
    ("tests/ui/test_ui_i18n.py", test):
        "apps/warband-manager-web/src/features/campaign/ui_i18n.test.ts"
    for test in (
        "test_default_locale_is_english_and_env_override_is_read",
        "test_english_locale_renders_keys_byte_identical",
        "test_every_catalogue_key_translates_in_spanish",
        "test_post_battle_chrome_translates_under_spanish",
        "test_translated_strings_have_a_spanish_entry_and_english_is_the_key",
        "test_unknown_keys_return_the_english_key_itself",
        "test_unsupported_locale_keeps_the_current_selection",
    )
})
IMPLEMENTED_UI_TESTS[(
    "tests/campaign/test_post_battle_engine.py",
    "test_hire_conditional_requires_acceptance_roll",
)] = "packages/typescript/domain/campaign/kernel/hireling-hire.test.ts"
IMPLEMENTED_UI_TESTS.update({
    ("tests/campaign/test_gui_interaction_regressions.py", test):
        "apps/warband-manager-web/src/features/economy/ManualCorrectionsPanel.test.tsx"
    for test in (
        "test_numeric_input_accepts_integers[ 2 -2]",
        "test_numeric_input_accepts_integers[-3--3]",
        "test_numeric_input_accepts_integers[0-0]",
        "test_numeric_input_rejects_invalid_raw_values[1.5]",
        "test_numeric_input_rejects_invalid_raw_values[True]",
        "test_numeric_input_rejects_invalid_raw_values[]",
        "test_numeric_input_rejects_invalid_raw_values[abc]",
        "test_resource_form_reports_invalid_input_without_mutation",
    )
})
IMPLEMENTED_UI_TESTS[(
    "tests/campaign/test_gui_interaction_regressions.py",
    "test_invalid_preview_keeps_last_battle_draft",
)] = "packages/typescript/application/campaign/service.test.ts"

# tests/ui files are desktop Tkinter UI behaviour → U, except the
# Combat Lab / Tkinter-only files with no web equivalent.
UI_DISPOSITION = ("U", "desktop-ui", "desktop-web-parity")
UI_EXCLUSIONS: dict[str, tuple[str, str, str]] = {
    name: ("X", "combat-lab-or-tkinter-only", "nobody")
    for name in (
        "test_execution.py",        # imports mordheim_combat_lab
        "test_motta.py",            # imports mordheim_combat
        "test_catalogue.py",        # imports mordheim_core
        "test_workbooks.py",        # Combat Lab workbooks
        "test_free_selection.py",   # Combat Lab free selection
        "test_improvements.py",     # Combat Lab improvements
        "test_checklist_popover.py", # mordheim_combat_lab Tkinter widget
        "test_choice_widgets.py",   # mordheim_combat_lab Tkinter ChoiceBox
        "test_editors_catalogue_sweep.py", # Combat Lab fighter editor selectors
        "test_weapons_tab.py",      # Combat Lab weapon analysis UI
        "test_preferences.py",      # Tkinter preferences persistence
        "test_app_preferences.py",  # Tkinter app preferences
        "test_no_untranslated_literals.py",  # Tkinter STRINGS scan
    )
}
UI_EXCLUSION_REASON = "Combat Lab / Tkinter-only, no web equivalent"

INDIVIDUAL_EXCLUSIONS: dict[tuple[str, str], str] = {
    (
        "tests/campaign/test_gui_interaction_regressions.py",
        "test_cancelled_load_keeps_state_path_and_undo",
    ): "Browser imports create isolated in-memory sessions; they never replace a file-backed active campaign or own a persistent path.",
    (
        "tests/campaign/test_gui_interaction_regressions.py",
        "test_ctrl_z_in_text_field_does_not_undo_campaign",
    ): "Browser text-field undo is native and the web application registers no competing global Ctrl+Z handler.",
    (
        "tests/campaign/test_gui_interaction_regressions.py",
        "test_modal_returns_grab_to_previous_editor",
    ): "Tkinter grab ownership has no browser equivalent; web dialogs use native focus semantics.",
    (
        "tests/campaign/test_gui_interaction_regressions.py",
        "test_renaming_active_save_updates_next_save",
    ): "The web keeps in-memory sessions and has no persistent file path to rename.",
}

# Consolidated/renamed targets that cannot be derived from the desktop filename.
TARGET_OVERRIDES = {
    "test_campaign_sequence_matrix.py": "packages/typescript/domain/campaign/campaign_sequence.test.ts",
    "test_gui_interaction_regressions.py": "apps/warband-manager-web/src/architecture/product-app-session.test.tsx",
    "test_injury_sequence_matrix.py": "packages/typescript/domain/campaign/injury_sequence.test.ts",
    "test_persistence.py": "packages/typescript/application/campaign/persistence_parity.test.ts",
    "test_ui_i18n.py": "apps/warband-manager-web/src/features/campaign/ui_i18n.test.ts",
}


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
    override = TARGET_OVERRIDES.get(Path(file).name)
    if override is not None:
        return override
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
        individual_exclusion = INDIVIDUAL_EXCLUSIONS.get((file, test))
        if individual_exclusion is not None:
            disposition, category, owner, reason = "X", "browser-no-equivalent", "nobody", individual_exclusion
        status = "excluded" if disposition == "X" else "implemented"
        evidence = f"target: {_web_target(disposition, file)}" if disposition != "X" else None
        follow_up = None
        if (file.startswith("tests/ui/") or basename == "test_gui_interaction_regressions.py") and disposition != "X":
            status = "partial"
            evidence = "apps/warband-manager-web/src/features/campaign/parity-gui-regressions.test.tsx"
            follow_up = UI_PARTIAL_FOLLOW_UP
        implemented = IMPLEMENTED_UI_TESTS.get((file, test))
        if implemented is not None:
            status = "implemented"
            evidence = implemented
            follow_up = None
        rows.append({
            "source_file": file,
            "source_test": test,
            "behavior_id": f"desktop.{_family(file)}",
            "desktop_category": category,
            "web_disposition": disposition,
            "web_target": _web_target(disposition, file),
            "owner": owner,
            "status": status,
            "parity_vector": None,
            "exclusion_reason": reason,
            "evidence": evidence,
            "follow_up": follow_up,
        })
    rows.sort(key=lambda r: (r["source_file"], r["source_test"]))
    return rows


def build_manifest() -> dict:
    rows = build_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["web_disposition"]] = counts.get(row["web_disposition"], 0) + 1
    return {
        "plan": "campaign-web-parity",
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
