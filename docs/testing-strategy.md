# Testing strategy for the duel engines

How the repository maximizes confidence that the vectorized (NumPy) and native
engines behave exactly like the modular oracle — **without** spending the
compute that exhaustive pair-by-pair statistical certification would require.

The core decision behind this document: the statistical six-sigma layer is
**not** the primary guarantee that individual rules work, and it never can be.
Rule-level correctness is certified *deterministically*, cheaply and at
engine-code granularity; the statistical layer is demoted to what it can
actually see (interaction between rules and joint drift), and every expensive
pair must justify itself by covering something no deterministic test covers.

Read this with the [interaction matrix](interaction-matrix.md) (the rule-pair
coverage) and the [task guide for test reports](tasks/generate-test-reports.md)
(the commands that produce the certificates).

## Why "thousands of pairs" is the wrong lever

The statistical gate in `_statistical.py` accepts a divergence smaller than
≈ `6·√(2·p·(1−p)/N)` percentage points. With the typical oracle budget of
100 000 duels per engine and `p ≈ 0.5` that is **±1.3 pp**; halving the
resolution costs *four times* the duels, and the gate is capped by the smaller
sample — the oracle — so a new pair of 100k buys the same resolution as every
pair before it. A thousand pairs is ≈ 10⁸ oracle duels ≈ weeks of compute, to
keep resolving the same ±1.3 pp. Worse, any rare branch (`p < 10⁻³`) is
invisible to any sample that fits in a working day.

The empirical history agrees: every real defect found so far — the reply-phase
suppression, the native port drifts, the automatic-wound dice-stream shift —
surfaced through **few deterministic cases designed for coverage**, not
through enumeration. Several "failing" pairs shared one root cause.

So the strategy is layered. Each layer certifies something the layer above it
cannot see, and the expensive layers run rarely because the cheap ones already
carry the load.

## The layers

| Layer | Certifies | Artifacts / commands | Cost | Runs when |
| --- | --- | --- | --- | --- |
| L0 structure | KB + compiled fighters are well-formed and connected | `validate`, structural contract `tests/specs/structural/` | seconds | every change |
| L1 per-rule determinism | each rule behaves as written, both engines, exact distributions | semantic specs with scripted dice + exhaustive finite brute force; exact operator checks; native backend where exposed | seconds–minutes | every change |
| L2 whole-duel determinism | orchestration: acting order, reply phases, stateful timing | round-truncation outcome parity (`parity --truncations`); observed-mode samples | minutes | engine-touching changes |
| L3 interaction, statistical | joint behaviour of many rules over real archetype duels | 6σ marginal gate; deep archetype matrix; numpy↔native cross at scale | minutes–hours | certification, deep on demand |
| L4 engine-code coverage | no reachable engine line lacks a deterministic test; the tests can tell engines apart | coverage drift gate; engine mutation catalogue | ~3–10 min | engine-touching changes |
| L5 process | gates are run, certificates are versioned and reproducible | certificate schema, committed budgets, `--seed`, this document | n/a | every change |

L0 is documented in the [knowledge base guide](knowledge-base-guide.md) and the
verification-corpus README; this document focuses on L1–L5.

## Runtime budget: the expensive layers run rarely

