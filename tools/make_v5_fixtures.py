"""One-off generator for the v5 contract fixtures.

Produces the four committed fixtures of ``contracts/campaign-file-v5/fixtures/``
from real application state built by the reference writer, so the fixtures are
guaranteed to validate against the schema. Run from the repository root:

    python tools/make_v5_fixtures.py

The output is deterministic except for ``saved_at``, which each fixture fixes
to an illustrative instant.
"""
from __future__ import annotations

import json
from pathlib import Path

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.domain.builders import make_draft_state, make_example_state
from mordheim_campaign.persistence.campaigns import _document

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "campaign-file-v5" / "fixtures"

SAVED_AT = "2026-09-08T18:30:00+00:00"


def _write(name: str, state) -> None:
    document = _document(state, saved_at=SAVED_AT)
    path = FIXTURES / f"{name}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def draft() -> None:
    _write("draft", make_draft_state(KnowledgePort(), "sisters-of-sigmar"))


def active_campaign() -> None:
    _write("active-campaign", make_example_state(KnowledgePort()))


def pending_post_battle() -> None:
    """A campaign whose newest post-battle sequence is mid-resolution.

    Starts from the example state (battle 8 pending) and walks the engine a
    few steps so the document carries real pending work: applied experience,
    completed steps and an event log.
    """
    port = KnowledgePort()
    state = make_example_state(port)
    engine = PostBattleEngine(port, state.campaign, state.campaign.pending_post_battle)
    # Step 1 (Experience): the example sequence already applied experience;
    # make sure it is applied.
    engine.apply_battle_experience()
    # Step 3 (Sell Wyrdstone): sell one shard so the document carries a real
    # applied mutation in its event log.
    ok, message = engine.sell_wyrdstone(1)
    assert ok, message
    _write("pending-post-battle", state)


def full_inventory() -> None:
    """An active campaign with a rich inventory and equipped/stash splits.

    Starts from the example state and adds stash copies and a rare item so
    every inventory field is exercised, then commits one more state so the
    timeline snapshots carry roster + inventory.
    """
    port = KnowledgePort()
    controller = AppController(port=port)
    controller.state.campaign = make_example_state(port).campaign
    inventory = controller.state.campaign.inventory
    # Move part of the owned daggers to the stash and give the rare relic a
    # scenario effect so every inventory field is exercised.
    daggers = next(item for item in inventory if item.id == "dagger")
    daggers.equipped = 2
    daggers.stash = 2
    relic = next(item for item in inventory if item.id == "holy_relic")
    relic.special_rules = ["Scenario effect"]
    _write("full-inventory", controller.state)


if __name__ == "__main__":
    FIXTURES.mkdir(parents=True, exist_ok=True)
    draft()
    active_campaign()
    pending_post_battle()
    full_inventory()
    # Sanity: every fixture must load through the public API.
    for path in sorted(FIXTURES.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
    print("all fixtures generated")
