import pathlib, yaml
from collections import defaultdict

root = pathlib.Path("sources/knowledge/catalog")

def walk(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("id", "name", "summary", "effect", "description", "notes"):
                if isinstance(v, str) and v.strip():
                    out.append((path, k, k + "_i18n" in node, len(v.strip()), node.get("id") or node.get("name")))
            else:
                walk(v, path, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path, out)

for p in sorted(root.rglob("*.yaml")):
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    rows = []
    walk(doc, str(p), rows)
    rel = str(p).replace(str(root) + "\\", "").replace(str(root) + "/", "")
    if rows:
        print("== " + rel)
        byk = defaultdict(list)
        for path, k, has_i18n, ln, rid in rows:
            byk[k].append((has_i18n, ln, rid))
        for k, items in byk.items():
            tot = len(items)
            with_i18n = sum(1 for h, _, _ in items if h)
            print(f"   {k}: {tot} total, {with_i18n} with {k}_i18n, maxlen {max(l for _, l, _ in items)}")
