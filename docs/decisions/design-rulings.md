# Design rulings

Permanent decisions taken during development that bind the KB, the engines or
the applications. Each entry states the decision and its justification; the
reviewed text that motivated it is linked where it lives (KB file, spec, or
code). This page is consultable on its own; audit findings and development
history are not part of the permanent design record.

Rulings that answer a specific spec `question` are additionally recorded next
to the spec (`ruling:` field in `tests/specs/semantic/**`); this page collects
the ones with lasting design impact plus the decisions that were taken outside
a single spec.

## Duel engine (modular oracle)

- **Basic critical table only.** The weapon-family critical charts are
  optional rules and are not enabled. A separate critical result roll governs
  damage, armour denial and Injury modification; table bonuses modify that
  roll; multiple-damage effects use the greater result.
  (`mordheim_combat/phases.py`, `catalog/rules/core-combat.yaml`)
- **WS 0 is an automatic hit, no hit die.** Automatic hits carry no fabricated
  natural six; a natural six fails an ordinary characteristic test. Opposed
  rolls and Leadership tests keep their own contracts.
- **Strike Last controls the whole round order.** The first-round `max`
  priority floor does not erase negative priority; charged spears get no
  extra tier. Strongman remains an explicit exception; equal first-strike
  tiers compare Initiative.
- **One combat-phase iteration per player turn**, starting with the charger's
  turn. Both fighters reset phase resources; only the active player's fighter
  recovers or tests paralysis/fire. Replaces simultaneous recovery; the
  documented automatic Black Hunger activation convention is retained.
- **Force of Will rescues immediately on OOA**, before later prepared attacks
  of the same multi-hit attack. The OOA trigger is not limited to ordinary
  melee attacks. Timing interpretation adopted to keep the second-removal
  clause meaningful.
- **Fire and other synthetic hits are hits, not melee finishers.** Burning
  causes an independent S4 hit whose source has neutral offensive effects
  (no inherited wound bonuses, rerolls, armour denial or extra damage) while
  the victim keeps real defenses. Spines, acid blood and Black Hunger
  backlash resolve as hits likewise.
- **Poison timing.** Spider Spittle tests immediately on an undefended hit,
  before wound and saves; a parry prevents the trigger. Disease Dagger tests
  on a natural hit six; the extra infection wound is separate and automatic
  (no To Wound roll), and allows no saving throws, as explicitly confirmed by
  the user under D13 on 2026-10-14. This supersedes the earlier instruction to
  allow general armour saves for that extra wound. Undead/Possessed are immune,
  and wound reactions resolve immediately and exactly once. The D13 exception
  applies to the extra infection wound, not the dagger's ordinary attack.
- **Stateful equipment projection happens before** priority, parry resource
  initialization and attack counting. Brace is limited to two shots with a
  surviving-hand-weapon or KB-compiled unarmed fallback afterwards; Trap
  Blade persists a broken hand and already-rolled hits keep their original
  weapon for wound resolution; the Serpent Staff active mode (fixed WS4/S4,
  one attack, no parries, chosen before priority) replaces all normal attacks.
- **Luck re-rolls one failed roll of its own** (hit or wound) and is spent for
  the rest of the duel. In the vectorized engine the defender-side Luck also
  re-rolls one failed armour save per battle.
- **Kusara / Whipcrack minimum is per warrior**, not per timed event: pools
  receive the phase-level minimum and consume each selected-hand suppression
  once; whip bonus projection retains the original hand slot.
- **Dagger-class +1 enemy armour save is not doubled with Strength** and
  Critical hits ignore armour only through the critical result. (Recorded
  where the consumers read it: `modular/attacks.py`, `vectorized/_attacks.py`.)


### Spectral Touch Q019

For Spirit Host Spectral Touch, the user accepted recommendations R1–R4 on
2026-10-01. A successful final natural hit six establishes one immediate extra
wound, then the ordinary contribution if both participants remain active.
Automatic/manufactured hits provide no natural six. Resolve original-hit
defenses first; the extra is not another hit and repeats neither hit defenses
nor on-hit effects. It has no wound/critical die and consumes no critical slot.

The extra inherits applicable attack save/injury modifiers and eligible defenses,
respecting each printed defense's timing, but remains capped at one despite
generic damage multipliers. Resolve its injury, rescue and immediate reactions
before the ordinary contribution; stop if either combatant remains removed.
A rescued participant may continue with current resources. Preserve collective
pool hit/defense preparation before per-hit extra/ordinary processing.

