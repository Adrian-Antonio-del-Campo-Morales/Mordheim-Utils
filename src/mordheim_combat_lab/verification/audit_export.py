"""Generación de un informe humano de cobertura sin modificar KB ni specs."""
from __future__ import annotations

from csv import DictWriter
from dataclasses import asdict, dataclass
from pathlib import Path

from mordheim_knowledge.loader import knowledge_root, read_yaml
from mordheim_knowledge.paths import project_root
from mordheim_combat_lab.verification.audit import verify_semantics
from mordheim_combat_lab.verification.inventory import binding_key
from mordheim_combat_lab.verification.interactions import REQUIREMENT_ORDER, RISK_ORDER


@dataclass(frozen=True)
class AuditRow:
    id: str
    kind: str
    name: str
    source_file: str
    section: str
    source_url: str
    scope: str
    scope_reason: str
    implemented: str
    binding: str
    structural_status: str
    semantic_status: str
    semantic_reason: str
    scenarios: str
    interactions: str
    ruling: str
    review_status: str = "ready"
    question: str = ""
    interpretation: str = ""
    risk_level: str = "not_applicable"
    verification_requirement: str = "not_applicable"
    interaction_status: str = "not_applicable"
    risk_reasons: str = ""
    coverage_evidence: str = ""


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _source_fields(source: dict | None) -> tuple[str, str]:
    source = source or {}
    return _text(source.get("section")), _text(source.get("url"))


def _scenario_evidence(report) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, str]]:
    scenarios: dict[str, list[str]] = {}
    pending = dict(report.pending)
    # Fixtures in the result preserve target IDs, while interpretations remain
    # in the independent source specifications. Rulings are loaded separately
    # by build_audit_rows to avoid turning runtime output into an oracle.
    for fixture in report.fixtures:
        for target in fixture.targets:
            scenarios.setdefault(target, []).append(fixture.id)
    interactions: dict[str, list[str]] = {}
    for pair in report.verified_interactions:
        for binding in pair:
            interactions.setdefault(binding, []).append(" + ".join(pair))
    return scenarios, interactions, pending


