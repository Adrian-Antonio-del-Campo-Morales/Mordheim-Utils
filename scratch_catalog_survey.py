import pathlib, yaml
from collections import Counter, defaultdict

root = pathlib.Path("sources/knowledge/catalog")
TEXTISH = ("name", "summary", "description", "notes", "effect", "flavour", "quote", "detail")
row = []
for p in sorted(root.rglob("*.yaml")):
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("PARSE FAIL", p, e); continue
    if not isinstance(doc, dict):
        continue
    for lk in ("items", "skills", "weapons", "mechanics", "traits", "rules", "mutations", "injuries", "scenarios", "spells", "hired_swords", "dramatis", "experiences", "advances"):
        for ent in doc.get(lk, []) or []:
            if not isinstance(ent, dict):
                continue
            ent = dict(ent)
            rid = ent.get("id") or ent.get("name") or "?"
            for t in TEXTISH:
                v = ent.get(t)
                if isinstance(v, str) and v.strip():
                    ni = ent.get(t + "_i18n") or {}
                    es = ni.get("es") if isinstance(ni, dict) else None
                    row.append((str(p), lk, t, bool(es and str(es).strip()), len(v.strip()), rid))

byfield = Counter()
noes = defaultdict(list)
for p, lk, t, hases, ln, rid in row:
    byfield[(lk, t)] += 1
    if not hases:
        noes[(lk, t)].append((p, ln, rid))

print("== field presence by list-kind ==")
for k in sorted(byfield):
    print(k, byfield[k])
print("\n== EN prose fields WITHOUT es translation ==")
for k in sorted(noes):
    print(k, len(noes[k]))
    for p, ln, rid in sorted(noes[k])[:6]:
        print("   ", p.replace("sources/knowledge/", ""), ln, rid)
