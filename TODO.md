# Project backlog

Open defects, verification gaps and deferred capabilities. Each entry states
what is pending and when it is done.

## Rules-conformance coverage

The suite is complete as of 2026-11-19: every admitted identity has scenarios, no case file is
`PARTIAL`, and `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`
passes. What remains is evidence quality, semantic review, and the KB, eligibility and engine
defects found while authoring. New identities admitted later are batched as described in
*New authoring backlog* (`tests/conformance/README.md`).

### Evidence quality

- **Construction-only evidence.** The removal probe (2026-11-19) reports 119 identities
  `construction-only` (110 rules, 9 mechanics). For construction rules (skill access, equipment
  restrictions) a refusal is the expected verdict; for combat identities it means no scenario shows
  the duel effect with and without the rule, because the build is refused once the rule is removed
  (handler leadership, brood mentality, mutations, tail attacks, Scorpion Tail on a Mutant who then
  has no mutation). Done when each combat identity has a scenario whose duel observable changes, or
  the build genuinely cannot exist without the rule (record why).
- **Non-discriminating evidence.** 74 identities pass with their rule removed; each carries a dated
  `# Discrimination note` naming the duplicate encoding that delivers the effect. Done when each
  effect has a single source (see *Printed-source checks before de-duplicating* below and the
  encoding questions recorded per batch).
- **Inert identities.** 19 mechanics and 8 rules probe `inert`: the removal never reaches the build.
  The mechanics are tag-only execution entries whose effect comes from the item catalogue or the
  engine (the body armours, `material.normal`, `weapon.natural-attacks`,
  `mechanic.norse-shieldmaster`, `skill.dodge-sidestepper`, `mechanic.wall-of-steel` - see its entry
  below - and `skill.regeneration-blocked-by-blessed`, whose flag is supplied as a trait). The rules
  are the six Fungus Brew conditions and Danse Macabre (band rules binding a supplied `condition.*`
  with `grant: none`) and the Ogre Hunting Bull Charge, whose three scenarios inject
  `mechanic.bull-charge` through `skill_ids`. Done when the probe can substitute an item, the rules are
  re-authored against their own binding, or each is accepted with its reason.
- **Coverage baseline digest is stale.** `integrity/evidence/coverage-baseline.yaml`
  was accepted on 2026-10-08 against an inventory digest that no longer matches (the
  control re-checks each clause and passes, but reports the move) and protects 16
  identities only. Done when a reviewed edit refreshes the digest and extends the
  reference to the reviewed identities.

### Semantic review

- **Files awaiting `REVIEWED`.** 16 of 2,305 case files are `REVIEWED`; the rest are `AUTHORED`.
  `REVIEWED` requires a manual comparison of each file with its print. Done when the files are
  reviewed.
- **Semantic review items from the authored batches.** Authored scenarios whose evidence
  route or reading deserves a reviewer's eye before `REVIEWED` (none blocks execution; each is
  documented in its file): (a) the Necrarchs' Nosferatu Leader borrow is evidenced on the Danse
  Macabre break-free test because no profile of that band can take a charged Fear test; (b) the
  War Priestess's War-Honed first-failed-Leadership reroll is evidenced on a plain supplied
  Leadership test because the same rule's fear immunity pre-empts fear tests; (c) the three
  automatic-Leadership Dramatis Personae (Belandysh, Ippan Shu, Maximilian) isolate the
  automatic pass from their psychology-immunity siblings through a supplied Danse test;
  (d) the knocked-down Songster still sings (consumer posture reading, print silent);
  (e) Warrior-Priest Hammer of Sigmar = Sigmarite hammer, Gwen's Knives = two daggers,
  William's Lucky Rabbit's Foot = the trading-post item (adopted equivalences, 2026-11-18).
  Done when a reviewer confirms or re-authors each and the files advance to `REVIEWED`.