Barrage requires failure to establish any wound for that attack. An established
extra wound therefore prevents another Barrage attack even when saved and even
if the ordinary wound roll fails. With no extra wound, ordinary failure keeps
its existing optional continuation. Each new hit has its own natural-die provenance.

These are project composition/order rulings justified by the original Night Haint
and general/Barrage sources, not quotations of an explicit combined rule.
The accepted source interpretation does not itself certify canonical grants,
every legal equipment composition or optimized execution. Spirit Knife/Q146
requires separate recipient and source review.


### Shifty S1–S4

The user accepted the independently reviewed S1–S4 recommendations on
2026-10-02. They define the modular composition contract:

- **S1 — count and suppression.** Add the charged warrior's bonus after Frenzy
  and the two-weapon extra, before whole-warrior reductions. When generic
  reductions leave one attack, that survivor retains the bonus's Strike First
  timing, including under the one-attack fist cap. Consume each selected-hand
  suppression at most once across the warrior's timed events. Source-specific
  losses, including Halfling Crude Belch's loss of an enemy's first/only attack,
  require their own targeted mechanism; do not represent them as generic count
  reductions or erase their explicit zero-attack consequence.
- **S2 — early melee nomination.** Nominate one usable carried melee hand before
  resolution and preserve its weapon, poison pair and hand slot. Mixed
  pistol/melee uses melee for the bonus; fabricate neither an extra shot nor a
  fist while weapons remain. Pistol-only refusal remains an explicit provisional
  simulator limitation, not a tabletop prohibition. Its complete allocation
  contract remains pending in F005/F026.
- **S3 — coherent ties.** Resolve equal priority/Initiative once per warrior pair
  and reuse that order for timed Shifty/Whipcrack events; do not redraw per event.
  Preserve both independently earned bonuses. This does not assert canonical
  whip access for Halflings.
- **S4 — replacement composition.** Choosing Serpent Staff power replaces the
  Shifty bonus together with ordinary attacks; declining retains normal Shifty
  behavior. A single bonus repeats neither Bull Charge, Body Slam, Anvil Head
  nor natural/extra attack lists. Synthetic Staff fixtures do not certify legal
  Halfling loadouts.

These are accepted project composition/order interpretations, not quotations of
an explicit combined source rule. These rulings bind future activation/specifications and optimized ports. F003 closes at this
modular boundary; canonical Shifty activation, maintained poison witnesses,
pistol-only allocation, Crude Belch implementation and optimized execution retain
their separate evidence and ownership.

## Construction and KB modelling

- **Equivalence is explicit, never inferred.** Two rules that do the same
  thing share `binding.kind` + `binding.id` (+ `parameters`); a rule without
  a `runtime` block is unclassified, not implemented.
- **Racial maximums live once** in `catalog/rules/racial-maximums.yaml`
  (`campaign.limit.racial-maximum.*`); warband rules and campaign advancement
  reference them by id and never embed the statline.
- **Hireling eligibility is evaluated by the application** from
  `*.rule.campaign-eligibility` rules and the KB trait registry
  (`catalog/hirelings/traits.yaml`), never inferred from static warband
  groups; ambiguous contexts produce explicit `needs_variant`/`unknown`
  decisions instead of guesses.
- **Hireling profile identities are not reused from bands** merely because
  names match; source-only concepts stay in `unresolved_references` until
  their catalogue exists.
- **English is canonical and stored once** in the `name` / `effect` fields;
  `name_i18n` / `effect_i18n` hold only translations and carry no `en`
  mirror. A reviewed Spanish pass fills `name_i18n.es` / `effect_i18n.es`
  across the warbands and catalogues, following the translation glossary
  ([translation glossary](../reference/translation-glossary.md)).

## Campaign application

- **The KB declares rules and tables, never results.** Warband XP, gold,
  wyrdstone, stash, injuries, rolls and purchases are campaign state
  identified by stable KB ids; no YAML of `catalog/campaign/` is loaded as
  duel-rule implementation.
- **The Trading Post prevails at the market.** Band `equipment-access.yaml`
  costs are creation prices; a `price_override` is recorded only when the
  warband's own source confirms a market-price exception (Nuln black-powder
  weapons, Hochland Duelist pistol, Lizardmen light armour).
