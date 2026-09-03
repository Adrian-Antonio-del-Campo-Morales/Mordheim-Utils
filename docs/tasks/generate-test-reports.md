# Generating test and parity reports

The recommended human-readable report is produced with:

```powershell
python -m mordheim_combat_lab test-report
```

The command runs semantic parity and the whole technical suite. It writes two
files under `outputs/test-report/`:

- `semantic-parity.csv`: the spec cases compared between the modular engine,
  NumPy and the native backend.
- `technical-tests.csv`: all the tests collected by `pytest`, including the
  parametrized ones, their duration and any error.

The CSVs use UTF-8 with BOM and `;` as separator. They are sanitized so that
line breaks, control characters or formula prefixes never break their display
in Excel.

## Options

```powershell
python -m mordheim_combat_lab test-report --output outputs/my-report
python -m mordheim_combat_lab test-report --require-complete
python -m mordheim_combat_lab test-report --statistical --statistical-simulations 100000 --seed 2026
```

| Option | Use |
| --- | --- |
| `--output DIRECTORY` | Changes the directory of both CSVs. |
| `--require-complete` | Also returns an error if adapters or the native backend are missing. |
| `--statistical` | Adds the five statistical scenarios to the semantic CSV. |
| `--statistical-simulations N` | Duels per engine and scenario; 100,000 by default. |
| `--seed N` | Seed for the statistical comparisons. |

Without `--require-complete`, a pending item does not fail the command. A
semantic divergence, a technical failure or a `pytest` error do produce a
non-zero exit code. The files are written even when the run fails, so the
diagnostics are preserved.

## Reading `semantic-parity.csv`

Each row is one semantic case. The result columns appear together, followed by
the status columns:

```text
modular_result | numpy_result | native_result
modular_status | numpy_status | native_status | passes
```

`expected` holds the expected observable and `rules` identifies the rules or
mechanics that justify the case. `details` is only filled when there is a
limitation or an error worth explaining.

Global `passes` states:

| State | Meaning |
| --- | --- |
| `PASS` | All applicable implementations agree. |
| `FAIL` | There is a real divergence or error. |
| `PENDING` | An adapter, a semantic decision or a backend is missing. |
| `OUT_OF_SCOPE` | The rule is excluded from the current runtime. |

Specific states such as `PASS_SHARED`, `NOT_APPLICABLE`,
`PENDING_ADAPTER`, `PENDING_SEMANTIC` and `NOT_AVAILABLE` explain why the
global state was reached. `PASS_SHARED` means the engines consume the same
compiler result; it does not represent two independent implementations.
`NOT_APPLICABLE` marks a case that an engine does not execute by design: the
native backend is a full-duel engine without standalone operators, so
per-operator cases show `NOT_APPLICABLE` for it and its certification appears
in the per-scenario statistical rows. When the native extension is not
compiled those rows are marked `NOT_AVAILABLE` and the report stays `PENDING`
until the backend exists.

## Other related commands

For a quick check without running `pytest` or generating CSVs:

```powershell
python -m mordheim_combat_lab parity
```

To require full parity and save the machine certificate as JSON:

```powershell
python -m mordheim_combat_lab parity --require-complete --output outputs/parity/report.json
```

`parity --statistical` runs the same aggregate comparisons as
`test-report --statistical`. A sample below two million duels per engine is
considered diagnostic, not a certification.

To measure performance without certifying rules:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --save-baseline outputs/benchmarks/numpy-before.json
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

`benchmark` accepts `modular`, `numpy`, `native` and `all`. Each JSON report includes the
configuration, the individual samples, the median, simulations per second and environment
data. A baseline is only compared when seed, batch size, warm-ups, repeats and number of
simulations match.

The performance gate applies the criteria of the optimized-engine development:

- at least one comparable scenario must improve by 10 %;
- no comparable scenario may regress by more than 5 %.

The thresholds can be tuned with `--min-improvement` and `--max-regression`. Without
`--require-improvement`, a failed comparison is shown and saved to the report, but does not
change the exit code. It is advisable to close intensive applications and run baseline and
candidate on the same machine under the same conditions.
