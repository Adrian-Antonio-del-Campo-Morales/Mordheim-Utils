# Develop and release

This guide distinguishes the fast development loop from the expensive certification gates. Commands assume an editable Python install and installed Node dependencies.

## Fast development loop

After a focused change, run the smallest relevant checks first:

```powershell
python tools/mordheim-utils.py validate
python tools/mordheim-utils.py tests --scope deterministic
```

For TypeScript/web changes:

```powershell
cd packages/typescript
npm run typecheck
npm test
cd ../../apps/warband-manager-web
npm run typecheck
npm run lint
npm test
npm run build
```

Use `tests --scope campaign`, `knowledge`, `construction`, `ui`, `cli` or `architecture` when the change is narrower. `tests --scope all` runs the complete Python suite.

## Knowledge artefact

The browser consumes generated JSON, not YAML. Rebuild and check it when changing canonical knowledge or the generator:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

The generator writes `build/generated/knowledge-web/`; `run-ci` stages the JSON into `apps/warband-manager-web/public/knowledge/`. Both locations are generated and ignored.

## Full CI-equivalent gate

```powershell
python tools/mordheim-utils.py run-ci
```

This runs the knowledge generator/check, Python contract/campaign/architecture/knowledge/web tests, TypeScript typecheck/tests and web typecheck/lint/tests/build plus the post-build bundle guard. CI uses the equivalent steps in `.github/workflows/ci.yml`.

## Combat verification and certification

The modular engine is the scalar correctness oracle. NumPy and native are candidates.

```powershell
python tools/mordheim-utils.py verify --require-complete
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py coverage-gate
python tools/mutate-engine.py
```

Use `parity --level statistical` for the standard statistical sample. Use `parity --level deep --pair-set fast` or `--pair-set full` for the curated interaction matrix; add `--truncations` for round-horizon checks. These can take minutes or hours and should be run after engine changes or before a release, not after every documentation/editing change.

Reports are generated under ignored `outputs/`:

- `audit/` — per-rule inventory (`python tools/mordheim-utils.py audit`).
- `test-report/` — semantic and technical CSVs.
- `parity/` — JSON/Markdown parity certificates.
- `benchmarks/` — benchmark results.

Never hand-edit those reports. The command output is the current status.

## Performance baseline

For a single configuration:

```powershell
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The default gate requires a 10% improvement in at least one scenario and no regression above 5%; adjust thresholds only when the change justifies it.

## Windows packaging

Install the dev extra, verify the desktop dependencies/Tkinter, then run the relevant script:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

The scripts build standalone EXEs from the current `packages/python`/`apps` layout and bundle `sources/knowledge/`. They are not CI deployment commands.

## Release checklist

- [ ] Fast relevant tests pass.
- [ ] `validate` and `verify --require-complete` pass.
- [ ] TypeScript/web checks pass when applicable.
- [ ] Contract fixtures and generated knowledge artefacts validate when applicable.
- [ ] Engine changes have the required parity/coverage/mutation evidence.
- [ ] No generated reports, `dist/`, `build/generated/`, screenshots or temporary campaign files are staged.
- [ ] Windows packages are smoke-tested when a desktop release is required.

See [Verification](../reference/verification.md) for what each gate can and cannot prove.
