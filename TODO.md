# Project backlog

Open defects, verification gaps and deferred capabilities. Each entry states
what is pending and when it is done.

## Rules-conformance coverage

- **Authoring backlog.** 603 of 2,272 admitted identities have no scenarios.
  Check with `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`;
  done when the gate passes.
- **Rousing Sermon (Trollheim) cost not modelled.** The printed "He may not use
  Prayers that turn" is not enforced, and `catalog/skills/warband.yaml`
  (`skill.inspiring-sermon`) describes a passive "+1 Attack for the turn" without
  the declaration. The two fixture scenarios in the Trollheim file exercise
  `mechanic.rousing-sermon` (the once-per-game Mordheim operator), not this
  rule's binding. Done when the cost is modelled or ruled out of duel scope and
  the fixtures are rebound.
- **Hypnotic Gaze for Lahmia.** Eligibility reads the KB `eligibility` list
  (`von-carstein-vampire`, `lahmia-vampire`), but the cited print (*Chaos in the
  Streets* p.181) is a Von Carstein section. Done when the list matches the print.
- **Master of Arms reaches only the Morning Star.** Items carry no
  Difficult-to-Use flag, so the exception in `eligibility/index.ts` names the
  Morning Star. Done when Difficult to Use is a declared item property, or a
  ruling confirms the Morning Star is the only such one-handed weapon on the list.
- **Dead Strongman branch.** `phases.py` still names `weapon.broadsword` in the
  Strongman exemption, though the broadsword has no penalty to remove. Done when
  the branch reads the two-handed case only.
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
- **Printed-source checks before de-duplicating.** Sons of Nagarythe Powerful
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
  `material.normal`, `weapon.natural-attacks`, `mechanic.norse-shieldmaster`);
  `skill.regeneration-blocked-by-blessed` waits for an `attack.blessed` source.
  Done when the probe can substitute an item, or these are accepted as covered
  by item-level coverage.
- **Haughty also bars obsidian.** The Dwarf-equipment guard in
  `_eligibility.js` treats `material.obsidian` as Dwarf-made; the printed text
  names only Dwarf origin and Gromril. Done when the guard matches the print or a
  ruling records why.
- **Scenarios that contradict or miss their print.** Pirates Sea Shanty
  `a-psychology-immune-enemy-is-not-tested-and-keeps-both-attacks` contradicts the
  print (only Undead and non-living are exempt); Curse of the Reborn
  `the-four-plus-regeneration-save-ignores-the-wound` claims
  `blocked-by-fire-and-blessed` without evidencing it; the Ogre Hunting skills
  file hosts five hand-built bull-charge/crude-belch scenarios that do not
  exercise it. Done when each scenario matches its print and identity.
- **Engine or eligibility behaviour without printed support.** Any two Dwarf axes
  get a parry re-roll regardless of skill (`contexts.py::_parry_context`); Wheelo
  fittings are gated on `mechanic.wheelo-impact`, not on the rule; the
  chaos-streets Troll Slayer refuses every special skill through `skill_ids`
  while a Dwarf Noble is admitted to Monster Slayer; Battle Monks warrior-monks
  henchmen are admitted to Energy Focus. Done when each is fixed or ruled.

## Runtime classification

- **Bindings that execute nothing.** `trait.pit-fighter` (six Mordheim Pit
  Fighters profiles; construction tests pin the trait tag),
  `compiler.warrior-wizard` (the Liche) and `condition.large-target` (three
  hired-sword rules) read as implemented, but no engine or compiler code
  consumes them. Decide per binding: implement it, or unbind it.
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

- **Parity deliveries behind the corpus.** Against 5,390 corpus scenarios and
  5,161 deliveries, 436 delivery keys name scenarios that no longer exist, 665
  scenarios have no delivery and 1,321 deliveries are stale (`source.sha256`);
  `tests/engines/fixtures/compiled-cases.json` likewise holds `conformance/...`
  entries under retired scenario ids. Done when the deliveries are re-prepared
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
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
