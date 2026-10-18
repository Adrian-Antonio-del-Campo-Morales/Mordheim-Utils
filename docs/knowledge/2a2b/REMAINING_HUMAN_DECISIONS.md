# Remaining human decisions

Only unresolved questions requiring human authority belong here. General work
remains in [the semantic CSV](tasks/T13-semantic-analysis.csv); concrete unresolved
implementation obstacles belong in
[Remaining modular engine problems](REMAINING_MODULAR_ENGINE_PROBLEMS.md).
Accepted decisions remain in [design-rulings.md](../../decisions/design-rulings.md).

The [implementation plan](REMAINING_MODULAR_ENGINE_WORK.md) delegates ordinary
rule interpretation to the implementer, within adopted rulings and admitted
scope. Missing data, source recovery, technical modelling choices and absent
fixtures do not by themselves require a human decision. Do not reintroduce
answered questions or ask for permission to implement an existing contract.

## Pending decisions

None currently recorded. Penthesilea Weapon Master was answered and implemented on
2026-10-15; the accepted ruling is in `docs/decisions/design-rulings.md`.

Disease Dagger D13 was answered on 2026-10-14: the extra infection wound is
automatic and allows no saving throws. Its accepted contract remains in
`design-rulings.md`, Poison timing; it is not an unanswered question.

## Adding and closing questions

Add only the exact unanswered question, affected rule, conflicting evidence or
scope/authority limit, and what the answer will unblock. An implementer-delegated
interpretation is escalated only when it would override an adopted decision or
expand authorized scope. On resolution, retain the accepted ruling in its
canonical home and remove the question from this active register.
