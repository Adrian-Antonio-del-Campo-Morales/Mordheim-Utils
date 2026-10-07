"""Generation of a human coverage report without modifying KB or specs."""
from __future__ import annotations

from csv import DictReader, DictWriter
from dataclasses import asdict, dataclass, replace
import json
from hashlib import sha256
import re
from types import SimpleNamespace
from pathlib import Path

from mordheim_knowledge.loader import knowledge_root, read_yaml
from mordheim_knowledge.paths import project_root
from mordheim_combat_lab.verification.audit import verify_semantics
from mordheim_combat_lab.verification.inventory import binding_key, inventory
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
    combat_work_status: str = ""
    t13_origin: str = ""
    t13_disposition: str = ""
    t13_lots: str = ""
    t13_question_id: str = ""
    effect_text: str = ""
    canonical_id: str = ""
    development_family: str = ""
    semantic_dependencies: str = ""
    question_status: str = "none"
    decision_reference: str = ""
    next_action: str = ""
    audit_mode: str = "semantic"
    scope_basis: str = "kb"
    scope_category: str = ""


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _source_fields(source: dict | str | None) -> tuple[str, str]:
    if isinstance(source, str):
        return source, ""
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
            errors = getattr(fixture, "errors", ())
            if errors and target in pending:
                pending[target] = " | ".join(dict.fromkeys([
                    pending[target], *(f"{fixture.id}: {error}" for error in errors),
                ]))
    interactions: dict[str, list[str]] = {}
    for pair in report.verified_interactions:
        for binding in pair:
            interactions.setdefault(binding, []).append(" + ".join(pair))
    return scenarios, interactions, pending


