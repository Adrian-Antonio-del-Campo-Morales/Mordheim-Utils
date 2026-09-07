import pathlib, yaml
path = pathlib.Path("sources/knowledge/catalog/mechanics/close-combat.yaml")
text = path.read_text(encoding="utf-8")
marker = "\nskills:\n"
assert marker in text, "skills family marker missing"
head, _tail = text.split(marker, 1)
if not head.endswith("\n"):
    head += "\n"
path.write_text(head, encoding="utf-8", newline="\n")
doc = yaml.safe_load(head)
assert "skills" not in doc
assert not any(r.get("id", "").startswith("skill.") for fam in doc.values() if isinstance(fam, list) for r in fam if isinstance(r, dict))
print("trimmed; lines now", len(head.splitlines()))
