import pathlib, yaml
from collections import defaultdict

root = pathlib.Path("sources/knowledge")
by = defaultdict(list)

def walk(node, rel, depth=0):
    if depth > 8:
        return
    if isinstance(node, dict):
        ni = node.get("name_i18n")
        has_name_es = isinstance(ni, dict) and isinstance(ni.get("es"), str) and ni["es"].strip()
        eff = node.get("effect")
        ei = node.get("effect_i18n")
        has_eff_es = isinstance(ei, dict) and isinstance(ei.get("es"), str) and ei["es"].strip()
        if isinstance(eff, str) and eff.strip() and len(eff.strip()) > 8:
            tag = "name-es" if has_name_es else "no-name-es"
            state = "eff-es" if has_eff_es else "eff-MISSING"
            by[(rel, tag, state)].append((node.get("id") or node.get("item_id") or "?", eff.strip()[:50], has_eff_es))
        for k, v in node.items():
            walk(v, rel, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, rel, depth + 1)

for p in sorted(root.rglob("*.yaml")):
    rel = p.relative_to(root).as_posix().replace("/", "\\")
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    walk(doc, rel)

for (rel, tag, state), rows in sorted(by.items()):
    print(f"== {rel} [{tag} {state}] x{len(rows)}")
    for rid, snip, has in rows[:6]:
        print("   ", rid, "|", snip, "| es?", has)