def build_audit_rows(knowledge: Path | None = None, specs: Path | None = None, *,
                     inventory_only: bool = False) -> tuple[AuditRow, ...]:
    """Combine the editorial inventory, scope and actually executed evidence."""
    from mordheim_combat_lab.verification.specifications import load_fixtures

    root = Path(knowledge) if knowledge else knowledge_root()
    documents = {}
    covered_nodes = set()

    def document(path):
        if path not in documents:
            documents[path] = read_yaml(path)
        return documents[path]

    report = (SimpleNamespace(obligations=inventory(root), verified=(), fixtures=(),
                              pending=(), verified_interactions=())
              if inventory_only else verify_semantics(root, specs))
    shared_path = root / "catalog/rules/special-rules.yaml"
    shared = {rule["id"]: rule for rule in
              (document(shared_path).get("rules", []) if shared_path.exists() else [])}
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
               binding: dict | None = None, effect_text: str = "", canonical_id: str = "") -> None:
        if scope != "YES" and not _text(reason).strip():
            reason = ("Runtime scope not classified in the KB." if scope == "UNCLASSIFIED"
                      else "Exclusion or deferral reason not documented in the KB.")
        obligation = obligations.get(identifier)
        key = binding_key(binding) if binding else (obligation.binding if obligation else "unbound")
        if scope == "UNCLASSIFIED":
            structural, semantic, semantic_reason = "unclassified", "unclassified", reason
        elif scope == "LATER":
            structural, semantic, semantic_reason = "not_applicable", "deferred", reason
        elif scope != "YES":
            structural, semantic, semantic_reason = "not_applicable", "out_of_scope", reason
        elif obligation is None:
            structural, semantic = "missing", "not_run" if inventory_only else "pending"
            semantic_reason = "There is no semantic obligation for this included effect."
        else:
            structural = "linked" if obligation.binding != "unbound" else "unbound"
            semantic = "not_run" if inventory_only else ("verified" if identifier in verified else "pending")
            semantic_reason = ("Semantic verification was not run." if inventory_only else
                               "" if semantic == "verified" else pending.get(identifier, "Incomplete evidence."))
        section, url = _source_fields(source)
        review_status = classify_review_status(
            scope=scope, verified=semantic == "verified",
            needs_ruling=identifier in unresolved_questions,
            missing_dependencies=bool(not inventory_only and obligation and set(obligation.dependencies) - verified),
        )
        assessments = interaction_risks.get(key, []) if scope == "YES" else []
        if assessments:
            risk_level = max((item.risk_level for item in assessments), key=RISK_ORDER.__getitem__)
            requirement = max((item.verification_requirement for item in assessments),
                              key=REQUIREMENT_ORDER.__getitem__)
            statuses = sorted({item.status for item in assessments})
            reasons = sorted({reason for item in assessments for reason in item.risk_reasons})
            evidence = sorted({evidence for item in assessments for evidence in item.evidence})
        elif scope == "YES" and inventory_only:
            risk_level, requirement, statuses, reasons, evidence = "not_assessed", "not_assessed", ["not_run"], [], []
        elif scope == "YES":
            risk_level, requirement, statuses, reasons, evidence = "low", "optional", ["independent"], [], []
        else:
            risk_level, requirement, statuses, reasons, evidence = "not_applicable", "not_applicable", ["not_applicable"], [], []
        rows.append(replace(AuditRow(
            identifier, kind, name, source_file, section, url, scope, reason,
            "UNKNOWN" if scope == "UNCLASSIFIED" else ("YES" if implemented else "NO"),
            key, structural, semantic, semantic_reason,
            "; ".join(sorted(set(scenarios.get(identifier, [])))),
            "; ".join(sorted(set(interactions.get(key, [])))),
            " | ".join(dict.fromkeys(rulings.get(identifier, []))),
            review_status,
            " | ".join(dict.fromkeys(questions.get(identifier, []))),
            " | ".join(dict.fromkeys(interpretations.get(identifier, []))),
            risk_level, requirement, "; ".join(statuses),
            "; ".join(reasons), "; ".join(evidence),
        ), effect_text=effect_text, canonical_id=canonical_id or identifier.rsplit("/", 1)[-1],
           semantic_dependencies="; ".join(obligation.dependencies if obligation else ()),
           audit_mode="inventory" if inventory_only else "semantic"))

    scope_doc = document(root / "registry/runtime-scope.yaml")
    exclusions = {row["id"]: row.get("reason", "") for row in scope_doc.get("mechanic_exclusions", [])}
    core_path = root / "catalog/rules/core-combat.yaml"
    if core_path.exists():
        for rule in document(core_path).get("rules", []):
            if not isinstance(rule, dict) or not rule.get("id"):
                continue
            covered_nodes.add(id(rule))
            runtime = rule.get("runtime") or {}
            scope = runtime.get("scope", "YES")
            append(identifier=f"core/{rule['id']}", kind="core", name=rule.get("name", rule["id"]),
                   source_file="catalog/rules/core-combat.yaml", source={"section": rule.get("section"),
                   "url": rule.get("source_url")}, scope=scope,
                   reason=runtime.get("reason", ""), implemented=runtime.get("implemented", "YES") == "YES",
                   binding={"kind": "core", "id": rule["id"]}, effect_text=rule.get("effect", ""))

    catalogue_path = root / "catalog/mechanics/close-combat.yaml"
    catalogue = document(catalogue_path)
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        # The `skills` family of the mechanics catalogue holds the executable
        # close-combat mechanics; catalog/skills is the selectable-skill
        # catalogue and is not the source of mechanic audit rows.
        mechanic_rows = catalogue.get(family, [])
        source_file = "catalog/mechanics/close-combat.yaml"
        for mechanic in mechanic_rows:
            if not isinstance(mechanic, dict) or not mechanic.get("id"):
                continue
            covered_nodes.add(id(mechanic))
            reason = exclusions.get(mechanic["id"], "")
            scope = "NO" if mechanic["id"] in exclusions else "YES"
            append(identifier=f"mechanic/{mechanic['id']}", kind=f"mechanic:{family}",
                   name=mechanic.get("name", mechanic["id"]), source_file=source_file,
                   source={"section": family, "url": mechanic.get("rules_source_url")}, scope=scope,
                   reason=reason, implemented=scope == "YES",
                   binding={"kind": "mechanic", "id": mechanic["id"]}, effect_text=mechanic.get("effect", ""))

    mappings_path = root / "catalog/mechanics/simulation-mappings.yaml"
    mappings = {item["item_id"]: item for item in document(mappings_path).get("item_mappings", [])} if mappings_path.exists() else {}
    options = {item["engine_option"]: item["id"] for family in
               ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills")
               for item in catalogue.get(family, []) if item.get("engine_option")}
    for path in sorted((root / "catalog/items").rglob("*.yaml")):
        for item in document(path).get("items", []):
            if not isinstance(item, dict) or not item.get("id"):
                continue
            covered_nodes.add(id(item))
            mapping = mappings.get(item["id"], {})
            state = item.get("combat_status", mapping.get("status"))
            scope = {"implemented": "YES", "out_of_scope": "NO", "pending": "LATER"}.get(state, "UNCLASSIFIED")
            mechanic_id = item.get("mechanic_id") or options.get(mapping.get("engine_option"))
            append(identifier=f"item/{item['id']}", kind="item_effect", name=item.get("name", item["id"]),
                   source_file=path.relative_to(root).as_posix(), source=next(iter(item.get("source_refs", [])), None),
                   scope=scope, reason=item.get("combat_reason", mapping.get("reason", "")),
                   implemented=state == "implemented" and mechanic_id is not None,
                   binding={"kind": "mechanic", "id": mechanic_id} if mechanic_id else None,
                   effect_text=item.get("effect", ""))

    paths = sorted((root / "bands").glob("*/*/special-rules.yaml"))
    paths += sorted((root / "catalog/skills").rglob("*.yaml"))
    for path in paths:
        doc = document(path)
        collection = path.parent.parent.name if "bands" in path.parts else "catalog"
        owner = path.parent.name if collection != "catalog" else path.stem
        for rule in doc.get("rules", doc.get("skills", [])):
            if not isinstance(rule, dict) or not rule.get("id"):
                continue  # the recursive pass retains anonymous source entries
            covered_nodes.add(id(rule))
            runtime = rule.get("runtime") or {}
            effects = runtime.get("effects") or []
            if not effects:
                effects = [{"id": "unclassified", "scope": runtime.get("scope", "UNCLASSIFIED"),
                            "reason": runtime.get("reason", "No classified runtime effects."), "binding": None}]
            for effect in effects:
                identifier = f"rule/{collection}/{owner}/{rule['id']}/{effect['id']}"
                scope = effect.get("scope", runtime.get("scope", "UNCLASSIFIED"))
                binding = effect.get("binding")
                implemented = scope == "YES" and binding is not None and runtime.get("implemented", "YES") == "YES"
                append(identifier=identifier, kind="editorial_effect", name=rule.get("name", rule["id"]),
                       source_file=path.relative_to(root).as_posix(), source=rule.get("source") or next(iter(rule.get("source_refs", [])), None), scope=scope,
                       reason=effect.get("reason", runtime.get("reason", "")), implemented=implemented,
                       binding=binding, canonical_id=rule["id"],
                       effect_text=rule.get("effect") or shared.get(rule.get("rule_ref"), {}).get("effect", "")
                       or (f"Unresolved or empty rule_ref: {rule['rule_ref']}" if rule.get("rule_ref") else ""))

    def source_nodes(value, locator="", owner=""):
        if isinstance(value, dict):
            owner = str(value.get("id") or owner)
            yield value, locator, owner
            for key, child in value.items():
                # Localizations and runtime effect descriptors describe the same
                # effect, not additional printed source rules.
                if key == "runtime" or key.endswith("_i18n") or key in {"source", "source_refs", "source_notes"}:
                    continue
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                yield from source_nodes(child, f"{locator}/{escaped}", owner)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from source_nodes(child, f"{locator}/{index}", owner)

    # Scan nodes, never mark an entire file covered after reading its main list.
    # Prose outside `effect` remains an unclassified candidate: no keyword
    # heuristic can safely decide whether an equipment note affects a duel.
    identifiers = {row.id for row in rows}
    source_paths = sorted(path for path in root.rglob("*") if path.suffix in {".yaml", ".yml"})
    known_ids = {row.canonical_id for row in rows} | {
        str(node["id"]) for path in source_paths
        for node, _, _ in source_nodes(document(path)) if node.get("id") and (
            "effect" in node or "effect_i18n" in node or node.get("rule_ref")
            or (node.get("runtime") or {}).get("effects"))}
    for path in source_paths:
        relative = path.relative_to(root).as_posix()
        for rule, locator, owner in source_nodes(document(path)):
            runtime = rule.get("runtime") or {}
            reference = rule.get("rule_ref")
            text = rule.get("effect") or shared.get(reference, {}).get("effect", "")
            if not text and rule.get("effect_i18n"):
                text = json.dumps(rule["effect_i18n"], ensure_ascii=False, sort_keys=True)
            if id(rule) not in covered_nodes and ("effect" in rule or "effect_i18n" in rule or reference or runtime.get("effects")):
                effects = runtime.get("effects") or [{"id": "unclassified"}]
                for effect in effects:
                    scope = effect.get("scope", runtime.get("scope", "UNCLASSIFIED"))
                    binding = effect.get("binding")
                    identifier = f"source/{relative}/{rule.get('id') or '@' + locator}/{effect.get('id', 'unclassified')}"
                    if identifier in identifiers:
                        identifier += "@" + locator
                    identifiers.add(identifier)
                    reason = effect.get("reason", runtime.get("reason", ""))
                    if reference and not text:
                        reason = f"Unresolved or empty rule_ref: {reference}. " + reason
                    append(identifier=identifier, kind="source_effect", name=rule.get("name", owner or locator),
                           source_file=relative, source=rule.get("source") or next(iter(rule.get("source_refs", [])), None),
                           scope=scope, reason=reason,
                           implemented=scope == "YES" and binding is not None and runtime.get("implemented") == "YES",
                           binding=binding, canonical_id=rule.get("id") or "@" + locator, effect_text=_text(text))
            for field in ("note", "notes", "description", "rule", "rules", "abilities", "equipment_restrictions", "restrictions",
                          "traits", "unresolved_references", "rule_ids", "special_skill_rule_ids"):
                value = rule.get(field)
                if not value:
                    continue
                # Structured children are visited above; retain their scalar
                # siblings too, without duplicating child rule definitions.
                values = value if isinstance(value, list) else [value]
                for index, prose in enumerate(values):
                    if field in {"rule_ids", "special_skill_rule_ids"}:
                        if prose in known_ids:
                            continue  # its definition already has a source row
                        prose = f"Unresolved {field} reference: {prose}"
                    elif field in {"traits", "unresolved_references"}:
                        prose = json.dumps(prose, ensure_ascii=False, sort_keys=True)
                    if not isinstance(prose, str) or not prose.strip():
                        continue
                    target = f"{locator}/{field}" + (f"/{index}" if isinstance(value, list) else "")
                    append(identifier=f"source/{relative}/@{target}/unclassified", kind="source_effect",
                           name=f"{rule.get('name', owner or relative)} ({field})", source_file=relative,
                           source=rule.get("source") or next(iter(rule.get("source_refs", [])), None),
                           scope="UNCLASSIFIED", reason="Source prose requires duel-scope classification.",
                           implemented=False, canonical_id="@" + target, effect_text=prose)
    result = tuple(sorted(rows, key=lambda row: (row.kind, row.source_file, row.id)))
    review = project_root() / "docs/knowledge/2a2b/tasks/T13-audit-scope-review.csv"
    if root.resolve() == knowledge_root().resolve() and review.exists():
        result = _apply_scope_review(result, review)
    return result


