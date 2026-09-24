#!/usr/bin/env python3
"""Normalize display names and locale blocks in the knowledge base.

Canonical English lives **once**: the ``name`` field (and ``effect`` prose).
The ``name_i18n`` / ``effect_i18n`` blocks store only *translations* for
non-canonical locales (``es``). The ``en`` mirror that used to duplicate the
canonical English is stripped whenever present — including multi-line quoted
scalars — and a locale block left without any real translation is removed.

On top of that policy the pass keeps its original job:

- ``name`` and ``name_i18n.es`` are **title case** (minor words lowercase
  unless they open/close the name; hyphen compounds keep preposition-like
  segments lowercase), and their scalar quoting is canonicalised to
  plain-when-safe.
- Everything else (``effect``, ``effect_i18n.es`` prose, ids, bindings,
  comments, anchors, aliases, flow mappings and key order) is untouched.

Editing is lexical and line-scoped. After writing, every edited file is
re-parsed and checked so that only the intended fields changed and the pass is
idempotent.

Usage::

    python tools/knowledge/maintenance/normalize_names.py --check sources/knowledge
    python tools/knowledge/maintenance/normalize_names.py --write sources/knowledge
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = ROOT / "sources" / "knowledge"

KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):(?P<rest>.*)$")

MINOR = {
    "en": {
        "a", "an", "the", "and", "but", "or", "nor", "for", "of", "on", "in",
        "at", "to", "from", "by", "as", "vs", "versus", "per", "over", "under",
        "with", "without",
    },
    "es": {
        "de", "del", "al", "a", "y", "e", "o", "u", "ni", "en", "con", "sin",
        "por", "para", "que", "el", "la", "los", "las", "un", "una", "unos",
        "unas", "entre", "hasta", "desde", "sobre", "contra", "según", "segun",
    },
}

# Accented letters (Latin-1 Supplement) plus ASCII letters/digits.
_LETTERS = re.compile(r"[^A-Za-z0-9\u00C0-\u024F]")

BLOCK_KEYS = {"name_i18n", "effect_i18n"}


def up_first(word: str) -> str:
    """Uppercase the first letter character, leaving the rest untouched."""
    for i, ch in enumerate(word):
        if ch.isalpha():
            return word[:i] + ch.upper() + word[i + 1:]
    return word


def title_case(text: str, lang: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    # Leave domains / bare URLs alone (e.g. mordheimer.net).
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-]*\.[a-z]{2,}", text) and text.lower() == text:
        return text
    words = text.split()
    n = len(words)
    out = []
    for i, word in enumerate(words):
        core = _LETTERS.sub("", word).lower()
        minor = core in MINOR.get(lang, set())
        if minor and i != 0 and i != n - 1:
            out.append(word.lower())
        else:
            segments = word.split("-")
            capped = []
            for j, seg in enumerate(segments):
                seg_core = _LETTERS.sub("", seg).lower()
                if seg_core in MINOR.get(lang, set()) and j != 0:
                    capped.append(seg.lower())
                else:
                    capped.append(up_first(seg))
            out.append("-".join(capped))
    return " ".join(out)


def plain_safe(value: str) -> bool:
    if not value or value != value.strip():
        return False
    if value[0] in "!&*-?|>%@`\"'#,:[]{}":
        return False
    if re.match(r"^(true|false|null|yes|no|on|off|~)$", value, re.I):
        return False
    if value.startswith(("---", "...", "!!")):
        return False
    if ":" in value or " #" in value:
        return False
    try:
        parsed = yaml.safe_load("x: " + value)
        return isinstance(parsed, dict) and parsed.get("x") == value
    except yaml.YAMLError:
        return False


def emit_plain(value: str) -> str:
    """Emit a scalar for a fresh line (plain when safe, else single-quoted)."""
    if plain_safe(value):
        return value
    return "'" + value.replace("'", "''") + "'"


def quote_closes(text: str, quote: str) -> bool:
    """Return whether a quoted scalar reaches its closing quote on this line."""
    text = text.rstrip()
    if not text or not text.endswith(quote):
        return False
    if quote == "'":
        apostrophes = len(text) - len(text.rstrip("'"))
        return apostrophes % 2 == 1
    backslashes = 0
    for character in reversed(text[:-1]):
        if character != "\\":
            break
        backslashes += 1
    return backslashes % 2 == 0


def _scalar_value(rest: str) -> Any:
    """Parse the scalar after ``key:`` (None when it is a container/empty)."""
    if not rest:
        return None
    try:
        return yaml.safe_load("x: " + rest)["x"]
    except (yaml.YAMLError, KeyError, TypeError):
        return None


def normalize_text(original: str) -> tuple[str, int]:
    lines = original.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent, key) of open nested mappings
    block: dict[str, Any] | None = None  # open name_i18n / effect_i18n block
    changed = 0
    index = 0

    def close_block() -> None:
        nonlocal block, changed
        if block is None:
            return
        if not block["kept"]:
            del out[block["opener"]:]
            changed += 1
        block = None

    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip()
        if not stripped:
            out.append(line)
            index += 1
            continue
        raw_indent = len(line) - len(stripped)
        if block is not None and raw_indent <= block["indent"]:
            close_block()

        match = KEY_RE.match(line)
        if not match:
            out.append(line)
            index += 1
            continue
        indent = len(match.group("indent"))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        key = match.group("key")
        rest = match.group("rest").strip()
        parent = stack[-1][1] if stack else None

        # Children of an open locale block. Real child keys (`en`, `es`) sit at
        # exactly ``block.indent + 2``; any deeper non-blank line is scalar
        # content of one of them and is never treated as a key (prose may start
        # with a word followed by ``:``, e.g. "Coste: 25 coronas…"). The `en`
        # mirror is removed together with its whole scalar (plain, quoted or
        # folded continuation lines at a deeper indent); null entries are
        # dropped; real translations are kept (name_i18n.es title-cased). Blank
        # lines are never consumed so layout stays stable and the pass remains
        # idempotent.
        if block is not None and parent == block["kind"] and indent == block["indent"] + 2:
            if key == "en":
                # Remove the mirror with its whole scalar. The scalar may span
                # several lines in any of YAML's styles: folded/literal (``>-``,
                # ``|``), a quote opened but not closed on the opener line (blank
                # lines inside are content), or a plain multi-line value.
                changed += 1
                index += 1
                quote = rest[0] if rest and rest[0] in ("'", "\"") else None
                folded = rest.startswith((">", "|"))
                quoted_open = quote is not None and not quote_closes(line, quote)
                if folded or quoted_open:
                    while index < len(lines):
                        following = lines[index]
                        next_stripped = following.lstrip()
                        if not next_stripped:
                            index += 1
                            changed += 1
                            continue
                        if len(following) - len(next_stripped) <= indent:
                            break
                        index += 1
                        changed += 1
                        if quoted_open and quote_closes(following, quote):
                            break
                else:
                    while index < len(lines):
                        following = lines[index]
                        next_stripped = following.lstrip()
                        if not next_stripped:
                            break
                        if len(following) - len(next_stripped) <= indent:
                            break
                        index += 1
                        changed += 1
                continue
            if rest.startswith((">", "|")) or (
                    rest and rest[0] in ("'", "\"") and not quote_closes(line, rest[0])):
                # Folded/literal or multi-line quoted scalar opening here; the
                # continuation lines below are appended verbatim by the loop.
                block["kept"] = True
                out.append(line)
                index += 1
                continue
            if rest == "" or _scalar_value(rest) is None:
                # Null entry (e.g. a name_i18n that never received its `es`).
                changed += 1
                index += 1
                continue
            block["kept"] = True
            value = _scalar_value(rest)
            if key == "es" and block["kind"] == "name_i18n" and isinstance(value, str):
                new_value = title_case(value, "es")
                expected = match.group("indent") + key + ": " + emit_plain(new_value)
                if expected != line:
                    changed += 1
                out.append(expected)
            else:
                out.append(line)
            index += 1
            continue

        # Ordinary record key.
        is_name = key == "name"
        value = _scalar_value(rest) if (is_name and rest and "#" not in rest) else None
        if is_name and isinstance(value, str) and value == value.strip() and "\n" not in value:
            new_value = title_case(value, "en")
            expected = match.group("indent") + key + ": " + emit_plain(new_value)
            if expected != line:
                changed += 1
            out.append(expected)
        else:
            out.append(line)
        index += 1

        if rest == "":
            if key in BLOCK_KEYS:
                block = {"kind": key, "indent": indent,
                         "opener": len(out) - 1, "kept": False}
            stack.append((indent, key))
    close_block()
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n", changed


# --- verification ----------------------------------------------------------

def _walk_checks(node: Any, path_hint: str, problems: list[str]) -> None:
    if isinstance(node, dict):
        name = node.get("name")
        if isinstance(name, str) and name != title_case(name, "en"):
            problems.append(f"{path_hint}: name {name!r} is not title-cased")
        for block_key in BLOCK_KEYS:
            i18n = node.get(block_key)
            if not isinstance(i18n, dict):
                continue
            if "en" in i18n:
                problems.append(f"{path_hint}: {block_key} still stores an 'en' mirror")
            has_translation = any(
                isinstance(value, str) and value for key, value in i18n.items()
                if key != "en"
            )
            if not has_translation:
                problems.append(f"{path_hint}: {block_key} holds no translation")
            es = i18n.get("es")
            if block_key == "name_i18n" and isinstance(es, str) and es != title_case(es, "es"):
                problems.append(f"{path_hint}: {block_key}.es {es!r} is not title-cased")
        for key, value in node.items():
            _walk_checks(value, f"{path_hint}/{key}", problems)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk_checks(value, f"{path_hint}[{index}]", problems)


def verify(path: Path) -> list[str]:
    """Check the written file: names title-cased, no ``en`` mirrors, no empty
    locale blocks, and re-normalizing it changes nothing (idempotent)."""
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return [f"YAML parse failure: {error}"]
    _walk_checks(doc, "root", problems)
    normalized, changed = normalize_text(text)
    if changed != 0:
        problems.append(f"re-normalization changes {changed} more fields (not idempotent)")
    return problems


def iter_yaml(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.yml"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="YAML files or directories")
    parser.add_argument("--write", action="store_true", help="write normalized files")
    parser.add_argument("--check", action="store_true", help="report files that would change")
    args = parser.parse_args()
    roots = args.paths or [DEFAULT_ROOT]
    paths = [path if path.is_absolute() else ROOT / path for path in roots]

    would_change = 0
    written = 0
    failures = 0
    for path in sum((iter_yaml(root) for root in paths), []):
        original = path.read_text(encoding="utf-8")
        formatted, changed = normalize_text(original)
        if changed == 0:
            continue
        if args.write:
            path.write_text(formatted, encoding="utf-8", newline="\n")
            problems = verify(path)
            if problems:
                failures += 1
                for problem in problems:
                    print(f"VERIFY {path}: {problem}")
            else:
                written += 1
                print(f"normalized {path} ({changed} name fields)")
        else:
            would_change += 1
            print(f"would change {path} ({changed} name fields)")
    if not args.write:
        print(f"checked {len(sum((iter_yaml(root) for root in paths), []))} files; {would_change} would change; {failures} failures")
    else:
        print(f"normalized {written} files; {failures} verification failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
