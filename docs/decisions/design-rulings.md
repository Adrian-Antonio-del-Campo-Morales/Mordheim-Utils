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
  on a natural hit six; the extra wound is separate, general armour saves
  apply (no denial clause exists), Undead/Possessed are immune, and wound
  reactions resolve immediately and exactly once.
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
[Source locators and accepted review scope](../knowledge/2a2b/tasks/T13-spectral-touch-review.md),
[contract and implementation proof](../knowledge/2a2b/tasks/T13-spectral-touch.md).
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
an explicit combined source rule. [Sources and independent recommendations](../knowledge/2a2b/tasks/T13-shifty-independent-review.md#11-decisions-ready-for-human-acceptance)
and [acceptance record](../knowledge/2a2b/tasks/T13-shifty-review.md#human-acceptance--2026-10-02)
bind future activation/specifications and optimized ports. F003 closes at this
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
  ([translation glossary](../../docs/knowledge/translation-glossary.md)).

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
