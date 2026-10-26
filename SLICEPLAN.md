# Slice: first removal pass

- Active branch: `vectorized-slice`.
- Base: `origin/main`, merge `efbe40ee` (test rework PR #4).
- Previous slice preserved at `refs/archive/vectorized-slice-before-rebuild-20261026`.
- Removed versioned application, KB, compiler, TypeScript, documentation/CI,
  native-engine, integration, parity and tooling trees outside the slice.
- Kept modular/NumPy/core, their mechanics/runtime/shared tests, frozen JSON,
  precompiled catalogue and loaders. Frozen data was not regenerated or edited.
- Reduced packaging to the two Python packages, NumPy, pytest and xdist;
  removed the native build and application entry point.

## Next step

Repair only what the retained precompiled tests need: imports, helper placement,
and residual compiler/KB/native preparation. Do not restore entire removed
components or rescue tests outside this scope. Execution dependencies have not
been audited in this pass.

## Limits

No tests, collection, simulations, installation or functional checks were run.
An automated approval review initially rejected bulk filesystem deletion.
Tracked removals used git rm. The user subsequently requested a fresh-start
cleanup: after reviewing git clean -ndX, git clean -fdX removed the local venv,
node_modules, outputs, egg-info and ignored caches/remnants of deleted trees.
The follow-up ignored-file preview was empty. Frozen JSON files stayed intact.
No commits or pushes were made in this pass.

## First easy dependency repairs

- Reused the previous slice's strict dice/decisions helper under
  tools/verification/strict_dice.py, including its local EvidenceMismatch.
- Extracted only modular scripted-duel execution into tools/verification/replay.py;
  optimized/native replay and cross-engine comparisons were not restored.
- Repointed helper imports in 52 test files and removed four unused imports
  of deleted application, KB and native modules.
- Four files still directly import deleted components (native/app-dependent
  runtime checks, catalogue checks and shared application helpers). Left for
  a separate scope decision; no engines, frozen JSON or assertions were changed.
- Static parsing only; no tests, collection, installs or simulations executed.

## Helper ownership

The two extracted helpers now live in existing engine-test directories:
`tests/engines/shared/dice.py` and `tests/engines/modular/replay.py`.
Engine-test imports were updated; the temporary tools/verification copies
were moved, not retained. See MAIN_HELPER_MOVES.md for the main-branch handoff.
No tests or collection were run.

## Remove final direct application/native dependencies

Removed the application catalogue check from modular mechanics and native
compile_duel calls/backend parameter cases from the two mixed modular runtime
files. Removed app attribute-improvement assertions and the mixed parallel/app
orchestration test from shared/contracts/test_duel_context.py. Main handoff:
MAIN_HELPER_MOVES.md. Separate engine parallel-runtime suites remain intact.
No tests or collection executed.
