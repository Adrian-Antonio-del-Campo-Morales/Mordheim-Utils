# Develop and release

Two loops: a fast local loop after a focused change, and the certification
gates that run rarely (engine changes, releases). Commands assume an editable
Python install and installed Node dependencies; `python tools/mordheim-utils.py
doctor` reports what is actually available.

## Fast development loop

```powershell
python tools/mordheim-utils.py verify --structural   # KB change only
python tools/mordheim-utils.py tests --scope deterministic
```

For TypeScript/web changes:

```powershell
npm run typecheck    # TypeScript packages and web app
npm test             # both Vitest suites
npm run lint         # ESLint over the workspace + the presentation gate
npm run build        # the web app: typecheck + Vite build
```

They run from the repository root and fan out to the npm workspaces; the
per-workspace forms (`npm test --workspace campaign-web-core`) still work when a
single suite is what changed.

Narrower Python scopes: `tests --scope campaign`, `knowledge`, `construction`,
`ui`, `cli`, `architecture`. `tests --scope all` runs the complete Python
suite; anything after the scope is forwarded to pytest.

## Knowledge artefact

The browser consumes generated JSON, not YAML. Rebuild and check it when
changing canonical knowledge or the generator:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

The generated browser knowledge files live in `outputs/web-public/knowledge/`
and are ignored;
`run-ci` and CI generate them before running the browser checks.

## Full CI-equivalent gate

```powershell
python tools/mordheim-utils.py run-ci
```

Runs the knowledge generator/check, the Python contract/campaign/architecture/
knowledge/web tests, the TypeScript typecheck/tests and the web
typecheck/lint/tests/build plus the post-build bundle guard — the same steps as
`.github/workflows/ci.yml`.

## Verification and certification

The modular engine is the scalar correctness oracle; NumPy and native are
candidates. What each layer can and cannot prove is
[Verification](../reference/verification.md).

```powershell
python tools/mordheim-utils.py verify --require-complete
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py coverage-gate
python tools/verification/mutate-engine.py
```

`parity --level statistical` adds the standard six-sigma sample;
`parity --level deep --pair-set fast|full` runs the curated archetype matrix,
with `--truncations` for round-horizon checks. These take minutes to hours and
belong to engine changes and releases, never to the per-change loop.

Generated reports live under ignored `outputs/` — never hand-edit them:

- `audit/` — per-rule inventory (`report rules`).
- `test-report/` — semantic and technical CSVs (`report tests`).
- `parity/` — JSON/Markdown parity certificates.
- `benchmarks/` — benchmark results.

## Performance work

Benchmark changes against a saved baseline:

```powershell
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The gate's thresholds belong to the command, not to this document. Store raw
results under ignored `outputs/benchmarks/`; do not copy measured throughput or
machine-specific optima into maintained documentation.

Calibrate after hardware, engine or combat-rule changes:

```powershell
python tools/mordheim-utils.py calibrate
python tools/mordheim-utils.py calibrate --pairs mini
python tools/mordheim-utils.py calibrate --reset         # drop the profile
```

The command installs `calibration.json` beside the local preferences. Use
`--no-install` for a read-only study, `--output PATH` for the full evidence and
`--json` for machine-readable output. A parity failure invalidates timing
results and must be fixed before interpreting performance.

## Windows packaging

Install the dev extra, verify the desktop dependencies/Tkinter, then run the
relevant script:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCombatLab_INSTALLER.bat
```

The scripts build Combat Lab from the current source checkout. They are not CI
deployment commands.

## Release checklist

- [ ] Fast relevant tests pass.
- [ ] `verify --require-complete` passes (structural + semantic).
- [ ] TypeScript/web checks pass when applicable.
- [ ] Contract fixtures and generated knowledge artefacts validate when applicable.
- [ ] Engine changes have the required parity/coverage/mutation evidence.
- [ ] No generated reports, `outputs/`, `dist/`, screenshots or temporary campaign files are staged.
- [ ] Windows packages are smoke-tested when a desktop release is required.

See [Verification](../reference/verification.md) for what each gate can and
cannot prove.
