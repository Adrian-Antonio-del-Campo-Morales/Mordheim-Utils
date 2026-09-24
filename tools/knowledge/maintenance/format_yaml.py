#!/usr/bin/env python3
"""Check and normalize formatting of maintained YAML source files.

The formatter is deliberately lexical: it preserves key order, comments, anchors,
aliases, and all non-text YAML syntax. Descriptive prose is canonicalised to
folded blocks: `effect` / `effect_i18n.es` values are never quoted and never
left continuation-wrapped — quoted scalars (single- or multi-line) and plain
values that spill over lines or exceed the target width are rewritten as `>-`
blocks rewrapped to the target width. A folded block whose body carries a
physical line past the 120 maximum is rewrapped too: writers that emit one
physical line per value leave prose that the check flags and can repair, so
the warning and the repair are the same policy. `reason` strings always fold
(quoted or plain, any length) so the audit-taxonomy metadata shares one style;
the other descriptive keys (`description`, `notes`, ...) fold when they need
wrapping (multi-line quoted scalars, content beyond the target width, or a
physical line past the 120 maximum) and short values keep their single-line
quotes.
Rule prose lives under exactly one key — `effect` (never `summary`); see
`tools/knowledge/maintenance/rename_summary_keys.py`. Parsed values are checked for semantic
equivalence after whitespace normalization.
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
TEXT_KEYS = {"effect", "description", "notes", "reason"}
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
    """Emit a descriptive prose scalar as a folded ``>-`` block, rewrapped.

    Prose is one logical line once loaded, so folding never loses content and
    quoting becomes unnecessary (colons, quotes and inch marks are all safe
    inside a block scalar).
    """
    block_indent = indent + "  "
    lines = wrap_words(value, max(20, TARGET_WIDTH - len(block_indent)))
    return [f"{indent}{key}: >-"] + [block_indent + line for line in lines]


def mapping_key_indices(lines: list[str], wanted) -> set[int]:
    """Line indexes that are genuine mapping keys satisfying ``wanted(key,
    parent)``.

    The walk is scalar-aware: quoted, block and plain continuations are
    consumed whole, so prose content that merely looks like a mapping line
    (e.g. ``reason: deferred`` inside a folded example) is never marked.
    """
    marked: set[int] = set()
    stack: list[tuple[int, str]] = []  # (indent, key) of open mapping keys
    index = 0
    while index < len(lines):
        match = KEY_RE.match(lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group("indent"))
        key = match.group("key")
        rest = match.group("rest").lstrip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else None
        if wanted(key, parent):
            marked.add(index)
        stack.append((indent, key))
        if not rest:
            # Mapping / list container: its children are real keys; visit them.
            index += 1
            continue
        if rest.startswith(("'", '"')) and not quote_closes(rest[1:], rest[0]):
            quote = rest[0]
            end = index + 1
            while end < len(lines) and not quote_closes(lines[end].strip(), quote):
                end += 1
            index = end + 1
            continue
        if rest.startswith((">-", ">", ">+", "|-", "|", "|+")):
            end = index + 1
            while end < len(lines):
                candidate = lines[end]
                if not candidate.strip():
                    end += 1
                    continue
                lead = len(candidate) - len(candidate.lstrip())
                if lead > indent:
                    end += 1
                    continue
                break
            index = end
            continue
        # Plain scalar: continuation lines are more-indented and non-blank; a
        # blank line or a line at the same indent ends the scalar.
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if not candidate.strip():
                break
            lead = len(candidate) - len(candidate.lstrip())
            if lead > indent:
                end += 1
                continue
            break
        index = end
    return marked


def text_target_indices(lines: list[str]) -> set[int]:
    """Line indexes whose key is a fold-target: ``effect`` or an ``es`` that
    sits directly under ``effect_i18n`` (the Spanish effect translation).
    """
    return mapping_key_indices(
        lines, lambda key, parent: key == "effect" or (key == "es" and parent == "effect_i18n"))


def reason_indices(lines: list[str]) -> set[int]:
    """Line indexes whose key is a genuine ``reason`` mapping key."""
    return mapping_key_indices(lines, lambda key, parent: key == "reason")


def plain_scalar_end(lines: list[str], index: int, indent: int) -> int:
    """Index just past a plain scalar opened at ``lines[index]``.

    Continuation lines are more-indented and non-blank; a blank line or a line
    at the same indent (a sibling key) ends the scalar.
    """
    end = index + 1
    while end < len(lines):
        candidate = lines[end]
        if not candidate.strip():
            break
        lead = len(candidate) - len(candidate.lstrip())
        if lead > indent:
            end += 1
            continue
        break
    return end


def folded_block_end(lines: list[str], index: int, indent: int) -> int:
    """Index just past a folded block opened at ``lines[index]``.

    Unlike a plain scalar, a block may hold blank lines of its own: they are
    part of its value, so the walk continues past them while the block does.
    """
    end = index + 1
    while end < len(lines):
        candidate = lines[end]
        if not candidate.strip():
            look = end
            while look < len(lines) and not lines[look].strip():
                look += 1
            if look < len(lines) and len(lines[look]) - len(lines[look].lstrip()) > indent:
                end = look
                continue
            break
        if len(candidate) - len(candidate.lstrip()) > indent:
            end += 1
            continue
        break
    return end


def normalize_lines(original: str) -> tuple[str, list[str]]:
    lines = original.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    changed_fields: list[str] = []
    targets = text_target_indices(lines)
    reasons = reason_indices(lines)
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        match = KEY_RE.match(line)
        if match:
            key = match.group("key")
            indent = match.group("indent")
            rest = match.group("rest").lstrip()
            quoted = rest.startswith(("'", '"'))
            multiline_quoted = quoted and not quote_closes(rest[1:], rest[0])
            is_target = index in targets  # effect / effect_i18n.es prose
            is_reason = index in reasons  # genuine reason mapping key
            is_text_key = key in TEXT_KEYS  # summary / description / notes / reason

            # Decide whether the scalar opened on this line must be folded.
            fold = False
            multiline_plain = False
            if is_target and quoted:
                # Quoted effect prose is never kept: single- or multi-line.
                fold = True
            elif is_target and rest and not quoted and not rest.startswith((">", "|")):
                # Plain effect prose folds when it spans continuation lines or
                # no longer fits the target width on a single physical line.
                end = plain_scalar_end(lines, index, len(indent))
                multiline_plain = end > index + 1
                if multiline_plain or len(line) > TARGET_WIDTH:
                    fold = True
            elif is_reason and rest and not rest.startswith((">", "|")):
                # Every reason string folds unconditionally — quoted or plain,
                # any length — so the audit-taxonomy metadata shares one style.
                fold = True
            elif is_text_key and not is_target and multiline_quoted:
                # Legacy: multi-line quoted descriptive scalars fold too.
                fold = True
            elif is_text_key and not is_target and quoted and not multiline_quoted:
                # Single-line quoted summary/notes/description fold only when
                # the prose genuinely needs wrapping (content beyond the
                # target width, or a physical line beyond the hard maximum).
                try:
                    value = yaml.safe_load("x: " + rest)["x"]
                except (KeyError, TypeError, yaml.YAMLError):
                    value = None
                if isinstance(value, str) and (
                        len(value) > TARGET_WIDTH
                        or len(indent) + len(key) + 2 + len(value) + 2 > MAX_WIDTH):
                    fold = True

            if not fold and rest.startswith(">"):
                # An already folded block can still carry one physical line per
                # value: that is the shape the staged writers emit, and the line
                # past the hard maximum is exactly what the check flags. The
                # block's value is unchanged by rewrapping, so the guard below
                # makes this safe for any folded scalar (a block whose value
                # carries paragraph breaks simply fails the round-trip and is
                # left alone).
                body = lines[index + 1 : folded_block_end(lines, index, len(indent))]
                if any(over_long(item) for item in body):
                    fold = True

            if fold:
                if quoted:
                    if multiline_quoted:
                        quote = rest[0]
                        last = index
                        while last + 1 < len(lines):
                            last += 1
                            if quote_closes(lines[last].strip(), quote):
                                break
                        else:
                            output.append(line)
                            index += 1
                            continue
                    else:
                        last = index
                elif rest.startswith(">"):
                    last = folded_block_end(lines, index, len(indent)) - 1
                else:
                    last = plain_scalar_end(lines, index, len(indent)) - 1
                scalar_source = "x: " + rest + "\n" + "\n".join(lines[index + 1 : last + 1])
                try:
                    value = yaml.safe_load(scalar_source)["x"]
                except (KeyError, TypeError, yaml.YAMLError):
                    output.extend(lines[index : last + 1])
                    index = last + 1
                    continue
                emitted = format_text_scalar(indent, key, value)
                # Per-scalar guard: the folded block must re-parse to the same
                # value; otherwise the scalar is left untouched.
                try:
                    probe = yaml.safe_load("\n".join(emitted))
                except yaml.YAMLError:
                    probe = None
                if not isinstance(probe, dict) or probe.get(key) != value:
                    output.extend(lines[index : last + 1])
                    index = last + 1
                    continue
                output.extend(emitted)
                changed_fields.append(key)
                index = last + 1
                continue
            # Scalars that stay as they are (plain short lines, block scalars,
            # short quoted metadata) fall through and are appended verbatim.
        output.append(line)
        index += 1
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output) + "\n", changed_fields


def over_long(line: str) -> bool:
    """Whether a physical line breaks the maintained maximum width.

    Lines carrying a URL are exempt: a URL is one token, so rewrapping cannot
    shorten it and the warning would never clear.
    """
    return (
        len(line) > MAX_WIDTH
        and "url:" not in line
        and "http://" not in line
        and "https://" not in line
    )


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
        if over_long(line):
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
        # Read the raw bytes: universal-newline translation would hide CRLF, and
        # the maintained sources are LF-only (the knowledge base has no CRLF).
        original = path.read_bytes().decode("utf-8")
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
                label = ", ".join(sorted(set(fields)))
                if "\r" in original:
                    label = f"{label}, CRLF" if label else "CRLF line endings"
                print(f"formatted {path} ({label or 'whitespace'})")
    if not args.write:
        print(f"checked {len(sum((iter_yaml(root) for root in paths), []))} YAML files; {changed} would change; {failures} failures")
    else:
        print(f"formatted {changed} YAML files; {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
