# T13 reconciliation audit — LOT E (unresolved source/interpretation entries)

Independent reconciliation of the frozen `E-unresolved.csv` assignment (63 entries).
Read-only with respect to KB, code, registries, shared reviews, `manifest.json` and
the assignment lists. Owns only `E-unresolved-results.csv` and this summary.

- Repository: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`
- Branch / HEAD at audit: `2A2B` / `820d1499a0c9ff04fd42975d3de9d97bd62d585d`
- Working tree carried large uncommitted concurrent edits (KB, TS eligibility,
  Python construction/combat, docs) before this audit; none were touched.
- No `AGENTS.md` exists anywhere in the tree.
- Parallel writers were active in the dispatch folder during the audit (lots A, B,
  C and D results/summaries appeared across the sessions); E shares no fact with
  them except the hireling/command sources also audited by D.
- **There is no `E.csv`.** The closed assignment list for this lot is
  `E-unresolved.csv`, the row list named in `manifest.json` under `E-unresolved`.

## Input verification

| Check | Result |
| --- | --- |
| `manifest.json` `E-unresolved` sha256 | `9d47cdce06ca0e96c1788c6fe5f4585a059020f091b6130fa5e1d6a5e4130069` |
| Assignment sha256 (measured, `sha256sum`) | `9d47cdce06ca0e96c1788c6fe5f4585a059020f091b6130fa5e1d6a5e4130069` — **match** |
| `manifest.json` rows / measured data rows | 63 / 63 — **match** |
| Distinct ids / duplicate ids | 63 / 0 |

Header: `id,source_file,effect_sha256,scope,category,reason,related_target,effect_text`
(UTF-8 with BOM, CRLF; read with `utf-8-sig`). **All 63 rows are `scope=UNCLASSIFIED`,
`category=source_review`, `related_target` empty** — the defining characteristic of
this lot is that none of its entries carries a `runtime` block in the KB, so the
audit had to recover the printed clause from the original source before any scope
could be proposed. There is **no `covered` row in lot E**.

## Method

1. Re-extracted every assigned id with the maintained extraction
   (`mordheim_combat_lab.verification.audit_export.build_audit_rows(inventory_only=True)`),
   re-hashed the raw effect text and compared it with the assigned `effect_sha256`.
   **63/63 match, 0 missing, 0 drift** (`build/audit/reconciliation/E/resolve.py` →
   `context.json`). Confirmed that **no node in the lot has a `runtime` or
   `source_refs` block**; 51 entries are KB *rules* whose `effect` is a summary
   ("Uses source X rule." / "Special skill option.") and 12 are
   `@locator` nodes (9 `unresolved_references` `kind: skill`, 1 `kind: rune_system`,
   the 2 Armen Abbas `equipment/.../notes`).
2. Resolved each unresolved *name* to a current KB counterpart (`grep` over
   `sources/knowledge/`): `Righteous Fury` → `catalog/skills/warband.yaml#skill.righteous-fury`;
   `Elixir of Life` / `Grizzled Veteran` / `Lightning Speed` / `Leap of Faith` /
   `Swashbuckler` → band-scoped rules (`bands/mordheim/{amazons-lustria,pit-fighters,battle-monks-of-cathay,pirates}/special-rules.yaml`);
   `Garlic` → `catalog/items/miscellaneous.yaml:566-577`. `Death without a face` and
   `Weapon Master` have **no** KB record.
3. **Recovered the printed definitions from the original sources** (all HTTP 200,
   read 2026-10-05) and transcribed the admitted/excluded clauses:
   - Hired Swords: `https://mordheimer.net/docs/campaigns/hired-swords/grade-1a|grade-1b|grade-1c|grade-2a`
     (Beast Hunter, Imperial Assassin, Roadwarden, Tilean Marksman, Runesmith
     Journeyman, Shadow Warrior, Snake Charmer, Tomb Robber, Witch, Black Orc
     Overseer, Clan Skryre Rat Ogre, Human Scout, Kislev Ranger, Mule Skinner,
     Cathayan Merchant, Chaos Centaur, Hobgoblin Scout, Pyromaniac, Swordsmith,
     Goblin Lantern Bearer, Imperial Tactician, Knight of the White Wolf, Ninja
     Gnoblar, Swashbuckler, Ungor Trapper, Chaos Fury, Ninja, Witch Hunter…).
   - Dramatis Personae: `https://mordheimer.net/docs/campaigns/dramatis-personae/grade-1a|grade-1b|grade-1c|grade-2a`
     (Ulli & Marquand, Abdul Alhazred, Crow Master, Drenok Johansen, Khar-mel,
     Penthesilea, Ippan Shu, Innominatus, Luthor the Looter, Luthor Wolfenbaum,
     William Schäkestange) and `https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf`
     p16 (Armen Abbas REL items).
