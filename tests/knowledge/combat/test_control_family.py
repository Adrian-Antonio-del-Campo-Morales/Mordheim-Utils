"""Canonical control-power bindings, independent of modular execution."""
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]

def rule_record(relative_path: str, rule_id: str) -> dict:
    document = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
    for record in document["rules"]:
        if record["id"] == rule_id:
            return record
    raise AssertionError(f"{rule_id} is missing from {relative_path}")

def test_the_printed_records_declare_their_canonical_mechanic():
    checks = (
        ("sources/knowledge/bands/trollheim/lustria-amazons/special-rules.yaml",
         "band--amazon-special-skills-hypnotic-dance", "mechanic.mesmerising-dance"),
        ("sources/knowledge/bands/trollheim/chaos-streets-undead-bloodlines/special-rules.yaml",
         "band--vampire-power-hypnotic-gaze", "mechanic.hypnotic-gaze"),
        ("sources/knowledge/bands/trollheim/chaos-streets-undead-bloodlines/special-rules.yaml",
         "band--lahmia-power-seduction", "mechanic.lahmia-seduction"),
        ("sources/knowledge/bands/trollheim/khemri-lahmian-brotherhood/special-rules.yaml",
         "band--lahmian-special-skills-seduction", "mechanic.lahmian-seduction"),
        ("sources/knowledge/bands/trollheim/chaos-streets-undead-bloodlines/special-rules.yaml",
         "lahmia-vampire--enchanting-beauty", "mechanic.enchanting-beauty"),
    )
    for relative_path, rule_id, mechanic in checks:
        runtime = rule_record(relative_path, rule_id)["runtime"]
        assert runtime["implemented"] == "YES", rule_id
        assert [effect["binding"]["id"] for effect in runtime["effects"]] == [mechanic], rule_id
