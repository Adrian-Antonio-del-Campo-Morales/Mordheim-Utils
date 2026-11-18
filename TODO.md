# Project backlog

Open defects, verification gaps and deferred capabilities. Each entry states
what is pending and when it is done.

## Rules-conformance coverage

- **Authoring backlog.** 517 of 2,271 admitted identities have no scenarios. The division
  into batches, the order and the per-batch procedure are in *Rules-conformance authoring
  plan* below. Check with `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`;
  done when the gate passes.
- **Rousing Sermon (Trollheim) cost not modelled.** The printed "He may not use
  Prayers that turn" is not enforced (no engine models Prayers), and
  `catalog/skills/warband.yaml` (`skill.inspiring-sermon`) still describes a passive
  "+1 Attack for the turn" without the declaration. The Trollheim file holds two
  real-profile scenarios plus two fixtures on `mechanic.rousing-sermon` (the
  once-per-game Mordheim operator), and its "ENGINE-DEFECT (2026-11-16)" comments are
  stale. Done when the cost is ruled out of duel scope or modelled, the skill text
  matches, and the fixtures are retired or rebound.
- **Hypnotic Gaze for Lahmia.** Eligibility reads the KB `eligibility` list
  (`von-carstein-vampire`, `lahmia-vampire`), but the cited print (*Chaos in the
  Streets* p.181) is a Von Carstein section. Done when the list matches the print.
- **Master of Arms misses the Broadsword.** Items carry no Difficult-to-Use flag, so
  the exception in `eligibility/index.ts` (and `_eligibility.js`) names the Morning
  Star only, while the KB prints the Broadsword as the one-handed "Difficult to use"
  weapon (`weapons-close-combat.yaml`) and the Morning Star's KB text says only
  "Heavy". Done when Difficult to Use is a declared item property read by the
  exception, after checking the Morning Star's print.
- **Dead Strongman branch.** `phases.py`, `vectorized/_operators.py` and
  `native/_combat_compile.py` still name `weapon.broadsword` in the Strongman
  exemption, though the broadsword has no penalty to remove. Done when the three
  branches read the two-handed case only.
- **Spiral and Triskele unmodifiable faces vs Djinn's Curse.** The Dark Emissary's Spiral
  (5+) and the Truthsayer's Triskele (4+) print saves "that cannot be reduced by anything"
  and are carried as ordinary wards (`defence.spiral`, `defence.triskele`); the only general
  reducer, Djinn's Curse, still worsens them because the modular respect-check
  (`contexts.py`, `intrinsic_djinn`) is Djinn-specific and `EffectSet` has no
  unmodifiable-ward field. Done when the 2026-10-15 Djinn ruling's "expressly unmodifiable"
  respect extends to these printed faces (and its optimized ports), or the composition is
  ruled unreachable.
- **Wall of Steel's stance is not a KB record.** The printed two-handed choice is carried by
  the hard-coded build variant `stance.wall-of-steel` (compiler and TS gate); the bound
  `mechanic.wall-of-steel` tag is read by the gate only, so the mechanic's entry probes
  inert (a dated Discrimination note records it). Done when the stance is a declared KB
  variant and the compiler reads the mechanic, or the current carrier is ruled canonical.
- **"Counts as a large target" is bound inconsistently.** The Clan Skryre Rat Ogre, Ogre
  Bodyguard and Ogre Slave Master bind `condition.large-target` (read by Slay Large
  Creature, the grapple immunity and the Rememberer), while the same printed sentence on
  the Bone Goliath, the Ogre Treasure Hunter and every band `shared-rule.large-target` is
  excluded as `out-of-scope.shooting`. Done when the prints are compared and one binding
  convention holds everywhere.
- **A hired leader lends Leadership inside his synthetic package only.** The Knight of the
  White Wolf's printed Pride ("may act as a Leader to their comrades") compiles to
  `mechanic.leader-six`, but the modular borrow gate requires a shared `band.*` tag, so he
  can lend only to another hireling of `hirelings.hired-sword.2a`, never to the hiring
  warband's members; the authored scenarios use a same-package comrade. Done when
  cross-package hiring facts let a hired leader reach his employer's warriors (web-app
  phase, with the hiring-facts entry below).
