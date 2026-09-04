"""verification.specifications: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_knowledge.loader import read_yaml
from pathlib import Path
import os
from mordheim_knowledge.paths import project_root


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


def load_interaction_policy(root: Path | None = None) -> dict | None:
    """Return the interaction policy document, or None when the corpus has none.

    The policy is a corpus-level artifact (sibling of the semantic fixtures); a
    root without one audits with the built-in default policy and no overrides.
    """
    path = specifications_root(root) / "interaction-policy.yaml"
    return read_yaml(path) if path.exists() else None


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
