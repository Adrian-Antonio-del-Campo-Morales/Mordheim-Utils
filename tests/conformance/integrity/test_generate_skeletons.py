"""Engine-free generator checks; run this file directly with Python/unittest."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml
import pytest

# The scaffold generator's guarantee is the provenance of authoring evidence:
# one admitted identity per file, preserved bytes and an explicit pending state.
# Contract rejections and CLI safety are part of that same tool contract.
pytestmark = pytest.mark.evidence

if __package__:
    from .. import generate_skeletons as generator
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import generate_skeletons as generator


def clause(clause_id, scope):
    return {"id": clause_id, "scope": scope}


class SkeletonGenerationTests(unittest.TestCase):
    def setUp(self):
        self.workspace = TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.knowledge = self.root / "knowledge"
        self.output = self.root / "cases"
        self.core = [
            {"id": "combat-fixture", "name": "Fixture", "effect": "Printed rule.",
             "clauses": [clause("threshold", "YES"), clause("excluded", "NO")]},
        ]
        self.mechanics = [
            {"id": "skill.fixture", "name": "Fixture"},
            {"id": "skill.outside", "name": "Outside"},
        ]
        self.write_knowledge()

    def write_knowledge(self):
        (self.knowledge / "catalog/rules").mkdir(parents=True, exist_ok=True)
        (self.knowledge / "catalog/mechanics").mkdir(parents=True, exist_ok=True)
        (self.knowledge / "catalog/rules/core-combat.yaml").write_text(
            yaml.safe_dump({"rules": self.core}), encoding="utf-8")
        (self.knowledge / "catalog/mechanics/close-combat.yaml").write_text(
            yaml.safe_dump({"skills": self.mechanics}), encoding="utf-8")
        (self.knowledge / "registry").mkdir(parents=True, exist_ok=True)
        (self.knowledge / "registry/runtime-scope.yaml").write_text(
            yaml.safe_dump({"mechanic_exclusions": [{"id": "skill.outside", "reason": "shooting"}]}), encoding="utf-8")
        (self.knowledge / "catalog/items").mkdir(parents=True, exist_ok=True)
        (self.knowledge / "bands").mkdir(parents=True, exist_ok=True)
        (self.knowledge / "catalog/skills").mkdir(parents=True, exist_ok=True)

    def generate(self, **options):
        return generator.generate(self.output, self.knowledge, **options)

    def path(self, identity="core/combat-fixture"):
        return self.output / generator.relative_path(identity)

    def test_only_admitted_ids_get_empty_files_with_their_clause_list(self):
        result = self.generate()
        self.assertEqual(result["created"], 2)
        self.assertEqual(len(list(self.output.rglob("*.yaml"))), 2)
        text = self.path().read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(text), [])
        self.assertIn("# authoring_status: TODO", text)
        self.assertIn("# TODO[threshold]", text)
        self.assertIn("# Clause: excluded (scope: NO)", text)
        self.assertNotIn("# TODO[excluded]", text)
        self.assertIn("catalog/rules/core-combat.yaml", text)
        fixture = self.path("mechanic/skill.fixture").read_text(encoding="utf-8")
        self.assertIn("# TODO: Review the rule", fixture, "an undivided identity gets one TODO")
        self.assertNotIn("# Clause:", fixture)
        self.assertTrue(all(yaml.safe_load(path.read_text(encoding="utf-8")) == []
                            for path in self.output.rglob("*.yaml")))

    def test_invalid_clauses_fail_before_writes(self):
        self.core[0]["clauses"].append(clause("threshold", "NO"))
        self.write_knowledge()
        with self.assertRaisesRegex(ValueError, "duplicate clause id"):
            self.generate()
        self.assertFalse(self.output.exists())

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
        self.assertEqual(result["unexpected"], [])
        self.assertEqual(before, {p: p.read_bytes() for p in self.output.rglob("*.yaml")})
        self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8")), [scenario])

    def test_an_identity_declared_by_scenarios_of_another_file_is_present(self):
        self.generate()
        host = self.path("mechanic/skill.fixture")
        scenario = {"audit_id": "core/combat-fixture", "id": "hosted",
                    "covers": ["threshold"], "expect_initial": {"first.wounds": 1}}
        host.write_text(host.read_text(encoding="utf-8").replace(
            "[]  # Empty scenario list: this file contributes no test or coverage.",
            yaml.safe_dump([scenario]).rstrip()), encoding="utf-8")
        self.path().unlink()
        result = self.generate(check=True)
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["preserved"], 2)

    def test_existing_cases_are_ignored_and_every_scaffold_starts_from_zero(self):
        self.output.mkdir()
        path = self.output / "existing.yaml"
        path.write_text("unfinished-legacy-case: [\n", encoding="utf-8")
        before = path.read_bytes()
        self.generate()
        text = self.path().read_text(encoding="utf-8")
        self.assertIn("# authoring_status: TODO", text)
        self.assertNotIn("existing.yaml", text)
        self.assertIn("# TODO[threshold]", text)
        self.assertEqual(yaml.safe_load(text), [])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.generate(check=True)["unexpected"], [])

    def test_retired_scaffolds_are_reported_and_preserved(self):
        self.generate()
        before = self.path().read_bytes()
        del self.core[0]
        self.write_knowledge()
        result = self.generate(check=True)
        self.assertEqual(result["unexpected"], [generator.relative_path("core/combat-fixture").as_posix()])
        self.assertEqual(self.path().read_bytes(), before)

    def test_a_declared_identity_outside_the_runtime_keeps_its_scaffold(self):
        self.generate()
        before = self.path("mechanic/skill.fixture").read_bytes()
        (self.knowledge / "registry/runtime-scope.yaml").write_text(
            yaml.safe_dump({"mechanic_exclusions": [{"id": "skill.fixture", "reason": "shooting"}]}), encoding="utf-8")
        result = self.generate(check=True)
        self.assertEqual(result["unexpected"], [])
        self.assertEqual(self.path("mechanic/skill.fixture").read_bytes(), before)

    def test_long_rule_ids_have_short_distinct_windows_safe_paths(self):
        prefix = "rule/mordheim/band/" + "long-name-" * 25
        paths = [generator.relative_path(prefix + suffix) for suffix in ("effect.one", "effect.two")]
        self.assertNotEqual(paths[0], paths[1])
        for path in paths:
            self.assertLessEqual(len(path.name), 91)
            self.assertFalse(any(char in path.name for char in '<>:"/\\|?*'))

    def test_cli_exit_codes_no_write_modes_and_no_combat_imports(self):
        script = Path(generator.__file__).resolve()
        command = [sys.executable, str(script), "--output-dir", str(self.output),
                   "--knowledge-root", str(self.knowledge)]
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
