import re, yaml, sys
sys.path.insert(0, "tools")
import importlib.util
spec = importlib.util.spec_from_file_location("rs", "tools/rename_summary_keys.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

text = open("sources/knowledge/catalog/campaign/scenarios.yaml", encoding="utf-8").read()
lines = text.replace("\r\n", "\n").split("\n")
marked = rs.summary_key_indices(lines)
raw = {i for i, l in enumerate(lines) if re.match(r"^\s*summary:", l)}
print("raw regex:", len(raw), "walker:", len(marked), "missed:", len(raw - marked))
for i in sorted(raw - marked)[:15]:
    print("LINE", i, repr(lines[i][:110]))
    for j in range(max(0, i - 3), min(len(lines), i + 4)):
        print("   ", j, repr(lines[j][:110]))
