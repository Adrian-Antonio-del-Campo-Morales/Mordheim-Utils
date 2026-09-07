import pathlib, yaml
from collections import Counter, defaultdict

root = pathlib.Path("sources/knowledge")
TEXT_KEYS = ("name", "summary", "effect", "description", "notes", "flavour", "title")
res = Counter()
examples = defaultdict(list)

def walk(node, where, depth=0):
    if depth > 10: return
    if isinstance(node, dict):
        for k, v in node.items():
            if k in TEXT_KEYS and isinstance(v, str) and v.strip():
                sibling = node.get(k + "_i18n")
                es = (sibling or {}).get("es") if isinstance(sibling, dict) else None
                has_es = bool(isinstance(es, str) and es.strip())
                tag = "i18n-block" if sibling else "no-i18n"
                res[(k, has_es, tag)] += 1
                if not has_es and len(examples[(k, tag)]) < 3:
                    examples[(k, tag)].append(f"{where} :: {node.get('id') or node.get('item_id') or '?'} :: {v[:60]!r}")
            walk(v, f"{where}.{k}", depth + 1)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{where}[{i}]", depth + 1)

for p in sorted(root.rglob("*.yaml")):
    if "special-rules.yaml" in p.name:
        continue  # band rules; already covered
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("FAIL", p, e); continue
    rel = p.relative_to(root).as_posix().replace("/", "\\")
    walk(doc, rel)

print("== prose keys with/without es translation (excluding band special-rules) ==")
for (k, has_es, tag), n in sorted(res.items()):
    print(f"  {k:10s} es={str(has_es):5s} {tag:10s} {n}")
print()
print("== examples of missing-es entries ==")
for (k, tag), exs in sorted(examples.items()):
    if k == "name":
        continue
    print(f"  [{k} {tag}]")
    for e in exs:
        print("    ", e)
