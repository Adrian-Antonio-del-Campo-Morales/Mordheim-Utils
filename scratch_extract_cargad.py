# -*- coding: utf-8 -*-
"""Extract text from the Cargad-23 PDF (Spanish Mordheim Annual-2002 printing)."""
import re, zlib, pathlib

pdf_path = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\cargad23.pdf")
data = pdf_path.read_bytes()

streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S)
texts = []
for s in streams:
    try:
        d = zlib.decompress(s)
    except Exception:
        continue
    for m in re.finditer(rb"\((?:[^()\\]|\\.)*\)", d):
        texts.append(m.group(0)[1:-1])

out = b"\n".join(texts)
out_path = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\cargad23_text.txt")
out_path.write_bytes(out)
txt = out.decode("latin-1", errors="replace")
print("bytes:", len(out))
print("Caos en las occurrences:", len(re.findall(r"Caos en las", txt)))
print("Mordheim occurrences:", len(re.findall(r"Mordheim", txt)))
print("written:", out_path)