def _apply_scope_review(rows: tuple[AuditRow, ...], path: Path) -> tuple[AuditRow, ...]:
    """Apply reviewed source scope without activating bindings or certifying code.

    Explicit KB scope wins. Changed text invalidates a previous review instead
    of letting an old exclusion hide a newly relevant clause.
    """
    decisions = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for decision in DictReader(stream):
            identifier = decision["id"]
            if (identifier in decisions or decision["scope"] not in {"YES", "NO", "UNCLASSIFIED"}
                    or not decision["reason"].strip()):
                raise ValueError(f"Invalid or duplicate audit scope review: {identifier}")
            decisions[identifier] = decision
    result = []
    for row in rows:
        decision = decisions.get(row.id)
        if row.scope != "UNCLASSIFIED" or decision is None:
            result.append(row)
            continue
        if (decision["source_file"] != row.source_file
                or decision["effect_sha256"] != sha256(row.effect_text.encode("utf-8")).hexdigest()):
            result.append(replace(row, scope_basis="stale_review",
                scope_reason="Source changed since scope review; review this candidate again.",
                semantic_reason="Source changed since scope review; review this candidate again."))
            continue
        scope, reason = decision["scope"], decision["reason"]
        result.append(replace(row, scope=scope, scope_reason=reason,
            scope_basis="reviewed_source", scope_category=decision["category"],
            structural_status="not_assessed" if scope == "YES" else "not_applicable" if scope == "NO" else "unclassified",
            semantic_status=("not_run" if row.audit_mode == "inventory" else "pending") if scope == "YES"
                else "out_of_scope" if scope == "NO" else "unclassified",
            semantic_reason="Scope review only; implementation and semantic evidence are not inferred." if scope == "YES" else reason,
            review_status=classify_review_status(scope=scope, verified=False,
                needs_ruling=bool(row.question and not row.ruling), missing_dependencies=False)))
    return tuple(result)