> **Warning — long-running commands.** The certification tiers below take
> minutes to hours by design and are **not** part of the per-change loop.
> Their intent is *point certification*: run them occasionally, after large
> modifications (a new engine pass, a new archetype family, a release), when
> the drift they watch can actually have moved.
>
> | Command | Full run | Trimmed version for small checks |
> | --- | --- | --- |
> | `parity --deep --pair-set fast` (L3) | 30 pairs: ≈2.925M oracle duels + 1M cross duels/pair (target ≈10–15 min pooled) | `--deep-simulations 10000 --deep-cross-simulations 100000` |
> | `parity --deep --pair-set full` (L3) | 42 pairs: ≈4.05M oracle duels + 1M cross duels/pair (tens of minutes pooled; hours without pooling or with larger cross samples) | use `--pair-set fast` for the short loop |
> | `parity --truncations --pair-set fast` (L2) | 30 pairs × 8 horizons × 10k duels/engine (≈20–40 min sequential, ≈6–12 min pooled) | `--truncation-simulations 2000` |
> | `parity --truncations --pair-set full` (L2) | 42 pairs × 8 horizons × 10k duels/engine (≈28–55 min sequential, ≈8–15 min pooled) | use `--pair-set fast` for a smaller sweep |
> | `coverage-gate` (L4) | ≈3–10 min under `coverage` | run the deterministic suites directly (`pytest tests/combat/... tests/verification/test_parity.py -q`) |
> | `tools/mutate-engine.py` (L4) | full catalogue ≈3–5 min | `--mutant <name>` for the single defect under test |
> | `test-report` | whole semantic corpus + full `pytest` suite (minutes) | omit `--statistical`; or `pytest tests/verification/test_semantics.py -q` |
> | `benchmark --deep --pair-set fast` | vectorized grid over 30 coverage pairs, up to 5M duels | shrink the sizes (`--simulation-sizes 10k,100k`) or select one `--scenario` |
> | `benchmark --deep --pair-set full` | vectorized grid over all 42 pairs, up to 5M duels | use `--pair-set fast` for the short loop |
>
> A small change cannot escape the cheap layers — L1 pins every rule and
> every engine line deterministically — so the full certification adds
> nothing to the small-change loop. When a certification command is
> genuinely needed for a small check, prefer the trimmed version; the CLI
> warns when a trimmed matrix still leaves an expensive layer at its full
> size (e.g. the deep cross at its 1M default).

### L1 — deterministic per-rule evidence (both engines)

- The **semantic specifications** (`tests/specs/semantic/`) declare exact dice
  and decisions and compare the *distribution* the engines induce, computed by
  exhaustive finite enumeration where the domain is small enough (up to 6⁶
  rolls per case) — no sampling, no tolerance. Each case is replayed against
  the modular oracle *and* the vectorized engine with scripted rolls
  reordered by semantic role.
- The **exact operator checks** (`_vectorized.py` inventory, run by
  `test_vectorized_parity_inventory_is_complete_and_exact_checks_pass`) compare
  the engines field-by-field on small exhaustive domains: hit/wound 11×11,
  armour across strengths, injury 1..12, attack pools, priority, keyed-dice
  replay. These checks exercise the **engine's real operators** — a gap in the
  past let a check test a delegating helper while the duplicated projection
  was never exercised (see L4, `hit-much-weaker-flip`).
- Per-rule evidence is tied to the knowledge inventory by `verify`
  (617/617 obligations verified, 0 pending) and every rule-family mutation
  detected by at least one spec.

New rules land here first. This layer is why adding a rule does **not**
require adding a statistical pair.

### L2 — whole-duel orchestration, deterministically

Per-rule checks prove each rule fires correctly in isolation; they are weak
at proving the *duel driver* composes phases in the right order. The known
orchestration defect — a downed primary suppressing the standing opponent's
reply attack — was invisible to per-rule evidence and only showed up on whole
duels.

The **round-truncation outcome parity** (`_truncations.py`, CLI
`parity --truncations`) certifies the outcome distribution at every horizon
`h ∈ {2, 4, 6, 8, 10, 12, 15, 20}` on **every deep-matrix pair** (42
scenarios; previously only the five standard ones): both engines run the
pair with `maximum_rounds = h` and the three outcome rates
(first / second / unresolved) must stay inside the same six-sigma gate used
for full duels. A defect that shifts *when* duels resolve pushes one or more
horizon rows apart (rows are labelled `<scenario>@rounds=<h>`) while the
final aggregate marginals still agree — exactly the class of divergence the
aggregate gate cannot see. Default budget is 10 000 duels per engine,
scenario and horizon (`--truncation-simulations`); the oracle leg is shared
per horizon and poolable with `--workers`.

**Round-ledger caveat.** The first attempt compared per-duel *resolution
rounds* via a χ² over a winner×round histogram and diverged on the
`stateful` scenario while aggregate rates passed. Triage showed the 
divergence was a ledger-convention artifact: duels resolved by round-start
phases (fire, Force-of-Will sustain) are attributed to different round
numbers by each driver. The oracle's observed mode
(`simulate_duel_observed`) keeps per-duel records (winner, resolution round,
wounds, conditions) and mirrors the vectorized ledger, but **resolution round
is not an engine-agnostic observable**. Outcome *after exactly h rounds* is
— an unresolved duel counts as unresolved in both drivers whatever internal
ledger they keep — which is why the truncation sweep replaced the histogram.

