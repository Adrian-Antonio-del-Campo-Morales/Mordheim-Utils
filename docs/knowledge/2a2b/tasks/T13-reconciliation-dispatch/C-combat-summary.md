# Lot C — combat reconciliation summary

Independent reconciliation audit of the frozen **C-combat** assignment
(243 entries). Read-only with respect to KB, code, shared registers and
assignment lists. Deliverables: this file and `C-combat-results.csv`.

## Entry state and inputs

- Repository `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, branch `2A2B`,
  HEAD `820d1499a0c9ff04fd42975d3de9d97bd62d585d`. The working tree was already
  dirty at entry (46 tracked modifications belonging to concurrent work);
  nothing was reverted, staged or committed.
- Assignment `docs/knowledge/2a2b/tasks/T13-reconciliation-dispatch/C-combat.csv`:
  SHA-256 `e79e9d8fa4eef98891ff1099faa81c778ced5d2bc0a5d60dd8c6271e9d48588f`,
  **243 data rows**, matching `manifest.json` (`C-combat` entry) exactly.
- Every assigned row is `scope: YES`, `category: combat` in
  `T13-audit-scope-review.csv`, and every one is still `UNCLASSIFIED` in the
  current KB (`scope_basis = reviewed_source`).
- Source drift: **0 / 243**. The maintained extraction
  (`audit_export.build_audit_rows`) still reproduces each assigned
  `effect_sha256` from the current raw effect text (never the flattened CSV
  column).

## Results at a glance

| family | metadata_gap | connection_gap | implementation_missing | partial | covered | out_of_scope | decision_required | total |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| selectable skills (`catalog/skills`) | 51 | 3 | 0 | 0 | 0 | 0 | 0 | 54 |
| shared rules (`catalog/rules/special-rules.yaml`) | 0 | 0 | 2 | 11 | 24 | 0 | 0 | 37 |
| hired swords | 0 | 30 | 23 | 5 | 2 | 1 | 0 | 61 |
| dramatis personae | 0 | 32 | 22 | 3 | 0 | 3 | 2 | 62 |
| conditions | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 8 |
| band equipment notes | 0 | 1 | 3 | 0 | 5 | 0 | 0 | 9 |
| campaign mutations | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 7 |
| campaign artefacts | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 4 |
| campaign magic note | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| **total** | **51** | **74** | **54** | **20** | **38** | **4** | **2** | **243** |

## Grouped actionable gaps

### 1. Classification-only gap — 51 selectable skills

Every `rule/catalog/{general,warband}/skill.*` entry except three already has an
executable operator: a row in `catalog/mechanics/close-combat.yaml` (skills
family, with `engine_option`) plus a `handler: effect-set` contract in
`catalog/mechanics/execution.yaml`. The parameters are real engine inputs —
either `EFFECT_FIELDS` (`strength_bonus`, `injury_modifier`, `reroll_wounds`,
`ward_save`, `charge_ws_bonus`, `step_aside`, `thick_skull`,
`out_of_action_threshold`, `charge_strength_bonus`, `incoming_strength_modifier`,
`parry`, `cannot_be_parried`, `reroll_hits`, `attacks_bonus`, …) or tags present
in `modular/contexts.py`, `modular/attacks.py`, `modular/state.py`,
`modular/phases.py`, `modular/rounds.py`, the vectorized operators and
`native/_combat_compile.py`. `mordheim_construction/compiler.py#compile_fighter`
compiles a player-selected skill through `mechanic_index`/`effect_index`, and
many band special skills bind the same id (`skill.expert-swordsman`,
`skill.hard-to-kill` 15 origins, `skill.ignore-pain` 22 …).

`existing_target = mechanic/skill.<id>`. **missing_part** is only the runtime
block (`scope`/`implemented`/`grant`/`effects`) on the `catalog/skills/*.yaml`
record; a few (`skill.strike-to-injure`, `skill.sure-strike`, `skill.regeneration`,
`skill.mighty-blow`, `skill.resilient`, `skill.step-aside`) are consumed purely
through effect fields, so `report tests` evidence for them is by field, not by
mechanic name.

### 2. Connection gap — 74 entries

The operator exists and is consumed, but nothing routes this record to it.