- **Construction-batch wrinkles (B11/B12, 2026-11-18).** Recorded in the files, none blocking:
  the Priest of Morr's permitted scythe has no simulation mapping (the dagger is the only
  reachable permitted weapon); the Priestess of Shallya's same rule forbids wielding her printed
  ceremonial dagger (`profile.active-weapon-restrictions` sibling, carried but unwieldable);
  the pirate human mercenary access widens only the slot picker (`buildAccess`), so a
  mercenary-pool item declared in `owned_item_ids` is refused even with the rule; the Imperial
  Assassin's "found" weapons may be wielded but not owned (supplied ownership must equal the
  printed kit); the hireling kit resolver pre-empts every priest stricture's own sentence (seven
  stricture identities probe non-discriminating with dated notes); the Halfling Too Big and
  Snotling Small Hands bans are enforced by the equipment-list gate only; the Dragon Monk's
  shield/buckler/helmet exemption and the Wolf Priest's blunt-weapon permit have no legal
  positive input; the Witch Doctor's compulsory headdress is judged only when `owned_item_ids`
  is supplied; the Master of Throwing Weapons mechanic file's header still claims the binding
  carries no parameters (it carries `max_missile_weapons`). Done when each is confirmed as the
  intended encoding or repaired.
- **Construction-skills wrinkles (2026-11-18).** Recorded in the files, none blocking: every
  printed Shooting skill (and every Academic skill) is a registry `mechanic_exclusion`, so a
  skill-access grant to those categories (Dwarf Slayer Cult Born Marksmen, Emissary of Chaos
  Tzeentch patron) can only be evidenced by diagnostic order — the compiler refuses the excluded
  skill after the access gate instead of admitting it inertly as the 2026-10-21 ruling allows for
  published table members; decide whether excluded table members should compile inertly. The
  Condemned's random profile is encoded twice (the `condemned--inconsistency` binding and the
  profile's own `source_profiles` data), as is the Born Marksmen grant (`profile.skill-access`
  with `variant_ids` and `compiler.promoted-hero-skill-access`); the Marauder/Beastmen Mutant
  gates count raw repeated `special_rule_ids` while the compiler applies a repeated id once and
  the loader has no duplicate check; the Priestess of Shallya's and Priest of Verena's strictures
  leave their printed dagger carried but unwieldable; Son of Ulric's `profile.fist` does not
  replace the kit weapon (the build must name `weapon.fist`); the Cursed Hillman's wolf form
  binds characteristic deltas where the print is absolute (fixture W/I drift). Done when each is
  confirmed as the intended encoding or repaired.
- **Survival-immunity wrinkles (2026-11-18).** Recorded in the files, none blocking: Marianna's
  `rule.fighting-undead` prints only a stub ("Uses the source anti-Undead rule") while the engine
  reads it as a defender-carried grant of Hatred to Vampire attackers — confirm the direction
  against Town Cryer 22; Mandrake Root prints "no effect on Undead" but the compiler's
  undead-inert drug set covers Crimson Shade and Mad Cap only, so the Nosferatu/Wight drug
  immunities discriminate through that gap; the Necrarch Banshee's own `forbids: [equipment]`
  refuses every drug, so her `mechanic.drug-immunity` identity is evidenced only by refusals and
  stays non-discriminating (a `covered.elsewhere` candidate on the Poltergeist precedent, which would
  retire it); one mechanic bound twice on one
  profile (Khar-Mel's Curse and Luck both bind `mechanic.djinns-curse`; the Bone Goliath's No
  Pain and Undead Construct both bind `skill.ignore-pain`) makes the rule identities
  non-discriminating (dated notes); Marianna's No Pain Knocked Down is lifted instantly by her
  Jump Up combination, so her face is STANDING; `mechanic.beak` has no engine reader (the
  compiler projects the bite); the Sigmund Spindle Frenzy compulsory charge is not modelled when a
  scenario declares `charging: []`; the Chaos Fury/Aksho "blessed" negation has no duel producer.
  Done when each is confirmed as the intended encoding or repaired.
- **Psychology and hatred wrinkles (2026-11-18).** Recorded in the files, none blocking: the
  Dark Jester's `rule.confound-and-confuse` and `rule.trip` both bind one mechanic and his
  `babbling-banter` tag is read by no engine code (the chooser carries the effect) — three
  non-discriminating identities with dated notes; `mechanic.vengeful-hatred` is compiled from the
  supplied target facts, so the probe cannot reach it; fire-fear (`mechanic.fears-fire`)
  is resolved outside ordinary Psychology, so a psychology-immune bearer would still test; the
  Lahmia Seduction's printed Stupidity exemption and the Hypnotic Musk's mount and Goading exceptions
  cannot be supplied by a fixture (the operator implements both); the Swashbuckler's Charismatic needs a printed sex the profile does not
  carry (supplied as male from the text); the Emissary of Khorne's Frenzy and +1 Attack are one
  effect-set (the +1 cannot be isolated) and the Tzeentch patron compiles identity tags only. Done
  when each is confirmed as the intended encoding or repaired.