### L3 — interaction, statistical, at scale

What remains for statistics is *interaction*: many rules composed over real
archetype duels, watched for joint drift. The 6σ marginal gate
(`--statistical`, `--deep`) compares first/second/unresolved rates on the
42-pair archetype matrix (glass cannons, brutes, elites, tanks, parry,
mechanics like regeneration-vs-fire, ward saves, entangle, and the
timing/parry amplifiers added 2026-09-05 — 4 hits vs one parry, a W1
stun stressor, a measurable-rate frenzy pair, the durable mirror and a
75-round heavy grind — plus skill consumers, helmet/injury-profile-2,
Cathayan Longsword, and the benchmark-only blessed-regeneration boundary)
plus the numpy↔native cross-certification at
1 000 000 duels/pair where the optimized engines make scale cheap and the
oracle is never touched. `--pair-set fast` is designed to retain the full
matrix's distinct effect-axis coverage in a smaller run; `--pair-set full`
adds the omitted baselines, mirrors and alternate matchup contexts. The pair
set applies only to the deep matrix and truncation sweep; the five-scenario
`--statistical` preset is unchanged.

Two properties keep this honest:

- the oracle sample is capped (`--max-modular-duels`), computed once and
  shared by every backend, and poolable across processes with bit-for-bit
  identical certificates (`--workers`, `MORDHEIM_PARALLEL_ORACLE_WORKERS`);
- the gate is deterministic in the seed: `--seed` fixes the streams, so a
  failure is reproducible.

A pair belongs in this layer only when it exercises an interaction axis no
deterministic case covers (see *When to add a pair*).

### Pair sets and current rule-coverage estimate

The deep tools expose two maintained views of the same matrix:

- **`fast` (30 pairs)** keeps one representative for each distinct mechanic
  family currently present in the full matrix, plus the timing/native-drift
  amplifiers and the eight coverage-completion probes. It intentionally removes
  baselines, mirrors and alternate matchup contexts, so it is the recommended
  10–15 minute certification loop.
- **`full` (42 pairs)** is the complete matrix. It adds the omitted baselines,
  mirrors and alternate contexts; these do not usually add a new rule family,
  but they are valuable for finding direction-dependent or composition bugs
  after substantial engine changes.

Both sets now exercise the **54 of 54 reachable compiled effect axes** identified
by the latest static reachability scan, or approximately **100% of this
executable rule-axis inventory**. The eight coverage-completion probes cover:
injury profiles 3/4; hit and wound rerolls, wound modifiers and attack bonuses;
incoming-strength modification; charge WS/Strength bonuses; first-round
bonuses; random characteristics; bear hug and caught-fire threshold; and
mundane-only ward/unmodified natural armour.

This is a statistical interaction estimate, not overall rule correctness or
Python line coverage. Deterministic semantic cases and operator checks remain
the authority for individual rules. Several probes use benchmark-only
trait/attack tags because the current catalogue has no legal selectable
producer; they do not modify the KB or engines. Because the simulator and KB
are being changed in parallel, re-run the reachability/fingerprint scan after
those changes settle before treating the percentage as a release metric. No
additional broad matchup variants are recommended until a new missing axis is
demonstrated.

### L4 — coverage gate and engine mutation

Two gates measure whether the deterministic corpus is *complete enough*,
which no amount of naming discipline can assert by itself.

**Coverage drift gate** (`coverage-gate`). The deterministic suites
(`tests/combat/modular`, `tests/combat/vectorized`,
`tests/combat/test_phases.py`, `tests/verification/test_parity.py`) run under
`coverage` and the result is compared against a committed budget
(`tests/fixtures/coverage/budget.json`, schema `mordheim-coverage-budget/v1`):
the ~2 500 engine statements that were exercised when the budget was written
(818 modular, 516 phases, 1 177 vectorized lines). The gate **fails when any
budgeted line stops being exercised** — a line became dead code, or its test
lost the path; both need a decision, not silence. Because the budget records
lines rather than percentages, refactors that move code do not fail
spuriously, while *new* engine code is simply not in the budget until the
author regenerates it:

