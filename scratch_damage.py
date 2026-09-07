import pathlib, yaml, collections
kb = pathlib.Path("sources/knowledge")
reg = yaml.safe_load((kb / "catalog/rules/special-rules.yaml").read_text(encoding="utf-8"))
reg_ids = {str(r["id"]) for r in reg.get("rules") or []}
print("registry entries:", len(reg_ids))
refs = collections.defaultdict(list)
for p in sorted((kb / "bands").rglob("special-rules.yaml")):
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for r in doc.get("rules") or []:
        ref = r.get("rule_ref")
        if ref:
            refs[str(ref)].append(p.as_posix())
print("band rule_refs:", sum(len(v) for v in refs.values()), "across", len(refs), "distinct ids")
missing = [rid for rid in refs if rid not in reg_ids]
print("referenced ids missing from registry:", len(missing))
for rid in missing:
    print("  MISSING", rid, "->", len(refs[rid]), "refs:", refs[rid][0])
print("registry entries never referenced:", sorted(reg_ids - set(refs)))
# What still has an effect on bands (rule-level)?
still = 0
for p in sorted((kb / "bands").rglob("special-rules.yaml")):
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for r in doc.get("rules") or []:
        if r.get("effect"):
            still += 1
print("band rules still carrying effect text:", still)
