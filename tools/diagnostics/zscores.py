"""Rank a parity-campaign.json by per-outcome z-score (difference / one sigma).

Usage: ``python tools/diagnostics/zscores.py REPORT.json [TOP_N]``.  Every
compared magnitude is ranked, not only the winner.  ``gate`` is the difference
as a multiple of the campaign tolerance (six sigma with the 0.25% floor), so
``gate > 1`` is exactly a failed comparison; ``z`` is the raw sigma distance
and is infinite when both samples are degenerate (sigma 0) yet disagree.
"""
import json
import math
import sys

p = json.load(open(sys.argv[1]))
rows = []
for r in p["scenarios"]:
    if not r["magnitudes"]:
        rows.append((math.inf, math.inf, r["corpus_key"], "-", r["maximum_rounds"], (), (), (), r["verdict"]))
        continue
    n = r["simulations_per_engine"]
    for m in r["magnitudes"]:
        zs, gates = [], []
        for a, b, tol in zip(m["modular_rates"], m["candidate_rates"], m["tolerances"]):
            se = math.sqrt(a * (1 - a) / n + b * (1 - b) / n)
            zs.append(abs(a - b) / se if se > 0 else (0.0 if a == b else math.inf))
            gates.append(abs(a - b) / tol if tol > 0 else (0.0 if a == b else math.inf))
        rows.append((max(gates), max(zs), r["corpus_key"], m["magnitude"], r["maximum_rounds"],
                     m["modular_rates"], m["candidate_rates"], zs, r["verdict"]))
rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
f = lambda t: "/".join(f"{100 * x:6.2f}" for x in t[:3])
print(f"{'corpus key':42} {'magnitude':9} {'rnd':>3} {'modular %':>24} {'candidate %':>24} "
      f"{'gate':>6} {'max z':>6} verdict")
for gate, z, k, magnitude, rnd, mr, nr, zs, v in rows[: int(sys.argv[2]) if len(sys.argv) > 2 else None]:
    print(f"{k:42} {magnitude:9} {rnd:>3} {f(mr):>24} {f(nr):>24} {gate:6.2f} {z:6.1f} {v}")
