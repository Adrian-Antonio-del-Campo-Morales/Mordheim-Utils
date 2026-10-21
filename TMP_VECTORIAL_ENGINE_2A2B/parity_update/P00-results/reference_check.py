"""Check every ``e2e:`` origin declared by the P01 catalogue against the E2E cases.

Structural only: reads YAML scenario ids and the catalogue source, imports no
engine and executes no duel.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "apps/combat-lab/mordheim_combat_lab/verification/parity/_battery_cases.py"
E2E = ROOT / "tests/E2E/modular-engine/cases"
OUT = Path(__file__).resolve().parent / "reference-check.txt"


def scenario_ids() -> set[str]:
    found: set[str] = set()
    for path in E2E.rglob("*.yaml"):
        audit = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            audit_match = re.match(r"^\s*-\s*audit_id:\s*([A-Za-z0-9_./-]+)\s*$", line)
            if audit_match:
                audit = audit_match.group(1)
                continue
            id_match = re.match(r"^\s+id:\s*([A-Za-z0-9_.-]+)\s*$", line)
            if id_match and audit:
                found.add(f"{audit}::{id_match.group(1)}")
    return found


def origins() -> list[tuple[int, str]]:
    tree = ast.parse(CASES.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", "")
        if name != "_case" or len(node.args) < 5:
            continue
        origin = node.args[4]
        if isinstance(origin, ast.Constant) and isinstance(origin.value, str):
            if origin.value.startswith("e2e:"):
                found.append((node.lineno, origin.value[4:]))
    return found


def main() -> None:
    known = scenario_ids()
    declared = origins()
    missing = [(line, origin) for line, origin in declared if origin not in known]
    lines = [
        f"e2e_scenarios={len(known)}",
        f"catalogue_origins={len(declared)}",
        f"missing={len(missing)}",
    ]
    for line, origin in missing:
        lines.append(f"line {line}: {origin}")
    print("\n".join(lines))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