- **Band members' hiring facts are not published.** `hire-eligibility.ts` reads hirelings
  through the derived `hireling_traits`, but band members still go through the hard-coded
  `FEAR_PROFILE_KEYWORDS` / `SPELLCASTER_PROFILE_KEYWORDS` substring lists, and the Witch
  Hunter's printed exception (priests of Sigmar, Ulric, Taal and Morr only) is coded as any
  `priest`. Several hireling species and alignment facts rest on knowledge of the printed
  sources rather than the KB text: check them when the prints are mirrored. Done when the
  generator publishes band members' facts and the keyword lists are gone (web-app phase).
- **Witch Hunter Burn the Witch binds the general `skill.hatred`.** The print hates enemy
  spellcasters; the band Witch Hunters bind `mechanic.burn-the-witch`, which reads
  `identity.spellcaster` (`trait_overrides: {spellcaster: true}` declares it), while
  the hired Witch Hunter binds the generic hatred of everyone. Done when the hireling
  rule binds `mechanic.burn-the-witch` and its file covers the non-spellcaster boundary.
- **Scenarios on out-of-scope identities.** 10 identities outside the admitted
  scope still carry scenarios because no admitted identity holds their
  behaviour: Living (Mordheim and Trollheim Tomb Scorpions; a profile
  `creature_kind: living` trait), Animated (Stone Golem), Teamwork (Snotling Mobs,
  Shoota Teams; LATER), and restrictions encoded only by an equipment-list line
  or a profile's skill access (Orc Boyz crossbow, Thieves Guild Enforcer and
  Ruffian, Strigany and Nipponese skill tables). Done when each behaviour has an
  admitted identity to hold the scenarios, or the scenarios are retired.
- **Conditions and bull-charge unreachable by scenarios.** 8 rule identities
  probe `inert`: the six Fungus Brew conditions and Danse Macabre (band rules
  that bind a supplied `condition.*` with `grant: none`) and the Ogre
  bull-charge. Done when each is routed, re-authored against its own binding or
  excluded with its own reason.
- **Protectorate of Sigmar (LotD3) special-skill access.** Unshakeable Faith (and the other
  band-wide special skills) has no eligibility list and no hero prints the `special` skill
  access, so the selection is refused for every profile and the identity stays `PARTIAL`.
  Done when the print says which heroes may use the band's Special Skills and the KB carries
  it (a `special` access or an eligibility list).
- **Printed-source checks before de-duplicating.** Skaven of Clan Mors and Clan Skryre
  (Karak Azgal) `band--rulebook-inheritance` grants a skill list whose members are already
  Hero-only warband skills of their own: the access is encoded twice and the two files carry a
  Discrimination note; keep one source. Sons of Nagarythe Powerful
  Build: the Shadow Master and Shadow Walker already list `strength` in
  `skill_access`, so the skill adds nothing for them; check the printed skill
  tables. `mad-scientist--lunatic` is printed as a Special Skill but granted
  automatically to four Masters of Horror profiles, which makes the Thrall's own
  Cause Fear redundant: `thrall--cause-fear` and the five
  `mad-scientist--alchemist` conditions probe `non-discriminating`; check the
  print. Done when each encoding matches its print and the probe reports the
  identity `discriminating`.
- **Construction-only evidence.** The probe reports 70 identities
  `construction-only`. For 12 the rule *is* a construction rule (skill access,
  equipment restrictions, single-model projection), where a refusal is the
  expected verdict. The other 58 are combat identities (handler leadership,
  brood mentality, mutations, tail attacks, ...) refused at construction when
  their rule is removed, so no scenario shows their duel effect with and without
  the rule. Done when each has a scenario whose duel observable changes, or the
  build genuinely cannot exist without the rule (record why).
- **Equipment mechanics the probe cannot reach.** 12 mechanics probe `inert`
  because their execution entry carries only a tag and the effect comes from the
  item catalogue or is synthesised by the engine (nine body armours,
  `material.normal`, `weapon.natural-attacks`, `mechanic.norse-shieldmaster`).
  Done when the probe can substitute an item, or these are accepted as covered
  by item-level coverage.
