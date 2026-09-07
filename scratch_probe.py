import pathlib, yaml, collections
root = pathlib.Path("sources/knowledge")
paths = collections.Counter()
problems = []
for p in sorted(root.rglob("*.yaml")):
    rel = p.as_posix()
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("PARSE FAIL", rel, e)
        continue
    hits = []
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "summary":
                    hits.append(path + ("summary",))
                walk(v, path + (str(k),))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + ("[%d]" % i,))
    walk(doc, ())
    for h in hits:
        paths[rel] += 1
    # flag summaries whose parent context is runtime-ish / non-record
    def walk2(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "summary":
                    ctx = path
                    if ctx and ctx[-1] not in ("",):
                        pass
                    # report parent chain of interest
                walk2(v, path + (str(k),))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk2(v, path + ("[%d]" % i,))
print("files with summary keys:", len(paths), "total summary keys:", sum(paths.values()))
for rel, n in paths.most_common():
    print("  %4d  %s" % (n, rel))