- **Conditions (8).** `catalog/rules/conditions.yaml` declares
  `condition.fear`, `condition.hatred`, `condition.immune-to-psychology`,
  `condition.cold-blooded` and the four `campaign.condition.*` serious-injury
  results, all without a runtime block. Their operators exist
  (`mechanic.causes-fear`, `mechanic.psychology-immunity`, `mechanic.stupidity`,
  `mechanic.fear-immunity`, `mechanic.fear-reroll`, `mechanic.cold-blooded-*`,
  `contexts._hit_reroll` for Hatred, `psychology.resolve_fear`) and the engine
  accepts condition-style tags (`condition.righteous-charge`,
  `condition.command.*`). The condition ids themselves are never mapped.
- **Hirelings (61).** Rules whose printed clause is an exact shared operator —
  `immune-to-poison → trait.poison-immune`, `immune-to-psychology/unfeeling/
  psychology → mechanic.psychology-immunity`, `causes-fear/fear →
  mechanic.causes-fear`, `no-pain → skill.ignore-pain`, `hard-to-kill →
  skill.hard-to-kill`, `hard-head → trait.concussion-immune`,
  `hate-orcs-and-goblins → mechanic.hatred-orcs-goblins`, `kindred-hatred`,
  `hate-dark-elves`, `man-hater`, `hardened → mechanic.fear-immunity`,
  `in-sigmar-s-name → mechanic.fear-reroll`, `luck`, `berserker`,
  `ferocious-charge`, `monster-slayer`, `strongman`, `cold-blooded`, `undead` —
  but the hireling rule record carries no runtime block at all. Equivalence is a
  *candidate* and must be declared explicitly (the KB forbids inferring it from
  names). The second, structural blocker is that
  `mordheim_construction/combat_packages.py` admits **only grade-2b hireling
  profiles** as native Combat Lab participants; core/1a/1b/1c/2a profiles have
  no construction route (existing finding **T13-F036**).
- **Band equipment notes (1).** `mark_of_the_old_ones` is
  `combat_status: out_of_scope`, but `mechanic.mark-of-the-old-ones` exists in
  the mechanics catalogue — only the item→mechanic mapping is missing.
- **Skills (3).** `skill.fey-quickness` (candidate `skill.elven-agility`),
  `skill.chosen-of-the-white-tower` and `skill.instinctive-warrior` (candidate
  `skill.defensive-stance` + the `resolution.yaml` parry reroll) have no
  dedicated mechanic; they need an explicit equivalence decision, not new code.

### 3. Implementation missing — 54 entries

No executable operator covers the admitted clause.

- **Unique hireling kits (45)** — e.g. Ienh-Khain's critical/parry/Strength,
  Aenur's invincible swordsman, Nicodemus's staff, Icefang, Darting Steel,
  Iron Fan, bare-handed martial arts, whip-master, torturer's grapple, Heart
  Strike, trample, lycanthrope, thin flesh, patron, main-gauche, rapier,
  slay-large-creature, venomous, head-hewer, weapons-master, poisoner,
  Poison Ring, trip, babbling banter, confound and confuse, coward king,
  massively built, daemonic flesh, fighting undead, no-time-for-you, snake-fear,
  djinn's luck, mark of the serpent, inured to pain, burn-the-witch.
  `skilleton`-style fragments that do exist (`mechanic.killing-blow`,
  `skill.defensive-stance`) are named as candidates where plausible.
- **Campaign artefacts (3).** All-Seeing Eye of Numas (unmodifiable 6+ save,
  no item record), Att'la's Plate Mail (`runic_attlas_plate_mail` is
  `out_of_scope`; the Rune of Fortitude extra Wound is a duel clause),
  Executioner's Hood (permanent Frenzy + Strength, no item). Acquisition is
  excluded; the supplied effect is not implemented.
- **Equipment notes (3).** `house_guard_plate_armour` 4+ save (item
  `out_of_scope`), `magic_acorn` first-round automatic hit (item
  `out_of_scope`), `thinglash` cannot-be-parried/whipcrack (item
  `out_of_scope`).
- **Trident (magic note + grade-2b kit).** `trident` is
  `catalog/items/miscellaneous.yaml#trident`, `out_of_scope`, no mechanic.
