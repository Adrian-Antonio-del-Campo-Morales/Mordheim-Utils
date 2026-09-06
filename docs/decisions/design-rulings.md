# Design rulings

Permanent decisions taken during development that bind the KB, the engines or
the applications. Each entry states the decision and its justification; the
reviewed text that motivated it is linked where it lives (KB file, spec, or
code). This page is consultable on its own and does not change when an audit
closes — audit findings, evidence and pending backlogs live in
[the modular audit record](modular-audit.md) and can be deleted once resolved;
the rulings recorded here survive.

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
- **Translation is single-locale canonical English** until a reviewed pass
  fills `name_i18n.es` / `effect_i18n.es`; the Bretonnian pilot band is the
  style and glossary reference
  ([translation glossary](../../sources/knowledge/catalog/translation-glossary.md)).

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
