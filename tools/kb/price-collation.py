#!/usr/bin/env python
"""Collate every band ``equipment-access.yaml`` ``cost`` against the Trading Post.

Purpose
-------
The KB keeps the historical ``cost`` values of the warband equipment lists as
evidence of the printed lists (see ``sources/knowledge/catalog/campaign/
README.md``). They are not a market price: the Trading Post of
``campaign/trading-post.yaml`` is the canonical market source, and a warband
list amount is only authoritative when it is a confirmed exception expressed
as ``price_override`` with its source.

This tool runs that comparison for *every* warband of *every* collection and
classifies each row so a reviewer can decide, per the migration TODO:

1. ``no-market``        — no Trading Post row exists for the item (or the TP
                          row is ``not sold``): the warband list is the only
                          price source; nothing to collate.
2. ``relative-tp``      — the Trading Post price is multiplier-based (e.g.
                          Gromril 4x base); a flat list cost cannot be
                          compared without the base record.
3. ``consistent``       — list ``cost`` equals the Trading Post base price.
4. ``consistent-special`` — list ``cost`` equals the Trading Post base while
                          the TP price also carries a variable part, ``per``
                          or ``purchase_options``; worth a glance for pairs.
5. ``differs`` / ``differs-special`` — list ``cost`` differs from the Trading
                          Post price: the review queue. Each row must be
                          checked against its band page to confirm either a
                          published exception (record ``price_override``) or
                          a source discrepancy (keep ``cost`` as evidence;
                          the Trading Post prevails).
6. ``override``         — a ``price_override`` already exists on the row;
                          confirm it still matches the collated expectation.

Output
------
- ``<outdir>/price-collation.md`` — summary counts plus every non-consistent
  row grouped by warband (the review queue).
- ``<outdir>/price-collation.csv`` — the full machine-readable comparison of
  every cost row.

The tool never edits YAML: recording ``price_override`` is an editorial step
performed after source verification (see the HOWTO).

Usage
-----
    python tools/kb/price-collation.py [--outdir docs/knowledge] [--collection mordheim]
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from mordheim_knowledge.campaign import load_campaign_catalog
from mordheim_knowledge.loader import BandPackage, load_bands, load_collections, load_items

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTDIR = ROOT / "docs" / "knowledge"

#: TP availability kinds that mean the market row carries no sellable price.
NOT_SOLD_KINDS = frozenset({"not_sold"})


def _price_base(price: dict) -> int | None:
    base = price.get("base_gc") if price else None
    return int(base) if isinstance(base, (int, float)) else None


def _price_special(price: dict) -> bool:
    """True when the TP price is not a plain flat base (dice, multiplier, per)."""
    return bool(
        price
        and (price.get("optional_variable_cost") or price.get("multiplier") or price.get("per"))
    )


def _entry_mentions_band(entry: dict, band_id: str) -> bool:
    for restriction in entry.get("restrictions") or ():
        if restriction.get("type") not in ("warband_only", "warband_forbidden"):
            continue
        if band_id in set(restriction.get("band_ids") or ()):
            return True
    return False


def _tp_by_item(entries: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        index[str(entry.get("item_id") or "")].append(entry)
    return index


def select_tp_entry(rows: list[dict], band_id: str) -> dict | None:
    """Pick the Trading Post row for an item; honour band-specific rows.

    Several items have both a generic Trading Post row and warband-restricted
    rows (e.g. ``double_barrelled_pistol``: generic 25+D6, Ostlander 30). When
    a row's ``warband_only`` restriction names the collated band it is the
    market row that band must be compared against.
    """
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    for entry in rows:
        if _entry_mentions_band(entry, band_id):
            return entry
    return rows[0]


def _tp_label(entry: dict | None) -> str:
    if entry is None:
        return ""
    price = entry.get("price") or {}
    base = _price_base(price)
    parts = []
    if base is not None:
        parts.append(f"{base} gc")
    if price.get("optional_variable_cost"):
        parts.append("+ dice")
    if price.get("multiplier"):
        parts.append(f"x{price['multiplier']}")
    if price.get("per"):
        parts.append(f"per {price['per']}")
    if not parts:
        return "(not sold)"
    return " ".join(parts)


def collate(ruleset: str = "mordheim") -> list[dict]:
    """Return one comparison row per equipment-access cost entry."""
    catalogue = load_campaign_catalog(ruleset)
    tp_entries = catalogue.catalogue("trading-post.yaml").get("items") or ()
    tp_index = _tp_by_item(list(tp_entries))
    items_by_id = {str(row.get("id") or ""): str(row.get("name") or "") for row in load_items(ruleset)}

    rows: list[dict] = []
    for collection_row in load_collections():
        collection = str(collection_row.get("id") or "")
        packages = load_bands(collection)
        for package in packages:
            band_id = str(package.band.get("id") or "")
            for equipment_list in package.equipment_lists:
                list_id = str(equipment_list.get("id") or "")
                list_name = str(equipment_list.get("name") or list_id)
                source = equipment_list.get("source") or {}
                for item in equipment_list.get("items") or ():
                    cost = item.get("cost")
                    if not isinstance(cost, (int, float)):
                        continue
                    item_id = str(item.get("item_id") or "")
                    override = item.get("price_override")
                    tp_entry = select_tp_entry(tp_index.get(item_id, []), band_id)
                    status, tp_base = "no-market", None
                    if override is not None:
                        status = "override"
                    elif tp_entry is None or (tp_entry.get("price")) is None or (
                        (tp_entry.get("availability") or {}).get("kind") in NOT_SOLD_KINDS
                    ):
                        status = "no-market"
                    else:
                        price = tp_entry["price"] or {}
                        tp_base = _price_base(price)
                        if tp_base is None:
                            status = "relative-tp"
                        elif _price_special(price):
                            status = "consistent-special" if tp_base == int(cost) else "differs-special"
                        else:
                            status = "consistent" if tp_base == int(cost) else "differs"
                    rows.append({
                        "collection": collection,
                        "band_id": band_id,
                        "band_name": str(package.band.get("name") or band_id),
                        "list_id": list_id,
                        "list_name": list_name,
                        "item_id": item_id,
                        "item_name": items_by_id.get(item_id, item_id),
                        "list_cost": cost,
                        "override": override if isinstance(override, (int, float, dict)) else None,
                        "tp_entry": tp_entry["id"] if tp_entry else "",
                        "tp_price": _tp_label(tp_entry),
                        "tp_availability": str(((tp_entry or {}).get("availability") or {}).get("kind") or ""),
                        "status": status,
                        "verified_note": "",
                        "source_url": str(source.get("url") or ""),
                        "source_section": str(source.get("section") or ""),
                    })
    return rows


def _band_summary(rows: list[dict]) -> dict[str, Counter]:
    summary: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        summary[row["band_id"]][row["status"]] += 1
    return summary


def load_resolutions(outdir: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """Page-verified verdicts: (band_id, item_id) -> (outcome, note).

    Outcomes: ``creation-price`` (the printed list price is a creation price;
    the Trading Post prevails at the market) or ``override`` (recorded as
    ``price_override``). Maintained next to the generated report so manual
    page verdicts survive regeneration.
    """
    path = outdir / "price-collation-resolutions.csv"
    result: dict[tuple[str, str], tuple[str, str]] = {}
    if not path.exists():
        return result
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (str(row.get("band_id") or ""), str(row.get("item_id") or ""))
            result[key] = (str(row.get("outcome") or ""), str(row.get("note") or ""))
    return result


def apply_resolutions(rows: list[dict], resolutions: dict[tuple[str, str], tuple[str, str]]) -> None:
    """Mark page-verified rows; override rows must match the recorded YAML."""
    for row in rows:
        verdict = resolutions.get((row["band_id"], row["item_id"]))
        if verdict is None:
            continue
        outcome, note = verdict
        if outcome == "creation-price" and row["status"].startswith("differs"):
            row["status"] = "creation-price"
            row["verified_note"] = note
        elif outcome == "override" and row["status"] != "override":
            print(f"warning: sidecar expects override for {row['band_id']}/{row['item_id']} "
                  f"but the YAML has none")
        elif outcome == "override":
            row["verified_note"] = note


def write_markdown(rows: list[dict], target: Path) -> None:
    """Summary + the review queue + verified creation-price rows."""
    total = Counter(row["status"] for row in rows)
    queue = [row for row in rows if row["status"].startswith("differs") or row["status"] == "override"]
    queue.sort(key=lambda r: (r["band_id"], r["list_name"], r["item_name"]))
    verified = [row for row in rows if row["status"] == "creation-price"]
    verified.sort(key=lambda r: (r["band_id"], r["item_name"]))
    by_band = _band_summary(rows)

    lines = [
        "# Trading Post price collation",
        "",
        f"_Regenerate with `python tools/kb/price-collation.py`._  ",
        f"_Compared every `cost` of every `equipment-access.yaml` against `campaign/trading-post.yaml`"
        f" ({total.total()} rows across {len(by_band)} warbands)._",
        "",
        "## Status counts",
        "",
        "| Status | Rows | Meaning |",
        "|---|---|---|",
        "| `no-market` | {0} | No Trading Post sellable row: list price stands, nothing to collate |".format(total["no-market"]),
        "| `relative-tp` | {0} | Trading Post price is multiplier-based; compare via the base record |".format(total["relative-tp"]),
        "| `consistent` | {0} | List cost equals the Trading Post base price |".format(total["consistent"]),
        "| `consistent-special` | {0} | Matches the TP base; TP also has a variable part/`per` (pairs — glance) |".format(total["consistent-special"]),
        "| `differs` | {0} | List cost differs from a flat Trading Post price |".format(total["differs"]),
        "| `differs-special` | {0} | List cost differs from a TP price with dice/per part |".format(total["differs-special"]),
        "| `creation-price` | {0} | Page-verified creation price; the Trading Post prevails at the market |".format(total["creation-price"]),
        "| `override` | {0} | `price_override` already recorded |".format(total["override"]),
        "",
        "## How to read a differing row",
        "",
        "A warband equipment list is the **creation/recruitment** price list of",
        "its printed source; the Trading Post is the **market** price used when",
        "the item is bought outside the list (post-battle). The two may differ",
        "by design, so a difference alone is not an exception. An override is",
        "recorded only when the warband's own source confirms that the list",
        "amount is what the warband pays as a market price too:",
        "",
        "- Nuln *Impeccable Care*: reduced black-powder weapon costs apply always.",
        "- Hochland *Powder's Expensive!*: bandit heroes always pay the higher",
        "  black-powder weapon costs of the Duelist list.",
        "- Lizardmen *Armour*: light armour always costs 50 gc for Lizardmen,",
        "  including from the Equipment chart.",
        "",
        f"{total['override']} rows carry a `price_override` and "
        f"{total['creation-price']} differing rows were page-verified as plain",
        "creation prices (the list price is what a recruit pays; the Trading",
        "Post prevails at the market). Remaining differing rows keep their list",
        "`cost` as historical evidence and stay in the queue until each printed",
        "source is verified; rows whose warband has no recorded source URL",
        "(Trollheim/Lustria/Khemri settings) are part of that queue.",
        "",
        "## Review queue (per warband)",
        "",
    ]
    if not queue:
        lines.append("_No differing rows: every list cost is consistent with the Trading Post._")
    current_band = None
    for row in queue:
        if row["band_id"] != current_band:
            current_band = row["band_id"]
            counts = by_band[current_band]
            lines += [
                "",
                f"### {row['band_name']} (`{row['collection']}/{current_band}`)",
                "",
                f"- Source: {row['source_section']} — {row['source_url']}",
                f"- Differing rows: {counts.get('differs', 0) + counts.get('differs-special', 0)};"
                f" overrides recorded: {counts.get('override', 0)}",
                "",
                "| Item | List cost | Trading Post | TP entry | Status | `price_override` |",
                "|---|---|---|---|---|---|",
            ]
        override = "—"
        if row["override"]:
            if isinstance(row["override"], dict):
                override = str(row["override"].get("base_gc") or row["override"].get("optional_variable_cost") or row["override"])
            else:
                override = f"{row['override']} gc"
        lines.append(
            f"| {row['item_name']} (`{row['item_id']}`) | {row['list_cost']} gc | {row['tp_price']} |"
            f" `{row['tp_entry']}` | {row['status']} | {override} |"
        )
    lines += ["", "## Verified creation prices (page-checked; Trading Post prevails)", ""]
    if not verified:
        lines.append("_None yet — every differing row is still pending page verification._")
    current_band = None
    for row in verified:
        if row["band_id"] != current_band:
            current_band = row["band_id"]
            lines += ["", f"### {row['band_name']} (`{row['band_id']}`)", "",
                      "| Item | List cost | Trading Post | Verdict note |", "|---|---|---|---|"]
        note = row.get("verified_note") or "Printed list price confirmed on the warband page; creation price."
        lines.append(f"| {row['item_name']} (`{row['item_id']}`) | {row['list_cost']} gc | {row['tp_price']} | {note} |")
    lines += ["", f"_Generated from the KB loaders; {total.total()} equipment-access cost rows checked._", ""]
    target.write_text("\n".join(lines), encoding="utf-8")


def write_csv(rows: list[dict], target: Path) -> None:
    fields = [
        "collection", "band_id", "band_name", "list_id", "list_name", "item_id", "item_name",
        "list_cost", "override", "tp_entry", "tp_price", "tp_availability", "status",
        "verified_note", "source_url", "source_section",
    ]
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["collection"], r["band_id"], r["list_name"], r["item_name"])):
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR, help="report directory (default: docs/knowledge)")
    parser.add_argument("--ruleset", default="mordheim")
    args = parser.parse_args()

    rows = collate(args.ruleset)
    args.outdir.mkdir(parents=True, exist_ok=True)
    resolutions = load_resolutions(args.outdir)
    apply_resolutions(rows, resolutions)
    markdown = args.outdir / "price-collation.md"
    csv_path = args.outdir / "price-collation.csv"
    write_markdown(rows, markdown)
    write_csv(rows, csv_path)

    counts = Counter(row["status"] for row in rows)
    queue = counts.get("differs", 0) + counts.get("differs-special", 0)
    bands = sorted({row["band_id"] for row in rows if row["status"].startswith("differs")})
    print(f"checked {len(rows)} cost rows across {len({r['band_id'] for r in rows})} warbands")
    print("statuses:", dict(counts))
    print(f"review queue: {queue} differing rows in {len(bands)} warbands")
    print(f"reports: {markdown.relative_to(ROOT)}  {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
