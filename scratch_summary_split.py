import pathlib, yaml

root = pathlib.Path("sources/knowledge")
per_file = {}

def walk(node, rel, depth=0):
    if depth > 7:
        return
    if isinstance(node, dict):
        s = node.get("summary")
        e = node.get("effect")
        if isinstance(s, str) and len(s.strip()) > 8:
            ni = node.get("name_i18n")
            has_name_es = bool(isinstance(ni, dict) and isinstance(ni.get("es"), str) and ni["es"].strip())
            has_effect = bool(isinstance(e, str) and e.strip())
            per_file.setdefault(rel, []).append(
                [len(s.strip()), has_name_es, has_effect])
        for v in node.values():
            walk(v, rel, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, rel, depth + 1)

for p in sorted(root.rglob("*.yaml")):
    if "special-rules.yaml" in p.name:
        continue
    rel = p.relative_to(root).as_posix().replace("/", "\\")
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    walk(doc, rel)

total = 0
for rel, items in sorted(per_file.items()):
    n = len(items)
    total += n
    avg = sum(it[0] for it in items) // n
    n_es = sum(1 for it in items if it[1])
    n_eff = sum(1 for it in items if it[2])
    print(f"{rel:52s} summaries={n:4d}  avg_len={avg:4d}  name-es={n_es:4d}  also-effect={n_eff}")
print("TOTAL", total)
