"""Rank a parity-campaign.json by per-outcome z-score (difference / one sigma)."""
import json, math, sys
p = json.load(open(sys.argv[1]))
rows = []
for r in p["scenarios"]:
    if not r["magnitudes"]:
        rows.append((99, r["corpus_key"], r["maximum_rounds"], (), (), (0, 0, 0), r["verdict"])); continue
    m = r["magnitudes"][0]; n = r["simulations_per_engine"]
    zs = []
    for a, b in zip(m["modular_rates"], m["candidate_rates"]):
        se = math.sqrt(a*(1-a)/n + b*(1-b)/n); zs.append(abs(a-b)/se if se > 0 else 0.0)
    rows.append((max(zs), r["corpus_key"], r["maximum_rounds"], m["modular_rates"], m["candidate_rates"], zs, r["verdict"]))
rows.sort(reverse=True)
f = lambda t: "/".join(f"{100*x:6.2f}" for x in t)
print(f"{'corpus key':42} {'rnd':>3} {'modular W/L/U %':>24} {'candidate W/L/U %':>24} {'z W':>5} {'z L':>5} {'z U':>5} verdict")
for z, k, rnd, mr, nr, zs, v in rows[: int(sys.argv[2]) if len(sys.argv) > 2 else None]:
    print(f"{k:42} {rnd:>3} {f(mr):>24} {f(nr):>24} {zs[0]:5.1f} {zs[1]:5.1f} {zs[2]:5.1f} {v}")
