"""Guards for the source-fidelity audit of sources/2A (``audit_2a_sources.py``).

The audit is only meaningful if three things hold, and this module pins all
three down with the cached mordheimer.net pages and their flat-text drafts
(``build/cache/2a-sources``, not versioned — the tests that need them skip when
the cache is absent, exactly like the ingest tools they guard):

1. the audited tree has no open finding, so a regression has to show up here;
2. the audit actually fails when a package drifts from the page — a wrong price,
   a list entry the page never prints, a rolled price flattened to null, a list
   whose source heading is gone. A green run of an audit that cannot fail is
   worthless, which is how the 2A equipment lists published under an ``h2``
   heading went unverified until the 2B re-verification;
3. the price cells of every currency and shape the pages use are read the way
   the schema prescribes (a rolled price as ``25+1D6``, a price relative to
   another item as null, a flat amount as the printed number).

The mutations run against a throwaway copy under ``build/cache``; the staging
tree is only ever read.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "knowledge"
PAGES = ROOT / "build" / "cache" / "2a-sources" / "pages"
TEXTS = ROOT / "build" / "cache" / "2a-sources" / "text"
BANDS = ROOT / "sources" / "2A" / "bands" / "mordheim"
SANDBOX = ROOT / "build" / "cache" / "2a-sources" / "test-sandbox"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

audit = pytest.importorskip("audit_2a_sources")

CACHED = pytest.mark.skipif(
    not (PAGES / "ogre-hunting-party-web.html").exists()
    or not (TEXTS / "ogre-hunting-party-web.txt").exists(),
    reason="mordheimer.net page snapshots are not cached (offline checkout)",
)


@pytest.fixture()
def sandbox() -> Path:
    """A throwaway copy of the package and catalogue trees, removed afterwards."""
    root = SANDBOX / "bands"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(BANDS.parent, root)
    shutil.copytree(ROOT / "sources" / "2A" / "catalog", SANDBOX / "catalog")
    bands, catalog = audit.BANDS, audit.CATALOG_DIR
    audit.BANDS = str(root / "mordheim")
    audit.CATALOG_DIR = str(SANDBOX / "catalog" / "items")
    try:
        yield root / "mordheim"
    finally:
        audit.BANDS, audit.CATALOG_DIR = bands, catalog
        shutil.rmtree(SANDBOX, ignore_errors=True)


@CACHED
def test_audited_tree_has_no_open_findings() -> None:
    items = audit.catalog_items()
    open_rows = [row for band in sorted(p.name for p in BANDS.iterdir())
                 for row in audit.check_band(band, items)
                 if row.get("verdict") != "known"]
    assert not open_rows, open_rows


@CACHED
def test_audit_detects_a_wrong_price(sandbox: Path) -> None:
    path = sandbox / "ogre-hunting-party-web" / "equipment-access.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("  - item_id: ogre_club\n    cost: 10",
                                 "  - item_id: ogre_club\n    cost: 25"), encoding="utf-8")
    found = [row for row in audit.check_band("ogre-hunting-party-web", audit.catalog_items())
             if row["kind"] == "item-cost"]
    assert found, "a wrong list price was not reported"


@CACHED
def test_audit_detects_a_source_row_missing_from_the_list(sandbox: Path) -> None:
    path = sandbox / "ogre-hunting-party-web" / "equipment-access.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("  - item_id: harpoon_crossbow\n    cost: 50\n", ""),
                    encoding="utf-8")
    found = [row for row in audit.check_band("ogre-hunting-party-web", audit.catalog_items())
             if row["kind"] in ("list-item-missing", "source-row-unmatched")]
    assert found, "a row the page prints was accepted although the list drops it"


@CACHED
def test_audit_detects_a_rolled_price_flattened_to_null(sandbox: Path) -> None:
    """The schema stores a rolled price as a dice expression, not as null."""
    path = sandbox / "masters-of-horror-sylv" / "equipment-access.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("    cost: 15+D6\n", "    cost: null\n"), encoding="utf-8")
    found = [row for row in audit.check_band("masters-of-horror-sylv", audit.catalog_items())
             if row["kind"] == "item-cost"]
    assert found, "a rolled list price stored as null was not reported"


@CACHED
def test_audit_detects_a_list_without_a_source_heading(sandbox: Path) -> None:
    path = sandbox / "ogre-hunting-party-web" / "equipment-access.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("  name: Ogre Equipment List",
                                 "  name: Missing Equipment List"), encoding="utf-8")
    found = [row for row in audit.check_band("ogre-hunting-party-web", audit.catalog_items())
             if row["kind"] == "list-without-source"]
    assert found, "a list the page never publishes was accepted silently"


@CACHED
def test_audit_checks_the_lists_published_under_an_h2_heading() -> None:
    """The h2 lists (Ogre, Outlaws, Sorcerous Society, Protectorate) are covered."""
    audit.STATS.clear()
    items = audit.catalog_items()
    for band in ("ogre-hunting-party-web", "outlaws-of-stirwood-forest-redux-fbg",
                 "sorcerous-society-lotd4", "protectorate-of-sigmar-lotd3"):
        audit.check_band(band, items)
    assert audit.STATS.get("lists_verified", 0) >= 6
    assert audit.STATS.get("list_levels_h2", 0) >= 5


@CACHED
def test_audit_detects_a_special_equipment_price_error(sandbox: Path) -> None:
    """The Special Equipment price is compared with the page, not trusted."""
    path = SANDBOX / "catalog" / "items" / "grave-robbers-equipment.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("Cost 15 + D6 gold crowns.", "Cost 45 gold crowns."),
                    encoding="utf-8")
    found = [row for row in audit.check_band("grave-robbers-sylv", audit.catalog_items())
             if row["kind"].startswith("special-price")]
    assert found, "a special-equipment price the page contradicts was not reported"
    assert any(row.get("verdict") != "known" for row in found), found


def test_special_equipment_prices_are_read_by_shape() -> None:
    """The prose prices of the Special Equipment sections, and their agreement."""
    shape = audit.price_shape
    assert shape("Darksteel Blade Cost: 3 x base weapon price") == ("x3",)
    assert shape("Sharp Stuff 1st Free / Second 3gc") == ("free",)
    assert shape("Pigback Mount 50 gold crowns") == (50, "", "gc")
    assert shape("Cost: 25 Warp Tokens") == (25, "", "wt")
    assert shape("Cost: 80 + 4D6 gold crowns") == (80, "4", "gc")
    assert shape("Availability: Rare 9") == ()
    assert audit.same_price((10, "", "gc"), (10, "", "")) is True
    assert audit.same_price((10, "", "gc"), (10, "", "wt")) is False
    assert audit.same_price((15, "", "gc"), (15, "1", "gc")) is False
    assert audit.same_price(("free",), ("free",)) is True


def test_cost_cells_are_read_by_shape_and_currency() -> None:
    """Flat, rolled, relative, free and non-gold prices, as the pages print them."""
    cell = audit.cost_cell_value
    agrees = audit.cost_agrees
    # flat amounts, whatever the currency: gc, crowns, warp tokens
    assert cell("10 gc") == ("flat", 10)
    assert cell("10 wt") == ("flat", 10)
    assert cell("30 Gold Crowns") == ("flat", 30)
    assert cell("1st free/2 gc") == ("flat", 2)
    assert cell("35 wt (70 for a brace)") == ("flat", 35)
    assert cell("5 gc*") == ("flat", 5)
    # a row printed without any price
    assert cell("Free!") == ("flat", 0)
    # a dice price the list itself prints
    assert cell("15 + D6 gc") == ("rolled", "15+D6")
    assert cell("45+3D6 gold crowns") == ("rolled", "45+3D6")
    assert cell("25 + 3D6 gc") == ("rolled", "25+3D6")
    # a price stated against another item
    assert cell("3x cost") == ("relative", 3)
    assert cell("2 x price") == ("relative", 2)
    # agreement
    assert agrees(10, "10 gc") is True
    assert agrees(25, "10 gc") is False
    assert agrees("15+D6", "15 + D6 gc") is True
    assert agrees(None, "15 + D6 gc") is False
    assert agrees(None, "3x cost") is True
    assert agrees(3, "3x cost") is False
    assert agrees(0, "Free!") is True


@CACHED
def test_sections_split_containers_from_their_child_lists() -> None:
    """A parent heading over child lists owns no rows; a list keeps its own.

    Druchii publishes four h3 lists under an h2 parent (a container), while
    Protectorate of Sigmar's h2 list merely contains one sub-list and keeps its
    own rows — the case the first version of the check got wrong.
    """
    druchii = audit.headings((PAGES / "druchii-mic.html").read_text(encoding="utf-8"))
    sections = audit.equipment_list_sections(druchii)
    parent = next(s for s in sections if "Druchii Equipment Lists" in s["head"])
    assert parent["children"], "the parent heading must see its child lists"
    assert all(s["children"] == [] for s in sections
               if s["head"] == "Corsair Equipment List")
    protectorate = audit.headings(
        (PAGES / "protectorate-of-sigmar-lotd3.html").read_text(encoding="utf-8"))
    main = next(s for s in audit.equipment_list_sections(protectorate)
                if s["head"].startswith("Protectorate of Sigmar"))
    assert main["children"], "the main list contains the Huntsman list"


@CACHED
def test_audit_detects_a_condensed_clarification(sandbox: Path) -> None:
    """A parenthetical clarification dropped from rule prose has to be reported.

    The Stampede, Back-up Records and Monster Slayer clarifications had all been
    condensed away with nothing noticing, because only the rule *names* were traced
    to the page.
    """
    path = sandbox / "snotlings-web" / "special-rules.yaml"
    text = path.read_text(encoding="utf-8")
    dropped = text.replace("forfeited (do not\n    count additional hand attacks). This bonus",
                           "forfeited. This bonus")
    assert dropped != text, "the clarification moved: update this test's pattern"
    path.write_text(dropped, encoding="utf-8")
    found = [row for row in audit.check_band("snotlings-web", audit.catalog_items())
             if row["kind"] == "clarification-absent"]
    assert found, "a clarification the page prints was not reported"


@CACHED
def test_audit_detects_a_dropped_item_profile_row(sandbox: Path) -> None:
    """A stat row printed inside a Special Equipment section cannot go missing.

    The Pigback Mount's profile lived only in its section's prose, so nothing —
    not ``audit_2a.py`` (which reads the page's ``div.fighter`` blocks) and not
    the catalogue checks — noticed it was absent. Removing the line from a
    throwaway catalogue has to be reported.
    """
    path = SANDBOX / "catalog" / "items" / "ogre-hunting-party-equipment.yaml"
    text = path.read_text(encoding="utf-8")
    dropped = text.replace("I3 A1 Ld5.", "A1 Ld5.")
    assert dropped != text, "the item profile line moved: update this test's pattern"
    path.write_text(dropped, encoding="utf-8")
    found = [row for row in audit.check_band("ogre-hunting-party-web", audit.catalog_items())
             if row["kind"] == "item-profile-absent"]
    assert found, "a dropped mount profile row was not reported"


def test_manifest_rows_still_name_their_source_page() -> None:
    """Every audited band keeps the slug the cache and the page snapshot use."""
    manifest = yaml.safe_load((ROOT / "sources" / "2A" / "manifest.yaml").read_text(
        encoding="utf-8"))
    rows = {row["id"]: row for row in manifest["bands"]}
    assert len(rows) == 19
    for band in sorted(p.name for p in BANDS.iterdir()):
        assert rows[band].get("slug"), f"{band} lost its page slug"
