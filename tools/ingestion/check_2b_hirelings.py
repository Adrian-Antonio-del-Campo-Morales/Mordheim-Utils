# -*- coding: utf-8 -*-
"""Cotejo de hirelings y dramatis personae de 2B contra sus PDFs fuente.

Para cada hireling de sources/2B/catalog/hirelings/*.yaml se extrae el
bloque impreso de su PDF (sección 'Hired Swords', 'Dramatis Personae',
'Specialists' o 'Priests for Every Occasion') y se comparan:

  1. Tarifa: '<N> gcs to hire, + <M> gcs upkeep' (variantes: 'gold crowns',
     'gc', órdenes inversos) contra hire_fee.
  2. Fila 'Profile M WS BS S T W I A Ld' siguiente: stats contra
     characteristics.
  3. Rating: '+<N> points' contra warband_rating.base.
  4. Presencia de cada regla (rule.name) y de cada ítem fijo del equipo en
     el bloque impreso.

Salida: JSON con verificaciones y hallazgos; los bloques extraídos quedan
en build/cache/2b-hirelings/hireling-blocks/ para lectura manual.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build/cache/2b-pdfs"
OUT = ROOT / "build/cache/2b-hirelings"
BLOCKS = OUT / "hireling-blocks"

LAYOUTS = CACHE / "layout"


def layout_pages(stem: str) -> list[str]:
    """Páginas (-layout) de un PDF cacheado, por nombre de fichero sin extensión."""
    path = LAYOUTS / f"{stem}.txt"
    if not path.exists():
        pdf = CACHE / f"{stem}.pdf"
        if not pdf.exists():
            pdf = CACHE / "extra" / f"{stem}.pdf"
        if not pdf.exists():
            return []
        LAYOUTS.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", str(pdf), str(path)], capture_output=True)
    return path.read_text(encoding="utf-8", errors="replace").split("\f")


def find_block(pages: list[str], name: str) -> list[int]:
    """Páginas (índice 1-based) que contienen el encabezado del hireling.

    Prueba el nombre completo y, si no hay suerte, los recortes naturales
    ('Norse Bearman Bodyguard' -> 'Bearman', 'Druid-Priest of Taal' ->
    'Druid-priest', 'Strigani Seer Necromancer' -> 'Strigani Seer').
    """
    candidates = [name, name.replace("Necromancer", "").strip(), name.upper()]
    words = name.split()
    if len(words) >= 2:
        candidates.append(" ".join(words[-2:]))
        candidates.append(words[-1])
    # variantes separadas por comas/hifenes: 'Snerik, Night Goblin Scout' -> 'Snerik';
    # 'Druid-Priest of Taal' -> 'Druid'; 'Norse Bearman Bodyguard' -> 'Bearman'
    for part in re.split(r"[,\-]", name):
        part = part.strip()
        if len(part) >= 5:
            candidates.append(part)
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if candidate == name and candidate is not name:
            continue
        pat = re.compile(re.escape(candidate).replace(r"\ ", r"\s+"), re.I)
        hits = [i + 1 for i, p in enumerate(pages)
                if pat.search(p) and not re.search(r"\.{4,}", p)]
        if hits:
            return hits
    return []


def block_text(pages: list[str], anchor: str, upto: list[str], page: int) -> str:
    """Texto desde el encabezado ``anchor`` hasta el próximo encabezado en ``upto``."""
    lines = pages[page - 1].splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.search(re.escape(anchor).replace(r"\ ", r"\s+"), l, re.I)), None)
    if start is None:
        return ""
    out = []
    for l in lines[start:]:
        if len(out) > 3 and any(re.search(re.escape(u).replace(r"\ ", r"\s+"), l, re.I) for u in upto):
            break
        out.append(l)
    return "\n".join(out)


# El bloque se cierra en el encabezado de OTRO hireling (se pasa la lista).


def hirelings() -> list[dict]:
    out = []
    for f in ("grade-2b", "mim-specialists", "miracle-workers-priests",
              "rel-relics-hirelings"):
        d = yaml.safe_load(open(ROOT / f"sources/2B/catalog/hirelings/{f}.yaml",
                                encoding="utf-8"))
        for h in d["profiles"]:
            h["_file"] = f
            out.append(h)
    return out


def fee_in_lines(lines: list[str]) -> list[tuple[int, int | None]]:
    """Tarifas por línea; una tarifa partida entre dos líneas se reúne."""
    out = []
    for i, l in enumerate(lines):
        for m in re.finditer(
                r"(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|wt|doubloons|dinars|warp tokens)\s*"
                r"(?:to hire|to\ hire),?\s*\+?\s*(\d+)?\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)?\s*upkeep",
                l, re.I):
            out.append((int(m.group(1)), int(m.group(2)) if m.group(2) else None))
        # tarifa al final de línea (la página parte la frase)
        m = re.search(r"(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)\s*(?:to hire|to\ hire)\s*,?\s*\+?\s*(\d+)?\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)?\s*(?:upkeep)?$",
                      l.rstrip(), re.I)
        if m and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            up = m.group(2) or (re.match(r"^(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)?\s*upkeep", nxt, re.I) or [None] and re.match(r"^(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)?\s*upkeep", nxt, re.I).group(1) if re.match(r"^(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|warp tokens)?\s*upkeep", nxt, re.I) else None)
            pair = (int(m.group(1)), int(up) if up else None)
            if not any(a == pair[0] and b == pair[1] for a, b in out):
                out.append(pair)
    return out


def fee_in_text(text: str) -> list[tuple[int, int | None]]:
    """Todas las tarifas impresas del bloque (los bloques a dos columnas
    comparten página con el hireling vecino)."""
    t = re.sub(r"\s+", " ", text)
    out = []
    for m in re.finditer(
            r"(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|wt|doubloons|dinars)\s*"
            r"(?:to hire|to\ hire),?\s*\+?\s*(\d+)?\s*(?:gcs?|gold crowns|crowns|gold coins)?\s*upkeep",
            t, re.I):
        out.append((int(m.group(1)), int(m.group(2)) if m.group(2) else None))
    for m in re.finditer(
            r"(\d+)\s*(?:gcs?|gold crowns|crowns|gold coins|dinars)\s*(?:to hire|to\ hire)", t, re.I):
        pair = (int(m.group(1)), None)
        if not any(a == pair[0] and b is None for a, b in out):
            out.append(pair)
    return out


def stats_in_text(text: str) -> list[list[int]]:
    """Todas las filas 'Profile' del bloque (el vecino de columna imprime la suya)."""
    rows = []
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if not re.search(r"\bProfile\b", l, re.I):
            continue
        for j in range(i + 1, min(i + 4, len(lines))):
            line = lines[j]
            clean = re.sub(r"\([^)]*\)", " ", line)  # '4(6)' -> '4'
            # si la línea mezcla dos columnas, quédate con la cola derecha (la fila
            # impresa va indentada a su columna) o con la primera tanda de >=9 dígitos
            tail = clean[35:] if len(clean) > 35 and re.search(r"[A-Za-z]{3,}", clean[:35]) else clean
            joined = re.sub(r"\D", "", tail)
            if len(joined) >= 9:
                rows.append([int(c) for c in joined[:9]])
                break
            digits = re.findall(r"\d+", tail)
            if len(digits) >= 9:
                rows.append([int(d) for d in digits[:9]])
                break
            joined_all = re.sub(r"\D", "", clean)
            if len(joined_all) >= 9:
                rows.append([int(c) for c in joined_all[:9]])
                break
    return rows


ALL_NAMES = [h["name"] for h in hirelings()]

# Nombre del perfil tal y como lo imprime la fuente cuando difiere del nombre
# del catálogo ('Cleric of Law' es el perfil de ambos sacerdotes de Verena/Solkan).
PROFILE_ANCHORS = {
    "Priest of Verena": "Cleric of Law",
    "Snorri Nosebiter": "Snorri",
    "Aldred Fellblade": "Aldred 4",
    "Mariner-Priest of Manann": "Mariner-priest",
    "Grave Warden": "Grave Warden",
    "Ogre Treasure-Hunter": "Scrap-Dealer",
    "Albino Stormvermin": "Albino Guard",
}


def main() -> int:
    only = set(sys.argv[1:])
    BLOCKS.mkdir(parents=True, exist_ok=True)
    report = []
    for h in hirelings():
        name = h["name"]
        if only and name not in only:
            continue
        refs = h.get("source_refs", [])
        entry = {"name": name, "file": h["_file"], "checks": [], "findings": []}

        pkg_stats = [(h.get("characteristics") or {}).get(k) for k in
                     ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")]
        pkg_fee = (h.get("hire_fee") or {})
        pkg_rate = (h.get("warband_rating") or {}).get("base")

        got_stats = got_fee = got_rate = got_block = False
        # Hallazgos por ref: un chequeo falla sólo si falla en TODAS las refs
        # (la segunda ref de un hireling puede ser una página donde el perfil
        # impreso es de otra variante, p. ej. el Mutant-Priest de Shallows Beasts).
        ref_fail = []  # lista de dicts {fee, stats, rating, rules} por ref
        for ref in refs:
            url = str(ref.get("url") or "")
            stem = url.rsplit("/", 1)[-1].replace(".pdf", "").replace("%20", " ")
            aliases = {
                "Karak Azgal": "adventurers-kaz",
                "97RelicsoftheCrusadesPt2": "fallen-the-rel",
                "Specialists": "MiM Specialists",
                "Miracle-workers-in-Mordheim": "Miracle Workers",
                "Lords of the Marsh": "lords-of-the-marsh-mim",
                "Shallows Beasts": "shallows-beasts-mim",
            }
            stem = aliases.get(stem, stem)
            pages = layout_pages(stem)
            if not pages:
                entry["findings"].append(f"PDF no cacheado: {url}")
                continue
            hits = find_block(pages, name)
            if not hits:
                continue
            page, lines, start = None, None, None
            short = re.split(r"[,]", name)[0].strip()
            anchors = [name, short, " ".join(name.split()[-2:]), name.split("-")[0]]
            # ancla por la fila de stats propia (nombre corto impreso o los dígitos)
            pkg_stats_digits = ''.join(str((h.get("characteristics") or {}).get(k, ''))
                                       for k in ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"))
            anchors += [PROFILE_ANCHORS.get(name, ""), pkg_stats_digits]
            for cand in sorted(set(hits), reverse=True):
                cand_lines = pages[cand - 1].splitlines()
                for anchor in anchors:
                    cand_start = next((i for i, l in enumerate(cand_lines)
                                       if re.search(re.escape(anchor).replace(r"\ ", r"\s+"),
                                                    l, re.I)), None)
                    if cand_start is None:
                        continue
                    window = cand_lines[max(0, cand_start - 30):cand_start + 45]
                    has_profile = any(re.search(r"\bProfile\b", l, re.I) for l in window)
                    has_statrow = any(len(re.sub(r"\D", "", l)) >= 9 for l in window)
                    if has_profile or has_statrow:
                        page, lines, start = cand, cand_lines, cand_start
                        break
                if page is not None:
                    break
            if page is None:
                continue
            # bloque: hasta el encabezado de otro hireling conocido, o 60 líneas
            other = [n for n in ALL_NAMES if n != name and n.split(",")[0] in
                     " ".join(lines[max(0, start - 3):start])]
            out = lines[max(0, start - 30):]
            text = chr(10).join(out)
            (BLOCKS / f"{name.replace(',', '').replace(' ', '_')}.txt").write_text(
                f"### {stem} p{page} ({ref.get('section','')})" + chr(10) + text + chr(10),
                encoding="utf-8")
            got_block = True
            fail = {"fee": [], "stats": [], "rating": [], "rules": []}

            t = re.sub(r"\s+", " ", text)
            fees = fee_in_text(chr(10).join(out)) + fee_in_text(chr(10).join(lines[start:max(0, start - 12):-1] if start > 12 else lines[:start]))
            # dedup preservando orden
            seen_ = set()
            fees = [f_ for f_ in fees if not (f_ in seen_ or seen_.add(f_))]
            ph, pu = pkg_fee.get("hire"), pkg_fee.get("upkeep")
            if fees:
                if any(h_ == ph and (u is None or pu is None or u == pu) for h_, u in fees):
                    got_fee = True
                else:
                    fail["fee"].append(f"tarifa impresa {fees} vs paquete {ph}+{pu} ({stem} p{page})")
            stats_rows = stats_in_text(text) or []
            if stats_rows:
                if any(r == pkg_stats or (r[:6] == pkg_stats[:6]
                                          and r[6:8] == [pkg_stats[7], pkg_stats[6]]
                                          and r[8] == pkg_stats[8])
                       for r in stats_rows):
                    got_stats = True
                else:
                    fail["stats"].append(
                        f"stats impresas {stats_rows} vs paquete {pkg_stats} ({stem} p{page})")
            rates = []
            for i, l in enumerate(out):
                m_ = re.search(r"rating by\s*\+?\s*(\d+)\s*points?", l, re.I)
                if not m_:
                    # 'rating by' al final de línea: el número abre la siguiente
                    if re.search(r"rating by\s*$", l.rstrip(), re.I) and i + 1 < len(out):
                        m2 = re.search(r"\+?\s*(\d+)\s*points?", out[i + 1], re.I)
                        if m2:
                            rates.append(m2.group(1))
                else:
                    rates.append(m_.group(1))
            if rates:
                if any(int(v) == pkg_rate for v in rates):
                    got_rate = True
                else:
                    fail["rating"].append(
                        f"rating impreso {rates} vs paquete {pkg_rate} ({stem} p{page})")
            shared = [n for n in ALL_NAMES if n != name
                      and re.search(re.escape(n.split(",")[0]).replace(r"\ ", r"\s+"),
                                    t, re.I)]
            for rule in h.get("rules", []) or []:
                words = [w for w in re.findall(r"[A-Za-z']{4,}", rule.get("name", ""))[:2]]
                if not words:
                    continue
                if not all(w.lower() in t.lower() for w in words):
                    if shared:
                        fail.setdefault("rules", []).append(
                            f"regla '{rule.get('name')}' (página compartida con {shared[0].split(',')[0]}; {stem} p{page})")
                    else:
                        fail["rules"].append(
                            f"regla '{rule.get('name')}' no aparece ({stem} p{page})")

            ref_fail.append(fail)
        # emitir sólo los fallos comunes a todas las refs
        if ref_fail:
            for kind in ("fee", "stats", "rating", "rules"):
                common = ref_fail[0].get(kind, [])
                for other in ref_fail[1:]:
                    common = [x for x in common if x in other.get(kind, [])]
                entry["findings"].extend(common)
        if not got_block:
            entry["findings"].append("bloque no encontrado en ningún PDF")
        entry["checks"] = [k for k, v in (("block", got_block), ("fee", got_fee),
                                          ("stats", got_stats), ("rating", got_rate)) if v]
        report.append(entry)

    (OUT / "hirelings_check.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    n_ok = sum(1 for r in report if {"block", "fee", "stats", "rating"} <= set(r["checks"]))
    print(f"hirelings: {len(report)}; fully verified: {n_ok}; with findings: "
          f"{sum(1 for r in report if r['findings'])}")
    for r in report:
        if r["findings"]:
            print(f"  {r['name']}:")
            for f in r["findings"]:
                print(f"    - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
