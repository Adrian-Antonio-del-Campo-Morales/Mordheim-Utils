"""Knowledge declarations and bindings separated from modular rule execution."""

import pytest


def test_the_beast_hunter_qualifiers_are_declared_and_bound():
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
    catalogue = yaml.safe_load((root / "catalog/mechanics/close-combat.yaml").read_text(
        encoding="utf-8-sig"))
    sections = [value for value in catalogue.values() if isinstance(value, list)]
    ids = {row["id"] for section in sections for row in section
           if isinstance(row, dict) and "id" in row}
    assert {"mechanic.fear-beastmen", "mechanic.hatred-beastmen"} <= ids
    document = yaml.safe_load(
        (root / "catalog/hirelings/hired-swords/grade-1a.yaml").read_text(encoding="utf-8-sig"))
    bound = {}
    for profile in document["profiles"]:
        for rule in profile.get("rules") or ():
            runtime = rule.get("runtime") or {}
            for effect in runtime.get("effects") or ():
                binding = effect.get("binding") or {}
                if binding.get("id"):
                    bound.setdefault(binding["id"], set()).add(rule["id"])
    assert bound["mechanic.fear-beastmen"] == {
        "hireling.hired-sword.beast-hunter.rule.skull-rack"}
    assert bound["mechanic.hatred-beastmen"] == {
        "hireling.hired-sword.beast-hunter.rule.beastmen-vengeance"}