- **Shared rules (2).** `shared-rule.burn-the-witch` (Hatred against
  spellcasters) and `shared-rule.ere-we-go` (ignore Fear tests when charging):
  every restating band origin is `LATER`/`NO` with no binding.

### 4. Partial and contradictory — 20 entries

Real semantic findings, not just missing bindings:

- `shared-rule.hard-as-steel`: two bound origins disagree — `clan-angrund-kep`
  binds `skill.hard-to-kill` and `dwarf-rangers`/`dwarf-treasure-hunters` bind
  `skill.tough-as-steel`, while the shared prose prints **1-3 knocked down**
  (the mechanics give knocked down on 1-2). Neither reproduces the printed band.
- `shared-rule.thick-skull`: the `clan-angrund-kep` origin binds
  `trait.concussion-immune` (mace/club concussion immunity, the *hard-head*
  mechanic) instead of a stun-save operator.
- `shared-rule.fear` (11/26), `immune-to-psychology` (7/16),
  `immune-to-psychology-4` (3/5), `undead` (3/4), `stupidity` (2/6),
  `stupidity-2` (1/8), `cause-fear-2` (3/10), `hard-to-kill` (2/9),
  `hate-orcs-and-goblins` (1/4): at least one origin executes the shared rule,
  but a measurable share of restating origins is still `LATER`/`NO` unbound.
- Hireling partials: `deathwish` and `unhinged` (All Alone half excluded),
  `religious-fervour` (movement compulsion), `daemonic-mind` (no-Experience),
  `gaoler/wolf-priest/grave-robber hatred` (source-listed target species),
  `eye-pendant` (4+ Ward save + Undead Leadership restriction).
- `campaign.magical-artefact.count-of-ventimiglias-misericordia`: the base item
  `misericordia` is implemented, but the artefact's printed Injury substitution
  (1-3 stunned / 4-6 out of action) is a different mechanic and is missing.

### 5. Verified covered — 38 entries

