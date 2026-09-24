"""Pipeline gate: maintained YAML must satisfy the canonical formatting.

Wraps ``tools/format_yaml.py --check`` so the lexical formatting policy
(folded prose blocks, canonical scalar quoting, LF line endings, 120-column
cap, semantic round-trip) is enforced on every test run, not only when someone
remembers to run the tool by hand.

The staging trees are held to the *same* policy as the active knowledge base:
a band package must already look like a knowledge-base document, so promotion
can never be the step that reflows, re-quotes or re-encodes its YAML.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "format_yaml.py"
TREES = {
    "knowledge": ROOT / "sources" / "knowledge",
    "2A": ROOT / "sources" / "2A",
    "2B": ROOT / "sources" / "2B",
}

#: A prose line longer than the 120 cap, of the kind a writer that emits one
#: physical line per value leaves inside an otherwise canonical `>-` block.
LONG_LINE = (
    "The banished Seer may not be hired by any warband whose current roster already "
    "holds a Hired Sword of the Elven kind, and the pack keeps both."
)


@pytest.mark.parametrize("tree", sorted(TREES))
def test_yaml_formatting_is_canonical(tree: str) -> None:
    root = TREES[tree]
    if not root.is_dir():
        pytest.skip(f"{root} is absent")
    result = subprocess.run(
        [sys.executable, str(TOOL), "--check", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"format_yaml --check failed on {tree}:\n" + (result.stdout or result.stderr)
    )
    summary = (result.stdout or "").strip().splitlines()[-1]
    assert "0 would change" in summary, (
        f"{tree} YAML needs reformatting "
        f"(run: python tools/format_yaml.py --write {root.relative_to(ROOT)}):\n"
        + (result.stdout or result.stderr)
    )


def run_tool(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_a_folded_block_written_as_one_line_is_rewrapped(tmp_path: Path) -> None:
    """The one-line-per-value shape is what the check flags and must repair.

    A writer that folds prose without wrapping it leaves a block whose body is
    a single line past the 120 maximum; the check warns about it, so writing it
    back must rewrap it — with the value intact and nothing left to do on the
    next run.
    """
    path = tmp_path / "staged.yaml"
    path.write_text(
        "catalog: campaign-magic\n"
        "lores:\n"
        "  - id: lore.fire\n"
        "    effect: >-\n"
        f"      {LONG_LINE}\n"
        "    effect_i18n:\n"
        "      es: >-\n"
        f"        {LONG_LINE}\n",
        encoding="utf-8",
        newline="\n",
    )
    before = yaml.safe_load(path.read_text(encoding="utf-8"))

    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr

    text = path.read_text(encoding="utf-8")
    assert max(len(line) for line in text.splitlines()) <= 100
    assert yaml.safe_load(text) == before
    assert "0 would change" in run_tool("--check", str(path)).stdout


def test_a_folded_block_that_keeps_paragraphs_is_left_alone(tmp_path: Path) -> None:
    """Two paragraphs in one folded block are a value, not wrapping to undo.

    The rewrapped block could not re-parse to the same value, so the round-trip
    guard keeps the file byte for byte — the warning stays, the prose does not.
    """
    path = tmp_path / "paragraphs.yaml"
    document = (
        "lores:\n"
        "  - id: lore.fire\n"
        "    effect: >-\n"
        f"      {LONG_LINE}\n"
        "\n"
        "      A second paragraph the block keeps apart.\n"
    )
    path.write_text(document, encoding="utf-8", newline="\n")

    written = run_tool("--write", str(path))
    assert written.returncode == 0, written.stdout + written.stderr
    assert path.read_text(encoding="utf-8") == document
