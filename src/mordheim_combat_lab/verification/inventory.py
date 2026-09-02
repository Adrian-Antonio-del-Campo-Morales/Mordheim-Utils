"""verification.inventory: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json as json
from mordheim_knowledge.loader import knowledge_root
from mordheim_knowledge.loader import read_yaml
from pathlib import Path


def fingerprint(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Obligation:
    id: str
    kind: str
    binding: str
    source_digest: str
    source: dict
    text: str
    dependencies: tuple[str, ...] = ()


def binding_key(binding: dict | None) -> str:
    if not binding:
        return "unbound"
    return json.dumps({"kind": binding.get("kind"), "id": binding.get("id"),
                       "parameters": binding.get("parameters") or {}}, sort_keys=True)


def inventory(root: Path | None = None) -> tuple[Obligation, ...]:
    """Read fresh documents, including YES effects of unimplemented rules."""
    root = root or knowledge_root()
    result = []
    excluded = {r["id"] for r in read_yaml(root / "registry/runtime-scope.yaml").get("mechanic_exclusions", [])}
    catalogue = read_yaml(root / "catalog/mechanics/close-combat.yaml")
    core_path = root / "catalog/rules/core-combat.yaml"
    if core_path.exists():
        for row in read_yaml(core_path).get("rules", []):
            if (row.get("runtime") or {}).get("scope") in {"NO", "LATER"}:
                continue
            result.append(Obligation(
                f"core/{row['id']}", "core", binding_key({"kind": "core", "id": row["id"]}),
                fingerprint(row), {"file": "catalog/rules/core-combat.yaml", "id": row["id"],
                                   "url": row.get("source_url")}, row.get("effect", ""),
            ))
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for row in catalogue.get(family, []):
            if row["id"] in excluded:
                continue
            result.append(Obligation(
                f"mechanic/{row['id']}", "mechanic",
                binding_key({"kind": "mechanic", "id": row["id"]}),
                fingerprint(row), {"file": "catalog/mechanics/close-combat.yaml", "id": row["id"],
                                   "references": row.get("source_refs", []),
                                   "url": row.get("rules_source_url")},
                row.get("summary", ""),
            ))
    # Deliberately do not use load_bands/runtime_bindings: those are runtime
    # filters and must not make a pending or partly classified effect disappear.
    paths = sorted((root / "bands").glob("*/*/special-rules.yaml"))
    paths += sorted((root / "catalog/skills").glob("*.yaml"))
    for path in paths:
        document = read_yaml(path)
        collection = path.parent.parent.name if "bands" in path.parts else "catalog"
        owner = path.parent.name if collection != "catalog" else path.stem
        related = {}
        if collection != "catalog":
            for name in ("profiles.yaml", "equipment-access.yaml", "band.yaml"):
                related[name] = read_yaml(path.parent / name)
        for row in document.get("rules", document.get("skills", [])):
            runtime = row.get("runtime") or {}
            for effect in runtime.get("effects") or []:
                if effect.get("scope") != "YES":
                    continue
                binding = effect.get("binding")
                dependency = (f"mechanic/{binding['id']}",) if binding and binding.get("kind") == "mechanic" else ()
                result.append(Obligation(
                    f"rule/{collection}/{owner}/{row['id']}/{effect['id']}", "grant",
                    binding_key(binding), fingerprint({"rule": row, "context": related}),
                    {"file": path.relative_to(root).as_posix(), "id": row["id"],
                     "effect": effect["id"], **(row.get("source") or {})},
                    row.get("effect", row.get("summary", "")), dependency,
                ))
    ids = [item.id for item in result]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate semantic obligation IDs")
    return tuple(result)
