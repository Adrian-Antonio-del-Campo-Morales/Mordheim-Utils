import pathlib, yaml, collections, re
root = pathlib.Path("sources/knowledge")
norm = collections.defaultdict(list)
for p in sorted((root / "bands").rglob("special-rules.yaml")):
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    for r in (doc.get("rules") or []):
        if not isinstance(r, dict):
            continue
        eff = str(r.get("effect") or "").strip()
        if not eff:
            continue
        key = " ".join(eff.casefold().split())
        binding = None
        rt = r.get("runtime") or {}
        for e in rt.get("effects") or []:
            b = (e or {}).get("binding")
            if isinstance(b, dict):
                binding = (b.get("kind"), b.get("id"))
                break
        norm[key].append({
            "file": p.as_posix(), "band": p.parent.name,
            "name": str(r.get("name")), "id": str(r.get("id")),
            "len": len(eff), "kind": r.get("kind"),
            "binding": binding,
            "es": ((r.get("effect_i18n") or {}).get("es") or "").strip(),
            "source_refs": bool(r.get("source_refs")) or bool(r.get("source")),
        })
clusters = []
for key, rows in norm.items():
    bands = {r["band"] for r in rows}
    if len(bands) >= 2:
        clusters.append((key, rows))
clusters.sort(key=lambda kv: -len(kv[1]))
print("total exact-text clusters (>=2 band dirs):", len(clusters), "records:", sum(len(r) for _, r in clusters))
buckets = collections.Counter()
for key, rows in clusters:
    buckets[min(rows[0]["len"] // 40 * 40, 400)] += 1
print("cluster count by min-length bucket:", dict(sorted(buckets.items())))
print()
for key, rows in clusters:
    bands = sorted({r["band"] for r in rows})
    es_ok = len({r["es"] for r in rows}) == 1
    names = collections.Counter(r["name"] for r in rows)
    binds = sorted({str(r["binding"]) for r in rows})
    kinds = sorted({str(r["kind"]) for r in rows})
    print("len=%3d n=%2d files=%d es_eq=%s" % (rows[0]["len"], len(rows), len(bands), es_ok))
    print("   names=%s binds=%s kinds=%s" % (dict(names), binds, kinds))
    print("   text=%s" % key[:150])
