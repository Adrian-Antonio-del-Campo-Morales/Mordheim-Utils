# Develop and distribute

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
python -m mordheim_combat_lab test-report
```

`verify` accepts pending items; `--require-complete` does not. `test-report`
generates the human CSVs of parity and technical tests; use
`test-report --require-complete` as the strict gate when the optimized backend
must be fully certified. See
[Generate test and parity reports](generate-test-reports.md).

Before optimizing, save a reproducible baseline:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
```

After the change, run the same configuration and enable the agreed gate:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The gate requires a 10 % improvement in some scenario without degrading another
by more than 5 %. Finally, build Windows with
`tools\windows\build_MordheimCombatLab_ONEFILE.bat`.

Done when tests and validation pass, the semantic status does not regress, and
the package bundles the KB but neither the specifications nor historical files.