- **Advancement thresholds and tables come from the KB**
  (`catalog/campaign/experience-and-advances.yaml`): the app seeds one
  pending advance per crossed XP threshold, resolves 2D6 (+D6 sub-rolls)
  against `advancement_tables`, and validates stat picks against the KB
  racial maximums and the henchman +1-over-starting cap.
- **The Lad's Got Talent promotion** follows the KB row: one member promotes
  to Hero preserving type, experience and characteristic increases, takes 2
  picks from the warband hero skill tables, the remaining group's advance
  resets for a reroll excluding the promotion itself, and the pending
  promotion bypasses the static hero limit for exactly one earned advance.
- **Equipment reassignment between roster and stash is always legal**
  (tabletop reallocation); buying and selling stay inside the post-battle
  sequence. Hired Swords are tracked by the roster (`hireling.*` profile
  ids) so mutual-exclusion hiring rules fire.
- **Battle records drive Recovery.** The recorded Out-of-Action list derives
  the casualties count and scopes the injury step; legacy records (no list)
  fall back to every warrior. Henchman groups tick as a whole group, matching
  how the injury engine decrements group quantity.

## Knight's Helm source erratum — 2026-10-04

The user has classified `knights_helm` as an error in the original data and
confirmed that it will be removed from the KB. The named Skull Busta/Basha
4+ counterpart is therefore not an admitted implementation obligation.
Do not invent a replacement item, access route or ordinary-helmet alias.
Ordinary-helmet Basha remains implemented and unchanged.
F063 no longer blocks modular completion. Any remaining references or
generated data for the rejected counterpart must be removed with that KB entry.

## Combat Lab remains a 1v1 duel simulator — 2026-10-04

The user reaffirmed that Combat Lab simulates one combatant against one
combatant. The modular engine must not expand it into group combat or a
warband battle engine.
Warband Rout tests, group casualties/psychology, All Alone enemy counting,
multi-target resolution and independently simulated third participants are
outside this product scope. Their absence does not block modular completion.

Individual tests, charges, attack sequences, escape and conditions affecting
the two duelists remain candidates. An external aura, leader or temporary
effect may be supplied as an explicit current condition/bonus of a duelist;
the simulator does not generate or evolve the surrounding group. Existing
nearby-provider inputs represent snapshots, not additional mutable combatants.
Hirelings may be canonical duelists; mounts/companions require a source-backed
single combatant projection and do not authorize extra independent fighters.
Commands are considered only for their supplied effects on the duel, not a
group emission/hearing/recipient subsystem. Preserve complete KB rule text and
split individual consequences from excluded group clauses.

This decision supersedes broader group/routing requirements recorded in
historical implementation inventories, deliveries and follow-ups. Those
records and their scope data are reconciled against this boundary; optimized
ports are certified only for the admitted 1v1 clauses.

The user additionally excluded map/terrain rules on 2026-10-04: fog, Mystic
Mist protection, water/aquatic combat, swamps and similar environmental
conditions are outside scope, including caller-supplied map-condition switches.
Do not add terrain/weather inputs, movement through terrain or environmental
combat modifiers. Preserve original KB prose and exclude those clauses during
scope reconciliation. A normal-duel individual clause may still be implemented
without its excluded environmental exception (for example Craven's Fear
consequence without Mystic Mist). This is an explicit supported-context limit,
not a claim that the entire source rule is implemented for all environments.
Personal attack effects such as poison or catching fire are not map rules.


## Bloated Squishy overrides No Pain — Q037 — 2026-10-04

User ruling: apply Squishy as the specific exception to No Pain for Ghost Pirates'
The Bloated. A stunned injury result remains stunned, including when No Pain is
inherited from another contribution. Preserve both contradictory source clauses
verbatim; do not rewrite the printed source. Q037 is resolved by this ruling.


## Sea Dragon Cloak is armour — Q128 — 2026-10-04

The user chose ordinary armour semantics for the Sea Dragon Cloak, like light
or heavy armour. It is an armour choice, not an independent ward or an additive
+2 bonus on another suit of armour. Use the normal armour-slot and shield
composition rules, not a blanket prohibition on shields/helmets. Preserve the
printed alternative interpretations as source prose; this ruling selects the
project contract. Q128's semantic decision is resolved; F024 remains an
implementation/integration task until selection and compilation follow it.

## Curse of the Revenant recovery — Q013 — 2026-10-04

The user fixed recovery at the start of the warrior's own turn. The printed
5+ roll, one recovered wound per turn, and Great Thirster prerequisite remain.
The user explicitly confirmed that fire does not prevent this recovery, including
wounds caused by fire. Do not reuse ordinary regeneration's fire prohibition or
wound-time timing for this separate ability. Q013's semantic decision is resolved;
F013 remains implementation work for its prerequisite, recovery clock and cap.

