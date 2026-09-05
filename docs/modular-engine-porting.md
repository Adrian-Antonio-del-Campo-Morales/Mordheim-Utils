# Pending ports of the modular rules audit

Scope updated at the user's request on 2026-09-05: finish the modular engine;
document NumPy and native work without continuing their implementation. See the
[research ledger](modular-remediation.md) for sources, editorial rulings and IDs.
The basic critical table is active; optional weapon-family charts are not enabled.

## Status

Existing candidate edits are retained as partial work, not certified ports.
The NumPy checkpoint of 3733 passing cases predates subsequent modular changes.
Native changes have not been built or behaviourally validated. Its successful
Cython syntax check predates the latest Spittle changes; syntax needs rechecking
too. Existing native binaries are stale. Neither checkpoint certifies completion.

## Required work

| Area | NumPy | Native |
| --- | --- | --- |
| Basic criticals | Verify all six results, phase limit, cancellation, maximum weapon/critical damage and independent Injury dice. | Complete/build the partial table and D3 port; test cancellation restoring eligibility and wound rerolls. |
| Automatic hits / finishers | Preserve pre-sequence condition through Spines and split events; no synthetic natural six. | Remove same-pool newly-stunned auto-removal; implement WS0 without dice; separate incidental hits from melee finishing. |
| Parry | Recheck highest-six capacity with unparryable attacks and charms. | Highest six must not offer a lower hit; preserve named exceptions and claw/two-axe rerolls. |
| Player turns | Verify active-player recovery, fire and paralysis with both fighters resetting phase resources. | Replace simultaneous recovery with alternating ownership; retain the documented Black Hunger convention. |
| Pistols / Trap Blade | Connect broken-hand state to equipment projection per row; implement breaking and original hand identity. | Port brace limits, spent-pistol fallback and persistent broken hands before priority/parry/counts. |
| Rapier | Route Barrage decisions through actual attack keys; test decline and cumulative penalties. | Replace single extra attack with optional iterative continuation through the complete pipeline. |
| Whipcrack | Split charged bonus into its own Strike First event; ordinary attacks retain priority, one bonus across hands. | Port the same event model and all whip tags; test Frenzy, two whips and staff replacement. |
| Weapon fields | Verify corrected KB consumers, magical armour denial, D3 damage and table bonuses. | Recheck shifted field indexes and all consumers, including armour denial and table bonuses. |
| Lotus / Spittle | Route optional Lotus decisions at runtime keys; guaranteed wounds do not reroll as failures. | Finish Lotus decline and immediate Spittle tests with correct recovery and dice consumption. |
| Disease Dagger | Implement immediate infection, immunity, separate wound/save and exactly-once reactions. | Port the same sequence and aggregate damage reporting, including infection killing before the dagger wound. |
| Kusara | Verify selected-hand counters and allocation across split events; keep minimum one attack. | Add selected-hand state, apply before reply and expire at the documented boundary. |
| Characteristic tests | Recheck genuine tests: natural six fails; opposed rolls differ. | Review callers still passing `six_fails=0`; do not change opposed/Leadership rolls indiscriminately. |
| Force of Will | Verify immediate rescue on relevant damage paths, including fire before later events, sustain and second removal. | Port immediate rescue, cumulative sustain penalty and spent resource; test success and failure. |
| Fist / Serpent Staff | Verify final fist cap and optional WS4/S4 single attack without parry or extra pools. | Port final cap and staff replacement before priority/count generation. |

## Shared contracts and required evidence

- `EffectSet.damage_die_sides` changed the native layout from 54 to 55 fields.
  Preserve the ABI guard and rebuild against matching fields before execution.
- Consume compiled unarmed fallback and original hand slots; no runtime KB reads.
- Persist broken/hampered hands and secondary-wound reaction accounting across
  events. Local operator projection alone does not prove runtime equivalence.
- Reject exhausted/unused dice and decisions. Individual NumPy attack replay was
  tightened; pool replay still needs review. Never invent missing sixes.
- Use source-derived expectations from modular regressions and semantic specs,
  then L0/L1, multi-event/multi-turn L2 and L4 coverage/mutations before statistics.
  Native requires observable deterministic behaviour, not only a successful build.
- Three earlier pending Averlander promoted-halfling cases depend on the Lad's
  Got Talent construction model. Keep them separately pending without weakening
  parity completeness checks.

Final modular interaction checks and certification remain in progress. This is
an implementation backlog, not proof that all candidate or modular interactions
are already correct.

Fire recovery must also isolate its S4 hit from the opponent's global offensive effects (wound bonuses, rerolls, armour denial and damage). Preserve the victim's defenses and immediate Force of Will response.

Kusara/Whipcrack: apply the minimum across the warrior's events, consume each suppression once, and preserve the original hand slot of the projected bonus weapon. Test A1, A3 and an off-hand whip.
