# Verification

The modular engine is the rule reference: source-derived checks in
`tests/engines/modular/mechanics/` verify rules, and
`tests/integration/e2e/` verifies the KB/compiler/modular path. Each engine's
`runtime/` checks simulator contracts. Statistical parity compares NumPy and
native with the modular oracle.

The semantic YAML test runner and NumPy per-operation adapters are retired.
There is no second semantic authoring or certification system. This change
does not establish that current mechanics/E2E coverage is complete or that any
unexecuted tests pass. Structural audits, corpus contracts and evidence records
remain separate from behavioural proof.

## Engine test fixtures

Tests are grouped under `tests/engines/{modular,vectorized,native,shared,parity}`;
KB, construction and integration checks live under `tests/knowledge`,
`tests/construction` and `tests/integration`, respectively, and retain
access to the compiler and source indexes.

`tests/engines/fixtures/compiled-cases.json` stores execution cases; its
`compiled-cases.manifest.json` records provenance and consumer mappings.
`tools/verification/compiled_cases.py` loads them without automatic recompilation.
The exporter is `tools/knowledge/export_compiled_cases.py`.

`tests/engines/fixtures/compiled-builds.json` stores compiled fighters keyed by
the complete `FighterBuild` and normalized root. Load it through
`tools/verification/compiled_builds.py`; modular and vectorized tests use the
session fixture `compiled_builds` and its `fighter(build, root)` callable.
Preserve all original builder arguments and subsequent transformations. Missing
entries fail explicitly.
Regenerate with `python tools/verification/generate_compiled_builds.py --write`;
the generator preserves existing frozen entries and adds newly captured builds.
Use a single writer for each generated document.

Deliberate compilation rejections live in `tests/construction/` and keep the
real compiler; combat assertions stay in the modular mechanics suite.
No import or file-access blocking instrumentation is required.

These are two independent formats: cases preserve scenario roles and execution
metadata; build snapshots cache the result for a complete build request. Keep
original arguments, `None` versus empty sequences and post-compilation transforms
unchanged when replacing preparation. Never substitute a similar fighter or
weaken an assertion to satisfy a missing key. Generate a missing entry explicitly
from its original build; intentional compiler rejections are not missing snapshots.
The case exporter is a Python API (`export_cases`), not a command-line generator.
Snapshot generation preserves existing entries; it does not automatically refresh
frozen results after a KB/compiler change. Review any intended data update explicitly.

A fixture update may read the KB; an ordinary engine test loads the checked-in
results. `check verify`, `check parity`, `performance benchmark` and
`performance calibrate` retain their application CLI defaults and may still compile scenarios. Their tests using fixtures do not
imply those commands have switched to precompiled input.

To smoke-test the connection without a statistical campaign:

```powershell
python -u -m pytest tests/engines/vectorized/runtime/test_parallel_numpy.py::test_single_batch_samples_are_unchanged_by_the_parallel_path -v --tb=short
python -u -m pytest tests/engines/native/test_native_engine.py::test_native_accumulates_counts_across_batches -v --tb=short
```

Keep these runs serial: the NumPy sample uses its own worker pool. A native skip
does not prove native execution. Successful samples establish the file-to-backend
connection for those paths; they do not certify every fixture or pending rule.
Classify missing keys, bad deserialization and wrong participant bindings as
preparation defects before interpreting engine output differences.

Migration verification on 2026-10-23: integrated collection completed, both
workspace typechecks passed, manual modular/shared runs (including the
parallel-oracle checks) passed, and focused NumPy sequential/parallel and native
batch-accumulation checks passed using precompiled inputs. These connection
checks do not certify unimplemented optimized-engine rules.

## Modular integration closure

Successful selected commands alone do not establish modular closure.

As of 2026-10-18, the admitted implementation queue is closed. This is
implementation disposition, not certification. The register itself is the
authority on admitted keys and pending work: read it through
`python -X utf8 tools/knowledge/clause_registry.py query --pending`, which
prints an empty list when no clause is pending. Catalogue contracts and
admission/kit corrections have focused evidence; integrated verification
remains outstanding.

Modular integration closure includes the E2E battery in
`tests/integration/e2e/`: declared scenarios, coverage inventory and
accepted-evidence non-regression checks. Run it with
`python -m pytest tests/integration/e2e -q` on the same integrated revision
as the other modular checks. Source-derived authoring and semantic review
remain separate from execution; static corpus validation alone is insufficient.

The multi-engine certification layers below are subsequent work. Modular closure
does not include optimized-backend parity, statistical or engine coverage
campaigns, NumPy/native implementation or optimized-port certification.

1. Run the existing modular, construction and modular E2E
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

## Verification responsibilities

