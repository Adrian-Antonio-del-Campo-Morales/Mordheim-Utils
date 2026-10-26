"""Knowledge declarations and bindings separated from modular rule execution."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
EXECUTION = "sources/knowledge/catalog/mechanics/execution.yaml"


def test_every_record_declares_the_canonical_tag():
    document = yaml.safe_load((ROOT / EXECUTION).read_text(encoding="utf-8"))
    effects = {effect["id"]: effect["parameters"]["tags"]
               for effect in document["mechanics"]
               if isinstance(effect, dict) and "parameters" in effect}
    expected = {
        "mechanic.confound-and-confuse": ["mechanic.confound-and-confuse"],
        "rule.slay-large-creature": ["rule.slay-large-creature"],
        "rule.thin-flesh": ["rule.thin-flesh"],
        "skill.backstabber": ["skill.backstabber"],
        "skill.dodge-sidestepper": ["mechanic.dodge-sidestepper"],
        "mechanic.babbling-banter": ["mechanic.babbling-banter"],
        "mechanic.mantle-of-crows": ["mechanic.mantle-of-crows"],
        "mechanic.needle-and-thread": ["mechanic.needle-and-thread"],
        "mechanic.hillman-lycanthrope": ["mechanic.hillman-lycanthrope"],
        "condition.mouth-sewn": ["condition.mouth-sewn"],
    }
    for mechanic, tags in expected.items():
        assert effects.get(mechanic) == tags, mechanic