- **`skill.regeneration-blocked-by-blessed` is authorable.** Its file still says no
  build supplies `attack.blessed`, but `condition.blessed-weapon` (with
  `trait_overrides: {blessed_weapon_slots: [main]}`) does, and a Curse of the Reborn
  scenario already uses it. Done when the mechanic's own blocked branch is authored
  and the header corrected.
- **Coverage baseline digest is stale.** `integrity/evidence/coverage-baseline.yaml`
  was accepted on 2026-10-08 against an inventory digest that no longer matches (the
  control re-checks each clause and passes, but reports the move) and protects 15
  identities only. Done when a reviewed edit refreshes the digest and extends the
  reference to the reviewed identities.
- **Ogre Hunting scenarios that miss their identity.** `crude-belch-ogre` probes
  non-discriminating without a dated `# Discrimination note`: its file exercises
  `skill.crude-belch-halfling` and hosts two Monster Slayer refusals moved from the retired
  skill-access file; the three `bull-charge` scenarios inject `mechanic.bull-charge` through
  `skill_ids` and probe `inert`. Done when each identity has scenarios on its own binding (or
  its note) and the refusals live with the identity they evidence.
- **Haughty also bars obsidian for the Mordheim High Elves.** One Dwarf-equipment guard
  (`_eligibility.js`, `index.ts`) serves two bands and treats `material.obsidian` as
  Dwarf-made: the Trollheim print names "Gromril and Obsidian", the Mordheim
  (`high-elves-lus`) print only Dwarf origin and Gromril. Done when the guard follows each
  band's print.
- **Scenarios that contradict or miss their print.** The Mordheim Pirates Sea Shanty
  scenario `a-psychology-immune-enemy-is-not-tested-and-keeps-both-attacks` contradicts its
  print (only Undead and non-living are exempt; the Trollheim copy matches its own print);
  in both Curse of the Reborn files `the-four-plus-regeneration-save-ignores-the-wound`
  declares `blocked-by-fire-and-blessed` without evidencing it. Done when each scenario
  matches its print and identity.
- **Engine or eligibility behaviour without printed support.** Any two Dwarf axes
  get a parry re-roll regardless of skill (`contexts.py::_parry_context`); Wheelo
  fittings are gated on `mechanic.wheelo-impact`, not on the rule; the
  chaos-streets Troll Slayer refuses every special skill through `skill_ids`
  while a Dwarf Noble is admitted to Monster Slayer; Battle Monks warrior-monks
  henchmen are admitted to Energy Focus. Done when each is fixed or ruled.

## Rules-conformance authoring plan

The plan of record for the admitted identities without scenarios.
`tools/conformance/backlog_batches.py` derives it from the knowledge base and the corpus and
never writes either; covered identities drop out when it is re-run, so the table below is
refreshed as batches land.

```bash
.venv/bin/python tools/conformance/backlog_batches.py --table          # this table
.venv/bin/python tools/conformance/backlog_batches.py --batch B02      # one batch's identities
.venv/bin/python tools/conformance/backlog_batches.py --out <work-dir> # batches.json + <id>.ids.txt for the probe
```

**Unit.** A printed-rule group: an uncovered mechanic with every uncovered rule bound to it
(one oracle; the mechanic through `skill_ids`, its rules through the real build), or the rules
that share a binding. A component of more than 30 members with an authored model
(`profile.equipment-restrictions`) is split by collection. **Effort:** 4 to derive a new
contract, 1 to add a member to an authored or batch-local model, 1.5 for a construction
member (admission/refusal pair), 2 for a triage item. Batches hold about 50 units.
**Triage first:** the `PARTIAL` files with a recorded blocker, the operators no engine or
construction code reads (a condition whose duel content sits in sibling effects counts as
read), and the identities on hireling profiles that do not compile (detected live). The
mechanics of one printed source section (Disability 1–6, Fungus Brew, Petru...) form one
family and are never split. Triage is a decision pass (author, rule or withhold with the
blocker named), not bulk authoring. **Model** counts the
identities whose binding already has authored scenarios elsewhere.