| Responsibility | Owned checks | What a passing result establishes |
| --- | --- | --- |
| KB and construction | `tests/knowledge/`, `tests/construction/`, structural `verify` | Data contracts, admission and compiled representation for the checked inputs. |
| Modular rules | `tests/engines/modular/mechanics/` | Source-defined consequences and relevant boundaries of the reference implementation. |
| Connected pipeline | `tests/integration/e2e/` | Configuration, real compilation and observed modular execution agree for the declared scenario. |
| Simulator operation | Each engine's `runtime/` and shared contracts | Execution, context, reproducibility and lifecycle guarantees. |
| Optimized-engine equivalence | Statistical parity and truncation scenarios | Observed distributions agree within the declared tolerances and sample limits. |
| Test infrastructure | Tooling, corpus contracts and coverage checks | The specified measurement/detection mechanism works; no blanket rule certificate. |

Run only the validation authorized for the change. Large batteries and
certification campaigns are separate work, not an automatic consequence of
editing a rule.

## Runtime budget

Equipment and skill eligibility has its own cross-consumer checks:
`tests/construction/fixtures/eligibility/decisions.json` is exercised by both
`tests/applications/warband_manager/domain/shared-eligibility.test.ts` and
`tests/construction/test_shared_eligibility.py`. The latter runs the
actual embedded JavaScript, checks the bundle against a fresh generation,
parallel calls and recovery after a validation error. `npm run check:eligibility` rebuilds in memory and
rejects a stale checked-in bundle. Construction and application/UI suites prove
the adapters' behavior; these checks do not certify a choice's duel effect.

Both CI and `check ci` include the bundle check and Python transport tests.

