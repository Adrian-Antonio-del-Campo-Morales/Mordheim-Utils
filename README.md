# Mordheim combat engines

Modular and NumPy combat engines with shared models and precompiled test inputs.
Requires Python 3.10 or later.

## Installation

Run the commands from the repository root. Creating a fresh environment avoids
reusing dependencies from other projects.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

The engine dependency is NumPy. The `dev` extra installs pytest and pytest-xdist.
The following examples use Windows paths; on Linux or macOS replace
`.\.venv\Scripts\python.exe` with `.venv/bin/python`.

## Running tests

Collect all tests without executing them:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```

Run all tests in series:

```powershell
.\.venv\Scripts\python.exe -u -m pytest -n 0 -q --durations=10 --tb=short
```

Run a selected suite with eight pytest workers:

```powershell
.\.venv\Scripts\python.exe -u -m pytest tests/engines/modular/mechanics -n 8 --dist=load -q --durations=10 --tb=short
```

Replace the path to select another suite:

| Path | Purpose |
|---|---|
| `tests/engines/modular/mechanics` | Application of combat rules in the modular engine |
| `tests/engines/modular/runtime` | Modular simulation, observations and execution contracts |
| `tests/engines/vectorized/mechanics` | Rule operators and combat behavior in NumPy |
| `tests/engines/vectorized/runtime` | NumPy batching, random inputs and execution contracts |
| `tests/engines/shared` | Shared contracts and precompiled-data checks |
| `tests/engines/parity` | Modular-to-NumPy statistical parity, round truncation, campaign catalogue and reports |

For runtime tests that exercise internal process pools, use `-n 0` to avoid
multiplying engine processes by pytest workers. To select one test, pass
`path/to/test_file.py::test_name` instead of a directory.

The cross-engine statistical comparison samples the modular oracle against the
NumPy backend, so it is timing-sensitive and CPU-bound. Run it in series:

```powershell
.\.venv\Scripts\python.exe -u -m pytest tests/engines/parity -n 0 -q --durations=10 --tb=short
```

These five tests compare outcome rates with the six-sigma tolerance (0.25%
floor) on two frozen scenarios; they are not a full-corpus campaign. The same
directory also holds the campaign's catalogue and report contracts, which load
frozen cases only and sample no engine.

## Statistical parity campaign

The campaign command runs the modular oracle against the NumPy backend over the
frozen catalogue: 43 scenarios under uniform `scenario/<name>` keys, selected
as three cumulative levels. It writes a complete JSON and Markdown report to
the output directory.

The levels are cumulative and `small` is the default: `small` (8 cheap
scenarios), `normal` (30, one representative per rule family) and `long` (43,
every scenario, including the 75-round grinds and the largest attack pools). A
level selects scenarios only; every scenario keeps its own frozen round limit.

Run the default `small` set with eight oracle workers:

```powershell
.\.venv\Scripts\python.exe -m tools.verification.parity_campaign --workers 8 --simulations 1000 --output reports/parity-small
```

Run `normal` and then the whole catalogue:

```powershell
.\.venv\Scripts\python.exe -m tools.verification.parity_campaign --level normal --workers 8 --simulations 1000 --output reports/parity-normal
.\.venv\Scripts\python.exe -m tools.verification.parity_campaign --level long --workers 8 --simulations 1000 --output reports/parity-long
```

Run the same selection in series, or narrow it to concrete scenario keys:

```powershell
.\.venv\Scripts\python.exe -m tools.verification.parity_campaign --workers 1 --simulations 1000 --output reports/parity-small
.\.venv\Scripts\python.exe -m tools.verification.parity_campaign --id scenario/basic --id scenario/long --workers 8 --simulations 5000 --output reports/parity-basic
```

The report is written to `parity-campaign.json` and `parity-campaign.md` under
`--output`. It records the configuration (level, keys, simulations, seed,
workers, round budget, corpus digest), one row per scenario with its corpus
key, sample width, the three outcome rates of each engine, tolerances,
differences, timings and verdict. `--simulations` sets one width for the
selected set (default 1,000); it is execution configuration, not scenario
data. `--seed` defaults to 2,026 and each scenario keeps its frozen round
budget unless `--rounds` overrides it. `--workers auto` pools only samples
estimated to take over about 20 seconds sequentially.

A scenario is reported as `pass` only when both samples were obtained and every
compared magnitude stayed within tolerance; `divergent` means the comparison
was performed and failed, and `not-run` means it was never performed. Rejected
or missing corpus entries are listed explicitly, and a candidate admission
refusal is reported as `INCOMPATIBLE` with its reason rather than as a parity
failure. The report sets `certification_sample_complete` only when every row
reached 100,000 duels per engine, so a narrower campaign is not presented as a
certification. The exit code is 0 only when every selected scenario was
compared and approved, 1 when the campaign ran but is incomplete, and 2 for a
configuration or corpus error.

The parity support tests are the `tests/engines/parity` command above: the five
statistical comparisons plus the campaign's catalogue and report contracts.

A green run verifies the retained tests; it does not establish complete rule
coverage or statistical equivalence between the engines. Parity is only
claimed for the scenarios and sample widths a campaign actually reports.

## Precompiled inputs

Tests load frozen inputs from `tests/engines/fixtures/`:

- `compiled-cases.json`: prepared fighter pairs and case metadata.
- `compiled-builds.json`: prepared fighters indexed by build request.
- `compiled-cases.manifest.json`: corpus provenance and fingerprints.
- `precompiled_catalog.py`: the 43 scenario definitions, their `scenario/<name>`
  corpus keys and the three cumulative selection levels.

Test execution does not require a knowledge base or construction compiler.
Missing frozen entries fail explicitly; loaders do not compile replacements.
Keep the JSON files when copying the project to another environment.

## Source layout

| Path | Contents |
|---|---|
| `packages/python/combat-engine/mordheim_combat/modular` | Modular combat implementation |
| `packages/python/combat-engine/mordheim_combat/vectorized` | NumPy combat implementation |
| `packages/python/core/mordheim_core` | Shared models, context, dice and effects |
| `tests/engines/shared/dice.py` | Strict scripted dice and decisions for tests |
| `tests/engines/modular/replay.py` | Scripted modular execution helper |
| `tools/verification/compiled_cases.py` | Frozen-case codec and loader |
| `tools/verification/compiled_builds.py` | Frozen-build loader |
| `tools/verification/parity_statistical.py` | Modular-to-NumPy statistical comparison and its result record |
| `tools/verification/parity_runner.py` | Parity runner for cases, worker policy and round-truncation horizons |
| `tools/verification/parity_catalog.py` | The 43 frozen scenarios, their corpus keys and selection rules |
| `tools/verification/parity_campaign.py` | Campaign command, JSON/Markdown report and CLI |