4. Traced every admitted clause to a current consumer: the modular engine
   supported-tag set (`kernel.py:109`), the fear/leadership/psychology consumers
   (`modular/leadership.py`, `modular/psychology.py`, `modular/contexts.py:97-120,214,297`),
   the save operator (`compiler.py:504` → `phases.py:477`, `EffectSet.ward_save`),
   `mechanic.psychology-immunity`, `mechanic.stupidity`, `mechanic.leader-six`,
   `mechanic.fear-reroll`, the Animal Handling mechanic
   (`compiler.py:452` → `modular/rounds.py:296-300`), and the Amazons (Lustria) band
   package (`mechanic.amazon-isolationists` → `contexts.py:121`, `vectorized/_attacks.py:256`).

Scratch tooling/evidence: `build/audit/reconciliation/E/`
(`resolve.py`, `analyze.py`, `classify.py`, `overrides.py`, `overrides_extra.py`,
`finalize.py`, `context.json`, `enriched.json`, `results.csv`).

## Result counts

63 result rows, one per assigned id, exact 16-column order, UTF-8/LF, no BOM.

| Family (source file) | n | out_of_scope | connection_gap | implementation_missing | partial | metadata_gap | source_blocked | decision_required |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `catalog/hirelings/dramatis-personae/core.yaml` | 1 | | 1 | | | | | |
| `catalog/hirelings/dramatis-personae/grade-1a.yaml` | 1 | 1 | | | | | | |
| `catalog/hirelings/dramatis-personae/grade-1b.yaml` | 8 | 2 | 2 | 2 | | 1 | 1 | |
| `catalog/hirelings/dramatis-personae/grade-1c.yaml` | 6 | 3 | | | | 2 | | 1 |
| `catalog/hirelings/dramatis-personae/grade-2a.yaml` | 1 | | | | | 1 | | |
| `catalog/hirelings/dramatis-personae/grade-2b.yaml` | 2 | | | | | 2 | | |
| `catalog/hirelings/hired-swords/grade-1a.yaml` | 6 | 3 | 2 | 1 | | | | |
| `catalog/hirelings/hired-swords/grade-1b.yaml` | 15 | 10 | 2 | | 1 | 1 | | 1 |
| `catalog/hirelings/hired-swords/grade-1c.yaml` | 12 | 7 | 2 | | 1 | 2 | | |
| `catalog/hirelings/hired-swords/grade-2a.yaml` | 10 | 8 | 1 | 1 | | | | |
| `catalog/rules/special-rules.yaml` | 1 | | | | | | | 1 |
| **Total** | **63** | **34** | **10** | **4** | **2** | **9** | **1** | **3** |

`proposed_scope`: **23 `YES`, 34 `NO`, 6 `UNCLASSIFIED`**. The 6 `UNCLASSIFIED`
are the 1 `source_blocked`, the 3 `decision_required` and the 2 Armen Abbas
equipment notes (intentionally dangling). `out_of_scope ⇔ proposed_scope=NO` holds.

## Admitted-clause gaps (grouped)