def classify_review_status(*, scope: str, verified: bool, needs_ruling: bool,
                          missing_dependencies: bool) -> str:
    """Explicit work status, never inferred from free-text reason wording."""
    if scope == "UNCLASSIFIED":
        return "needs_classification"
    if scope == "LATER":
        return "needs_ruling" if needs_ruling else "deferred"
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


def combat_audit_rows(rows: tuple[AuditRow, ...], plan: Path | None = None) -> tuple[AuditRow, ...]:
    """Include executable obligations and separately labelled historical T13 candidates.

    Planning data never changes canonical scope or constitutes execution evidence.
    Missing historical targets remain visible until their reconciliation is recorded.
    """
    current = {row.id: row for row in rows}
    # Retain exclusions and unclassified candidates too: lack of an operator is
    # not proof that the printed effect cannot affect combat.
    selected = dict(current)
    if plan is not None and plan.exists():
        with plan.open(encoding="utf-8-sig", newline="") as stream:
            for origin in DictReader(stream):
                targets = [item["id"] for item in json.loads(origin["existing_audit_status"] or "[]")
                           if item["id"] in current]
                item_target = f"item/{origin['canonical_id']}"
                if origin["family"] == "item" and item_target in current:
                    targets = list(dict.fromkeys([*targets, item_target]))
                canonical_file = origin["canonical_file"].removeprefix("sources/knowledge/")
                targets = list(dict.fromkeys([*targets, *(row.id for row in rows
                    if row.source_file == canonical_file
                    and row.canonical_id == origin["canonical_id"])]))
                if origin["disposition"] in {"campaign", "data-only"}:
                    # Historical planning cannot remove current KB candidates.
                    continue
                if origin["disposition"] not in {"included", "mixed", "construction", "source-blocked", "excluded"}:
                    continue
                if not targets:
                    identifier = f"planning/{origin['origin_key']}"
                    selected[identifier] = AuditRow(
                        id=identifier, kind="planning_effect", name=origin["canonical_id"],
                        source_file=origin["canonical_file"], section="T13 historical origin",
                        source_url="", scope="UNCLASSIFIED",
                        scope_reason="Historical T13 target is absent from the current rule audit; reconcile its clauses and current scope.",
                        implemented="UNKNOWN", binding="unbound", structural_status="unclassified",
                        semantic_status="unclassified", semantic_reason="Planning only; no execution evidence inferred.",
                        scenarios="", interactions="", ruling="", review_status="needs_classification",
                        combat_work_status="needs_target_reconciliation", question=origin["source_question"],
                        t13_origin=origin["origin_key"], t13_disposition=origin["disposition"],
                        t13_lots=origin["lots"], t13_question_id=origin["question_id"],
                        effect_text=origin["clause_summary"], canonical_id=origin["canonical_id"],
                        development_family=origin.get("mechanisms", ""),
                    )
                for target in targets:
                    row = selected.get(target, current[target])
                    selected[target] = replace(row, **{
                        field: " | ".join(dict.fromkeys(filter(None, (getattr(row, field), origin[column]))))
                        for field, column in (("t13_origin", "origin_key"), ("t13_disposition", "disposition"),
                                              ("t13_lots", "lots"), ("t13_question_id", "question_id"),
                                              ("question", "source_question"))
                    }, development_family=row.development_family or origin.get("mechanisms", ""))
    decisions = {}
    decision_path = project_root() / "docs/decisions/design-rulings.md"
    if plan is not None and decision_path.exists():
        for section in re.split(r"(?m)^## ", decision_path.read_text(encoding="utf-8"))[1:]:
            heading, _, body = section.partition("\n")
            for identifier in re.findall(r"\b[QF]\d{3}\b", heading):
                decisions["T13-" + identifier] = (body.strip(), heading)
    result = []
    actions = {
        "needs_target_reconciliation": "Locate the current source/contract and reconcile its target before deciding whether new implementation is needed.",
        "needs_classification": "Classify the printed effect against the current 1v1 duel scope.",
        "excluded": "No duel implementation required.",
        "deferred_scope_review": "Review scope and prerequisites before admitting or implementing the effect.",
        "needs_ruling": "Resolve the explicit unanswered interpretation before implementation.",
        "needs_question_review": "Reconcile the historical question with current source decisions before implementation; do not assume it requires a new user answer.",
        "implementation_required": "Implement the complete included effect, reusing its binding family.",
        "implemented_pending_verification": "Review existing evidence; repair verification metadata or missing evidence without reimplementing the effect.",
        "verified_modular": "No modular implementation work required; optimized ports remain separate.",
    }
    for row in selected.values():
        ids = row.t13_question_id.split(" | ")
        answers = [decisions[key] for key in ids if key in decisions]
        question_status = ("resolved" if answers and all(key in decisions for key in ids if key)
                           else "needs_review" if row.t13_question_id
                           else "unresolved" if row.question and not row.ruling else "resolved" if row.ruling else "none")
        if answers:
            row = replace(row, ruling=" | ".join(dict.fromkeys([row.ruling, *(answer[0] for answer in answers)])).strip(" |"),
                          decision_reference=" | ".join("docs/decisions/design-rulings.md: " + answer[1] for answer in answers))
        if question_status == "resolved" and row.review_status == "needs_ruling":
            row = replace(row, review_status=("deferred" if row.scope == "LATER" else
                "verified" if row.semantic_status == "verified" else "ready"))
        if row.combat_work_status:
            status = row.combat_work_status
        elif row.scope == "NO":
            status = "excluded"
        elif row.scope == "UNCLASSIFIED":
            status = "needs_classification"
        elif question_status == "unresolved":
            status = "needs_ruling"
        elif row.scope == "LATER":
            status = "deferred_scope_review"
        elif row.implemented != "YES" and question_status == "needs_review":
            status = "needs_question_review"
        elif row.implemented == "UNKNOWN":
            status = "needs_target_reconciliation"
        elif row.implemented != "YES":
            status = "implementation_required"
        else:
            status = "verified_modular" if row.semantic_status == "verified" else "implemented_pending_verification"
        result.append(replace(row, combat_work_status=status, question_status=question_status,
                              next_action=actions[status]))
    return tuple(sorted(result, key=lambda row: (row.kind, row.source_file, row.id)))


