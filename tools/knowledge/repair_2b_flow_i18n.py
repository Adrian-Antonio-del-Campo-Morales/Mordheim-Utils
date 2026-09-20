"""Repair 2B staging i18n scalars silently truncated by flow-style commas.

A single-line ``effect_i18n: {es: texto, con comas}`` is parsed by YAML as a
mapping whose ``es`` value ends at the first comma; the remaining fragments
become spurious sibling keys and the rest of the sentence is lost. The raw
line still carries the full intended translation, so this script rewrites
every affected scalar as a folded block scalar (``>-``), which survives
commas, colons and exclamation marks.

Usage::

    python tools/knowledge/repair_2b_flow_i18n.py            # dry run
    python tools/knowledge/repair_2b_flow_i18n.py --write    # apply
"""
from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

STAGING = Path(__file__).resolve().parents[2] / "sources" / "2B"

I18N_FIELDS = ("effect_i18n", "name_i18n", "note_i18n")

# Single-line flow mapping with an unquoted es scalar:  effect_i18n: {es: ...}
_FLOW_LINE = re.compile(
    r"^(?P<indent>\s*)(?P<field>" + "|".join(I18N_FIELDS) + r"): \{es: (?P<text>.+)\}\s*$"
)

# Keys YAML would fabricate out of comma fragments are anything but a locale.
_LOCALES = {"es", "en", "fr", "de", "it"}


def _wrap(text: str, indent: str) -> str:
    """Folded block scalar body, wrapped to the canonical ~100 columns."""
    body = textwrap.fill(" ".join(text.split()), width=100,
                         initial_indent=indent + "  ", subsequent_indent=indent + "  ")
    return f"{indent}  es: >-\n{body}"


def repair_file(path: Path, write: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)
    repaired: list[str] = []
    out: list[str] = []
    for line in lines:
        match = _FLOW_LINE.match(line.rstrip("\n"))
        if match:
            text = match.group("text").strip()
            # Skip properly quoted scalars: a broken one never starts with a quote.
            if text[:1] in {'"', "'"}:
                out.append(line)
                continue
            # Without a comma the flow scalar is intact (e.g. {es: Líder}).
            if "," not in text:
                out.append(line)
                continue
            out.append(_wrap(text, match.group("indent")) + "\n")
            repaired.append(f"{match.group('field')} -> {text[:60]}...")
        else:
            out.append(line)
    if repaired and write:
        path.write_text("".join(out), encoding="utf-8")
    return repaired


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply repairs (default: dry run)")
    args = parser.parse_args()

    total = 0
    for path in sorted(STAGING.rglob("*.yaml")):
        repaired = repair_file(path, args.write)
        for entry in repaired:
            print(f"{path.relative_to(STAGING)}: {entry}")
        total += len(repaired)
    print(f"\n{'repaired' if args.write else 'would repair'} {total} scalar(s) in {STAGING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