| Batch | Theme | Ids | Model | Effort | Routes |
| --- | --- | ---: | ---: | ---: | --- |
| B00 | triage-blockers | 1 | 1 | 2 | special_rule_ids 1 |
| B01 | psy-tests-and-enemy-effects | 24 | 14 | 36 | skill_ids 14, real profile build 10 |
| B02 | hatred-frenzy-and-charge-rages-1 | 25 | 3 | 49 | skill_ids 14, real profile build 7, special_rule_ids 4 |
| B03 | hatred-frenzy-and-charge-rages-2 | 27 | 7 | 48 | skill_ids 12, real profile build 12, special_rule_ids 2, condition_ids 1 |
| B04 | leadership | 51 | 33 | 66 | real profile build 27, skill_ids 16, special_rule_ids 6, condition_ids 2 |
| B05 | survival-injury-and-immunity-1 | 34 | 18 | 55 | real profile build 22, skill_ids 9, special_rule_ids 3 |
| B06 | survival-injury-and-immunity-2 | 34 | 17 | 55 | real profile build 20, skill_ids 7, special_rule_ids 5, equipment slot 2 |
| B07 | survival-saves-and-rerolls | 32 | 11 | 62 | real profile build 21, skill_ids 6, equipment slot 3, special_rule_ids 1, condition_ids 1 |
| B08 | supplied-conditions-1 | 23 | 3 | 41 | condition_ids 21, skill_ids 1, real profile build 1 |
| B09 | supplied-conditions-2 | 27 | 19 | 39 | condition_ids 27 |
| B10 | equipment-items-1 | 23 | 4 | 56 | equipment slot 21, skill_ids 1, real profile build 1 |
| B11 | equipment-items-2 | 21 | 3 | 54 | equipment slot 21 |
| B12 | construction-equipment-1 | 35 | 34 | 52.5 | construction 35 |
| B13 | construction-equipment-2 | 35 | 33 | 52.5 | construction 35 |
| B14 | construction-skills-and-profile | 43 | 28 | 64.5 | construction 43 |
| B15 | operators-hirelings | 39 | 27 | 57 | real profile build 24, special_rule_ids 10, skill_ids 5 |
| B16 | operators-band-rules | 43 | 25 | 64 | skill_ids 29, real profile build 7, special_rule_ids 5, condition_ids 1, equipment slot 1 |
| | **Total** | **517** | 280 | 853.5 | |

**Order.** Triage first (B00; the second triage batch landed 2026-11-18, leaving only the
Unshakeable Faith identity withheld on its print). Then the model-heavy themes, which confirm the workflow on
cheap members: leadership, construction-equipment, construction-skills-and-profile,
survival-injury-and-immunity. Then psy-tests-and-enemy-effects, hatred-frenzy-and-charge-rages
and survival-saves-and-rerolls. The new-contract themes last: supplied-conditions,
equipment-items, operators-hirelings, operators-band-rules. Batches own disjoint files by
construction and may run in parallel; the coordinator owns the shared documents (this file,
the design rulings, the conformance README).

**Per batch.** Follow *Author by semantic family* in `tests/conformance/README.md`
(hireling recipients: *Hireling recipients* there). Verify with
`validate_corpus.py` (0 metadata conflicts), `pytest tests/conformance/execution/test_cases.py -k <selector> -n 4`
and `removal_probe.py --identities-file <id>.ids.txt --workers 3 --show non-discriminating`.
A surviving scenario whose duplicate is a KB encoding gets a dated `# Discrimination note`;
an identity that cannot be built stays `PARTIAL` with the blocker named. Record new rulings
in `docs/decisions/design-rulings.md` and new defects here.

## Runtime classification

- **Bindings that execute nothing.** `compiler.warrior-wizard` (the Liche) reads as
  implemented, but no engine or compiler code consumes it. Decide: implement it, or unbind
  it.
