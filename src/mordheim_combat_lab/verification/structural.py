"""verification.structural: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from functools import lru_cache
from mordheim_combat.phases import Phase
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import COMPILER_CONTRACTS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_construction.contracts import effect_index
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_execution_contract
from mordheim_knowledge.loader import load_mechanics
from mordheim_combat_lab.verification.specifications import load_phase_verification
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import runtime_bindings
from mordheim_combat_lab.verification.consumers import MODULAR_COMPLEX_SCENARIOS
from mordheim_combat_lab.verification.consumers import MODULAR_FIELD_CONSUMERS
from mordheim_combat_lab.verification.consumers import MODULAR_TAG_CONSUMERS
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VerificationReport:
    execution_mechanics: int
    projected_mechanics: int
    projected_trait_bindings: int
    evidenced_profile_bindings: int
    projected_automatic_compiler_bindings: int
    evidenced_selectable_compiler_bindings: int
    evidenced_special_compiler_bindings: int
    observable_canonical_bindings: int
    evidenced_complex_sequences: int
    modular_tag_consumers: int
    modular_operator_fields: int
    modular_execution_mechanics: int
    implemented_rule_records: int
    canonical_bindings: int
    operator_fields: int
    complex_rules: int
    interaction_groups: int
    errors: tuple[str, ...] = ()

    @property
    def structural_complete(self) -> bool:
        return not self.errors

    @property
    def complete(self) -> bool:
        """Compatibility alias: structural completeness, NOT semantic proof."""
        return self.structural_complete


def _projection_errors(ruleset: str, root: Path | None) -> tuple[int, list[str]]:
    """Compile every in-scope catalogue mechanism and inspect its public output.

    This is deliberately stronger than checking that ``compile_fighter`` does
    not raise.  Every parameter declared by the execution contract must be
    visible in the appropriate compiled EffectSet.
    """
    catalogue = load_mechanics(ruleset, root)
    effects = effect_index(ruleset, root)
    parameters_by_id = {
        str(row["id"]): dict(row.get("parameters") or {})
        for row in load_execution_contract(ruleset, root).get("mechanics") or ()
    }
    excluded = {
        str(row["id"])
        for row in load_runtime_scope(ruleset, root).get("mechanic_exclusions") or ()
    }
    characteristics = Characteristics(3, 3, 3, 1, 3, 1)
    errors: list[str] = []
    projected = 0

    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for row in catalogue.get(family) or ():
            mechanic_id = str(row["id"])
            if mechanic_id in excluded:
                continue
            error_count = len(errors)
            kwargs: dict[str, object]
            if family == "weapons":
                kwargs = ({"main_weapon_id": mechanic_id} if row.get("main_hand")
                          else {"off_hand_id": mechanic_id})
            elif family == "armours":
                kwargs = ({"defence_ids": (mechanic_id,)}
                          if mechanic_id == "armour.cathayan-quilted-silk"
                          else {"armour_id": mechanic_id})
            elif family == "defences":
                kwargs = ({"off_hand_id": mechanic_id}
                          if mechanic_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}
                          else {"defence_ids": (mechanic_id,)})
            elif family == "materials":
                kwargs = {"main_material_id": mechanic_id}
            elif family == "preparations":
                kwargs = {"preparation_ids": (mechanic_id,)}
            elif family == "poisons":
                kwargs = {"main_poison_id": mechanic_id}
            else:
                kwargs = {"skill_ids": (mechanic_id,)}

            try:
                fighter = compile_fighter(FighterBuild(ruleset, characteristics, **kwargs), root)
            except Exception as exc:  # converted into an actionable audit error
                errors.append(f"{mechanic_id}: cannot compile observable projection: {exc}")
                continue

            if family in {"weapons", "materials", "poisons"}:
                actual = fighter.main_weapon if family != "weapons" or row.get("main_hand") else fighter.off_hand
            else:
                actual = fighter.global_effects
            if actual is None:
                errors.append(f"{mechanic_id}: compiled projection is missing")
                continue

            expected = effects[mechanic_id].effect
            for field_name in parameters_by_id[mechanic_id]:
                value = getattr(expected, field_name)
                observed = getattr(actual, field_name)
                if field_name == "tags":
                    matches = set(value) <= set(observed)
                else:
                    matches = observed == value
                if not matches:
                    errors.append(
                        f"{mechanic_id}: {field_name} compiles as {observed!r}, expected {value!r}"
                    )
            if len(errors) == error_count:
                projected += 1
    return projected, errors


def _trait_projection_errors(
    ruleset: str,
    root: Path | None,
    bindings: dict[tuple[str, str], dict[str, object]],
) -> tuple[int, list[str]]:
    """Prove that every canonical trait binding changes compiled state."""
    characteristics = Characteristics(3, 3, 3, 1, 3, 1)
    baseline = compile_fighter(FighterBuild(ruleset, characteristics), root)
    projected = 0
    errors: list[str] = []
    for (kind, binding_id), parameters in sorted(bindings.items()):
        if kind != "trait":
            continue
        trait = binding_id.removeprefix("trait.").replace("-", "_")
        if "value" not in parameters:
            errors.append(f"{binding_id}: trait binding has no value to project")
            continue
        try:
            compiled = compile_fighter(FighterBuild(
                ruleset,
                characteristics,
                trait_overrides={trait: parameters["value"]},
            ), root)
        except Exception as exc:
            errors.append(f"{binding_id}: cannot compile trait projection: {exc}")
            continue
        if compiled == baseline:
            errors.append(f"{binding_id}: trait value is not observable in CompiledFighter")
            continue
        projected += 1
    return projected, errors


def _required_profile_build(collection: str, band_id: str, profile_id: str) -> FighterBuild:
    special_rule_ids = (
        ("band--mutations-tentacle",)
        if band_id in {"cult-of-the-possessed", "trollheim-cult-of-the-possessed"}
        and profile_id in {"mutants", "the-possessed"}
        else ("band--blessings-of-nurgle-bloated-foulness",)
        if band_id == "carnival-of-chaos" and profile_id == "tainted-ones"
        else ()
    )
    return FighterBuild(
        "mordheim",
        band_id=band_id,
        profile_id=profile_id,
        collection=collection,
        special_rule_ids=special_rule_ids,
    )


def _automatic_compiler_projection_errors(
    root: Path | None,
    expected: set[str],
) -> tuple[int, list[str]]:
    """Compile every legal profile and collect automatic construction contracts."""
    observed: set[str] = set()
    errors: list[str] = []
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection, root):
            band_id = str(band.band["id"])
            for profile in band.profiles:
                profile_id = str(profile["id"])
                try:
                    fighter = compile_fighter(
                        _required_profile_build(collection, band_id, profile_id), root
                    )
                except Exception as exc:
                    errors.append(
                        f"{band_id}/{profile_id}: cannot project automatic compiler bindings: {exc}"
                    )
                    continue
                observed.update(fighter.construction_tags)
    missing = expected - observed
    if missing:
        errors.append(f"automatic compiler bindings without compiled projection: {sorted(missing)}")
    return len(expected & observed), errors


@lru_cache(maxsize=None)
def audit_phase_verification(
    ruleset: str = "mordheim", root: Path | None = None, specs_root: Path | None = None
) -> VerificationReport:
    specification = load_phase_verification(ruleset, specs_root)
    execution = tuple(load_execution_contract(ruleset, root).get("mechanics") or ())
    declared_fields = specification.get("operator_fields") or {}
    valid_phases = {phase.value for phase in Phase}
    errors: list[str] = []

    semantic = specification.get("semantic_evidence") or {}
    strategies = semantic.get("binding_strategies") or {}
    expected_strategies = {
        "mechanic": "compiled-effect-and-phase",
        "trait": "compiled-value-and-phase",
        "profile": "construction-result",
        "compiler": "acceptance-and-rejection",
    }
    if strategies != expected_strategies:
        errors.append("semantic_evidence.binding_strategies must define all canonical proof obligations")
    if (semantic.get("mechanism_projection") or {}).get("observable") != "compiled-effect-set":
        errors.append("semantic evidence must require an observable compiled EffectSet projection")

    effect_fields = {field.name for field in fields(EffectSet)}
    if set(MODULAR_FIELD_CONSUMERS) != effect_fields - {"tags"}:
        errors.append(
            "modular field consumer mismatch: "
            f"missing={sorted(effect_fields - {'tags'} - set(MODULAR_FIELD_CONSUMERS))}, "
            f"unknown={sorted(set(MODULAR_FIELD_CONSUMERS) - effect_fields)}"
        )
    missing_fields = effect_fields - set(declared_fields)
    unknown_fields = set(declared_fields) - effect_fields
    if missing_fields:
        errors.append(f"EffectSet fields without phase operator: {sorted(missing_fields)}")
    if unknown_fields:
        errors.append(f"unknown phase operator fields: {sorted(unknown_fields)}")
    for field_name, phases in declared_fields.items():
        if not phases or set(phases) - valid_phases:
            errors.append(f"{field_name}: invalid or empty phase ownership {phases!r}")

    execution_ids: set[str] = set()
    tag_only_contracts: set[str] = set()
    for row in execution:
        mechanic_id = str(row.get("id") or "")
        execution_ids.add(mechanic_id)
        parameters = row.get("parameters") or {}
        uncovered = set(parameters) - set(declared_fields)
        if uncovered:
            errors.append(f"{mechanic_id}: parameters without phase operators {sorted(uncovered)}")
        if set(parameters) == {"tags"}:
            tag_only_contracts.update(str(tag) for tag in parameters["tags"])
    if set(MODULAR_TAG_CONSUMERS) != tag_only_contracts:
        errors.append(
            "modular tag consumer mismatch: "
            f"missing={sorted(tag_only_contracts - set(MODULAR_TAG_CONSUMERS))}, "
            f"unknown={sorted(set(MODULAR_TAG_CONSUMERS) - tag_only_contracts)}"
        )

    records = []
    bindings: set[tuple[str, str]] = set()
    binding_parameters: dict[tuple[str, str], dict[str, object]] = {}
    binding_grants: dict[tuple[str, str], set[str]] = {}
    binding_categories = specification.get("binding_categories") or {}
    if set(binding_categories) != {"mechanic", "trait", "profile", "compiler"}:
        errors.append("binding_categories must classify mechanic, trait, profile and compiler")
    for band in (*load_bands("mordheim", root), *load_bands("trollheim", root)):
        for rule in band.special_rules:
            runtime = rule.get("runtime") or {}
            if runtime.get("scope") != "YES" or runtime.get("implemented") != "YES":
                continue
            records.append(rule)
            rule_bindings = runtime_bindings(rule)
            if not rule_bindings:
                errors.append(f"{band.band['id']}/{rule['id']}: implemented rule has no binding")
            for binding in rule_bindings:
                kind, binding_id = str(binding.get("kind")), str(binding.get("id"))
                bindings.add((kind, binding_id))
                binding_parameters.setdefault((kind, binding_id), dict(binding.get("parameters") or {}))
                binding_grants.setdefault((kind, binding_id), set()).add(str(runtime.get("grant")))
                if kind == "mechanic" and binding_id not in execution_ids:
                    errors.append(f"{rule['id']}: unknown mechanic binding {binding_id}")
                elif kind == "trait" and binding_id.removeprefix("trait.").replace("-", "_") not in TRAIT_TYPES:
                    errors.append(f"{rule['id']}: unknown trait binding {binding_id}")
                elif (
                    kind == "compiler"
                    and binding_id not in COMPILER_CONTRACTS
                    and not binding_id.startswith(("special-rule.", "profile-rule."))
                ):
                    errors.append(f"{rule['id']}: unknown compiler binding {binding_id}")
                elif kind not in {"mechanic", "trait", "profile", "compiler"}:
                    errors.append(f"{rule['id']}: unknown binding kind {kind}")

    complex_rules = specification.get("complex_rules") or {}
    for rule_id, contract in complex_rules.items():
        phases = contract.get("phases") or ()
        if not phases or set(phases) - valid_phases:
            errors.append(f"complex rule {rule_id}: invalid phase sequence {phases!r}")
        if not contract.get("scenario"):
            errors.append(f"complex rule {rule_id}: missing executable scenario")
        if contract.get("engine") != "scalar-reference":
            errors.append(f"complex rule {rule_id}: evidence must target scalar-reference")
    declared_complex_scenarios = {
        str(contract.get("scenario")) for contract in complex_rules.values()
    }
    if declared_complex_scenarios != set(MODULAR_COMPLEX_SCENARIOS):
        errors.append("complex scenario registry does not match scalar reference scenarios")

    interaction_fields = {
        field_name
        for field_name in declared_fields
        if sum(field_name in (row.get("parameters") or {}) for row in execution) > 1
    }
    projected_mechanics, projection_errors = _projection_errors(ruleset, root)
    errors.extend(projection_errors)
    projected_traits, trait_projection_errors = _trait_projection_errors(
        ruleset, root, binding_parameters
    )
    errors.extend(trait_projection_errors)
    profile_bindings = {binding_id for kind, binding_id in bindings if kind == "profile"}
    profile_evidence = semantic.get("profile_bindings") or {}
    if set(profile_evidence) != profile_bindings:
        errors.append(
            "profile semantic evidence mismatch: "
            f"missing={sorted(profile_bindings - set(profile_evidence))}, "
            f"unknown={sorted(set(profile_evidence) - profile_bindings)}"
        )
    for binding_id, evidence in profile_evidence.items():
        if not evidence.get("observable") or not evidence.get("scenario"):
            errors.append(f"{binding_id}: profile evidence needs observable and scenario")
    automatic_compilers = {
        binding_id
        for (kind, binding_id), grants in binding_grants.items()
        if kind == "compiler"
        and binding_id in COMPILER_CONTRACTS
        and bool(grants - {"selectable"})
    }
    projected_compilers, compiler_projection_errors = _automatic_compiler_projection_errors(
        root, automatic_compilers
    )
    errors.extend(compiler_projection_errors)
    selectable_compilers = {
        binding_id
        for (kind, binding_id), grants in binding_grants.items()
        if kind == "compiler"
        and binding_id in COMPILER_CONTRACTS
        and grants == {"selectable"}
    }
    selectable_evidence = semantic.get("selectable_compiler_bindings") or {}
    if set(selectable_evidence) != selectable_compilers:
        errors.append(
            "selectable compiler evidence mismatch: "
            f"missing={sorted(selectable_compilers - set(selectable_evidence))}, "
            f"unknown={sorted(set(selectable_evidence) - selectable_compilers)}"
        )
    if any(not scenario for scenario in selectable_evidence.values()):
        errors.append("every selectable compiler binding needs a semantic scenario")
    special_compilers = {
        binding_id
        for kind, binding_id in bindings
        if kind == "compiler" and binding_id.startswith(("special-rule.", "profile-rule."))
    }
    special_evidence = semantic.get("special_compiler_bindings") or {}
    if set(special_evidence) != special_compilers:
        errors.append(
            "special compiler evidence mismatch: "
            f"missing={sorted(special_compilers - set(special_evidence))}, "
            f"unknown={sorted(set(special_evidence) - special_compilers)}"
        )
    if any(not scenario for scenario in special_evidence.values()):
        errors.append("every special compiler binding needs a compiled observable scenario")
    observable_bindings = {
        (kind, binding_id)
        for kind, binding_id in bindings
        if (
            kind == "mechanic" and binding_id in execution_ids
            or kind == "trait"
            or kind == "profile" and binding_id in profile_evidence
            or kind == "compiler" and binding_id in (
                automatic_compilers | set(selectable_evidence) | set(special_evidence)
            )
        )
    }
    if observable_bindings != bindings:
        errors.append(
            f"canonical bindings without compiled observable: {sorted(bindings - observable_bindings)}"
        )
    return VerificationReport(
        execution_mechanics=len(execution),
        projected_mechanics=projected_mechanics,
        projected_trait_bindings=projected_traits,
        evidenced_profile_bindings=len(profile_evidence),
        projected_automatic_compiler_bindings=projected_compilers,
        evidenced_selectable_compiler_bindings=len(selectable_evidence),
        evidenced_special_compiler_bindings=len(special_evidence),
        observable_canonical_bindings=len(observable_bindings),
        evidenced_complex_sequences=sum(
            bool(contract.get("scenario")) for contract in complex_rules.values()
        ),
        modular_tag_consumers=len(MODULAR_TAG_CONSUMERS),
        modular_operator_fields=len(MODULAR_FIELD_CONSUMERS),
        modular_execution_mechanics=sum(
            all(
                field_name in MODULAR_FIELD_CONSUMERS
                or field_name == "tags" and (
                    len(row.get("parameters") or {}) > 1
                    or all(str(tag) in MODULAR_TAG_CONSUMERS for tag in field_value)
                )
                for field_name, field_value in (row.get("parameters") or {}).items()
            )
            for row in execution
        ),
        implemented_rule_records=len(records),
        canonical_bindings=len(bindings),
        operator_fields=len(declared_fields),
        complex_rules=len(complex_rules),
        interaction_groups=len(interaction_fields),
        errors=tuple(errors),
    )
