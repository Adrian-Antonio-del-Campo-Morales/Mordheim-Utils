# Verification

How the repository maximizes confidence that the vectorized (NumPy) and native
engines behave exactly like the modular oracle — **without** spending the
compute that exhaustive pair-by-pair statistical certification would require.

The core decision: the statistical six-sigma layer is **not** the primary
guarantee that individual rules work, and it never can be. Rule-level
correctness is certified *deterministically*, cheaply and at engine-code
granularity; the statistical layer is demoted to what it can actually see
(interaction between rules and joint drift), and every expensive pair must
justify itself by covering something no deterministic test covers.

## Modular integration closure

The [test classification reference](test-sequence.md) defines the phase
categories, assignment criteria and execution/repair dependencies, and the
`test-sequence` launcher implements that Python order. Successful selected
commands alone do not establish modular closure.

As of 2026-10-18, the admitted implementation queue is closed. This is
implementation disposition, not certification. The register itself is the
authority on admitted keys and pending work: read it through
`python -X utf8 tools/knowledge/clause_registry.py query --pending`, which
prints an empty list when no clause is pending. Catalogue contracts and
admission/kit corrections have focused evidence; integrated verification
remains outstanding.

Modular integration closure includes the E2E battery in
`tests/rules/integration/e2e/`: declared scenarios, coverage inventory and
accepted-evidence non-regression checks. Run it with
`python -m pytest tests/rules/integration/e2e -q` on the same integrated revision
as the other modular checks. Source-derived authoring and semantic review
remain separate from execution; static corpus validation alone is insufficient.

The multi-engine certification layers below are subsequent work. Modular closure
does not include optimized-backend parity, statistical or engine coverage
campaigns, NumPy/native implementation or optimized-port certification.

1. Run the existing modular, construction, modular semantic and modular E2E
   checks together on one integrated revision.
2. Include the relevant type, generated eligibility bundle, editorial contract
   and CSV conservation checks.
3. Group failures by cause and consumer. Fix each common admitted cause once;
   an older failure still counts if it prevents closure. Preserve positive tests
   and admission controls.
4. Rerun only affected groups after corrections, then run one final integrated
   confirmation on the delivered state. Preserve useful output rather than
   repeating unchanged checks.

Closure requires accessible configuration, correct compilation and consumption
for every admitted consequence, no known executable/composition defect, passing
applicable integrated checks including the modular E2E battery, and preserved
CSV keys and traceability. A binding,
closed row or test count alone proves none of these. Reuse existing tests; add
only missing discriminators for behaviour, limits, consumption, expiry or
composition. Record unresolved concrete defects in [the backlog](../../TODO.md).
A genuinely missing source must be identified exactly; do not invent a rule.

## The layers

| Layer | Certifies | Artifacts / commands | Cost | Runs when |
| --- | --- | --- | --- | --- |
| L0 structure | KB + compiled fighters are well-formed and connected | `verify --structural`, structural contract `tests/rules/integration/specs/structural/` | seconds | every change |
| L1 per-rule determinism | each rule behaves as written, both engines, exact distributions | semantic specs with scripted dice + exhaustive finite brute force; exact operator checks; native backend where exposed | seconds–minutes | every change |
| L2 whole-duel determinism | orchestration: acting order, reply phases, stateful timing | round-truncation outcome parity (`parity --truncations`); observed-mode samples | minutes | engine-touching changes |
| L3 interaction, statistical | joint behaviour of many rules over real archetype duels | 6σ marginal gate; deep archetype matrix; numpy↔native cross at scale | minutes–hours | certification, deep on demand |
| L4 engine-code coverage | no reachable engine line lacks a deterministic test; the tests can tell engines apart | coverage drift gate; engine mutation catalogue | ~3–10 min | engine-touching changes |
| L5 process | gates are run, certificates are versioned and reproducible | certificate schema, committed budgets, `--seed` | n/a | every change |