- **Equipment and hireling-operator wrinkles (2026-11-18).** Recorded in the files, none blocking:
  the engine carries an unbound `mechanic.darting-steel` parry operator (`contexts.py`)
  with no KB record while the Duellist binds only `trait.counts-as-buckler`; the Druchii Sea
  Dragon Cloak prints a +1 overlay combinable with light armour while the Q128 ruling fixes the
  shared cloak as an armour choice (two different encodings); `armour.wizard-robe` encodes only a
  6+ save and the printed casting permission is not modelled; `species.black-orc` has no
  `trait_overrides` producer; the Dark Elf Blade material and Marianna's garlic coating are laid
  on the kit weapon by profile grants, so `main_material_id`/`main_poison_id` cannot be declared
  on those hirelings; Belandysh cannot be silenced (`require_characteristics` rolls his Attacks);
  the Misericordia's "Undead knocked down as normal" needs the victim's own No Pain; the Eagle
  Friend's second eagle strikes before the first (die order is an engine reading); several
  hireling item rules only name a catalogue item the kit already wields (Diestro's rapier,
  Nicodemus's staff, the Sister's holy relic, the Wolf-Priest's pelt), so they probe
  non-discriminating with dated notes. Done when each is confirmed as the intended encoding or
  repaired.
- **Supplied-condition and band-operator wrinkles (2026-11-18).** Recorded in the files, none
  blocking: Combat Charge's engine reading also applies the Weapon Skill bonus defensively against the reply although the print says "when
  charging"; Power Grab's compiler gate admits any Underworld Alliance duelist regardless of
  race (the majority fact is the caller's); the Disability hero-nearby exemption is decided by
  explicit Hero provider records even without the supplied id; `condition.poetry-inspired` and
  `condition.goading-charge` have no compiler recipient gate; the Bull Rush body charge rolls the
  save against the weapon's armour penetration; Deathwish selected on a Giant Slayer is inert
  because `band--slayer-rules` already grants the immunity (printed duplicate); the Lustria Wild
  Lunatics row is the sole `mechanic.lunatics` carrier (the Masters of Horror `lunatic` skill
  binds other operators); `skill.axe-mastery`'s Dwarf-axe parry face and Whirling Blades are not
  encoded; Netter and the `grant: none` producers (brewers, poetry scholars, netter, goading,
  power grab) probe non-discriminating with dated notes. Done when each is confirmed as the
  intended encoding or repaired.
- **Saves-and-rerolls wrinkles (2026-11-18, last authoring wave).** Recorded in the files, none
  blocking: the Fen Guard Bark Skin's stacked step is folded into the compiled `armour_save` and is
  Strength-modified, and a fire attack zeroes only the natural branch (the print says fire ignores
  the whole rule, stacking included — the fourth bark-skin fire scenario is authored from the
  print and flags the likely engine gap); the Halfling Elder's Layers of Fat prints "regardless of
  strength … on top of any armour" with the same folding; the Iron Fan is split between a passive
  +1 Initiative mechanic and a parrying weapon item; the Dark Jester's Sidestepper tag is read by
  no engine code (the confound chooser lights the dodge), so both identities probe
  non-discriminating/inert with notes; the Tomb Robber's dodge upgrade is runtime-only (compiled
  `ward_save` stays 5); the Cursed Hillman's wolf form encodes the lost cloak twice (trait and
  equipment projection). Done when each is confirmed as the intended encoding or repaired.

### KB, eligibility and engine defects

- **Rousing Sermon (Trollheim) cost not modelled.** The printed "He may not use
  Prayers that turn" is not enforced (no engine models Prayers), and
  `catalog/skills/warband.yaml` (`skill.inspiring-sermon`) still describes a passive
  "+1 Attack for the turn" without the declaration. The Trollheim file holds two
  real-profile scenarios plus two fixtures on `mechanic.rousing-sermon` (the
  once-per-game Mordheim operator), and its "ENGINE-DEFECT (2026-11-16)" comments are
  stale. Done when the cost is ruled out of duel scope or modelled, the skill text
  matches, and the fixtures are retired or rebound.