def generate_audit(*, knowledge: Path | None = None, specs: Path | None = None,
                   output: Path | None = None, scope: str | None = None,
                   status: str | None = None, review_status: str | None = None,
                   inventory_only: bool = False, t13: bool = False,
                   family: str | None = None, work_status: str | None = None) -> tuple[Path, Path]:
    rows = (build_audit_rows(knowledge, specs, inventory_only=True) if inventory_only
            else build_audit_rows(knowledge, specs))
    plan = (project_root() / "docs/knowledge/2a2b/tasks/T13-obligations.csv"
            if knowledge is None or Path(knowledge).resolve() == knowledge_root().resolve() else None)
    operational = combat_audit_rows(rows, plan)
    combat = filter_audit_rows(tuple(row for row in operational
        if (not t13 or row.t13_origin) and (family is None or family in
            (json.loads(row.development_family) if row.development_family else []))
        and (work_status is None or row.combat_work_status == work_status)), scope, status, review_status)
    rules = filter_audit_rows(tuple(row for row in combat if row.kind in {"editorial_effect", "item_effect", "source_effect"}),
                              scope, status, review_status)
    output = Path(output) if output else project_root() / "outputs/audit"
    from mordheim_combat_lab.report_naming import timestamped_report_path
    combat_path = timestamped_report_path(output, "combat-audit", ".csv") if output == project_root() / "outputs/audit" else output / "combat-audit.csv"
    rules_path = combat_path.with_name(combat_path.name.replace("combat-audit", "rules-audit", 1))
    write_csv(combat, combat_path)
    write_csv(rules, rules_path)
    return combat_path, rules_path