## Shifty and pistol special attacks coexist — F005 — 2026-10-04

The user permits both the pistol's special additional attack and Shifty's
additional attack to be used together. This supersedes the provisional pistol-only
refusal in S2 above. Preserve both separately earned attacks and Shifty's timing;
do not cancel either merely because the other is present. F005 is semantically
unblocked but its allocation/resource implementation remains pending, coordinated
with F026's maintained melee-pistol contract. Existing code still rejects the
pistol-only nomination; this ruling is not a claim of delivered behavior.


## Voluntary escape does not belong to Combat Lab — 2026-10-04

The user excludes mechanics whose purpose is escaping or terminating the duel
prematurely without resolving it. A two-model implementation alone does not
justify admission. Voluntary escape, withdrawal and contact-breaking effects that end the duel without resolving it are outside Combat Lab scope. No board movement, re-engagement or escape subsystem is required.
Combat effects that alter attacks, defences, wounds, recovery, states or ability
to fight remain admitted; normal Fear/Stupidity charge consequences are not
voluntary escape mechanics. Composite rules retain applicable combat clauses
and exclude escape/map/group/campaign clauses explicitly.


## Shallya healing does not permit self-healing — 2026-10-05

The user confirms that Mercy and Healing Hands heal another model in contact,
not the Priestess herself. No self-healing operator or exception is authorized.
The user also rejects healing the adversary. Both abilities are excluded from
Combat Lab as support to other warriors; post-battle Surgery is likewise excluded.
No healing operator, tactical opponent-healing option or source-text change is required.

## F074 equipment bearer rulings — 2026-10-06

