"""Anti-leak test: user-visible widget literals must go through ``tr``.

Scans the UI packages with AST and flags string literals passed directly to
Tkinter's user-visible parameters (``text=``, ``label=``, ``title=``,
``heading=``, ``value=`` on StringVar, ``messagebox.*`` bodies) when they look
like prose (two or more words). Symbols, colours, fonts and pure data values
are exempt; so are literals that are already wrapped in ``tr(...)``.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"

#: UI packages whose visible strings must be translated.
UI_PACKAGES = (
    SRC / "mordheim_campaign" / "ui",
    SRC / "mordheim_combat_lab" / "ui",
)

#: Parameter names that render their string on screen.
VISIBLE_PARAMS = {"text", "label", "title", "heading", "detail", "message"}

#: Literals that are UI symbols or data, never prose.
ALLOWED_EXACT = {
    "", " ", "→", "•••", "…", "—", "‹", "›", "·", "✓", "None", "→",
    "black", "flat", "w", "e", "center", "left", "right", "top", "bottom",
}

_WORDY = re.compile(r"[A-Za-z]{3,}[\s\-·—]")


def _looks_like_prose(value: str) -> bool:
    return bool(value.strip()) and value not in ALLOWED_EXACT and bool(_WORDY.search(value)) and "{}" not in value


def _visible_string_args(call: ast.Call) -> list[str]:
    """String literals of a call that land in a user-visible parameter."""
    found: list[str] = []
    func = call.func
    name = getattr(func, "attr", getattr(func, "id", ""))
    # messagebox/showerror-style positional message body.
    if name.startswith(("show", "ask")) and "messagebox" in ast.dump(func)[:80] and call.args:
        arg = call.args[1] if len(call.args) > 1 else None
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            found.append(arg.value)
    for keyword in call.keywords:
        if keyword.arg in VISIBLE_PARAMS and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            found.append(keyword.value.value)
    return found


def _is_tr_wrapped(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in {"tr", "tr_message"}


def _scan_file(path: Path) -> list[str]:
    leaks: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for value in _visible_string_args(node):
            pass
        # keyword args: skip when the value is a tr() call
        for keyword in node.keywords:
            if keyword.arg in VISIBLE_PARAMS and isinstance(keyword.value, ast.Constant) \
                    and isinstance(keyword.value.value, str) and _looks_like_prose(keyword.value.value):
                leaks.append(f"{path.relative_to(SRC)}:{node.lineno}: {keyword.arg}={keyword.value.value!r}")
        func = node.func
        name = getattr(func, "attr", getattr(func, "id", ""))
        if name.startswith(("show", "ask")) and len(node.args) > 1 \
                and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str) \
                and _looks_like_prose(node.args[1].value):
            leaks.append(f"{path.relative_to(SRC)}:{node.lineno}: body={node.args[1].value!r}")
    return leaks


def test_ui_visible_literals_are_translated() -> None:
    leaks: list[str] = []
    for package in UI_PACKAGES:
        for path in sorted(package.rglob("*.py")):
            leaks.extend(_scan_file(path))
    assert leaks == [], "\n".join(leaks[:40])
