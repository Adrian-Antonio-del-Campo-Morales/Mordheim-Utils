"""external.find_stub_sources: locate cached text for each missing-item stub.

Prints the owner PDF text file and page hint for every stub id so the
transcription pass can group work by source document.
"""
from __future__ import annotations

import sys
from pathlib import Path

STUBS = Path("sources/2B/catalog/items/missing-item-stubs.yaml")
CACHE = Path("build/cache/2b-pdfs/text")


def main(argv: list[str]) -> int:
    import yaml

    data = yaml.safe_load(STUBS.read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    wanted = argv or None

    for it in items:
        if wanted and it["id"] not in wanted:
            continue
        band = (it.get("source_bands") or ["?"])[0]
        pdf = band + ".pdf"
        txt = CACHE / (band + ".txt")
        status = txt.exists() and "ok" or "MISSING"
        print(f"{it['id']}\t{band}\t{status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
