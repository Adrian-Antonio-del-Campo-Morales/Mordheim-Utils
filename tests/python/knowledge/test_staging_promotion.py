"""external.test_staging_promotion: the promotion of the staged catalogues.

The passes of ``staging_promotion`` give the staged trees the *shape* of the
knowledge base; ``staging_promotion.promote`` merges them into a destination
root. These tests are the pins of that second half:

* a preview writes nothing, anywhere;
* a destination that starts empty is promoted whole, and the knowledge base and
  the staged trees stay byte for byte as they were;
* a second promotion of the same tree changes nothing;
* the identity decisions of T04 reach the destination (the declared variants,
  the item redirects, the ``-miracle-workers`` suffix of the three priests with
  every reference that follows their profile, the Taal & Rhya variant, the
  harpoon reclassification);
* no printed prose, price, restriction or currency is lost;
* a collision no decision table declares is refused instead of overwriting a
  published record.

``promote`` reads the staged trees through the normalisation passes, so every
case here works on the trees as they are checked out; the write lands in a
``tmp_path`` destination and never in ``sources/knowledge``.
"""
from __future__ import annotations

from pathlib import Path
import hashlib

import pytest
import yaml

from mordheim_knowledge import hireling_promotion
from mordheim_knowledge import magic_promotion
from mordheim_knowledge import staging_promotion as promotion

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
STAGED = (ROOT / "sources" / "2A", ROOT / "sources" / "2B")
TAAL = "lore.prayers-of-taal-and-rhya"
PRIESTS = tuple(hireling_promotion.HIRELING_REDIRECTS.values())


