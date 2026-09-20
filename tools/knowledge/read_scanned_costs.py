# -*- coding: utf-8 -*-
"""Read the recruiting costs of the scanned KEP pages off their images.

The three Keepers of the Keys pages (Clan Angrund, Crooked Moon, Slave Uprising)
are scans: their text layer is OCR and drops the figure in front of the cost
line ("85 Gold Crowns To Hire" comes back as "5LD<RWNTHIRE", and the Demagogue's
whole figure is lost). This tool re-reads those rows from the page image: it
finds every cost row with the OCR, crops the strip in front of "gold crowns to
hire" and prints what it reads there three ways plus an ASCII rendering of the
strip, which is what a human reads when the OCR still loses a digit.

The readings it prints are the evidence behind ``READ_OFF_PAGE`` in
``audit_2b.py``; the auditor itself does not depend on this tool (RapidOCR is a
user-level install, not a project dependency), it only records what was read.

Usage: python tools/knowledge/read_scanned_costs.py [band-id ...]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
PDFS = ROOT / "build" / "cache" / "2b-pdfs"
DPI = 400
# The OCR reads the words after the figure in ways that all still end the line.
MARKERS = ("thire", "rwnthire", "rwnsth", "sthire", "ntlinthire")


def load_engine():
    """RapidOCR, or a clear message when the optional install is missing."""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:  # pragma: no cover - depends on the local environment
        print("RapidOCR is not installed: pip install --user rapidocr-onnxruntime")
        raise SystemExit(1)
    return RapidOCR()


def strip_of(image, box, dpi: int = DPI):
    """The strip in front of a cost row's words, with a little margin."""
    xs = [int(point[0]) for point in box]
    ys = [int(point[1]) for point in box]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return image[max(0, y0 - 16):y1 + 16, max(0, x0 - 340):x1 + 20]


def ascii_art(strip, width: int = 108) -> str:
    """The strip as text, dark ink on white, for a human to read the digits."""
    small = cv2.resize(strip, (width, max(1, int(strip.shape[0] * width / strip.shape[1]))),
                       interpolation=cv2.INTER_AREA)
    rows = []
    for line in small:
        rows.append("".join(" .:-=+*#%@"[min(9, (255 - int(value)) * 10 // 256)] for value in line))
    return "\n".join(rows)


def main() -> int:
    band_ids = sys.argv[1:]
    if not band_ids:
        band_ids = [path.stem for path in sorted(PDFS.glob("*-kep.pdf"))]
    engine = load_engine()
    for band_id in band_ids:
        pdf = PDFS / f"{band_id}.pdf"
        if not pdf.exists():
            print(f"!! no cached PDF for {band_id}")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["pdftoppm", "-r", str(DPI), "-png", str(pdf),
                            str(Path(tmp) / "page")], capture_output=True)
            for png in sorted(Path(tmp).glob("*.png")):
                image = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
                result, _ = engine(str(png))
                for box, text, _score in result or []:
                    flat = text.lower().replace(" ", "")
                    if not any(marker in flat for marker in MARKERS):
                        continue
                    strip = strip_of(image, box)
                    print(f"### {band_id} {png.name} row={text[:70]!r}")
                    for label, variant in (
                        ("raw", strip),
                        ("inverted", 255 - cv2.threshold(
                            strip, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                        ("x2", cv2.resize(strip, None, fx=2, fy=2,
                                          interpolation=cv2.INTER_CUBIC)),
                    ):
                        read, _ = engine(variant)
                        if read:
                            print(f"    {label:<9} {' '.join(part[1] for part in read)}")
                    print(ascii_art(strip))
                    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
