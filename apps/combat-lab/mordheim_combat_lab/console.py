"""Shared console styling for every command-line tool in the repository.

One palette and one help layout for the Combat Lab CLI, the ``mordheim-utils``
launcher and the standalone ``tools/*.py`` scripts, so ``--help`` looks the
same everywhere:

- section headings (``options:``, ``certification samples:``, command groups)
  are rendered bold cyan;
- option and command names are rendered bold yellow;
- the ``usage:`` line is bold.

Output is colored only when stdout is a real terminal.  Pipes, redirected
output, CI and pytest capture get plain text.  ``NO_COLOR`` and
``MORDHEIM_NO_COLOR`` disable colors explicitly; ``MORDHEIM_FORCE_COLOR=1``
enables them even when stdout is not a terminal (useful for tests and for
inspecting the palette).  On Windows, VT processing is enabled on the console
handle the first time color is used (colorama-style, dependency-free).

``HelpFormatter`` is an ``argparse`` formatter with the shared layout; drop it
into any ``ArgumentParser(..., formatter_class=HelpFormatter)`` and the
``--help`` text is styled automatically.
"""
from __future__ import annotations

from argparse import HelpFormatter as _ArgparseHelpFormatter
import os
import re
import sys

_RESET = "\x1b[0m"
_BOLD = "1"
_BOLD_CYAN = "1;36"
_BOLD_YELLOW = "1;33"

#: ``--help`` text is styled by line kind; the rules below are shared by every
#: help renderer (argparse formatter and the launcher's own text).
_USAGE_RE = re.compile(r"^usage: ")
_HEADING_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ,/._-]*:$")


def color_enabled() -> bool:
    """Whether styling should be applied to stdout right now."""
    if (os.environ.get("NO_COLOR") is not None
            or os.environ.get("MORDHEIM_NO_COLOR") is not None):
        return False
    forced = os.environ.get("MORDHEIM_FORCE_COLOR")
    if forced not in (None, "", "0"):
        return True
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def _enable_windows_vt() -> None:
    """Enable ANSI escape processing on a Windows console (best effort)."""
    if os.name != "nt" or not sys.stdout.isatty():
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(
                handle, mode.value | 0x0004,  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            )
    except Exception:  # pragma: no cover - defensive on exotic consoles
        pass


def _paint(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}{_RESET}"


def bold(text: str) -> str:
    return _paint(_BOLD, text)


def heading(text: str) -> str:
    return _paint(_BOLD_CYAN, text)


def name(text: str) -> str:
    return _paint(_BOLD_YELLOW, text)


def _split_leading_token(line: str) -> tuple[str, str, str] | None:
    """Split an indented option/command line into (indent, name, rest).

    Returns ``None`` for continuation lines and prose: the token is the text
    up to the first double space, and it must look like an option (``-x`` /
    ``--name``) or a bare command name.  Descriptions are aligned with single
    interior spaces, so the double space is the column gap and never occurs
    inside an option invocation.
    """
    indent = len(line) - len(line.lstrip(" "))
    if indent not in (2, 3, 4):
        return None
    rest = line[indent:]
    gap = rest.find("  ")
    if gap <= 0:
        return None
    token = rest[:gap].rstrip()
    if not token.startswith("-") and re.fullmatch(r"[\w-]+", token) is None:
        return None
    return " " * indent, token, rest[gap:]


def style_help(text: str, *, color: bool | None = None) -> str:
    """Apply the shared palette to help text, line by line.

    With ``color=None`` the decision follows stdout (auto-detection).  Pass
    ``color=True/False`` to force it (tests, previews).
    """
    active = color_enabled() if color is None else color
    if not active:
        return text
    if os.name == "nt":
        _enable_windows_vt()
    styled = []
    for line in text.splitlines():
        if _USAGE_RE.match(line):
            styled.append(bold(line))
            continue
        if _HEADING_RE.match(line):
            styled.append(heading(line))
            continue
        # Indented group label without content of its own ("  Engines, …").
        # Only plain alphabetic labels qualify: metavar listings such as
        # "  {a,b,c}" or option tokens are not headings.
        if (line.startswith("  ") and not line.startswith("   ")
                and len(line) > 2 and line[2].isalpha()
                and "  " not in line[2:] and not line[2:].endswith(":")):
            styled.append(heading(line))
            continue
        split = _split_leading_token(line)
        if split is not None:
            indent, token, remainder = split
            styled.append(indent + name(token) + remainder)
            continue
        styled.append(line)
    return "\n".join(styled) + ("\n" if text.endswith("\n") else "")


class HelpFormatter(_ArgparseHelpFormatter):
    """Argparse formatter with the shared layout and palette.

    Use as ``formatter_class=HelpFormatter`` in any parser; widths match the
    rest of the repository so every ``--help`` renders the same way.
    """

    def __init__(self, prog: str, *, color: bool | None = None) -> None:
        super().__init__(prog, max_help_position=38, width=100)
        self._color = color

    def format_help(self) -> str:
        return style_help(super().format_help(), color=self._color)