def digests() -> dict[str, str]:
    """The sha256 of every staged and KB YAML document, by path."""
    found: dict[str, str] = {}
    for root in (KNOWLEDGE, *STAGED):
        for path in sorted(root.rglob("*.yaml")):
            found[path.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def items(destination: Path) -> dict[str, dict]:
    """Every item of a KB-shaped tree, by id."""
    found: dict[str, dict] = {}
    for path in sorted((destination / "catalog" / "items").glob("*.yaml")):
        for item in read(path).get("items") or []:
            found[str(item["id"])] = item
    return found


def campaigns(destination: Path) -> dict[str, dict]:
    document = read(destination / "catalog" / "campaign" / "hired-swords-and-dramatis.yaml")
    entries = list(document.get("hired_swords") or []) + list(document.get("dramatis_personae") or [])
    return {str(entry["id"]): entry for entry in entries}


@pytest.fixture(scope="module")
def promoted(tmp_path_factory) -> dict:
    """A temporary destination, promoted from an empty root."""
    before = digests()
    root = tmp_path_factory.mktemp("promotion")
    plan = promotion.promote(root)
    assert not plan.conflicts, [action.as_dict() for action in plan.conflicts]
    written = plan.write()
    return {"root": root, "plan": plan, "written": written, "before": before, "after": digests()}


def test_a_preview_writes_nothing() -> None:
    """Planning a promotion is a read: no file of the trees or the KB moves."""
    before = digests()
    plan = promotion.promote()
    assert plan.actions, "a promotion that previews no record is not a preview"
    assert plan.edits, "the KB promotion of an unmerged staging tree must have work to do"
    assert digests() == before


def test_a_promotion_leaves_the_knowledge_base_and_staging_untouched(promoted) -> None:
    """The destination is the only tree a promotion writes."""
    assert promoted["written"], "an empty destination must receive the promotion"
    assert all(path.is_relative_to(promoted["root"]) for path in promoted["written"])
    assert promoted["after"] == promoted["before"]


def test_a_second_promotion_of_the_same_tree_changes_nothing(promoted) -> None:
    """Idempotence: the destination already carries every promoted record."""
    again = promotion.promote(promoted["root"])
    assert not again.conflicts
    assert again.edits == []
    assert again.counts().get(promotion.ACTION_PRESENT, 0) > 300


def test_an_undeclared_collision_is_refused(monkeypatch, tmp_path) -> None:
    """A staged id the KB already publishes, with no decision, stops the write."""
    staged = promotion.staged_catalogues

    def colliding(tree: str) -> dict:
        found = staged(tree)
        if tree != "2B":
            return found
        squatter = {"id": "mace_hammer", "kind": "close-combat-weapon", "name": "Squatter's Club"}
        return {**found, "items": [*found["items"], squatter]}

    monkeypatch.setattr(promotion, "staged_catalogues", colliding)
    plan = promotion.promote(tmp_path)
    assert [action.source_id for action in plan.conflicts] == ["mace_hammer"]
    with pytest.raises(promotion.PromotionRefused):
        plan.write()
    assert list(tmp_path.rglob("*.yaml")) == []


def test_the_declared_decisions_are_the_ones_t04_accepted() -> None:
    """The tables, read directly: they are the only reason a collision is legal."""
    assert magic_promotion.MIRROR_LORES == (), "Taal & Rhya is not a mirror (T04 §12)"
    assert promotion.ITEM_REDIRECTS["rope_and_hook"] == "rope_hook"
    assert promotion.ITEM_REDIRECTS["elven_bow"] == "elf_bow"
    assert promotion.ITEM_REDIRECTS["wardog"] == "warhound"
    assert promotion.ITEM_MERGES["hunting_arrows"] == "hunting_arrows"
    assert set(promotion.ITEM_VARIANTS) >= {
        "repeater_pistol_moh",
        "shield_of_sigmar",
        "society_familiar",
        "wolf_cloak",
    }
    assert promotion.ITEM_KINDS["harpoon"] == "ranged-weapon"
    assert set(PRIESTS) == {
        "hireling.hired-sword.priest-of-morr-miracle-workers",
        "hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers",
        "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers",
    }


def test_the_item_decisions_reach_the_destination(promoted) -> None:
    """Variants are published, redirects are not, and their provenance is kept."""
    published = items(promoted["root"])
    for variant in promotion.ITEM_VARIANTS:
        assert variant in published, variant
    for redirected in ("rope_and_hook", "elven_bow", "wardog", "dueling_pistol"):
        assert redirected not in published, redirected
    for survivor in ("rope_hook", "elf_bow", "warhound", "horsemans_hammer"):
        assert survivor in published, survivor
    assert published["harpoon"]["kind"] == "ranged-weapon"
    # The folded provenance points at the publication the redirect came from.
    assert any(
        ref["manual"] == "broheim.net" for ref in published["rope_hook"]["source_refs"]
    )


def test_the_three_priests_and_every_reference_move_together(promoted) -> None:
    """The profile, its rules and its campaign entry share the new suffix."""
    profiles = {
        str(profile["id"]): profile
        for path in sorted((promoted["root"] / "catalog" / "hirelings" / "hired-swords").glob("*.yaml"))
        for profile in read(path).get("profiles") or []
    }
    entries = campaigns(promoted["root"])
    for priest in PRIESTS:
        assert priest in profiles, priest
        assert priest in {entry["profile_id"] for entry in entries.values()}, priest
        assert all(rule["id"].startswith(priest + ".") for rule in profiles[priest]["rules"])
        entry = next(entry for entry in entries.values() if entry["profile_id"] == priest)
        assert entry["id"] == f"campaign.hireling.hired-sword.{priest.split('.', 2)[2]}"


def test_taal_and_rhya_keeps_its_prose_and_its_spells(promoted) -> None:
    """The variant is published whole, with the ruling in its note."""
    staged = read(ROOT / "sources" / "2B" / "catalog" / "magic-2b.yaml")
    source = next(lore for lore in staged["lores"] if lore["id"] == TAAL)
    destination = read(promoted["root"] / "catalog" / "campaign" / "magic.yaml")
    lore = next(candidate for candidate in destination["lores"] if candidate["id"] == TAAL)
    assert [spell["id"] for spell in lore["spells"]] == [spell["id"] for spell in source["spells"]]
    assert [spell["effect"] for spell in lore["spells"]] == [spell["effect"] for spell in source["spells"]]
    assert all(spell["effect"].strip() for spell in lore["spells"])
    assert "VARIANT of the KB lore.prayers-of-taal" in lore["note"]
    assert "MIRROR of the KB" not in lore["note"]
    rows = [
        row
        for row in destination["lore_assignments"]["rows"]
        if row["lore"] == TAAL
    ]
    assert [row["profile_id"] for row in rows] == ["hireling.hired-sword.druid-priest-of-taal"]


def test_local_prices_restrictions_and_currencies_survive(promoted) -> None:
    """No gold-crown normalisation: warp tokens, dinars and band prices stay."""
    market = read(promoted["root"] / "catalog" / "campaign" / "trading-post.yaml")
    entries = {str(entry["id"]): entry for entry in market["items"]}
    # The KB entry of another item keeps its own price, availability and id.
    assert entries["campaign.trading-post.club-mace-or-hammer"]["price"] == {"base_gc": 3}
    assert entries["campaign.trading-post.warplock-pistol"]["item_id"] == "warp_pistol"
    assert entries["campaign.trading-post.warplock-pistol"]["availability"] == {
        "kind": "rare",
        "rarity": 11,
    }
    # The variant's own entry keeps the published price and the band restriction.
    variant = entries["campaign.trading-post.warplock-pistol-mim"]
    assert variant["price"] == {"base_gc": 35}
    assert variant["restrictions"][0] == {
        "type": "warband_only",
        "band_ids": ["metal-mongers-mim"],
    }
    # A price printed in a currency the KB does not model keeps its amount in the
    # verbatim note instead of being turned into gold crowns.
    entries_by_item = {str(entry["item_id"]): entry for entry in market["items"]}
    tokens = entries_by_item["beastwhip"]
    assert tokens["price"] is None
    assert any(
        restriction.get("note") == "Clan Moulder only. 25 Warp Tokens."
        for restriction in tokens["restrictions"]
    )
    # The KB entry of a similarly named item is never reused for a staged one.
    assert entries_by_item["staff_club_mace"]["availability"] == {"kind": "not_sold"}
    fees = {
        str(entry["profile_id"]): entry
        for entry in campaigns(promoted["root"]).values()
    }
    assert fees["hireling.hired-sword.albino-stormvermin"]["hiring_fee"]["resources"][
        "gold_crowns"
    ]["cost"] == "75 warp tokens"
    assert fees["hireling.dramatis.armen-abbas"]["hiring_fee"]["resources"]["gold_crowns"][
        "cost"
    ] == "85 dinars"