- **G1 — Source-recovered duel clauses with an existing but unbound operator
  (10 `connection_gap`).** The printed clause maps to a tag the engine already
  consumes, but the KB rule is a summary with no `binding`: Righteous Fury →
  `skill.righteous-fury`; Sabertooth Tiger Hide (Drenok) → the save operator
  (`ward_save`, with the 6+ close-combat / 5+ missile split exceeding the single
  field); Penthesilea `Amazon` → the Amazons (Lustria) band package
  (`mechanic.amazon-isolationists`, `mechanic.mesmerising-dance`); Skull Rack
  (causes fear in Beastmen) → `mechanic.causes-fear`; Roadwarden `Stern` →
  `mechanic.fear-reroll`; Clan Skryre `Bio-machinery` → `mechanic.psychology-immunity`;
  Tomb Robber `Excellent Reflexes` (5+/4+ special save) → `ward_save`; Chaos Centaur
  `Drunken` → `mechanic.stupidity`+frenzy; Swordsmith `Honing` → a Cutting Edge
  operator (target to locate); Knight of the White Wolf `Pride` → `mechanic.leader-six`.
- **G2 — Real duel clauses with no operator at all (4 `implementation_missing`).**
  Crow Master `Mantle of Crows` (automatic S2 hit to base contact at the start of
  the hand-to-hand phase); Khar-mel `Djinn's Curse` (proximity aura: −1 to hit and
  −1 to saves within 4"); Imperial Assassin `Backstabber` (charge bonus +1 to
  hit/injury vs an opponent he cannot see); Swashbuckler `Charismatic` (an
  opposite-sex opponent must pass a Leadership test to charge). The `sex.*` facts
  exist but no charge-gating psychology operator consumes them.
- **G3 — Partly-admitted clauses (2 `partial`).** Witch `Potions`: the lasting
  characteristic change is a supplied stat fact (admitted) but the pre-battle D6
  draught is non-duel. Hobgoblin Scout `Traitor`: the Scout is *subject to* the
  greenskin hatred (admitted) but no reciprocal hatred/recipient fact exists; the
  "may never hire other greenskins" clause is campaign.
- **G4 — Unresolved skill identities and one skill-grant (9 `metadata_gap` + 1
  `source_blocked`).** Band-scoped counterparts exist for `Elixir of Life`
  (note: the band rule is itself `unimplemented.amazons-lustria…`), `Grizzled
  Veteran`, `Lightning Speed`, `Leap of Faith` and `Swashbuckler` — no global
  canonical skill id links the hireling reference. `Death without a face` has a
  printed definition (*Causes fear*) but no canonical record. Mule Skinner
  `Animal Handler` grants one Animal Handling skill while the handling mechanic
  (`animal_handler_leadership`) is consumed but unbound. `Weapon Master` is named on
  the source page with **no** definition and no KB record → `source_blocked`.
- **G5 — REL-specific dangling equipment (2 `metadata_gap`).** Armen Abbas's
  `stickfire` and `vermin pots` are recorded in `grade-2b.yaml` with only a
  "define at promotion" note and no catalog record (`broheim REL p16`).

## Out-of-scope decisions (34 rows, `proposed_scope=NO`)

Every `out_of_scope` row carries an explicit `excluded_clause`; none is a silent
exclusion. They fall in the governing 1v1 boundary (group Rout/psychology,
movement, deployment, terrain, shooting/spell resolution, mounts/third
participants, post-duel capture/retention, escape):

- **Shooting / templates (8):** Lethal Marksman, Steady Hands, Expert Hunter,
  Hunter's Cloak, Fire Breath (Way of the Dragon), Crazed Firestarter,
  Display Artist, Rocket Science.
- **Movement / terrain / deployment (6):** Whirlwind, Predator (wilderness setup),
  Animal Call, Expert Tactician, Expert Rooftop Jumper, Acrobatic.
- **Group psychology / Rout (3):** Black Orc Overseer (animosity suppression +
  leader replacement), Goblin Lantern Bearer `Smart` (animosity), Imperial
  Tactician `Read the Battle` (group Rout).
- **Post-duel consequences (3):** `I Ain't Got Time` (escape from combat),
  `Evil Eye` (permanent-injury table), Kislev Ranger `Herb Lore` (recovery phase).
- **Campaign economy / retention / upkeep (9):** Human Scout `Not a Fighter`
  (post-game retention), Snake Charmer `Snake Hunter`, Runesmith (pre-battle
  inscription + trading), Cathayan Merchant `Stone-Cutter`, Swordsmith
  `Master Craftsman`, Swordsmith `Farrier` (mounts), Shadow Warrior `Bitter
  Enemies` (upkeep), Knight of the White Wolf `Among Wolves` (upkeep), Ungor
  Trapper `Just a Twit` (post-game retention).