For phased integration, apply the
[existing construction boundary](eligibility.md#construction-boundary-for-phased-implementation).
Reuse accepted evidence whose inputs still match; revalidate affected adapters
and both consumers when a shared decision changes. A legal choice, an exactly-once
compiled effect and correct battle behavior require distinct evidence. F035
classifies historical construction findings against the current implementation;
it does not require rebuilding the shared module or repeating accepted Web phases.

Run affected deterministic files or node IDs for ordinary changes; broad
selections such as `tests modular` are not a per-edit default. Deep parity, truncation,
coverage and benchmark matrices are certification jobs for engine
changes and releases; use their focused CLI options while developing. The
commands and current defaults are discoverable through
`python tools/mordheim-utils.py --help`, the group help and
`tests <selection> --help`.

## Deterministic modular evidence

Mechanics tests state expectations from the written rule, not from engine
output. Use explicit dice and decisions for local results and short sequences
for stateful interactions. Cover activation, non-activation, limits, resource
consumption, expiry and relevant composition in the owning tests.

E2E cases exercise actual KB/compiler/modular integration. Their declaration,
coverage and accepted-evidence checks are useful but not behavioural proof by
themselves: the scenarios must also be executed successfully.

Structural verification is reached through `check verify` (the application's
`verify` command). It checks the editorial and execution contracts, validates
binding contracts and compiles every band profile with its default
construction. It is a structural gate; the modular mechanics and E2E suites
own rule behaviour.

The cross-engine deterministic replay suite was retired; each engine keeps its
own deterministic replay and operator checks, and optimized engines remain
compared through the statistical scenarios. These checks are not the retired
semantic adapter system.

## Simulator and whole-duel checks

Runtime tests distinguish seeded reproducibility, cancellation, batch totals,
parallel execution and observation. The modular total-only and observed paths
must agree on the same inputs; their purpose is simulator consistency, not a
second rule implementation.

`parity --truncations` compares outcome distributions at several round horizons.
It is a statistical comparison, even when fixed seeds make its runs reproducible.
It can reveal timing drift hidden by final aggregate totals; it does not replace
source-derived mechanics expectations.

## L3 — interaction, statistical, at scale

Statistics compare optimized-engine behaviour with the modular reference over
curated archetype duels, covering rule variants and their interactions. The 6σ marginal gate
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

Choose pairs for meaningful rule variants, boundaries and interactions, not
for the Cartesian product of all profiles (see *When to add a pair*).

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
Python line coverage. Source-derived modular mechanics and E2E assertions remain
the authority for individual rules. Several probes use benchmark-only
trait/attack tags because the current catalogue has no legal selectable
producer; they do not modify the KB or engines. No additional broad matchup
variants are recommended until a new missing axis is demonstrated.

## L4 — coverage gate

The coverage gate measures whether the deterministic corpus is *complete
enough*, which no amount of naming discipline can assert by itself.

**Coverage drift gate** (`python -m mordheim_combat_lab coverage-gate`, wrapped as
`check coverage`). The engine and parity smoke suites
(`tests/engines/modular`, `tests/engines/vectorized`,
`tests/engines/shared/contracts/test_duel_context.py`,
`tests/engines/native/runtime/test_duel_context.py`,
`tests/engines/native/runtime/test_duel_replay_native.py`,
`tests/tooling/parity/test_runner.py`,
`tests/engines/parity/statistical/test_parity_statistics.py`) run under
`coverage` and the result is compared against a committed budget
(`tests/tooling/coverage/fixtures/budget.json`, schema `mordheim-coverage-budget/v1`):
the engine statements that were exercised when the budget was written; the
committed file records the covered statement lines per module. The gate **fails when any
budgeted line stops being exercised** — a line became dead code, or its test
lost the path; both need a decision, not silence. The budget stores raw
statement line numbers, so moving code can also invalidate indexes. Compare
the budget-origin source with the current measured source before deciding
whether a reported loss is an actual missing witness or an index change.
New engine code is not budgeted until the author adds deterministic evidence
and regenerates the reviewed budget.

A measurement is valid only after pytest exits successfully. Failed tests,
collection/interruption/internal errors, invalid usage and empty collection
abort measurement. The CLI preserves its destination when measurement fails,
and also when a requested area floor fails during an update. The engine
directories this gate measures are also covered by `tests modular` and
`tests vectorized`; the parity runner self-check is `tests parity tooling` and
must be selected separately.

After reviewing source movement and real witness gaps:

```bash
python tools/mordheim-utils.py check coverage                      # check (drift gate)
python tools/mordheim-utils.py check coverage --update-budget      # regenerate after adding tests
python tools/mordheim-utils.py check coverage --area-floor modular:95 --area-floor vectorized:93
```

The discipline is code first, deterministic evidence with it, budget
regenerated in the same change. `--area-floor AREA:PCT` optionally adds a
percentage floor so a brand-new area cannot start empty.

## Process and certificates

Keep executed evidence tied to revision, inputs, suites, seeds and sample sizes.
A successful static check, collection or export is not a passing functional
result. A skipped native extension is not native execution. An empty admission
ledger or matching inventory count is not behavioural certification.

Use focused checks for routine changes, reuse valid results and record unresolved
concrete defects in `TODO.md`. Run broad statistical/deep certification only when
explicitly requested. Never refresh a coverage budget, fingerprint or generated
report merely to hide lost evidence.

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
python -X utf8 tools/mordheim-utils.py check parity --profile quick --output outputs/parity/battery-quick.json

# both candidates, per-backend coverage
python -X utf8 tools/mordheim-utils.py check parity --profile complete --backend all --output outputs/parity/battery-complete.json

# markdown certificate and strict gate
python -X utf8 tools/mordheim-utils.py check parity --profile deep --output outputs/parity/battery-deep.md --require-complete

# smaller sample width for calibration, never for acceptance
python -X utf8 tools/mordheim-utils.py check parity --profile quick --rows 256 --output outputs/parity/battery-quick-256.json

# 1000 duels per case, up to 10 modular-oracle worker processes
python -X utf8 tools/mordheim-utils.py check parity --profile quick --backend numpy --rows 1000 --workers 10 --output outputs/parity/battery-quick-1000.json
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

The catalogue in `_battery_cases.py` is the authority on case counts; the
certificate's `coverage` block reports the declared, prepared, executed and
approved totals of the run. Profiles are cumulative: `quick` is the small
regression set, `complete` adds the bulk of the catalogue, and `deep` adds its
own long-horizon and interaction cases (fear → charge → parry, leadership →
retest, extra attacks → defensive capacity, armour → parry, order → attacks and
spines → injury). Two cases keep a real input limit. `c03-petru-potion` needs a
campaign-only potion table the KB marks out of scope, and `v01-restriction`
needs a charge the construction rejects before any sample exists. Both remain in
the profile denominator as `INCOMPATIBLE` with their cause.

`--backend` defaults to `numpy` for a profile. `native` never falls back to
NumPy: a missing, stale or unsupported extension is `NOT_RUN:native-*` and never
a comparison. A battery `--backend` is valid only with `--profile`; on the
historical route it is accepted only with `--level statistical` and no
`--truncations`. `--rows` requires `--profile` and is rejected together with
`--require-complete`. These configuration errors exit with code 2.

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

## Limits of the evidence

Statistical agreement does not prove the source interpretation: modular mechanics
and E2E expectations must be reviewed against the written rules and adopted
rulings. Rare branches may require a focused modular test rather than more random
sampling. Conversely, deterministic modular checks do not prove optimized-engine
equivalence: the selected statistical scenarios must actually run on both engines.

Coverage records execution paths, not correct answers. Corpus inventory records
scenario references, not passing scenarios. Keep declarations, preparation,
execution and acceptance distinct in every report.

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

## Reports

`check report tests` writes technical test results and, when requested, statistical
comparison rows under `outputs/test-report/`. It does not run or approve a
semantic YAML corpus. `check parity` writes versioned statistical certificates under
`outputs/parity/`; `check report rules` exports structural/planning inventory without
claiming new semantic verification. Legacy semantic columns in existing CSVs
are historical fields, not current certificates.

The retired interaction-specification matrix and its policy file no longer gate
verification. Rule interactions belong to modular mechanics/E2E and the curated
statistical scenario catalogue. Adopted decisions remain in
[design-rulings.md](../decisions/design-rulings.md).

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
The native replay cases live in
`tests/engines/native/runtime/test_duel_replay_native.py`; new
mechanisms are specified and checked in modular mechanics/E2E tests, with
statistical scenarios for optimized-engine comparison.
