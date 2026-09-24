# -*- coding: utf-8 -*-
"""Clasificar glifos dudosos de filas de stats KEP por plantillas.

Las filas YA verificadas de la misma página (misma fuente decorativa)
dan la librería de plantillas; cada glifo de la fila dudosa se clasifica
por diferencia de imágenes normalizadas.

Uso: python kep_template_match.py <band> <page>
Filas conocidas y dudosas están codificadas dentro (coordenadas @200dpi).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PDFS = ROOT / "build/cache/2b-pdfs"

# (y0, y1, etiqueta, dígitos esperados o None=dudosa) @200dpi, x 435..645
ROWS = {
    "slave-uprising-kep": {
        2: [
            (700, 738, "Demagogue", "633331157"),
            (1140, 1176, "Underlings", None),
            (1458, 1496, "Goblin Leader", "433331136"),
            (1818, 1856, "Human Leader", "433331137"),
        ],
    },
    "crooked-moon-kep": {
        5: [
            (0, 0, "Big Boss", None),  # rellenar tras sondeo
        ],
    },
    "clan-angrund-kep": {
        4: [
            (0, 0, "Dwarf Thunderers", None),
        ],
    },
}

X0, X1 = 430, 650  # franja de dígitos @200dpi


def render(band, page, dpi=400):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                        "-png", str(PDFS / f"{band}.pdf"), str(Path(tmp) / "p")],
                       capture_output=True)
        png = sorted(Path(tmp).glob("*.png"))[0]
        return cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)


def glyphs(img, y0, y1, scale):
    """Componentes conexos tipo-glifo en la franja, ordenados por x."""
    band = img[y0 * scale:(y1 + 2) * scale, X0 * scale:X1 * scale]
    ink = (band < 128).astype(np.uint8)
    count, _lbl, stats, _c = cv2.connectedComponentsWithStats(ink, 8)
    boxes = [tuple(int(v) for v in stats[i]) for i in range(1, count)
             if stats[i][3] >= 20 * scale]  # solo altura: los «1» son estrechos (w 7-8)
    boxes.sort(key=lambda b: b[0])
    out = []
    for x, y, w, h, _a in boxes:
        g = (band[y:y + h, x:x + w].astype(np.float32) / 255.0)
        out.append((x + X0 * scale, cv2.resize(g, (32, 48),
                                               interpolation=cv2.INTER_AREA)))
    return out


def main():
    band, page = sys.argv[1], int(sys.argv[2])
    rows = [r for r in ROWS[band][page] if r[2] or r[1]]
    img = render(band, page)
    scale = 2  # 400dpi vs coords 200dpi

    lib = {}   # dígito -> [plantillas]
    rows_g = {}
    for y0, y1, name, expected in rows:
        if y0 == 0:
            continue
        gs = glyphs(img, y0, y1, scale)
        rows_g[name] = gs
        if expected and len(gs) == len(expected):
            for g, d in zip(gs, expected):
                lib.setdefault(d, []).append(g[1])
        print(f"{name}: {len(gs)} glifos esper={expected}")

    def classify(g):
        best, bd = None, 1e9
        for d, ts in lib.items():
            for t in ts:
                d_ = float(np.mean(np.abs(g - t)))
                if d_ < bd:
                    best, bd = d, d_
        return best, bd

    print("\n-- clasificación de filas dudosas --")
    for y0, y1, name, expected in rows:
        if y0 and expected:
            continue
        gs = rows_g.get(name, [])
        read = ""
        for _x, g in gs:
            d, dist = classify(g)
            read += f"{d}({dist:.2f})" if d else "?"
        print(f"{name}: {read}")


if __name__ == "__main__":
    main()