- **Multiplayer / behaviour / third participant (4):** Ulli & Marquand
  `A Fistful of Crowns` (bribery), Abdul Alhazred `Djinn Master` (Lamp table),
  Chaos Fury `Malicious` (movement-phase torture), Cathayan Merchant `Guardian`
  (bodyguard actor).
- **Pre-battle inscription (1):** Runesmith `Rune Use` `unresolved_reference`.

## Decisions needed (recorded, not resolved by this audit)

- **`shared-rule.free-the-slaves` (`decision_required`, F001).** "Pit Fighters hate
  slavers" — whether narrative dislike is formal Hatred and whether a `slaver`
  opponent identity fact should exist. The captive-selling clause is campaign-only.
- **Garlic (`decision_required`, F036).** The item record is
  `combat_status: out_of_scope` (`catalog/items/miscellaneous.yaml:566-577`) while
  its clause ("a Vampire must pass a Leadership test or cannot charge a Garlic
  carrier") is a charge interaction; the contact-gating boundary needs a ruling.
- **Innominatus `Who is the hero?` (`decision_required`, F036).** Whether the
  once-per-battle forced-duel trigger belongs to the 1v1 boundary; the accepted
  fight can be resolved by the melee engine, but the challenge selection, the
  removal of a refusing model and the Thumbs Up/Down consequences are campaign/roster.

## Recommended next implementation groups

1. **G1 bindings** — smallest, reuse existing operators (especially `ward_save`,
   `mechanic.causes-fear`, `mechanic.fear-reroll`, `mechanic.psychology-immunity`,
   `mechanic.leader-six`, `mechanic.stupidity`). Blocked on nothing.
2. **G4 canonical skill identities** — add canonical records for the five band-scoped
   skills, `Death without a face` and the Animal Handling grant, then link the
   hireling references.
3. **G2 new operators** — start-of-combat automatic hit, proximity to-hit/save aura,
   charge-backstab bonus, charge-gating psychology.
4. **Decisions** — resolve F001 (Free the Slaves) and the Garlic / Who-is-the-hero
   boundary calls before binding their clauses.
5. **G5 REL items** — define the Armen Abbas `stickfire`/`vermin pots` or mark the
   REL subset as unmodelled.

## Checks actually run vs inspection-only

- **Executed:** the maintained extraction re-run and 63/63 re-hash
  (`build/audit/reconciliation/E/resolve.py`, `analyze.py`); the assignment
  hash/row-count check (`sha256sum`, 63 rows); the results-file structural
  validation (16 columns, 63 unique ids equal to the assignment, status vocabulary,
  `out_of_scope ⇔ proposed_scope=NO`, no empty evidence/next-action/closure,
  UTF-8/LF, no BOM) in `finalize.py`; targeted read-only KB greps and
  `load_*` loads of the hireling/skill/item/band YAML; direct reads of the
  maintained external source pages (mordheimer.net HTTP 200) via the browser.
- **Inspection-only (not executed behaviour):** every listed operator/consumer
  claim is code inspection of the current tree (`kernel.py:109`, `contracts.py`,
  `compiler.py:452,504`, `phases.py:477`, `modular/*.py`, `TRAIT_TYPES`). No new
  semantic test was written and no per-entry integration campaign was run, per the
  dispatch. No unexecuted check is labelled as passed.

## Concurrent drift and closure

- Other lots' deliverables (A/B/C/D) appeared in this folder across the sessions;
  the assignment list, `manifest.json` and shared registries were not modified by
  this lot.
- **Closure revalidation:** `E-unresolved.csv` sha256 re-measured at closure equals
  the manifest value `9d47cdce…0069` with 63 data rows; the retained results file
  reproduces 63/63 rows with unique ids equal to the assignment. Any later edit to
  the hirelings catalogue (`dramatis-personae/*`, `hired-swords/*`),
  `catalog/rules/special-rules.yaml`, `catalog/items/miscellaneous.yaml`,
  `catalog/skills/warband.yaml` or the band `special-rules.yaml` files invalidates
  the affected rows' hashes and must re-open them.
