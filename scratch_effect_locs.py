import pathlib, yaml
from collections import Counter

root = pathlib.Path("sources/knowledge")

def walk(node, where, depth, out, seen):
    if depth > 10:
        return
    if isinstance(node, dict):
        eff = node.get("effect")
        if isinstance(eff, str) and len(eff.strip()) > 12:
            i18n = node.get("effect_i18n")
            es = (i18n or {}).get("es") if isinstance(i18n, dict) else None
            rid = node.get("id") or node.get("item_id") or "?"
            out.append((where, rid, bool(isinstance(es, str) and es.strip()), len(eff.strip())))
        for k, v in node.items():
            walk(v, where, depth + 1, out, seen)
    elif isinstance(node, list):
        for v in node:
            walk(v, where, depth + 1, out, seen)

counter = Counter()
rows = []
for p in sorted(root.rglob("*.yaml")):
    if "special-rules.yaml" in p.name or "schema" in str(p):
        continue
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    rel = p.relative_to(root).as_posix().replace("/", "\\")
    out = []
    walk(doc, rel, 0, out, set())
    for where, rid, has_es, ln in out:
        counter[(where, has_es)] += 1
        rows.append((where, rid, has_es, ln))

for (where, has_es), n in sorted(counter.items()):
    print(f"{n:5d}  es={str(has_es):5s}  {where}")
