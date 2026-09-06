#!/usr/bin/env python3
"""Check and normalize formatting of maintained YAML source files.

The formatter is deliberately lexical: it preserves key order, comments, anchors,
aliases, and all non-text YAML syntax. Descriptive scalar fields may be changed
from ingestion-style quoted wrapping to folded blocks; parsed values are checked
for semantic equivalence after whitespace normalization.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "sources" / "knowledge"
TEXT_KEYS = {"effect", "summary", "description", "notes", "reason"}
TARGET_WIDTH = 100
MAX_WIDTH = 120
KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):(?P<rest>.*)$")


def scalar_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def semantic_shape(value: Any, field: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: semantic_shape(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [semantic_shape(item, field) for item in value]
    if isinstance(value, str) and field in TEXT_KEYS:
        return scalar_text(value)
    return value


def load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def quote_closes(text: str, quote: str) -> bool:
    """Return whether quoted scalar reaches its closing quote on this line."""
    text = text.rstrip()
    if not text or not text.endswith(quote):
        return False
    if quote == "'":
        # A doubled apostrophe is content, not the scalar terminator.
        apostrophes = len(text) - len(text.rstrip("'"))
        return apostrophes % 2 == 1
    backslashes = 0
    for character in reversed(text[:-1]):
        if character != "\\":
            break
        backslashes += 1
    return backslashes % 2 == 0


def wrap_words(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def format_text_scalar(indent: str, key: str, value: str) -> list[str]:
    value = scalar_text(value)
    prefix = f"{indent}{key}: "
    if len(prefix) + len(value) <= TARGET_WIDTH and "\\n" not in value:
        escaped = value.replace("'", "''")
        return [prefix + "'" + escaped + "'"]
    block_indent = indent + "  "
    lines = wrap_words(value, max(20, TARGET_WIDTH - len(block_indent)))
    return [f"{indent}{key}: >-"] + [block_indent + line for line in lines]


def normalize_lines(original: str) -> tuple[str, list[str]]:
    lines = original.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    changed_fields: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        match = KEY_RE.match(line)
        if match and match.group("key") in TEXT_KEYS:
            rest = match.group("rest").lstrip()
            if rest.startswith(("'", '"')) and not quote_closes(rest[1:], rest[0]):
                quote = rest[0]
                end = index
                while end + 1 < len(lines):
                    end += 1
                    if quote_closes(lines[end].strip(), quote):
                        break
                else:
                    output.append(line)
                    index += 1
                    continue
                scalar_source = "x: " + rest + "\n" + "\n".join(lines[index + 1 : end + 1])
                try:
                    value = yaml.safe_load(scalar_source)["x"]
                except (KeyError, TypeError, yaml.YAMLError):
                    output.extend(lines[index : end + 1])
                    index = end + 1
                    continue
                output.extend(format_text_scalar(match.group("indent"), match.group("key"), value))
                changed_fields.append(match.group("key"))
                index = end + 1
                continue
            # Plain long scalars can contain YAML syntax. Leave them untouched;
            # the checker reports them for a later, schema-aware migration.
        output.append(line)
        index += 1
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output) + "\n", changed_fields


def iter_yaml(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.yml"))


def diagnostics(text: str) -> list[str]:
    result: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            result.append(f"line {number}: tab used for indentation")
        if line.rstrip() != line:
            result.append(f"line {number}: trailing whitespace")
        if len(line) > MAX_WIDTH and "url:" not in line and "http://" not in line and "https://" not in line:
            result.append(f"line {number}: {len(line)} characters (max {MAX_WIDTH})")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="YAML files or directories")
    parser.add_argument("--write", action="store_true", help="write normalized files")
    parser.add_argument("--check", action="store_true", help="check formatting and semantic round-trip")
    args = parser.parse_args()
    roots = args.paths or [DEFAULT_ROOT]
    paths = [path if path.is_absolute() else ROOT / path for path in roots]
    failures = 0
    changed = 0
    for path in sum((iter_yaml(root) for root in paths), []):
        original = path.read_text(encoding="utf-8")
        formatted, fields = normalize_lines(original)
        try:
            before = load(path)
            after = yaml.safe_load(formatted)
        except yaml.YAMLError as error:
            print(f"ERROR {path}: YAML parse failure: {error}")
            failures += 1
            continue
        if semantic_shape(before) != semantic_shape(after):
            print(f"ERROR {path}: semantic values changed during formatting")
            failures += 1
            continue
        issues = diagnostics(formatted)
        if issues and (args.check or not args.write):
            for issue in issues:
                print(f"WARN {path}: {issue}")
        if formatted != original:
            changed += 1
            if args.write:
                path.write_text(formatted, encoding="utf-8", newline="\n")
                print(f"formatted {path} ({', '.join(sorted(set(fields))) or 'whitespace'})")
    if not args.write:
        print(f"checked {len(sum((iter_yaml(root) for root in paths), []))} YAML files; {changed} would change; {failures} failures")
    else:
        print(f"formatted {changed} YAML files; {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