L0 is documented in [the KB guide](knowledge-base.md); this document focuses
on L1–L5.

## Runtime budget

Equipment and skill eligibility has its own cross-consumer checks:
`tests/rules/construction/fixtures/eligibility/decisions.json` is exercised by both
`tests/applications/warband_manager/domain/shared-eligibility.test.ts` and
`tests/rules/construction/test_shared_eligibility.py`. The latter runs the
actual embedded JavaScript, checks the bundle against a fresh generation,
parallel calls and recovery after a validation error. `npm run check:eligibility` rebuilds in memory and
rejects a stale checked-in bundle. Construction and application/UI suites prove
the adapters' behavior; these checks do not certify a choice's duel effect.

Both CI and `run-ci` include the bundle check and Python transport tests.

For phased integration, apply the
[existing construction boundary](eligibility.md#construction-boundary-for-phased-implementation).
Reuse accepted evidence whose inputs still match; revalidate affected adapters
and both consumers when a shared decision changes. A legal choice, an exactly-once
compiled effect and correct battle behavior require distinct evidence. F035
classifies historical construction findings against the current implementation;
it does not require rebuilding the shared module or repeating accepted Web phases.

Run deterministic suites for ordinary changes. Deep parity, truncation,
coverage mutation and benchmark matrices are certification jobs for engine
changes and releases; use their focused CLI options while developing. The
commands and current defaults are discoverable through
`python tools/mordheim-utils.py --help` and the relevant subcommand help.

## L1 — deterministic per-rule evidence (both engines)

- The **semantic specifications** (`tests/rules/integration/specs/semantic/`) declare exact dice
  and decisions and compare the *distribution* the engines induce, computed by
  exhaustive finite enumeration where the domain is small enough (up to 6⁶
  rolls per case) — no sampling, no tolerance. Each case is replayed against
  the modular oracle *and* the vectorized engine with scripted rolls
  reordered by semantic role.
- The **exact operator checks** (`_vectorized.py` inventory, run by
  `test_vectorized_parity_inventory_is_complete_and_exact_checks_pass`) compare
  the engines field-by-field on small exhaustive domains: hit/wound 11×11,
  armour across strengths, injury 1..12, attack pools, priority, keyed-dice
  replay. These checks exercise the **engine's real operators** — the exact
  checks must drive the engine's own code, not a delegating helper, so a
  duplicated projection cannot hide untested behavior (see L4).
- Per-rule evidence is tied to the knowledge inventory. Use
  `verify --inventory` for current obligations and gaps.

New rules land here first. This layer is why adding a rule does **not**
require adding a statistical pair.

## L2 — whole-duel orchestration, deterministically

Per-rule checks prove each rule fires correctly in isolation; they are weak
at proving the *duel driver* composes phases in the right order — a defect in
how phases are sequenced can leave every individual rule green.

The **round-truncation outcome parity** (`_truncations.py`, CLI
`parity --truncations`) certifies the outcome distribution at each configured
horizon on every selected deep-matrix pair: both engines run the pair with
`maximum_rounds = h` and the three
outcome rates (first / second / unresolved) must stay inside the same
six-sigma gate used for full duels. A defect that shifts *when* duels resolve
pushes one or more horizon rows apart (rows are labelled
`<scenario>@rounds=<h>`) while the final aggregate marginals still agree —
exactly the class of divergence the aggregate gate cannot see. The budget is
controlled by `--truncation-simulations`; the oracle leg is shared per horizon
and poolable with `--workers`.

**Round-ledger convention.** Resolution round is not an engine-agnostic
observable: duels resolved by round-start phases (fire, Force-of-Will
sustain) are attributed to different round numbers by each driver's ledger.
Outcome *after exactly h rounds* is engine-agnostic — an unresolved duel
counts as unresolved in both drivers — which is why the truncation sweep
compares outcomes at each horizon rather than resolution-round histograms.

## L3 — interaction, statistical, at scale

What remains for statistics is *interaction*: many rules composed over real
archetype duels, watched for joint drift. The 6σ marginal gate
(`--level statistical`, `--level deep`) compares first/second/unresolved rates on the
42-pair archetype matrix (glass cannons, brutes, elites, tanks, parry,
mechanics like regeneration-vs-fire, ward saves, entangle, the
timing/parry amplifiers — 4 hits vs one parry, a W1 stun stressor, a
measurable-rate frenzy pair, the durable mirror and a 75-round heavy grind —
plus skill consumers, helmet/injury-profile-2, Cathayan Longsword, and the
benchmark-only blessed-regeneration boundary) plus the numpy↔native
cross-certification at 1 000 000 duels/pair where the optimized engines make
scale cheap and the oracle is never touched. `--pair-set fast` is designed to
retain the full matrix's distinct effect-axis coverage in a smaller run;
`--pair-set full` adds the omitted baselines, mirrors and alternate matchup
contexts. The pair set applies only to the deep matrix and truncation sweep;
the five-scenario statistical preset is unchanged.

Two properties keep this honest:

- the oracle sample is capped (`--max-modular-duels`), computed once and
  shared by every backend, and poolable across processes with bit-for-bit
  identical certificates (`--workers`, `MORDHEIM_PARALLEL_ORACLE_WORKERS`);
- the gate is deterministic in the seed: `--seed` fixes the streams, so a
  failure is reproducible.

A pair belongs in this layer only when it exercises an interaction axis no
deterministic case covers (see *When to add a pair*).

### Pair sets and current rule-coverage estimate

- **`fast` (30 pairs)** keeps one representative for each distinct mechanic
  family currently present in the full matrix, plus the timing/native-drift
  amplifiers and the eight coverage-completion probes. It intentionally
  removes baselines, mirrors and alternate matchup contexts, so it is the
  recommended 10–15 minute certification loop.
- **`full` (42 pairs)** is the complete matrix. It adds the omitted baselines,
  mirrors and alternate contexts; these do not usually add a new rule family,
  but they are valuable for finding direction-dependent or composition bugs
  after substantial engine changes.

Both sets are curated to exercise every reachable compiled effect axis in the
executable rule-axis inventory; the live coverage figure is whatever the
reachability/fingerprint scan reports, not a number kept here. The eight
coverage-completion probes cover: injury profiles 3/4; hit and wound rerolls,
wound modifiers and attack bonuses; incoming-strength modification; charge
WS/Strength bonuses; first-round bonuses; random characteristics; bear hug and
caught-fire threshold; and mundane-only ward/unmodified natural armour.

This is a statistical interaction estimate, not overall rule correctness or
Python line coverage. Deterministic semantic cases and operator checks remain
the authority for individual rules. Several probes use benchmark-only
trait/attack tags because the current catalogue has no legal selectable
producer; they do not modify the KB or engines. No additional broad matchup
variants are recommended until a new missing axis is demonstrated.

## L4 — coverage gate and engine mutation

Two gates measure whether the deterministic corpus is *complete enough*,
which no amount of naming discipline can assert by itself.

**Coverage drift gate** (`coverage-gate`). The deterministic suites
(`tests/engines/modular`, `tests/engines/vectorized`,
`tests/engines/shared/test_phases.py`, `tests/engines/shared/test_duel_context.py`,
`tests/engines/shared/test_exact_phases.py`, `tests/engines/shared/test_interactions.py`,
`tests/engines/parity/test_duel_replay.py`, `tests/engines/parity/test_parity.py`) run under
`coverage` and the result is compared against a committed budget
(`tests/tooling/verification/fixtures/coverage/budget.json`, schema `mordheim-coverage-budget/v1`):
the engine statements that were exercised when the budget was written (the
committed file lists every line). The gate **fails when any
budgeted line stops being exercised** — a line became dead code, or its test
lost the path; both need a decision, not silence. The budget stores raw
statement line numbers, so moving code can also invalidate indexes. Compare
the budget-origin source with the current measured source before deciding
whether a reported loss is an actual missing witness or an index change.
New engine code is not budgeted until the author adds deterministic evidence
and regenerates the reviewed budget.

A measurement is valid only after pytest exits successfully. Failed tests,
collection/interruption/internal errors, invalid usage and empty collection
abort measurement. Both budget update entry points preserve their destination
when measurement fails. The CLI also preserves the destination when a requested
area floor fails during an update. The umbrella deterministic scope includes the same
context/replay suites as this gate.

After reviewing source movement and real witness gaps:

```bash
python tools/mordheim-utils.py coverage-gate                      # check (drift gate)
python tools/verification/update-coverage-budget.py                            # regenerate after adding tests
python tools/mordheim-utils.py coverage-gate --area-floor modular:95 --area-floor vectorized:93
```

The discipline is code first, deterministic evidence with it, budget
regenerated in the same change. `--area-floor AREA:PCT` optionally adds a
percentage floor so a brand-new area cannot start empty.

**Engine mutation harness** (`engine_mutation.py`,
`tools/verification/mutate-engine.py`). Where the semantic specs mutate *rules* (proving
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
is fully killed — every mutant is detected. A survivor is not a bug in the
harness: it exposes an untested engine decision, and the response is always a
deterministic test that can tell the two versions apart:

```bash
python tools/verification/mutate-engine.py                 # full catalogue (≈3–5 min)
python tools/verification/mutate-engine.py --mutant wound-ramp-off-by-one --json   # one mutant
```

## L5 — process and certificates

- **Every change** touching the engines must leave green: unit suites,
  semantic specs, deterministic parity inventory, and `coverage-gate` — all
  of the deterministic suites at once with `tests --scope deterministic`
  (the same selection the coverage gate measures).
- **Engine-touching changes** additionally run `parity --truncations` — the
  `--level` presets of `parity` select the statistical/deep certification
  tiers, see [Develop and release](../guides/develop-and-release.md) — and,
  for vectorized/native code, the mutation catalogue.
- **Deep statistical runs** (`parity --level deep`, hours) are certification
  runs, executed on demand or before a release — never the default loop.
  Because L1/L2/L4 already pin each rule and each engine line, the deep layer
  only watches interaction drift.
- Certificates are versioned. The parity certificate is schema
  `mordheim-combat-parity/v2`: it adds the `truncations` block (horizon rows
  with their own `complete` flag) and records top-level `elapsed_seconds`;
  statistical/deep rows carry engine-level wall times. Every certificate and
  budget pins its seed/suites so a reported divergence is reproducible.

## Renewed statistical scenario battery

`parity --profile quick|complete|deep` runs the scenario catalogue of
`mordheim_combat_lab.verification.parity._battery_cases` and compares the
terminal outcome distributions of the modular oracle and the selected candidate.
Profiles are cumulative by case id (`quick` ⊆ `complete` ⊆ `deep`). Each case
declares origin, variant, fighters, context, decisions, sample width, seed and
horizon; it is executed by both real engines, never by delegating one to the
other.

```bash
# minimal battery (11 prepared cases; execution evidence is separate)
python -X utf8 tools/mordheim-utils.py parity --profile quick --output outputs/parity/battery-quick.json

# both candidates, per-backend coverage
python -X utf8 tools/mordheim-utils.py parity --profile complete --backend all --output outputs/parity/battery-complete.json

# markdown certificate and strict gate
python -X utf8 tools/mordheim-utils.py parity --profile deep --output outputs/parity/battery-deep.md --require-complete

# smaller sample width for calibration, never for acceptance
python -X utf8 tools/mordheim-utils.py parity --profile quick --rows 256 --output outputs/parity/battery-quick-256.json

# 1000 duels per case, up to 10 modular-oracle worker processes
python -X utf8 tools/mordheim-utils.py parity --profile quick --backend numpy --rows 1000 --workers 10 --output outputs/parity/battery-quick-1000.json
```

`--workers N|auto` also applies to all three profiles. It partitions each
modular sample into contiguous `seed + i` ranges, preserves terminal row order
and reuses one process pool across cases. `1` stays sequential; explicit counts
are capped to available CPUs, and `auto` uses the historical cost threshold.
Candidate batches are unchanged, and `--backend all` still shares the modular
sample between candidates. The report records `oracle_workers_requested` as
the requested policy, not a claim that every case used that many processes.

The comparison is statistical. `winner` (first win, second win, unresolved) is
always compared with the six-sigma tolerance shared with the historical
certificate (`_statistical.six_sigma_tolerance`, floor 0.25%). `rounds`,
`wounds` and `condition` are added when the case declares them, because both
sampling paths already publish those distributions. Internal counters, typed
witnesses, activation flags, equipment hashes and checkpoints are **not**
required: `expect`, `positive_control` and `witness_value` remain declaration
data and never gate execution or approval.

A real input limit is still a limit: a supplied state or preparation the current
API cannot express (`blocked_by="state:…"`) or a per-row decision script
(`decision:per-row`) makes the case `INCOMPATIBLE` with its cause and keeps it in
the profile denominator. It is never executed as a different scenario. The
certificate lists those limits (`limits`), so a partial run cannot be read as
complete coverage.

The reviewed catalogue declares 122 cases (11 exclusive to `quick`, 103 to
`complete`, 8 to `deep`; cumulative 11/114/122). 118 are prepared by static
reading of the catalogue, the compiler and both consumers; four keep a real
limit. `c03-petru-potion` needs a campaign-only potion table the KB marks out of
scope; `v01-restriction` needs a charge the construction rejects before any
sample exists; and `v14-handler`/`v14-handler-absent` need an engine change: the
canonical bear-and-tamer build auto-exempts the bear's Stupidity inside the
handler radius and its Fear test never occurs because the bear itself causes
Fear, so the handler branch has no test left to lend to. The `deep` profile composes already
justified situations (fear → charge → parry, leadership → psychology, extra
attacks → defensive capacity, armour → parry, order → attacks and reactions →
injury) and adds no new rule material.

`--backend` defaults to `numpy`. `native` never falls back to NumPy: a missing,
stale or unsupported extension is `NOT_RUN:native-*` and never a comparison.
`--backend`/`--rows` without `--profile` and `--rows` with `--require-complete`
are rejected with code 2; the historical route without `--profile` is unchanged.

The certificate is schema `mordheim-combat-parity-battery/v3`. Per case it
records the stages actually reached — `executed` (both samples obtained),
`compared` (at least one magnitude compared) and `approved` (all magnitudes
within tolerance) — plus every `comparisons[]` entry with the modular and
candidate rates and tolerances. `coverage` aggregates `declared`, `case_ids`,
`prepared` (no real input limit), `executed`, `compared`, `approved`,
`divergent`, `incompatible`, `not_run`, `errors`, `dependency` and
`sensitivity_pending`. `magnitudes` reports how many comparisons of each
magnitude stayed within tolerance, and `variants`/`clauses` keep the same stages
per variant and canonical clause.

Own errors (`NOT_RUN:compile`, `NOT_RUN:decision-script`,
`NOT_RUN:case-definition`, `NOT_RUN:outcome-codes`, an unexpected exception, a
batch-shape or determinism failure and any divergence) make the command exit 1
**even without `--require-complete`**. Real input limits and an absent backend are dependencies:
they leave the run partial and only `--require-complete` turns that into a
failure. The CLI and the report share one classification
(`battery_failure_kind`), so a bucket cannot contradict the exit code.

Each engine's winner convention is validated before normalisation (oracle
`0/1/2`, candidate `1/-1/0`). A code outside its own convention is malformed
data: the case is `NOT_RUN:outcome-codes`, an own error, and the code never
enters the unresolved category or disappears from the sample.

A case names a printed rule in `special_rule_ids` (a band rule id for a
band/profile build, any rule id of the collection for a free build); an effect
id such as `trait.flammable` is not a rule and is refused. Supplied traits
(`concussion_immune`, `poison_immune`, `injury_profile`, `frenzy`, …) travel in
`trait_overrides`, and hand-held defences (`defence.shield`,
`defence.buckler`) occupy `off_hand_id`, not `defence_ids`.

`sensitivity` is reported as pending for every case: a statistical PASS compares
outcome distributions, it does not prove that a rule changes them. The
with/without-rule contrast over the oracle belongs to the later campaign, and
`complete`/`accepted` are execution semantics over the required scenarios of the
profile, not semantic coverage of every internal rule.

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
  output; see `tests/rules/integration/specs/README.md`.

## Why "thousands of pairs" is the wrong lever

The statistical gate in `_statistical.py` accepts a divergence smaller than
≈ `6·√(2·p·(1−p)/N)` percentage points. With the typical oracle budget of
100 000 duels per engine and `p ≈ 0.5` that is **±1.3 pp**; halving the
resolution costs *four times* the duels, and the gate is capped by the smaller
sample — the oracle — so a new pair of 100k buys the same resolution as every
pair before it. A thousand pairs is ≈ 10⁸ oracle duels ≈ weeks of compute, to
keep resolving the same ±1.3 pp. Worse, any rare branch (`p < 10⁻³`) is
invisible to any sample that fits in a working day.

In practice, deterministic cases designed for coverage expose defects more
efficiently than broad enumeration.

## When to add a pair

Add or reuse a statistical scenario when it represents a rule variant, boundary
or interaction missing from the selected catalogue and can affect measured duel
outcomes. Existing deterministic coverage does not replace statistical execution
of the selected scenario. Prefer material with/without-rule contrasts where
useful, record sensitivity limits and avoid the Cartesian product of matchups.
Keep the matrix curated by justified behaviour, without a fixed scenario quota.

## Reports and the interaction matrix

`report tests` writes Excel-friendly CSVs (`outputs/test-report/`);
`parity` saves versioned certificates (`outputs/parity/`); options, statuses
and presets are documented in [Develop and release](../guides/develop-and-release.md).

The **interaction matrix** — how every required interaction pair of the
verification gate is closed — is documented per cluster in the verification
corpus README (`tests/rules/integration/specs/README.md`): the nine cluster files of
`tests/rules/integration/specs/semantic/interactions/`, the authoring recipe (one spec per pair
with composition + boundary cases, strict dice, ≥1 detected mutation) and the
10 reviewed `illegal` overrides in `tests/rules/integration/specs/interaction-policy.yaml`
(body-armour × body-armour pairs that can never co-occur in legal
construction). The matrix is complete — run `python tools/mordheim-utils.py
verify --inventory` for the live status (required interactions covered,
pending, divergences); the executable reports are the source of truth, not a
number written here.

## Local context and strict engine replay

The local-context contract documents optional
local participant IDs, numeric M/Ld preservation, explicit distances/contact, and
independent charge/player-turn facts. Use `prepare_duel_context` in both production
and verification; missing required facts must fail rather than become defaults.
Combat Lab shares canonical KB data and the pure eligibility module with Warband
Manager; campaign state/services and combat execution remain independent.

For a small deterministic whole-duel proof, use
`mordheim_combat_lab.verification.parity.replay_duel`. It exercises the
actual modular, NumPy or compiled native driver with strict, fully consumed dice
and decisions, then records terminal state/resources. Author each backend's legacy
physical draw order explicitly; do not assume equal seeds imply equal streams.
Native replay requires a rebuilt context-aware extension and never falls back.
The foundation cases live in `tests/engines/parity/test_duel_replay.py`; new
mechanisms still need source-derived specifications, interactions and mutations.
