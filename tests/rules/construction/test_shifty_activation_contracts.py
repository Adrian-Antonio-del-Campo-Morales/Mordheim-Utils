"""Construction contracts split from ``tests/engines/modular/test_shifty_activation.py``.

The selectable Halfling Shifty skill is admitted through the canonical
``FighterBuild``/``compile_fighter`` route and through the catalogue offer, and it
is refused for every profile that does not print it.  Every check below asserts on
the compiled output, on the catalogue round trip or on the backend gate that
refuses an unported skill, never on a duel round; that is why they belong to the
construction suite.
"""
from functools import lru_cache

import numpy as np
import pytest

from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.native._combat_compile import compile_duel
from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.models import Characteristics, DuelRequest, FighterBuild
from mordheim_knowledge.loader import knowledge_root

BAND = 'halflings-mic'
RULE = 'halfling-elder--shifty'
HEROES = ('halfling-elder', 'halfling-cook', 'halfling-thief', 'halfling-youths')
HENCHMEN = ('halfling-scouts', 'halfling-warriors', 'piggies', 'village-ogre')


def build(profile='halfling-elder', selected=True, **options):
    return FighterBuild('mordheim', band_id=BAND, profile_id=profile,
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'),
        special_rule_ids=options.pop('special_rule_ids', (RULE,) if selected else ()), **options)


@lru_cache
def hero(profile='halfling-elder', selected=True):
    return compile_fighter(build(profile, selected))


@pytest.fixture(scope='module')
def opponent():
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 4, 3, 1),
                                       main_weapon_id='weapon.mace'))


@pytest.mark.phase2_construction
@pytest.mark.parametrize('profile', HEROES)
def test_canonical_heroes_offer_select_compile_once_and_keep_absence_control(profile):
    assert RULE in available_special_rules(build(profile, False), knowledge_root())
    selected, absent = hero(profile), hero(profile, False)
    assert selected.global_effects.tags.count('skill.shifty') == 1
    assert 'skill.shifty' not in absent.global_effects.tags
    assert selected.characteristics == absent.characteristics
    assert selected.main_weapon == absent.main_weapon
    assert 'weapon.mace' in selected.main_weapon.tags
    assert selected.global_effects.attacks_bonus == absent.global_effects.attacks_bonus == 0
    # The bonus is contextual, never a permanent compiled Attack increment.
    assert selected.characteristics.attacks == 1


@pytest.mark.phase2_construction
@pytest.mark.parametrize('profile', HEROES)
def test_catalogue_offer_roundtrips_into_canonical_rule_selection(profile):
    catalogue = CombatCatalogue()
    choice = next(p for p in catalogue.profiles('mordheim', BAND) if p.profile_id == profile)
    skill = next(s for s in catalogue.skills(choice) if s.rule_id == RULE)
    assert skill.runtime_available and skill.unavailable_reason is None
    assert skill.selection_kind == 'warband_skill'
    ordinary, special = catalogue.skill_rule_ids((skill.id,))
    assert ordinary == () and special == (RULE,)
    assert catalogue.skill_ui_ids(choice, ordinary, special) == (skill.id,)
    assert 'skill.shifty' in compile_fighter(build(profile, special_rule_ids=special)).global_effects.tags


@pytest.mark.phase2_construction
@pytest.mark.parametrize('profile', HENCHMEN)
def test_unpromoted_canonical_henchmen_do_not_offer_or_compile_the_skill(profile):
    assert RULE not in available_special_rules(build(profile, False), knowledge_root())
    with pytest.raises(ValueError, match='special rule is not available'):
        compile_fighter(build(profile))
    control = compile_fighter(build(profile, False, main_weapon_id='weapon.fist'))
    assert 'skill.shifty' not in control.global_effects.tags


@pytest.mark.phase2_construction
def test_foreign_profile_cannot_select_halfling_skill():
    with pytest.raises(ValueError, match='special rule is not available'):
        compile_fighter(FighterBuild('mordheim', band_id='mercenaries',
            profile_id='mercenary-captain', special_rule_ids=(RULE,)))


@pytest.mark.phase2_construction
def test_foreign_profile_cannot_bypass_recipients_with_raw_mechanic_id():
    with pytest.raises(ValueError, match='skills are not available'):
        compile_fighter(FighterBuild('mordheim', band_id='mercenaries',
            profile_id='mercenary-captain', skill_ids=('skill.shifty',)))


@pytest.mark.phase2_construction
@pytest.mark.parametrize('second', [False, True])
@pytest.mark.parametrize('backend', ['auto', 'numpy', 'native'])
def test_optimized_entries_explicitly_refuse_the_unported_canonical_skill(second, backend, opponent):
    """The accepted NumPy gate executes Shifty; the native gate still refuses it.

    ``NUMPY_CONNECTED_BEHAVIOURS`` declares the connected NumPy port, while
    ``NATIVE_PENDING`` keeps the whole snapshot. ``auto`` resolves to the
    available native backend and therefore follows the native gate. The Elder
    also carries its innate Leader contract, which the native gate rejects
    before Shifty, so the refusal is asserted generically here.
    """
    pair = (opponent, hero()) if second else (hero(), opponent)
    request = DuelRequest(*pair, simulations=1)
    if backend == 'numpy':
        result = simulate_duel(request, backend=backend)
        assert result.first_wins + result.second_wins + result.unresolved == 1
        return
    with pytest.raises(ValueError, match='modular engine'):
        simulate_duel(request, backend=backend)


@pytest.mark.phase2_construction
def test_low_level_optimized_entries_refuse_without_losing_other_guards(opponent):
    """Native entries refuse Shifty; the connected NumPy entries execute it.

    ``compile_duel_plan``/``compile_duel`` default to the native gate, which
    still rejects the skill. ``simulate_batch``/``simulate_duel_parallel`` run
    the accepted NumPy port, which now applies the same contract instead of
    refusing it.
    """
    cook = hero(profile='halfling-cook')
    for call in (lambda: compile_duel_plan(cook, opponent), lambda: compile_duel(cook, opponent)):
        with pytest.raises(ValueError, match='Shifty.*modular'):
            call()
    assert sum(simulate_batch(cook, opponent, 1, np.random.default_rng(0), 1)) == 1
    parallel = simulate_duel_parallel(DuelRequest(cook, opponent, simulations=1))
    assert parallel.first_wins + parallel.second_wins + parallel.unresolved == 1
    # The Elder now has an innate modular-only Leader contract, independently
    # of selected Shifty. A Cook without either contract remains supported.
    with pytest.raises(ValueError, match='Local modifier.*modular'):
        compile_duel_plan(hero(selected=False), opponent)
    compile_duel_plan(hero(profile='halfling-cook', selected=False), opponent)