For Order of the Mare, the user prioritizes the
[Mordheimer web version](https://mordheimer.net/docs/warbands/grade-2a-warbands/order-of-the-mare)
over the conflicting PDF equipment table. Heavy armour in the Footman list is
therefore restricted to Knights: Paragon, Gallant and Redeemed Knights.
The decision does not introduce mounted-combat support.

For Wood Elves of Athel Loren, the user restricts the local Ithilmar weapon and
armour entries to Heroes, including promoted Henchmen. Express the restriction
as the configured `hero` profile type, not a fixed list of starting Hero IDs.
The discount and rarity/initial-purchase clauses are separate acquisition
conditions; they neither grant nor remove eligibility to use the items.
Preserve the printed prices and notes in the
[equipment lists](../../sources/knowledge/bands/mordheim/wood-elves-of-athel-loren-web/equipment-access.yaml).

### F074 source clarifications

These accepted source interpretations retain their original audit IDs; they do
not certify implementation. User rulings above take precedence. Revalidate a
changed source before reusing an interpretation. Historical source URLs and
per-origin text fingerprints remain available in Git.

| Id | Scope | Decision |
| --- | --- | --- |
| `F074-brood-dagger` | YES | Printed dagger restricts the bearer to Henchmen; not merely a free-dagger price condition. |
| `F074-crooked-moon-daggers` | YES | Poison Daggers belong to the Fanatic list; their appearance on the ordinary Night Goblin list does not grant them to ordinary Goblins. |
| `F074-pirate-variants` | YES | Qualifiers select warband variants: Estalian adds rapier/heavy armour and removes crossbows; Wasteland adds handguns. Keep other prohibitions conjunctive. |
| `F074-forest-bosspole` | YES | Bosspole recipients are Chieftain and Bosses, not every Hero; its spear contribution and Animosity immunity affect the duel. |
| `F074-halfling-aliases` | YES | The Cook-only footnote is about parenthesized culinary aliases; it does not prohibit generic dagger/hammer/axe/sword/helmet for other list users. |
| `F074-mare-lance` | YES | Knight-only in both tables; the Paragon has a separate explicit lance prohibition. |
| `F074-mare-mounts` | NO | Barding/warhorse entries belong to excluded mount-equipment support. |
| `F074-house-equipment` | YES | A House is selected for the whole warband; Fierezza/Halcon/Baluardo qualifiers are explicit. |
| `F074-lizard-poisons` | YES | Skinks use these poisons only on missile weapons; Saurus may use them on melee weapons. |
| `F074-reptile-venom` | NO | Belongs to Skink Henchmen missile weapons and lasts one battle; no admitted melee contribution. |
| `F074-lizard-sacred-marks` | YES | Sacred Markings Hero-only, at most one; Oversized Jaws Saurus-only (modifies bite); Poison Glands Skink-only (replacement bite). |
| `F074-sniper-equipment` | YES | Sniper is a chosen Modus Operandi of a Hero other than the Silent Master, not a missing profile. |
| `F074-underworld-leaders` | YES | The warband has two leaders; Man Catcher is Leader-only on both faction lists, so Goblin Bully and Skaven Slum Lord qualify. |

## Cathayan longsword prints no armour penalty — 2026-10-14

The coordinator decides that the printed prose governs: the Cathayan longsword
gives only +1 Initiative and +1 Weapon Skill. The `armour_penetration: 1`
parameter of the execution contract was project scaffolding and is removed from
`sources/knowledge/catalog/mechanics/execution.yaml`. Armoured defenders save
at their own printed face against the longsword. The corresponding E2E
clauses-authored record is in the corpus ficha for `weapon.cathayan-longsword`.

## The Starsword printed Dodge save is the ward save — 2026-10-14

For the Starsword standing exception ("ignores all armour saves except for ward
and Dodge saves"), the coordinator rules that the printed Dodge save and the ward
save are the same thing. The engine's ward face therefore carries the printed
Dodge exemption; no separate Dodge-save representation is added. The E2E
scenarios live in the `dodge-exception` clause of the starsword ficha.


## Supplied Weaponsmith maintenance affects the physical equipment — 2026-10-15

The recovered Maintenance table is rolled before each game; its first result
stands even without eligible equipment. Only its already obtained individual result
is supplied to the duel. Recipients are Heroes and the Weaponsmith. Result 2 gives
heavy armour 4+ and light armour 5+ before other modifiers. The extra +1 save for
helmets (3) and bucklers (4) is an armour-save contribution of that worn piece;
it does not change the helmet's separate 4+ Stunned reaction. Result 5 lets a shield
parry as a buckler, including sword-and-buckler composition, retaining its normal
armour contribution. Improvements last this game and leave with the physical item.
Results 1 and 6 grant no close-combat bonus; result 6's shooting range is excluded.
This implements the admitted supplied effects, not the external roll or party.


## Djinn's Curse respects expressly unmodifiable saves — 2026-10-15

Implementation criterion: the general penalty to enemy saves does not override
an individual save explicitly printed as unmodifiable. Ethereal's hit interception,
Marks of Ranald's 6+, Daemonic Flesh's unmodified 5+ and the Djinn's intrinsic 5+
keep their faces and prohibit roll modifiers. This follows the specific save's
exception; it does not make ordinary armour, wards or regeneration unmodifiable.
Djinn's Luck supplies an ordinary modifiable ward, so Curse still worsens it. If a
stronger ordinary ward ties the intrinsic save after the penalty, the ordinary
ward retains its own optional modifiers. Magic/blessed denials retain their
printed scope. These combinations resolve the duel rather than raising a
composition-ruling error.


## TC14 whip: disarm is a declared replacement action — 2026-10-15

Town Cryer 14, Mule Skinner / Whip (PDF page 11), is a distinct source-qualified
weapon (`whip_tc14`); it does not resolve the unqualified Trollheim placeholder.
Its melee uses S-1, cannot be parried and grants the enemy +1 armour save. Reach
and use outside contact remain excluded. Declare the target physical weapon before
the hit roll; disarm replaces injury, including a normal coup de grace. It still
rolls to hit, then grants exactly one independent hold parry irrespective of native
parry equipment/capacity or Strength. This hold attempt is not prevented by the
whip's normal no-parry clause, does not spend an ordinary parry, and grants no
weapon-pair reroll. It uses the ordinary strict-higher comparison (so a six cannot
be beaten), while universal owned-roll choices retain their own scope. Indestructible
and natural weapons are not disarm targets. Dropped pieces remain unavailable for
this combat; active or separately carried backups are used in declared kit order,
otherwise the fighter uses its unarmed fallback. Their actual effects apply already
to the reply in the same round. No post-combat retrieval/loss process is simulated.


## Haunted Mien lifts the Priest kit restriction — 2026-10-15

A selected Haunted Mien is the Black Guard career, mutually exclusive with Augur.
Ignoring Strictures lifts both the Priest's armour prohibition and the exclusive
scythe/dagger kit, not merely the armour token. Implementation uses the maintained
ordinary human Mercenary Equipment List for the newly available basic equipment;
it grants no faction-specific/unique catalogue wildcard. The printed starting kit
is retained when ownership is unspecified; an explicitly supplied current kit may
replace it but must contain the physical copies actually wielded. Offering, shared
facts and compilation consume the same choice. Combat/Strength access is added by
the existing source bindings. An unmarked Priest and an Augur retain Strictures;
Augur alone retains the permanent -1 S and the once-per-battle personal reroll.
Campaign advancement and determination of new prayers remain excluded.


## Drenok's Berserker is not the Slayer skill — 2026-10-15

Town Cryer 15 printed p27 (PDF p29, read visually) defines a distinct ability:
a first reduction to zero Wounds requires 4+ to stand fighting this turn, with a
fresh roll every subsequent player turn while still at zero; failure means Out
of Action. It neither restores a Wound nor grants the Slayer skill's charging hit
bonus. A successful roll covers further ordinary wound damage in that same turn;
renewal occurs next turn, including the opposing player's turn, because the source
says every turn without an own-turn qualifier. The roll is a continuation test,
not an armour/ward save that negates the wound. Other explicit instant-Out effects
retain their own conditions. Icefang is the printed double-handed weapon plus
Parry and +1 injury, not two stacked weapon profiles. The hide supplies ordinary
6+ melee armour; the separate 5+ missile face remains excluded. Gear effects belong
to the actual active pieces; they are not automatic innate profile grants.


## Eye Pendant: the attacking Undead tests — 2026-10-15

Khemri Dramatis Personae printed p16 requires any Undead warrior wishing to attack
Abdul to pass Leadership. The attacker tests once before its attacks in each combat
turn; a failure blocks that turn's attacks, without cancelling contact, charge or
defence. There is no retained success or once-per-battle resource. This is an attack
restriction rather than Psychology, so Psychology immunity does not waive it; an
explicit automatic-Leadership ability still follows the shared Leadership contract.
The text does not prohibit using a leader's Leadership. Both this restriction and
the 4+ Ward are carried by the equipped Eye, not an innate property of Abdul.
The Ward uses the ordinary pipeline including explicit all-save prohibitions such
as D13. Nomad Robes' weather effects and the spellcasting/Lamp producers stay excluded.


## Disability consumes a permanent supplied result — 2026-10-15

Chaos in the Streets p149 rolls Disability when the Cripple group is created.
The modular duel accepts exactly one condition.disability-1..6 and applies its
statistics once during compilation; initialization must not roll group creation
again. Parkinson permits one active weapon, not two weapons or weapon plus shield;
it does not forbid a single two-handed weapon or equate a buckler with a shield.
Head Injury uses ordinary Stupidity unless a friendly active Hero is within six
inches. A supplied qualified proximity condition is a current local fact, not a
permanent cure; explicit supplied provider records resolve side, activity and the
inclusive six-inch boundary. Poor Eyesight adjusts stored BS only; shooting, group
creation and campaign progression remain excluded.


## Penthesilea Weapon Master means Weapons Training — 2026-10-15

The user explicitly approved treating Penthesilea's undefined printed Weapon Master
as Weapons Training: proficiency/access to hand-to-hand weapons, without any extra
hit, attack or parry bonus. This is a project ruling, not a recovered definition
from Town Cryer 15. Bind compiler.weapon-knowledge with allowed_kinds restricted to
close-combat-weapon. Proficiency does not create physical copies, grant ranged
weapons, manufacture innate attacks or transfer another character's unique gear.
Her printed M/I 5/5 already include the Mark; Dance, Fury and individual human-male
Hatred retain their own operators. Concealment (jungle detection), Elixir of Life
(post-battle injury reroll) and hiring remain outside the duel.

## Alchemist attempts at the start of the owner's turn — 2026-10-15

The user chose the start of each own turn, once per turn, for both Backley's
Toughness test and the addicted Mad Scientist's attempt to brew a 6. The source
states the effects and release conditions but does not specify their cadence;
this timing is a project ruling, not recovered source text. No attempt occurs on
the opponent's turn or after that state has been cleared. Success is effective
that turn: Backley's actual Strength/Initiative penalties end; a successful brew
ends the action restriction and supplies Aberrantius Vigortia (+1 Strength and
Toughness), once, without healing Wounds or duplicating an already supplied dose.
The initial potion result/addiction are supplied. Campaign creation of addiction,
post-battle rolls and Quicksilver's Movement effect remain excluded.
