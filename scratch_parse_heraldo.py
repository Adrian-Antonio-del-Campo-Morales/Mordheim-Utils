# -*- coding: utf-8 -*-
"""Extract the full embedded text of the Scribd El Heraldo de Mordheim document."""
import html, pathlib, re

raw = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\scribd_heraldo.html").read_bytes()
for enc in ("utf-8", "latin-1"):
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        continue

start = text.find('class="blurred_page"')
if start == -1:
    start = 0
body = text[start:]
body = re.sub(r"<script.*?</script>", " ", body, flags=re.S | re.I)
body = re.sub(r"<style.*?</style>", " ", body, flags=re.S | re.I)
body = re.sub(r"<br\s*/?\s*>", "\n", body, flags=re.I)
body = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", body, flags=re.I)
body = re.sub(r"<[^>]+>", "", body)
body = html.unescape(body)
lines = [ln.strip() for ln in body.split("\n")]
lines = [ln for ln in lines if ln]
final = "\n".join(lines)

out_path = pathlib.Path(r"C:\Users\PHOLTE~1\AppData\Local\Temp\heraldo_full.txt")
out_path.write_text(final, encoding="utf-8")
print("chars:", len(final))
for probe in ["Escenario", "Heraldo", "Secuestrado", "Ataque de Rata", "Plaza", "Rodeado", "Emboscada", "Caravana"]:
    print(probe, "->", final.count(probe))
print("written:", out_path)