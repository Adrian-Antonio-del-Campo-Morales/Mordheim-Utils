# Project backlog

Open defects, verification gaps and deferred capabilities. Each entry states
what is pending and when it is done.

## Rules-conformance coverage

- **Authoring backlog.** 611 of 2,333 admitted identities have no scenarios.
  Check with `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`;
  done when the gate passes.
- **Engine disagrees with the printed rule (9 failing scenarios).**
  `weapon.broadsword` strikes last (`priority: -1` in `execution.yaml`, not
  printed); Long Daggers carry an unprinted `weapon.dagger` tag (Knife Fighting
  applies, the dagger save does not) — 2 scenarios; Master of Arms does not allow
  a Difficult-to-Use weapon with a hand weapon; Machine-Ogre Bio Machinery is
  `implemented: NO`, so its psychology immunity never compiles; Rousing Sermon
  (`skill.inspiring-sermon`) offers no declaration and adds the attack even when
  declined — 2 scenarios; Von Carstein Hypnotic Gaze is refused for want of a
  bloodline prefix; `core/combat-order::strike-first-overrides-the-standing-up-penalty`
  expects a stood-up Always-Strikes-First fighter to strike last. Done when each
  scenario passes (the combat-order one after a ruling confirms the reading; its
  id still reads the old way).
- **Parity deliveries behind the corpus.** 278 delivery keys name scenarios that
  no longer exist, 602 scenarios have no delivery and 1,257 deliveries are stale
  (`source.sha256`). Done when the deliveries are re-prepared with `export_cases`
  and the orphans removed.
- **Scenarios on out-of-scope identities.** 10 identities outside the admitted
  scope still carry scenarios because no admitted identity holds their
  behaviour: Living (Mordheim and Trollheim Tomb Scorpions; a profile
  `creature_kind: living` trait), Animated (Stone Golem), Teamwork (Snotling Mobs,
  Shoota Teams; LATER), and restrictions encoded only by an equipment-list line
  or a profile's skill access (Orc Boyz crossbow, Thieves Guild Enforcer and
  Ruffian, Strigany and Nipponese skill tables). Done when each behaviour has an
  admitted identity to hold the scenarios, or the scenarios are retired.
- **Catalogue skills unreachable by scenarios.** The 56
  `rule/catalog/{general,warband}/skill.*` identities have `grant: none` and no
  construction path reads their binding (`skill_ids` and starting skills resolve
  to the mechanic directly); the same holds for the six Fungus Brew conditions and
  Danse Macabre. The rule-removal probe reports them `inert`. Done when the KB
  routes these grants through their records or excludes them from conformance.
- **Printed-source checks before de-duplicating.** Sons of Nagarythe Powerful
  Build: the Shadow Master and Shadow Walker already list `strength` in
  `skill_access`, so the skill adds nothing for them; check the printed skill
  tables. `mad-scientist--lunatic` is printed as a Special Skill but granted
  automatically to four Masters of Horror profiles, which also makes the Thrall's
  own Cause Fear redundant; check the print. Done when each encoding matches its
  print and the probe reports the identity `discriminating`.
- **Construction-only evidence.** About 35 combat identities (handler leadership,
  brood mentality, mutations, tail attacks, ...) are refused at construction when
  their rule is removed, so no scenario shows their duel effect with and without
  the rule. Done when each has a scenario whose duel observable changes, or the
  build genuinely cannot exist without the rule (record why).
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
- **Header prose out of date.** Some `AUTHORED`/`PARTIAL` marker texts quote old
  scenario counts (automatic-leadership and rat-ogre Stupidity families, Khemri
  Necrotect, `weapon.kusara-kama`); House Guard Adjutant and
  `weapon.yari-two-handed` describe a scenario the file no longer holds; the
  Snotlings Bigsnotz Big Bully header calls Big Bully "implemented NO"; the
  Snotlings Wheelo grant header repeats the "Strength 3 crew" reading; the
  Swordsmen, Troll Slayer Hard to Kill, Strigoi and Necrotect Hatred files still
  describe selecting rules that are now automatic. Done when each header matches
  its file and the KB.

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

## Combat Lab checklist popover

Unverified `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`; needs Tkinter). Done when both pass
with their theme, width and scrollbar assertions intact.

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
- **Stale stores.** In each delivery store, 254 records name scenario ids that no
  longer exist and 249 admitted deliveries have no record; 11 deliveries are
  stale (8 Night Goblins KAZ, 3 Extra Arm). KAZ goblin and Main Gauche samples
  predate their behaviour changes. Regenerate at the next re-sample.
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
- **Rejected deliveries.** 1,484 deliveries need `initial_state` overrides or
  auxiliary participants and 529 prescribe scripted decisions; they stay
  uncertified until the shared runner supports them.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause (engine support stays pending by user decision). |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
