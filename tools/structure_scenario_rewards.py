"""Build the executable scenario-reward catalogue from the source transcription."""
from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/knowledge/catalog/campaign/scenarios.yaml"
TARGET = ROOT / "sources/knowledge/catalog/campaign/scenario-rewards.yaml"


def _item_names() -> list[tuple[str, str]]:
    rows = []
    for path in (ROOT / "sources/knowledge/catalog/items").glob("*.yaml"):
        for item in yaml.safe_load(path.read_text(encoding="utf-8")).get("items") or ():
            if item.get("name"):
                rows.append((str(item["name"]).casefold(), str(item["id"])))
    return sorted(rows, key=lambda pair: len(pair[0]), reverse=True)


def _grants(reward: str, item_id: str | None = None) -> list[dict]:
    text = reward.casefold()
    if item_id:
        item_grants = [{"kind": "item", "item_id": item_id, "quantity_input": True}]
    else:
        matches = [(name, candidate) for name, candidate in _item_names() if re.search(rf"\b{re.escape(name)}s?\b", text)]
        selected = []
        for name, candidate in matches:
            if not any(name in longer for longer, _item in selected):
                selected.append((name, candidate))
        item_grants = [{"kind": "item", "item_id": candidate, "quantity_input": True} for _name, candidate in selected]
    grants = []
    if "wyrdstone" in text:
        grants.append({"kind": "resource", "resource": "wyrdstone_fragments", "quantity_input": True})
    if any(token in text for token in ("gold", " gc", "gem", "jeweller")):
        grants.append({"kind": "resource", "resource": "gold_crowns", "quantity_input": True})
    grants.extend(item_grants)
    if grants:
        return grants
    slug = re.sub(r"[^a-z0-9]+", "-", reward.casefold()).strip("-")[:60]
    return [{"kind": "special", "special_id": slug or "scenario-reward", "quantity_input": True}]


def _dice(text: str) -> dict | None:
    match = re.search(r"(?<![A-Z0-9])(\d*)D(\d+)(?:\s*[x×]\s*(\d+)|\s*\+\s*(\d+))?", text, re.IGNORECASE)
    if not match:
        return None
    return {
        "count": int(match.group(1) or 1), "sides": int(match.group(2)),
        "multiplier": int(match.group(3) or 1), "modifier": int(match.group(4) or 0),
    }


def build() -> dict:
    scenarios = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["scenarios"]
    entries = []
    for scenario in scenarios:
        progression = scenario.get("progression") or {}
        rewards = []
        for key, resource in (("income", "gold_crowns"), ("wyrdstone", "wyrdstone_fragments")):
            if progression.get(key):
                rewards.append({
                    "id": f"{scenario['id']}.{key}", "kind": "resource",
                    "resource": resource, "rule": progression[key], "quantity_input": True,
                })
        if progression.get("exploration"):
            reward = {
                "id": f"{scenario['id']}.exploration", "kind": "exploration",
                "rule": progression["exploration"],
            }
            if scenario["id"] == "scenario.a-stroll-in-the-garden":
                reward.update({"extra_dice": 1, "reroll_all": True})
            rewards.append(reward)
        loot = progression.get("loot") or {}
        contents = []
        for index, content in enumerate(loot.get("contents") or (), 1):
            for grant_index, grant in enumerate(_grants(content["reward"], content.get("item_id")), 1):
                row = {
                    "id": f"{scenario['id']}.loot.{index}.{grant_index}",
                    "label": content["reward"], "roll": content["roll"], "grant": grant,
                }
                quantity_dice = _dice(content["reward"])
                if quantity_dice:
                    if grant.get("resource") == "gold_crowns" and "worth 10" in content["reward"].casefold():
                        quantity_dice["multiplier"] *= 10
                    row["quantity_dice"] = quantity_dice
                threshold = re.fullmatch(r"(\d+)\+", str(content["roll"]).strip())
                roll_dice = _dice(str(content["roll"]))
                if threshold:
                    row["availability"] = {"dice": {"count": 1, "sides": 6}, "target": int(threshold.group(1))}
                elif roll_dice:
                    row["availability"] = {"dice": roll_dice}
                if content.get("when"):
                    row["when"] = content["when"]
                contents.append(row)
        if loot:
            if not contents:
                contents.append({
                    "id": f"{scenario['id']}.loot.1", "label": loot.get("effect", "Scenario reward"),
                    "roll": "manual", "grant": {
                        "kind": "special", "special_id": f"{scenario['id']}.reward",
                        "quantity_input": True,
                    },
                })
            rewards.append({
                "id": f"{scenario['id']}.loot", "kind": "loot_table",
                "rule": loot.get("effect", ""), "contents": contents,
                "manual_resolution": str(contents[0].get("roll")) == "manual",
            })
        if rewards:
            entries.append({"scenario_id": scenario["id"], "rewards": rewards})
    return {
        "schema_version": 2, "ruleset": "mordheim",
        "catalog": "campaign-scenario-rewards", "status": "published", "scenarios": entries,
    }


if __name__ == "__main__":
    TARGET.write_text(yaml.safe_dump(build(), sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
