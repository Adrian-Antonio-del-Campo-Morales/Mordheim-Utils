#!/usr/bin/env python3
"""One-shot migration: the rule-prose key is ``effect``, never ``summary``.

Renames every genuine ``summary`` mapping key across ``sources/knowledge`` to
``effect`` (rule / catalogue / campaign display prose). The one non-prose
``summary`` in the tree — the count metadata block at the top of
``catalog/rules/implemented-canonical-families.yaml`` — becomes ``counts`` so
no ``summary`` key survives anywhere.

The pass is lexical: outside block-scalar content the word ``summary``
immediately followed by ``:`` is rewritten (it is a mapping key both in
block style and inside flow mappings such as ``- {ref: x, summary: y}``).
Block-scalar content lines (folded ``>-`` / literal ``|`` bodies) are never
touched, and the whole file is re-parsed afterwards with ``summary`` remapped
to prove the parsed values are byte-identical after whitespace folding — so
renaming prose *content* that merely contains the word is impossible to miss.
Comments, anchors, aliases, key order and every other token are preserved.
Run ``python tools/knowledge/maintenance/format_yaml.py --write sources/knowledge`` afterwards to
canonicalise the newly renamed scalars.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = ROOT / "sources" / "knowledge"
BLOCK_INDICATORS = re.compile(r"^\s*[A-Za-z0-9_.-]+:\s*(>|>\+|>-|\||\|\+|\|-)\s*$")
KEY_SUMMARY = re.compile(r"(?<![\w-])summary(?=\s*:)")


def block_scalar_regions(lines: list[str]) -> list[tuple[int, int]]:
    """(start, end) line ranges that are the *content* of block scalars."""
    regions: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        match = BLOCK_INDICATORS.match(lines[index])
        if match:
            indent = len(lines[index]) - len(lines[index].lstrip())
            end = index + 1
            while end < len(lines):
                candidate = lines[end]
                if not candidate.strip():
                    end += 1
                    continue
                if len(candidate) - len(candidate.lstrip()) > indent:
                    end += 1
                    continue
                break
            regions.append((index + 1, end))
            index = end
            continue
        index += 1
    return regions


def rename_keys(text: str, *, replacement: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    protected = block_scalar_regions(lines)
    for start, end in protected:
        for index in range(start, end):
            lines[index] = "\x00BLOCK\x00" + lines[index]
    for index, line in enumerate(lines):
        if line.startswith("\x00BLOCK\x00"):
            lines[index] = line[len("\x00BLOCK\x00"):]
            continue
        lines[index] = KEY_SUMMARY.sub(replacement, line)
    return "\n".join(lines)


def semantic_with_rename(value, rename_to: str):
    """Parsed shape with ``summary`` remapped, so a pre/post comparison is
    rename-aware (dict values are compared after key substitution)."""
    if isinstance(value, dict):
        return {
            ("effect" if key == "summary" and rename_to == "effect"
             else "counts" if key == "summary" else str(key)): semantic_with_rename(item, rename_to)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [semantic_with_rename(item, rename_to) for item in value]
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip() if value.strip() else value
    return value


def _keys(node) -> set:
    result = set()
    if isinstance(node, dict):
        result.update(str(key) for key in node)
        for value in node.values():
            result |= _keys(value)
    elif isinstance(node, list):
        for value in node:
            result |= _keys(value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="YAML files or directories")
    parser.add_argument("--write", action="store_true", help="write migrated files")
    args = parser.parse_args()
    roots = args.paths or [DEFAULT_ROOT]
    paths = [path if path.is_absolute() else ROOT / path for path in roots]
    files: list[Path] = []
    for root in paths:
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.yml")))
        else:
            files.append(root)
    changed = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        counts_rename = path.name == "implemented-canonical-families.yaml"
        replacement = "counts" if counts_rename else "effect"
        migrated = rename_keys(original, replacement=replacement)
        if migrated == original:
            continue
        before = yaml.safe_load(original)
        after = yaml.safe_load(migrated)
        if semantic_with_rename(before, replacement) != semantic_with_rename(after, replacement):
            print(f"ERROR {path}: parsed values changed during rename")
            return 1
        if isinstance(after, dict) and "summary" in _keys(after):
            print(f"ERROR {path}: residual summary key after migration")
            return 1
        count = len(KEY_SUMMARY.findall(original))
        changed += 1
        if args.write:
            path.write_text(migrated, encoding="utf-8", newline="\n")
            print(f"renamed {count} summary key(s) in {path} -> {replacement}")
        else:
            print(f"would rename {count} summary key(s) in {path}")
    print(f"{'migrated' if args.write else 'would migrate'} {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
