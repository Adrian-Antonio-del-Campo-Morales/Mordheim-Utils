# L06–L14 — local modular rule integration

**Current scope, 2026-10-04:** the [user's 1v1 decision](../../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04)
supersedes historical group/multi-recipient deferrals below. Group Rout, extra
independent combatants and multi-enemy Crude Belch resolution are excluded.
Provider inputs remain caller-supplied external snapshots; no group lifecycle
is required. Individual duel clauses and visible supplied conditions remain.

Canonical modular milestones delivered on 2026-10-04. 249 canonical clause milestones
now reach their admitted local effects, including the subsequent natural-attack,
injury, recursive-attack and first-attack-loss blocks below. Existing generic hit, wound,
parry, armour and special-save resolvers are reused. L06/L07/L08 and T13 remain
open; this is not optimized-engine or integral certification.

## Source contracts and implementation

| Canonical rule | Source consulted | Modular behavior |
| --- | --- | --- |
| High Elves / Miniath | [High Elves](https://broheim.net/downloads/warbands/supplement/lustria/High%20Elves.pdf), PDF p. 3 | Existing `skill.miniath`: any weapon parry, native-parry reroll under the accepted Miniath contract. |
| High Elves / Unerring Strike | Same source/page | Existing `skill.sure-strike`: one failed-wound reroll. |
| High Elves / Fey Quickness | Same source/page | Existing `skill.elven-agility`: melee special save 6+, improved to 4+ with Step Aside. Shooting remains excluded. |
| Silent Brotherhood / Cutthroat | [Silent Brotherhood](https://broheim.net/downloads/warbands/supplement/sealedcity/Silent%20Brotherhood.pdf), PDF p. 2 | New `skill.cutthroat`: +1 armour penetration for the attacking dagger when wielding a real dagger pair. A paired Long Daggers profile qualifies; one dagger or dagger/sword does not. The ordinary dagger enemy-save bonus remains its own contribution. |
| Silent Master / Perfect Killer | Same source, profile entry | Existing `trait.perfect-killer`: automatic +1 armour penetration, absent on the Poisoner. No shooting subsystem added. |
| Bitter Moors / Virtue of Valour | [Knights of the Bitter Moors](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Knights%20Of%20The%20Bitter%20Moors.pdf), PDF p. 3 | New `skill.wound-valour`: failed-wound reroll only against strictly higher natural Strength, independent of weapon bonuses. |
| Sea Troll / Slimy | [Orc Pirates](https://broheim.net/downloads/warbands/supplement/sartosa/Orc%20Pirates%20%26%20Savage%20Orcs.pdf), PDF p. 4 | New `mechanic.sea-troll-slime`: incoming melee hit modifier -1; generic natural-six success remains. |
| Feast Master / Talismanic Tattoos | [Sea Ghosts](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Sea%20Ghosts.pdf), PDF p. 5 | `trait.ward-save` value 6 replaces the erroneous natural-armour binding. The real special-save stage retains the save against high Strength, magical and armour-negating attacks. |

The same name does not imply the same Virtue of Valour rule: the existing
`skill.virtue-of-valour` grants conditional hit rerolls under its own reviewed
source. It was neither changed nor reused for Bitter Moors' wound variant.
Cutthroat's family check uses maintained explicit dagger tags, including the
paired poisoned/disease variants; it does not infer a dagger from equipment
prices or generic one-handedness. Natural extra attacks do not receive it.

Canonical runtime bindings and their five exact ingestion mirrors were updated.
Source text, recipient declarations and other runtime blocks were retained.
Source identities in the historical T13 origin register remain unchanged;
L21 owns reconciliation to the newly active effect identities.

### High Elf access correction discovered during activation

The PDF p. 3 skill table was visually checked (retained screenshot and original
PDF under the evidence directory). The original profiles had mistranscribed
columns. Correct maintained lists are:

| Profile | Printed categories |
| --- | --- |
| Loremaster | Academic, Speed, Special |
| Sword Warden | Combat, Academic, Strength, Speed, Special |
| Ranger | Shooting, Speed, Special |

All three canonical profile lists and their 2B mirror now match that table.
The shared eligibility module consumes these facts without a new rule table
or bundle change. Actual compilation and catalogue offerings use the corrected
access; the focused suite asserts the three table rows. No approximate default
or extra general category was added to make a combat test pass.

## Focused validation

The one new maintained family suite is
[test_local_modifier_variants.py](../../../../tests/python/combat/modular/test_local_modifier_variants.py),
The initial block has 17 cases through canonical compilation and strict real attacks. It covers
activation/absence, dagger-pair controls, natural-Strength equality/weapon
controls, parry reroll, save-kind immunity and canonical access. Existing
mechanism traversal initially ran 204 mechanisms (201 + three local variants);
the subsequent blocks increase it to 207.
The old automatic-grant matrix no longer asserts Tattoos as natural armour;
its recipient and real save behavior are covered by this suite.

Entry backups and command results are retained under
`build/cache/t13-parallel/local-modifiers-defences/`. Broader affected cases,
schemas, mirrors, generated knowledge and documentation links are checked
once for the complete family; no new parallel spec/mutation/review battery
was created. New modifier variants explicitly require the modular backend.
L19/L20 retain their ports, and the user has instructed this autonomous run
to stop before starting those lots.

## Problems and resumption

- The family run passed all 142 local/automatic/catalogue cases. Its additional
  promotion gate exposed twelve inherited L06 item metadata conflicts in the
  staging trees. Only `mechanic_id`/`combat_status` were synchronized to the
  live KB, without changing source text, prices or references. The fresh
  promotion/documentation run then passed ten cases. F066 records that repair.
  Schema/data-isolation checks passed for 24 affected documents.
- The Knight's Helm report's one broken relative file link was corrected;
  the source investigation and its implementation limits remain unchanged.
- F022 is corrected for canonical/modular save semantics; remaining backend
  and final certification belong to the existing L19–L22 owners.
- F063: the user classified `knights_helm` as a source erratum on 2026-10-04
  and confirmed its planned KB removal. The Basha 4+ counterpart is no longer
  an implementation obligation; pending data/reference cleanup stays in F063.
- F064/F065 retain Hellblade target facts and Concealable carry/scenario
  contracts. Neither clause is excluded or declared complete by this family.
- High Elf profile/source digests and the newly active identities require
  their normal L21 reconciliation. Existing historical pins and source-question
  gates are not bulk refreshed to conceal these transitions.

No vectorized/native implementation, automatic agent launch, commit or push
was performed by this milestone.

## Subsequent L06/L07 block — natural attacks and injury grants

Thirty-two further canonical rules reuse existing execution operators, apart
from Wolf Rat's explicit armour exception. Source text and identities are
preserved; changed bindings are synchronized to their existing ingestion mirrors.

| Rules / source | Admitted behavior and boundary |
| --- | --- |
| Clan Moulder Wolf Rat / [printed web source](https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder) | New `mechanic.wolf-rat-bite`: natural attack S4, with no Strength-derived armour modifier. Its name does not grant Black Lotus or another generic poison. |
| Mousillon Plague Rat / [Pestilens PDF](https://broheim.net/downloads/warbands/supplement/mousillon/Skaven%20of%20Clan%20Pestilens.pdf), p. 6 | Existing `poison.black-lotus` on its actual natural attack, without an equipment purchase. Natural hit six and poison immunity use the maintained wound resolver. |
| Five Blood Dragon immunity grants / [Blood Dragons PDF](https://broheim.net/downloads/warbands/supplement/mousillon/Blood%20Dragons.pdf), pp. 4–6; Fallen Revenant / [Relics PDF](https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf), p. 13 | Existing `trait.poison-immune`, recipient-scoped; Vampire, Wights, Skeleton Warriors, Grave Guards, Hell Hounds and Fallen Revenant gain no invented disease immunity. Dreg/Butcher controls remain nonimmune. |
| Sixteen No Pain grants / Blood Dragons (five), [Night Haint PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf) (seven), [Masters of Horror](https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror) (three), [Survivors of Strigos](https://mordheimer.net/docs/warbands/grade-2a-warbands/survivors-of-strigos) (one) | Existing `skill.ignore-pain`, automatic and once-only; the real injury resolver converts Stunned to Knocked Down. Existing chart/reaction ordering is retained. |
| Night Haint Poltergeist / same PDF, p. 5 | Existing `trait.injury-profile` value 2: an unsaved wound immediately takes it OUT without an injury die, before No Pain. Its separate Ethereal clause is not certified here. |
| Dwarf Slayer Cult Hard to Kill and Hard Head / [source](https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult) | Bind existing `skill.hard-to-kill` and `trait.concussion-immune`: injury 2 remains Knocked Down against a mace, 5 is Stunned and 6 is OUT. Related unsupported psychology clauses remain separate. |
| Snotlings Dodgy, Not-So-Tough Gits and three exemptions / [source](https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings) | Recipient-filtered 6+ melee save (4+ with Step Aside), injury chart KD1/Stunned2–3/OUT4–6. Goblin and Wheelo receive neither effect; Mobs retain Dodgy and the normal chart. Campaign/missile clauses remain separate NO effect rows. |

Snotling recipient lists are source facts consumed by the already centralized
shared filter. No second eligibility table or engine rule was introduced.
The 829-row automatic trace preserves every original `origin_key`; 32 rows
were reconciled here, including limitations rather than a whole-profile claim.

## Subsequent L07/L08 block — conditional ward and recursive attacks

- **Domnu / Gypsy Ward:** the [Strigos source](https://mordheimer.net/docs/warbands/grade-2a-warbands/survivors-of-strigos)
  prints a magical-only 5+ special save. New `mechanic.gypsy-ward` activates
  that minimum only when the actual incoming attack is magical, preserving
  stronger saves. A mundane-only contribution cannot block this separate
  magical save. No spell casting or battle-magic subsystem was added.
- **Mourngul / Ravening Onslaught:** [Night Haint PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf),
  p. 5, explicitly grants further attacks on subsequent hit sixes. New
  `mechanic.ravening-onslaught` appends a natural attack to the prepared pool
  for each physical six, including generated attacks. No arbitrary recursion
  cap is introduced. All hit rolls join collective preparation before parry
  and wounds; removal interrupts remaining wound resolution through the
  existing reaction pipeline. A normal five never extends the pool.

The two additional automatic trace rows retain their original origin keys.
The complete maintained local modifier suite has 47 cases, including three strict
whole-round Onslaught tapes. Only changed behavior and meaningful controls
were added to this one suite and the existing automatic-grant matrix.

Evidence for the subsequent blocks is under
`build/cache/t13-parallel/natural-poison-attacks/`. Source preservation and
schemas pass for 20 changed documents; changed mirror rules match canonically.
Unrelated pre-existing staging reason paths are preserved for promotion's
maintained reference rewrite. No blanket byte-equality claim is made for
those unrelated rows. Wolf Rat, Gypsy Ward and Onslaught require the modular
backend until L19/L20.

Wolf Rat's structural closing check identified that an intrinsic profile
attack had been placed on an attack-trigger skill that free skill projection
does not consume. Its final contract is a passive profile tag: the real
Strength/armour resolver enforces S4 and no Strength-derived armour modifier.
Canonical behavior remains the same; the ordinary maintained structural
projection and tag-consumer gates now both prove the final contract. No audit
allowlist or weakened check was added.

### Deferred source and context gates

- F013/Q013 remains blocked: Strigos' source specifies prerequisite Great
  Thirster, recovery 5+ and one wound per turn, but not its exact recovery
  point or relation to fire. Its existing generic regeneration binding is
  a known unresolved defect, not validated by the new No Pain or Domnu cases.
- Ivy Ferret Poison Teeth also constrains attacks to rounds in which its
  keeper can attack. Reusing Lotus alone cannot close that compound rule;
  L17 owns keeper-dependent local allocation before activation.
- Andanti anti-Vampire effects and F064 Hellblade need exact opponent
  category facts from L11; a broad Undead/Possessed flag is insufficient.
- House Guard Dueling Pride needs its House variant and Hero facts; Pikewall
  needs the receiving-charge direction in the hit context. Resume those
  local rerolls with L08/L11 contextual work, rather than binding generic
  Hatred or inferring a House from the band id.
- New source fingerprints, active verifier identities and coverage line
  positions belong to L21 reconciliation. Previously accepted budgets/pins
  do not certify the changed engine revision. Original source-question and
  exclusion boundaries remain in force.

## Subsequent L07/L08/L10 block — unarmed training, natural hide and Leadership

- **Channel Rats Domnu / Prize-Fighter:** [the source PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Channel%20Rats.pdf),
  printed p. 179 (PDF p. 5), supplies no unarmed penalties and +1 Attack when
  unarmed. Existing `skill.unarmed-fighting` already has exactly those
  operators. Its automatic binding gives A3/S4 with fists, while a mace
  retains A2. The source's Bear Hug remains separately pending: F067 records
  the replacement/allocation question introduced by the third attack.
- **Ogre Hunting Party Sabretusks / Tough Hide:** [the primary web source](https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party)
  supplies natural armour 5+. The existing `trait.natural-armour-save`
  binding retains normal Strength modifiers. Fear, Untamed and the literal
  charge attack-count clause are not certified by this save.
- **Halflings / Crude Belch:** [the dedicated milestone](T13-crude-belch.md)
  supplies canonical selection, actual 2D6 Leadership and ordered loss of the
  first/only attack. Eight strict round cases reuse the real engine. Extra
  enemy contacts fail explicitly until the multi-recipient consumer exists;
  F061 remains open at that boundary.

The original 829 automatic-trace origin keys are preserved. Three rows are
reconciled to these delivered bindings; Crude Belch's row explicitly records
that its historical automatic origin is now selectable. The live selectable
partition is 56 origins / 55 canonical rules, without changing the historical
obligation register or hiding the Master of Blades dual provenance.

## Autonomous continuation validation

The final family and affected construction checks use the maintained suites.
No duplicate spec/mutation/review battery was created for these local rules.
The maintained modular gate passed **447 cases** after the Crude Belch
recovery/finishing guards; the focused Crude/selection reconciliation passed
59 cases. The subsequent Wolf Rat closing contract change was verified by
the 50-case affected family/catalogue rerun and the full structural projection,
without repeating unrelated suites.

The final Wolf Rat contract rerun passed all 50 local/catalogue cases;
the affected construction scope passed **608 cases** before that final Wolf
binding adjustment. Structural verification
is green with **1,050 profiles**, **211 execution mechanisms / 208 projected**,
**183 observable bindings**, **539 implemented rule records** and **82 explicit
tag consumers**. The existing snapshot assertions were reconciled to those
actual catalogue changes; their independent no-binding and field-ownership
checks remain. These are structural counts, not semantic certification.

Promotion exposed two obsolete `BAND_SCOPE_REPAIRS` entries that forced the
now-active Dwarf Slayer rules back to LATER. Those two entries were removed;
the other declared repairs and undeclared-collision refusal are preserved.
This is distinct from the earlier twelve item-metadata repairs (F066).
The fresh promotion suite passed **9 cases**; the four affected structural
tests and documentation links pass. The generated web catalogue was rebuilt
and its maintained `--check` passes at the final KB revision.

Schemas and source isolation pass for the subsequent 20-document block and
the six Crude/Prize-Fighter/Hide documents. Changed ingestion rules match their
canonical rows. Original source prose and unrelated runtime blocks remain.
Promotion, publication freshness and documentation links use their maintained
checks. This does not run T14's full semantic/parity certification, refresh
source pins or rewrite coverage budgets. Their current-revision reconciliation
remains L21; modular implementation itself remains incomplete.

## Subsequent L08/L09 block — ordered natural attacks and one chosen reroll

Implemented on 2026-10-04 through the existing canonical compiler and modular
round pipeline. This adds three rules to the previous 45-rule continuation.

| Canonical clause | Source and resulting behavior |
| --- | --- |
| Shallows Beasts / Mutant-Priest / Bite Attack | [Original PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Shallows%20Beasts.pdf), PDF p. 3 / printed p. 191. `compiler.strikes-last-bite` creates one independent natural attack, using the Priest's own Strength without fist penalties. A final round event follows both warriors' weapon attacks, including double-handed weapons. |
| Ogre Hunting Party / Sabretusks / Charge | [Canonical web source](https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party), Sabretusk Cubs / Charge. `mechanic.sabretusk-charge` replaces base Attacks with two during the actual charging phase. It is not a generic additive bonus; ordinary profile Attacks remain in other phases. |
| Lothern Sea Patrol / Seaguards / Spear Master | [Original PDF](https://broheim.net/downloads/warbands/supplement/sartosa/Lothern%20Sea%20Patrol.pdf), PDF p. 4. `mechanic.seaguard-spear-master` supplies first-round Strength +1 only to an actual spear, plus one chosen failed hit reroll. Declining a miss preserves the resource for another miss; the replacement result stands. |

The bite is excluded from ordinary extra-attack allocation even when a broken
weapon causes the equipment projection to be rebuilt. Its own event preserves
the phase's parry and once-only resources, and is cancelled if its owner is
disabled or the target is removed first. It cannot repeat whole-pool
replacements or weapon-only effects. Two final bites use their own Initiative
and the existing tie resolver after ordinary-event ordering, without borrowing
weapon Initiative bonuses. Charge, Strongman and ordinary strike-first effects
cannot move the bite ahead of weapon attacks.

Spear Master reuses `FighterState.resources_spent`, the existing hit resolver
and `DecisionPolicy`. The hit-preparation pool now forwards that policy for
the optional failed-hit choice. Successful hits, other weapons/profiles,
later rounds and already-rerolled failures receive no extra reroll request.
Existing automatic hit rerolls keep their policy; Spear Master never creates
a second reroll of the same die. Its first-round Strength also affects the
ordinary armour modifier through the existing shared Strength projection.
This does not activate the separately configured Hero Honour of the same name.

An exposed construction mismatch was repaired in this block: for a profile
without equipment lists or fixed equipment, neutral `weapon.fist` now projects
the same natural attack as the default dagger input. Previously the explicit
empty-hand input could apply fist penalties and clamp the Sabretusk to one
attack. Explicit `profile.fist` contracts and equipped profiles retain their
own unarmed semantics. Shared eligibility and campaign services were unchanged.

The existing family suite now has 63 cases, including 16 focused additions
for these clauses and the neutral-input boundary. No separate test/spec/review
battery was added. All three canonical runtime rows match their exact 2A/2B
mirrors; original source text and recipients are unchanged against HEAD.
The automatic register keeps all 829 origin keys and updates only these three
rows. Existing structural/catalogue count assertions follow the real additions.
Source/mirror reconciliation is retained under
`build/cache/t13-parallel/attack-priority-resources/source-mirrors.json`.

L08/L09 remain open. Pistol-only Shifty and the pistol shot/resource contract
retain F005/F026/Q151; Domnu Bear Hug retains F067. Ports remain L19/L20,
visible configuration L18, and source-pin/coverage/T14 reconciliation L21.
No source pins, coverage budget or vectorized/native implementation were changed.

Closing validation for this block: **1,080 passed** in one maintained affected
run (463 modular, 608 construction, nine staging-promotion cases); **four
affected structural checks passed**. The current structural snapshot is 213
execution mechanisms / 210 projected, 36 automatic compiler contracts, 186
observable canonical bindings, 542 implemented rule records and 84 execution
tag consumers. The generated web catalogue was rebuilt through its maintained
generator. These checks preserve the separate L21/T14 semantic and coverage
barriers; implementation coverage is not inferred from the structural counts.

## Subsequent L10/L12 block — actual local Leadership providers

Implemented on 2026-10-04, reusing Crude Belch's real Leadership caller rather
than introducing a contract-only API. Four additional canonical clauses bring
this continuation to 52 rule milestones. The Cult of the Possessed clauses
provide the source-backed baseline alongside the two 2A/2B leader origins.

| Canonical clause | Source consulted and resulting behavior |
| --- | --- |
| Halflings / Elder / Leader | [Halfling source](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings), Elder / Leader; the existing `shared-rule.leader` reference is preserved. Optional Leadership provider within 6 inches. |
| Shallows Beasts / Buccaneer / Leader | [Original PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Shallows%20Beasts.pdf), PDF p. 3 / printed p. 191. Same provider contract, using the Buccaneer's actual compiled Leadership. |
| Cult of the Possessed / Magister / Leader | [Canonical source](https://mordheimer.net/docs/warbands/grade-1a-warbands/cult-of-the-possessed), Magister / Leader. Same-warband provider at 6 inches. |
| Cult of the Possessed / Darksouls / Crazed | Same source, Darksouls / Crazed. Automatically pass required individual Leadership tests; no Leadership dice or provider lookup are consumed. This does not grant a generic psychology-immunity tag or implement warband Rout tests. |

The [general Leader rule](https://mordheimer.net/docs/rules/leadership-psychology#leaders)
forbids borrowing from knocked-down, stunned or fleeing leaders. Providers
must therefore be standing, on the tested warrior's local side, and carry
the same compiled canonical `band.*` fact. The supported local side represents
one such warband group. It is not a campaign roster identity; mixed alliances
of separate warbands of the same canonical type, and hireling membership,
are not modeled by this contract (F068, L12/L16/L17). Distances remain explicit edge-to-edge inches; missing distance for
an otherwise eligible provider fails before any test dice. Disabled, opposing
and foreign-band providers do not request a distance or decision.

`resolve_local_leadership` uses the tested warrior's own Leadership unless
an eligible provider is chosen. Candidate order follows the caller's supplied
nearby participants; the first accepted provider supplies the threshold.
Decision keys are `<test-key>.leader.<participant-id>`. The original two dice
keep `<test-key>.0` / `.1`; equality passes. Declining an unknown provider keeps
a known own value usable; accepting an unknown value fails before rolling.
Auto-pass precedes all such requirements, so it also works for unknown own
Leadership. With no nearby context, ordinary legacy Leadership tests remain.

Nearby providers are read-only snapshots; the caller supplies their current
condition. The mutable duel opponent cannot confer its Leadership, and a
participant's own Leader tag does not produce a choice to borrow from itself.
This is local simulation context, separate from shared warrior construction
and from campaign routing. All new mechanics explicitly refuse optimized
execution pending L19/L20; no vectorized/native implementation changed.

The existing Crude Belch suite was extended from eight to 21 cases: actual
round outcomes distinguish provider acceptance/refusal, exact/outside range,
provider state/side/band, unknown facts and automatic pass. Two direct calls
to the same production Crude Belch operator prove the other canonical leader
recipients. No parallel test/spec/mutation/review battery was added. The two
2A/2B rows update the automatic register without changing its 829 origin keys;
canonical runtime mirrors preserve complete source prose and recipient lists.

L10/L12 remain open: additional providers, rerolls, group tests and routing
still require their source-specific consumers. In particular, Wizened
Halfling is a selected leader skill and benefits Halflings, not the band's
Ogre or Piggies. It remains pending until exact recipient facts and its
optional failed-test reroll are implemented together (F068). Generic
Cold-blooded summaries are not applied to Crude Belch: the original printed
variant restricts its dice rule to Psychology/Rout tests. L18 still owns
visible neighbor/provider configuration; L21/T14 own semantic pins, coverage
and final certification. No source pins or coverage budgets were changed.

Closing validation: the affected combined run reported **1,092 passed and one
failed** (476 modular, 608 construction and nine promotion cases collected).
The failure was the existing Shifty guard control assuming an unselected
Elder had no modular-only rules; its innate Leader now requires the modular
engine. The same test retains a supported unselected Cook control and checks
the Elder's explicit refusal. The final focused rerun passed **56 cases**
(35 Shifty activation and 21 Crude Belch); the broad run was not repeated.
This is an explicit support change for newly activated leader profiles even
when a particular duel would not consume their aura, pending their ports.

Five affected structural checks passed (the expensive independent effect-pair
matrix was not rerun). The fresh structural snapshot is **215 execution / 212
projected**, **188 observable canonical bindings**, **546 implemented band-rule
records**, and **86 tag consumers**, with no structural errors. Source/mirror
checks validate the six band documents and three catalogue contracts, and
preserve all four original rule texts/recipients against HEAD. Documentation
links, regenerated publication freshness and `git diff --check` pass. Compact
closing evidence is in `build/cache/t13-parallel/local-leadership/`; full test
output remains in the coordinator transcript. No phase completion, current
source-pin certification or optimized behavior is inferred from these counts.

## Subsequent L11/L14 block — Fear tests, hits and cancelled charges

Implemented on 2026-10-04. Three additional canonical Fear clauses bring the
continuation to 55 milestones: Halfling Village Ogre, Ogre Hunting Party
Sabretusks and classic Cult of the Possessed / The Possessed. Their standalone
printed Fear clauses bind the new `mechanic.causes-fear`; multi-clause Ogre
Huuuuge, other undeclared variants and unrelated source entries remain pending.

Sources consulted: [Living Rulebook, printed p. 23 / PDF p. 22](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf),
Fear/Frenzy/Hatred; [Halfling Village Ogre](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings);
[Sabretusk Cubs](https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party);
[The Possessed](https://mordheimer.net/docs/warbands/grade-1a-warbands/cult-of-the-possessed).
The [FAQ compilation](https://mordheimer.net/docs/faqs#psychology) reproduces the
2005 Rules Review p. 33 clarification that the failure affects attacks against
any opponent. Its Other Pistol Related section also attributes the natural-six
requirement overriding hit modifiers to the author's clarification. No pistol
resource/allocation decision under F005/F026/Q151 is closed by this lot.

The erroneous EN/ES `condition.fear` summary (flee when charged) was replaced
with both charge-direction outcomes and their exceptions. `condition.hatred`
was repaired from the same primary page: first combat turn rerolls against
hated opponents, with no invented Leadership-to-avoid-charge obligation.
Hatred target variants still need their own source-backed recipient facts;
this source correction does not activate them. Other condition rows are intact.

The modular initial charge pipeline now uses `resolve_local_leadership` before
contact reactions, Crude Belch, Spines, priority and attack allocation:

- Failed voluntary charge: remove that actual charge flag, record the attempted
  side in `DuelState.failed_charges`, and leave the pair unengaged when no charge
  succeeds. No contact attacks, charge bonuses, priority dice or kill credit are
  invented. Player-turn ownership is preserved independently of the failed charge.
- Failed test while being charged: set the tested fighter's transient
  `fear_hit_sixes`. All melee hit contexts, including ordinary hands, Shifty,
  prepared hits and subsequent rerolls, use target six irrespective of hit
  modifiers or automatic-hit flags. Sweep's alternative hit procedure cannot
  bypass this requirement. Passive nonmelee damage retains its own procedure.
- A Fear-causing fighter ignores Fear tests; a currently frenzied fighter in
  this supplied in-range duel is exempt. Loss of Frenzy uses mutable state,
  not the original compiled flag. Darksoul auto-pass and chosen valid nearby
  leaders reuse the delivered personal Leadership path.

Dice keys are `round.0.<side>.fear.charge.0/.1` for an attempted charge and
`round.0.<side>.fear.charged.0/.1` for receiving a successful opposing charge.
Provider choices reuse `<test-key>.leader.<participant-id>`. Unknown Leadership
fails only when a test actually needs it. No-charge established melee does not
request Fear tests. On later combat phases the hit restriction is cleared and
no initial-charge test repeats. Unaffected encounters retain their original
charge/turn state rather than acquiring extra initialization behavior.

Both modular drivers stop a pair whose initial charge failed as **unresolved**,
with both fighters alive, rather than silently making them fight in the next
iteration. Observed resolution rounds record the one attempted phase. The
caller can supply a new engagement later; this lot supplies no board movement,
pathfinding, interception, charge-range calculation or automatic re-engagement.
Explicit `DuelContext.charging` describes in-range initial attempts, not an
unconditional promise that Psychology permits contact. Existing legacy random
charge choice remains the initial attempt for unconstrained duels.

Fifteen cases were added to the existing local family suite (63 -> 78), using
canonical fighters and strict request tapes, plus explicitly labelled free
trait/effect controls. Cases cover both failure directions, equality, expiry,
actual state and provider consumption, no extra passive hit die, two drivers,
Shifty/collective hit preparation and one permitted hit reroll. Existing
Sabretusk charge fixtures now provide known opponent Leadership and the
required successful Fear tape; no missing value was assigned in production.
The general catalogue control likewise supplies explicit Leadership. No
separate per-rule spec, mutation or review battery was introduced.

Temporary optimized support guards remain until L19/L20 port this behavior;
all three engines still share the final target contract. L11/L14 remain open,
including involuntary movement/interception and later engagement facts (F069),
source-specific test dice/rerolls (L10), remaining variants, product presentation
(L18), and current source-pin/coverage/T14 reconciliation (L21/T14). No source
pins, coverage budget or vectorized/native implementation were changed.

Closing validation: the modular and construction suites, staging promotion and
canonical condition catalogue gate pass together: **1109 passed** (201.51 s).
The affected structural inventory checks pass: **5 passed, 1 deselected**;
the quadratic all-effect-pairs check was not repeated. Documentation links
pass. The maintained web knowledge generator was run and its freshness check
passes. These results validate this delivered block, not completion of L11/L14
or the outstanding T14 certification.


## L11 continuation — common Fear grants and supplied current conditions

The shared Fear consumer now has **97 canonical band-rule connections**
(previously three; 94 added). This includes the ordinary Fear clauses of
Vampires, Skeletons, Zombies, Rat Ogres, Minotaurs, Kroxigors, Trolls and other
printed recipients, following shared references as well as local rule text.
The 97 include the selectable Hideous mutation and Nurgle blessing. No rule is
activated merely because an incidental mention of Fear appears in its prose.

Band grants retain their printed exceptions: Brood of Ghurash grants Fear to
its three starting Hero profiles; Maneaters excludes Youngbloods and does not
mistake the independently Fear-causing Sabretusk for an Ogre; Tomb Guardians
excludes living Tomb Scorpions. These recipients use the existing shared band
recipient filter. This does not automate future promotions or transformations.

Seven compound records execute their unconditional Fear clause only:
`fen-guard-mim/branchnymph--instinctual`,
`ogre-hunting-party-web/band--huuuuge`, and the five `ghost-pirates-sar`
Undead records (Ghost Captain, Screaming Ghosts, Skeleton Mates, Gibbets,
the Bloated). Their other printed clauses retain explicit pending effect rows.
A runtime marker does not claim those remaining clauses are implemented.

Additional acquisition paths:

- **Fearsome / Temible**: `skill.fearsome` is executable, uses Strength-skill
  access through the shared eligibility decision, and grants the existing Fear
  tag. Its obsolete psychology exclusion was removed. Source:
  [Strength skills](https://mordheimer.net/docs/campaigns/skills#fearsome).
- **Hideous**: the Cult mutation and Nurgle blessing bind the same Fear mechanic;
  their existing recruitment, recipient and selection restrictions remain.
  Other mutation-grant routes projecting that canonical mutation reuse it.
- **Chainsaw Sword**: the canonical item is mapped to a one-hand weapon with
  the printed -2 armour-save effect. Bearing it, in either hand or a supplied
  complete carried kit, grants Fear independently of striking with it. Its
  armour penetration remains on its own attacks, not the bearer globally.
  Source: [Masters of Horror](https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror).
- **Beastlash**: the existing wielded weapon now feeds Fear only against a
  canonical `species.animal` opponent. It does not grant unrestricted Fear to
  its bearer. A stored, unwielded Beastlash does not activate Beastbane.
- **Acquired or already-active condition**: the existing typed
  `FighterBuild.trait_overrides` accepts `causes_fear: true`. Compilation projects
  the common tag exactly once. This is a current local combat fact, suitable
  for acquired Horrible Scars or an already-active fear-granting effect. It
  grants no new skill, mutation, purchase permission or spellcasting ability.

Combat Lab's fighter editor exposes **Causes Fear (already active)** and an
optional explicit Leadership field; blank Leadership remains unknown. The
editor preserves this fact and Leadership through its existing build/workbook
representation. Turning off the supplied condition cannot erase Fear granted
independently by a profile, skill or carried Chainsaw Sword. The UI labels are
published in English and Spanish. No Warband Manager campaign is imported.

The current-condition input is a supplied snapshot for this local engagement.
It does not cast Death Vision, roll the injury chart, acquire mutations, or
schedule a spell's expiry. If an effect expires before another engagement,
the caller supplies the new snapshot without it. Exact spell/group activation,
recipient selection and phase expiry remain with their original action-family
owners, not a new generic spell engine. F070 records the remaining conditioned
sources, and F069 retains involuntary contact/later-engagement integration.
The new input must not be used to certify those unimplemented producers.

Nine functional cases were added to the existing modular family suite, plus
one editor round-trip case. The existing all-profile construction/round gate
covers the expanded data; no per-profile test battery, specification corpus or
mutation project was added. Existing Onslaught tapes now include the printed
Fear test for the newly activated Mourngul. Vectorized/native implementation
files and source pins remain unchanged; temporary optimized guards cover all
these Fear inputs until L19/L20.

Closing validation for this continuation: **87 local-family cases pass**, plus
one real Tk editor case (the retained initial headless run's five skips were
not claimed as UI proof; the focused editor case was rerun with the available
Tcl/Tk runtime). Structural verification is green for 1050 admitted profiles;
all six maintained structural tests pass. The combined modular/construction/
promotion/catalogue run reported **1125 passed, 8 failed**: four newly required
Fear fixture inputs, the old execution count, and three inherited catalogue
expectations (named versus band-specific skills, listing identities, optional
characteristics). These were repaired without weakening the engine contract;
the six affected modules then pass together (**126 passed**). The unchanged
construction/promotion remainder was not run again after test-only repairs.
The editor/workbook/documentation closing gate passes (**4 passed**); an
existing workbook round-trip now preserves the acquired Fear fact and the
opponent's explicit Leadership. Canonical source/recipient checks preserve
73 edited rule/skill document spans; changed staging rows and the Chainsaw
item match the KB, and six affected catalogue schemas validate. Generator
freshness and diff whitespace checks pass. Current-source semantic pin and
optimized parity certification remain L21/T14, with no fresh claim of either.

## L10 continuation — individual Cold-Blooded tests

Implemented on 2026-10-04 within the 1v1 scope: three canonical clauses,
152 cumulative clause milestones. [Lizardmen](https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf)
(PDF p. 1; both classic and `lizardmen-lus` records) use the lowest two of three
D6 in individual Psychology tests. [Fimir](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Lords%20Of%20The%20Marsh.pdf)
(PDF p. 1 / source printed p. 2) use them in individual Leadership tests.

The existing resolver carries the benefit; Fear explicitly identifies its
test as Psychology. Crude Belch remains ordinary Leadership: two dice for
Lizardmen, three for Fimir. Existing `.0`/`.1` request keys are retained; only
an applicable benefit requests `.2`. Equality passes and exactly one highest
die is discarded. Unknown Leadership fails before dice; automatic pass uses
none. Borrowed Leadership does not transfer/remove the tested model's dice
benefit. The passive implementation uses the beneficial procedure whenever
applicable, without adding a decision to decline it.

The canonical bindings, two 2B mirrors, mechanics and consumer/family registers
are connected. The conditions summary now has correct EN/ES wording and actual
source references. Two automatic-grant trace rows retain their origin keys.
Original rule prose is unchanged; Lizardmen's warband Rout/provider restriction
is explicitly `scope: NO`, not deferred group work. Separate Trollheim and
hireling records are unchanged.

Six cases were added to the existing family module: canonical Fear charge
pass/equality/failure and exact die selection, actual Crude Belch variant
contrast, unknown Leadership and automatic-pass precedence. Initial fixtures
used the wrong Great Crest Leadership (6 instead of the printed 7) and omitted
an explicit player-turn owner; those fixture errors were corrected without
source edits. Family plus Crude Belch: **114 passed in 23.04 s**. Existing
catalogue traversal plus structural snapshot: **2 passed in 27.49 s**.
Structural CLI: no errors, 1050 profiles. Snapshot: 220 execution / 217 projected
mechanisms, 191 canonical bindings, 646 implemented band records, 89 tag consumers.
Four affected catalogue schemas, source-field preservation and two mirror
checks pass. No new specification/mutation/review battery or integral,
semantic, parity or coverage run. Evidence: `build/cache/t13-parallel/cold-blooded/`.

Future individual Psychology callers must supply the same explicit test
classification; their actions are not delivered here. F070 retains the separate
Craven/Mystic Mist individual exception. L10/L11 remain partial. Optimized guards
refuse unported variants until L19/L20; no group simulator or source-pin refresh.

## L10 continuation — individual Cold-Blooded tests

Implemented on 2026-10-04 within the reaffirmed 1v1 boundary. Three more
canonical clauses bring this continuation to 152 clause milestones.

| Canonical clause | Source and individual behavior |
| --- | --- |
| `lizardmen/band--cold-blooded`, `lizardmen-lus/band--cold-blooded` | [Lizardmen PDF](https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf), PDF p. 1, and [classic source](https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen). Individual Psychology tests use the lowest two of three D6; other individual Leadership tests retain two D6. |
| `lords-of-the-marsh-mim/band--cold-blooded` | [Lords of the Marsh PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Lords%20Of%20The%20Marsh.pdf), PDF p. 1 / source printed p. 2. Individual Leadership tests use the lowest two of three D6, including Crude Belch. |

The existing Leadership resolver now accepts the three-dice benefit; the local
consumer selects its exact source variant. Fear explicitly identifies its
test as Psychology. Crude Belch remains an ordinary Leadership test, so the
Lizardmen benefit does not silently widen to it. Requests remain `<key>.0`
and `<key>.1`, adding `<key>.2` only when applicable. Equality passes; repeated
highest values discard exactly one die. Unknown Leadership is refused before
requesting dice, and an automatic pass consumes none. Borrowing a leader's
threshold does not transfer or remove the tested duelist's dice benefit.
The passive implementation uses the beneficial three-dice procedure whenever
applicable; it adds no separate decision to decline that benefit.

Canonical runtime bindings, two 2B mirrors, mechanics, consumer declarations
and the shared-family register are connected. The conditions summary's wrong
two-dice wording is corrected in both locales with actual source references.
The two affected automatic-grant trace rows retain their historical origin
keys. Complete original rule text is preserved: Lizardmen warband Rout and the
Saurus/Kroxigor provider restriction are explicitly `scope: NO`, not pending
group machinery. Trollheim's separate record and hireling records are unchanged.

Six cases were added to the existing family module: both canonical Lizardmen
records, pass/equality/failure and die selection through a real Fear charge;
the Fimir/Lizardmen contrast through real Crude Belch; and unknown-value/
automatic-pass precedence. Initial fixtures misstated Great Crest Leadership
as 6 instead of its printed 7 and omitted an explicit player-turn owner; these
fixture mistakes were corrected without source changes. The family and Crude
Belch modules pass together: **114 passed in 23.04 s**. Maintained catalogue
traversal and structural snapshot: **2 passed in 27.49 s**. Structural CLI has
no errors and 1050 compiled profiles. Snapshot: 220 execution / 217 projected
mechanisms, 191 canonical bindings, 646 implemented band records, 89 tag consumers.
Four affected catalogue schemas, source-field preservation and changed mirror
rows pass. No per-rule specification/mutation/review suite or integral,
semantic, parity or coverage battery was added/run. Evidence and entry copies:
`build/cache/t13-parallel/cold-blooded/`.

Future admitted individual Psychology callers (for example Stupidity) must use
the same explicit classification; their actions are not implemented by this
lot. F070 records Lords of the Marsh's Craven/Mystic Mist individual exception,
separate from the delivered dice selection. L10/L11 remain partial. Optimized
guards refuse these variants until L19/L20; no optimized implementation,
source-pin refresh or group simulator was added.


## L11 continuation — Craven in the normal duel

Three canonical clauses bring the cumulative milestone count to 155: Lords of
the Marsh Draich, Young Nobles and Shearls now carry `mechanic.craven`.
The [printed source](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Lords%20Of%20The%20Marsh.pdf)
subjects them to Fear even when they cause Fear themselves. The existing Fear
predicate now applies this exception, retaining ordinary causes-Fear immunity
and the existing Frenzy exemption. Cold-Blooded still uses the lowest two of
3D6. Charge failure prevents contact; failure when receiving a charge requires
natural sixes to hit in that round.

Original source prose is preserved. Mystic Mist protection has a separate
unimplemented effect explicitly excluded by the map/weather scope decision;
there is no environmental toggle. At this milestone, individual Stupidity for Young Nobles and
Shearls remains pending under F070. Three automatic-grant origin rows record
this split. Optimized entry refuses Craven until L19/L20; L11 remains partial.

Seven cases added to the existing local-modifier family cover all recipients,
acquired Fear, charge failure, received-charge pass/failure and ordinary
immunity/non-Fear controls through strict dice/decision tapes. The family
module passes **100 cases**; maintained structural snapshot and catalogue
traversal pass **2 cases**. Three affected catalogue schemas, source-field
preservation and exact changed staging mirrors pass. Evidence is retained in
`build/cache/t13-parallel/craven/`. No broad certification suite was added.


## L11 continuation — Individual Stupidity

Three Lords of the Marsh clauses (Young Nobles, Shearls and Fimir Warriors)
bring the cumulative milestone count to 158. `mechanic.stupidity` reuses local
Leadership with `psychology=True`, including Fimir Cold-Blooded. At each own
player turn it refreshes a persistent failure flag. Failure suppresses the
warrior's attack events, including replacement and bonus attacks, through the
enemy turn; success clears it on the next own turn. Enemy hit rolls still use
the normal standing defender. The existing Frenzy exemption takes precedence.
An initial failed test cancels the active warrior's voluntary charge; a duel
without resulting contact returns unresolved, with no invented winner.

Source: [Mordheim Living Rulebook, printed page 23, Stupidity](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf)
and the existing Lords of the Marsh profile citations. Canonical source prose
is unchanged and the three changed runtime records match their staging copies.
Random board movement and Mystic Mist protection are explicitly excluded.
The initial receiving duelist starts without an earlier failed-test history;
that limitation, other canonical grants and supplied condition access are
tracked in F071. There is no assertion that all Stupidity sources are connected.

Five cases added to the existing family prove all three canonical recipients,
charge cancellation, failure persistence through the enemy turn, normal enemy
hit targets, restoration after a successful Cold-Blooded test and Frenzy's
zero-dice exemption. The initial family run passed 104 cases with one fixture
ordering error; corrected Initiative ordering passes the focused 12 Stupidity/
Craven cases (93 unaffected cases were not repeated). Affected catalogue and
structural gates pass **2 cases**; documentation passes **1 case**. Evidence and source entry copies are in
`build/cache/t13-parallel/stupidity/`. No per-rule spec, mutation or review
battery was introduced; optimized support remains explicitly refused until
L19/L20. L11 and the modular implementation remain incomplete.


## L11 continuation — Canonical Troll Stupidity grants

Six additional profile grants now use the existing Stupidity operator: Trolls
in Black Orcs, Night Goblins (Karak Azgal, MIC and Web), Orc Mob, and the
Underworld Alliance Warpstone Troll. The cumulative milestone count is 164.
No new combat operator or context field is required. Original source fields
and recipient lists are preserved; the two existing staging mirrors match.
Two T13 automatic-grant origin rows are updated; the four original-band grants
are outside that 2A/2B origin register.

All six resolve `shared-rule.stupidity-2`, the unconditional Troll clause.
References: [Orc Mob / Troll](https://mordheimer.net/docs/warbands/grade-1a-warbands/orc-mob)
and [Underworld Alliance / Warpstone Troll](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Underworld%20Alliance.pdf),
plus each unchanged canonical row's source citation. This is distinct from
`shared-rule.stupidity`, which includes a nearby Skaven-Hero exemption.
Crooked Moon's Troll and Mazzalupo's Black Sheep currently reference that
Rat-Ogre text; this milestone deferred them to F071, resolved in the closure below.
The five Rat-Ogre grants and Dark Elf Beastmaster-specific Leadership route
also remain pending; no generic nearby-Hero immunity is invented.

Four new cases in the existing family prove all six recipient/control pairs
and three real-round failures. Strict empty decision tapes verify that a failed
Troll cannot bypass suppression by selecting Vomit Attack. Existing Vomit
witnesses now explicitly supply successful Stupidity dice when the active
canonical Troll requires them. Random board movement remains excluded.
Evidence and runtime-entry backups: `build/cache/t13-parallel/troll-stupidity/`.
The initial-history/acquired-condition limits recorded here were subsequently resolved by the Stupidity closure below; no optimized port,
source-pin refresh or broad semantic/parity/coverage suite is included.

Validation of this continuation: **4 new family cases**, **16 existing Vomit
cases**, **1 structural snapshot** and **1 documentation case** pass. The
Warpstone failure witness explicitly selects the canonical optional Vomit
binding; its final focused re-run also passes without consuming that choice.
No unaffected family or broader engine suite was repeated.

## L11 closure — Stupidity in the supported duel

The individual effect now has an end-to-end construction, modular and editor
route. Twelve further static canonical grants bring the Stupidity family to
21: five Rat-Ogre variants, Crooked Moon Troll, Black Sheep, Cold One Beasthounds,
Brood of Ghurash Trolls, both Forest Goblin giant spiders and the Kislev bear.
Baneworms do not receive Brood Mentality. The cumulative delivery count is 176
canonical clause milestones; family memberships are not additional deliveries.

The editor accepts acquired Stupidity, a qualified exemption already active,
a prior failed test, the eligible handler's own Leadership within 6 inches and
an already-active Brood Mentality bonus. Acquired Stupidity adds the condition;
unchecking it does not remove an innate grant. Prior failure persists during
the opposing turn and is refreshed on the fighter's first own turn. Head Injury
result 6 uses the same operator. Frenzy and an active exemption prevent the test.

Cold One Beasthounds may use only their own Leadership or their Beastmaster's
basic Leadership, never ordinary Leader borrowing or a recursively borrowed
value. The bear likewise uses its qualified Bear Tamer. Brood's supplied bonus
affects only Stupidity. Helpers, group membership and proximity are qualified
input facts, not independently simulated fighters or group lifecycles.

Source reconciliation resolves Q006/Q025: Black Sheep use the printed
Sheepherder exemption rather than shared Rat-Ogre prose; Crooked Moon uses
standard Troll Stupidity (`shared-rule.stupidity-2`). Its source URL is corrected
to the actual campaign PDF; printed page remains 0 (unknown), not guessed.
Moulder's exemption explicitly requires a Clan Moulder Hero. Existing staging
mirrors are synchronized. The two distinct shared Stupidity records are retained.
Sources: [Mazzalupo](https://mordheimer.net/docs/warbands/grade-2a-warbands/mazzalupo),
[Clan Moulder](https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder),
[Dark Elves](https://mordheimer.net/docs/warbands/grade-1b-warbands/dark-elves),
[Death Under the Eight Peaks](https://broheim.net/downloads/campaigns/karakeightpeaks/Death%20Under%20The%20Eight%20Peaks.pdf)
and [Brood of Ghurash](https://broheim.net/downloads/warbands/supplement/sealedcity/Brood%20Of%20Ghurash.pdf).

Seven new cases extend the existing family suite; one real Tk editor case checks
round-trip construction. The affected family plus Vomit suites pass (132 cases),
as do the structural snapshot and execution-pipeline checks (2 cases), changed
runtime contracts, mirrors and three catalogue schemas. Structural snapshots now
record 224 execution contracts, 221 projected, 195 observable bindings, 670
implemented records and 93 modular tag consumers. Evidence is under
`build/cache/t13-parallel/stupidity-completion/`.

F071 is resolved for this individual effect and its static grants. Random
Drunkenness, Fungus and Goading producers retain their own compound-rule work
under L13/L09; they do not reopen the base operator. Board movement, weather,
rider/group lifecycles and campaign progression remain excluded. L21/T14 owns
inventory/source-pin reconciliation; no semantic pins were refreshed here.
No optimized port or broad certification gate was run.

## L11 continuation — Static Frenzy and unrestricted Hatred

Four previously deferred static grants now activate the existing Frenzy contract:
Adventurer Barbarian, Khorne Cannibal Boys, Mousillon Plague Priest and Plague
Champion. Their source-specific recipient filters remain unchanged. They compile
through automatic trait bindings; the modular pool doubles base attacks, preserves
the separately added off-hand attack, skips Fear/Stupidity while Frenzy is active
and loses Frenzy after knockdown/stun. The existing operators are reused without
new engine branches. Compulsory movement/charge range/target choice on a board is
explicitly excluded; original source prose is preserved. Changed rule rows match their existing 2B mirrors.

Sons of Hashut's selectable Unlimited Hatred now binds `skill.hatred` for its three
published eligible Hero profiles. Unlimited refers to enemy eligibility, not
unlimited duration: missed hits reroll in the first combat turn only. Selection
absence and a foreign in-band recipient remain controls. Shared construction and
the existing product option route supply the selection; no duplicate legality rule
or additional editor switch is introduced.

Sources: [Karak Azgal, Barbarian](https://broheim.net/downloads/campaigns/karakazgal/Karak%20Azgal.pdf),
[Khorne Raiders, Cannibal Boys](https://broheim.net/downloads/warbands/supplement/sartosa/Khorne%20Raiders.pdf),
[Mousillon Clan Pestilens, Priest/Champions](https://broheim.net/downloads/warbands/supplement/mousillon/Skaven%20of%20Clan%20Pestilens.pdf)
and [Sons of Hashut, Unlimited Hatred](https://mordheimer.net/docs/warbands/grade-1c-warbands/sons-of-hashut).

Six cases extend the existing family module: four canonical grants with absence
controls, real round attack counts and injury-driven Frenzy loss; two real attacks
contrast first/later-turn Hatred rerolls. The cumulative milestone count is 181.
Existing family tests and the structural snapshot are the bounded validation set.
L11 remains in progress for opponent-specific Hatred and compound condition
producers; this lot does not claim those effects implemented. L21 owns historical
origin/pin reconciliation; optimized ports remain L19/L20. No pins are refreshed.

Validation for this block: the existing combat family module passes all 122 cases
(including six new cases); the updated structural snapshot and documentation
checks pass (2 cases). Four changed canonical documents validate against the
maintained schema and changed rows match existing staging mirrors. Family counts
reconcile to 78 families/238 memberships; structural bindings are 196 and
implemented records 675. The generator was rerun; no whole semantic/parity,
coverage, UI sweep or optimized test battery was added.

## L11 continuation — Opposed Elven Hatred

Six canonical clauses now use first-combat-turn, opponent-qualified Hatred:
Adventurer Elf, Shadow Warriors, Athel Loren Wood Elves and Lothern Sea Rangers
hate Dark Elf individuals; Dark Elves and Druchii hate High Elf individuals.
Original source prose is preserved. Dark/Druchii band grants now explicitly
exclude Cold One Beasthounds and Slavehounds by recipient, rather than applying
an Elf's racial hatred to every member of the roster. Other Lothern profiles
do not acquire the Sea Ranger's rule.

`combat_traits.elf_kind` is an explicit individual fact (`high`, `dark`, `other`).
Canonical Elf profiles carry the qualified identity; animals do not. Athel Loren
Wood Elves are `other`, not High Elves. Shadow Warriors are High Elves, despite
their separate band name. Lothern Raw Recruits have no fixed identity: their
source admits High Elves, half-breeds and captured Humans. The editor's localized
identity choice keeps canonical identity by default and permits a supplied
individual override, including neither High nor Dark Elf. Missing mixed/free
identity is not inferred from the band, name, characteristics or employer;
configure the specific recruit when its identity is known.

The predicate checks the enemy's individual tag, not a band substring. It reuses
all normal attack consumers, including prepared pools and bonus attacks, through
`_hit_reroll`; later turns receive no Hatred reroll. There is no new group state,
constructor, hiring/campaign route or optimized port. The source's High Elf Hired
Sword opponent clause can be represented by a supplied individual identity;
this does not claim a named hireling catalogue participant route (F036–F038).

Sources: [Dark Elves](https://mordheimer.net/docs/warbands/grade-1b-warbands/dark-elves),
[Druchii](https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii),
[Shadow Warriors](https://mordheimer.net/docs/warbands/grade-1b-warbands/shadow-warriors),
[Wood Elves](https://mordheimer.net/docs/warbands/grade-2a-warbands/wood-elves-of-athel-loren),
[Karak Azgal](https://broheim.net/downloads/campaigns/karakazgal/Karak%20Azgal.pdf)
and [Lothern Sea Patrol](https://broheim.net/downloads/warbands/supplement/sartosa/Lothern%20Sea%20Patrol.pdf).
The Lothern source specifically describes Sea Rangers as Shadow Warriors and
Raw Recruits as mixed backgrounds; it prevents a band-wide racial inference.

Seven cases extend the existing family suite: six canonical real-attack scenarios
check matching identity, animal/nonmatching controls and later turns; one checks
recipients, mixed identity and invalid input. One real Tk case round-trips the
profile default and explicit overrides. The existing family module passes all
129 cases; structural snapshot, trait/schema registry and execution-pipeline
checks pass (3 cases); the Tk case passes. Thirteen affected band documents and
three catalogues validate. The generator is rerun and checked for freshness.
Structural counts: 226 execution mechanisms, 223 projected, 198 observable
bindings, 95 modular tag consumers and 681 implemented records. Family counts:
80 families, 244 memberships. Four historical automatic-origin rows are updated;
original source-origin identities are retained.

The cumulative milestone count is 187. Other race/affiliation-specific Hatred and
compound condition producers remain in L11/L13. L21/F001 must reconcile affected
profile/rule source fingerprints and historical origin snapshots; no semantic pin
is refreshed or old error count asserted in this lot. L19/L20 owns optimized ports.

## L10/L11 continuation — Leadership rerolls and Fear immunity

Six source clauses now execute through the existing individual Leadership path:
Battle Pilgrims' Stubborn, Dwarf Longbeards' Stubborn, Barbarian Courage for both
Norse variants, Beastmen Fearless and Sylvania Vampire Hunters' Iron Will.
The cumulative milestone count is 193; these are admitted individual effects.

The source variants stay distinct. Battle Pilgrims must reroll a failed individual
Leadership test; Longbeards may choose a reroll. Barbarian Courage permits a
failed Fear reroll, not a reroll of every Psychology test. A successful first roll
consumes no choice or extra dice. An optional refusal retains the failure.
The second result is final even if it fails: combined grants do not produce a
third test. The chosen threshold and full dice convention are reused, including
Cold-Blooded's lowest two of three. Leader borrowing is resolved once before the
first roll, not renegotiated for the reroll. No extra mutable resource is needed.

Fearless and Iron Will skip Fear dice and do not grant general Leadership or
Stupidity immunity. Iron Will's published recipients are Vampire Hunters and
Slayers; the Priest of Morr can choose only the explicitly permitted other special
skills. Its shared availability now carries that recipient restriction, with a
negative canonical construction control. Standard skill selection supplies all
four selectable origins; innate Stubborn needs no new editor input or constructor.

All Alone clauses of Fearless/Barbarian Courage are preserved in the source and
explicitly excluded from the 1v1 runtime. Rout and group mechanics are not added.
Sources: [Battle Pilgrims](https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard),
[Longbeards](https://mordheimer.net/docs/warbands/grade-1b-warbands/dwarf-rangers),
[Norse Barbarian Courage](https://mordheimer.net/docs/warbands/grade-1b-warbands/norse),
[Beastmen Fearless](https://mordheimer.net/docs/warbands/grade-1a-warbands/beastmen-raiders)
and [Sylvania Iron Will and recipients](https://mordheimer.net/docs/warbands/grade-2a-warbands/vampire-hunters-of-sylvania).

Six cases extend the existing combat family, using canonical construction and
real charged-Fear rounds, then bounded individual-test checks for accepted/declined
rerolls, final failure, initial success, Cold-Blooded and unrelated Stupidity.
The full existing family module passes 135 cases. Structural snapshot, execution
pipeline and the existing selectable partition/availability checks pass (4 cases).
Six changed canonical documents and three catalogues validate; original source
prose/references/other rows are unchanged against guarded entry copies. Changed
staging rows match their canonical counterparts. The Iron Will historical origin
and maintained partition table now record implementation instead of refusal.

Counts reconcile to 84 families/250 memberships, 230 execution mechanisms,
227 projected, 202 observable bindings, 99 modular tag consumers and 687
implemented records. Generated knowledge is refreshed. L21/F001 owns source-pin
and historical inventory reconciliation; no pins or old semantic error totals
are refreshed here. Other individual Psychology/Leadership effects remain pending.
The new effects explicitly refuse unported optimized execution; L19/L20 remains
untouched. No full semantic/parity, coverage, UI sweep or new test layer is added.


## L10/L11 continuation — explicit automatic Leadership grants

Four further canonical clauses now use the existing `mechanic.automatic-leadership`
operator: Carnival of Chaos Plague Bearers, Nurglings and Plague Cart, and Khorne
Raiders Madbrains. Their printed effects explicitly pass any Leadership-based
test; this is broader than ordinary Psychology immunity or Fear immunity. Source
prose, translations and recipient lists are preserved. Madbrains' prohibition
on promotion to Leader is retained as a separate campaign-only excluded clause.
The existing Khorne 2B mirror is updated with its canonical runtime.

Canonical construction grants the existing modular operator. It passes individual
Fear, Stupidity and other Leadership callers without dice, reroll decisions or a
borrowed Leader, including an unknown base Leadership. It does not remove Hatred
or Frenzy merely because the source name says Psychology immunity. Ordinary
Psychology immunity remains a separate unfinished family. Group tests, map rules
and optimized ports remain outside this delivery; no engine code was duplicated.

Validation is limited to four new parametrized cases in the maintained local
family module, the affected structural snapshot and documentation links, plus
normal generated-publication freshness. Cumulative milestones: 197; family
memberships: 254 (84 families); implemented rule records: 691. Existing mechanics,
observable bindings and consumer counts are unchanged. Source-pin reconciliation
for these runtime transitions remains with F001/L21; no pins are refreshed here.

References: canonical `special-rules.yaml` in `carnival-of-chaos` and
`khorne-raiders-sar`; `modular/leadership.py`; the existing Darksouls Crazed
binding; `implemented-canonical-families.yaml` automatic-Leadership family.


Observed validation: four new family cases pass (135 unrelated cases deselected);
the current structural snapshot and documentation-links check pass (2 tests).
`git diff --check` passes. Fixture setup initially omitted explicit charge facts
and then their player-turn owner; those fixture errors were corrected without
changing production logic. Generated knowledge was rebuilt through its maintained
generator. No full semantic, parity, coverage or optimized-engine suite was run.


## L10/L11 continuation — ordinary Psychology immunity

39 canonical grants in 11 bands share `mechanic.psychology-immunity`. The
canonical condition `condition.immune-to-psychology` supplies the governing
contract: ignore Psychology, including Fear, Stupidity, Hatred and Frenzy.
Shared prose variants `shared-rule.immune-to-psychology` and
`shared-rule.immune-to-psychology-4` retain their complete source text.

Initialization suppresses Frenzy and any supplied previous Stupidity failure.
Individual Psychology callers consume no test dice or Leadership-provider choices.
Fear consequences are skipped. Attack contexts suppress general and opposed
Hatred, preserving unrelated weapon/skill hit rerolls. Non-Psychology Leadership
still uses the normal test: this is not the broader automatic-Leadership operator.
No departure, All Alone, group psychology, terrain or compulsory map movement is
introduced. Conditional immunity producers remain separate source-specific rules.

The 39 origins are enumerated by the maintained Psychology-immunity family in
`implemented-canonical-families.yaml`. Canonical recipients are preserved except
for Tomb Guardians' band clause, explicitly restricted to its five profiles with
the printed Undead rule; its Living Tomb Scorpion receives no immunity. Existing
2A/2B mirrors are updated for these owned runtime records. Source prose and
translations are unchanged. Existing historical automatic-register identities
are retained and their status updated with an explicit family-witness limit.

Three added family cases cover two different canonical source routes, acquired
Stupidity/previous failure plus Frenzy/Hatred conflicts, unknown Leadership,
non-Psychology rejection, independent rerolls and the Living recipient control.
Affected editorial schemas and the current structural snapshot pass. The new
snapshot is 85 families/293 memberships, 231 execution mechanisms, 228 projected,
203 observable bindings, 100 modular tag consumers and 730 implemented records.
Cumulative delivered clause milestones: 236. No optimized implementation or full
semantic/parity/coverage certification is included. F001/L21 owns exact source-pin
reconciliation; no pins are refreshed during this implementation.

References: `sources/knowledge/catalog/rules/conditions.yaml`, shared-rule catalogue,
the 11 canonical band packages listed in the family register, and modular
`state.py`, `psychology.py`, `leadership.py`, `contexts.py`.


Observed bounded validation: local family suite 142 passed (three new cases);
structural snapshot 1 passed; documentation 1 passed; affected canonical/catalogue
schemas pass; `git diff --check` passes. The maintained web knowledge generator
was run for the promoted runtime data. Historical register: 29 existing rows
updated, no origin identity added or removed. An initial file write was rejected
by the filesystem; the continuation resumed only the affected grants and completed
the remaining canonical/mirror writes. No user work was reverted.


## L10/L11 continuation — remaining direct Hatred and automatic Leadership

Order of the Mare Pilgrims' printed Hatred of every enemy now grants existing
`skill.hatred` innately: failed hits reroll in the first combat round only, and
ordinary Psychology immunity suppresses this benefit. Other Order profiles do
not receive the grant. The existing 2A mirror retains the same runtime.

Marauders of Chaos Spawn's Psychology clause explicitly passes all Leadership
checks, and now grants existing `mechanic.automatic-leadership`. Its separately
implemented random preparation and per-phase Special Attacks remain unchanged.
Unknown base Leadership requires neither dice nor Leader/reroll choices. Other
Marauders do not receive the grant. This clause is broader than ordinary immunity
and does not silently acquire its Hatred/Frenzy suppression semantics.

Both source effects, translations and recipients are preserved. No new operator,
field or product input is required: normal canonical selection carries the innate
effects. Four focused cases cover timing/immunity/recipient controls and Spawn
preparation without unwanted test dice. Affected structural and editorial-schema
checks pass. Counts: 238 cumulative clause milestones, 85 families/295 memberships
and 732 implemented records; execution and consumer counts remain unchanged.
Specific-enemy Hatred (greenskins, Skaven, other vampire bloodlines) still needs
source-qualified opponent/variant identities; these rules are not activated by
name or by the entire opponent's band. F001/L21 retains exact source-pin review;
optimized ports remain L19/L20. No general certification gate was run.

References: `order-of-the-mare-web/special-rules.yaml` Pilgrims Hatred;
`marauders-of-chaos/special-rules.yaml` Spawn Psychology;
`implemented-canonical-families.yaml` Hatred/automatic-Leadership families;
modular `contexts.py`, `leadership.py`, `rounds.py` Special Attacks.


Observed validation: four focused family cases passed (142 unrelated cases
left deselected), current structural snapshot 1 passed, documentation links
1 passed, affected editorial schemas passed and `git diff --check` passed.
The initial Spawn control named a nonexistent Chieftain id; corrected to the
canonical `marauder-chieftain` before the passing run. Source edits were checked
structurally to preserve all non-runtime leaves, and the web knowledge generator
was rerun. No full family, semantics, parity or coverage run was needed here.


## L07 continuation — remaining innate injury defences

Ten canonical records now supply eleven individual clauses through existing
operators, without new engine fields or algorithms:

- No Pain (`skill.ignore-pain`): Ghost Pirates Skeleton Mates and Gibbets;
  Necrarchs (Mousillon) Nosferatu, Abomination, Defiled and Skeleton;
  Metal Mongers Machine Ogre. Stunned becomes knocked down after the normal
  injury chart; out of action is unchanged.
- Hard Head (`trait.concussion-immune`): Black Dwarfs, excluding Informers;
  Guild of Disgraced Engineers. The ordinary injury chart remains active;
  only clubs/maces' concussion transformation is ignored.
- Slayer Pirates' compound rule: Hard to Kill plus Hard Head, for the six
  Slayer profiles, excluding Thaggi. The printed chart is 1–2 knocked down,
  3–5 stunned, 6 out of action. Grudgebearers' Elven-hireling restriction is
  retained as a separate campaign-only clause, not a duel effect.

Canonical and existing staging mirrors preserve printed effects/translations.
Black Dwarfs' explicit Informer exception and Slayer Pirates' Slayer-only wording
now have recipient lists. No Pain/Squishy for the Bloated remain blocked by
existing T13-Q037: the same source expressly says both stunned-to-knocked-down
and the opposite. This delivery does not invent precedence. Its two historical
register rows now state the real blocker rather than generic pending status.

Four focused cases cover all seven No Pain grants, injury transformations and
out-of-action control, both Hard Head routes with normal-stun and Informer
controls, and Slayer Pirates' full chart plus Thaggi exclusion. Existing operators
also retain their existing support in other engines; no optimized implementation
was started. Source-pin reconciliation remains F001/L21.

Current totals: 249 delivered clause milestones, 742 implemented rule records,
88 canonical families/306 memberships (42 compiler, 39 mechanic, 7 trait).
The family header had remained stale after earlier runtime additions; it is now
reconciled against the actual rows. Execution, observable binding and consumer
counts are unchanged. References: the six canonical band `special-rules.yaml`
files; existing `skill.ignore-pain`, `skill.hard-to-kill` and
`trait.concussion-immune`; modular injury contexts and `phases.injury_condition`.


Observed bounded validation: four new family cases passed (146 unrelated cases
deselected); structural snapshot 1 passed; documentation 1 passed; six affected
band schemas and the canonical-family schema passed; `git diff --check` passed.
Nine existing automatic-register rows were updated, plus the two Q037 blocked
rows; no origin key was added or removed. Initial injury tapes used wound face 6,
which correctly requested a critical die; changed to noncritical wound face 5
so the cases isolate the injury defences. No production behavior was altered to
satisfy those fixture errors. The maintained knowledge generator was rerun.


## Q037 resolved — Squishy overrides No Pain

The user accepted Squishy as the specific exception on 2026-10-04. The Bloated
keeps stunned results even when an inherited contribution grants No Pain. Both
printed clauses/translations remain intact; No Pain is marked overridden, and
Squishy now has an executable canonical binding and modular consumer. This
supersedes the earlier Q037 blocked status. One new family case exercises the
real attack/injury path with both effects; existing No Pain witnesses remain.
Optimized engines explicitly refuse the new exception until its normal ports.
Structural totals: 232 execution, 229 projected, 204 observable bindings, 101 tag
consumers and 743 implemented records; 89 families/307 memberships. F001/L21 owns
pin integration. See [permanent ruling](../../../decisions/design-rulings.md#bloated-squishy-overrides-no-pain--q037--2026-10-04).


## Q128/Q013/F005 — accepted contracts implemented

The user's 2026-10-04 rulings are implemented in the modular duel. The printed
source prose and translations remain unchanged; see
[permanent rulings](../../../decisions/design-rulings.md).

- **Sea Dragon Cloak (Q128):** occupies the armour choice, grants a normal 5+
  melee armour save, and combines with a shield (4+) and helmet normally. It
  cannot combine with another suit; armour prohibitions apply. The existing
  `defence.sea-dragon-cloak` identifier is retained for compatibility. Shared
  eligibility enforces the role for both neutral construction and Combat Lab
  facts; the compiler applies the armour base before shield modifiers.
- **Curse of the Revenant (Q013/F013):** an acquired Strigoi special skill,
  requiring Great Thirster. A dedicated modular operator attempts to recover
  one lost wound on 5+ at the beginning of the owner's turn, before engagement
  handling. Fire does not prevent it; full health and Out of Action generate
  no roll, and repeating the same turn cannot grant another attempt. The old
  generic regeneration binding is removed, avoiding a wound-time save.
- **Great Thirster:** its prerequisite is fully executable, rather than an
  access-only marker. Taking the enemy Out of Action grants Frenzy after
  immediate rescue/reactions; Knocked Down/Stunned/Out of Action clears it
  through the existing injury operator. Its specific conditional Frenzy
  overrides the vampire's general psychology immunity for this effect.
- **Shifty plus pistols (F005):** pistol-only loadouts now receive a separate
  Shifty contribution and the existing ordinary pistol contribution. A single
  pistol and a brace both work; differing pistols use the nomination decision.
  Mixed melee/pistol loadouts retain melee nomination. Existing first-round
  pistol availability and later-round equipment handling remain in force.
  This completes the F005 allocation ruling, not all F026/Q151 pistol work.

Implementation references: `eligibility/index.ts` (shared prerequisites and
armour composition), `compiler.py` (armour projection), modular `rounds.py`
(turn-start recovery and nomination), `aftermath.py` (recovery and conditional
Frenzy), and the Strigoi canonical special rules plus their existing 2A mirror.
New effects are registered in `execution.yaml`, `close-combat.yaml` and the
canonical-family register. Optimized engines explicitly reject the new recovery
and conditional-Frenzy tags until their normal ports; no port was started.

Bounded validation: three maintained family cases passed; four pistol-focused
cases passed; shared construction context suite 25 passed; structural snapshot
1 passed; workspace typechecks and eligibility bundle freshness passed. An
additional real injury assertion checks loss of Great Thirster's Frenzy.
No full semantic/parity/coverage run is required by this functional lot.
Source-pin reconciliation remains F001/L21; broad certification remains T14.
Structural totals: 234 execution entries, 231 projected, 206 observable
bindings, 103 modular tag consumers, 744 implemented records; 91 canonical
families / 309 memberships (42 compiler, 42 mechanic, 7 trait).

Final publication check: the maintained knowledge generator and its `--check` passed; five affected editorial schemas passed; documentation links passed; `git diff --check` passed. The documentation test is `tests/python/architecture/test_documentation.py` (an initial obsolete-path invocation collected no tests and was corrected). No commit or push was made.


## L08/L09/L11 — self Sermon and Frantic priority

Delivered 2026-10-04, modular only. Two local attack contributions are now
connected to canonical selection/compilation and execution:

- **Rousing Sermon**, Protectorate of Sigmar: only the Warrior Priest can
  acquire it. At the beginning of his own turn he may declare it, receiving
  +1 Attack in that turn's combat phase, once per duel. The persistent state
  spends the resource; the attack modifier is a temporary fighter projection,
  so it expires on the next player turn and cannot accumulate or refresh.
  Re-entering the same phase reuses the active declaration without consuming
  another decision. Normal weapon attack-count restrictions still apply.
  The source's other friendly models and six-inch aura are outside the 1v1
  product boundary; no group or spatial subsystem was added.
- **Frantic**, Crooked Moon Fanatics: the innate rule now has an executable
  binding. Its priority operator ignores weapon penalties and ordinary
  Initiative, including the normal standing-up priority penalty. Other
  profiles receive no contribution. The existing legacy compiler contract
  for same-named rules in other bands is preserved; this source-specific
  operator does not depend on its numerical bonus or add it twice.

Sources: canonical Protectorate
`band--special-skill-rousing-sermon` and Crooked Moon `fanatics--frantic`,
including their printed source references and unchanged EN/ES prose. Existing
2A/2B mirrors were updated. Runtime bindings, execution descriptors, catalogue
descriptions, canonical families and consumer registry stay aligned.

Implementation: modular `rounds.resolve_round` handles the optional own-turn
declaration/resource and temporary attack projection; `phases.resolve_priority`
handles Frantic after ordinary priority penalties. `kernel` rejects both new
tags in optimized engines until L19/L20; no port was started.

Bounded validation: three cases in the existing local-family test module:
Sermon on either duel side across three successive turns, wrong recipient
refusal, and Frantic's canonical activation/negative recipient, weapon/standing
penalties and a real round against a faster charging opponent. Structural
snapshot passed; seven affected editorial documents validated. Knowledge
publication and freshness, documentation links and whitespace checks were run.
No full semantics/parity/coverage or new test suite was added.

Snapshot: 236 execution, 233 projected, 208 observable/canonical bindings,
105 modular tag consumers, 746 implemented rule records, and 93 families /
311 memberships (42 compiler, 44 mechanic, 7 trait). These are structural
counts, not a claim that T13 or the modular implementation is complete.

Specific-enemy Hatred and Torturer remain with F064's exact opponent nature
facts: `undead_or_possessed` cannot distinguish Undead from Possessed, and is
absent on many canonical Undead. No substitute identity was inferred from
Fear, poison immunity, No Pain or whole-band membership. Complete the identity
contract in L11/L13, then implement all these consumers as one family. Source
pins remain F001/L21; none was refreshed in this lot.


## L10/L11 — Absolute Faith and Questing Vow

Delivered 2026-10-04, modular only. Absolute Faith now uses the existing optional
failed-Fear reroll operator for its published Sisters recipients. Its All Alone
clause stays outside 1v1. Questing Vow is an acquired Knightly skill, restricted
to the Questing Knight: it is not a default band-wide gift. The incorrect legacy
`grant: band` classification is replaced by `kind: warband_skill`, selectable
grant and explicit recipient metadata.

Questing Vow qualifies while charging, charged by or engaged with an opponent
that causes Fear against this particular warrior. The round projects the
existing Leadership-reroll tag temporarily, before Stupidity/Fear/other local
Leadership callers. It therefore permits one optional failed Leadership repeat,
not just a Fear repeat; ordinary opponents and absent contact/charge do not
qualify. General Psychology immunity and existing reroll/Cold-Blooded/leader
contracts remain unchanged. No group Rout flow is added.

Sources: Sisters `band--special-skills-absolute-faith` and Bretonnian Chapel
Guard `band--questing-vow`, including their published URLs, EN/ES texts and
recipient lists. Canonical runtime, existing staging mirrors, execution,
catalogue and family records are aligned. Only one new operator/tag is needed;
Absolute Faith reuses an existing operator. The optimized kernel rejects the
Questing tag pending its normal port.

Three focused cases in the maintained family module cover real failed-charge
Fear repeats for each skill, acquired/foreign-recipient controls, non-Fear
Leadership, a final failed repeat with no third roll, and ordinary/no-contact
opponent exclusions. Structural snapshot, affected editorial schemas, knowledge
generation/freshness, documentation and whitespace checks form the bounded
validation; no full semantics/parity/coverage suite is required here.

Structural snapshot: 237 execution, 234 projected, 209 observable/canonical
bindings, 106 modular tag consumers, 748 implemented records, and 94 canonical
families / 313 memberships (42 compiler, 45 mechanic, 7 trait). T13 remains in
progress. Ports belong to L19/L20 and source pins to F001/L21.

The user's scope correction excludes voluntary escape/withdrawal even when
expressible with two models: it ends the duel rather than resolving it. The
three Swashbuckler/Hit and Run records plus Jump Back, Leap of Faith and
Escapists are explicitly `scope: NO`, keeping printed texts intact. Their
map/interception/campaign clauses are also excluded. See
[permanent scope ruling](../../../decisions/design-rulings.md#voluntary-escape-does-not-belong-to-combat-lab--2026-10-04).


## L06/L07 — Iron Cage and Frustratingly Tiny

Delivered 2026-10-04. Two personal defences are fully connected to canonical
construction and real modular attacks, reusing existing EffectSet fields:

- **Gibbets' Iron Cage:** automatic normal 5+ armour, affected by Strength,
  not an extra natural/ward save. It remains part of the profile when the
  armour slot is empty and cannot be removed or replaced. A structured
  equipment restriction reserves the suit role: another suit or Sea Dragon
  Cloak is forbidden. The shared `armour-suit` token differs deliberately from
  `armour`, so it does not blanket-prohibit shields/helmets. It does not grant
  equipment absent from the Gibbet's canonical list. Loss/theft/transfers are
  campaign operations, outside Combat Lab.
- **Frustratingly Tiny:** an acquired skill for the three published Snotling
  hero recipients (BigSnotz, Scouts, Shaman), not an innate gift and not usable
  by the Bullied Goblin. Enemies receive -1 to melee hit. The shared
  prerequisite decision forbids combining Tiny and Big Bully in either
  selection order. Big Bully's advancement-time Strength-skill grant is not
  activated here. Hidden-detection changes remain explicitly outside 1v1.

Sources: `ghost-pirates-sar/gibbets--iron-cage` and
`snotlings-web/bullied-goblin--frustratingly-tiny`, with their printed source
URLs and unchanged EN/ES text. The misleading historical Tiny id remains
stable; published recipients and skill metadata carry its actual meaning.
Existing staging mirrors, execution descriptors and canonical families align.

No new combat resolver or mutable state was added. Iron Cage uses the existing
armour-save bonus during compilation; Tiny uses incoming-hit modifier in the
existing hit phase. Shared TypeScript owns both legal-construction decisions;
the embedded Python bundle was rebuilt by its maintained generator. These
fields already have engine operators: no vectorized/native implementation was
started, and this delivery makes no new parity/certification claim.

Bounded validation: three cases added to the maintained local-family module
cover Strength-modified real armour saves, profile/empty-slot persistence,
wrong-recipient and competing-armour refusal, and the exact Tiny hit boundary
with a canonical control. Two shared construction cases cover suit versus
shield/helmet and both Tiny/Big Bully selection orders (27 suite cases total).
Workspace typechecks, bundle freshness, affected editorial schemas, one
structural snapshot and maintained publication/docs/whitespace checks are the
closing gates. No new suite, full semantics/parity/coverage run or mutation
inventory was added.

Snapshot: 239 execution, 236 projected, 211 observable/canonical bindings,
106 modular tag consumers (unchanged: both descriptors use existing scalar
fields and empty tags), 750 implemented records, 96 families / 315 memberships
(42 compiler, 47 mechanic, 7 trait). F001/L21 retains source-pin reconciliation;
none refreshed. T13 and the modular implementation remain in progress.

## L07 — Grouped personal save and stun defences (2026-10-04)

Five canonical records are completed together, reusing the existing special-save
and stun-reaction pipeline:

| Rule and source | Canonical grant and complete admitted behavior |
| --- | --- |
| [Dark Elf Fey Quickness](../../../../sources/knowledge/bands/mordheim/dark-elves/special-rules.yaml) | Acquired special skill: melee ward 6+, improved to 4+ with Step Aside. |
| [Druchii Fey Quickness](../../../../sources/knowledge/bands/mordheim/druchii-mic/special-rules.yaml) | Same source-backed skill for the four printed Hero recipients. `kind: warband_skill` and selectable grant correct the former automatic profile classification. |
| [Strigoi Bestial](../../../../sources/knowledge/bands/mordheim/strigoi-kaz/special-rules.yaml) | Innate Vampire ward 6+, effective against mundane and magical attacks. Other profiles receive no Bestial grant. |
| [Corpse Master Magical Void](../../../../sources/knowledge/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml) | Innate 4+ special save against magical weapon attacks; no save from this rule against mundane weapons. Preserve a stronger applicable ward and bypass an unrelated mundane-only ward's magic restriction. |
| [Fen Guard Hard to Rattle](../../../../sources/knowledge/bands/mordheim/fen-guard-mim/special-rules.yaml) | Innate helmet-equivalent 4+ reaction after a Stunned injury. Fire ignores this protection. Existing independently worn helmets and Thick Skull retain their own contracts; the contextual protection does not rewrite the equipped helmet field. |

Fey Quickness reuses `skill.elven-agility`, including the already implemented
High Elf variant. Bestial adds a scalar ward descriptor. Magical Void and Hard
to Rattle add two modular tag consumers and explicit optimized-support refusals
until L19/L20. No new combat state, generic save subsystem or test module was
introduced. Printed source prose and translations remain intact; existing 2A/2B
mirrors are aligned. Missile avoidance and spell saves remain outside the
Combat Lab duel scope; no shooting/casting subsystem is implied by these grants.

Bounded verification: eight new cases in the maintained
`test_local_modifier_variants.py`, plus six existing High Elf and Domnu controls,
give 14 passed. They check acquisition/absence, 6+/4+ boundaries, Step Aside
composition, Bestial's mundane/magical behavior, Magical Void's target restriction
and independent save, and Hard to Rattle's 4+/3 failure boundary and fire
exception. Save fixtures retain canonical compilation; two-wound fixtures or a
one-wound current state isolate the relevant save/injury boundary. Tagged incoming
attacks exercise supplied magical/fire facts, not spell or ignition production.

The structural snapshot has 242 execution mechanics, 239 projected mechanics,
215 canonical/observable bindings, 108 modular tag consumers and 756 implemented
records. Families: 101 / 322 memberships (43 compiler, 51 mechanic, 7 trait),
including the three equivalent Fey Quickness sources. Affected editorial schema,
publication, documentation and whitespace checks close this lot. No full
semantics, parity, coverage or mutation suite was added or run. F001/L21 owns
the exact source/runtime pin reconciliation; no pin was refreshed. T13 remains
in progress.
## L07 — Grouped innate resilience and injury charts (2026-10-04)

Four canonical grants now execute together:

- [Fen Guard Hard to Kill](../../../../sources/knowledge/bands/mordheim/fen-guard-mim/special-rules.yaml):
  only Dryads and Spiteborn use 1–2 Knocked Down, 3–5 Stunned, 6 Out of Action.
  Fire disables this protection. The structured band recipient filter now names
  those two printed profiles; Branchwych and other Fen Guard do not inherit it.
  Hard to Rattle remains a separate stun reaction with its own fire exception.
- [Strigoi Bats Squishy](../../../../sources/knowledge/bands/mordheim/strigoi-kaz/special-rules.yaml):
  1–2 Knocked Down, 3 Stunned, 4–6 Out of Action. The source-qualified
  `mechanic.bat-injury-chart` avoids conflating this chart with the Bloated
  `rule.squishy` No Pain exception resolved under Q037.
- [Plague Priest and Plague Champion Resilient](../../../../sources/knowledge/bands/mordheim/skaven-of-clan-pestilens-mou/special-rules.yaml):
  both start with the existing `skill.resilient` effect, reducing incoming
  close-combat Strength by one. Other profiles receive no automatic grant.
  The skill's execution stacking is now `once`: explicitly selecting that
  same skill cannot double an innate grant in the same compilation.

Existing modular injury and Strength consumers are reused. Only two
source-qualified injury tags are added; their optimized support is explicitly
refused until L19/L20. The bat threshold is contextual: changing the shared
`out_of_action_threshold` max-composition contract would discard the weaker
printed chart. No generic composition or battle-state redesign was introduced.
Printed prose/i18n and existing 2B mirrors are preserved/aligned.

Bounded validation: six new cases in the maintained family module plus three
existing Hard to Rattle/Q037 controls, nine passed. Tests cover the priest and
champion's actual wound boundary and duplicate grant, an ungranted novice,
the bat's 3/4 injury boundary, and the Fen Guard recipient/fire exception at
injury 5. The structural snapshot, affected schemas, maintained publication,
documentation and whitespace checks close the lot. No new test suite or full
semantic/parity/coverage run. Snapshot: 244 execution / 241 projected mechanics,
218 canonical bindings, 110 tag consumers, 760 implemented records; 104 families
/ 326 memberships. F001/L21 retains source pins; none refreshed.

## L08/L09 — Shadow Dances of Loec

Implemented in the modular engine from the [Sea Ghosts source](../../../../sources/knowledge/bands/mordheim/sea-ghosts-mim/special-rules.yaml):
Whirling Death (+1 Injury), Storm of Blades (+1 Attack), Shadows Coil
(unmodifiable 4+ special save, including magic), and Woven Mist (total attacks
−1, Strike First with Initiative ties). Learned dances are available to the
Feast-Master and a Hero-promoted Minstrel; bonuses last only the chosen round.
Feast-Master Bestial also grants Psychology immunity; leader succession is
campaign-only.

**Q078 interpretation:** choose a learned dance each close-combat round when
able, excluding the preceding round's dance. With only one learned dance,
alternate a dance round and a round without it. A fresh duel resets history.
Reject declining all legal choices. Parent acquisition records add no passive
bonus; campaign learning is outside the duel.

Validation: five new focused cases, ten passed with existing controls;
structural audit and affected schemas pass. Remaining: L18 product choice
controls, L19/L20 optimized ports and F001/L21 source-pin reconciliation.

## L08/L09 — Conditional attack restrictions

Imperial Noble Honorable now forbids melee attacks against Knocked Down or
Stunned opponents at attack declaration, including separately timed pools;
attacks already declared together against a standing target retain the normal
collective resolution. Sign of Sigmar and Righteous Aura now reuse the existing
Undead/Possessed first-round reduction, with a minimum of one attack.
Core Vampire, Dire Wolf, Zombie and Possessed profiles now carry the existing
explicit target-classification trait; living Necromancers and Dregs do not.
Four new focused cases cover canonical construction, two-round expiry,
classification/minimum controls and denial without dice; nine pass with the
previous dance cases. Schemas and structural audit pass. F001/L21 retains pins;
Honorable's optimized port remains L19/L20.


## Grouped modular continuation — 2026-10-05

This continuation implements opponent-qualified modifiers, individual control,
reactions and turn-limited behavior in the modular engine. Optimized engines
explicitly refuse these effects until their ports; classification facts alone
do not prohibit optimized execution.

| Family | Delivered duel behavior |
| --- | --- |
| Opponent facts | Explicit Undead/Daemon/Possessed/living, ordinary-animal, Vampire, Lizardman and racial facts. Canonical warband-group identities remain separate from individual race. Necrarchs-Mou's living Abomination stays living; the LotD1 Abomination's unproven Undead inference was removed. |
| Qualified modifiers | Animal Friendship affects ordinary animals only; Morr, Thirst for Vengeance, Andanti Knowledge, Torturer, faction/racial Hatred and Noble Disdain use their actual target facts. Hellblade is a selected magical two-handed weapon: S+1, qualified hit bonus and source-qualified critical threshold. Torturer's permanent S loss excludes non-melee damage and survives random-S refresh. |
| Charm | Mesmerising Dance blocks attacks, preserving defence. Savage Fury grants its charge attack and Fear/charm exemptions. Shornaal tests with three dice, discards the lowest and stops testing after success. Hypnotist uses a separate trance, breaks at the first declared attack, and preserves the victim's ordinary retaliation after waking. |
| Special attacks | Wraith Touch replaces the whole pool with one unarmed attack and the Liche-only healing choice. Titanic Strength tests after a failed To Wound. Wheelo's charging D3 automatic S4 impact hits precede weapon blows; its failed Fear test preserves collision and only restricts crew hits. The four supplied legal fittings add armour penetration, Concussion, a counter-charge hit or first-event S5. Mighty Blow changes crew wound rolls instead of Strength. Multiple independent targets remain excluded. |
| Defences and current conditions | Foul Odour penalizes living melee opponents, strengthens incoming fire and refuses supplied open flames through shared legality. Night Haint Ethereal saves mundane hits before wounds; magical hits bypass it. Ghost Pirates use a distinct 4+ unmodifiable wound save, bypassed by magic and their printed special metals, excluding Dodge/Step Aside. Fen Guard Fear of Fire preserves the printed exception to Psychology immunity. Centigor Drunken results expire after its player turn; the duplicate canonical Trample attack contribution was removed. |
| Compound clauses | Slayer Psychology immunity excludes novice Stubbles/Axe Hurlers and the Rememberer. Shared equipment restrictions preserve thrown weapons and refuse armour/constant-save cloaks. Ogre Hunter keeps light armour and refuses heavy armour. Supplied mounted Righteous Charge lasts the charging first round only. |
| Leadership | Source-identical shared grants and 102 further six-inch Leader declarations reuse existing operators. Twelve explicit Undead declarations reuse the complete local Undead operator. Selected Arkhar affects the Chieftain, not the whole band. Undivided and Wizened use eligible supplied leader snapshots; Wizened rerolls affect Halflings, not their Ogre. Slavehounds accept a supplied active handler value and do not borrow an ordinary Leader. |
| Individual Animosity | Night Goblins-Mic and Crooked Moon's printed one-die squabble blocks only the model's own-turn attacks and excludes their Trolls, Squigs and Snotlings. The different pre-engagement two-die tables are not substituted by this operator. |
| Conditional Fear and Commands | Gaolers' Nasty Reputation targets explicit Humans. Sea Singer uses an explicit male/female fact: male non-animal charge/control tests, female Fear, and no further control tests after success. The editor supplies sex, nature, species, lit items and already qualified individual effects without guessing from names. Supplied active Mazzalupo Follow Me gives +1 melee hit until turn end; Ready to Die raises the Injury threshold until the recipient's next turn. Issuing/casting, range, third providers and group actions are not simulated. |

Consult the affected canonical `special-rules.yaml`/`profiles.yaml`,
`catalog/mechanics/close-combat.yaml`, `execution.yaml`,
`implemented-canonical-families.yaml` and `registry/runtime-scope.yaml` for
identities, bindings and source citations. Existing 2B mirrors follow their
canonical changes. The retained family suite exercises canonical compilation,
strict attack/turn sequences, recipient and ordinary controls; the maintained
structural audit covers the projections. No new report or suite was created.

Explicit facts never mean that all unnamed racial profiles have been classified.
Missing source classification, Domnu Bear Hug allocation, remaining hired
participant clauses and keeper-qualified Ferret effects retain
the existing follow-up owners. Wheelo fittings describe an already trained,
legally fitted participant; campaign acquisition and Sprint movement are not
simulated. Source fingerprints remain F001/L21; no blanket repin was performed.
Warband Rout, post-victory Bloodgreed, post-OOA banishment and Shame conversion
are excluded under the agreed resolved-1v1 scope, rather than missing damage or
Leadership mechanics. This section does not close T13 or declare the entire
modular inventory complete.

Stable family checkpoint: 275 cases passed (the existing modular family plus
characteristic-bonus contract), the real Tk supplied-fact round trip passed,
and structural verification compiled 1,050 profiles with zero errors. The
publication generator ran successfully after repairing corrupted aliases of
canonical skill prose; no presentation conflict was suppressed. Remaining
hireling/product integration and source-blocked clauses are not certified by
these results.


The 2026-10-05 canonical hireling continuation adds separate 2B participant
choices backed by `load_hirelings`, preserving canonical ids and starting skills.
Shared eligibility validates whole printed kits, alternatives, quantities and
source-qualified materials. Crimashin's dagger uses gromril; the Holy Man's
staff counts as a double-handed weapon. Bog Hunter Unholy Stink affects every
melee enemy, including Undead. Norse Bearman Shieldmaster grants shield parry;
Bulwark improves melee armour only with axe and shield; Drunken reuses the
source-identical existing turn operator. Hardened and Ogre Fear reuse existing
operators. Snorri's printed 5+ save is bound, but his unresolved compound rules
still block canonical compilation. Name-only entries are not editable profiles.

Twelve hired-sword profiles have no pending intrinsic operator; fourteen
normalized hired/Dramatis profiles remain explicitly blocked, and two Dramatis
lack stats. Optional priest Marks remain pending choices, never automatic
combined grants. F036 therefore stays open for those clauses and full product
closure; F037's unresolved Aldred starting skills are not guessed. Seven narrow
regressions were added to the existing construction/modular families; the
historical trace now checks runtime dispositions instead of their absence.

Validation: 385 existing-family cases passed (seven new cases), five focused
structural checks and the documentation check passed. Both native profile
documents validate; staging promotion remains a no-op; the publication and
shared eligibility bundle are current, and workspace typechecks pass. All
twelve unblocked canonical profiles compiled. Real Tk round trips compiled
Norse Bearman, Crimashin and Holy Man without changing their selected weapons.
No full semantic/parity campaign gate or optimized port is claimed.