- **Morning Star printed text (2026-11-19).** By user ruling the Morning Star is Difficult to Use
  (it carries the `difficult-to-use` tag), but its catalogue `effect` in
  `catalog/items/weapons-close-combat.yaml` prints only "Heavy". Separately, the eligibility
  `restricted` table lets a Morning Star take no off-hand item at all, while the Broadsword's printed
  Difficult to Use text lets its bearer "carry a shield or a kite shield as normal". Done when the
  effect text matches the printed entry and the Morning Star's shield allowance is checked against it.
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
- **Profile prose `equipment_restrictions` duplicates bound rules.** The eligibility gate reads
  the free-text `equipment_restrictions` lines of `profiles.yaml` (`index.ts`, the prose scan
  near the profile-restriction stage) and yields "armour is forbidden" without the bound rule,
  so the Kislevite warrior profiles, the Marauder Seer and the Necrarch Nosferatu no-armour
  identities probe non-discriminating (dated Discrimination notes in their files). Done when
  one source carries each printed ban (the bound rule) and the prose is descriptive only.
- **The web app still applies band equipment restrictions band-wide.** The Rememberer ruling
  (2026-11-19) made the shared eligibility stage honour `applies_to.profile_ids`, but
  `tools/knowledge/generate_knowledge_web.py` (`_band_equipment_data`) and the web app's
  `packages/typescript/domain/campaign/construction.ts` (`bandFactsOf`) still treat the Slayer tokens as band-wide, so the
  web roster builder refuses the Rememberer's armour. Done when both read the recipient list.
