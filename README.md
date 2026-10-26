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

For runtime tests that exercise internal process pools, use `-n 0` to avoid
multiplying engine processes by pytest workers. To select one test, pass
`path/to/test_file.py::test_name` instead of a directory.

The latest complete serial run reported **1485 passed in 40.40 seconds**.
This verifies the retained tests; it does not establish complete rule coverage
or statistical equivalence between the engines.

## Precompiled inputs

Tests load frozen inputs from `tests/engines/fixtures/`:

- `compiled-cases.json`: prepared fighter pairs and case metadata.
- `compiled-builds.json`: prepared fighters indexed by build request.
- `compiled-cases.manifest.json`: corpus provenance and fingerprints.
- `precompiled_catalog.py`: scenario definitions and historical case keys.

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
