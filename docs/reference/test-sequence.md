# Test classification and execution order

This is the contract for classifying existing tests by what they prove.
Classification is applied to the Python suites listed under
[Implementation](#implementation); the TypeScript and web suites are still
unclassified and the `test-sequence` command now orders classified Python tests
in one sequential pytest session or with workers inside sequential phases.
JavaScript selection and detailed prerequisite classification remain
separate work; this command does not claim to schedule the whole repository.

The aim is to detect the smallest causal defect before interpreting failures in
the larger paths that depend on it. Repairing one incorrect grant, compiled
value or rule operation can resolve several downstream failures. Follow these
dependencies without maintaining a second catalogue of individual test files or
function names. Classification does not establish correctness, coverage
completeness or permission to delete tests.

## Classification unit

Every executable test has **one primary category**, chosen from its assertions
and the defect it detects. Do not classify from its name, imports, setup size or
fixture directory alone.

The component is independent: KB, construction, modular combat, NumPy/native
combat, campaign, Combat Lab, web or tooling. Use existing directories and runner
configuration for this distinction, rather than a category for every combination.
Backend, display and expensive-execution requirements are also separate; retain
existing skips and environment rules.

Use file-level classification for homogeneous files, and function/parameter-level
classification for mixed files or parametrized entry points. A reviewed group of
cases with the same purpose can inherit one classification; do not repeat an
annotation thousands of times.

Prefer a small file split when responsibilities are independent and setup,
isolation and collection can be preserved. Do not split a coherent behavioural
scenario merely because it has several related assertions. For inseparable mixed
assertions, choose the main acceptance condition and explain the secondary
guarantee beside the test.

## Primary categories

These identifiers are the selection vocabulary. They are registered as pytest
markers in `pyproject.toml` and enforced for the classified Python roots (see
[Implementation](#implementation)). Meanings are shared across runners;
representation depends on the installed runner's supported mechanisms.

| Identifier | What it proves | Include | Distinguish from |
| --- | --- | --- | --- |
| `architecture` | Component and dependency boundaries are respected | Forbidden imports, package purity, prohibited components in a bundle | Functional correctness |
| `data_contract` | Documents/requests conform to structural contracts | Schemas, field types, required fields, versions, invalid-shape rejection | Legality of a game choice |
| `knowledge_integrity` | Canonical KB records are consistent and preserve source facts | References, unique IDs, printed values, declared recipients, translation completeness | Effects reaching combat consumers |
| `data_transport` | Information survives generation, loading and projection | Deterministic web artefacts, fragments, readers, Python/JS transport | Correctness of the game decision transported |
| `eligibility` | A choice is offered, admitted or rejected for the correct reason | Recipient permissions, prerequisites, exclusions, available choices and legal loadouts | The numerical effects produced after admission |
| `compilation` | An admitted configuration becomes the correct executable representation | Profile/item resolution, characteristics, exactly-once grants, effect parameters, weapon slots and backend input projection | Whether a choice is legal, or whether combat consumes its compiled effect |
| `operator` | A local operation produces its defined value/distribution | Generic hit/wound/save/injury tables, primitive composition, exact finite distributions | Full conditions of a named rule |
| `rule_behavior` | One game rule has its source-defined consequences | Activation, absence controls, magnitude, limits, duration, resource consumption; campaign rules included | Orchestration of independent rules/steps |
| `interaction` | Multiple rules or phases compose in the required order | Named-rule combinations, precedence, shared resources, state transfer | One rule merely having several clauses |
| `workflow` | An application or execution service connects its steps correctly | Campaign use cases, cancellation, batching, workers, routing, report formatting | Complete product paths or isolated rule calculations |
| `persistence` | Saved state is preserved and invalid storage handled | Save/load, serialization, imports, corruption, compatibility | Schema-fixture validation alone |
| `presentation` | Visible and interactive results are correct | UI actions, accessibility, translations, tooltips, errors, technical-ID leak prevention | Browser E2E, which simulated DOM alone cannot prove |
| `end_to_end` | A complete connected product path meets observable acceptance | Canonical fighter configuration through compilation, initialization and actual combat; equivalent complete campaign paths | Every file under E2E, isolated compilation refusals or rendering alone |
| `test_infrastructure` | Testing/diagnostic mechanisms detect faults reliably | Strict dice/decisions, malformed cases, wrong-expectation detection, mutation isolation, detector self-tests | Product-input validation |
| `evidence` | Coverage/provenance/certification records are valid | Inventories, accepted-scenario retention, source digests, pending/verified state, coverage-budget policy | Game correctness or execution of an entire certification campaign |
| `parity` | Implementations/execution modes agree under a defined comparison | Modular/NumPy/native comparisons, replay, cross-language decisions, statistical agreement | Independent source-based correctness |
| `performance` | A measured execution or delivery budget is met | Runtime, throughput, memory, download-size limits | Benchmark parsing or report formatting |
| `delivery` | The built/packaged product contains required usable artefacts | Build outputs, published fonts/assets, packaging composition | Source-only architecture or pre-build UI behaviour |

Classify the observed guarantee, not the promise in the test name. An expensive
test can be `evidence`; a short refusal in the E2E corpus can be `eligibility`.

## Ambiguous cases

- A malformed field is `data_contract`; a valid profile forbidden from choosing
  a skill is `eligibility`.
- Declaring the correct recipient in KB data is `knowledge_integrity`; proving
  that recipient receives a compiled effect is `compilation`.
- A generic injury table is `operator`; a named rule changing injuries under its
  printed conditions is `rule_behavior`; its precedence with another rule is
  `interaction`.
- An E2E YAML expecting poison rejection is `eligibility`. A canonical build
  that resolves actual rounds and checks their result is `end_to_end`.
- A test calling `compile_fighter` is not automatically `compilation`: a refusal
  assertion is `eligibility`, a compiled-field assertion is `compilation`, and
  an assertion about the consumed effect belongs to its behavioural level.
- A bridge test can check transport or compare decisions. Classify each test's
  assertions; two languages alone do not make the whole file `parity`.
- Falsifying evidence to test an auditor is `test_infrastructure`; comparing the
  live corpus with accepted evidence is `evidence`. Formatting its report is
  `workflow`, not execution of the campaign described by that report.
- Mutation-catalogue anchors are `test_infrastructure`; live coverage thresholds
  are `evidence`. A behavioural mutation can support a rule test without changing
  its primary behavioural category.
- Excluding Combat Lab from a bundle is `architecture`; publishing a required
  font is `delivery`; limiting download size is `performance`.

## Applying the classification

For Python, use native pytest markers registered with descriptions in
`pyproject.toml`. Use module-level `pytestmark` for homogeneous files, decorators
for individual functions and `pytest.param(..., marks=...)` for mixed case sets.
Reject missing, multiple or unknown primary categories through collection or one
small validation over collected items, without a manual list of test names.
Strict marker registration alone does not detect missing/multiple categories.

For Vitest and `node:test`, inspect installed versions/configuration first.
Reuse supported native selection or homogeneous suite/file grouping. Do not add a
wrapper, custom test DSL, comment parser or source-text classifier to imitate
pytest. A comment that cannot drive selection is documentation, not executable
classification. State any remaining selection limitation explicitly.

YAML remains test data with its current identities and schemas. Do not overwrite
existing `category`, `roles`, `covers`, `audit_id`, status or source digests: they
represent other contracts. Classify collected parameters, reusing explicit
metadata only where meanings match. Interpret mixed cases manually; scripts may
validate explicit assignments but must not infer semantic equivalence from
keywords, names or engine output. If metadata cannot represent a necessary
distinction, identify the exact gap before proposing a compatible schema change.

Keep one executable classification source per test. Generated inventories are
derived views, never another editable registry. Do not change expectations, dice,
decisions, fixture data, meaning or skips to classify tests. Moves can change node
IDs: preserve a reviewable before/after mapping and inspect consumers such as
mutation selectors, budgets and baselines. Avoid moves requiring unrelated
contract changes. Do not duplicate test bodies to obtain category selections.

## Execution order: causal depth first

The execution policy is **prerequisites before consumers, narrow contracts
before composed behaviour**. This minimizes the number of downstream failures
that must be investigated as if they were independent. Within ready tests,
prioritize shared components with more actual consumers and assertions that
isolate one responsibility. Use measured duration only as a tie-breaker; neither
file size nor test count measures causal importance.

This is a source-based execution policy, not a benchmarked optimum. The initial
Python executor below implements a conservative subset. Dependency decisions come from the called implementation
and fixture path, not from a test name or the number of imports. Category is
what a test proves; it is not by itself a sufficient scheduling key.

### Functional stages

| Stage | Categories / checks | Prerequisites and diagnostic purpose |
| --- | --- | --- |
| 0. Executable test mechanisms | Environment/import/collection checks and focused `test_infrastructure` self-tests | Establish that the selected runner, strict inputs and assertions can be trusted. Only self-tests independent of the product belong here; a harness test driving real combat waits for combat prerequisites. |
| 1. Valid source inputs | `data_contract`, then relevant `knowledge_integrity` | Resolve invalid shapes, identifiers, references and canonical records before their readers or compilers. Schema-definition self-tests precede validation of real documents. |
| 2. Shared foundations | Ready `operator`, `eligibility` and `data_transport` tests | Test direct calculations, the shared decision implementation, loaders and adapters before their consumers. These are independent subbranches, not an arbitrary total ordering. A transport test that needs a real eligibility decision follows that direct decision test. |
| 3. Executable configuration | `compilation` | Check resolved profiles/items, projected characteristics, slots, tags and effect values after required source, eligibility and adapter tests. This separates wrongly produced inputs from faulty consumers. |
| 4. Individual behaviour | `rule_behavior` | Check one source-defined consequence and its positive/negative/boundary conditions after its real compilation and operator dependencies. Cover both combat and campaign domain rules here. |
| 5. Composed behaviour | `interaction` | Check precedence, phase order, state transfer and resources shared between rules after the relevant individual behaviours. |
| 6. Application connections | `persistence` and `workflow` | Direct storage tests precede services that import/save; domain tests precede orchestration. Independent persistence and service branches need not wait for unrelated combat families. |
| 7. User interface | `presentation` | Check rendering, choices, actions and messages after their read models, services and data sources. Pure text helpers can run earlier if their only prerequisite is an already validated input contract. |
| 8. Connected acceptance | `end_to_end` | Validate the complete relevant path after its local contracts. Combat E2E follows compilation, rule and sequence checks; it does not depend on web presentation. Browser/product E2E follows the UI it actually exercises. |

A test whose setup uses canonical compilation must wait for that compilation even
if its primary category is `operator`. A direct operator test using explicit
inputs need not wait. Likewise, a workflow tested with injected fakes does not
prove the real adapters and must not stand in for their integration checks.
Do not create synthetic dependencies between independent branches just to give
all categories a single ordinal number.

### Repository branches

- **Modular combat:** schemas/KB and required loaders → shared eligibility and
  its Python transport → fighter compilation → individual rule consumers →
  phase/state interactions → connected modular E2E. Direct generic operators
  are an earlier independent foundation feeding the rule consumers. The actual
  current phase tests that compile fighters inherit the compiler prerequisite.
- **Campaign/web:** schemas/KB → generated artefact and reader adapters, alongside
  direct eligibility/domain foundations → campaign rules and state transitions
  → storage adapters and application services in their dependency order → UI →
  available complete acceptance paths. Do not invent browser E2E coverage where
  the repository only has simulated-DOM tests.
- **Combat Lab:** shared construction/combat contracts → catalogue/read models,
  execution services and settings → storage/service integrations → desktop UI.
  A settings calculation or storage test with explicit inputs can run before
  real simulations; batch execution consumes the actual driver it invokes.
- **Optimized combat:** stabilize the required modular contracts first, then
  backend compilation → backend operators/rules/sequences → deterministic
  cross-backend `parity` → statistical `parity`. NumPy/native divergence should
  not redefine the modular expectation. Cross-language eligibility parity is
  different: it belongs near the early shared eligibility/transport branch,
  not behind optimized combat certification.

### Orthogonal controls and late campaigns

| Category | Position |
| --- | --- |
| `architecture` | Run relevant source-boundary checks early. Bundle-boundary checks require the build and run after it. Architecture findings do not imply all functional branches are broken. |
| `test_infrastructure` | Run each executor's focused self-tests before trusting that executor. Auditor/report self-tests run when validating that tool; those driving live product behaviour inherit its prerequisites. |
| `evidence` | Run cheap corpus identity/provenance checks early to expose stale or missing evidence; reconcile final coverage/certification on the delivered state after functionality. Missing evidence must not be presented as a functional failure or silently ignored. |
| `parity` | Position depends on the compared component: shared adapter parity near those adapters; optimized deterministic comparison after the oracle and backend contracts; statistical comparisons last. |
| `delivery` | After a real build/package. Validate required published artefacts and composition before interpreting deployment failures. |
| `performance` | After correctness of the measured path and preparation of the actual artefact/backend. Run expensive benchmarks and statistical campaigns only for the required scope. |

Coverage/mutation campaign execution is distinct from testing its catalogue,
policy or report. All classification and ordering must retain this distinction.
Skipped native tests are not native correctness evidence. An evidence refresh,
relaxed threshold or larger sample is not a repair for a functional defect.

### Failure and rerun policy

When a prerequisite fails, prioritize diagnosing and repairing that contract.
Its dependent stages are blocked for normal progression; independent branches
remain runnable. An explicitly requested diagnostic run may execute dependents,
but their failures must remain provisional until the prerequisite is repaired.
Do not infer that every later failure shares the first cause.

After a repair, rerun the narrow failing contract, then its affected consumers
in dependency order, finishing with the relevant connected acceptance checks.
Revalidate earlier foundations if their code or inputs changed. Reuse valid
results whose inputs are unchanged, and perform the required final integrated
confirmation once the repair package is stable.

For incremental development, this policy applies to the affected dependency
branch and family. For a broad repository check, traverse the same stages across
all branches and execute shared prerequisites once per selected revision. Do not
rerun all low-level categories for each scenario. Mixed files must acquire usable
category/component selection before a future launcher can implement this order;
do not compensate with hard-coded function-name lists.

## Repair and classification acceptance

Validate failed expectations against source and accepted rulings first. Group
failures by cause and locate the first incorrect transition: input → admission/
compilation → local consumer → state/order → observable result. Prefer the
smallest failing test that discriminates the suspected cause. Repair that cause
once, recheck it locally, then rerun affected connected tests to confirm that the
downstream failures disappeared. A shared cause is a hypothesis until those
checks confirm it; remaining failures still require investigation. Work through
each family; do not finish every semantic test before looking at any E2E.

Classification covers all maintained executable tests: Python, Vitest,
`node:test`, declarative cases and tests under `tools/`. Temporary failure notes,
fixtures and generated reports are not independent executable tests. Collection
failures remain visible blockers, never silent exclusions. Every executable test
needs an explicit primary category and usable category/component selection in its runner; disclose
any unresolved limitation rather than claiming completion.

Compare collection before/after and check fixture/isolation behaviour where
files move. Validate category selection with focused checks. Do not run every
simulation just to prove annotations were added. Keep existing functional
failures separate from classification defects. Do not delete tests, relax
assertions, refresh evidence or change KB/game behaviour to finish this work.

A launcher must consume runner-supported categories and retain category
dependency order and component prerequisites only. See
[verification](verification.md#modular-integration-closure) for closure and
certification requirements; unresolved concrete defects belong in
[TODO.md](../../TODO.md).

## Initial Python executor

The central launcher loads a small pytest plugin, not another inventory of
test functions. Sequential mode collects once, applies native path/marker selection, sorts
the remaining items stably, then executes in that same session. Existing
`tests` invocations are unchanged.

```powershell
# Fast phase list: imports the plugin only, without collecting tests/corpus.
python tools/mordheim-utils.py test-sequence --steps
# Execute one phase (both spellings are supported).
python tools/mordheim-utils.py test-sequence --step 1 -q
python tools/mordheim-utils.py test-sequence -step3 --scope construction -q
# Inspect the actual ordered collection; no test bodies run.
python tools/mordheim-utils.py test-sequence --sequence-plan -q
# Execute selected Python tests; default scope is all Python tests under tests/.
python tools/mordheim-utils.py test-sequence -q
# Select a component or category using existing pytest mechanisms.
python tools/mordheim-utils.py test-sequence --scope construction -q
python tools/mordheim-utils.py test-sequence --scope e2e -m eligibility -q
# Explicitly omit earlier stages; this does not validate old results.
python tools/mordheim-utils.py test-sequence --sequence-from rule_behavior -q
# Diagnostic mode; later failures may be consequences of earlier ones.
python tools/mordheim-utils.py test-sequence --sequence-keep-going -q
```

Default execution continues after failures and retains pytest's nonzero exit
status. Use `-x` to stop at the first failure, or `--maxfail N` to stop after N.
The explicit `--sequence-keep-going` option remains compatible with existing
commands but is no longer required. The summary distinguishes passed, failed,
skipped and not-run items. Invalid/missing primary categories prevent execution.
Parallel workers require one selected phase per pytest session; the launcher
provides those sessions and waits for all workers before advancing.

The conservative order is architecture → data contracts → KB integrity → data
transport → eligibility → compilation → operators → individual rule behaviour →
interactions → test infrastructure → persistence → workflows → presentation →
E2E → evidence → delivery/performance. Shared construction parity runs after
eligibility. Backend component suites and backend parity follow the selected
baseline checks; existing `backend=numpy/native` parameters are also deferred.
The plan prints the nonempty stages and their counts.

Infrastructure is deliberately late in this first executor: its current category
includes harness checks that drive live combat, so running that entire category
first would hide its product dependencies. Similarly, operators conservatively
follow compilation because current operator tests can compile canonical fighters.
Earlier execution of independent self-tests/operators needs a more precise
classification; the runner does not infer it from function names.

This is not a dependency-graph scheduler. It does not expand scopes to include
prerequisites, prepare generated inputs/builds, distinguish every statistical
parity case, cache success, or run Vitest/`node:test`. Category/component selections
can deliberately omit prerequisites. `--sequence-from optimized/compilation`
resumes within the deferred backend stages. Collection still imports modules and
loads declarative data even in plan mode; collection errors remain failures.

Implementation: `tools/verification/test_sequence.py`. Inspect its options with
`python tools/mordheim-utils.py test-sequence --help`.

Numbered phases are: 1 contracts/KB; 2 transport/eligibility/shared parity;
3 compilation/operators; 4 individual behaviour; 5 interactions; 6 harnesses,
persistence and workflows; 7 presentation; 8 E2E; 9 evidence; 10 baseline
delivery/performance; 11 optimized components and engine parity. The executable
phase definitions live with the ordering policy in the plugin, not in a test
inventory. Backend tests belong to phase 11 regardless of their primary category.

`--step N` selects exactly one phase, not every phase up to N. It can be combined
with scopes, markers, plan mode and diagnostic continuation, but not with
`--sequence-from`. An empty selection retains pytest's nonzero no-tests exit.

An actual plan must import test modules and expand parameters; the semantic and
E2E entry points load their YAML corpora during collection. `-qq` only reduces
output. Phase/marker filtering occurs after those imports, so phase selection
alone does not remove that cost. Use `--scope` to reduce the collected component
roots, and `--steps` when only the phase definitions are needed. No cached
inventory or heuristic source classifier is used to bypass collection.

### Optional processes within sequential phases

Install the development dependencies, which now include `pytest-xdist`:

```powershell
python -m pip install -e ".[dev]"
# One phase, four processes; combine with a scope to reduce collection.
python tools/mordheim-utils.py test-sequence -step1 --scope knowledge --workers 4 -q
# Full sequence: finish all processes in one phase before starting the next.
python tools/mordheim-utils.py test-sequence --workers 4 -q
# Preserve the original single-session, category-ordered execution.
python tools/mordheim-utils.py test-sequence --workers 1 -q
```

The default remains one process. For `--workers N` with N greater than one,
the launcher makes blocking pytest calls for the selected numbered phases.
`pytest-xdist` owns distribution, using `--dist=loadfile` so all selected tests
of a file stay in the same worker. There is no custom scheduler or test list.
There is **no cross-file/category execution order within a phase**: use this
mode for independent tests. Shared on-disk resources still require isolation;
in-memory monkeypatches/caches are process-local. This option does not certify
that every existing test is safe or faster in parallel.

Each worker collects the selected roots anew, and a complete sequence starts
new workers for each phase. This trades startup/collection cost for parallel
test execution; prefer a single phase and narrow scope when diagnosing a change.
Session fixtures/caches are repeated per worker and phase. `--sequence-plan`
stays a single sequential collection even when `--workers` is present.

The phase summary retains failures when later phases pass. Empty phases in a
full sequence are reported as unvalidated and skipped; an entirely empty run
returns pytest's no-tests exit code. A selected empty phase also returns that
code. Normal test failures continue to the next phase by default. Collection,
configuration, internal errors and interruption abort progression. With `-x`
or a positive `--maxfail N`, execution stops after a failing phase; the limit
is evaluated inside each pytest session, not globally across phases. Workers
already running can finish before that session exits.

Parallel mode accepts `--step` but not `--sequence-from`; choose the phase
explicitly. `--workers` owns the worker count and distribution options, so do
not combine it with raw `-n`, `--numprocesses` or `--dist` options. Direct plugin
use with xdist requires one `--step` and `--dist=loadfile`. Controller summaries
are per-phase; sequential summaries retain the finer category stages.

Verification of this feature uses synthetic tests that demonstrate different
worker process IDs, completion before the next phase, and failure propagation.
It does not constitute execution or certification of the full KB/combat suite.

### What the categories do not express

A category says what a test proves, not what it needs. Two tests in one category
can have different prerequisites: an `operator` test with explicit inputs is a
foundation, while an `operator` test that compiles a canonical fighter waits for
compilation. The prerequisite comes from the fixture path and the called
implementation, so selection reads the marker *and* the setup: canonical
`compile_fighter`, `load_corpus` or reader setup inherits its layer, while an
injected fake does not stand in for the real adapter it replaces. `parity` is
placed by what it compares (shared adapters early, optimized backends after the
oracle, statistical last), `evidence` by cost, `delivery` after a build, and
`performance` after the measured path is correct. This is why the executor orders
whole categories conservatively instead of inferring per-test dependencies.

## Implementation

The eighteen identifiers above are registered as pytest markers with their
descriptions in `pyproject.toml`, and `addopts = "--strict-markers"` rejects a
marker that is not registered. `tests/conftest.py` holds the one validation over
collected items: for every collected item under a classified root it rejects no
primary category, several primary categories, or a marker that is not a category
(pytest's own `parametrize`, `skip`, `skipif`, `xfail`, `usefixtures` and
`filterwarnings` are not categories). It reads no source text, keeps no list of
test names and names the offending node IDs, so a missing or doubled annotation
is visible at collection instead of silently selecting the wrong set. An unknown
category fails even earlier, at strict marker registration.

Classified roots, in the guard's `CLASSIFIED_ROOTS`:

| Root | Component |
| --- | --- |
| `tests/python/architecture` | package boundaries |
| `tests/python/contracts` | campaign-file contracts |
| `tests/python/knowledge` | KB, catalogues, editorial and translation |
| `tests/python/construction` | roster construction and eligibility |
| `tests/python/application` | Combat Lab application services and settings |
| `tests/python/persistence` | saved state |
| `tests/python/ui` | Combat Lab desktop UI |
| `tests/python/cli` | launcher and console |
| `tests/python/web` | generated web artefact, reader projections and vectors |
| `tests/python/combat` | modular, NumPy/vectorized and native duel execution |
| `tests/python/verification` | audit, inventory, consumers and structural verifiers |
| `tests/E2E/modular-engine` | declarative corpus, phase/variant suites and the generator checks |

On 2026-10-20 the full suite collected 12,952 items: none fell outside those
roots and none carried zero or several primary categories. The per-category and
per-root selections were counted over that same collection, and three focused
selections were run: `-m parity` over `native` + `vectorized` (12 of 119),
`-m interaction` over `modular` (131 of 1,411) and `-m eligibility` over the E2E
corpus (468 of 5,262). No functional battery was executed to prove the
annotations; a collection confirms selection, not behaviour.

Every maintained Python executable test is now inside a guarded root. What is
still outside the guard is the TypeScript and web slice (see below), and
`tests/specs`, which is declarative YAML test data rather than collected pytest
items. `tests/E2E/modular-engine/conftest.py` keeps loading its local support
package; nothing there needed to change for the classification.

Selection:

```
python -m pytest -m compilation                     # one primary category
python -m pytest -m "data_contract or operator"     # the foundation stages
python -m pytest -m eligibility tests/python/construction   # within a component
python -m pytest -m "not presentation" tests/python/ui      # exclusion
python -m pytest --collect-only -m rule_behavior    # inspect without executing
```

Component selection stays the existing directory layout; category selection is
the marker. The initial ordered Python launcher uses those same selections;
the full [execution order](#execution-order-causal-depth-first) still requires
the appropriate component and prerequisite selection.

A concurrent slice moved `tools/knowledge/test_clause_registry.py` to
`tests/python/knowledge/test_clause_registry.py`: its eight cases keep their names
and change node ID prefix, and `tools/` is no longer a test root. The only
reference to the old path (`docs/reference/knowledge-base.md`) was updated by that
slice, and no mutation selector, budget or baseline names the old node IDs.

Collection note: `tests/python/construction/__init__.py` exists solely because
the default import mode names modules by base name and
`test_profile_save_thresholds.py` exists in both the construction and combat
suites. The package marker makes the two modules distinct without moving a file
or changing a node ID. The two files now collect together (56 items); before it,
the duplicate base name interrupted the whole collection with an import
mismatch. Each module keeps its identity, so no consumer of a node ID changes.

### TypeScript and web suites

The TypeScript and web suites have no executable primary category yet. The slice
delivered for them assigned categories by reading assertions and left the suites
unchanged apart from `reporters: ["default"]` in
`packages/typescript/vitest.config.ts` and `apps/warband-manager-web/vite.config.ts`
plus an explanatory comment; a reporter setting neither tags nor selects a test.
The installed runners expose no per-test category tag, checked against the
binaries rather than assumed: `vitest --help` lists `-t/--testNamePattern`,
`--project` and `--dir` and no tag filter, `@vitest/runner`'s types declare no
`tags`, and `node:test` on Node 24 offers `--test-name-pattern` and `--test-only`.
A category therefore has to live where the runner can see it: the test's name or
its file path. That assignment is documentation, not executable classification,
and it is recorded as such.

What the installed runner does support, measured on 2026-10-20:

- `npx vitest list --config packages/typescript/vitest.config.ts` collects 961
  items from the 92 `tests/typescript/**/*.test.ts` files.
- `npx vitest list --config apps/warband-manager-web/vite.config.ts`, invoked with
  `apps/warband-manager-web` as the working directory, collects 444 items from the
  66 `tests/web/**/*.test.{ts,tsx}` files.
- Component selection is the directory (`--dir tests/typescript/<area>`); a mixed
  file is selected per block with `--testNamePattern`.
- Native project selection works and partitions cleanly: a throwaway config with
  one `test.projects` entry per directory (per-project aliases, wildcard
  `include`) selected `--project domain` 518 items, `--project application` 275
  and `--project adapters` 118 -- 911 of the 961 TypeScript items, disjoint and
  exhaustive for those three directories.

The smallest change that turns a category into a selection key is a category
token in the file name, `<name>.<category>.test.ts`, plus one project per
category whose `include` is `**/*.<category>.test.ts`: eighteen wildcard globs,
no path catalogue, no wrapper, and a new file joins its project by name. Only the
five mixed files need a small split. It renames the 158 maintained Vitest files,
so every Vitest report identity changes and the consumers (mutation selectors,
budgets, baselines and the documents quoting test paths) must be reviewed in the
same change. It is not executed here: those files are under active concurrent
editing, and the contract asks for a reviewable before/after mapping instead of a
bulk rename under other writers. Until it is done, the TypeScript and web
categories stay a reading of each test, not a selection key.

The web suite resolves its generated artefacts with
`resolve(process.cwd(), "../../outputs/web-public/knowledge/...")`, so it must be
invoked from `apps/warband-manager-web`. Invoked from the repository root it
fails collection with `ENOENT` for a path one directory above the checkout,
although `outputs/web-public/knowledge/`, `build/generated/knowledge-web` and
`contracts/campaign-file-v5/fixtures` all exist in this tree: the failure is the
working directory, not missing data.

Limitations of the current state:

- `-m <category>` is a complete specification of the Python suite, not of the
  repository: for the TypeScript and web suites above, the primary category
  remains a reading of each test, not a selection key.
- A homogeneous `unittest` module carries its category at module level and its
  methods inherit it: `test_generate_skeletons.py` is `evidence` and
  `-m evidence` selects its 12 cases, `-m "not evidence"` selects none.
- A test added later to a classified root fails collection until it carries a
  marker. That is intended, and it is the only enforcement.
- A skipped test (`Tk display is not available`, a missing generated artefact)
  keeps its primary category but proves nothing when it skips.
- A mixed file is annotated per function; a module-level `pytestmark` combined
  with a differently classified function is rejected at collection by design,
  not silently resolved.
- Where one test inseparably mixes two guarantees, it keeps the primary category
  and a comment names the secondary guarantee; the guard cannot check that
  judgement.
- No file was moved, split or consolidated in this pass, so a mixed file is
  selected per case rather than per new file.