- **Pit Fighter skill needs a terrain operator.** `band--pit-fighter-skill` ("+1 WS and +1 A
  when fighting in ruins, buildings or The Pit") is `LATER` (pending implementation); the
  duel context already carries `terrain` labels. Done when an operator reads them or the
  skill is ruled out of the duel.
- **Saurus bite.** `compiler.bite-attack` never strikes last (only
  `rule.strikes-last-bite` does, `modular/rounds.py`), although the printed bite
  "always strikes last".
- **Bagh Nakh through Trading.** The Thieves' Guild list entry names the
  Hashashiyyin as the creation-price bearer; the printed "other members must
  acquire it through Trading" path is not modelled because
  `catalog/campaign/trading-post.yaml` is Mordheim's post, where Bagh Nakh is not
  sold. Add the Khemri trading entry (rarity, recipients).
- **Thrown weapons and `non-thrown-ranged`.** `no-missiles-or-armour` lets thrown
  weapons pass a text that bans "any missile weapons"; record a ruling or
  change the token.
- **Close-combat items marked `out_of_scope`.** Spike-Jawed Snatcher, Gas Mask,
  Cathayan Plate Armour, Corpse Liquor and Pneumatic Arm: review their duel
  status in the item catalogue.
- **Untracked supplied conditions.** 38 conditions of
  `catalog/rules/conditions.yaml` have no mirror in
  `catalog/mechanics/close-combat.yaml`, so no rule can bind them and the
  inventory does not track them (runes, Witch and Weaponsmith services, Master
  Craftsman, serious-injury states). Mirror the duel-relevant ones when their
  rules are bound.
- **Snotling Mob "Dodgy".** Crooked Moon prints "+D6 dodge save" where every
  other copy prints "6+": verify the source.
- **Sharing proposals left out.** Set Traps, Netter, Addict, Frantic,
  Swashbuckler, two Wizard / Spellcaster pairs, the "Immune to Psychology" texts
  that lack "never leaves combat", and a Large Target text that spells out +1 To
  Hit. Decide each with the equivalence rule of `docs/reference/knowledge-base.md`.

## Item catalogue

- **Derived descriptions awaiting printed entries.** These items carry a
  `# Derived description` comment; their entries are printed only in Spanish books
  not mirrored here: *Khemri* (`dispelling_scroll`, `icon_of_manann`, `whip`),
  *Lustria* (`feather_headdress`, `sacrifice_dagger`, `magic_tattoos`,
  `shrunken_head` for the Savage Goblins; `jungle_roast`, `magic_tattoo`,
  `spider_amulet`, `poisoned_darts` for the Pygmies) and *Chaos in the Streets*
  (`travel_staff`, `poison_darts`). The *Lustrian Artefacts* *Spider Amulet* is a
  different object from the Pygmy list item.
- **Item coverage.** List implemented items with missing or partial
  deterministic coverage with
  `python tools/knowledge/clauses.py coverage --kind item --pending`.

## Engine coverage lost with the retired replay suites

282 engine statements are covered by no current suite since the replay suites
were retired (127 in
`vectorized/_operators.py`, 78 in `vectorized/_attacks.py`, 28 in
`vectorized/_driver.py`, 24 in `phases.py`, 25 across `modular/`). Done when they
are covered again or explicitly accepted as out of scope.

## Order-dependent engine test

`tests/engines/modular/mechanics/test_source_corrections.py::test_m25_break_preserves_prepared_hits_and_projects_surviving_equipment[weapon.dagger]`
passes alone and in its own file, but fails under
`pytest tests/engines tests/construction -n 4 -k "<selection>"` with
`unused rolls: p.attack.1.armour`, also on a clean checkout of `4f271cb7b`.
Done when the shared state it depends on is found and isolated.

## Intermittent removal-probe baseline failure

On 2026-11-17, two probe runs of the first hireling batch (`--workers 3`) reported both Grave Robber hatred
scenarios `baseline-fails` (identity `inert`) although they pass under pytest; nine later
runs (three CLI, six instrumented) were clean, and the cause was not found. While looking,
`mordheim_construction.eligibility` was found to install the catalogue into its JavaScript
engine once per process (`_installed`), while the probe only clears the Python
`_catalogue` cache: a removal never reaches the JavaScript eligibility checks. Done when the
probe resets the installed catalogue per execution and the flake is explained or gone.

## Web construction-blockers test F074

`tests/applications/warband_manager/domain/campaign/construction-blockers.test.ts`
("Printed entry recipients (F074) > applies a printed recipient clause across the
collections") expects `equipment_not_permitted` for Trollheim entries (Lustria Pirates
parrot, Lustria High Elves mage staff, Deathbringers witch sword) and gets
`equipment_forbidden`; it fails the same way on an artefact generated from the
committed KB (2026-11-17), so it predates the hireling work. Done when the verdict code
matches the printed recipient clause.

## Combat Lab checklist popover

Unverified `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`; needs Tkinter). Done when both pass
with their theme, width and scrollbar assertions intact.

