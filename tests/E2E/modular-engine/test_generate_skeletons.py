"""Engine-free generator checks; run this file directly with Python/unittest."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml

if __package__:
    from . import generate_skeletons as generator
else:
    import generate_skeletons as generator


class SkeletonGenerationTests(unittest.TestCase):
    def setUp(self):
        self.workspace = TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.knowledge = self.root / "knowledge"
        self.knowledge.mkdir()
        self.source = self.knowledge / "rule.yaml"
        self.source.write_text("rule: fixture\n", encoding="utf-8")
        self.register = self.root / "register.csv"
        self.output = self.root / "cases"
        self.rows = [self.row("core/combat-fixture", "threshold", "YES"),
                     self.row("core/combat-fixture", "excluded", "NO"),
                     self.row("mechanic/skill.fixture", "effect", "YES"),
                     self.row("mechanic/skill.outside", "shooting", "NO")]
        self.write_register()

    def row(self, identity, clause, scope):
        row = {field: "" for field in generator.REQUIRED_FIELDS + generator.CONTEXT_FIELDS}
        row.update(current_id=identity, origin_id=identity, clause_id=clause,
                   clause_scope=scope, source_file="rule.yaml", analysis_status="reviewed",
                   source_fingerprint=hashlib.sha256(self.source.read_bytes()).hexdigest(),
                   clause_text="Printed rule.\nA second line.", semantic_contract="Independent contract.")
        return row

    def write_register(self):
        with self.register.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, generator.REQUIRED_FIELDS + generator.CONTEXT_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)

    def generate(self, **options):
        return generator.generate(self.register, self.output, self.knowledge, **options)

    def path(self, identity="core/combat-fixture"):
        return self.output / generator.relative_path(identity)

    def test_only_admitted_ids_get_empty_files_with_all_clause_context(self):
        result = self.generate()
        self.assertEqual(result["created"], 2)
        self.assertEqual(len(list(self.output.rglob("*.yaml"))), 2)
        text = self.path().read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(text), [])
        self.assertIn("# authoring_status: TODO", text)
        self.assertIn("# TODO[threshold]", text)
        self.assertIn("# Clause: excluded (scope: NO)", text)
        self.assertNotIn("# TODO[excluded]", text)
        self.assertIn("#   A second line.", text)
        self.assertIn(str(self.register.resolve()), text)
        self.assertTrue(all(yaml.safe_load(path.read_text(encoding="utf-8")) == []
                            for path in self.output.rglob("*.yaml")))

    def test_regeneration_preserves_authored_scenarios_byte_for_byte(self):
        self.generate()
        path = self.path()
        text = path.read_text(encoding="utf-8")
        scenario = {"audit_id": "core/combat-fixture", "id": "written",
                    "covers": ["threshold"], "expect_initial": {"first.wounds": 1}}
        text = text.replace("[]  # Empty scenario list: this file contributes no test or coverage.",
                            yaml.safe_dump([scenario]).rstrip())
        path.write_text(text, encoding="utf-8")
        before = {p: p.read_bytes() for p in self.output.rglob("*.yaml")}
        result = self.generate()
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["preserved"], 2)
        self.assertEqual(result["stale"], [])
        self.assertEqual(before, {p: p.read_bytes() for p in self.output.rglob("*.yaml")})
        self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8")), [scenario])

    def test_existing_cases_are_ignored_and_every_scaffold_starts_from_zero(self):
        self.output.mkdir()
        path = self.output / "existing.yaml"
        path.write_text("unfinished-legacy-case: [\n", encoding="utf-8")
        before = path.read_bytes()
        self.generate()
        text = self.path().read_text(encoding="utf-8")
        self.assertIn("# authoring_status: TODO", text)
        self.assertNotIn("existing.yaml", text)
        self.assertNotIn("Existing declarations", text)
        self.assertIn("# TODO[threshold]", text)
        self.assertEqual(yaml.safe_load(text), [])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.generate(check=True)["stale"], [])

    def test_contract_changes_are_reported_without_overwriting(self):
        self.generate()
        before = self.path().read_bytes()
        self.rows[0]["semantic_contract"] = "Changed accepted contract."
        self.write_register()
        result = self.generate(check=True)
        self.assertIn(generator.relative_path("core/combat-fixture").as_posix(), result["stale"])
        self.assertEqual(self.path().read_bytes(), before)

    def test_record_and_file_hashes_are_not_compared_as_equivalent(self):
        self.rows[0]["source_fingerprint"] = "record-level-fingerprint"
        self.write_register()
        self.generate()
        text = self.path().read_text(encoding="utf-8")
        self.assertIn("record-level-fingerprint", text)
        self.assertIn(hashlib.sha256(self.source.read_bytes()).hexdigest(), text)
        self.assertNotIn("TODO[source-review]", text)
        self.assertEqual(self.generate(check=True)["stale"], [])

    def test_missing_source_is_pending_and_later_source_changes_are_detected(self):
        self.source.unlink()
        self.generate()
        text = self.path().read_text(encoding="utf-8")
        self.assertIn("# TODO[source-review]: The registered source file is missing.", text)
        self.assertIn("# authoring_status: TODO", text)
        self.assertEqual(yaml.safe_load(text), [])
        before = self.path().read_bytes()
        self.source.write_text("rule: changed\n", encoding="utf-8")
        result = self.generate()
        self.assertEqual(len(result["stale"]), 2)
        self.assertEqual(self.path().read_bytes(), before)

    def test_retired_scaffolds_are_reported_and_preserved(self):
        self.generate()
        before = self.path().read_bytes()
        self.rows[0]["clause_scope"] = "NO"
        self.write_register()
        result = self.generate(check=True)
        self.assertEqual(result["unexpected"], [generator.relative_path("core/combat-fixture").as_posix()])
        self.assertEqual(self.path().read_bytes(), before)

    def test_invalid_register_and_unsafe_source_fail_before_writes(self):
        self.rows.append(dict(self.rows[0]))
        self.write_register()
        with self.assertRaisesRegex(ValueError, "duplicate identity/clause"):
            self.generate()
        self.assertFalse(self.output.exists())
        self.rows.pop()
        self.rows[0]["source_file"] = "../outside.yaml"
        self.write_register()
        with self.assertRaisesRegex(ValueError, "escapes the knowledge root"):
            self.generate()
        self.assertFalse(self.output.exists())

    def test_long_rule_ids_have_short_distinct_windows_safe_paths(self):
        prefix = "rule/mordheim/band/" + "long-name-" * 25
        paths = [generator.relative_path(prefix + suffix) for suffix in ("effect.one", "effect.two")]
        self.assertNotEqual(paths[0], paths[1])
        for path in paths:
            self.assertLessEqual(len(path.name), 91)
            self.assertFalse(any(char in path.name for char in '<>:"/\\|?*'))

    def test_cli_exit_codes_no_write_modes_and_no_combat_imports(self):
        script = Path(generator.__file__).resolve()
        command = [sys.executable, str(script), "--register", str(self.register),
                   "--output-dir", str(self.output), "--knowledge-root", str(self.knowledge)]
        for flag, expected in (("--dry-run", 0), ("--check", 1)):
            result = subprocess.run(command + [flag], capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertFalse(self.output.exists())
        guarded_code = (
            "import runpy, sys; "
            "sys.path.insert(0, sys.argv[1]); sys.argv = sys.argv[2:]; "
            "module = runpy.run_path(sys.argv[0]); code = module['main'](sys.argv[1:]); "
            "assert not any(name.startswith(('mordheim_combat', 'mordheim_construction', "
            "'mordheim_core', 'mordheim_combat_lab')) for name in sys.modules); "
            "raise SystemExit(code)"
        )
        result = subprocess.run([sys.executable, "-c", guarded_code, str(script.parent)] + command[1:],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(command + ["--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
