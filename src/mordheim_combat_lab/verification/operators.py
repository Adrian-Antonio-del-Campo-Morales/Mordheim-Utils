"""verification.operators: responsibility extracted without altering the rules."""
from __future__ import annotations

from itertools import product
import mordheim_combat.phases as phases
from mordheim_core.dice import ScriptedDice
import mordheim_core.effects as effect_ops
from mordheim_core.models import EffectSet


OPERATOR_CHECKS = ("stack", "best", "once-and-context", "priority-composition", "limits-and-replacement")


def verify_operators() -> tuple[tuple[str, ...], tuple[str, ...]]:
    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def stack():
        for a, b, c in product(range(-2, 3), repeat=3):
            left, middle, right = (EffectSet(strength_bonus=n) for n in (a, b, c))
            require(effect_ops.merge_effects(left, middle).strength_bonus == a + b, "additive magnitude")
            require(effect_ops.merge_effects(left, middle) == effect_ops.merge_effects(middle, left), "commutativity")
            require(effect_ops.merge_effects(effect_ops.merge_effects(left, middle), right).strength_bonus == a + b + c,
                    "associativity")
            require(effect_ops.merge_effects(left, effect_ops.merge_effects(middle, right)).strength_bonus == a + b + c,
                    "right associativity")

    def best():
        for a, b in product(range(2, 8), repeat=2):
            left, right = EffectSet(ward_save=a), EffectSet(ward_save=b)
            require(effect_ops.merge_best_effects(left, right).ward_save == min(a, b), "best save threshold")
            require(effect_ops.merge_effects(left, right).ward_save == min(a, b), "saves cannot add")
        for a, b in product(range(4), repeat=2):
            left, right = EffectSet(attacks_bonus=a), EffectSet(attacks_bonus=b)
            require(effect_ops.merge_best_effects(left, right).attacks_bonus == max(a, b), "best attack bonus")
            require(effect_ops.merge_best_effects(left, left) == left, "best is idempotent")
        for a, b in product((False, True), repeat=2):
            require(effect_ops.merge_effects(EffectSet(parry=a), EffectSet(parry=b)).parry is (a or b),
                    "boolean permissions cannot accumulate")

    def once_and_context():
        for policy, expected in (("once", 1), ("stack", 3), ("best", 1)):
            definition = effect_ops.ExecutionEffect(EffectSet(attacks_bonus=1), "attack", "attack", policy)
            definitions = {"example": definition}
            result = effect_ops.apply_execution_effects(EffectSet(), ("example",) * 3, definitions, "attack", "attack")
            require(result.attacks_bonus == expected, f"{policy} multiplicity")
            require(effect_ops.apply_execution_effects(EffectSet(), ("example",), definitions,
                    "passive", "fighter").attacks_bonus == 0, "effect leaked into another phase")
        # 'Once' is per compilation context, not process-global state.
        definition = effect_ops.ExecutionEffect(EffectSet(attacks_bonus=1), "attack", "attack", "once")
        for _ in range(2):
            require(effect_ops.apply_execution_effects(EffectSet(), ("x", "x"), {"x": definition},
                    "attack", "attack").attacks_bonus == 1, "once leaked across independent builds")

    def priority():
        for a, b in product((-1, 0, 1, 10), repeat=2):
            expected = b if a == 0 else a if b == 0 else max(a, b)
            require(effect_ops.merge_effects(EffectSet(priority=a), EffectSet(priority=b)).priority == expected,
                    "neutral priority erased strike-last or precedence was reversed")

    def limits():
        for roll in range(1, 7):
            result = phases.resolve_hit(phases.HitContext(3, 3, modifier=100), ScriptedDice((roll,)))
            require(result.target == 2 and result.success == (roll >= 2), "natural one / lower hit limit")
            result = phases.resolve_hit(phases.HitContext(3, 3, modifier=-100), ScriptedDice((roll,)))
            require(result.target == 6 and result.success == (roll == 6), "upper hit limit")
        ordinary = phases.resolve_armour(phases.ArmourContext(4, ignore_armour=True), ScriptedDice(()))
        protected = phases.resolve_armour(phases.ArmourContext(4, ignore_armour=True,
            armour_save_floor=6, armour_cannot_be_ignored=True), ScriptedDice((6,)))
        require(not ordinary.eligible and protected.target == 6 and protected.saved, "armour override precedence")
        automatic = phases.resolve_wound(phases.WoundContext(1, 10, automatic=True), ScriptedDice(()))
        require(automatic.success and not automatic.critical, "automatic wound invented a critical")

    passed, errors = [], []
    for name, run in zip(OPERATOR_CHECKS, (stack, best, once_and_context, priority, limits)):
        try:
            run()
        except Exception as error:
            errors.append(f"operator/{name}: {type(error).__name__}: {error}")
        else:
            passed.append(name)
    return tuple(passed), tuple(errors)
