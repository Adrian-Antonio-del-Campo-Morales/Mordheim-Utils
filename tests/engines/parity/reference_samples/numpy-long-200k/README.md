# `numpy-long-200k` — NumPy self-reference outcome store

The NumPy engine's own statistical outcomes over the 43 `long` scenarios,
200,000 duels each (8,600,000 duels), recorded **before** the rule-algorithm
optimization work so a later revision can be checked against the engine as it
behaved here.

**This store is not a certification.** It carries no oracle: it was produced by
the candidate engine alone, so it proves reproducibility, not correctness.
Modular remains the only correctness oracle, and
`tests/engines/parity/reference_samples/modular-100k` remains the reference for
the 43-scenario campaign. A change that keeps this store's counts has not been
shown to agree with the oracle; it has been shown not to have moved.

## Measurement design

| Field | Value |
| --- | --- |
| Engine | NumPy (`vectorized`), digest `cd08479214200888d635b096fb55ae415e3106c888833acca0affc301ba2aaa4` |
| Level | `long` (all 43 precompiled scenarios) |
| Duels | 200,000 per scenario, in 2 chunks of 100,000 |
| Chunk / batch | 100,000 — the measured NumPy optimum and the app default |
| Seed | 2026 (the tool derives the candidate seed as `seed + 1000003`) |
| Round budget | each scenario's frozen limit (50, or 75 for `long` and `heavy-grind`) |
| Commit | `bf433764`, clean tree |
| Machine | i5-11400H (12 threads, `powersave`), Linux, CPython 3.14.4, NumPy 2.5.4 |

The chunk size is part of the design: each batch draws its own random stream, so
a re-sample at another chunk size produces different counts for the same seed.

Recorded with:

```bash
python -m tools.verification.parity_samples sample --engine numpy --level long \
    --simulations 200000 --chunk 100000 --seed 2026 --workers 4 --compress \
    --store tests/engines/parity/reference_samples/numpy-long-200k
```

The sample is worker-independent: re-sampling `basic`, `defences`, `long`,
`stateful` and `trained-bear-vs-scarecrow` with `--workers 1` reproduced every
stored chunk count exactly.

## Aggregate

43 scenarios, 8,600,000 duels: first 48.251 %, second 44.180 %, unresolved
7.568 %. Outcomes range from near-deterministic (`a2-vs-w1-stun`, 99.9 % first)
to the `long` stalemate (97.7 % unresolved).

## Re-checking a later revision against it

Re-sample into a scratch store with the same design and compare the stored
counts. A change meant to preserve results must reproduce them **exactly** —
these are the same duels, so equality is the expectation, not a tolerance:

```bash
python -m tools.verification.parity_samples sample --engine numpy --level long \
    --simulations 200000 --chunk 100000 --seed 2026 --workers 4 --compress \
    --store outputs/parity/numpy-long-200k-after
```

Then diff the per-scenario chunk counts of the two stores. A revision that
deliberately changes the dice streams cannot be read with this store at all: it
needs a fresh oracle-backed campaign, not a self-comparison.