## Parity deliveries derived from the conformance corpus

Deliveries in `tests/engines/parity/deliveries/` are derived artefacts of the
rules-conformance corpus, not part of the rules-conformance suite; they are
tracked here so corpus work is not blocked on them. A delivery is never proof of
its source scenario's expectations. Charter:
[`tests/engines/parity/README.md`](tests/engines/parity/README.md).

- **Parity deliveries behind the corpus.** Measured on 2026-11-17 against 5,390
  corpus scenarios (the corpus has grown since): of 5,161 deliveries, 436 keys name
  scenarios that no longer exist, 665 scenarios had no delivery and 1,321 deliveries
  were stale (`source.sha256`). `tests/engines/fixtures/compiled-cases.json` holds
  `conformance/...` entries under retired scenario ids, and its manifest still lists
  the retired `catalog/hirelings/traits.yaml` as an input. Done when the deliveries are re-prepared
  with `export_cases` and the orphans removed. This must precede any delivery
  re-sample.
- **Delivery README figures are stale.** `tests/engines/parity/README.md`
  prints admission counts that no longer hold. Done when they are refreshed
  after the re-preparation above.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle with the
six-sigma gate (`python tools/mordheim-utils.py check samples compare`).
Stored samples live in `tests/engines/parity/reference_samples/`; running the
modular engine requires explicit authorization.

- **Native.** Run `tests/engines/native/` (attack-event gating, pool allocation
  and Rapier Barrage touch the replay paths), then requalify `--scenarios big`
  against `modular-100k` and re-sample `native-deliveries-100k` from a clean
  commit.
- **NumPy.** Re-sample `numpy-deliveries-100k` from a clean commit (the current
  engine passes every delivery against `modular-deliveries-100k` at 20,000
  duels).
- **Stale stores.** In each of the three delivery stores (`modular-`, `numpy-`,
  `native-deliveries-100k`), records name scenario ids that no longer exist and
  admitted deliveries have no record; KAZ goblin and Main Gauche samples predate
  their behaviour changes. Regenerate at the next re-sample, after *Parity
  deliveries behind the corpus* is cleared.
- **Systematic offset.** NumPy deliveries all pass, but first-win z-scores
  average about +0.2 and unresolved ones about +0.9 over 1,815 inputs (one shared
  seed). Determine whether it is an engine difference or the oracle-provenance
  problem.
- **Oracle provenance.** The stored modular samples carry a source digest that
  matches no commit. Confirm which inputs later commits affect, or regenerate
  with authorization, before claiming current-engine certification.
- **Survivor condition.** On `scenario/stateful` the winner of a decided duel is
  not Standing in 1.56 % (Modular) vs 1.98 % (NumPy) of duels. Decide whether the
  terminal condition should become a compared magnitude.
- **Portable native digests.** Add a line-ending rule for `.pyx`/`.pxd` in
  `.gitattributes` so Windows and Linux checkouts produce the same digest.
- **Rejected deliveries.** Deliveries that need `initial_state` overrides or
  auxiliary participants, or that prescribe scripted decisions, stay
  uncertified until the shared runner supports them.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause (engine support stays pending by user decision). |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae; the Headless Horseman's four duel effects wait on it (`LATER`, `deferred.mounts`). |
