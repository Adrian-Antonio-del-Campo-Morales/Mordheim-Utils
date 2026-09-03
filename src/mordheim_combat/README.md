# Combat

Phases, modular and vectorized engines. Consumes compiled fighters and never
loads YAML. See [Architecture](../../../docs/architecture.md).

## Parity between engines

Semantic evidence belongs to the modular engine. The vectorized engine used by
the UI is certified separately with `python -m mordheim_combat_lab parity`:
every field, tag and complex sequence of the oracle must have a vectorized
consumer and evidence.

The former `Poisonous` and secondary-weapon Initiative divergences are covered
by explicit regressions. A rule may keep running while its parity is pending,
but it cannot enter a new or optimized execution path until it is certified.

The KB and the modular engine are the protected oracle. A divergence detected
while working on the vectorized engine is presumed to be a defect of the
candidate: `parity` only reads the oracle and never modifies it. Changing the
oracle requires an independent semantic review and is outside the optimization
flow.

## Reports

`python -m mordheim_combat_lab test-report` runs the parity inventory and the
technical suite and writes Excel-ready CSVs to `outputs/test-report/`. The
semantic report places the modular, NumPy and native results and statuses side
by side. A `PENDING` status is not a divergence: it may mean the vectorized
adapter is missing or that the native backend is not yet available. The
per-operator cases do not apply to the native engine (`NOT_APPLICABLE`, a
complete duel engine): its certification lives in the per-scenario statistical
rows and in `parity --statistical`, where it shares the modular-oracle sample
with NumPy and must pass the same six-sigma gate.

The full guide of options and statuses is in
[Generate test and parity reports](../../../docs/tasks/generate-test-reports.md).
