# Engine parity: deliveries, stored samples and campaigns

| | Parity deliveries / delivery parity campaigns |
|---|---|
| Question answered | Do the NumPy and native engines produce the same outcome distributions as the modular engine? |
| Oracle | The modular engine (statistical six-sigma gate on first-win/second-win/unresolved rates) |
| Dice | Random (seeded), many duels per configuration (stored campaigns: 100,000 per delivery) |
| Unit of accounting | Delivery (one frozen duel configuration) and its outcome distribution |
| Runs | Deliberate CLI campaigns (`check parity`, `check samples`); `tests parity` checks the infrastructure with small comparisons, never parity proof |
| Lives in | `tests/engines/parity/` (deliveries, reference_samples, statistical tests) + `tools/verification/parity_deliveries.py`, `parity_catalog.py`, `parity_samples.py` |

The deliveries are derived from the [rules-conformance suite](../../conformance/README.md),
which checks the printed rules with scripted dice; see
[Test suites at a glance](../../../docs/reference/verification.md#test-suites-at-a-glance)
for how the two relate.

## Layout

| Path | Responsibility |
|---|---|
| `deliveries/` | Frozen parity deliveries, one `<sha256(case_key UTF-8)>.json` per translated conformance scenario. |
| `reference_samples/` | Versioned sample stores (oracle and candidate outcome counts). |
| `statistical/` | Pytest contracts of the catalogue, deliveries, sample store and reports, plus small six-sigma comparisons on frozen scenarios. |
| `conftest.py` | Loads the frozen corpus `tests/engines/fixtures/compiled-cases.json` once per session (`cases` fixture); never compiles. |
| `tools/verification/parity_deliveries.py` | Delivery index, validation against the current conformance YAML, admission, `CAMPAIGN_MAXIMUM_ROUNDS`. |
| `tools/verification/parity_catalog.py` | The shared `--scenarios` vocabulary: resolves tokens to runnable cases and lists every case it cannot run, with its reason. |
| `tools/verification/parity_samples.py` | Chunked per-engine sample stores (`sample`, resume, `status`) and the comparison of stored samples. |

## Input sources for `--scenarios`

Several values select their union, in the order given. Unknown tokens are
reported as unknown immediately; only `deliveries`, `delivery/...` keys and
`<audit_id>::<id>` ids consult the delivery catalogue (`is_delivery_token`).

| Source | Tokens | Origin |
|---|---|---|
| Precompiled scenarios | `small`, `normal`, `big` (8, 30, 43); `<name>` or `scenario/<name>` | Frozen fighters in `compiled-cases.json`; never compiled. |
| Curated realistic duels | `realistic-50`, `realistic-100`; `realistic/<nnn>` | Frozen corpus cases (`tests/engines/fixtures/realistic_sets.py`). |
| Parity deliveries | `deliveries`; `delivery/<audit_id>/<id>` or `<audit_id>::<id>` | `deliveries/`, through the admission rules below. |
| Statistical battery | `battery`; `battery/<id>` | 122 short duels compiled from the knowledge base. |

## Parity deliveries

Lifecycle: conformance scenario -> translation (compiled once with the
`export_cases` API; preparation, not execution) -> frozen delivery ->
admission -> sample -> verdict. A translated delivery is never proof of
engine compatibility or of the original scenario's expectations.

A `mordheim-parity-delivery/v2` document has exactly the fields `schema`,
`status` (`translated`, `blocked`, `not-applicable`), `source` (`revision`,
`path`, `sha256`, `test_id`), `case_key`, `case`, `decision_policy`,
`magnitudes` (`["winner"]`) and `reason`. The normative table is in
[Parity deliveries](../../../docs/reference/verification.md#parity-deliveries);
see the [example](../../../docs/examples/parity-delivery.json).

- **Kept:** both fighters, the context (including local participants),
  initial state, auxiliary participants and the original `maximum_rounds`.
- **Stripped:** scripted dice and decisions (empty), `expectations` and
  `benchmark` (null); `limits` declare only `maximum_rounds`. Translated
  entries use `decision_policy = {"kind": "engine-default"}` and
  `reason = null`; the others carry `case = null` and a nonempty reason.
- **Keys:** `case_key` is `delivery/<audit_id>/<id>`, `source.test_id` is
  `<audit_id>::<id>`, the filename is `sha256(case_key UTF-8).json`, and
  `case.origin.kind` is `conformance` with origin path/node/sha matching
  `source`.
- **Freshness:** `source.sha256` pins the conformance YAML bytes. Editing a
  scenario makes its delivery `stale` until it is re-translated; a matching key
  alone does not prove freshness. A `source.revision` different from HEAD is a
  warning only.

Admission states (`admit`):

| State | Meaning |
|---|---|
| `admitted` | The frozen inputs execute as they stand. |
| `blocked` / `not-applicable` | Declared by the delivery itself; its reason is preserved. |
| `incompatible` | An input the runner cannot express (initial state, auxiliary participants, scripted input) or non-corresponding default decision policies. |
| `stale` / `invalid` | No longer matches its source YAML, or malformed. |
| `policy-unverified` | The decision-policy probe raised; correspondence unknown. |

Campaigns run every admitted delivery to `CAMPAIGN_MAXIMUM_ROUNDS` = 50 rounds,
independently of the stored original horizon. Every rejected case stays in the
report with its reason.

Current counts: 5,161 deliveries = 4,167 translated, 530 blocked, 464
not-applicable; 11 are stale (8 KAZ goblin, 3 Extra Arm).

## Stored samples and reference stores

A store is laid out as `<store>/<engine>/<file>` (`modular`, `numpy`,
`native`). `sample_path` names delivery records
`delivery__<sha256(case_key)>.json.gz` (short Windows paths) and every other
record `<key with / -> __>.json[.gz]`. Each record holds `engine`,
`corpus_key`, `scenario`, `seed`, `maximum_rounds`, `chunk_size`,
`inputs_sha256`, `engine_digest`, `environment`, `created_at` and `chunks`
(`start`, `count`, `first`, `second`, `unresolved`, `seconds`,
`completed_at`, optional per-chunk provenance). Stores keep winner counts only.

| Store | Holds |
|---|---|
| `modular-100k` | Modular oracle for the 43 precompiled scenarios, 100,000 duels each. |
| `numpy-big-200k` | NumPy self-reference over the 43 `big` scenarios, 200,000 duels each; no oracle (see its [README](reference_samples/numpy-big-200k/README.md)). |
| `modular-deliveries-100k` | Modular oracle, 2,678 delivery records. |
| `numpy-deliveries-100k` | NumPy candidate, 2,678 delivery records. |
| `native-deliveries-100k` | Native candidate, 2,678 delivery records. |

The delivery stores hold 100,000 duels per record in ten 10,000-duel chunks,
seed 2026, 50-round limit. Recorded verdicts against the modular store: NumPy
2,677 approved / 1 divergent; native 2,567 approved / 111 divergent. These are
stored candidate results, not parity acceptance.

`compare` executes no engine: it checks fingerprints, seeds, round limits and
coverage, then applies the six-sigma gate; fewer than 7,200 duels is
`underpowered`, never approved. Provenance differences only warn.

## Running

```bash
python tools/mordheim-utils.py tests parity
```

runs the statistical and tooling tests: contracts and small comparisons of
the infrastructure, not parity proof.

Real campaigns are deliberate, long runs (`check parity`, `check samples
sample|compare|status`); all options are in
[Delivery parity campaigns](../../../docs/reference/tools.md#delivery-parity-campaigns).

```bash
# Compare stored NumPy delivery samples with the modular oracle (no engine runs)
python tools/mordheim-utils.py check samples compare --backend numpy --scenarios deliveries --simulations 100k --store tests/engines/parity/reference_samples/numpy-deliveries-100k --reference-store tests/engines/parity/reference_samples/modular-deliveries-100k --output outputs/parity-deliveries-stored/compare
# Sample (or resume) a modular delivery store
python tools/mordheim-utils.py check samples sample --backend modular --scenarios deliveries --simulations 100k --batch-size 500 --workers 2 --store outputs/parity-modular-deliveries
# Coverage of a store
python tools/mordheim-utils.py check samples status --scenarios deliveries --store outputs/parity-modular-deliveries
```