- **A Hero with special access but no applicable special table gets every special skill.** When
  `profileSkillLists` returns no list, the access check in `eligibility/index.ts` falls back to every
  catalogue skill of category `special`. The Dwarf Slayer Cult Rememberer ("may not learn 'Slayer Only'
  skills") is therefore admitted `skill.deathwish`. Found 2026-11-19; it predates the promotion work.
  Done when the fallback is limited to the profile's own printed tables, after checking which bands
  rely on it.
- **Haughty also bars obsidian for the Mordheim High Elves.** One Dwarf-equipment guard
  (`_eligibility.js`, `index.ts`) serves two bands and treats `material.obsidian` as
  Dwarf-made: the Trollheim print names "Gromril and Obsidian", the Mordheim
  (`high-elves-lus`) print only Dwarf origin and Gromril. Done when the guard follows each
  band's print.
- **Chaos armour ban matches any "chaos" id.** The eligibility ban `Chaos armour is forbidden for
  <who>` (Chaos Engineer, `eligibility/index.ts`) tests whether any equipment mechanic id contains
  "chaos"; the print bans only "the Chaos Armours". No reachable build trips it today. Done when the
  ban names the armour mechanics.
- **Ogre Crude Belch drops extra engaged enemies.** The Ogre path (`modular/rounds.py`) resolves one
  target and silently ignores a third engaged enemy, where the Halfling path refuses a multi-contact
  fixture. Done when the Ogre path refuses it the same way.
- **Dwarf Unbeatable Warrior clause duplicates the axe re-roll.** The Dwarf `skill.unbeatable-warrior`
  effects (dwarf-treasure-hunters, chaos-streets-dwarf-treasure-hunters) still declare a
  `reroll-with-two-dwarf-axes` clause that `mechanic.master-of-blades-axe-reroll` now carries (Sword
  Master split, 2026-11-19). Done when one identity owns the clause.
- **Printed-source checks before de-duplicating.** Skaven of Clan Mors and Clan Skryre
  (Karak Azgal) `band--rulebook-inheritance` grants a skill list whose members are already
  Hero-only warband skills of their own: the access is encoded twice and the two files carry a
  Discrimination note; keep one source. `mad-scientist--lunatic` is printed as a Special Skill but granted
  automatically to four Masters of Horror profiles, which makes the Thrall's own
  Cause Fear redundant: `thrall--cause-fear` and the five
  `mad-scientist--alchemist` conditions probe `non-discriminating`; check the
  print. Done when each encoding matches its print and the probe reports the
  identity `discriminating`.
- **Scenarios that contradict or miss their print.** The Mordheim Pirates Sea Shanty
  scenario `a-psychology-immune-enemy-is-not-tested-and-keeps-both-attacks` contradicts its
  print (only Undead and non-living are exempt; the Trollheim copy matches its own print);
  in both Curse of the Reborn files `the-four-plus-regeneration-save-ignores-the-wound`
  declares `blocked-by-fire-and-blessed` without evidencing it (the clause itself is evidenced
  by dedicated fire and blessed tapes; only that scenario's `covers:` label is over-broad). Done when each
  scenario matches its print and identity.
- **Engine or eligibility behaviour without printed support.** Any two Dwarf axes
  get a parry re-roll regardless of skill (`contexts.py::_parry_context`, mirrored in both
  ports; check first whether the Dwarf Slayer Cult's printed Parry rule, which the code comment
  cites, needs it - Master of Blades now has its own carrier, `mechanic.master-of-blades-axe-reroll`,
  which probes non-discriminating until this term is gated); Wheelo
  fittings are gated on `mechanic.wheelo-impact`, not on the rule; the
  chaos-streets Troll Slayer refuses every special skill through `skill_ids`
  while a Dwarf Noble is admitted to Monster Slayer; Battle Monks warrior-monks
  henchmen are admitted to Energy Focus. Done when each is fixed or ruled.

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

## Rules-conformance suite memory use with several workers

Running `tests/conformance` with many pytest-xdist workers has frozen or forced a reboot of a
16 GB machine. Measured on 2026-11-20 (commit `3f580a6f9`, one process and `-n 1`/`-n 2`): there is
no runaway leak, since every process's memory levels off. Each worker cost a fixed amount, about
770 MB at peak (892 MB with `-n 1`), so the total grows with the worker count: about
100 MB + 770 MB per worker. Projected, `-n 8` needs about 6.3 GB and `-n auto` (12 workers on that
machine) about 9.3 GB, beyond the 8 GB that was free. Projection only: no run above `-n 2` was
measured. The `_COMBINED_EFFECTS` effect cache was measured and is not a cause; the removal probe
alone levels off at about 450 MB per worker.

Fixed in the same change, measured on 300 scenarios but not yet on a full or multi-worker run:
the five test modules now share one corpus (`corpus.shared_corpus()`, saving about 200 MB per
worker), and `check_case` asks the eligibility JavaScript engine for a full collection every 50
scenarios (`eligibility.collect_garbage()`). That engine collects lazily and otherwise holds
150-190 MB of garbage per process.

Pending:

- **Re-measure after the fixes.** Run the full suite with `-n 1`, `-n 2` and ideally `-n 3`/`-n 4`
  under the adaptive memory watcher, and compare with the 2026-11-20 reports. Done when the
  per-worker peak and the scaling with workers are measured on the fixed revision. The expected
  peak, about 400-450 MB per worker, is an estimate from the 300-scenario run.
- **The whole-corpus variant check doubles the suite's work.**
  `integrity/test_variants.py::test_executing_the_corpus_does_not_change_shared_variant_data`
  re-runs all scenarios inside one test, and with xdist it decides the wall time: 417 s with
  `-n 2`, 158 s without it. It barely changes memory. Done when the mutation check no longer
  re-executes the corpus (for example by snapshotting the shared data around the ordinary
  scenario run) or is made opt-in.
- **pytest collection cost per worker (inferred).** Each worker reached 520-590 MB before
  executing much, against 340 MB for imports, corpus and the engine in one process; every xdist
  worker collects all 8,005 items. Done when a `--collect-only` measurement confirms or rejects it.
- **No worker cap.** `tests conformance` forwards `-n` (including `-n auto`) unchanged. Done when
  the documented guidance (or the launcher) derives a safe worker count from the memory available.
- **Minor.** The engine process keeps 55-65 MB of freed memory until `malloc_trim`. The xdist
  controller grows to about 100 MB with the number of test reports. The removal probe rebuilds the
  4.8 MB eligibility catalogue for every scenario (`_catalogue.cache_clear()`): extra CPU, not
  extra memory; see the entry below.

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

## Web-app tests read a stale knowledge artefact

Three web-app tests (`knowledge-reader.test.ts` H7 concessions, `rules-catalogue.test.ts` shared-rule
count, `warband-reference.test.ts` Sisters sheet) fail against
`outputs/web-public/knowledge/knowledge-web.json`, an untracked artefact generated on 2026-11-17 from
an older KB. Done when the artefact is regenerated (`tools/knowledge/generate_knowledge_web.py`) and the
tests are re-run; any that still fail become defects of their own.

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
  corpus scenarios (the corpus has since grown to about 7,900 scenarios, with scenarios moved
  between identities and case files retired on 2026-11-18/19, so re-measure first): of 5,161 deliveries, 436 keys name
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
