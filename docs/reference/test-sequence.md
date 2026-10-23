# Test classification and execution order

This is the contract for classifying every maintained executable test by the
project's functional dependencies. There is one classification: the phase
categories below. The previous per-guarantee vocabulary (`architecture`,
`data_contract`, `compilation`, `parity`, ...) was removed together with its
execution order; no translation table is kept and no runner still selects it.

The aim is to detect the smallest causal defect before interpreting failures in
the layers that consume it. A broken KB record, compiled value or rule operation
can explain several downstream failures; the phases order those consumers behind
their prerequisites. Classification does not establish correctness, coverage
completeness or permission to delete tests.

## Classification unit

Every executable item has **one category**, chosen from its assertions and the
defect it detects. The category is applied where the runner can select it:

- Python: a pytest marker, at module, function or `pytest.param` level.
- TypeScript/web: a native Vitest project (see [TypeScript and web](#typescript-and-web-suites)).

Judge what the item validates, not what it uses as preparation, fixture or
reference. A test that builds a fighter to check a rule is proving the rule; the
construction is setup. Reading a path, a file name or a called function is not
enough evidence on its own.

When one item inseparably proves guarantees of several phases, assign it to the
most advanced guarantee it checks. Do not duplicate a test across phases or split
a coherent scenario only to make classification easier. A reviewed group with
one purpose may share a category; mixed files use per-function or per-parameter
annotations instead of a second classification system.

## Functional phases

| Phase | Identifier | What it proves | Typical contents |
| --- | --- | --- | --- |
| 0 | `phase0_preflight` | The test mechanism and the architecture boundaries can be trusted before product behaviour is interpreted | Launcher/plugin/guard tests, synthetic strict-dice and decision self-tests, declarative E2E corpus and loader contracts (schema, identity, isolation), component/import boundaries and forbidden dependency checks |
| 1 | `phase1_kb_contracts` | Canonical data is valid, coherent and interpretable | KB schemas and strictness, references and IDs, editorial and translation integrity, loaders, generated KB artefact and reader/transport contracts, presentation locators, campaign-catalogue data contracts |
| 2 | `phase2_construction` | Valid data produces the combatants the engine consumes | Eligibility and refusals, options, loadouts and team assignment, profiles, compilation, compiled values, exactly-once grants, rule concessions, shared Python/TypeScript eligibility parity, declarative E2E cases that assert a named refusal |
| 3 | `phase3_rules` | A modular condition, operator or effect has its defined local consequence | Hit/wound/save/injury/parry tables and primitives, isolated rule activation, magnitude, limits and duration, rule behaviour with construction as setup |
| 4 | `phase4_modular` | The modular oracle composes rules and rounds correctly | Interactions and precedence, phase order and state transfer, shared resources, combat sequences, modular integration and modular E2E, observed-vs-reference and parallel-oracle parity |
| 5 | `phase5_vectorized` | The vectorized backend is correct and agrees with the oracle | Every functional test specific to the vectorized backend, including isolated rule and KB-shaped assertions there, deterministic and statistical parity against the modular oracle, truncation and deep certification samples |
| 6 | `phase6_native` | The native backend is correct and agrees with the oracle | Every functional test specific to the native backend, native compilation/lowering, native error and cleanup contracts, parity against the oracle or another backend |
| 7 | `phase7_warband` | The application tier connects persistence, flows, presentation and integration correctly | Warband Manager persistence, campaign flows, UI/presentation, adapters and E2E, campaign-file v5 contracts, TypeScript domain/application/adapters/web suites; the Combat Lab application services, desktop UI, storage and console share this application tier |

Phases are ordered strictly: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. A test may be
short, cheap or located early and still belong to a later phase; duration,
framework, directory and diagnostic convenience are not criteria.

### Assignment rules for the ambiguous cases

- **Construction versus rule application.** A test that compiles a canonical
  fighter and asserts a fight consequence is `phase3_rules`; a test that asserts
  the compiled profile, item, slot, tag or effect value is `phase2_construction`;
  a refusal is also `phase2_construction`.
- **KB record versus consumer.** Declaring a recipient, reference or printed
  value is `phase1_kb_contracts`; proving that the recipient receives a compiled
  grant is `phase2_construction`.
- **Operators versus named rules.** A generic table or primitive is
  `phase3_rules`; a named rule under its printed conditions is also
  `phase3_rules`; precedence or state transfer between independent rules is
  `phase4_modular`.
- **E2E belongs to the system it verifies.** A modular declarative scenario that
  observes rounds or a final state is `phase4_modular`; a declaration that only
  asserts a named rejection is `phase2_construction` (admission, not an executed
  path); an application E2E is `phase7_warband`.
- **Parity validates one implementation against a reference.** The comparison is
  placed after both participants have reached their phase, so the category names
  the implementation being validated:
  - shared Python/TypeScript eligibility: `phase2_construction`;
  - modular observed-vs-reference and parallel oracle: `phase4_modular`;
  - vectorized against the modular oracle (deterministic, statistical,
    truncation, deep certification): `phase5_vectorized`;
  - native against the oracle or another backend: `phase6_native`;
  - formatting a parity report is `evidence`, not execution of the comparison.
- **Backend parametrizations are classified per item.** A single function
  parametrized over `modular`, `numpy` and `native` produces three categories:
  `phase4_modular`, `phase5_vectorized`, `phase6_native`. A rule test that uses
  the backend as preparation follows the backend it executes (`phase3_rules`
  for the modular item). Explicit `pytest.param(..., marks=...)` keeps the
  parametrization, the ids and the number of items unchanged.
- **Backend-specific suites.** Every functional item under
  `tests/engines/vectorized` is `phase5_vectorized` and under
  `tests/engines/native` is `phase6_native`, even when it asserts a rule,
  a KB-shaped value or an architecture/transport contract of that backend.
- **Test infrastructure versus product.** A mechanism that detects faults on
  synthetic inputs is `phase0_preflight`. A harness or mutation witness that
  drives the real pipeline is assigned to the phase of the product it exercises;
  certification and audit machinery (semantic audit, coverage baseline,
  coverage gate, provenance records) is `evidence`.
- **Architecture and bundle boundaries.** Source-boundary checks are
  `phase0_preflight`; a check of the built/published artefact is `packaging`.
- **Mixed files.** Per-case annotations keep each Python item in one category. A
  file-level unit that cannot be selected per test (Vitest) is assigned to one
  category; the choice and its limitation are stated in the runner section.

## Additional categories

These are real categories with their own marker/project, but they are **outside**
the functional sequence because they either need a built artefact, measure a
budget or certify records rather than exercise a product path.

| Category | What it proves | How it runs |
| --- | --- | --- |
| `evidence` | Coverage, provenance, inventory, semantic-audit and certification records are valid | `--extras` after the phases, or `--sequence-category evidence` |
| `packaging` | The built or published product contains the required usable artefacts | `--extras`, or `--sequence-category packaging` after a build |
| `performance` | A measured execution or delivery budget is met | `--extras`, or `--sequence-category performance` |

`--extras` appends all three after the selected functional phases, in the order
evidence → packaging → performance. It does not slip them into the functional
order and never runs them by default.

## Mechanisms

### Python markers and guard

The eleven categories are registered as pytest markers with descriptions in
`pyproject.toml`; `addopts = "--strict-markers"` rejects an unregistered marker.
`tests/conftest.py` holds the single guard over collected items under the
classified roots: it rejects an item with no category, with several, or with a
marker that is not a category (pytest's own `parametrize`, `skip`, `skipif`,
`xfail`, `usefixtures` and `filterwarnings` excluded). It reads no source text,
keeps no list of test names and reports the offending node IDs.

Classified roots:

| Root | Component |
| --- | --- |
| `tests/tooling/architecture` | package boundaries |
| `tests/applications/warband_manager/persistence/campaign_file` | campaign-file contracts |
| `tests/rules/knowledge` | KB, catalogues, editorial and translation |
| `tests/rules/construction` | roster construction and eligibility |
| `tests/applications/combat_lab/services` | Combat Lab application services and settings |
| `tests/applications/combat_lab/persistence` | Combat Lab saved state |
| `tests/applications/combat_lab/ui` | Combat Lab desktop UI |
| `tests/tooling/launcher`, `tests/applications/combat_lab/cli`, `tests/engines/parity/benchmarks` | launcher, tests and console |
| `tests/rules/knowledge/web` | generated web artefact, readers and vectors |
| `tests/engines/modular`, `tests/engines/vectorized`, `tests/engines/native`, `tests/engines/shared` | modular, vectorized and native execution |
| `tests/engines/parity`, `tests/tooling/verification`, `tests/tooling/evidence`, `tests/rules/integration` | audit, inventory, parity, consumers and verifiers |
| `tests/rules/integration/e2e` | declarative corpus, phase/variant suites and generator checks |

`tests/rules/integration/specs` remains declarative YAML test data. `tests/rules/integration/e2e`
loads its corpus during collection; an item that asserts a named refusal is
derived as `phase2_construction`, every observed declaration as
`phase4_modular`, from the declaration's explicit expectation channel. The
semantic specification runner derives each authored case from its reviewed
`roles`/`operation`/`category` metadata.

### Ordering plugin

`tools/verification/test_sequence.py` loads as a pytest plugin only through
`test-sequence`. It collects once, sorts items by the explicit category marker
and executes in that order. Ordering uses no path rule, no file-name rule, no
backend-name guess and no separate test inventory: a parametrized item is placed
by the marker it carries.

With `--workers 1` the sequence is one pytest session. With `--workers N > 1`
each selected category is a blocking pytest/xdist session (`--dist=loadfile`),
so all workers of a category finish before the next category starts. There is no
ordering between files inside a category.

Failure policy:

- the default continues after failures and returns pytest's nonzero status;
- `-x` / `--maxfail N` stop the current session (and therefore later categories
  when the failing category exits);
- collection, configuration, internal errors and interruption abort the
  sequence;
- an empty full run returns pytest's no-tests exit code; an empty selected
  category is reported as unvalidated and skipped.

### Commands

```text
python tools/mordheim-utils.py test-sequence --steps
python tools/mordheim-utils.py test-sequence -step0 -q
python tools/mordheim-utils.py test-sequence --step 2 --scope construction -q
python tools/mordheim-utils.py test-sequence --sequence-plan -qq
python tools/mordheim-utils.py test-sequence --sequence-from phase3_rules -q
python tools/mordheim-utils.py test-sequence -m "phase1_kb_contracts or phase2_construction" -q
python tools/mordheim-utils.py test-sequence --workers 4 -q
python tools/mordheim-utils.py test-sequence --workers 4 -q --output reports/tests.txt
python tools/mordheim-utils.py test-sequence -step2 --workers 4 -q
python tools/mordheim-utils.py test-sequence --extras -q
python tools/mordheim-utils.py test-sequence --sequence-category performance -q
```

Phase numbers are zero-based and match the table: `--step 0` .. `--step 7`.
`--output FILE` saves combined standard output and errors in a UTF-8 text file
while still displaying them on screen. It creates parent directories and
overwrites an existing file. It covers the whole invocation, including all
parallel phases and their final summary, and preserves the test exit status.
Relative report paths are resolved from the directory where the command is run.
`-stepN` is an alias. `--step` selects exactly one phase, not every phase up to
N, and can be combined with `--extras` to add the additional categories after it.
`--sequence-from` accepts a functional phase identifier (`phase0_preflight` ..
`phase7_warband`) and is sequential only. `--sequence-category` selects one
additional category and cannot be combined with `--step`, `--sequence-from` or
`--extras`. `--workers` manages `-n`/`--dist`; do not pass those directly.

The launcher forwards ordinary pytest filters (`-m`, `-k`, paths, `-q`,
`--maxfail`, `-x`), so a phase can be narrowed, for example
`-step5 --scope vectorized -m phase5_vectorized`. Filters do not add
prerequisites.

`--sequence-plan` collects and prints the ordered selection without executing a
test body. Plan mode still imports test modules and loads the semantic/E2E
corpora; `-qq` only reduces output. Use `--scope` to reduce collected roots, and
`--steps` when only the static phase list is needed. No success is cached.

### TypeScript and web suites

Both suites use the runner's native project mechanism; the installed Vitest
3.2.7 exposes no per-test tag, so the category is selected per file.

`packages/typescript/vitest.config.ts`:

| Project | Files |
| --- | --- |
| `phase0_preflight` | `tests/tooling/architecture/purity.test.ts` |
| `phase1_kb_contracts` | `tests/rules/knowledge/parity-kb-vectors.test.ts` |
| `phase7_warband` | `tests/applications/warband_manager/domain/**/*.test.ts`, `tests/applications/warband_manager/application/**/*.test.ts`, `tests/applications/warband_manager/adapters/**/*.test.ts` and `tests/applications/warband_manager/parity-vectors.test.ts` |

`apps/warband-manager-web/vite.config.ts` (invoked from that directory):

| Project | Files |
| --- | --- |
| `phase0_preflight` | `tests/tooling/architecture/web-boundaries.test.ts` |
| `packaging` | `tests/applications/warband_manager/packaging/font-publication.test.ts` and `tests/applications/warband_manager/packaging/bundle-boundaries.test.ts` |
| `phase7_warband` | `tests/applications/warband_manager/features/**/*.test.{ts,tsx}`, `tests/applications/warband_manager/presentation/**/*.test.{ts,tsx}` and `tests/tooling/web/**/*.test.{ts,tsx}` |

```text
cd packages/typescript && npx vitest run --project phase7_warband
cd apps/warband-manager-web && npx vitest run --project phase7_warband
```

The default `vitest run` (and `npm test`) still runs every project. Test and
suite identities, parametrizations and worker settings are unchanged. The web
suite must be invoked from `apps/warband-manager-web`: its absolute include
patterns resolve the generated artefacts from `process.cwd()`.

Limits of this runner:

- There is no per-test tag, so a file is the smallest selectable unit. The
  source-boundary checks in `tests/tooling/architecture/web-boundaries.test.ts`
  stay in `phase0_preflight`; the post-build bundle guards live in
  `tests/applications/warband_manager/packaging/bundle-boundaries.test.ts`,
  skip when no build exists and are selected by `packaging`. The minimal change
  for per-test selection is a newer Vitest with
  test tags, or a category token in the file name
  (`<name>.<category>.test.ts`) with one project per token, which renames files
  and changes every Vitest report identity.
- The Python launcher does not schedule the TypeScript/web projects. Running
  `test-sequence` sequences Python only; the commands above select the same
  phase names in the other runners.
- `node:test` exposes only `--test-name-pattern`; no maintained suite currently
  uses it.

## Verification performed on 2026-10-21

Collection and plan only; no functional battery was executed to decide or
validate this classification.

- Full Python suite: **13,029 collected items**. Every item was counted in
  exactly one category; the sum of the category counts equals the collection.
- Python partition (`--sequence-plan --extras`): `phase0_preflight` 88,
  `phase1_kb_contracts` 834, `phase2_construction` 2,731, `phase3_rules` 3,485,
  `phase4_modular` 5,425, `phase5_vectorized` 171, `phase6_native` 38,
  `phase7_warband` 143, `evidence` 106, `packaging` 1, `performance` 7.
- Ordered collection is monotonic across the eight phases; the last item of each
  phase precedes the first item of the next one (first/last collected indexes:
  0–87, 88–921, 922–3652, 3653–7137, 7138–12562, 12563–12733, 12734–12771,
  12772–12914; the additional categories follow when selected).
- All 132 functional items under `tests/python/combat/vectorized` are
  `phase5_vectorized` (its two coverage-catalogue checks remain `evidence`); all
  12 collected items under `tests/python/combat/native` are `phase6_native`.
  Backend-parametrized items keep their ids and split as intended, e.g.
  `...[modular]` → `phase4_modular`, `...[numpy]` → `phase5_vectorized`,
  `...[native]` → `phase6_native`.
- Identity comparison against the pre-change inventory (13,024 items): three new
  launcher checks were added and one obsolete launcher check was replaced (net
  +2), and three vectorized regression tests were added concurrently (net +3,
  net total 13,029). No other node ID changed, and no existing parametrization id
  changed.
- TypeScript: 964 collected items (2 `phase0_preflight`, 18
  `phase1_kb_contracts`, 944 `phase7_warband`); web: 444 items (5
  `phase0_preflight`, 2 `packaging`, 437 `phase7_warband`). The projects are
  disjoint and their sum equals the default collection of each config.
- Not established: that the batteries pass, that phases are correctly ordered
  for a particular defect, or repository-wide certification. Collection proves
  selection, not behaviour.

## Limits

- Collection imports modules and loads declarative corpora even in plan mode;
  collection errors remain failures.
- Selections do not expand to prerequisites and do not prepare generated inputs
  or builds; a phase can be selected without its inputs.
- The launcher sequences Python only. TypeScript/web categories are selectable
  by project but are not part of that ordered session.
- A skipped test keeps its category but proves nothing. Native availability and
  missing generated artefacts are environment preconditions, not passing
  evidence.
- Mixed Python files are selected per case; a mixed Vitest file is selected as a
  whole (see the runner limits above).
- `evidence` is outside the default sequence. A default phase run does not
  validate the semantic audit, coverage baseline or coverage gate.
- A test added to a classified root without a category fails collection by
  design; that is the only enforcement of completeness.
