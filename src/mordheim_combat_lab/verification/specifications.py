"""verification.specifications: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_combat_lab.knowledge.loader import read_yaml
from pathlib import Path
import os
from mordheim_combat_lab.paths import project_root


def specifications_root(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    override = os.environ.get("MORDHEIM_COMBAT_LAB_SPECS_PATH")
    return Path(override) if override else project_root() / "tests" / "specs"


def load_phase_verification(ruleset: str = "mordheim", root: Path | None = None) -> dict:
    document = read_yaml(specifications_root(root) / "structural/phase-verification.yaml")
    if document.get("ruleset") != ruleset:
        raise ValueError(f"structural specification belongs to another ruleset: {ruleset}")
    return document


def load_fixtures(root: Path | None = None) -> tuple[dict, ...]:
    root = specifications_root(root)
    if not (root / "semantic").is_dir():
        raise FileNotFoundError(f"semantic specifications not found: {root}")
    result = []
    for path in sorted((root / "semantic").rglob("*.yaml")):
        document = read_yaml(path)
        if document.get("schema_version") != 1:
            raise ValueError(f"unsupported semantic schema: {path}")
        result.extend(document.get("specifications", []))
    ids = [spec["id"] for spec in result]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate semantic specification IDs")
    for spec in result:
        for name in ("question", "ruling"):
            if name in spec and (not isinstance(spec[name], str) or not spec[name].strip()):
                raise ValueError(f"{spec['id']}: {name} must be a non-empty string")
        if spec.get("question") and not spec.get("ruling") and not spec.get("pending"):
            raise ValueError(f"{spec['id']}: unresolved question requires pending")
    return tuple(result)