def build_audit_rows(knowledge: Path | None = None, specs: Path | None = None) -> tuple[AuditRow, ...]:
    """Combine el inventario editorial, scope y evidencia realmente ejecutada."""
    from mordheim_combat_lab.verification.specifications import load_fixtures

    root = Path(knowledge) if knowledge else knowledge_root()
    report = verify_semantics(root, specs)
    obligations = {item.id: item for item in report.obligations}
    verified = set(report.verified)
    scenarios, interactions, pending = _scenario_evidence(report)
    interpretations: dict[str, list[str]] = {}
    questions: dict[str, list[str]] = {}
    rulings: dict[str, list[str]] = {}
    unresolved_questions: set[str] = set()
    interaction_risks: dict[str, list] = {}
    for assessment in getattr(report, "interaction_assessments", ()):
        for binding in assessment.bindings:
            interaction_risks.setdefault(binding, []).append(assessment)
    for fixture in load_fixtures(specs):
        interpretation = _text(fixture.get("interpretation"))
        for source in fixture.get("sources", []):
            if interpretation:
                interpretations.setdefault(source["target"], []).append(interpretation)
            target = source["target"]
            if fixture.get("question"):
                questions.setdefault(target, []).append(fixture["question"])
                if not fixture.get("ruling"):
                    unresolved_questions.add(target)
            if fixture.get("ruling"):
                rulings.setdefault(target, []).append(fixture["ruling"])

    rows: list[AuditRow] = []

    def append(*, identifier: str, kind: str, name: str, source_file: str,
               source: dict | None, scope: str, reason: str, implemented: bool,
               binding: dict | None = None) -> None:
        if scope != "YES" and not _text(reason).strip():
            reason = "Razón de exclusión o aplazamiento no documentada en la KB."
        obligation = obligations.get(identifier)
        key = binding_key(binding) if binding else (obligation.binding if obligation else "unbound")
        if scope != "YES":
            structural, semantic, semantic_reason = "not_applicable", "out_of_scope", reason
        elif obligation is None:
            structural, semantic = "missing", "pending"
            semantic_reason = "No existe una obligación semántica para este efecto incluido."
        else:
            structural = "linked" if obligation.binding != "unbound" else "unbound"
            semantic = "verified" if identifier in verified else "pending"
            semantic_reason = "" if semantic == "verified" else pending.get(identifier, "Evidencia incompleta.")
        section, url = _source_fields(source)
        review_status = classify_review_status(
            scope=scope, verified=semantic == "verified",
            needs_ruling=identifier in unresolved_questions,
            missing_dependencies=bool(obligation and set(obligation.dependencies) - verified),
        )
        assessments = interaction_risks.get(key, []) if scope == "YES" else []
        if assessments:
            risk_level = max((item.risk_level for item in assessments), key=RISK_ORDER.__getitem__)
            requirement = max((item.verification_requirement for item in assessments),
                              key=REQUIREMENT_ORDER.__getitem__)
            statuses = sorted({item.status for item in assessments})
            reasons = sorted({reason for item in assessments for reason in item.risk_reasons})
            evidence = sorted({evidence for item in assessments for evidence in item.evidence})
        elif scope == "YES":
            risk_level, requirement, statuses, reasons, evidence = "low", "optional", ["independent"], [], []
        else:
            risk_level, requirement, statuses, reasons, evidence = "not_applicable", "not_applicable", ["not_applicable"], [], []
        rows.append(AuditRow(
            identifier, kind, name, source_file, section, url, scope, reason,
            "YES" if implemented else "NO", key, structural, semantic, semantic_reason,
            "; ".join(sorted(set(scenarios.get(identifier, [])))),
            "; ".join(sorted(set(interactions.get(key, [])))),
            " | ".join(dict.fromkeys(rulings.get(identifier, []))),
            review_status,
            " | ".join(dict.fromkeys(questions.get(identifier, []))),
            " | ".join(dict.fromkeys(interpretations.get(identifier, []))),
            risk_level, requirement, "; ".join(statuses),
            "; ".join(reasons), "; ".join(evidence),
        ))

    scope_doc = read_yaml(root / "registry/runtime-scope.yaml")
    exclusions = {row["id"]: row.get("reason", "") for row in scope_doc.get("mechanic_exclusions", [])}
    core_path = root / "catalog/rules/core-combat.yaml"
    if core_path.exists():
        for rule in read_yaml(core_path).get("rules", []):
            runtime = rule.get("runtime") or {}
            scope = runtime.get("scope", "YES")
            append(identifier=f"core/{rule['id']}", kind="core", name=rule.get("name", rule["id"]),
                   source_file="catalog/rules/core-combat.yaml", source={"section": rule.get("section"),
                   "url": rule.get("source_url")}, scope=scope,
                   reason=runtime.get("reason", ""), implemented=runtime.get("implemented", "YES") == "YES",
                   binding={"kind": "core", "id": rule["id"]})

    catalogue_path = root / "catalog/mechanics/close-combat.yaml"
    catalogue = read_yaml(catalogue_path)
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for mechanic in catalogue.get(family, []):
            reason = exclusions.get(mechanic["id"], "")
            scope = "NO" if mechanic["id"] in exclusions else "YES"
            append(identifier=f"mechanic/{mechanic['id']}", kind=f"mechanic:{family}",
                   name=mechanic.get("name", mechanic["id"]), source_file="catalog/mechanics/close-combat.yaml",
                   source={"section": family, "url": mechanic.get("rules_source_url")}, scope=scope,
                   reason=reason, implemented=scope == "YES",
                   binding={"kind": "mechanic", "id": mechanic["id"]})

    paths = sorted((root / "bands").glob("*/*/special-rules.yaml"))
    paths += sorted((root / "catalog/skills").glob("*.yaml"))
    for path in paths:
        document = read_yaml(path)
        collection = path.parent.parent.name if "bands" in path.parts else "catalog"
        owner = path.parent.name if collection != "catalog" else path.stem
        for rule in document.get("rules", document.get("skills", [])):
            runtime = rule.get("runtime") or {}
            effects = runtime.get("effects") or []
            if not effects:
                effects = [{"id": "unclassified", "scope": runtime.get("scope", "NO"),
                            "reason": runtime.get("reason", "No hay efectos runtime clasificados."), "binding": None}]
            for effect in effects:
                identifier = f"rule/{collection}/{owner}/{rule['id']}/{effect['id']}"
                scope = effect.get("scope", runtime.get("scope", "NO"))
                binding = effect.get("binding")
                implemented = scope == "YES" and binding is not None and runtime.get("implemented", "YES") == "YES"
                append(identifier=identifier, kind="editorial_effect", name=rule.get("name", rule["id"]),
                       source_file=path.relative_to(root).as_posix(), source=rule.get("source"), scope=scope,
                       reason=effect.get("reason", runtime.get("reason", "")), implemented=implemented,
                       binding=binding)
    return tuple(sorted(rows, key=lambda row: (row.kind, row.source_file, row.id)))


def classify_review_status(*, scope: str, verified: bool, needs_ruling: bool,
                          missing_dependencies: bool) -> str:
    """Estado de trabajo explícito, nunca inferido de palabras del motivo libre."""
    if scope != "YES":
        return "not_applicable"
    if needs_ruling:
        return "needs_ruling"
    if verified:
        return "verified"
    return "blocked_by_dependency" if missing_dependencies else "ready"


def filter_audit_rows(rows: tuple[AuditRow, ...], scope: str | None = None,
                      status: str | None = None, review_status: str | None = None) -> tuple[AuditRow, ...]:
    return tuple(row for row in rows
                 if (scope is None or row.scope == scope)
                 and (status is None or row.semantic_status == status)
                 and (review_status is None or row.review_status == review_status))


def write_csv(rows: tuple[AuditRow, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = DictWriter(stream, fieldnames=list(AuditRow.__dataclass_fields__))
        writer.writeheader()
        # Keep one physical line per audit row. Multiline YAML prose is valid
        # inside quoted CSV fields, but previews often display its continuation
        # as a spurious blank record.
        writer.writerows({key: " ".join(str(value).splitlines())
                          for key, value in asdict(row).items()} for row in rows)


def generate_audit(*, knowledge: Path | None = None, specs: Path | None = None,
                   output: Path | None = None, scope: str | None = None,
                   status: str | None = None, review_status: str | None = None) -> Path:
    rows = filter_audit_rows(build_audit_rows(knowledge, specs), scope, status, review_status)
    output = Path(output) if output else project_root() / "outputs/audit"
    path = output / "rules-audit.csv"
    write_csv(rows, path)
    return path
