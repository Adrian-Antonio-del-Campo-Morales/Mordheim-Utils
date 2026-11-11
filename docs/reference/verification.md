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
frozen results after a KB/compiler change. It records a fingerprint of the KB
and compiler sources and prints a provenance warning when frozen entries were
compiled from other sources; it exits 1 on compile failures or blocked
consumers. Review any intended data update explicitly.

A fixture update may read the KB; an ordinary engine test loads the checked-in
results. `check verify`, `check parity`, `performance benchmark` and
`performance calibrate` retain their application CLI defaults and may still compile scenarios. Their tests using fixtures do not
imply those commands have switched to precompiled input.

To smoke-test the connection without a statistical campaign:

```powershell
python -u -m pytest tests/engines/vectorized/runtime/test_parallel_numpy.py::test_single_batch_samples_are_unchanged_by_the_parallel_path -v --tb=short
python -u -m pytest tests/engines/native/test_native_engine.py::test_native_accumulates_counts_across_batches -v --tb=short
```

Engine tests can run together with `-n 6 --dist=load`. Ordinary checks sample
sequentially; tests of concurrency retain real pools capped at two workers.
Collection remains serial. A native skip does not prove native execution. Successful samples establish the file-to-backend
connection for those paths; they do not certify every fixture or pending rule.
Classify missing keys, bad deserialization and wrong participant bindings as
preparation defects before interpreting engine output differences.

## Engine and parity test selection

`tests/engines/modular`, `vectorized` and `native` check each engine's own
behavior. `shared` checks common contracts and frozen inputs. Modular tests
do not require another backend to reject a supported rule.

`tests/engines/parity/statistical` contains statistical comparisons and the
catalogue, report and sample-store checks that support them. There is no
separate deterministic parity suite. The launcher selects these tests with
`python tools/mordheim-utils.py tests parity statistical -n 6 --dist=load -q`.
This selection is not the complete large-sample certification campaign.

For campaigns using saved modular references, use `check samples`
(`tools.verification.parity_samples`): `sample --backend numpy` or
`sample --backend native` stores candidate batches, then `compare` reads the
candidate store and the modular `--reference-store` without rerunning the
oracle. Samples record inputs, seeds, round limits, the source digest of
everything each engine executes, the source commit, the dirty state and the
native build. Reusing samples from older engines is expected: every provenance
difference is reported as a prominent warning and recorded in the report, but
never blocks a comparison. A historical reference is still not evidence about
the current engine. See [the tools reference](tools.md) for sampling and
comparison commands.

## E2E statistical deliveries