```bash
python tools/mordheim-utils.py coverage-gate                      # check (drift gate)
python tools/update-coverage-budget.py                            # regenerate after adding tests
python tools/mordheim-utils.py coverage-gate --area-floor modular:95 --area-floor vectorized:93
```

The discipline is code first, deterministic evidence with it, budget
regenerated in the same change. `--area-floor AREA:PCT` optionally adds a
percentage floor so a brand-new area cannot start empty.

**Engine mutation harness** (`engine_mutation.py`,
`tools/mutate-engine.py`). Where the semantic specs mutate *rules* (proving
the specs detect rule defects), this harness mutates *engine code*: a
catalogue of single-token defects is applied to a staged copy of
`mordheim_combat` (the live tree is never touched), the deterministic
detector suites run against the stage, and the mutant is **killed** when at
least one test fails. A surviving mutant is a real gap — some reachable
engine decision has no deterministic test that can tell it apart from the
oracle — and every survivor is a directive to add one deterministic test,
**never** a statistical pair.

The catalogue (wound-ramp off-by-one, wound-impossible tail, armour strength
modifier, injury stun threshold, paired extra attack, hit much-weaker flip)
started at 5/6 killed. The survivor paid for itself immediately:
`hit-much-weaker-flip` survived because the exact-check inventory exercised
`vectorized.to_hit`, which delegates to the shared scalar, while the engine's
own duplicated `hit_targets` formula was untested. The check now drives the
real operator and all six mutants are killed:

```bash
python tools/mutate-engine.py                 # full catalogue (≈3–5 min)
python tools/mutate-engine.py --mutant wound-ramp-off-by-one --json   # one mutant
```

### L5 — process and certificates

- **Every change** touching the engines must leave green: unit suites,
  semantic specs, deterministic parity inventory, and `coverage-gate` — all
  of the deterministic suites at once with `tests --scope deterministic`
  (the same selection the coverage gate measures).
- **Engine-touching changes** additionally run `parity --truncations` — the
  `--level` presets of `parity` select the statistical/deep certification
  tiers, see [the report guide](tasks/generate-test-reports.md) — and, for
  vectorized/native code, the mutation catalogue.
- **Deep statistical runs** (`parity --deep`, hours) are certification runs,
  executed on demand or before a release — never the default loop. Because
  L1/L2/L4 already pin each rule and each engine line, the deep layer only
  watches interaction drift. See *Runtime budget* above for the trimmed
  versions to use when a small change still deserves a statistical check.
- Certificates are versioned. The parity certificate is schema
  `mordheim-combat-parity/v2`: it adds the `truncations` block (horizon rows
  with their own `complete` flag) and records top-level `elapsed_seconds`;
  statistical/deep rows carry engine-level wall times. Every certificate and
  budget pins its seed/suites so a reported divergence is reproducible.

## What each layer cannot see (and who covers it)

- Sampling noise hides branches rarer than ~10⁻³ even at deep scale → L1 exact
  enumeration and L2 truncation sweeps cover the deterministic cases; a rule
  with a genuinely rare branch needs a deterministic case, not more duels.
- L1 cannot see composition order across rules → L2 truncation rows and L3
  archetype pairs.
- L3 marginal rates cannot see *when* duels resolve → L2 truncations.
- Coverage alone cannot tell a *wrong* line from a *covered* line → L1 exact
  checks and L4 mutation catalogue.
- Two engines may share a wrong reading of a rule (oracle included) → L1
  specs are reviewed against the written sources, never against engine
  output; see the verification-corpus README.

## When to add a pair

Add a statistical pair only when it exercises an **interaction axis** no
deterministic case covers (a new combination of rule families over a legal
construction that L1/L2 do not compose), and prefer adding the deterministic
case that covers that axis instead whenever one exists. Keep the matrix
curated: each pair is justified by the axis it adds, triage is expected to
find root causes shared by several pairs, and the number of pairs converges
to tens — not to the combinatorics of all possible matchups.
