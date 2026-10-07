# Halfling Crude Belch — canonical modular milestone

Implemented on 2026-10-04 during the autonomous L06–L18 continuation.
This delivers the duel portion of [F061](T13-execution-follow-ups.md#t13-f061--halfling-crude-belch-cannot-use-the-generic-minimum-one-reduction).
L08/L10/L11 remain incomplete. Under the [user's 1v1 scope decision, 2026-10-04](../../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04),
multi-enemy resolution is excluded, not a deferred L12/L18 requirement.
L18 retains visible duel configuration; L19/L20 retain applicable ports.

## Sources and contract

The [Halfling special skill](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings)
allows an optional first-melee-round belch. Every enemy in base contact tests
Leadership; failure makes its first attack miss, even its only attack.
The [characteristic-test rules](https://mordheimer.net/docs/rules/characteristics)
use two D6 whose sum must not exceed Leadership. Crude Belch is not a
psychology exemption: Undead, poison immunity and Frenzy do not avoid its test.
Cold-blooded variants limited to psychology/routing are not applied to it.

The canonical rule and its existing 2A mirror now declare a selectable
`warband_skill`, bound to `skill.crude-belch-halfling`. The four original
Hero recipients are preserved. It is not automatically granted to every Hero,
and no legality rule was duplicated outside shared eligibility.

`phases.resolve_leadership` is the first actual Leadership consumer's minimal
2D6 operator. Unknown Leadership raises a specific error before attack dice;
it is never silently replaced by a default. Leadership providers, rerolls,
Cold-blooded selection and other variants still belong to L10/L12.

The round pipeline decides the belch and tests the opponent before attack
allocation. Failure is an ordered miss, not a numeric attack reduction. The
first allocated weapon is retained as a missed outcome with no hit die, and
later attacks retain their own weapons. A separately timed Shifty/Whipcrack
bonus consumes the miss if it is that warrior's first attack. Whole-pool
replacements and stunned finishing also respect the first-attack loss. The
existing generic minimum-one attack reduction remains unchanged.

## Local contacts and limitations

A legacy duel represents two combatants in melee. Explicit empty contacts
skip the belch entirely, without a decision or Leadership dice. The prepared
context identifies the actual local participants and their sides, without any
Warband Manager member, campaign or battle identifier.

The duel currently owns only two mutable fighter states. If the supplied
contacts contain an additional enemy of the belching warrior, execution
raises an explicit multi-participant error instead of silently leaving that
enemy unaffected. F061 remains open for this area-effect branch and its L18
visible configuration. Friendly contacts do not introduce an extra recipient.
No movement/board engine or group-state simulator is claimed by this milestone.

Optimized support explicitly refuses the new tag pending L19/L20. No
vectorized/native code was implemented or certified. Source identities/pins
and coverage line drift are reconciled in L21; old certificates are not reused.

## Focused validation

[The maintained suite](../../../../tests/python/combat/modular/test_crude_belch.py)
contains eight cases through canonical compilation and actual
`initialize_duel -> resolve_round`, with strict decisions/dice:

- Equality passes, failure removes the sole attack, and declining draws no test.
- A surviving off-hand attack keeps its own hit modifier after the main misses.
- Later rounds do not repeat the decision or test.
- Explicit no-contact facts skip the ability.
- Unknown Leadership and additional enemy contacts fail before attack dice.
- A timed Shifty bonus misses once; its ordinary attacks survive.

Focal family/Shifty/catalogue validation: **100 passed**. The catalogue's
generic test opponent now supplies explicit Leadership because it exercises
this real consumer; the maintained mechanism traversal reaches **208**.
Final broad results are recorded in the autonomous delivery appendix of
[the local-family report](T13-local-modifiers-defences.md#autonomous-continuation-validation).
Ignored command logs are under `build/cache/t13-parallel/crude-belch/`.
