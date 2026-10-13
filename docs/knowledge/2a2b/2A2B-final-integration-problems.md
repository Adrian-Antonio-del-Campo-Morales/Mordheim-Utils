# 2A/2B — Contradictions and open items after the final consolidation

Written when `sources/2A` and `sources/2B` were retired (2026-10-08). Every item
below is either a **contradiction between a printed source and the canonical KB**
or a **decision with no home in the current schema**. Each one carries the exact
IDs, the source text that was available, the next action and the criterion that
closes it. Nothing here is resolved by assumption: where a reading is uncertain,
the uncertainty itself is the recorded finding.

The reconciled part of the batch (68 band documents and 12 hireling profiles the
canonical KB had already moved past) is *not* a problem list: it is recorded in
[2A2B-Knowledge.md](2A2B-Knowledge.md) §6.

## 1. Sea Dragon Cloak — `druchii-mic` page contradicts KB `sea_dragon_cloak`

- **IDs:** band `druchii-mic`; KB item `sea_dragon_cloak`
  (`sources/knowledge/catalog/items/shields-and-defences.yaml`), source
  `mordheimer.net` grade-1b *dark-elves*.
- **Contradiction (two axes).**
  1. *Combination.* KB: “cannot combine with other armour”. Page
     (`https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii`, section
     *Scales*): “A Sea Dragon Cloak **may be combined** with other pieces of
     armour (shield, light armour) with no penalty.”
  2. *Numbers.* KB: “Grants a 5+ save in close combat and 4+ against shooting”.
     Page: “a **+2 bonus** to his save against shooting (or in the event where he
     has none, a 5+ save) and a **+1 bonus** to his save in close combat (or, if
     he has none, a 6+ save).”
- **State:** the 2A package referenced the canonical `item_id` and never
  re-printed the page's version, so the page variant is **not modelled anywhere**.
  The page text above is the only surviving copy of it.
- **Next action:** decide between (a) canonical text + a `source_ref` to the
  `druchii` page documenting the variant, or (b) a separate variant item for the
  page's own Cloak. Precedent for (a): 2B `dragon_cloak` → `sea_dragon_cloak`.
- **Closes when:** the variant is either recorded in that item's `source_refs` or
  modelled under its own `item_id`, and no reader has to choose between two
  contradictory saves for one item.

## 2. Draich *Swift* — `druchii-mic` page contradicts KB `draich`

- **IDs:** band `druchii-mic`; KB item `draich`
  (`sources/knowledge/catalog/items/trollheim.yaml`, mechanic `weapon.draich`,
  “strikes last”).
- **Contradiction.** Page: “Range: Close combat · Strength: As user +2 · Special
  Rules: Two-handed, **Swift**. *Swift: A Draich, unlike other double-handed
  weapons, does not Strike last.*” The KB models a Draich that **does** strike
  last.
- **State:** the 2A package referenced the canonical `item_id`; the printed *Swift*
  rule is modelled nowhere. Page text above is the only surviving copy.
- **Next action:** same two exits as item 1.
- **Closes when:** the *Swift* variant is recorded in the item's `source_refs` or
  modelled under its own `item_id`.

## 3. Dwarf Axe — re-roll of a failed parry with two axes is not implemented

- **IDs:** band `dwarf-slayer-cult-web`; mechanic `weapon.dwarf-axe`;
  `rules/resolution.yaml` (`reroll: {sword_and_buckler: one_reroll_of_failed_parry,
  two_swords: no_reroll}`).
- **Contradiction:** the page prints “a model armed with two dwarf axes (or a dwarf
  axe and a sword, etc) does not get to parry two attacks but may instead re-roll
  a failed parry”. The resolution table fixes `two_swords: no_reroll`, so the
  printed re-roll is lost.
- **Next action:** extend the item mechanic / resolution table, or record the
  engine gap against `dwarf-slayer-cult-web`.
- **Closes when:** the axe-plus-axe case has a resolved outcome and a check that
  fails if it regresses.

## 4. Band starting currency has no schema field

- **IDs:** `skaven-of-clan-moulder-web` (“You have **500 warp tokens** (equivalent
  to gold crowns)”, `sources/2A`); 2B `currency: dinars` and `currency: warp
  tokens` rows plus the `currency_note` of Clan Pestilens.
- **Gap:** the band contract has no currency field (`band.yaml` keeps
  `id`/`name`/…/`roster`/`rule_ids`/`variants`; roster members keep
  `profile_id`/`minimum`/`maximum`/`group_size`). Moulder's
  `starting_gold_currency`/`starting_gold_note` were withdrawn in the conformance
  pass for not being KB shape. The equivalence statement (“warp tokens equivalent
  to gold crowns”) therefore has nowhere canonical to live, although the per-list
  notes still print the currency per row.
- **Next action:** decide the single shape (documented band field applied to both
  packs, or a note) and apply it once.
- **Closes when:** the statement is stored in the band schema and no pack keeps a
  withdrawn key.

## 5. Cold One Hounds of `dark-elf-corsairs-mou` are prose, not profiles

- **IDs:** band `dark-elf-corsairs-mou`, rule `band--roster`.
- **State:** the two Cold One Hounds stay described inside the roster rule text
  (faithful to the source); separating them into their own profile is a modelling
  decision that was never taken.
- **Next action:** decide profile or prose, once, and keep the source text either
  way.
- **Closes when:** the decision is recorded and the band reads the same way in both
  artefacts.

## 6. Historical staging paths inside the maintained CSVs

- **IDs:** `docs/knowledge/2a2b/tasks/T13-obligations.csv` — 1692 rows carry
  `origin_key`/`origin_source` pointing at `sources/2A/...` and `sources/2B/...`
  (e.g. `sources/2A/bands/mordheim/dreamwalkers-cult-of-morr-fbg/special-rules.yaml`).
  `docs/knowledge/2a2b/tasks/T13-semantic-analysis.csv` line 910 cites
  `sources/2B/catalog/promotion-merge-notes.md` in prose.
- **Not a defect:** the column is historical provenance (`origin_key` is an
  identity, and the row's hashes are over the reviewed rule text, not the file).
  No maintained tool or test resolves these paths, and the canonical destination
  is present in the same row (`canonical_file`, `canonical_id`).
- **Next action:** none. Rewriting 1692 identities would lose the link to the
  report they were reconciled against.
- **Closes when:** — (kept open only as a note for readers of those columns).