- **24 shared rules** whose runtime legitimately lives on the band origin
  (`catalog/rules/special-rules.yaml` is a promotion mirror: "Band rules
  restate them as `rule_ref`; runtime stays on the band rule"). Each has ≥1
  origin with `scope: YES`/`implemented: YES` and a real binding
  (`skill.regeneration`, `mechanic.causes-fear`, `trait.poison-immune`,
  `skill.ignore-pain`, `mechanic.leader-six`, `weapon.vomit-attack`,
  `trait.injury-profile`, `compiler.censer-bearer-loadout`,
  `profile.equipment-restrictions`, `compiler.promoted-hero-skill-access`, …).
  No classification is needed on the shared record itself.
- **7 campaign mutations** (`blackblood`→`trait.acid-blood` consumed by
  `modular/aftermath.py`; `spines`→`trait.spines`; `scorpion-tail`→
  `trait.scorpion-tail` consumed by `modular/contexts.py`; `hideous`→
  `mechanic.causes-fear`; `great-claw`/`extra-arm`→dedicated
  `compiler.py` branches at lines 617/628; `tentacle`→
  `incoming_attacks_modifier`), all bound by
  `bands/mordheim/cult-of-the-possessed/special-rules.yaml` and exercised by
  `tests/specs/semantic/grants/editorial-mutation-sequences.yaml`.
- **5 band equipment notes** whose item is `combat_status: implemented` with a
  working `mechanic_id`/mapping: `poison_daggers` (×2), `pike`, `shock_rod`,
  `dark_steel_weapon`.
- **2 grade-2b hireling kit notes**: `beastlash` (`weapon.beastlash`) and
  `ceremonial_scythe` (`weapon.ceremonial-scythe`).

### 6. Excluded and decision-required

- **4 out of scope:** Veskit's integrated Warplock Pistols (shooting), the
  Foole's Master Craftsman and the Weaponsmith's maintenance (post-battle),
  Belandysh's Inconsistency (random-characteristic reroll / campaign).
- **2 decisions required:** the two `unresolved_references` entries (Countess
  Marianna's garlic-coating `equipment_modifier`, and the Grade-2a
  `item_instance_modifier` "Master Craftsman weapon modifications"). Both need a
  modelling decision (equipment-modifier / item-instance-modifier model) before
  they can be admitted or excluded.

## Notable blockers

1. **Hireling admission route** (T13-F036): only grade-2b profiles become native
   Combat Lab participants; the other grades have no construction route, which
   caps what any hireling-rule binding can achieve today.
2. **Explicit equivalence review**: 61 hireling rules and 3 skills are
   `connection_gap` because reusing an existing operator requires a declared
   `binding` (the KB forbids name/prose inference).
3. **Staging-only item**: the grade-2b Wolf Priest's `wolf_pelt_cloak` exists
   only in `sources/2B/catalog/items/miracle-workers-gear.yaml`; promotion into
   `sources/knowledge` is missing.
4. **Two shared-rule contradictions** (`hard-as-steel`, `thick-skull`) that a
   blanket "≥1 bound origin ⇒ covered" rule would have hidden.

## Recommended next implementation groups

1. **G-C1 — Declare the 51 skill classifications.** Pure KB metadata; no
   behaviour change; unblocks `report rules` and the residual queue.
2. **G-C2 — Bind the shared-operator hireling rules** (61) plus the 8 condition
   ids and `mark_of_the_old_ones`, pairing each with an explicit equivalence
   review; coordinate with T13-F036 for the profile admission route.
3. **G-C3 — Implement the unique hireling kits** (45) in semantic families
   (injury/recovery: `inured-to-pain`, `thin-flesh`, `head-hewer`; attack
   modifiers: `trample`, `torturer's grapple`, `iron-fan`; weapon rules:
   `main-gauche`, `rapier`; psychology/hatred targets: `burn-the-witch`,
   `patron`).
4. **G-C4 — Campaign/artefact supplied effects**: Executioner's Hood and
   All-Seeing Eye of Numas items, the Att'la extra Wound, the Misericordia
   artefact Injury substitution, and the trident Strike First/Parry item.
5. **G-C5 — Repair the shared-rule contradictions** (`hard-as-steel`,
   `thick-skull`) and the lagging origins for `fear`, `immune-to-psychology`,
   `undead`, `stupidity`, `hard-to-kill`.

## Checks actually run

- Manifest/assignment SHA-256, byte-level LF check, row count, duplicate-id and
  column-order validation of the output.
- Maintained extraction (`build_audit_rows`, inventory mode) recomputed for all
  243 ids: 243/243 hash match (entry and closure).
- KB-wide scan of `sources/knowledge/**/*.yaml` (rule ids, `rule_ref` users,
  binding users, `runtime` blocks, item `combat_status`/`mechanic_id`).
- Code inspection: `verification/audit_export.py`, `verification/consumers.py`,
  `mordheim_construction/{compiler,contracts,combat_packages}.py`,
  `mordheim_combat/kernel.py`, `modular/{contexts,attacks,state,rounds,phases,
  aftermath}.py`, vectorized/native compile, `tests/specs/**`.
- **Not run:** full `verify`, `parity`, statistical/deep certification or the
  coverage gate; no engine test suite was executed. No behavioural execution is
  claimed, and no result is labelled "passed" on unexecuted evidence.
- Scratch evidence (read-only scripts and intermediate JSON/TSV) lives in
  `build/audit/reconciliation/C/`.

## Concurrent drift and closure

- Entry and closure assignment hash are identical; closure re-scan found
  **0 source drift and 0 missing ids** against the current KB.
- Relevant code/KB hashes at closure (16 hex chars):
  `audit_export.py a7a58dd9ad2f21e1`, `consumers.py 02ef61320605d8c0`,
  `compiler.py 27c2dc96baff1278`, `combat_packages.py 481526be0d78f808`,
  `contracts.py 1d5aad3675fccb8b`, `kernel.py cb80ac269d8fa3ca`,
  `mechanics/close-combat.yaml 1c77f3197a93e5d6`,
  `mechanics/execution.yaml 2aa3f58a3b1c580e`,
  `rules/special-rules.yaml 5d0fdd1aa5c9ac57`,
  `rules/conditions.yaml 0ab0c85e41f9ff2e`,
  `hirelings/traits.yaml 825d5ecc85e61aae`.
- The 46 tracked working-tree modifications present at entry were left
  untouched. No KB, code, register, review or assignment file was modified; no
  commit, push or agent was created. Only `C-combat-results.csv` and this
  summary were written for lot C.
