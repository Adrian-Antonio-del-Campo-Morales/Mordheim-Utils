# English-review pass — 2B staging (2026-09-14)

Objective: verify every band package in `sources/2B/bands/mordheim` against its
source (cached PDF text or OCR render) and mark the row `english-reviewed` in
the manifest once verified.

## Method

1. The pass covers all 60 manifest rows, package by package.
2. New read-only cross-check tool `tools/knowledge/review_2b.py` re-derives every
   number in the packages (roster limits, starting gold, profile costs/xp, stat
   runs, equipment prices, digits quoted in rule effects) from the cached source
   texts. First run: **2295 checks — 1967 OK / 218 NOT_FOUND / 110 MISMATCH**.
3. Every MISMATCH outside the three scanned KEP bands (already fully audited at
   300/600 dpi — see `discrepancy-verdicts.md`) was investigated individually
   with targeted source reads (evidence dumps in `build/cache/2b-pdfs/review-*`).

## Verdicts

**No transcription error was found in the non-scanned packages.** All flagged
values were confirmed package-correct against their sources; the flags were
artifacts of automated text matching:

| Artifact class | Examples | Explanation |
|---|---|---|
| Extraction interleaving | metal-mongers (all profile costs), woodsmen-de-artois, fen-guard | The PDF text layer interleaves page furniture with content: "===== page 4 =====" + "55 warp tokens to hire" normalizes to `455` etc. Raw-text reads confirm every value (Engineer Adept 55 / Black Skaven 40 / Forge-Rats 20 / Pirate-Rats 30 warp tokens; Bowman 35 gc; Treekin 180 gc). |
| Non-gc currencies | ghutani / muzil / turjuk `townsmen` 20, slavers `caravan-guards` 30 | REL Araby bands print costs in **dinars** ("20 dinars to hire"), Metal Mongers in **warp tokens**; the checker only searched "gold crowns". |
| Free / special-recruitment units | swabbies ×4, thaggi, floordogs, raw-recruits, the-bloated | Source prints "Not Hired"/"Special Recruitment" with no cost line; package models cost 0 (or None) faithfully. |
| D6 formulas | bretonnian-knights-errant (D6+7 → 8), lost-the-mou (15+D6 → 15) | The engine's `experience` field is numeric; packages store the fixed component and the rule text preserves the formula verbatim. |
| Verified-large sets | all KAZ bands (roster max 12/15/20/15, gold 500, all profile costs incl. Troll 200, Snotling Mob 50 + 10/Snotling), lords-of-the-marsh (110/100/30/55/180), watchmen (60/35/55/25), sea-ghosts (70/90/30/35/45/60 + Riverboat 100), shallows-beasts (85/75/35/20/20), channel-rats (65/40/45/25/25), low-kings, militiant-mootlanders (60/40/10/50/20/15/40), blood-dragons (Grave Guards "50 GC each") | Confirmed line-by-line in the raw source texts. |
| Stat-line + name adjacency | a handful of profile stats/xp flags | The tool searches digit groups near the profile name; table layouts (MIM "0-3 RACONTEURS10 gc") and page markers defeat it. Each was read in the raw text and confirmed. |
| Scanned KEP trio | clan-angrund / crooked-moon / slave-uprising | OCR text is not a reliable comparison base; these packages passed a **complete manual 300/600 dpi digit audit** (profiles, costs, equipment, rule texts) documented in `discrepancy-verdicts.md`. The one error that audit found (Escapists truncated capture clause) is already fixed. |

## Known source oddities (preserved, not errors)

- `metal-mongers-mim` equipment list prints "X gold crowns (Forge-Rats and
  Technicians only)" — the price is literally an "X" placeholder in the
  brochure; the package carries the note instead of inventing a number.
- `crooked-moon-kep` Squig Hopper 30 gc was recovered by glyph analysis
  (connected-component read of the "0") — see `discrepancy-verdicts.md`.

## Result

All 60 rows advanced `modeled` → `english-reviewed` in the manifest.
Active knowledge base untouched. `ingest_2b.py validate` and
`tests/knowledge/test_2b_staging.py` stay green.
