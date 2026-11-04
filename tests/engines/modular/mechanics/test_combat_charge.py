"""Combat Charge's bonuses belong only to the bearer's actual charge phase."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_core.models import DuelContext, EffectSet


class LowDice:
    def roll(self, request):
        return 1


@pytest.mark.parametrize("backend", ["numpy", "native"])
def test_combat_charge_is_admitted_by_optimized_backends(cases, backend):
    from mordheim_combat.kernel import require_optimized_support

    case = cases["scenario/basic"]
    selected = replace(case.first, global_effects=EffectSet(tags=("skill.combat-charge",)))
    require_optimized_support(selected, case.second, backend=backend)
    require_optimized_support(case.first, case.second, backend=backend)


@pytest.mark.parametrize("owner_first", [True, False])
@pytest.mark.parametrize("charging", [True, False])
@pytest.mark.parametrize("weapon_skills", [(3, 3), (2, 1)])
def test_combat_charge_adds_attacks_and_offensive_and_defensive_ws_only_during_charge(
    cases, owner_first, charging, weapon_skills,
):
    base = cases["scenario/basic"].first
    owner_ws, enemy_ws = weapon_skills
    owner = replace(base, global_effects=EffectSet(tags=("skill.combat-charge",)),
                    characteristics=replace(base.characteristics, weapon_skill=owner_ws,
                                            initiative=4, attacks=1))
    enemy = replace(base, global_effects=EffectSet(),
                    characteristics=replace(base.characteristics, weapon_skill=enemy_ws,
                                            initiative=2, attacks=1))
    first, second = (owner, enemy) if owner_first else (enemy, owner)
    owner_label = "first" if owner_first else "second"
    enemy_label = "second" if owner_first else "first"
    charger = owner_label if charging else enemy_label
    dice = LowDice()
    initial = initialize_duel(first, second, dice, context=DuelContext(
        charging=(charger,), active_participant=charger))
    result = resolve_round(first, second, initial, dice)
    # Charge priority determines the attack order; low hit rolls preserve both.
    own_attacks = result.attacks[:2] if charging else result.attacks[1:]
    enemy_attacks = result.attacks[2:] if charging else result.attacks[:1]
    assert len(own_attacks) == (2 if charging else 1)
    assert len(enemy_attacks) == 1
    assert [attack.hit_target for attack in own_attacks] == [
        3 if charging or owner_ws > enemy_ws else 4
    ] * len(own_attacks)
    assert enemy_attacks[0].hit_target == (5 if charging and owner_ws == 2 else 4)
    returned_owner = result.state.first if owner_first else result.state.second
    assert returned_owner.weapon_skill == owner_ws
    assert owner.global_effects.attacks_bonus == 0
    assert owner.characteristics.weapon_skill == owner_ws
    later = resolve_round(first, second, result.state, dice)
    assert len(later.attacks) == 2
    assert sorted(attack.hit_target for attack in later.attacks) == sorted(
        (3 if owner_ws > enemy_ws else 4, 4))


def test_combat_charge_does_not_change_a_plain_fighter_or_a_cancelled_charge(cases):
    base = cases["scenario/basic"].first
    plain = replace(base, global_effects=EffectSet(),
                    characteristics=replace(base.characteristics, initiative=4, attacks=1))
    enemy = replace(plain, characteristics=replace(plain.characteristics, initiative=2))
    dice = LowDice()
    context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(plain, enemy, dice, context=context)
    result = resolve_round(plain, enemy, state, dice)
    assert len(result.attacks) == 2
    assert [attack.hit_target for attack in result.attacks] == [4, 4]
    assert result.state.first.weapon_skill == state.first.weapon_skill

    owner = replace(plain, global_effects=EffectSet(tags=("skill.combat-charge",)),
                    characteristics=replace(plain.characteristics, leadership=0))
    fear = replace(enemy, global_effects=EffectSet(tags=("mechanic.causes-fear",)))
    state = initialize_duel(owner, fear, dice, context=context)
    result = resolve_round(owner, fear, state, dice)
    assert not result.attacks and not result.state.engaged
    assert result.state.first.weapon_skill == state.first.weapon_skill
