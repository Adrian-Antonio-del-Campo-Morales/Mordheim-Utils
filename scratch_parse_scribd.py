# -*- coding: utf-8 -*-
"""Extract the full embedded text of the Scribd Annual-2002 Spanish document."""
import html, pathlib, re

raw = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\scribd_annual.html").read_bytes()
# Try UTF-8 first, fall back to latin-1
for enc in ("utf-8", "latin-1"):
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        continue

# The document body is inside a container; simplest robust approach: strip scripts/styles,
# convert <br/> to newlines, then collapse tags.
text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text, flags=re.I)
text = re.sub(r"<[^>]+>", "", text)
text = html.unescape(text)
lines = [ln.rstrip() for ln in text.split("\n")]
# Collapse blank runs
out = []
blank = 0
for ln in lines:
    if not ln.strip():
        blank += 1
        if blank > 1:
            continue
    else:
        blank = 0
    out.append(ln)
final = "\n".join(out)

# Find where the document content begins: after "Formatos disponibles" marker
marker = "Recopilado de varios documentos"
idx = final.find(marker)
if idx == -1:
    idx = 0
else:
    idx -= 2000
final = final[idx:]

out_path = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\annual2002_full.txt")
out_path.write_text(final, encoding="utf-8")
print("chars:", len(final))
print("lines:", final.count("\n"))
for probe in ["Estandarte", "Carroza Opulenta", "Martillo de Brujas", "Nicodemus", "Ulli", "Almac", "Objetos"]:
    print(probe, "->", final.count(probe))
print("written:", out_path)