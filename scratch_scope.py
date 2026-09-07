import pathlib, yaml

root = pathlib.Path("sources/knowledge/catalog")

def walk(node, where, out, depth=0):
    if depth > 8:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("summary", "effect", "description", "notes") and isinstance(v, str) and len(v.strip()) > 25:
                i18n = node.get(k + "_i18n")
                es = (i18n or {}).get("es") if isinstance(i18n, dict) else None
                out.append((where, node.get("id") or node.get("item_id") or "?", k, len(v.strip()), bool(isinstance(es, str) and es.strip())))
            walk(v, where, out, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, where, out, depth + 1)

for rel in ("mechanics", "skills", "items"):
    for p in sorted((root / rel).rglob("*.yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        out = []
        walk(doc, "", out)
        if not out:
            continue
        print(f"== {p.relative_to(root).as_posix()}")
        by_key = {}
        for where, rid, k, ln, has_es in out:
            by_key.setdefault(k, [0, 0]).__setitem__(0, by_key.get(k, [0, 0])[0] + 1)
            if not has_es:
                by_key[k][1] += 1
        for k, (tot, missing) in sorted(by_key.items()):
            print(f"   {k}: {tot} total, {missing} without es")
