"""Focused conservation and conflict discriminators; never writes the live CSV."""
import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "knowledge"))

import clause_registry as tool


@pytest.mark.phase1_kb_contracts
class RegisterToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "register.csv"
        template = dict.fromkeys(tool.validator.FIELDS, "")
        template.update(id="same-id", source_file="source.yaml", source_fingerprint="abc",
                        clause_text='Quoted "source"\nsecond line', clause_scope="YES",
                        semantic_contract="Printed contract", relation="independent",
                        parameters="{}", conditions="{}", consumer="[]", pending="{}",
                        verification='["inspection"]', status='{"numpy":"pending","native":"pending"}', notes="Existing useful note")
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=tool.validator.FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dict(template, clause_id=str(n)) for n in range(4556))
        self.raw = out.getvalue().encode("utf-8")
        self.path.write_bytes(self.raw)
        self.requests = [{"id": "same-id", "clause_id": "1",
                          "set": {"pending": {"work": "connection"}},
                          "append_notes": "Explicit implementation decision"}]

    def test_three_cli_operations_and_multiclause_conservation(self):
        def cli(*args):
            return subprocess.run([sys.executable, "-X", "utf8", str(Path(tool.__file__)),
                                   "--csv", str(self.path), *args],
                                  capture_output=True, text=True, encoding="utf-8", check=True)
        result = cli("query", "--id", "same-id", "--clause-id", "1")
        self.assertEqual(json.loads(result.stdout)[0]["clause_id"], "1")
        requests = self.root / "changes.json"
        requests.write_text(json.dumps(self.requests), encoding="utf-8")
        package = self.root / "prepared.json"
        cli("prepare", str(requests), "--out", str(package))
        cli("apply", str(package))
        self.assertEqual(self.path.read_bytes(), self.raw)
        output = cli("apply", str(package), "--write").stdout
        backup = Path(next(line[8:] for line in output.splitlines() if line.startswith("Backup: ")))
        self.addCleanup(lambda: (backup.unlink(), backup.parent.rmdir()))
        self.assertEqual(backup.read_bytes(), self.raw)
        before, after = tool.read(self.raw), tool.read(self.path.read_bytes())
        self.assertEqual(before[:1] + before[2:], after[:1] + after[2:])
        self.assertEqual(after[1]["notes"], before[1]["notes"] + "\nExplicit implementation decision")
        self.assertEqual(json.loads(after[1]["pending"]), {"work": "connection"})
        self.assertEqual(cli("query", "--pending", "--work", "connection").returncode, 0)

    def test_windows_line_endings_and_untouched_records_preserved(self):
        raw = self.raw.replace(b"\n", b"\r\n")
        self.path.write_bytes(raw)
        package = tool.prepare(self.path, self.requests)
        result = tool.candidate(raw, package)
        before, after = tool.read(raw), tool.read(result)
        self.assertEqual(before[:1] + before[2:], after[:1] + after[2:])
        self.assertEqual(before[1]["clause_text"], after[1]["clause_text"])
        self.assertTrue(result.startswith(raw[:raw.index(b"\r\n") + 2]))
        self.assertEqual(result.count(b"Existing useful note"), 4556)

    def test_rejects_protected_fields_and_note_replacement(self):
        for field in (*tool.PROTECTED, "notes", "unknown"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                tool.prepare(self.path, [{"id": "same-id", "clause_id": "1", "set": {field: "bad"}}])
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_rejects_invalid_pending_and_duplicate_clause_changes(self):
        for requests in ([self.requests[0], self.requests[0]],
                         [{"id": "same-id", "clause_id": "1", "set": {"pending": {"work": "invented"}}}]):
            with self.assertRaises(ValueError):
                tool.prepare(self.path, requests)

    def test_delivery_reference_replacement_preserves_other_notes(self):
        raw = self.raw.replace(b"Existing useful note", b"Useful note; C04a-completed.md", 1)
        self.path.write_bytes(raw)
        request = {"id": "same-id", "clause_id": "0",
                   "replace_note_references": {"C04a-completed.md": "tests/construction.py"}}
        package = tool.prepare(self.path, [request])
        rows = tool.read(tool.candidate(raw, package))
        self.assertEqual(rows[0]["notes"], "Useful note; tests/construction.py")
        self.assertEqual(rows[1:], tool.read(raw)[1:])
        package["changes"][0]["after"]["notes"] = "Discarded useful note"
        with self.assertRaisesRegex(ValueError, "notes must be preserved"):
            tool.candidate(raw, package)
        request["replace_note_references"] = {"Useful note": "discard"}
        with self.assertRaisesRegex(ValueError, "delivery reference"):
            tool.prepare(self.path, [request])

    def test_status_validation_and_explicit_scope_transition(self):
        for status in ([], {"numpy": "pending"}, {"numpy": "wrong", "native": "pending"},
                       {"numpy": [], "native": "pending"},
                       {"numpy": "pending", "native": "pending", "other": "pending"}):
            with self.subTest(status=status), self.assertRaises(ValueError):
                tool.prepare(self.path, [{"id": "same-id", "clause_id": "1",
                                          "set": {"status": status}}])
        with self.assertRaises(ValueError):
            tool.prepare(self.path, [{"id": "same-id", "clause_id": "1",
                                      "set": {"clause_scope": "NO"}}])
        package = tool.prepare(self.path, [{"id": "same-id", "clause_id": "1",
                                           "set": {"clause_scope": "NO", "status": {}}}])
        self.assertEqual(json.loads(tool.read(tool.candidate(self.raw, package))[1]["status"]), {})

    def test_migration_conservation_idempotence_snapshot_and_old_packages(self):
        rows = tool.read(self.raw)
        rows[1]["clause_scope"] = "NO"
        for ending in ("\n", "\r\n"):
            out = io.StringIO(newline="")
            writer = csv.DictWriter(out, fieldnames=tool.validator.FIELDS[:-1],
                                    extrasaction="ignore", lineterminator=ending)
            writer.writeheader()
            writer.writerows(rows)
            legacy = out.getvalue().encode("utf-8")
            self.path.write_bytes(legacy)
            package = tool.migration(self.path)
            with contextlib.redirect_stdout(io.StringIO()):
                tool.apply(self.path, package)
            self.assertEqual(self.path.read_bytes(), legacy)
            result = tool.candidate(legacy, package)
            actual = tool.read(result)
            self.assertEqual([{f: row[f] for f in tool.validator.FIELDS[:-1]}
                              for row in actual], tool.read(legacy, legacy=True))
            self.assertEqual(json.loads(actual[0]["status"]), {"numpy": "pending", "native": "pending"})
            self.assertEqual(json.loads(actual[1]["status"]), {})
            self.assertEqual(result.count(ending.encode()), legacy.count(ending.encode()))
            with self.assertRaisesRegex(ValueError, "Concurrent change"):
                tool.candidate(legacy + b"\n", package)
            self.path.write_bytes(result)
            changed = tool.prepare(self.path, [{"id": "same-id", "clause_id": "0",
                "set": {"status": {"numpy": "implemented", "native": "blocked"}}}])
            result = tool.candidate(result, changed)
            self.path.write_bytes(result)
            self.assertEqual(tool.candidate(result, tool.migration(self.path)), result)
            with self.assertRaisesRegex(ValueError, "schema"):
                tool.candidate(result, {"sha256": tool.digest(result), "changes": []})

    def test_backend_query_filters_and_required_backend(self):
        package = tool.prepare(self.path, [{"id": "same-id", "clause_id": "1",
            "set": {"status": {"numpy": "implemented", "native": "blocked"}}},
            {"id": "same-id", "clause_id": "2", "set": {"clause_scope": "NO", "status": {}}}])
        self.path.write_bytes(tool.candidate(self.raw, package))
        def query(*args):
            return subprocess.run([sys.executable, "-X", "utf8", str(Path(tool.__file__)),
                                   "--csv", str(self.path), "query", *args],
                                  capture_output=True, text=True, encoding="utf-8")
        result = query("--backend", "numpy", "--status", "implemented", "--fields", "clause_id,status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["clause_id"], "1")
        self.assertEqual(json.loads(query("--backend", "native", "--clause-id", "2").stdout), [])
        self.assertIn("--status requires --backend", query("--status", "pending").stderr)

    def test_stale_package_rejected_and_lock_removed(self):
        package = tool.prepare(self.path, self.requests)
        concurrent = self.raw.replace(b"Existing useful note", b"Concurrent useful note", 1)
        self.path.write_bytes(concurrent)
        with self.assertRaisesRegex(ValueError, "Concurrent change"):
            tool.apply(self.path, package, write=True)
        self.assertEqual(self.path.read_bytes(), concurrent)
        self.assertFalse(self.path.with_suffix(".csv.lock").exists())

    def test_rechecks_concurrency_immediately_before_replace(self):
        package = tool.prepare(self.path, self.requests)
        backup_dir = self.root / "backup"
        backup_dir.mkdir()
        concurrent = self.raw.replace(b"Existing useful note", b"Concurrent useful note", 1)
        def concurrent_write(_):
            self.path.write_bytes(concurrent)
        with patch.object(tool.tempfile, "mkdtemp", return_value=str(backup_dir)), \
                patch.object(tool.os, "fsync", side_effect=concurrent_write), \
                contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaisesRegex(ValueError, "Concurrent change"):
            tool.apply(self.path, package, write=True)
        self.assertEqual(self.path.read_bytes(), concurrent)
        self.assertEqual((backup_dir / self.path.name).read_bytes(), self.raw)
        self.assertFalse(self.path.with_suffix(".csv.lock").exists())

    def test_tampered_package_and_existing_lock_rejected(self):
        package = tool.prepare(self.path, self.requests)
        package["changes"][0]["after"]["clause_text"] = "tampered"
        with self.assertRaisesRegex(ValueError, "Protected"):
            tool.candidate(self.raw, package)
        lock = self.path.with_suffix(".csv.lock")
        lock.write_text("another writer")
        with self.assertRaises(FileExistsError):
            tool.apply(self.path, package, write=True)
        self.assertEqual(lock.read_text(), "another writer")
        self.assertEqual(self.path.read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