`tools/verification/e2e_parity.py` discovers and validates the frozen inputs for
[E2E statistical campaigns](tools.md#e2e-statistical-campaigns). Deliveries live in
`tests/engines/fixtures/e2e-statistical-deliveries/<sha256(case_key UTF-8)>.json`.
Their keys are `e2e/<audit_id>/<id>` and their source test identifiers are
`audit_id::id`. See the [encoded example](../examples/e2e-statistical-parity.json).

Each document contains exactly these fields:

| Field | Contract |
|---|---|
| `schema` | `mordheim-e2e-statistical-delivery/v1`. |
| `status` | `translated`, `blocked` or `not-applicable`. |
| `source` | Exactly `revision` (preparation commit), `path` (repository-relative YAML), `sha256` (YAML bytes) and `test_id`. |
| `case_key` | The E2E key matching `source.test_id`. |
| `case` | `compiled_cases.encode_case` output for translated entries; otherwise `null`. |
| `decision_policy` | `{"kind":"engine-default"}` for translated entries; otherwise `null`. |
| `magnitudes` | `["winner"]`; campaigns may optionally add `rounds`. |
| `reason` | `null` for translated entries; otherwise a concrete, nonempty reason. |

Preparation preserves both compiled fighters, complete context including local
participants, auxiliary participants, initial state and synthetic labels where
present. Reuse a frozen entry only after checking correspondence with the current
YAML; otherwise prepare it with the existing `export_cases` API. Compilation is
preparation work, not part of statistical execution. Missing fighters or inputs
must not be invented or simplified to make a case admissible.

Translated cases have current E2E origin metadata, empty `determinism.dice` and
`determinism.decisions`, null `expectations` and `benchmark`, and only
`maximum_rounds` in `limits`. That stored limit preserves the original E2E value
(1 when omitted); campaigns independently use 50 rounds by default. Seeds,
simulation counts, chunk sizes and workers are execution settings.
Recalculate fingerprints with `encode_case` and check an exact codec round trip,
identity and the current YAML hash. A matching key alone does not prove freshness.

Explicit scripted decisions are blocked until a general policy for random
trajectories is supported; removing the script does not prove equivalence with
`engine-default`. Admission checks that the engines' default decision policies
correspond; a probe that fails or finds them disagreeing fails the run, because
no case could be compared. Expected construction refusals are `not-applicable`; expected runtime
refusals and unrepresentable input data are `blocked` pending review. An unexpected
exporter error is not evidence of a construction refusal.

The shared execution path currently cannot express `initial_state` overrides or
`auxiliary_participants`; those inputs remain `incompatible` with a concrete reason.
A run that compares no case exits non-zero unless every selected case is
blocked or not-applicable, and delivery discovery defects fail it too.
Stale source hashes and invalid documents cannot execute. `translated` describes
prepared data, not engine compatibility, correct original E2E expectations or
approved statistical parity. No engine fallback or partial execution may conceal
unsupported inputs.

## Modular integration closure

Successful selected commands alone do not establish modular closure.

The knowledge base is the inventory of obligations (see
[Identities and clauses](knowledge-base.md#identities-and-clauses)). Inspect
the ones no scenario or `covers` marker names yet with
`python tools/knowledge/clauses.py coverage --pending`. An empty queue does not
certify runtime behavior or engine parity.

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
consumption, expiry and relevant composition in the owning tests. Declare the
knowledge-base identity a test demonstrates with
`@pytest.mark.covers("<identity>")`, adding the clause ids when the identity
is split into clauses, so `python tools/knowledge/clauses.py coverage` counts
it next to the E2E scenarios; the marker is a declaration, never proof. The
observable the test checks belongs in the test's docstring, not in the
knowledge base.

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

`check parity --rounds 2,4,8,15` compares outcome distributions at several round horizons.
It is a statistical comparison, even when fixed seeds make its runs reproducible.
It can reveal timing drift hidden by final aggregate totals; it does not replace
source-derived mechanics expectations.

## L3 — interaction, statistical, at scale

Statistics compare optimized-engine behaviour with the modular reference over
curated archetype duels, covering rule variants and their interactions. The 6σ marginal gate
(`check parity --scenarios ...`, or `check samples compare` on stored samples)
compares first/second/unresolved rates on the
42-pair archetype matrix (glass cannons, brutes, elites, tanks, parry,
mechanics like regeneration-vs-fire, ward saves, entangle, the
timing/parry amplifiers — 4 hits vs one parry, a W1 stun stressor, a
measurable-rate frenzy pair, the durable mirror and a 75-round heavy grind —
plus skill consumers, helmet/injury-profile-2, Cathayan Longsword, and the
benchmark-only blessed-regeneration boundary). A numpy↔native cross-check at
scale never touches the oracle: sample both candidates with `check samples
sample` and compare them with `check samples compare --backend native
--reference numpy`. `--scenarios normal` is designed to retain the whole
matrix's distinct effect-axis coverage in a smaller run; `--scenarios big`
adds the omitted baselines, mirrors and alternate matchup contexts.

Two properties keep this honest:

- the oracle sample is computed once per case and shared by every candidate,
  and poolable across processes with bit-for-bit identical totals
  (`--workers`, `MORDHEIM_PARALLEL_ORACLE_WORKERS`);
- the gate is deterministic in the seed: `--seed` fixes the streams, so a
  failure is reproducible.

Choose pairs for meaningful rule variants, boundaries and interactions, not
for the Cartesian product of all profiles (see *When to add a pair*).

### Levels and current rule-coverage estimate

- **`normal` (30 pairs)** keeps one representative for each distinct mechanic
  family currently present in the full matrix, plus the timing/native-drift
  amplifiers and the eight coverage-completion probes. It intentionally
  removes baselines, mirrors and alternate matchup contexts, so it is the
  recommended 10–15 minute certification loop.
- **`big` (42 pairs)** is the complete matrix. It adds the omitted baselines,
  mirrors and alternate contexts; these do not usually add a new rule family,
  but they are valuable for finding direction-dependent or composition bugs
  after substantial engine changes.

Both levels are curated to exercise every reachable compiled effect axis in the
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

## The statistical battery

`--scenarios battery` (or a single `battery/<id>`) selects 122 short duels of
one to three rounds, each built from the knowledge base so that one mechanic
decides the outcome. They are a third catalogue beside the 43 precompiled
scenarios and the E2E deliveries, not a subset of either: a long duel averages
a defect away, and these do not. They are compared by the one parity
comparison, with the same six-sigma gate, and they are the only cases that
carry scripted decisions, which `check parity` passes on to both engines.

```bash
# the whole battery, both candidates, Markdown report and strict gate
python -X utf8 tools/mordheim-utils.py check parity --scenarios battery --backend numpy native --simulations 7200 --output outputs/parity/battery.md --require-complete

# two named cases at a small width; their rows are UNDERPOWERED, never approved
python -X utf8 tools/mordheim-utils.py check parity --scenarios battery/q04-parry-attempt battery/q04-injury-chart --simulations 256
```

Two cases declare an input the engines cannot express and are reported
`INCOMPATIBLE` with their cause rather than run as a different duel:
`c03-petru-potion` needs a campaign-only potion table the KB marks out of
scope, and `v01-restriction` needs a charge construction refuses.

A battery case is not special once selected: it is sampled, compared and
reported exactly like a precompiled scenario or an E2E delivery. Its declared
width (64 rows) is a smoke size, so `--simulations` decides the real one and
anything below 7,200 is `UNDERPOWERED`.

## The realistic sets

`--scenarios realistic-50` and `realistic-100` select curated duels that
reproduce how the game is actually played; they exist to measure performance
(see "Realistic performance sets" in `docs/reference/tools.md`). They are
frozen corpus cases, so parity, samples, benchmark and calibration run them
like precompiled scenarios. They are not a rules catalogue: a mechanic they
miss is still covered by the 43 scenarios, the E2E deliveries and the battery.

```bash
python -X utf8 tools/mordheim-utils.py check parity --scenarios realistic-100 --backend numpy native --simulations 20k --workers 4
```

## Oracle sampling and worker pools

`--workers N|auto` applies to the modular samples of `check parity` and
`check samples`. It partitions each sample into contiguous `seed + i` ranges,
preserves terminal row order and reuses one process pool across cases. `1`
stays sequential; explicit counts are capped to available CPUs, and `auto`
uses the measured cost threshold. Candidate batches are unchanged, and
`--backend numpy native` shares the modular sample between candidates.

Every oracle and candidate pool checks at start-up that each worker imported
the parent's engine files; a worker that resolved another engine copy stops
the run (exit 2) instead of merging another engine's duels into the sample.

The comparison is statistical: `winner` (first win, second win, unresolved) is
compared with the six-sigma tolerance (`_statistical.six_sigma_tolerance`,
floor 0.25%), and `rounds` when the case declares it. Internal counters,
activation flags and equipment hashes are never compared.

`--backend` defaults to `numpy`. `native` never falls back to NumPy: a missing
or stale extension is `NOT_RUN:native-unavailable` or `NOT_RUN:native-stale`,
an error that fails the run, and a plan the extension cannot express is
`NOT_RUN:native-plan`, a declared limitation. Neither is a comparison. Native
rows replay the native core with the NumPy random generator, so they do not
exercise production native seeding; reports say so.

Each engine's winner convention is validated before normalisation (oracle
`0/1/2`, candidate `1/-1/0`). A code outside its own convention is malformed
data: the case is `NOT_RUN:outcome-codes`, an own error, and the code never
enters the unresolved category or disappears from the sample.

An own error (a compile failure, a crashed candidate, a malformed or
non-deterministic batch, a missing requested native backend, any divergence)
fails the command on its own. A declared limitation leaves the run incomplete,
which only `--require-complete` turns into a failure. The report records the
source revision, dirty state, engine digests and native build; provenance
differences only warn.

A statistical PASS compares outcome distributions; it does not prove that a
rule changes them. The with/without-rule contrast over the oracle belongs to
the modular mechanics and E2E layers.

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

`check report tests` writes technical test results under
`outputs/test-report/`. It does not run or approve a
semantic YAML corpus. Skipped and expected-failure tests are reported as `SKIP`
and `XFAIL`, never as passes. The CSV left by an earlier run is removed before
pytest starts, so a run that crashes before writing its own reports the CSV as
missing instead of reusing stale results; from a source checkout the child
pytest imports that checkout's packages. `check parity --output` writes comparison reports
(JSON or Markdown); `check report rules` exports the rule inventory and the
declared clause coverage without claiming semantic verification. The retired
clause register CSVs under `docs/archive/` are historical records, not current
certificates.

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
