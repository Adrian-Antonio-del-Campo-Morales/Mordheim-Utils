"""Construction and eligibility of local rule variants."""
from dataclasses import replace
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def canonical(band, profile, weapon='weapon.sword', **options):
    return compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile,
        main_weapon_id=weapon, **options))

def dancer(*dances, profile='feast-master', **options):
    return canonical('sea-ghosts-mim', profile, 'weapon.sword',
        special_rule_ids=tuple('band--dance-' + dance for dance in dances), **options)


def test_shadow_dances_require_a_promoted_minstrel():
    with pytest.raises(ValueError, match='not available'):
        dancer('storm-of-blades', profile='minstrels')
    dancer('storm-of-blades', profile='minstrels', variant_ids=('promotion.hero',))

def test_shared_slayer_prohibition_uses_declared_thrown_and_cloak_facts():
    from mordheim_construction.eligibility import call
    from mordheim_knowledge.loader import load_items
    items = {row['id']: row for row in load_items('mordheim')}
    for item_id, forbidden in [('throwing_knives', False), ('javelin', False), ('pistol', True), ('bow', True)]:
        item = items[item_id]
        assert call('tokenForbids', 'non-thrown-ranged', item_id,
                    {'kind': item['kind'], 'tags': item.get('tags', []), 'mechanic_id': None}) is forbidden
    cloak = items['wolf_pelt_cloak']
    assert call('tokenForbids', 'constant-save-cloak', 'wolf_pelt_cloak',
                {'kind': cloak['kind'], 'tags': cloak['tags'], 'mechanic_id': None})

def test_shallya_shared_binding_keeps_ceremonial_dagger_owned_but_not_active():
    from mordheim_construction.combat_packages import combat_packages
    from mordheim_construction.restrictions import _validate_bound_equipment_restrictions
    from mordheim_knowledge.loader import runtime_bindings
    pack = next(p for p in combat_packages('mordheim') if p.band['id'] == 'hirelings.hired-sword.2b')
    profile = next(p for p in pack.profiles if p['id'] == 'hireling.hired-sword.priestess-of-shallya')
    rule = next(r for r in pack.special_rules if r['id'] == profile['id'] + '.rule.strictures')
    bindings = runtime_bindings(rule, 'profile')
    build = FighterBuild('mordheim', band_id=pack.band['id'], profile_id=profile['id'],
        main_weapon_id='weapon.quarter-staff', owned_item_ids=('dagger', 'staff'))
    _validate_bound_equipment_restrictions(build, build.main_weapon_id, bindings, package=pack, profile=profile)
    for invalid in (replace(build, main_weapon_id='weapon.dagger'), replace(build, armour_id='armour.light-armour')):
        with pytest.raises(ValueError):
            _validate_bound_equipment_restrictions(invalid, invalid.main_weapon_id, bindings, package=pack, profile=profile)
