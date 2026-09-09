# Verification history

Development record of how the verification layers earned their current shape.
The [verification reference](../reference/verification.md) describes *what*
each layer certifies today; this page records *why*, with the empirical
evidence. These narratives were moved here from the reference so it stays
descriptive and stable.

## L2 — why the truncation sweep replaced the round histogram

The first attempt at whole-duel orchestration parity compared per-duel
*resolution rounds* via a χ² over a winner×round histogram. It diverged on
the `stateful` scenario while the aggregate outcome rates passed. Triage
showed the divergence was a ledger-convention artifact: duels resolved by
round-start phases (fire, Force-of-Will sustain) are attributed to different
round numbers by each driver. The oracle's observed mode
(`simulate_duel_observed`) keeps per-duel records and mirrors the vectorized
ledger, but **resolution round is not an engine-agnostic observable**.
Outcome *after exactly h rounds* is — an unresolved duel counts as unresolved
in both drivers whatever internal ledger they keep — which is why the
round-truncation sweep replaced the histogram.

Empirical payoff: the orchestration defect this layer exists for — a downed
primary suppressing the standing opponent's reply attack — was invisible to
per-rule evidence and only showed up on whole-duel checks.

## L4 — the mutation survivor that paid for the harness

The engine-mutation catalogue (wound-ramp off-by-one, wound-impossible tail,
armour strength modifier, injury stun threshold, paired extra attack,
hit-much-weaker flip) started at 5/6 killed. The survivor,
`hit-much-weaker-flip`, survived because the exact-check inventory exercised
`vectorized.to_hit`, which delegates to the shared scalar, while the engine's
own duplicated `hit_targets` formula was untested. The check was rewritten to
drive the real operator, and all six mutants are now killed. This is the
concrete case behind the rule that a surviving mutant is a directive to add
one deterministic test, never a statistical pair.

## L3 — why "thousands of pairs" is the wrong lever, empirically

The statistical argument lives in the reference (±1.3 pp resolution per
100 000 oracle duels; rare branches invisible to any sample that fits in a
working day). The empirical history agrees: every real defect found so far —
the reply-phase suppression, the native port drifts, the automatic-wound
dice-stream shift — surfaced through **few deterministic cases designed for
coverage**, not through enumeration. Several "failing" pairs shared one root
cause. This is why the matrix stays curated at tens of pairs, each justified
by the interaction axis it adds.
