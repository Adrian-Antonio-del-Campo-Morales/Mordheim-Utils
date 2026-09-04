"""verification.audit: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations
from mordheim_knowledge.loader import knowledge_root
from mordheim_knowledge.loader import read_yaml
from mordheim_combat_lab.verification.integrations import verify_integrations
from mordheim_combat_lab.verification.interactions import assess_interaction, normalize_interaction_contract
from mordheim_combat_lab.verification.inventory import fingerprint
from mordheim_combat_lab.verification.inventory import inventory
from mordheim_combat_lab.verification.operators import verify_operators
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_combat_lab.verification.reports import FixtureResult
from mordheim_combat_lab.verification.reports import REQUIRED_CASES
from mordheim_combat_lab.verification.reports import SemanticReport
from mordheim_combat_lab.verification.scenarios import check_case
from mordheim_combat_lab.verification.specifications import load_fixtures
from mordheim_combat_lab.verification.specifications import load_interaction_policy
from mordheim_combat_lab.verification.specifications import specifications_root
from pathlib import Path


def verify_semantics(root: Path | None = None, specs_root: Path | None = None) -> SemanticReport:
    root = root or knowledge_root()
    obligations = inventory(root)
    indexed = {item.id: item for item in obligations}
    dependencies = {item.id: set(item.dependencies) for item in obligations}
    results = []
    verified = set()
    declared_pending = {}
    errors = []
    contracts = {}
    proved_pairs = set()
    proved_higher = set()
    scope_digest = fingerprint(read_yaml(root / "registry/runtime-scope.yaml"))
    for spec in load_fixtures(specs_root):
        targets = tuple(source["target"] for source in spec.get("sources", []))
        local_errors = []
        if spec.get("scope_digest") != scope_digest:
            local_errors.append("scope changed or scope review missing")
        for source in spec.get("sources", []):
            item = indexed.get(source["target"])
            if item is None:
                local_errors.append(f"unknown target {source['target']}")
            elif item.source_digest != source.get("digest"):
                local_errors.append(f"source changed: {item.id}")
        extra_dependencies = set(spec.get("depends_on", []))
        if extra_dependencies - set(indexed):
            local_errors.append(f"unknown semantic dependencies: {sorted(extra_dependencies - set(indexed))}")
        elif spec.get("category") != "interaction":
            for target in targets:
                if target in dependencies:
                    dependencies[target].update(extra_dependencies)
        if spec.get("pending"):
            for target in targets:
                declared_pending[target] = spec["pending"]
            errors.extend(f"{spec['id']}: {error}" for error in local_errors)
            continue
        if spec.get("interaction_contract"):
            try:
                contract = normalize_interaction_contract(spec["interaction_contract"])
            except ValueError as error:
                local_errors.append(str(error))
            else:
                if not local_errors:
                    for target in targets:
                        binding = indexed[target].binding
                        if binding in contracts and contracts[binding] != contract:
                            local_errors.append(f"conflicting interaction contracts for {binding}")
                        contracts[binding] = contract
        if not targets or not spec.get("interpretation"):
            local_errors.append("specification needs source targets and independent interpretation")
        required = REQUIRED_CASES.get(spec.get("category"))
        if required is None:
            local_errors.append("unknown verification category")
            required = set()
        cases = spec.get("cases", [])
        case_ids = [case["id"] for case in cases]
        if len(case_ids) != len(set(case_ids)):
            local_errors.append("duplicate case IDs")
        passed = []
        roles = set()
        for case in cases:
            try:
                case_roles = set(case.get("roles", []))
                if case["operation"] == "compile" and case_roles - {"compiled", "grant", "accepted", "rejected"}:
                    raise ValueError("compile-only checks cannot satisfy behavioural roles")
                if case_roles - {"compiled", "grant", "accepted", "rejected"}:
                    observable = (case.get("distribution") or {}).get("observable", "")
                    if not observable.startswith("result.") and not any(
                        path.startswith(("result.", "context.")) for path in case.get("expect", {})
                    ):
                        raise ValueError("behavioural case requires a phase/state observable")
                check_case(case, root)
            except Exception as error:
                local_errors.append(f"{case['id']}: {type(error).__name__}: {error}")
            else:
                passed.append(case["id"])
                roles.update(case.get("roles", []))
        if required - roles:
            local_errors.append(f"missing executed case roles: {sorted(required - roles)}")
        if spec.get("category") != "interaction" and any(indexed[t].kind == "grant" for t in targets if t in indexed) and "grant" not in roles:
            local_errors.append("editorial target needs an executed grant assertion")
        killed, justified = [], []
        for mutant in spec.get("mutations", []):
            if set(mutant.get("cases", [])) - set(passed):
                local_errors.append(f"{mutant['id']}: witnesses must name passing baseline cases")
                continue
            witnesses = [case for case in cases if case["id"] in mutant.get("cases", [])]
            if not witnesses or any(case["operation"] == "compile" for case in witnesses):
                local_errors.append(f"{mutant['id']}: mutation needs behavioural witnesses")
                continue
            detected = False
            for case in witnesses:
                try:
                    check_case(case, root, mutant)
                except EvidenceMismatch:
                    detected = True
                except Exception as error:
                    local_errors.append(f"{mutant['id']}: invalid mutation: {error}")
            if detected:
                if mutant.get("equivalent_reason"):
                    local_errors.append(f"{mutant['id']}: claimed equivalent mutation changes an observable")
                else:
                    killed.append(mutant["id"])
            elif str(mutant.get("equivalent_reason") or "").strip():
                behavioural_ids = {case["id"] for case in cases if case["operation"] != "compile"}
                if set(mutant.get("cases", [])) != behavioural_ids:
                    local_errors.append(f"{mutant['id']}: equivalence must exercise every non-compile case")
                else:
                    justified.append(mutant["id"])
            else:
                local_errors.append(f"surviving mutation: {mutant['id']}")
        if not killed and not justified:
            local_errors.append("no behavioural mutation was detected or independently justified")
        results.append(FixtureResult(spec["id"], targets, tuple(passed), tuple(killed), tuple(local_errors), tuple(justified)))
        errors.extend(f"{spec['id']}: {error}" for error in local_errors)
        if not local_errors and spec.get("category") == "interaction":
            pair = tuple(sorted(spec.get("bindings", [])))
            if len(pair) < 2 or len(set(pair)) != len(pair) or any(binding not in {item.binding for item in obligations} for binding in pair):
                errors.append(f"{spec['id']}: interaction needs at least two distinct known binding variants")
            elif len(pair) > 2:
                proved_higher.add(pair)
            else:
                proved_pairs.add(pair)
        elif not local_errors:
            verified.update(targets)
    # A compositional proof cannot establish its own premise, even indirectly.
    visited, cyclic = set(), set()
    def visit(target, path):
        if target in path:
            cyclic.update(path[path.index(target):])
            return
        if target in visited:
            return
        for dependency in dependencies[target]:
            visit(dependency, (*path, target))
        visited.add(target)
    for target in dependencies:
        visit(target, ())
    if cyclic:
        errors.append(f"circular semantic dependencies: {sorted(cyclic)}")
        verified -= cyclic
    # Grant evidence cannot certify the mechanism it grants by implication.
    while True:
        missing = {target for target in verified if dependencies[target] - verified}
        if not missing:
            break
        verified -= missing
    pending = tuple((item.id, declared_pending.get(item.id,
        "dependency lacks semantic evidence" if dependencies[item.id] - verified
        else "independent semantic specification incomplete or missing"))
        for item in obligations if item.id not in verified)
    candidates = set()
    for left, right in combinations(sorted(contracts), 2):
        a, b = contracts[left], contracts[right]
        if (set(a["writes"]) & (set(b["reads"]) | set(b["writes"]))
                or set(b["writes"]) & set(a["reads"])):
            candidates.add((left, right))
    overrides = {}
    policy_name = "critical_and_high_required"
    policy = load_interaction_policy(specs_root)
    if policy is not None:
        if policy.get("schema_version") != 1:
            errors.append("unsupported interaction policy schema")
        policy_name = str(policy.get("policy") or policy_name)
        for override in policy.get("overrides", []):
            pair = tuple(sorted(override.get("bindings", [])))
            if len(pair) != 2 or len(set(pair)) != 2:
                errors.append("invalid interaction policy override")
            elif set(pair) - set(contracts):
                errors.append(f"interaction policy override references unknown bindings: {pair}")
            else:
                overrides[pair] = override
    assessments = []
    for pair in sorted(candidates | set(overrides)):
        try:
            assessments.append(assess_interaction(
                *pair, contracts, tested=pair in proved_pairs, override=overrides.get(pair)))
        except ValueError as error:
            errors.append(f"interaction policy {pair}: {error}")
    integrations, integration_errors = verify_integrations(root)
    errors.extend(integration_errors)
    operators, operator_errors = verify_operators()
    errors.extend(operator_errors)
    higher_path = specifications_root(specs_root) / "interactions.yaml"
    required_higher = set()
    if higher_path.exists():
        requirements = read_yaml(higher_path)
        if requirements.get("schema_version") != 1:
            errors.append("unsupported higher-order interaction inventory schema")
        known_bindings = {item.binding for item in obligations}
        for requirement in requirements.get("higher_order", []):
            group = tuple(sorted(requirement.get("bindings", [])))
            if len(group) < 3 or len(group) != len(set(group)) or set(group) - known_bindings or not requirement.get("reason"):
                errors.append("invalid higher-order interaction requirement")
            else:
                required_higher.add(group)
    else:
        errors.append("missing higher-order interaction inventory")
    return SemanticReport(
        tuple(replace(item, dependencies=tuple(sorted(dependencies[item.id]))) for item in obligations),
        tuple(results), tuple(sorted(verified)), pending, tuple(errors),
        tuple(sorted({item.binding for item in obligations} - set(contracts))),
        tuple(sorted(candidates - proved_pairs)), tuple(sorted(proved_pairs)), integrations, operators,
        tuple(sorted(proved_higher)), tuple(sorted(required_higher - proved_higher)),
        tuple(assessments), policy_name,
    )
