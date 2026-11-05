# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
"""_combat_native — compiled batch combat backend mirroring combat.vectorized.

The NumPy engine in ``mordheim_combat.vectorized`` is the certified runtime
and the implementation reference for this extension.  The modular engine is
the only correctness oracle: statistical and semantic parity certify this
backend against it, never the other way around.

Implementation strategy
-----------------------
Every tag decision made inside the vectorized hot loops depends only on the
two fighters and the weapon used, so ``_combat_compile`` folds each of them
into scalar flags ONCE per duel.  The compiled core below is then pure
arithmetic over C arrays plus the draws of a small generator (PCG32 in
production; an injected scripted source for exact verification).  The state
arrays, round loop and attack pipeline mirror ``vectorized.py`` site by site
so the port can be reviewed side by side against the certified engine.
"""

from libc.stdint cimport int16_t
from libc.stdint cimport int32_t
from libc.stdint cimport int8_t
from libc.stdint cimport uint8_t
from libc.stdint cimport uint32_t
from libc.stdint cimport uint64_t
from libc.stdlib cimport free
from libc.stdlib cimport calloc
from libc.stdlib cimport malloc
from libc.stdlib cimport realloc
from libc.string cimport memcpy
from libc.string cimport memset

import math
import numbers
import operator
import numpy as np




# Combat conditions, matching mordheim_combat.phases.Condition.
cdef enum:
    STANDING = 0
    KNOCKED_DOWN = 1
    STUNNED = 2
    PARALYZED = 3
    OUT = 4


# Effect value layout: index order MUST equal kernel.EFFECT_VALUE_FIELDS.
# ``N_EFFECT_FIELDS`` is compared against that runtime tuple by
# ``vectorized._driver`` before the native backend may be selected; a new
# EffectSet field must therefore be appended here in the same position.
cdef enum Field:
    F_STRENGTH_BONUS = 0
    F_FIRST_ROUND_STRENGTH_BONUS = 1
    F_CHARGE_STRENGTH_BONUS = 2
    F_TOUGHNESS_BONUS = 3
    F_INITIATIVE_BONUS = 4
    F_FIXED_STRENGTH = 5
    F_ARMOUR_PENETRATION = 6
    F_TARGET_ARMOUR_BONUS = 7
    F_HIT_MODIFIER = 8
    F_WOUND_MODIFIER = 9
    F_INJURY_MODIFIER = 10
    F_ATTACKS_BONUS = 11
    F_CHARGE_ATTACKS_BONUS = 12
    F_FIRST_ROUND_CHARGE_ATTACKS_BONUS = 13
    F_CHARGE_WS_BONUS = 14
    F_FIRST_ROUND_ATTACKS_BONUS = 15
    F_INCOMING_STRENGTH_MODIFIER = 16
    F_ARMOUR_STRENGTH_MODIFIER = 17
    F_WEAPON_SKILL_BONUS = 18
    F_CRITICAL_INJURY_BONUS = 19
    F_ENERGY_FOCUS_ATTACKS = 20
    F_INCOMING_ATTACKS_MODIFIER = 21
    F_INCOMING_HIT_MODIFIER = 22
    F_ARMOUR_SAVE_BONUS = 23
    F_WARD_SAVE = 24
    F_PRIORITY = 25
    F_PARRY = 26
    F_CONCUSSION = 27
    F_TWO_HANDED = 28
    F_PAIRED = 29
    F_REROLL_HITS = 30
    F_REROLL_WOUNDS = 31
    F_STRONGMAN = 32
    F_CHARGE_REROLL_HITS = 33
    F_STEP_ASIDE = 34
    F_THICK_SKULL = 35
    F_IGNORE_ARMOUR = 36
    F_AUTOMATIC_HIT = 37
    F_CANNOT_BE_PARRIED = 38
    F_BEAR_HUG = 39
    F_POISON_IMMUNITY = 40
    F_FRENZY = 41
    F_DAMAGE = 42
    F_REGENERATION_SAVE = 43
    F_OUT_OF_ACTION_THRESHOLD = 44
    F_TRUE_GRIT = 45
    F_DAMAGE_DIE_SIDES = 46
    F_MAXIMUM_WOUND_TARGET = 47
    F_ARMOUR_SAVE_FLOOR = 48
    F_ARMOUR_CANNOT_BE_IGNORED = 49
    F_WARD_SAVE_MUNDANE_ONLY = 50
    F_NATURAL_ARMOUR_NEGATED_BY_MAGIC = 51
    F_REGENERATION_BLOCKED_BY_FIRE = 52
    F_REGENERATION_BLOCKED_BY_BLESSED = 53
    F_IGNITION_THRESHOLD = 54
    F_CAUGHT_FIRE_THRESHOLD = 55
    F_IGNORE_ARMOUR_AGAINST_KNOCKED_DOWN = 56
    F_IGNORE_ARMOUR_EXCEPT_SHIELD_AND_SKILLS = 57
    F_CRITICAL_THRESHOLD = 58
    F_ETHEREAL_HIT_SAVE = 59
    F_NATURAL_ARMOUR_NEGATED_BY_FIRE = 60
    F_EFFECT_FIELD_COUNT = 61

N_EFFECT_FIELDS = <int>F_EFFECT_FIELD_COUNT
CONTEXT_VERSION = 1

STATE_COLUMNS = (
    "wounds",
    "condition",
    "initiative_penalty",
    "initiative_floor",
    "frenzy",
    "lucky_charm",
    "crimson_initiative",
    "attack_penalty",
    "entangled",
    "parry_used",
    "parry_remaining",
    "seaguard_used",
    "corruption_used",
    "critical_used",
    "force_of_will_used",
    "force_of_will_active",
    "force_of_will_penalty",
    "disability",
    "mark_of_old_ones_used",
    "luck_used",
    "on_fire",
    "weapon_skill",
    "strength",
    "toughness",
    "initiative",
    "attacks",
    "broken_hands",
    "hampered_main",
    "hampered_off",
    "starting_wounds",
    "initiative_missing",
    "random_rolled",
    "random_modifiers",
    "torture_strength_loss",
    "guiding_dream_result",
    "stupidity_failed",
    "massively_built_lost_turn",
    "netted",
    "fear_hit_sixes",
    "grappled",
    "grappling",
    "backley_strength",
    "backley_initiative",
    "mutation_count",
    "atrophied_arms",
    "atrophied_legs",
    "transformed",
    "equipment_cast_off",
    "hillman_wolf",
    "mutation_tail",
    "projection",
    "drenok_fighting",
    "magic_acorn_used",
    "rememberer_used",
    "rememberer_active",
    "banter_trick_active",
    "dodge_trick_active",
    "trip_trick_active",
    "charm_auto_hit",
    "danse_macabre_controlled",
    "mouth_sewn",
    "giggle_juice_used",
    "trip_trick_used",
    "holy_relic_used",
    "first_failed_used",
    "poetry_first_used",
    "one_roll_reroll_used",
    "ranalds_luck_used",
    "lunatic_result",
    "lunatic_stupidity",
    "shornaal_passed",
    "feral_instinct_failed",
    "charm_blocked",
    "entranced",
    "seduction_controlled",
    "drunken_result",
    "animosity_failed",
    "beauty_passed",
    "charm_attack_blocked",
    "hypnotized",
    "hit_this_phase",
    "attacked_this_phase",
    "attacks_bonus_row",
    "combat_charge_active",
    "injury_bonus_row",
    "rousing_sermon_used",
    "backley_used",
    "addiction_cured",
    "black_hunger_active",
    "djinn_power",
    "last_djinn_power",
    "last_dance",
    "bitten_result",
    "devoted_frenzy",
    "crude_belch_ogre_used",
    "backley_spent",
    "addicted_spent",
    "petru_spent",
    "first_attack_lost",
    "shanty_loss",
    "hit_penalty",
    "poetry_active",
    "impetuous_released",
    "mutation_tail_choice",
    "gauche_parry",
    "deathblow_used",
    "dance_shadows_coil",
    "dance_woven_mist",
    "main_gauche_attacks",
    "shadows_coil_active",
    "woven_mist_active",
    "freed_this_turn",
    "mutation_projection",
    "shifty_projection",
    "shifty_row",
    "gauche_mode",
    "whole_choice",
    "anvil_removed",
    "death_blow_removed",
    "petru_debilitating_spent",
    "petru_strength_spent",
    "petru_resilience_spent",
    "out_threshold_row",
    "follow_me_active",
    "righteous_active",
    "attack_loss_row",
    "hit_penalty_row",
    "crude_belch_used",
    "miss_first_attack",
    "wheelo_first_impact",
    "electrical_available_at",
    "grapple_declared",
    "jolt_declared",
    "death_fighting",
    "pool_loss_row",
    "electrical_forfeit",
)

#: ``CombatState`` fields whose storage the compiled core represents differently:
#: the object-valued mutation inventory lives on the Python ``ProjectionTable``
#: row facts, so a row carries its projection index and its brand count; the
#: Backley penalties are the two numeric columns the oracle stores as pairs.
STATE_COLUMN_ALIASES = {
    "effective_fighter": ("projection",),
    "mutations": ("mutation_count", "projection"),
    "mutation_equipment": ("projection",),
    "mutation_weapon_limbs": ("projection",),
    "mutated_hands": ("projection",),
    "backley_penalties": ("backley_strength", "backley_initiative"),
    # The vectorized driver mirrors its per-round charge masks into
    # ``CombatState.being_charged`` for the hit operators; this engine already
    # hands the defender's charge rows (``def_charges``) to the same
    # resolution, so no stored column backs the mirror.
    "being_charged": (),
}

# Capacity gates (kept in sync with _combat_compile).  Compile-time
# constants: they size the C arrays inside FighterC.
cdef enum:
    MAX_EXTRA_ATTACKS = 8
    MAX_RANDOM_CHARACTERISTICS = 8


# ---------------------------------------------------------------------------
# PCG32 generator
# ---------------------------------------------------------------------------

cdef struct PCG32:
    uint64_t state
    uint64_t inc


cdef inline void pcg32_seed(PCG32* rng, uint64_t seed) noexcept:
    rng.state = 0
    rng.inc = (seed << 1) | 1
    pcg32_next(rng)
    rng.state += seed
    pcg32_next(rng)


cdef inline uint32_t pcg32_next(PCG32* rng) noexcept:
    cdef uint64_t oldstate = rng.state
    rng.state = oldstate * 6364136223846793005ULL + rng.inc
    cdef uint32_t xorshifted = <uint32_t>(((oldstate >> 18) ^ oldstate) >> 27)
    cdef uint32_t rot = <uint32_t>(oldstate >> 59)
    return (xorshifted >> rot) | (xorshifted << ((0 - rot) & 31))


cdef inline uint32_t pcg32_bounded(PCG32* rng, uint32_t bound) noexcept:
    """Lemire's unbiased bounded draw (multiply-high + rejection on the low
    word): removes the 64-bit division that the modulo form needs."""
    cdef uint64_t m
    cdef uint32_t low
    while True:
        m = <uint64_t>pcg32_next(rng) * bound
        low = <uint32_t>m
        if low >= bound:
            return <uint32_t>(m >> 32)


# Scripted verification source (None in production).  A cdef struct cannot
# hold Python objects, so the callback lives at module scope: the batch core
# runs single-threaded and one duel at a time, which keeps this safe.
cdef object _rng_callback = None
cdef bint _batch_running = False


cdef struct Rng:
    PCG32 pcg
    bint use_callback


cdef inline void rng_init(Rng* r, uint64_t seed, object callback) noexcept:
    global _rng_callback
    pcg32_seed(&r.pcg, seed)
    _rng_callback = callback
    r.use_callback = callback is not None


cdef int rng_draw_cb(Rng* r, int low, int high) except -1:
    arr = _rng_callback.integers(low, high + 1, 1)
    if len(arr) != 1 or isinstance(arr[0], (bool, np.bool_)):
        raise ValueError("native RNG callback must return one integer")
    value = operator.index(arr[0])
    if value < low or value > high:
        raise ValueError("native RNG callback integer outside requested bounds")
    return value


cdef int rng_coin(Rng* r) except -1:
    if not r.use_callback:
        return <int>pcg32_bounded(&r.pcg, 2)
    arr = _rng_callback.random(1)
    if (len(arr) != 1 or isinstance(arr[0], (bool, np.bool_))
            or not isinstance(arr[0], numbers.Real)):
        raise ValueError("native RNG callback must return one real number")
    value = float(arr[0])
    if not math.isfinite(value) or value < 0 or value >= 1:
        raise ValueError("native RNG callback random outside [0, 1)")
    return 1 if value < .5 else 0


cdef inline int rng_draw_safe(Rng* r, int low, int high) except -1:
    """Draw helper callable from functions that propagate exceptions."""
    if not r.use_callback:
        return <int>pcg32_bounded(&r.pcg, <uint32_t>(high - low + 1)) + low
    return rng_draw_cb(r, low, high)


# ---------------------------------------------------------------------------
# Compiled data structures (filled once per duel from _combat_compile dicts)
# ---------------------------------------------------------------------------

cdef struct EffectC:
    int v[F_EFFECT_FIELD_COUNT]


cdef struct SourceC:
    EffectC weapon
    EffectC effect
    bint unarmed
    bint knife_fighting
    bint sigmarite
    bint mounted_only
    bint first_round_bonus_always
    bint scorpion_tail_poison
    bint energy_focus_strength
    bint berserker
    bint ferocious
    bint sweep
    bint bellowing
    int hit_mod_base
    bint reroll_base
    bint reroll_charge
    bint reroll_charge_fr
    bint reroll_fr_all
    bint reroll_all
    bint luck
    bint virtue
    bint auto_wound_six
    bint automatic_wound_tag
    bint monster_slayer
    bint monster_slayer_eff
    bint rapier
    bint manbane
    bint hardy
    bint magical
    bint no_critical
    bint critical_on_reroll
    bint no_saves
    bint non_melee
    bint kusara
    bint chained
    bint anvil
    bint counter_cutlass
    bint flammable_double
    bint nightshade
    bint disease_dagger
    bint luck_wound
    bint spider_spittle
    bint web_of_steel
    bint poisonous_injury
    bint head_crusher
    bint fire
    bint horned_one
    int fixed_hit_target
    bint guiding_dream_target
    bint shallya_aura
    bint shallya_self
    bint shallya_foe
    int strength_fr_bonus
    bint seaguard_reroll
    bint trap_blade
    bint trap_main
    int strength_charge_fr_bonus
    int strength_fire_bonus
    bint wolf_rat_bite
    int armour_penetration_extra
    bint daemonic_flesh_negated
    bint critical_when_needing_six
    bint hellblade
    bint reroll_wounds_extra
    bint parry_roll_under
    bint parry_max_roll
    int hit_mod_charge_fr
    bint honorable
    bint magic_acorn
    bint marks_of_ranald
    bint corruption
    bint titanic_strength
    bint marine_hunter
    bint achilles_stampede
    bint lycanthrope
    bint torturer
    bint great_thirster
    bint first_of_pool
    bint wraith_heal
    bint killing_blow
    bint spectral_touch
    bint lotus
    bint wight_blades
    bint magical_attack
    bint shock
    bint skull_busta
    bint needle_and_thread
    bint artefact_chart
    bint blessing_of_morr
    bint knife_fighting_injury
    #: ``modular/contexts.py::_hit_reroll`` folded over the three facts that
    #: vary inside the duel: index = 4*first_round + 2*charging + frenzy.
    int reroll_table[16]
    int critical_threshold
    int ignition
    int ward
    int regeneration
    int damage


cdef struct FighterC:
    int ws, s, t, w, ini, a
    int movement, leadership
    bint has_movement, has_leadership
    int armour_save
    int natural_armour_save
    int natural_armour_worst_save
    int helmet_save
    int injury_profile
    int ballistic_skill
    bint off_hand_attacks
    bint mounted
    int parry_capacity
    # defender-side flags
    bint natural_armour_unmodified
    bint natural_armour_negated_by_magic
    bint armour_cannot_be_ignored
    int armour_save_floor
    int shield_skill_armour_save
    bint norse_bulwark
    bint eshin_robes
    bint armour_specialist
    int out_of_action_threshold
    bint poison_immune
    bint luck
    bint infection_immune
    int incoming_strength_modifier
    int incoming_attacks_modifier
    bint revenant
    bint herb_lore
    bint herb_lore_outside
    bint rousing_sermon
    bint alchemist_backley
    bint alchemist_addicted
    bint alchemist_vigortia
    bint confound_and_confuse
    bint djinns_curse
    bint solkan_inquisitor
    bint djinn_ethereal
    int dances
    bint main_gauche_modes
    bint rememberer
    bint rememberer_large_or_tough
    bint rememberer_target_large
    bint thin_flesh
    bint lycanthrope_self
    bint frantic
    bint sabretusk_charge
    bint lunatics
    bint centigor_drunken
    bint animosity
    bint animosity_wide
    bint feral_instinct
    bint bitten_transform
    bint devoted_to_vampire
    bint devoted_vampire_killed
    bint devoted_vampire_down
    bint petru_debilitating
    bint petru_strength
    bint petru_resilience
    bint follow_me
    bint death_fighting
    bint righteous_charge
    bint sea_shanty
    bint sea_shanty_psychology
    bint shanty_excluded
    bint shanty_psych_excluded
    bint crude_belch_ogre
    bint crude_belch_halfling
    bint gaoler_grapple
    bint ravening_onslaught
    bint mantle_of_crows
    bint electrical_touch
    bint giggle_juice_spray
    bint slayer_deathblow
    bint wheelo_morning_star
    bint wheelo_axe
    bint wheelo_club
    bint wheelo_spear
    bint noblesse_stomp
    bint thick_skull
    bint injury_reroll_out
    int ethereal_hit_save
    bint ethereal
    bint natural_armour_negated_by_fire
    bint bat_injury_chart
    bint fen_hard_to_kill
    bint hard_to_rattle
    bint inured_to_pain
    bint undead_construct
    bint veskit_no_pain
    bint marianna_jump_up
    bint hard_to_kill
    bint true_grit
    bint concussion_immune
    bint fragile
    bint survivor
    bint ignore_pain
    bint jump_up
    bint mandrake
    bint acid_blood
    bint contagious
    bint flammable
    bint spider_infested
    # attacker-side abilities (each vs the duel opponent)
    bint bull_charge
    bint body_slam
    bint bear_hug
    bint spawn
    bint netter
    bint spines
    bint black_hunger
    bint combat_charge
    bint force_of_will
    bint entangle
    bint can_burn
    bint serpent_whip
    bint boar_spear
    bint sigmar_effective
    bint animal_friendship_effective
    bint undead_or_possessed
    bint ferocious_charge
    bint mark
    bint blessed
    bint amazon
    bint spiritual_weapons
    bint strike_skinks_always
    bint strike_skinks_first
    bint lightning_reflexes
    bint always_strikes_first
    bint strongman
    bint long_boat_hook
    bint trident
    bint spear
    bint opponent_always_first
    # attack-count scalars
    int attacks_bonus_total
    int extra_weapon_attack
    bint fist_penalized
    bint unarmed_bonus
    bint art_bonus
    bint inspiring
    int first_round_attacks_bonus
    bint frenzy_effect
    bint vomit
    bint sweep_main
    bint main_pistol
    bint off_pistol
    int charge_attacks_bonus
    int first_round_charge_attacks_bonus
    bint body_bull_anvil
    bint death_blow
    bint energy_focus_active
    int energy_focus_attacks
    bint maddened
    # priority scalars
    int weapon_priority
    int priority_global
    int initiative_bonus_total
    # initialize scalars
    int base_wounds
    int toughness_bonus
    bint frenzy_init
    bint lucky_charm_init
    bint crimson_shade
    bint disability
    # state initialisation facts (port of modular.state.initialize_fighter)
    int starting_wounds
    bint initiative_missing
    bint inconsistency
    int condition_deltas[9][3]
    int condition_delta_count
    bint poetry_inspired
    int supplied_disability
    bint guiding_dream
    bint guiding_dream_nominated
    bint netted_init
    bint persistent_frenzy
    bint frenzy_permitted
    bint stupidity_failed_init
    bint massively_built_init
    bint danse_macabre_init
    bint hillman_wolf_init
    bint can_charge
    # Psychology and Leadership facts (port of modular/psychology.py,
    # modular/leadership.py and the charm block of modular/rounds.py)
    bint psychology_immunity
    bint fear_immunity
    bint fear_immunity_undead_chargers
    bint undead_foes_no_fear
    bint automatic_leadership
    bint holy_relic
    bint sigmar_enlightened
    bint squig_recipient
    bint handler_leadership
    bint has_stupidity_leadership
    int stupidity_leadership
    int stupidity_leadership_bonus
    bint own_leadership
    bint broken_spirit
    bint devoted
    bint slave
    bint halfling
    bint poetry_victorious_leader
    bint mob_leadership
    int mob_allies
    bint enchanting_beauty
    bint questing_vow_reroll
    bint opponent_ghostly_howl
    bint cold_blooded_leadership
    bint cold_blooded_psychology
    bint first_failed_leadership_reroll
    bint mandatory_leadership_reroll
    bint leadership_reroll
    bint raise_our_insignia
    bint fear_reroll
    bint ranalds_luck
    bint one_roll_reroll
    bint scryer
    bint stupidity
    bint stupidity_exempt
    bint impetuous_charge
    bint disability_hero_nearby
    bint skaven_group
    int printed_skaven_bits
    bint bear_handler_recipient
    bint bear_handler_nearby
    bint causes_fear
    bint fears_foe_fire
    bint morrs_special
    bint ere_we_go
    bint accustomed_to_fear
    bint craven
    bint wheelo_impact
    int charge_gate
    bint beauty_target
    bint dance_target
    bint pendant_target
    bint shornaal_target
    bint hypnotist_target
    bint foe_hypnotist
    int fauna_mode
    bint has_animal_handler_leadership
    int animal_handler_leadership
    bint deceive_target
    bint hypnotize_target
    bint male
    bint foe_controls[3]
    bint control_excluded[3]
    # parry flags (defender role)
    bint parry_parry
    bint parry_match_allowed
    bint parry_starblade
    bint parry_can_parry_six
    bint parry_dwarf_axes
    bint parry_parry_reroll
    # attack sources (weapon + merged effect per attack type)
    SourceC main
    SourceC unarmed
    SourceC unpredictable
    SourceC off
    bint has_unpredictable
    bint off_present
    SourceC extras[MAX_EXTRA_ATTACKS]
    int extra_count
    SourceC last_bite[MAX_EXTRA_ATTACKS]
    int last_bite_count
    # random characteristics: rows of (stat_index, dice, sides, bonus)
    int random_characteristics[MAX_RANDOM_CHARACTERISTICS][4]
    int random_characteristics_count


# One fighter's compiled view against its foe: the fighter scalars plus
# every reaction attack it can deliver.  Entry zero of a side's table is the
# printed fighter; later entries are per-row projections (``compile_side``).
cdef struct SideC:
    FighterC f
    SourceC bull
    SourceC body
    SourceC spines
    SourceC backlash
    SourceC fire
    SourceC entangle
    SourceC hug
    SourceC acid
    SourceC counter
    SourceC infection
    SourceC crows
    SourceC stomp
    SourceC giggle
    SourceC jolt
    SourceC impact
    SourceC impact_more


# The pair of compiled sides one row group is simulated with.  A view,
# never an owner: both pointers address entries of ``TablesC``.
cdef struct DuelC:
    SideC* first
    SideC* second


# Growable per-side projection tables (``sides[0]`` first, ``sides[1]``
# second).  Entries are heap-allocated so the pointers held by views stay
# valid when a table grows.
cdef struct TablesC:
    SideC** sides[2]
    int n[2]
    int cap[2]


# A supplied local participant folded for the Leadership and Psychology
# consumers (``modular/leadership.py``, ``modular/psychology.py``).
cdef struct ParticipantC:
    int side
    int condition
    int leadership
    int movement
    bint has_leadership
    bint has_movement
    uint64_t bands
    bint leader_six
    bint leader_twelve
    bint leader_four
    bint dim_witted_leader
    bint leader_fallback
    bint relay_orders
    bint songster
    bint slave_driver
    bint scourge
    bint bear_handler
    bint handler_leadership
    bint mouth_sewn
    bint hero
    bint skaven
    bint squig_herder
    bint squig_prodder
    bint undivided_leader
    bint wizened_halfling
    bint halfling
    bint undead
    bint vampire
    bint necromancer
    int printed_skaven_bits


# ``PreparedDuelContext`` as index-addressed scalars.  Participants 0 and
# 1 are the duelists; ``distances`` is an ``n x n`` matrix with ``-1`` for a
# pair the caller did not measure.
cdef struct ContextC:
    bint present
    int n
    ParticipantC* participants
    double* distances
    bint explicit_charging
    bint first_charges
    bint second_charges
    bint has_active
    bint active_first
    bint has_contacts
    bint duelists_in_contact


# ``rows`` partitioned into runs that share one (first, second)
# projection pair; rows stay ascending inside each run.
cdef struct GroupsC:
    int n_groups
    int* starts
    int* p1
    int* p2
    int* rows


cdef struct StateC:
    int n
    int16_t* wounds
    int8_t* condition
    int8_t* initiative_penalty
    int8_t* initiative_floor
    int8_t* frenzy
    int8_t* lucky_charm
    int8_t* crimson_initiative
    int8_t* attack_penalty
    int8_t* entangled
    int8_t* parry_used
    int8_t* parry_remaining
    int8_t* seaguard_used
    int8_t* corruption_used
    int8_t* critical_used
    int8_t* force_of_will_used
    int8_t* force_of_will_active
    int8_t* force_of_will_penalty
    int8_t* disability
    int8_t* mark_of_old_ones_used
    int8_t* luck_used
    int8_t* on_fire
    int16_t* weapon_skill
    int16_t* strength
    int16_t* toughness
    int16_t* initiative
    int16_t* attacks
    uint8_t* broken_hands
    int16_t* hampered_main
    int16_t* hampered_off
    int16_t* starting_wounds
    int8_t* initiative_missing
    uint8_t* random_rolled
    int16_t* random_modifiers
    int8_t* torture_strength_loss
    int8_t* guiding_dream_result
    int8_t* stupidity_failed
    int8_t* massively_built_lost_turn
    int8_t* netted
    int8_t* fear_hit_sixes
    int8_t* grappled
    int8_t* grappling
    int8_t* backley_strength
    int8_t* backley_initiative
    int8_t* mutation_count
    int8_t* atrophied_arms
    int8_t* atrophied_legs
    int8_t* transformed
    int8_t* equipment_cast_off
    int8_t* hillman_wolf
    int8_t* mutation_tail
    int32_t* projection
    int8_t* drenok_fighting
    int8_t* magic_acorn_used
    int8_t* rememberer_used
    int8_t* rememberer_active
    int8_t* banter_trick_active
    int8_t* dodge_trick_active
    int8_t* trip_trick_active
    int8_t* charm_auto_hit
    int8_t* danse_macabre_controlled
    int8_t* mouth_sewn
    int8_t* giggle_juice_used
    int8_t* trip_trick_used
    int8_t* holy_relic_used
    int8_t* first_failed_used
    int8_t* poetry_first_used
    int8_t* one_roll_reroll_used
    int8_t* ranalds_luck_used
    int8_t* lunatic_result
    int8_t* lunatic_stupidity
    int8_t* shornaal_passed
    int8_t* feral_instinct_failed
    int8_t* charm_blocked
    int8_t* entranced
    int8_t* seduction_controlled
    int8_t* drunken_result
    int8_t* animosity_failed
    int8_t* beauty_passed
    int8_t* charm_attack_blocked
    int8_t* hypnotized
    int8_t* hit_this_phase
    int8_t* attacked_this_phase
    int8_t* attacks_bonus_row
    int8_t* combat_charge_active
    int8_t* injury_bonus_row
    int8_t* rousing_sermon_used
    int8_t* backley_used
    int8_t* addiction_cured
    int8_t* black_hunger_active
    int8_t* djinn_power
    int8_t* last_djinn_power
    int8_t* last_dance
    int8_t* bitten_result
    int8_t* devoted_frenzy
    int8_t* crude_belch_ogre_used
    int8_t* backley_spent
    int8_t* addicted_spent
    int8_t* petru_spent
    int8_t* first_attack_lost
    int8_t* shanty_loss
    int8_t* hit_penalty
    int8_t* poetry_active
    int8_t* impetuous_released
    int8_t* mutation_tail_choice
    int8_t* gauche_parry
    int8_t* deathblow_used
    int8_t* dance_shadows_coil
    int8_t* dance_woven_mist
    int8_t* main_gauche_attacks
    int8_t* shadows_coil_active
    int8_t* woven_mist_active
    int8_t* freed_this_turn
    int32_t* mutation_projection
    int32_t* shifty_projection
    int8_t* shifty_row
    int8_t* gauche_mode
    int8_t* whole_choice
    int8_t* anvil_removed
    int8_t* death_blow_removed
    int8_t* petru_debilitating_spent
    int8_t* petru_strength_spent
    int8_t* petru_resilience_spent
    int8_t* out_threshold_row
    int8_t* follow_me_active
    int8_t* righteous_active
    int8_t* attack_loss_row
    int8_t* hit_penalty_row
    int8_t* crude_belch_used
    int8_t* miss_first_attack
    int8_t* wheelo_first_impact
    int16_t* electrical_available_at
    int8_t* grapple_declared
    int8_t* jolt_declared
    int8_t* death_fighting
    int8_t* pool_loss_row
    int8_t* electrical_forfeit


cdef struct PreparedC:
    SourceC src
    int active_n
    int* active
    int16_t* strength
    int16_t* armour_strength
    int8_t* hit_target
    int8_t* rolls
    int hit_n
    int* hit_rows
    int* hit_positions


# ---------------------------------------------------------------------------
# Conversion helpers (dicts produced by mordheim_combat._combat_compile)
# ---------------------------------------------------------------------------

cdef int _flag(object d, str key) noexcept:
    return 1 if d.get(key) else 0


cdef int _int(object d, str key) noexcept:
    return <int>d[key]


cdef void fill_effect(object values, EffectC* out) except *:
    cdef int i
    if len(values) != N_EFFECT_FIELDS:
        raise ValueError("native combat effect layout mismatch; rebuild the native backend")
    for i in range(N_EFFECT_FIELDS):
        out.v[i] = <int>values[i]


cdef void fill_source(object d, SourceC* out) except *:
    fill_effect(d["weapon"], &out.weapon)
    fill_effect(d["effect"], &out.effect)
    cdef object f = d["flags"]
    out.unarmed = _flag(f, "unarmed")
    out.knife_fighting = _flag(f, "knife_fighting")
    out.sigmarite = _flag(f, "sigmarite")
    out.mounted_only = _flag(f, "mounted_only")
    out.first_round_bonus_always = _flag(f, "first_round_bonus_always")
    out.scorpion_tail_poison = _flag(f, "scorpion_tail_poison")
    out.energy_focus_strength = _flag(f, "energy_focus_strength")
    out.berserker = _flag(f, "berserker")
    out.ferocious = _flag(f, "ferocious")
    out.sweep = _flag(f, "sweep")
    out.bellowing = _flag(f, "bellowing")
    out.hit_mod_base = _int(f, "hit_mod_base")
    out.reroll_base = _flag(f, "reroll_base")
    out.reroll_charge = _flag(f, "reroll_charge")
    out.reroll_charge_fr = _flag(f, "reroll_charge_fr")
    out.reroll_fr_all = _flag(f, "reroll_fr_all")
    out.reroll_all = _flag(f, "reroll_all")
    out.luck = _flag(f, "luck")
    out.virtue = _flag(f, "virtue")
    out.auto_wound_six = _flag(f, "auto_wound_six")
    out.automatic_wound_tag = _flag(f, "automatic_wound_tag")
    out.monster_slayer = _flag(f, "monster_slayer")
    out.monster_slayer_eff = _flag(f, "monster_slayer_eff")
    out.rapier = _flag(f, "rapier")
    out.manbane = _flag(f, "manbane")
    out.hardy = _flag(f, "hardy")
    out.magical = _flag(f, "magical")
    out.no_critical = _flag(f, "no_critical")
    out.critical_on_reroll = 1 if f.get("critical_on_reroll", True) else 0
    out.no_saves = _flag(f, "no_saves")
    out.non_melee = _flag(f, "non_melee")
    out.kusara = _flag(f, "kusara")
    out.chained = _flag(f, "chained")
    out.anvil = _flag(f, "anvil")
    out.counter_cutlass = _flag(f, "counter_cutlass")
    out.flammable_double = _flag(f, "flammable_double")
    out.nightshade = _flag(f, "nightshade")
    out.disease_dagger = _flag(f, "disease_dagger")
    out.luck_wound = _flag(f, "luck_wound")
    out.spider_spittle = _flag(f, "spider_spittle")
    out.web_of_steel = _flag(f, "web_of_steel")
    out.poisonous_injury = _flag(f, "poisonous_injury")
    out.head_crusher = _flag(f, "head_crusher")
    out.fire = _flag(f, "fire")
    out.horned_one = _flag(f, "horned_one")
    out.fixed_hit_target = <int>f.get("fixed_hit_target", 0)
    out.guiding_dream_target = _flag(f, "guiding_dream_target")
    out.shallya_aura = _flag(f, "shallya_aura")
    out.shallya_self = _flag(f, "shallya_self")
    out.shallya_foe = _flag(f, "shallya_foe")
    out.strength_fr_bonus = <int>f.get("strength_fr_bonus", 0)
    out.seaguard_reroll = _flag(f, "seaguard_reroll")
    out.trap_blade = _flag(f, "trap_blade")
    out.trap_main = _flag(f, "trap_main")
    out.strength_charge_fr_bonus = <int>f.get("strength_charge_fr_bonus", 0)
    out.strength_fire_bonus = <int>f.get("strength_fire_bonus", 0)
    out.wolf_rat_bite = _flag(f, "wolf_rat_bite")
    out.armour_penetration_extra = <int>f.get("armour_penetration_extra", 0)
    out.daemonic_flesh_negated = _flag(f, "daemonic_flesh_negated")
    out.critical_when_needing_six = _flag(f, "critical_when_needing_six")
    out.hellblade = _flag(f, "hellblade")
    out.reroll_wounds_extra = _flag(f, "reroll_wounds_extra")
    out.parry_roll_under = _flag(f, "parry_roll_under")
    out.parry_max_roll = _flag(f, "parry_max_roll")
    out.hit_mod_charge_fr = <int>f.get("hit_mod_charge_fr", 0)
    out.honorable = _flag(f, "honorable")
    out.magic_acorn = _flag(f, "magic_acorn")
    out.marks_of_ranald = _flag(f, "marks_of_ranald")
    out.corruption = _flag(f, "corruption")
    out.titanic_strength = _flag(f, "titanic_strength")
    out.marine_hunter = _flag(f, "marine_hunter")
    out.achilles_stampede = _flag(f, "achilles_stampede")
    out.lycanthrope = _flag(f, "lycanthrope")
    out.torturer = _flag(f, "torturer")
    out.great_thirster = _flag(f, "great_thirster")
    out.wraith_heal = _flag(f, "wraith_heal")
    out.killing_blow = _flag(f, "killing_blow")
    out.spectral_touch = _flag(f, "spectral_touch")
    out.lotus = _flag(f, "lotus")
    out.wight_blades = _flag(f, "wight_blades")
    out.magical_attack = _flag(f, "magical_attack")
    out.shock = _flag(f, "shock")
    out.skull_busta = _flag(f, "skull_busta")
    out.needle_and_thread = _flag(f, "needle_and_thread")
    out.artefact_chart = _flag(f, "artefact_chart")
    out.blessing_of_morr = _flag(f, "blessing_of_morr")
    out.knife_fighting_injury = _flag(f, "knife_fighting_injury")
    cdef object table = d.get("reroll_table") or [0] * 16
    cdef int ri
    for ri in range(16):
        out.reroll_table[ri] = <int>table[ri]
    out.critical_threshold = <int>d["critical_threshold"]
    out.ignition = <int>d["ignition"]
    out.ward = <int>d["ward"]
    out.regeneration = <int>d["regeneration"]
    out.damage = <int>d["damage"]


cdef void fill_fighter(object d, FighterC* out, object sources, object reactions,
                       SourceC* bull, SourceC* body, SourceC* spines, SourceC* backlash,
                       SourceC* fire, SourceC* entangle, SourceC* hug, SourceC* acid,
                       SourceC* counter, SourceC* infection) except *:
    out.ws = _int(d, "ws")
    out.s = _int(d, "s")
    out.t = _int(d, "t")
    out.w = _int(d, "w")
    out.ini = _int(d, "ini")
    out.a = _int(d, "a")
    out.has_movement = d["movement"] is not None
    out.has_leadership = d["leadership"] is not None
    out.movement = <int>d["movement"] if out.has_movement else 0
    out.leadership = <int>d["leadership"] if out.has_leadership else 0
    out.armour_save = _int(d, "armour_save")
    out.natural_armour_save = _int(d, "natural_armour_save")
    out.natural_armour_worst_save = _int(d, "natural_armour_worst_save")
    out.helmet_save = _int(d, "helmet_save")
    out.injury_profile = _int(d, "injury_profile")
    out.ballistic_skill = _int(d, "ballistic_skill")
    out.off_hand_attacks = 1 if d.get("off_hand_attacks") else 0
    out.mounted = 1 if d.get("mounted") else 0
    out.parry_capacity = _int(d, "parry_capacity")
    out.natural_armour_unmodified = _flag(d, "natural_armour_unmodified")
    out.natural_armour_negated_by_magic = _flag(d, "natural_armour_negated_by_magic")
    out.armour_cannot_be_ignored = _flag(d, "armour_cannot_be_ignored")
    out.armour_save_floor = _int(d, "armour_save_floor")
    out.shield_skill_armour_save = <int>d.get("shield_skill_armour_save", 7)
    out.norse_bulwark = _flag(d, "norse_bulwark")
    out.eshin_robes = _flag(d, "eshin_robes")
    out.armour_specialist = _flag(d, "armour_specialist")
    out.out_of_action_threshold = _int(d, "out_of_action_threshold")
    out.poison_immune = _flag(d, "poison_immune")
    out.luck = _flag(d, "luck")
    out.infection_immune = _flag(d, "infection_immune")
    out.incoming_strength_modifier = _int(d, "incoming_strength_modifier")
    out.incoming_attacks_modifier = _int(d, "incoming_attacks_modifier")
    out.revenant = _flag(d, "revenant")
    out.herb_lore = _flag(d, "herb_lore")
    out.herb_lore_outside = _flag(d, "herb_lore_outside")
    out.rousing_sermon = _flag(d, "rousing_sermon")
    out.alchemist_backley = _flag(d, "alchemist_backley")
    out.alchemist_addicted = _flag(d, "alchemist_addicted")
    out.alchemist_vigortia = _flag(d, "alchemist_vigortia")
    out.confound_and_confuse = _flag(d, "confound_and_confuse")
    out.djinns_curse = _flag(d, "djinns_curse")
    out.solkan_inquisitor = _flag(d, "solkan_inquisitor")
    out.djinn_ethereal = _flag(d, "djinn_ethereal")
    out.dances = <int>d.get("dances", 0)
    out.main_gauche_modes = _flag(d, "main_gauche_modes")
    out.rememberer = _flag(d, "rememberer")
    out.rememberer_large_or_tough = _flag(d, "rememberer_large_or_tough")
    out.rememberer_target_large = _flag(d, "rememberer_target_large")
    out.thin_flesh = _flag(d, "thin_flesh")
    out.lycanthrope_self = _flag(d, "lycanthrope_self")
    out.frantic = _flag(d, "frantic")
    out.sabretusk_charge = _flag(d, "sabretusk_charge")
    out.lunatics = _flag(d, "lunatics")
    out.centigor_drunken = _flag(d, "centigor_drunken")
    out.animosity = _flag(d, "animosity")
    out.animosity_wide = _flag(d, "animosity_wide")
    out.feral_instinct = _flag(d, "feral_instinct")
    out.bitten_transform = _flag(d, "bitten_transform")
    out.devoted_to_vampire = _flag(d, "devoted_to_vampire")
    out.devoted_vampire_killed = _flag(d, "devoted_vampire_killed")
    out.devoted_vampire_down = _flag(d, "devoted_vampire_down")
    out.petru_debilitating = _flag(d, "petru_debilitating")
    out.petru_strength = _flag(d, "petru_strength")
    out.petru_resilience = _flag(d, "petru_resilience")
    out.follow_me = _flag(d, "follow_me")
    out.death_fighting = _flag(d, "death_fighting")
    out.righteous_charge = _flag(d, "righteous_charge")
    out.sea_shanty = _flag(d, "sea_shanty")
    out.sea_shanty_psychology = _flag(d, "sea_shanty_psychology")
    out.shanty_excluded = _flag(d, "shanty_excluded")
    out.shanty_psych_excluded = _flag(d, "shanty_psych_excluded")
    out.crude_belch_ogre = _flag(d, "crude_belch_ogre")
    out.crude_belch_halfling = _flag(d, "crude_belch_halfling")
    out.gaoler_grapple = _flag(d, "gaoler_grapple")
    out.ravening_onslaught = _flag(d, "ravening_onslaught")
    out.mantle_of_crows = _flag(d, "mantle_of_crows")
    out.electrical_touch = _flag(d, "electrical_touch")
    out.giggle_juice_spray = _flag(d, "giggle_juice_spray")
    out.slayer_deathblow = _flag(d, "slayer_deathblow")
    out.wheelo_morning_star = _flag(d, "wheelo_morning_star")
    out.wheelo_axe = _flag(d, "wheelo_axe")
    out.wheelo_club = _flag(d, "wheelo_club")
    out.wheelo_spear = _flag(d, "wheelo_spear")
    out.noblesse_stomp = _flag(d, "noblesse_stomp")
    out.thick_skull = _flag(d, "thick_skull")
    out.injury_reroll_out = _flag(d, "injury_reroll_out")
    out.ethereal_hit_save = <int>d.get("ethereal_hit_save", 4)
    out.ethereal = _flag(d, "ethereal")
    out.natural_armour_negated_by_fire = _flag(d, "natural_armour_negated_by_fire")
    out.bat_injury_chart = _flag(d, "bat_injury_chart")
    out.fen_hard_to_kill = _flag(d, "fen_hard_to_kill")
    out.hard_to_rattle = _flag(d, "hard_to_rattle")
    out.inured_to_pain = _flag(d, "inured_to_pain")
    out.undead_construct = _flag(d, "undead_construct")
    out.veskit_no_pain = _flag(d, "veskit_no_pain")
    out.marianna_jump_up = _flag(d, "marianna_jump_up")
    out.hard_to_kill = _flag(d, "hard_to_kill")
    out.true_grit = _flag(d, "true_grit")
    out.concussion_immune = _flag(d, "concussion_immune")
    out.fragile = _flag(d, "fragile")
    out.survivor = _flag(d, "survivor")
    out.ignore_pain = _flag(d, "ignore_pain")
    out.jump_up = _flag(d, "jump_up")
    out.mandrake = _flag(d, "mandrake")
    out.acid_blood = _flag(d, "acid_blood")
    out.contagious = _flag(d, "contagious")
    out.flammable = _flag(d, "flammable")
    out.spider_infested = _flag(d, "spider_infested")
    out.bull_charge = _flag(d, "bull_charge")
    out.body_slam = _flag(d, "body_slam")
    out.bear_hug = _flag(d, "bear_hug")
    out.spawn = _flag(d, "spawn")
    out.netter = _flag(d, "netter")
    out.spines = _flag(d, "spines")
    out.black_hunger = _flag(d, "black_hunger")
    out.combat_charge = _flag(d, "combat_charge")
    out.force_of_will = _flag(d, "force_of_will")
    out.entangle = _flag(d, "entangle")
    out.can_burn = _flag(d, "can_burn")
    out.serpent_whip = _flag(d, "serpent_whip")
    out.boar_spear = _flag(d, "boar_spear")
    out.sigmar_effective = _flag(d, "sigmar_effective")
    out.animal_friendship_effective = _flag(d, "animal_friendship_effective")
    out.undead_or_possessed = _flag(d, "undead_or_possessed")
    out.ferocious_charge = _flag(d, "ferocious_charge")
    out.mark = _flag(d, "mark")
    out.blessed = _flag(d, "blessed")
    out.amazon = _flag(d, "amazon")
    out.spiritual_weapons = _flag(d, "spiritual_weapons")
    out.strike_skinks_always = _flag(d, "strike_skinks_always")
    out.strike_skinks_first = _flag(d, "strike_skinks_first")
    out.lightning_reflexes = _flag(d, "lightning_reflexes")
    out.always_strikes_first = _flag(d, "always_strikes_first")
    out.strongman = _flag(d, "strongman")
    out.long_boat_hook = _flag(d, "long_boat_hook")
    out.trident = _flag(d, "trident")
    out.spear = _flag(d, "spear")
    out.opponent_always_first = _flag(d, "opponent_always_first")
    out.attacks_bonus_total = _int(d, "attacks_bonus_total")
    out.extra_weapon_attack = _int(d, "extra_weapon_attack")
    out.fist_penalized = _flag(d, "fist_penalized")
    out.unarmed_bonus = _flag(d, "unarmed_bonus")
    out.art_bonus = _flag(d, "art_bonus")
    out.inspiring = _flag(d, "inspiring")
    out.first_round_attacks_bonus = _int(d, "first_round_attacks_bonus")
    out.frenzy_effect = _flag(d, "frenzy_effect")
    out.vomit = _flag(d, "vomit")
    out.sweep_main = _flag(d, "sweep_main")
    out.main_pistol = _flag(d, "main_pistol")
    out.off_pistol = _flag(d, "off_pistol")
    out.charge_attacks_bonus = _int(d, "charge_attacks_bonus")
    out.first_round_charge_attacks_bonus = _int(d, "first_round_charge_attacks_bonus")
    out.body_bull_anvil = _flag(d, "body_bull_anvil")
    out.death_blow = _flag(d, "death_blow")
    out.energy_focus_active = _flag(d, "energy_focus_active")
    out.energy_focus_attacks = _int(d, "energy_focus_attacks")
    out.maddened = _flag(d, "maddened")
    out.weapon_priority = _int(d, "weapon_priority")
    out.priority_global = _int(d, "priority_global")
    out.initiative_bonus_total = _int(d, "initiative_bonus_total")
    out.base_wounds = _int(d, "base_wounds")
    out.toughness_bonus = _int(d, "toughness_bonus")
    out.frenzy_init = _flag(d, "frenzy_init")
    out.lucky_charm_init = _flag(d, "lucky_charm_init")
    out.crimson_shade = _flag(d, "crimson_shade")
    out.disability = _flag(d, "disability")
    out.parry_parry = _flag(d, "parry_parry")
    out.parry_match_allowed = _flag(d, "parry_match_allowed")
    out.parry_starblade = _flag(d, "parry_starblade")
    out.parry_can_parry_six = _flag(d, "parry_can_parry_six")
    out.parry_dwarf_axes = _flag(d, "parry_dwarf_axes")
    out.parry_parry_reroll = _flag(d, "parry_parry_reroll")
    fill_source(sources["main"], &out.main)
    fill_source(sources["unarmed"], &out.unarmed)
    if sources.get("unpredictable") is not None:
        fill_source(sources["unpredictable"], &out.unpredictable)
        out.has_unpredictable = 1
    if sources.get("off") is not None:
        fill_source(sources["off"], &out.off)
        out.off_present = 1
    out.extra_count = len(sources["extras"])
    cdef int i
    for i in range(out.extra_count):
        fill_source(sources["extras"][i], &out.extras[i])
    cdef object bites = sources.get("last_bite") or ()
    out.last_bite_count = min(len(bites), MAX_EXTRA_ATTACKS)
    for i in range(out.last_bite_count):
        fill_source(bites[i], &out.last_bite[i])
    fill_source(reactions["bull"], bull)
    fill_source(reactions["body"], body)
    fill_source(reactions["spines"], spines)
    fill_source(reactions["backlash"], backlash)
    fill_source(reactions["fire"], fire)
    fill_source(reactions["entangle"], entangle)
    fill_source(reactions["hug"], hug)
    fill_source(reactions["acid"], acid)
    fill_source(reactions["counter"], counter)
    fill_source(reactions["infection"], infection)
    out.starting_wounds = <int>d.get("starting_wounds", d["base_wounds"])
    out.initiative_missing = _flag(d, "initiative_missing")
    out.inconsistency = _flag(d, "inconsistency")
    cdef object deltas = d.get("condition_deltas") or ()
    out.condition_delta_count = min(len(deltas), 9)
    for i in range(out.condition_delta_count):
        out.condition_deltas[i][0] = <int>deltas[i][0]
        out.condition_deltas[i][1] = <int>deltas[i][1]
        out.condition_deltas[i][2] = 1 if deltas[i][2] else 0
    out.poetry_inspired = _flag(d, "poetry_inspired")
    out.supplied_disability = <int>d.get("supplied_disability", 0)
    out.guiding_dream = _flag(d, "guiding_dream")
    out.guiding_dream_nominated = _flag(d, "guiding_dream_nominated")
    out.netted_init = _flag(d, "netted_init")
    out.persistent_frenzy = _flag(d, "persistent_frenzy")
    out.frenzy_permitted = 1 if d.get("frenzy_permitted", True) else 0
    out.stupidity_failed_init = _flag(d, "stupidity_failed_init")
    out.massively_built_init = _flag(d, "massively_built_init")
    out.danse_macabre_init = _flag(d, "danse_macabre_init")
    out.hillman_wolf_init = _flag(d, "hillman_wolf_init")
    out.can_charge = 1 if d.get("can_charge", True) else 0
    out.psychology_immunity = _flag(d, "psychology_immunity")
    out.fear_immunity = _flag(d, "fear_immunity")
    out.fear_immunity_undead_chargers = _flag(d, "fear_immunity_undead_chargers")
    out.undead_foes_no_fear = _flag(d, "undead_foes_no_fear")
    out.automatic_leadership = _flag(d, "automatic_leadership")
    out.holy_relic = _flag(d, "holy_relic")
    out.sigmar_enlightened = _flag(d, "sigmar_enlightened")
    out.squig_recipient = _flag(d, "squig_recipient")
    out.handler_leadership = _flag(d, "handler_leadership")
    out.has_stupidity_leadership = d.get("stupidity_leadership") is not None
    out.stupidity_leadership = <int>d["stupidity_leadership"] if out.has_stupidity_leadership else 0
    out.stupidity_leadership_bonus = <int>d.get("stupidity_leadership_bonus", 0)
    out.own_leadership = _flag(d, "own_leadership")
    out.broken_spirit = _flag(d, "broken_spirit")
    out.devoted = _flag(d, "devoted")
    out.slave = _flag(d, "slave")
    out.halfling = _flag(d, "halfling")
    out.poetry_victorious_leader = _flag(d, "poetry_victorious_leader")
    out.mob_leadership = _flag(d, "mob_leadership")
    out.mob_allies = <int>d.get("mob_allies", 0)
    out.enchanting_beauty = _flag(d, "enchanting_beauty")
    out.questing_vow_reroll = _flag(d, "questing_vow_reroll")
    out.opponent_ghostly_howl = _flag(d, "opponent_ghostly_howl")
    out.cold_blooded_leadership = _flag(d, "cold_blooded_leadership")
    out.cold_blooded_psychology = _flag(d, "cold_blooded_psychology")
    out.first_failed_leadership_reroll = _flag(d, "first_failed_leadership_reroll")
    out.mandatory_leadership_reroll = _flag(d, "mandatory_leadership_reroll")
    out.leadership_reroll = _flag(d, "leadership_reroll")
    out.raise_our_insignia = _flag(d, "raise_our_insignia")
    out.fear_reroll = _flag(d, "fear_reroll")
    out.ranalds_luck = _flag(d, "ranalds_luck")
    out.one_roll_reroll = _flag(d, "one_roll_reroll")
    out.scryer = _flag(d, "scryer")
    out.stupidity = _flag(d, "stupidity")
    out.stupidity_exempt = _flag(d, "stupidity_exempt")
    out.impetuous_charge = _flag(d, "impetuous_charge")
    out.disability_hero_nearby = _flag(d, "disability_hero_nearby")
    out.skaven_group = _flag(d, "skaven_group")
    out.printed_skaven_bits = <int>d.get("printed_skaven_bits", 0)
    out.bear_handler_recipient = _flag(d, "bear_handler_recipient")
    out.bear_handler_nearby = _flag(d, "bear_handler_nearby")
    out.causes_fear = _flag(d, "causes_fear")
    out.fears_foe_fire = _flag(d, "fears_foe_fire")
    out.morrs_special = _flag(d, "morrs_special")
    out.ere_we_go = _flag(d, "ere_we_go")
    out.accustomed_to_fear = _flag(d, "accustomed_to_fear")
    out.craven = _flag(d, "craven")
    out.wheelo_impact = _flag(d, "wheelo_impact")
    out.charge_gate = <int>d.get("charge_gate", 0)
    out.beauty_target = _flag(d, "beauty_target")
    out.dance_target = _flag(d, "dance_target")
    out.pendant_target = _flag(d, "pendant_target")
    out.shornaal_target = _flag(d, "shornaal_target")
    out.hypnotist_target = _flag(d, "hypnotist_target")
    out.foe_hypnotist = _flag(d, "foe_hypnotist")
    out.fauna_mode = <int>d.get("fauna_mode", 0)
    out.has_animal_handler_leadership = d.get("animal_handler_leadership") is not None
    out.animal_handler_leadership = <int>d["animal_handler_leadership"] if out.has_animal_handler_leadership else 0
    out.deceive_target = _flag(d, "deceive_target")
    out.hypnotize_target = _flag(d, "hypnotize_target")
    out.male = _flag(d, "male")
    cdef object controls = d.get("foe_controls") or (False, False, False)
    cdef object excluded = d.get("control_excluded") or (False, False, False)
    cdef int k
    for k in range(3):
        out.foe_controls[k] = 1 if controls[k] else 0
        out.control_excluded[k] = 1 if excluded[k] else 0
    cdef object rc_list = d.get("random_characteristics") or ()
    out.random_characteristics_count = min(len(rc_list), MAX_RANDOM_CHARACTERISTICS)
    cdef dict stat_index = {"WS": 0, "S": 1, "T": 2, "I": 3, "A": 4}
    for i in range(out.random_characteristics_count):
        row = rc_list[i]
        out.random_characteristics[i][0] = stat_index[row[0]]
        out.random_characteristics[i][1] = <int>row[1]
        out.random_characteristics[i][2] = <int>row[2]
        out.random_characteristics[i][3] = <int>row[3]


cdef void fill_side(object compiled, SideC* out) except *:
    """Fill one table entry from a ``compile_side`` view."""
    fill_fighter(compiled["fighter"], &out.f, compiled["sources"], compiled["reactions"],
                 &out.bull, &out.body, &out.spines, &out.backlash, &out.fire,
                 &out.entangle, &out.hug, &out.acid, &out.counter, &out.infection)
    fill_source(compiled["reactions"]["crows"], &out.crows)
    fill_source(compiled["reactions"]["stomp"], &out.stomp)
    fill_source(compiled["reactions"]["giggle"], &out.giggle)
    fill_source(compiled["reactions"]["jolt"], &out.jolt)
    fill_source(compiled["reactions"]["impact"], &out.impact)
    fill_source(compiled["reactions"].get("impact_more", compiled["reactions"]["impact"]),
                &out.impact_more)


# ---------------------------------------------------------------------------
# State lifecycle
# ---------------------------------------------------------------------------

cdef void state_alloc(StateC* s, int n) noexcept:
    """Zeroed per-row columns of the full ``CombatState`` schema."""
    s.n = n
    s.wounds = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.condition = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.initiative_penalty = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.initiative_floor = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.frenzy = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.lucky_charm = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.crimson_initiative = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.attack_penalty = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.entangled = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.parry_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.parry_remaining = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.seaguard_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.corruption_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.critical_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.force_of_will_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.force_of_will_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.force_of_will_penalty = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.disability = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mark_of_old_ones_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.luck_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.on_fire = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.weapon_skill = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.strength = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.toughness = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.initiative = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.attacks = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.broken_hands = <uint8_t*>calloc(n if n > 0 else 1, sizeof(uint8_t))
    s.hampered_main = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.hampered_off = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.starting_wounds = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.initiative_missing = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.random_rolled = <uint8_t*>calloc(n if n > 0 else 1, sizeof(uint8_t))
    s.random_modifiers = <int16_t*>calloc(5 * n if n > 0 else 1, sizeof(int16_t))
    s.torture_strength_loss = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.guiding_dream_result = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.stupidity_failed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.massively_built_lost_turn = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.netted = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.fear_hit_sixes = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.grappled = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.grappling = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.backley_strength = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.backley_initiative = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mutation_count = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.atrophied_arms = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.atrophied_legs = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.transformed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.equipment_cast_off = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.hillman_wolf = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mutation_tail = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.projection = <int32_t*>calloc(n if n > 0 else 1, sizeof(int32_t))
    s.drenok_fighting = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.magic_acorn_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.rememberer_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.rememberer_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.banter_trick_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.dodge_trick_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.trip_trick_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.charm_auto_hit = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.danse_macabre_controlled = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mouth_sewn = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.giggle_juice_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.trip_trick_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.holy_relic_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.first_failed_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.poetry_first_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.one_roll_reroll_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.ranalds_luck_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.lunatic_result = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.lunatic_stupidity = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.shornaal_passed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.feral_instinct_failed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.charm_blocked = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.entranced = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.seduction_controlled = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.drunken_result = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.animosity_failed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.beauty_passed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.charm_attack_blocked = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.hypnotized = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.hit_this_phase = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.attacked_this_phase = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.attacks_bonus_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.combat_charge_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.injury_bonus_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.rousing_sermon_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.backley_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.addiction_cured = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.black_hunger_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.djinn_power = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.last_djinn_power = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.last_dance = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.bitten_result = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.devoted_frenzy = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.crude_belch_ogre_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.backley_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.addicted_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.petru_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.first_attack_lost = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.shanty_loss = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.hit_penalty = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.poetry_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.impetuous_released = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mutation_tail_choice = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.gauche_parry = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.deathblow_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.dance_shadows_coil = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.dance_woven_mist = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.main_gauche_attacks = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.shadows_coil_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.woven_mist_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.freed_this_turn = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.mutation_projection = <int32_t*>calloc(n if n > 0 else 1, sizeof(int32_t))
    s.shifty_projection = <int32_t*>calloc(n if n > 0 else 1, sizeof(int32_t))
    s.shifty_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.gauche_mode = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.whole_choice = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.anvil_removed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.death_blow_removed = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.petru_debilitating_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.petru_strength_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.petru_resilience_spent = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.out_threshold_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.follow_me_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.righteous_active = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.attack_loss_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.hit_penalty_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.crude_belch_used = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.miss_first_attack = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.wheelo_first_impact = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.electrical_available_at = <int16_t*>calloc(n if n > 0 else 1, sizeof(int16_t))
    s.grapple_declared = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.jolt_declared = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.death_fighting = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.pool_loss_row = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))
    s.electrical_forfeit = <int8_t*>calloc(n if n > 0 else 1, sizeof(int8_t))


cdef bint state_ok(StateC* s) noexcept:
    """True when every column of the state was allocated."""
    if s.combat_charge_active == NULL:
        return False
    return not (s.wounds == NULL or s.condition == NULL or s.initiative_penalty == NULL or s.initiative_floor == NULL or s.frenzy == NULL or s.lucky_charm == NULL or s.crimson_initiative == NULL or s.attack_penalty == NULL or s.entangled == NULL or s.parry_used == NULL or s.parry_remaining == NULL or s.seaguard_used == NULL or s.corruption_used == NULL or s.critical_used == NULL or s.force_of_will_used == NULL or s.force_of_will_active == NULL or s.force_of_will_penalty == NULL or s.disability == NULL or s.mark_of_old_ones_used == NULL or s.luck_used == NULL or s.on_fire == NULL or s.weapon_skill == NULL or s.strength == NULL or s.toughness == NULL or s.initiative == NULL or s.attacks == NULL or s.broken_hands == NULL or s.hampered_main == NULL or s.hampered_off == NULL or s.starting_wounds == NULL or s.initiative_missing == NULL or s.random_rolled == NULL or s.random_modifiers == NULL or s.torture_strength_loss == NULL or s.guiding_dream_result == NULL or s.stupidity_failed == NULL or s.massively_built_lost_turn == NULL or s.netted == NULL or s.fear_hit_sixes == NULL or s.grappled == NULL or s.grappling == NULL or s.backley_strength == NULL or s.backley_initiative == NULL or s.mutation_count == NULL or s.atrophied_arms == NULL or s.atrophied_legs == NULL or s.transformed == NULL or s.equipment_cast_off == NULL or s.hillman_wolf == NULL or s.mutation_tail == NULL or s.projection == NULL or s.drenok_fighting == NULL or s.magic_acorn_used == NULL or s.rememberer_used == NULL or s.rememberer_active == NULL or s.banter_trick_active == NULL or s.dodge_trick_active == NULL or s.trip_trick_active == NULL or s.charm_auto_hit == NULL or s.danse_macabre_controlled == NULL or s.mouth_sewn == NULL or s.giggle_juice_used == NULL or s.trip_trick_used == NULL or s.holy_relic_used == NULL or s.first_failed_used == NULL or s.poetry_first_used == NULL or s.one_roll_reroll_used == NULL or s.ranalds_luck_used == NULL or s.lunatic_result == NULL or s.lunatic_stupidity == NULL or s.shornaal_passed == NULL or s.feral_instinct_failed == NULL or s.charm_blocked == NULL or s.entranced == NULL or s.seduction_controlled == NULL or s.drunken_result == NULL or s.animosity_failed == NULL or s.beauty_passed == NULL or s.charm_attack_blocked == NULL or s.hypnotized == NULL or s.hit_this_phase == NULL or s.attacked_this_phase == NULL or s.attacks_bonus_row == NULL or s.injury_bonus_row == NULL or s.rousing_sermon_used == NULL or s.backley_used == NULL or s.addiction_cured == NULL or s.black_hunger_active == NULL or s.djinn_power == NULL or s.last_djinn_power == NULL or s.last_dance == NULL or s.bitten_result == NULL or s.devoted_frenzy == NULL or s.crude_belch_ogre_used == NULL or s.backley_spent == NULL or s.addicted_spent == NULL or s.petru_spent == NULL or s.first_attack_lost == NULL or s.shanty_loss == NULL or s.hit_penalty == NULL or s.poetry_active == NULL or s.impetuous_released == NULL or s.mutation_tail_choice == NULL or s.gauche_parry == NULL or s.deathblow_used == NULL or s.dance_shadows_coil == NULL or s.dance_woven_mist == NULL or s.main_gauche_attacks == NULL or s.shadows_coil_active == NULL or s.woven_mist_active == NULL or s.freed_this_turn == NULL or s.mutation_projection == NULL or s.shifty_projection == NULL or s.shifty_row == NULL or s.gauche_mode == NULL or s.whole_choice == NULL or s.anvil_removed == NULL or s.death_blow_removed == NULL or s.petru_debilitating_spent == NULL or s.petru_strength_spent == NULL or s.petru_resilience_spent == NULL or s.out_threshold_row == NULL or s.follow_me_active == NULL or s.righteous_active == NULL or s.attack_loss_row == NULL or s.hit_penalty_row == NULL or s.crude_belch_used == NULL or s.miss_first_attack == NULL or s.wheelo_first_impact == NULL or s.electrical_available_at == NULL or s.grapple_declared == NULL or s.jolt_declared == NULL or s.death_fighting == NULL or s.pool_loss_row == NULL or s.electrical_forfeit == NULL)


cdef void state_free(StateC* s) noexcept:
    free(s.wounds)
    free(s.condition)
    free(s.initiative_penalty)
    free(s.initiative_floor)
    free(s.frenzy)
    free(s.lucky_charm)
    free(s.crimson_initiative)
    free(s.attack_penalty)
    free(s.entangled)
    free(s.parry_used)
    free(s.parry_remaining)
    free(s.seaguard_used)
    free(s.corruption_used)
    free(s.critical_used)
    free(s.force_of_will_used)
    free(s.force_of_will_active)
    free(s.force_of_will_penalty)
    free(s.disability)
    free(s.mark_of_old_ones_used)
    free(s.luck_used)
    free(s.on_fire)
    free(s.weapon_skill)
    free(s.strength)
    free(s.toughness)
    free(s.initiative)
    free(s.attacks)
    free(s.broken_hands)
    free(s.hampered_main)
    free(s.hampered_off)
    free(s.starting_wounds)
    free(s.initiative_missing)
    free(s.random_rolled)
    free(s.random_modifiers)
    free(s.torture_strength_loss)
    free(s.guiding_dream_result)
    free(s.stupidity_failed)
    free(s.massively_built_lost_turn)
    free(s.netted)
    free(s.fear_hit_sixes)
    free(s.grappled)
    free(s.grappling)
    free(s.backley_strength)
    free(s.backley_initiative)
    free(s.mutation_count)
    free(s.atrophied_arms)
    free(s.atrophied_legs)
    free(s.transformed)
    free(s.equipment_cast_off)
    free(s.hillman_wolf)
    free(s.mutation_tail)
    free(s.projection)
    free(s.drenok_fighting)
    free(s.magic_acorn_used)
    free(s.rememberer_used)
    free(s.rememberer_active)
    free(s.banter_trick_active)
    free(s.dodge_trick_active)
    free(s.trip_trick_active)
    free(s.charm_auto_hit)
    free(s.danse_macabre_controlled)
    free(s.mouth_sewn)
    free(s.giggle_juice_used)
    free(s.trip_trick_used)
    free(s.holy_relic_used)
    free(s.first_failed_used)
    free(s.poetry_first_used)
    free(s.one_roll_reroll_used)
    free(s.ranalds_luck_used)
    free(s.lunatic_result)
    free(s.lunatic_stupidity)
    free(s.shornaal_passed)
    free(s.feral_instinct_failed)
    free(s.charm_blocked)
    free(s.entranced)
    free(s.seduction_controlled)
    free(s.drunken_result)
    free(s.animosity_failed)
    free(s.beauty_passed)
    free(s.charm_attack_blocked)
    free(s.hypnotized)
    free(s.hit_this_phase)
    free(s.attacked_this_phase)
    free(s.attacks_bonus_row)
    free(s.combat_charge_active)
    free(s.injury_bonus_row)
    free(s.rousing_sermon_used)
    free(s.backley_used)
    free(s.addiction_cured)
    free(s.black_hunger_active)
    free(s.djinn_power)
    free(s.last_djinn_power)
    free(s.last_dance)
    free(s.bitten_result)
    free(s.devoted_frenzy)
    free(s.crude_belch_ogre_used)
    free(s.backley_spent)
    free(s.addicted_spent)
    free(s.petru_spent)
    free(s.first_attack_lost)
    free(s.shanty_loss)
    free(s.hit_penalty)
    free(s.poetry_active)
    free(s.impetuous_released)
    free(s.mutation_tail_choice)
    free(s.gauche_parry)
    free(s.deathblow_used)
    free(s.dance_shadows_coil)
    free(s.dance_woven_mist)
    free(s.main_gauche_attacks)
    free(s.shadows_coil_active)
    free(s.woven_mist_active)
    free(s.freed_this_turn)
    free(s.mutation_projection)
    free(s.shifty_projection)
    free(s.shifty_row)
    free(s.gauche_mode)
    free(s.whole_choice)
    free(s.anvil_removed)
    free(s.death_blow_removed)
    free(s.petru_debilitating_spent)
    free(s.petru_strength_spent)
    free(s.petru_resilience_spent)
    free(s.out_threshold_row)
    free(s.follow_me_active)
    free(s.righteous_active)
    free(s.attack_loss_row)
    free(s.hit_penalty_row)
    free(s.crude_belch_used)
    free(s.miss_first_attack)
    free(s.wheelo_first_impact)
    free(s.electrical_available_at)
    free(s.grapple_declared)
    free(s.jolt_declared)
    free(s.death_fighting)
    free(s.pool_loss_row)
    free(s.electrical_forfeit)
    memset(s, 0, sizeof(StateC))


# ---------------------------------------------------------------------------
# Pure scalar operators (canonical ports of the vectorized arithmetic forms)
# ---------------------------------------------------------------------------

cdef inline int hit_target_c(int aws, int dws) noexcept:
    if dws == 0:
        return 0
    cdef int target = 4 + (1 if dws > 2 * aws else 0) - (1 if aws > dws else 0)
    return target


cdef inline int wound_target_c(int strength, int toughness, int maximum) noexcept:
    cdef int difference = strength - toughness
    cdef int target
    if difference >= 2:
        target = 2
    elif difference == 1:
        target = 3
    elif difference == 0:
        target = 4
    elif difference == -1:
        target = 5
    elif difference >= -3:
        target = 6
    else:
        target = 7
    if target > maximum:
        target = maximum
    return target


cdef inline int _clip(int value, int low, int high) noexcept:
    if value < low:
        return low
    if value > high:
        return high
    return value


cdef int injury_condition_c(int total, FighterC* d, SourceC* src,
                            bint initial_standing,
                            bint death_fighting=0) noexcept:
    """Port of ``phases.injury_condition`` with its supplied table shapes.

    The chart the attack prints (the Misericordia's own two-band table) and
    the chart the victim prints (the bat chart) both move the thresholds;
    every later clause then rewrites the result in the oracle's order.
    """
    cdef int out_threshold = d.out_of_action_threshold
    cdef int stun_threshold = 3
    cdef bint hard_to_kill = d.hard_to_kill or (d.fen_hard_to_kill and not src.fire)
    cdef int result
    if death_fighting:
        # Art Thou Ready To Die Fighting: only a six takes the bearer out.
        out_threshold = 6
    if src.artefact_chart or d.bat_injury_chart:
        out_threshold = 4
    if src.artefact_chart:
        stun_threshold = 1
    if total >= out_threshold:
        result = OUT
    elif total >= stun_threshold:
        result = STUNNED
    else:
        result = KNOCKED_DOWN
    if hard_to_kill:
        if total >= 6:
            result = OUT
        elif total >= 3:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    if d.true_grit:
        if total >= 6:
            result = OUT
        elif total >= 4:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    if src.effect.v[<int>F_CONCUSSION] and not d.concussion_immune and 2 <= total <= 4:
        result = STUNNED
    # The Shock Rod's printed band: a low result stuns instead.
    if src.shock and 1 <= total <= 4:
        result = STUNNED
    if d.injury_profile == 1:
        if total >= 4:
            result = OUT
        elif total >= 2:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    elif d.injury_profile == 3:
        if total >= 4:
            result = OUT
        else:
            result = KNOCKED_DOWN
    if d.fragile and total == 2:
        result = STUNNED
    if src.poisonous_injury:
        if total >= 5:
            result = OUT
        elif total >= 2:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    if d.survivor and initial_standing and result == OUT:
        result = STUNNED
    if src.head_crusher and result == KNOCKED_DOWN:
        result = STUNNED
    cdef bint knocked_down_by_no_pain = d.ignore_pain and result == STUNNED
    if knocked_down_by_no_pain:
        result = KNOCKED_DOWN
    if d.jump_up and result == KNOCKED_DOWN and not knocked_down_by_no_pain:
        result = STANDING
    if d.mandrake and result == STUNNED:
        result = KNOCKED_DOWN
    return result


cdef int armour_target_c(FighterC* d, int strength, SourceC* src,
                         bint magical_attack, bint ignored) noexcept:
    cdef int delta = strength - 3
    cdef int strength_limit
    cdef int strength_penalty = delta if delta > 0 else 0
    cdef int penetration = src.effect.v[<int>F_ARMOUR_PENETRATION] + src.armour_penetration_extra
    cdef int target_bonus = src.effect.v[<int>F_TARGET_ARMOUR_BONUS]
    cdef int modifier = strength_penalty + penetration - target_bonus
    cdef bint ladle = src.effect.v[<int>F_IGNORE_ARMOUR_EXCEPT_SHIELD_AND_SKILLS] != 0
    cdef int armour_save = d.armour_save
    cdef int natural_save = d.natural_armour_save
    cdef int natural_worst = d.natural_armour_worst_save
    if ladle:
        # Printed Ladle: only shields and skills may save, so worn and
        # natural armour are denied while those selections keep their save.
        armour_save = d.shield_skill_armour_save
        natural_save = 7
        natural_worst = 7
    if d.norse_bulwark:
        # Norse Bulwark: an axe and a shield improve the save by one.
        armour_save = armour_save - 1 if armour_save > 2 else 2
    cdef int armour = armour_save + modifier
    cdef int natural = natural_save
    if not d.natural_armour_unmodified:
        # ``phases.armour_target``: only the Strength penalty (and the
        # dagger bonus) is capped at the worst natural save; armour
        # penetration is added after the cap.
        natural += strength_penalty - target_bonus
        if natural > natural_worst:
            natural = natural_worst
        natural += penetration
    if d.natural_armour_negated_by_magic and magical_attack:
        natural = 7
    if src.daemonic_flesh_negated:
        # Daemonic Flesh keeps no natural armour against a blessed attack.
        natural = 7
    if d.natural_armour_negated_by_fire and src.fire and not ladle:
        # The natural save also contributed to the worn-armour combination,
        # so the worn save loses exactly what the natural save lent it.
        natural = 7
        armour += 7 - d.natural_armour_save if d.natural_armour_save < 7 else 0
    if d.armour_specialist and not src.effect.v[<int>F_IGNORE_ARMOUR_EXCEPT_SHIELD_AND_SKILLS]:
        # Only Strength's worn-armour penalty is capped at 5+. Other save
        # modifiers and natural armour keep their existing arithmetic.
        strength_limit = 5 - (armour - modifier)
        if strength_limit < 0:
            strength_limit = 0
        if delta > strength_limit:
            armour -= delta - strength_limit
    cdef int target = armour if armour < natural else natural
    ignored = ignored or src.effect.v[<int>F_IGNORE_ARMOUR] != 0
    if ignored:
        if d.armour_cannot_be_ignored and not magical_attack:
            target = d.armour_save_floor
        else:
            target = 7
    # ``phases.armour_target``: the floor protects only a save that is not
    # ignored; an ignored save keeps the replacement chosen above.
    if d.armour_save_floor <= 6 and target > d.armour_save_floor and not ignored:
        target = d.armour_save_floor
    return target


cdef int require_characteristic_c(StateC* s, FighterC* f, int row, int stat,
                                  Rng* rng, int count) except -1:
    """Port of ``modular.state.require_characteristics`` for one stat.

    An Inconsistency profile leaves its variable characteristics unrolled;
    the operation that first reads one draws it, and the value stands for
    the rest of that round (``random_rolled`` is cleared when the round
    turns).  A characteristic nothing reads is never rolled at all, which is
    why this is called from the read sites rather than once per round.
    """
    cdef int k, d, total
    if not f.inconsistency or (s.random_rolled[row] & (1 << stat)):
        return 0
    for k in range(f.random_characteristics_count):
        if f.random_characteristics[k][0] != stat:
            continue
        total = f.random_characteristics[k][3]
        for d in range(f.random_characteristics[k][1]):
            total += rng_draw_safe(rng, 1, f.random_characteristics[k][2])
        total += s.random_modifiers[stat * count + row]
        if stat == 1:
            total -= s.torture_strength_loss[row]
        if total < 1:
            total = 1
        if stat == 0: s.weapon_skill[row] = <int16_t>total
        elif stat == 1: s.strength[row] = <int16_t>total
        elif stat == 2: s.toughness[row] = <int16_t>total
        elif stat == 3: s.initiative[row] = <int16_t>total
        else: s.attacks[row] = <int16_t>total
        s.random_rolled[row] |= <uint8_t>(1 << stat)
        break
    return 0


cdef bint characteristic_test_one_c(FighterC* me, StateC* s, int row, int target,
                                    Rng* rng, bint six_always_fails) except -1:
    """One row's characteristic test, with the Blessed Sight re-roll."""
    cdef int roll = rng_draw_safe(rng, 1, 6)
    cdef bint passed = roll <= target and not (six_always_fails and roll == 6)
    if not passed and me.blessed:
        roll = rng_draw_safe(rng, 1, 6)
        passed = roll <= target and not (six_always_fails and roll == 6)
    return passed


cdef void characteristic_tests_c(FighterC* me, int* rows, int n, int* targets,
                                 Rng* rng, bint six_always_fails,
                                 int8_t* results) except *:
    """Phased port of vectorized._characteristic_test over a row set.

    Phase 1 draws one roll per row; phase 2 (only with Blessed Sight)
    rerolls the failed rows, preserving the NumPy draw order for exact
    scripted verification.
    """
    cdef int i, roll, target, passed, failed_count
    failed_count = 0
    for i in range(n):
        roll = rng_draw_safe(rng, 1, 6)
        target = targets[i]
        passed = 1 if roll <= target and not (six_always_fails and roll == 6) else 0
        results[i] = passed
        if not passed:
            failed_count += 1
    if failed_count and me.blessed:
        for i in range(n):
            if results[i]:
                continue
            roll = rng_draw_safe(rng, 1, 6)
            target = targets[i]
            passed = 1 if roll <= target and not (six_always_fails and roll == 6) else 0
            results[i] = passed


# Observed batches record the decision keys asked and the phases executed;
# production batches leave both None and pay nothing.
#: The running batch's generator, exposed so the Python-side rule helpers
#: (the mutation chart) draw from the very same stream as the compiled core
#: instead of opening a second one.  The batch is single-threaded and
#: ``_batch_running`` already refuses reentry, so one pointer is enough.
cdef Rng* _active_rng = NULL


class NativeDice:
    """``DiceSource`` over the running batch's generator."""

    def roll(self, request):
        return native_draw(request.sides)


cdef object _decision_log = None
cdef object _phase_trace = None


def native_draw(int sides):
    """One draw from the running batch's generator."""
    if _active_rng == NULL:
        raise RuntimeError("no native batch is running")
    return rng_draw_safe(_active_rng, 1, sides)


cdef bint decide_c(object decisions, str key, object subject) except? -1:
    """Ask the policy under the oracle's key; no policy accepts, as NumPy does."""
    if _decision_log is not None:
        _decision_log.append(key)
    if decisions is None:
        return 1
    return 1 if decisions.choose(key, subject) else 0


cdef inline str round_key(int round_index, int side):
    """The oracle's ``round.{index}.{first|second}`` decision prefix."""
    return f"round.{round_index}." + ("first" if side == 0 else "second")


cdef bint decide_cached_c(object decisions, dict cache, str key, object subject) except? -1:
    """One answer per key and row set, as the NumPy engine asks its policy."""
    if key in cache:
        return cache[key]
    cdef bint value = decide_c(decisions, key, subject)
    cache[key] = value
    return value


cdef int owned_attack_d6_c(StateC* s, FighterC* f, int row, Rng* rng, str key,
                           object decisions, dict cache, object subject,
                           bint close_combat, int8_t* rerolled) except -1:
    """Port of ``OwnedRollDice.roll`` for one owned D6 of one row.

    The same wrapper the oracle puts around every owned roll, here around an
    attack die: Ranald's Luck adjusts one owned roll by one once per battle,
    the Oracle and the Augur re-roll one owned roll once per battle, and the
    Scryer repeats any close-combat die with no resource.  A die already
    re-rolled is never re-rolled again and a ``.reroll`` key offers nothing.
    ``skill.luck`` is not offered here: the attack pipeline spends
    ``luck_used`` at its own printed hit and wound sites.
    """
    cdef int value = rng_draw_safe(rng, 1, 6)
    cdef bint reroll_key
    rerolled[0] = 0
    if decisions is None or cache is None:
        return value
    reroll_key = ".reroll" in key
    if f.ranalds_luck and not s.ranalds_luck_used[row]:
        if decide_cached_c(decisions, cache, key + ".ranalds-luck.plus", subject):
            value += 1
            s.ranalds_luck_used[row] = 1
        elif decide_cached_c(decisions, cache, key + ".ranalds-luck.minus", subject):
            value -= 1
            s.ranalds_luck_used[row] = 1
    if (f.one_roll_reroll and not s.one_roll_reroll_used[row] and not reroll_key
            and decide_cached_c(decisions, cache, key + ".one-roll-reroll", subject)):
        s.one_roll_reroll_used[row] = 1
        value = rng_draw_safe(rng, 1, 6)
        rerolled[0] = 1
    if (close_combat and f.scryer and not rerolled[0] and not reroll_key
            and decide_cached_c(decisions, cache, key + ".scryer", subject)):
        value = rng_draw_safe(rng, 1, 6)
        rerolled[0] = 1
    return value


# ---------------------------------------------------------------------------
# Prepared attack (port of vectorized._prepare_weapon_attack)
# ---------------------------------------------------------------------------

cdef void prepared_free(PreparedC* p) noexcept:
    free(p.active); free(p.strength); free(p.armour_strength)
    free(p.hit_target); free(p.rolls); free(p.hit_rows); free(p.hit_positions)
    memset(p, 0, sizeof(PreparedC))


cdef int _clip_int(int value, int low, int high) noexcept:
    if value < low:
        return low
    return value if value <= high else high


cdef int prepare_attack_c(FighterC* atk, FighterC* defender, SourceC* src,
                          const int* active_in, int active_n,
                          const int8_t* charging, StateC* atk_state,
                          StateC* def_state, Rng* rng, bint first_round,
                          PreparedC* out, object decisions=None,
                          str attack_key=None, dict cache=None,
                          object attacker_py=None,
                          const int8_t* def_charges=NULL) except -1:
    """Prepare one weapon attack over ``active_in`` duel rows.

    Returns 1 when the attack resolves over at least one row and 0 when every
    defender row left the fight during preparation (mirrors ``None``).
    Kills STUNNED defenders first, exactly like the NumPy engine.
    """
    if active_n == 0:
        return 0
    memset(out, 0, sizeof(PreparedC))
    out.src = src[0]
    cdef EffectC* eff = &src.effect
    cdef EffectC* weapon = &src.weapon
    cdef int* active = <int*>malloc(active_n * sizeof(int))
    cdef int8_t* successful = <int8_t*>malloc(active_n * sizeof(int8_t))
    cdef int8_t* want_reroll = <int8_t*>malloc(active_n * sizeof(int8_t))
    cdef int8_t* luck_used_here = <int8_t*>malloc(active_n * sizeof(int8_t))
    if active == NULL or successful == NULL or want_reroll == NULL \
            or luck_used_here == NULL:
        return -1
    cdef int i, row, count = 0, strength, aws, dws, target, roll, hit_n = 0
    cdef int defender_cond, modifier, armour_strength
    cdef bint charging_row, charged_row, helpless, sweep, any_failed, use_luck
    cdef int8_t owned_rerolled = 0
    # Do not finish STUNNED defenders here. The phase-level snapshot above
    # handles only defenders stunned before this pool began; a new STUNNED
    # result must remain available to later attacks in this same pool.
    for i in range(active_n):
        row = active_in[i]
        if def_state.condition[row] == OUT:
            continue
        if src.honorable and (def_state.condition[row] == KNOCKED_DOWN
                              or def_state.condition[row] == STUNNED):
            # The Honourable strike nothing at a foe already down.
            continue
        active[count] = row
        count += 1
    if count == 0:
        free(active); free(successful); free(want_reroll); free(luck_used_here)
        return 0
    sweep = src.sweep and weapon.v[<int>F_TWO_HANDED]
    out.active_n = count
    out.active = active
    out.strength = <int16_t*>malloc(count * sizeof(int16_t))
    out.armour_strength = <int16_t*>malloc(count * sizeof(int16_t))
    out.hit_target = <int8_t*>malloc(count * sizeof(int8_t))
    out.rolls = <int8_t*>malloc(count * sizeof(int8_t))
    if (out.strength == NULL or out.armour_strength == NULL
            or out.hit_target == NULL or out.rolls == NULL):
        return -1
    # Per-row strengths, weapon skill and hit targets (no draws yet).
    for i in range(count):
        row = out.active[i]
        charging_row = charging is not NULL and charging[row] != 0
        if eff.v[<int>F_FIXED_STRENGTH]:
            strength = eff.v[<int>F_FIXED_STRENGTH]
        else:
            require_characteristic_c(atk_state, atk, row, 1, rng, def_state.n)
            strength = atk_state.strength[row]
            if eff.v[<int>F_STRENGTH_BONUS]:
                strength += eff.v[<int>F_STRENGTH_BONUS]
        if src.unarmed:
            strength += 1
        if src.energy_focus_strength:
            strength += eff.v[<int>F_ENERGY_FOCUS_ATTACKS]
        if src.scorpion_tail_poison:
            strength = 2
        if first_round or src.first_round_bonus_always:
            strength += weapon.v[<int>F_FIRST_ROUND_STRENGTH_BONUS]
        if first_round:
            # The Seaguard's spear bites harder in the opening round.
            strength += src.strength_fr_bonus
            if charging_row:
                # Slay the Large Creature pays on the charge itself.
                strength += src.strength_charge_fr_bonus
        # Foul Odour feeds a flame rather than blunting it.
        strength += src.strength_fire_bonus
        if first_round and eff.v[<int>F_CHARGE_STRENGTH_BONUS] and charging_row:
            if not src.mounted_only or atk.mounted:
                strength += eff.v[<int>F_CHARGE_STRENGTH_BONUS]
        armour_strength = strength
        if eff.v[<int>F_ARMOUR_STRENGTH_MODIFIER]:
            armour_strength += eff.v[<int>F_ARMOUR_STRENGTH_MODIFIER]
        if src.wolf_rat_bite:
            # The printed S4 bite wounds normally but pierces no armour.
            strength = 4
            armour_strength = 3
        if defender.incoming_strength_modifier:
            strength += defender.incoming_strength_modifier
            if strength < 1:
                strength = 1
        out.strength[i] = <int16_t>strength
        out.armour_strength[i] = <int16_t>armour_strength
        require_characteristic_c(atk_state, atk, row, 0, rng, def_state.n)
        require_characteristic_c(def_state, defender, row, 0, rng, def_state.n)
        aws = atk_state.weapon_skill[row]
        dws = def_state.weapon_skill[row]
        if src.shallya_aura:
            # The Tranquil Aura lowers every living model fighting in it.
            if src.shallya_self and aws > 0:
                aws -= 1
            if src.shallya_foe and dws > 0:
                dws -= 1
        if weapon.v[<int>F_WEAPON_SKILL_BONUS]:
            aws += weapon.v[<int>F_WEAPON_SKILL_BONUS]
        if src.knife_fighting:
            aws += 1
        if first_round and eff.v[<int>F_CHARGE_WS_BONUS] and charging_row:
            aws += eff.v[<int>F_CHARGE_WS_BONUS]
        target = hit_target_c(aws, dws)
        modifier = src.hit_mod_base
        if first_round and charging_row:
            modifier += src.hit_mod_charge_fr
        # Follow Me and the Righteous Charge each lift the blow they grant.
        if atk_state.follow_me_active[row] or atk_state.righteous_active[row]:
            modifier += 1
        # The Ogre's belch leaves its listener swinging wide.
        modifier -= atk_state.hit_penalty_row[row]
        # The nominated Guiding Dream target strikes better on a 2 or 3.
        if src.guiding_dream_target and (
                atk_state.guiding_dream_result[row] == 2
                or atk_state.guiding_dream_result[row] == 3):
            modifier += 1
        if first_round and src.bellowing:
            modifier -= 1
        target = _clip_int(target - modifier, 2, 6)
        if src.berserker and charging_row:
            target = _clip_int(target - 1, 2, 6)
        if first_round and atk.ferocious_charge and charging_row:
            target = _clip_int(target + 1, 2, 6)
        # Every attack against a hypnotized model gains +1 To Hit this turn.
        if def_state.hypnotized[row]:
            target = _clip_int(target - 1, 2, 6)
        # Babbling Banter: the declaring bearer hits better, and an enemy
        # that declared it hits this bearer worse.
        if atk_state.banter_trick_active[row]:
            target = _clip_int(target - 1, 2, 6)
        if def_state.banter_trick_active[row]:
            target = _clip_int(target + 1, 2, 6)
        # The Djinn's Curse turns blows aside: an attack against its bearer
        # suffers one point of To Hit (``modular/contexts.py``).
        if def_state.djinn_power[row] == 1:
            target = _clip_int(target + 1, 2, 6)
        # Invincible Swordsman strikes on its own printed face.
        if src.fixed_hit_target:
            target = src.fixed_hit_target
        # Fear's consequence: the attacker hits on a natural six only, even
        # against a defender with no Weapon Skill.
        if atk_state.fear_hit_sixes[row]:
            target = 6
        out.hit_target[i] = <int8_t>target
        want_reroll[i] = 0
        luck_used_here[i] = 0
    # Draws and per-row success flags.
    cdef int* targets = <int*>malloc(count * sizeof(int))
    cdef int8_t* char_results = NULL
    if targets == NULL:
        return -1
    if sweep:
        for i in range(count):
            require_characteristic_c(def_state, defender, out.active[i], 3, rng,
                                     def_state.n)
            targets[i] = def_state.initiative[out.active[i]]
        char_results = <int8_t*>malloc(count * sizeof(int8_t))
        if char_results == NULL:
            return -1
        characteristic_tests_c(defender, out.active, count, targets, rng, 0,
                               char_results)
    for i in range(count):
        row = out.active[i]
        charging_row = charging is not NULL and charging[row] != 0
        charged_row = def_charges is not NULL and def_charges[row] != 0
        if sweep:
            successful[i] = 1 if not char_results[i] else 0
            out.rolls[i] = 6 if not char_results[i] else 1
        else:
            if atk_state.miss_first_attack[row] and src.first_of_pool:
                # Preserve the weapon allocation: the first blow misses
                # without a die rather than reducing the count.
                roll = 0
                successful[i] = 0
                atk_state.miss_first_attack[row] = 0
            elif (eff.v[<int>F_AUTOMATIC_HIT] or def_state.charm_auto_hit[row]
                    or def_state.entranced[row]):
                # Automatic hits have no natural die result.  Keep roll=0,
                # matching vectorized._prepare_weapon_attack; success is
                # explicit so this value cannot trigger natural-six effects.
                # A charm's auto-hit half (Hypnotic Gaze, the Mark of
                # Shornaal) and an entranced defender hit automatically; the
                # first declaration against a trance ends both trances.
                roll = 0
                successful[i] = 1
                if def_state.entranced[row]:
                    def_state.entranced[row] = 0
                    atk_state.entranced[row] = 0
            else:
                roll = owned_attack_d6_c(
                    atk_state, atk, row, rng,
                    attack_key + ".hit" if attack_key is not None else "hit",
                    decisions, cache, attacker_py, 1, &owned_rerolled)
                successful[i] = 1 if roll >= out.hit_target[i] else 0
            out.rolls[i] = <int8_t>roll
        defender_cond = def_state.condition[row]
        helpless = defender_cond == KNOCKED_DOWN or defender_cond == PARALYZED
        if helpless:
            successful[i] = 1
            out.rolls[i] = 1
        if not successful[i]:
            # Hatred and every other To Hit re-roll, read from the oracle's
            # own ``_hit_reroll`` folded at compile time.  Frenzy suppresses
            # the Psychology half, so it indexes the table per row.
            want_reroll[i] = src.reroll_table[
                (8 if first_round else 0) + (4 if charging_row else 0)
                + (2 if charged_row else 0) + (1 if atk_state.frenzy[row] else 0)]
            # The Rememberer: the remembered Slayer Hero may repeat one
            # missed blow against a large (or, in the wider printed variant,
            # a Toughness 5+) enemy.  The marker is pool-scoped, so every
            # later blow of the same pool repeats freely once it is lit.
            if (not want_reroll[i] and atk.rememberer
                    and (atk.rememberer_target_large
                         or (atk.rememberer_large_or_tough
                             and def_state.toughness[row] >= 5))
                    and (atk_state.rememberer_active[row]
                         or (not atk_state.rememberer_used[row]
                             and decisions is not None
                             and decide_cached_c(
                                 decisions, cache,
                                 (attack_key + ".rememberer") if attack_key is not None
                                 else "rememberer", attacker_py)))):
                atk_state.rememberer_used[row] = 1
                atk_state.rememberer_active[row] = 1
                want_reroll[i] = 1
            use_luck = 0
            if src.luck and not atk_state.luck_used[row] and not want_reroll[i]:
                want_reroll[i] = 1
                use_luck = 1
            if (not want_reroll[i] and src.virtue
                    and def_state.strength[row] > atk_state.strength[row]):
                want_reroll[i] = 1
            luck_used_here[i] = use_luck
    free(targets)
    if char_results is not NULL:
        free(char_results)
    # Reroll phase: a draw per failed row (NumPy draw order preserved).
    for i in range(count):
        if want_reroll[i] and not successful[i]:
            roll = owned_attack_d6_c(
                atk_state, atk, out.active[i], rng,
                attack_key + ".hit.reroll" if attack_key is not None else "hit.reroll",
                decisions, cache, attacker_py, 1, &owned_rerolled)
            out.rolls[i] = <int8_t>roll
            if roll >= out.hit_target[i]:
                successful[i] = 1
            if luck_used_here[i]:
                atk_state.luck_used[out.active[i]] = 1
    # Seaguard Spear Master: one failed opening-round hit per row is rolled
    # again; a die Hatred (or Luck) already rerolled is never repeated.
    if src.seaguard_reroll and first_round:
        for i in range(count):
            row = out.active[i]
            if (not successful[i] and not want_reroll[i]
                    and not atk_state.seaguard_used[row]):
                atk_state.seaguard_used[row] = 1
                roll = rng_draw_safe(rng, 1, 6)
                out.rolls[i] = <int8_t>roll
                if roll >= out.hit_target[i]:
                    successful[i] = 1
    free(want_reroll)
    free(luck_used_here)
    # The Magic Acorn turns one missed opening blow of a Hero into a hit.
    if src.magic_acorn and first_round:
        for i in range(count):
            row = out.active[i]
            if not successful[i] and not atk_state.magic_acorn_used[row]:
                atk_state.magic_acorn_used[row] = 1
                successful[i] = 1
                out.rolls[i] = out.hit_target[i]
    # Corruption: the victim forces one landed blow to be rolled again, once
    # per battle, and the second result stands.
    if src.corruption and decisions is not None:
        for i in range(count):
            row = out.active[i]
            if (successful[i] and not def_state.corruption_used[row]
                    and decide_cached_c(
                        decisions, cache,
                        (attack_key + ".corruption") if attack_key is not None
                        else "corruption", int(row))):
                def_state.corruption_used[row] = 1
                roll = rng_draw_safe(rng, 1, 6)
                out.rolls[i] = <int8_t>roll
                successful[i] = 1 if roll >= out.hit_target[i] else 0
    # Marks of Ranald: the Priest ducks past any hit on an unmodifiable six,
    # before any critical effect is determined.
    if src.marks_of_ranald:
        for i in range(count):
            if successful[i] and rng_draw_safe(rng, 1, 6) >= 6:
                successful[i] = 0
    # Mark of the Old Ones converts every remaining failed roll once per battle.
    if atk.mark:
        for i in range(count):
            row = out.active[i]
            if not successful[i] and not atk_state.mark_of_old_ones_used[row]:
                successful[i] = 1
                out.rolls[i] = out.hit_target[i]
                atk_state.mark_of_old_ones_used[row] = 1
    for i in range(count):
        if successful[i]:
            hit_n += 1
    out.hit_n = hit_n
    out.hit_rows = <int*>malloc(hit_n * sizeof(int)) if hit_n else NULL
    out.hit_positions = <int*>malloc(hit_n * sizeof(int)) if hit_n else NULL
    if hit_n and (out.hit_rows == NULL or out.hit_positions == NULL):
        return -1
    hit_n = 0
    for i in range(count):
        row = out.active[i]
        if successful[i]:
            out.hit_rows[hit_n] = row
            out.hit_positions[hit_n] = i
            hit_n += 1
            def_state.hit_this_phase[row] = 1
        elif defender.spider_infested:
            atk_state.initiative_penalty[row] = <int8_t>(atk_state.initiative_penalty[row] + 1)
            atk_state.initiative_floor[row] = 0
    free(successful)
    return 1


# ---------------------------------------------------------------------------
# Parry and hit defences (port of vectorized._parry_hits / _apply_hit_defences)
# ---------------------------------------------------------------------------
# (Forward declarations for apply_hit_defences_c / resolve_weapon_c live in
# _combat_native.pxd: the pair is mutually recursive.)
# ---------------------------------------------------------------------------

cdef int resolve_weapon_c(DuelC* d, int atk_side, SourceC* src,
                          PreparedC* prepared, const int8_t* charging,
                          StateC* s_atk, StateC* s_def, Rng* rng,
                          bint first_round, const int8_t* phase_condition,
                          bint defences_resolved, const int* parry_rows,
                          int parry_rows_n, bint parry_given, object decisions,
                          bint always_accept, object attacker_py,
                          object defender_py, object observation,
                          str attack_key=None, dict cache=None) except -1:
    cdef FighterC* atk = &d.first.f if atk_side == 0 else &d.second.f
    cdef FighterC* defender = &d.first.f if atk_side == 1 else &d.second.f
    cdef EffectC* eff = &src.effect
    cdef int i, j, k, row, n, m, total, damage, helmet, ward_t, regen_t, crit_need
    cdef int8_t owned_wound_rerolled = 0
    cdef int t, raw, sigmarite = 1 if src.sigmarite else 0
    cdef int rc = 0, expanded = 0
    cdef int8_t* hit_values = NULL
    cdef int16_t* strength_hits = NULL
    cdef int16_t* armour_strength_hits = NULL
    cdef int8_t* automatic_wound = NULL
    cdef int8_t* raw_targets = NULL
    cdef int8_t* targets = NULL
    cdef int8_t* wound_rolls = NULL
    cdef int8_t* critical_rolls = NULL
    cdef int8_t* wounded = NULL
    cdef int8_t* extra_hits = NULL
    cdef int8_t* extra_wounds = NULL
    cdef int* barrage_rows = NULL
    cdef int n_barrage = 0
    cdef SourceC barrage_src
    cdef PreparedC barrage_prep
    cdef int8_t* rerolls = NULL
    cdef int8_t* auto_w = NULL
    cdef int8_t* crit_roll = NULL
    cdef int8_t* tgt = NULL
    cdef int8_t* raw_tgt = NULL
    cdef int* wound_rows = NULL
    cdef int16_t* wound_strength = NULL
    cdef int8_t* critical = NULL
    cdef int8_t* save_target = NULL
    cdef int8_t* saved = NULL
    cdef int8_t* helpless = NULL
    cdef int* damage_rows = NULL
    cdef int8_t* damage_critical = NULL
    cdef int8_t* damage_helpless = NULL
    cdef int* damage_values = NULL
    cdef int16_t* wounds_before = NULL
    cdef int* dmg_counts = NULL
    cdef int* reactive_rows = NULL
    cdef int* spittle_targets = NULL
    cdef int* spittle_rows = NULL
    cdef int8_t* spittle_results = NULL
    cdef int* infection_rows = NULL
    cdef int* infection_rows2 = NULL
    cdef SourceC spectral_src
    cdef PreparedC spectral_prep
    cdef int* infection_targets = NULL
    cdef int8_t* infection_results = NULL
    cdef int* injury_rows = NULL
    cdef int8_t* injury_crit = NULL
    cdef int8_t* injury_rolls = NULL
    cdef int8_t* injury = NULL
    cdef int* contagious = NULL
    cdef int* cont_targets = NULL
    cdef int8_t* cont_results = NULL
    cdef int* hit_rows = prepared.hit_rows
    cdef int* hit_positions = prepared.hit_positions
    cdef int* repeats = NULL
    cdef int8_t* hv2 = NULL
    cdef int16_t* sh2 = NULL
    cdef int16_t* ash2 = NULL
    cdef int* hr2 = NULL
    cdef int* hp2 = NULL
    cdef SourceC* acid_src = &d.first.acid if atk_side == 1 else &d.second.acid
    cdef SourceC* infection_src = &d.first.infection if atk_side == 0 else &d.second.infection
    cdef PreparedC acid_prep
    cdef PreparedC infection_prep
    cdef int n_react = 0, prepared_ok = 0
    cdef int inj_count = 0
    cdef int pos = 0
    cdef int wb = 0, c2 = 0, run_index = 0
    cdef int highest_crit = 0
    cdef int crit_bonus = (1 if src.web_of_steel else 0) + eff.v[<int>F_CRITICAL_INJURY_BONUS]
    cdef int n_contagious = 0
    cdef int n_spittle = 0
    cdef int highest = 0
    try:
        """Wound/injury pipeline, site-by-site port of vectorized._resolve_weapon.

        ``prepared`` holds the attack built by ``prepare_attack_c``.  When
        ``defences_resolved`` is false the hit/parry boundary runs first (the
        batch-core path); the phase-level runner pre-resolves it and passes true,
        in which case hit positions are recomputed by searching the active pool
        exactly like ``np.searchsorted``.  Returns 0 on success, -1 on failure.
        """
        if not defences_resolved:
            if apply_hit_defences_c(d, atk_side, src, prepared, charging, s_atk,
                                    s_def, rng, parry_rows, parry_rows_n,
                                    parry_given, decisions, attack_key, cache,
                                    defender_py) < 0:
                return -1
        n = prepared.hit_n
        if n == 0:
            return 0
        if defences_resolved:
            # np.searchsorted(active, hit_rows): both arrays are sorted ascending.
            j = 0
            for i in range(n):
                row = hit_rows[i]
                while j < prepared.active_n and prepared.active[j] < row:
                    j += 1
                hit_positions[i] = j
        hit_values = <int8_t*>malloc(n * sizeof(int8_t))
        strength_hits = <int16_t*>malloc(n * sizeof(int16_t))
        armour_strength_hits = <int16_t*>malloc(n * sizeof(int16_t))
        if (hit_values == NULL or strength_hits == NULL
                or armour_strength_hits == NULL):
            rc = -1
            return rc
        for i in range(n):
            hit_values[i] = prepared.rolls[hit_positions[i]]
            strength_hits[i] = prepared.strength[hit_positions[i]]
            armour_strength_hits[i] = prepared.armour_strength[hit_positions[i]]
        # Kusara-kama and chained-squig weapon reactions.
        if src.kusara:
            # The hit hampers one hand (the main hand unless the bearer
            # fights with both and declines); the reply loses that hand's
            # weapon, keeping the published minimum of one attack.
            for i in range(n):
                if hit_values[i] >= 5:
                    row = hit_rows[i]
                    s_def.attack_penalty[row] = <int8_t>(s_def.attack_penalty[row] + 1)
                    if (defender.off_hand_attacks and defender.off_present
                            and decisions is not None
                            and not decide_cached_c(
                                decisions, cache,
                                (attack_key + ".kusara-main-hand") if attack_key is not None
                                else "kusara-main-hand", defender_py)):
                        s_def.hampered_off[row] = <int16_t>(s_def.hampered_off[row] + 1)
                    else:
                        s_def.hampered_main[row] = <int16_t>(s_def.hampered_main[row] + 1)
        if src.chained:
            for i in range(n):
                s_def.entangled[hit_rows[i]] = 1
        # Anvil-head: a charging Necromantic Abomination replicates each hit
        # 1-3 times; outside a charge the rule is inert (Khemri, Necromantic
        # Modification / Anvil Head). Dice are drawn only for charging rows so
        # the RNG stream stays aligned with the NumPy backend.
        if src.anvil and first_round:
            repeats = <int*>malloc(n * sizeof(int))
            if repeats == NULL:
                rc = -1
                return rc
            total = 0
            for i in range(n):
                if charging[hit_rows[i]]:
                    repeats[i] = rng_draw_safe(rng, 1, 3)
                else:
                    repeats[i] = 1
                total += repeats[i]
            hv2 = <int8_t*>malloc(total * sizeof(int8_t))
            sh2 = <int16_t*>malloc(total * sizeof(int16_t))
            ash2 = <int16_t*>malloc(total * sizeof(int16_t))
            hr2 = <int*>malloc(total * sizeof(int))
            hp2 = <int*>malloc(total * sizeof(int))
            if (hv2 == NULL or sh2 == NULL or ash2 == NULL or hr2 == NULL or hp2 == NULL):
                free(repeats)
                free(hv2); free(sh2); free(ash2); free(hr2); free(hp2)
                rc = -1
                return rc
            k = 0
            for i in range(n):
                for j in range(repeats[i]):
                    hr2[k] = hit_rows[i]
                    hp2[k] = hit_positions[i]
                    hv2[k] = hit_values[i]
                    sh2[k] = strength_hits[i]
                    ash2[k] = armour_strength_hits[i]
                    k += 1
            free(repeats)
            free(hit_values); free(strength_hits); free(armour_strength_hits)
            hit_values = hv2
            strength_hits = sh2
            armour_strength_hits = ash2
            hit_rows = hr2
            hit_positions = hp2
            n = total
            expanded = 1
        # Wound-track arrays must be sized AFTER the anvil expansion: their
        # loops below run over the expanded ``n`` (mirrors the NumPy engine,
        # which builds them post-replication).
        automatic_wound = <int8_t*>malloc(n * sizeof(int8_t))
        infection_rows2 = <int*>malloc(n * sizeof(int))
        if infection_rows2 == NULL:
            rc = -1
            return rc
        raw_targets = <int8_t*>malloc(n * sizeof(int8_t))
        targets = <int8_t*>malloc(n * sizeof(int8_t))
        wound_rolls = <int8_t*>malloc(n * sizeof(int8_t))
        critical_rolls = <int8_t*>malloc(n * sizeof(int8_t))
        wounded = <int8_t*>malloc(n * sizeof(int8_t))
        if (automatic_wound == NULL or raw_targets == NULL or targets == NULL
                or wound_rolls == NULL or critical_rolls == NULL
                or wounded == NULL):
            rc = -1
            return rc
        # Ignition (per-source threshold folded at compile time).
        if src.ignition <= 6:
            for i in range(n):
                if rng_draw_safe(rng, 1, 6) >= src.ignition:
                    s_def.on_fire[hit_rows[i]] = 1
        if src.spider_spittle:
            spittle_targets = <int*>malloc(n * sizeof(int))
            spittle_rows = <int*>malloc(n * sizeof(int))
            spittle_results = <int8_t*>malloc(n * sizeof(int8_t))
            if spittle_targets == NULL or spittle_results == NULL or spittle_rows == NULL:
                rc = -1
                return rc
            for i in range(n):
                row = hit_rows[i]
                if s_def.condition[row] == STANDING:
                    spittle_rows[n_spittle] = row
                    spittle_targets[n_spittle] = s_def.toughness[row]
                    n_spittle += 1
            characteristic_tests_c(defender, spittle_rows, n_spittle, spittle_targets, rng, 1, spittle_results)
            for i in range(n_spittle):
                if not spittle_results[i]:
                    s_def.condition[spittle_rows[i]] = PARALYZED
        # Disease Dagger adds one ordinary automatic wound on a natural-six
        # hit unless the defender has poison/disease immunity. Resolve it
        # before the dagger's ordinary wound, matching modular.attacks.
        if src.disease_dagger and not defender.infection_immune:
            infection_rows = <int*>malloc(n * sizeof(int))
            infection_targets = <int*>malloc(n * sizeof(int))
            infection_results = <int8_t*>malloc(n * sizeof(int8_t))
            if infection_rows == NULL or infection_targets == NULL or infection_results == NULL:
                rc = -1
                return rc
            n_spittle = 0
            for i in range(n):
                if hit_values[i] == 6:
                    infection_rows[n_spittle] = hit_rows[i]
                    infection_targets[n_spittle] = s_def.toughness[hit_rows[i]]
                    n_spittle += 1
            if n_spittle:
                characteristic_tests_c(defender, infection_rows, n_spittle,
                                       infection_targets, rng, 1, infection_results)
                k = 0
                for i in range(n_spittle):
                    if not infection_results[i]:
                        infection_rows[k] = infection_rows[i]
                        k += 1
                if k:
                    if prepare_attack_c(atk, defender, infection_src, infection_rows, k,
                                         charging, s_atk, s_def, rng, first_round,
                                         &infection_prep) < 0:
                        rc = -1
                        return rc
                    if infection_prep.active_n:
                        if resolve_weapon_c(d, atk_side, infection_src, &infection_prep,
                                             charging, s_atk, s_def, rng, first_round,
                                             phase_condition, 1, NULL, 0, 0, decisions,
                                             always_accept, attacker_py, defender_py,
                                             None) < 0:
                            prepared_free(&infection_prep)
                            rc = -1
                            return rc
                        prepared_free(&infection_prep)
                    k = 0
                    for i in range(n):
                        if s_def.condition[hit_rows[i]] != OUT:
                            hit_rows[k] = hit_rows[i]
                            hit_positions[k] = hit_positions[i]
                            hit_values[k] = hit_values[i]
                            strength_hits[k] = strength_hits[i]
                            armour_strength_hits[k] = armour_strength_hits[i]
                            k += 1
                    n = k
            free(infection_rows); infection_rows = NULL
            free(infection_targets); infection_targets = NULL
            free(infection_results); infection_results = NULL
            if n == 0:
                return rc
        # The ethereal save intercepts an ordinary hit before any critical
        # effect, on the defender's own supplied face; a magical attack
        # passes straight through (``modular/attacks.py``).
        if defender.ethereal and not src.magical_attack and defender.ethereal_hit_save <= 6:
            k = 0
            for i in range(n):
                if rng_draw_safe(rng, 1, 6) >= defender.ethereal_hit_save:
                    continue
                hit_rows[k] = hit_rows[i]
                hit_positions[k] = hit_positions[i]
                hit_values[k] = hit_values[i]
                strength_hits[k] = strength_hits[i]
                armour_strength_hits[k] = armour_strength_hits[i]
                k += 1
            n = k
            if n == 0:
                return rc
        # Spectral Touch: a natural six adds ONE extra wound of this very
        # attack -- not a fresh hit, poison or critical trigger.  The oracle
        # resolves it before the ordinary wound, through the same armour,
        # ward and regeneration this source already carries, so the source is
        # reused with its wound forced automatic and its damage fixed at one.
        if src.spectral_touch:
            n_spittle = 0
            for i in range(n):
                if hit_values[i] == 6:
                    infection_rows2[n_spittle] = hit_rows[i]
                    n_spittle += 1
            if n_spittle:
                spectral_src = src[0]
                spectral_src.spectral_touch = 0
                spectral_src.killing_blow = 0
                spectral_src.disease_dagger = 0
                spectral_src.spider_spittle = 0
                spectral_src.automatic_wound_tag = 1
                spectral_src.no_critical = 1
                spectral_src.rapier = 0
                spectral_src.ignition = 7
                spectral_src.damage = 1
                spectral_src.effect.v[<int>F_AUTOMATIC_HIT] = 1
                spectral_src.effect.v[<int>F_DAMAGE_DIE_SIDES] = 0
                ok = prepare_attack_c(atk, defender, &spectral_src, infection_rows2,
                                      n_spittle, charging, s_atk, s_def, rng,
                                      first_round, &spectral_prep)
                if ok < 0:
                    rc = -1
                    return rc
                if ok > 0:
                    if resolve_weapon_c(d, atk_side, &spectral_src, &spectral_prep,
                                        charging, s_atk, s_def, rng, first_round,
                                        phase_condition, 1, NULL, 0, 0, decisions,
                                        always_accept, attacker_py, defender_py,
                                        None, None, cache) < 0:
                        prepared_free(&spectral_prep)
                        rc = -1
                        return rc
                    prepared_free(&spectral_prep)
                k = 0
                for i in range(n):
                    if s_def.condition[hit_rows[i]] != OUT:
                        hit_rows[k] = hit_rows[i]
                        hit_positions[k] = hit_positions[i]
                        hit_values[k] = hit_values[i]
                        strength_hits[k] = strength_hits[i]
                        armour_strength_hits[k] = armour_strength_hits[i]
                        k += 1
                n = k
                if n == 0:
                    return rc
        # Automatic tagged wounds omit the die. Lotus/Wight retain a wound
        # while allowing the ordinary critical attempt.
        if src.automatic_wound_tag:
            for i in range(n):
                automatic_wound[i] = 1
        else:
            for i in range(n):
                automatic_wound[i] = 0
        # The Trip trick is the round's chosen alternative for exactly one
        # attack: after a hit the bearer gives up that attack's wound roll
        # and trips the opponent on a 2+.  It is resolved BEFORE the wound
        # step, so no wound die is consumed.
        if (atk.confound_and_confuse and decisions is not None
                and attack_key is not None and not src.spectral_touch):
            k = 0
            for i in range(n):
                row = hit_rows[i]
                if (s_atk.trip_trick_active[row] and not s_atk.trip_trick_used[row]
                        and s_def.condition[row] == STANDING
                        and decide_cached_c(decisions, cache,
                                            attack_key + ".trip.hit", int(row))):
                    s_atk.trip_trick_used[row] = 1
                    if rng_draw_safe(rng, 1, 6) >= 2:
                        s_def.condition[row] = KNOCKED_DOWN
                        if not defender.persistent_frenzy:
                            s_def.frenzy[row] = 0
                    continue
                hit_rows[k] = hit_rows[i]
                hit_positions[k] = hit_positions[i]
                hit_values[k] = hit_values[i]
                strength_hits[k] = strength_hits[i]
                armour_strength_hits[k] = armour_strength_hits[i]
                k += 1
            n = k
            if n == 0:
                return rc
        # Killing Blow: a natural To Hit six wounds automatically, so no die
        # is rolled and no critical is invented.  Black Lotus keeps its own
        # explicitly permitted critical attempt instead (the oracle's
        # ``killing_blow and not lotus`` gate).
        if src.killing_blow and not src.lotus:
            for i in range(n):
                if hit_values[i] == 6:
                    automatic_wound[i] = 1
        # Black Lotus already wounds: the oracle offers its optional critical
        # attempt under the round's own attack key and turns the wound
        # automatic when the player declines it.
        if src.lotus and decisions is not None and attack_key is not None:
            for i in range(n):
                if hit_values[i] == 6 and not decide_cached_c(
                        decisions, cache, attack_key + ".lotus-critical",
                        int(hit_rows[i])):
                    automatic_wound[i] = 1
        # To-wound targets.
        for i in range(n):
            require_characteristic_c(s_def, defender, hit_rows[i], 2, rng, s_def.n)
            t = s_def.toughness[hit_rows[i]]
            if defender.thin_flesh:
                # Printed Thin Flesh: one point of Toughness for the wound
                # target only, never below one.
                t = t - 1 if t > 1 else 1
            raw = wound_target_c(strength_hits[i], t,
                                 eff.v[<int>F_MAXIMUM_WOUND_TARGET])
            raw_targets[i] = <int8_t>raw
            t = raw
            if src.monster_slayer and t > 4:
                t = 4
            t = t - eff.v[<int>F_WOUND_MODIFIER] - sigmarite
            if t < 2:
                t = 2
            targets[i] = <int8_t>t
        # Wound rolls.
        for i in range(n):
            wound_rolls[i] = 0 if automatic_wound[i] else <int8_t>owned_attack_d6_c(
                s_atk, atk, hit_rows[i], rng,
                attack_key + ".wound" if attack_key is not None else "wound",
                decisions, cache, attacker_py, 1, &owned_wound_rerolled)
            critical_rolls[i] = wound_rolls[i]
            wounded[i] = 1 if automatic_wound[i] or (
                (src.lotus or src.wight_blades) and hit_values[i] == 6
            ) or wound_rolls[i] >= targets[i] else 0
        # Manbane: a natural 1 on the wound roll always fails.
        if src.manbane:
            for i in range(n):
                if wounded[i] and wound_rolls[i] == 1:
                    wounded[i] = 0
        # Luck rerolls one failed wound when not already spent on hit.
        if src.luck_wound:
            for i in range(n):
                if not wounded[i] and not s_atk.luck_used[hit_rows[i]]:
                    roll = rng_draw_safe(rng, 1, 6)
                    wound_rolls[i] = <int8_t>roll
                    if src.critical_on_reroll:
                        critical_rolls[i] = <int8_t>roll
                    wounded[i] = 1 if roll >= targets[i] else 0
                    s_atk.luck_used[hit_rows[i]] = 1
        # Rerolled wound rolls (single full-array draw over the failed rows).
        if eff.v[<int>F_REROLL_WOUNDS] or src.reroll_wounds_extra:
            rerolls = <int8_t*>malloc(n * sizeof(int8_t))
            if rerolls == NULL:
                rc = -1
                return rc
            for i in range(n):
                rerolls[i] = 0
                if not wounded[i]:
                    rerolls[i] = <int8_t>rng_draw_safe(rng, 1, 6)
            for i in range(n):
                if not wounded[i] and rerolls[i]:
                    # The second die stands, and (Devil's Toxin apart) it
                    # is the die the critical reads (``critical_on_reroll``).
                    wound_rolls[i] = rerolls[i]
                    if src.critical_on_reroll:
                        critical_rolls[i] = rerolls[i]
                    if rerolls[i] >= targets[i]:
                        wounded[i] = 1
            free(rerolls)
            rerolls = NULL
        # Mark of the Old Ones: one guaranteed wound roll per row and battle.
        if atk.mark:
            for i in range(n):
                row = hit_rows[i]
                if not wounded[i] and not s_atk.mark_of_old_ones_used[row]:
                    wounded[i] = 1
                    wound_rolls[i] = targets[i]
                    s_atk.mark_of_old_ones_used[row] = 1
        # The Liche mends itself on the wound its touch steals.
        if src.wraith_heal and decisions is not None:
            for i in range(n):
                row = hit_rows[i]
                if (wounded[i] and s_atk.wounds[row] < atk.base_wounds
                        and decide_cached_c(
                            decisions, cache,
                            (attack_key + ".wraith-heal") if attack_key is not None
                            else "wraith-heal", attacker_py)):
                    s_atk.wounds[row] = <int16_t>(s_atk.wounds[row] + 1)
        # Titanic Strength: a blow that fails to wound still throws a
        # standing foe to the ground on a failed Strength test.
        if src.titanic_strength:
            for i in range(n):
                row = hit_rows[i]
                if wounded[i] or s_def.condition[row] != STANDING:
                    continue
                if not characteristic_test_one_c(defender, s_def, row,
                                                 s_def.strength[row], rng, 0):
                    s_def.condition[row] = KNOCKED_DOWN
                    if not defender.persistent_frenzy:
                        s_def.frenzy[row] = 0
        # Rapier Barrage (``modular/attacks.py::resolve_reference_attack``):
        # a hit that fails to wound grants another full attack at a further
        # -1 to hit, and that attack may itself continue the barrage.  The
        # rows that wounded and the rows that continue are disjoint, so the
        # continuation is resolved here, before this step's damage.
        if src.rapier and src.hit_mod_base > -12:
            barrage_rows = <int*>malloc(n * sizeof(int))
            if barrage_rows == NULL:
                rc = -1
                return rc
            n_barrage = 0
            for i in range(n):
                row = hit_rows[i]
                if (not wounded[i] and s_atk.condition[row] != OUT
                        and s_def.condition[row] != OUT):
                    barrage_rows[n_barrage] = row
                    n_barrage += 1
            if n_barrage:
                barrage_src = src[0]
                barrage_src.hit_mod_base -= 1
                memset(&barrage_prep, 0, sizeof(PreparedC))
                prepared_ok = prepare_attack_c(
                    atk, defender, &barrage_src, barrage_rows, n_barrage, charging,
                    s_atk, s_def, rng, first_round, &barrage_prep, decisions,
                    (attack_key + ".barrage") if attack_key is not None else None,
                    cache, attacker_py)
                if prepared_ok < 0:
                    rc = -1
                    return rc
                if prepared_ok > 0:
                    if resolve_weapon_c(d, atk_side, &barrage_src, &barrage_prep, charging,
                                        s_atk, s_def, rng, first_round, phase_condition,
                                        0, NULL, 0, 0, decisions, always_accept,
                                        attacker_py, defender_py, None,
                                        (attack_key + ".barrage") if attack_key is not None else None,
                                        cache) < 0:
                        prepared_free(&barrage_prep)
                        rc = -1
                        return rc
                    prepared_free(&barrage_prep)
        # Collect the wounded rows with their per-row context.
        auto_w = <int8_t*>malloc(n * sizeof(int8_t))
        crit_roll = <int8_t*>malloc(n * sizeof(int8_t))
        tgt = <int8_t*>malloc(n * sizeof(int8_t))
        raw_tgt = <int8_t*>malloc(n * sizeof(int8_t))
        wound_rows = <int*>malloc(n * sizeof(int))
        wound_strength = <int16_t*>malloc(n * sizeof(int16_t))
        if (auto_w == NULL or crit_roll == NULL or tgt == NULL or raw_tgt == NULL
                or wound_rows == NULL or wound_strength == NULL):
            rc = -1
            return rc
        m = 0
        for i in range(n):
            if wounded[i]:
                wound_rows[m] = hit_rows[i]
                auto_w[m] = automatic_wound[i]
                crit_roll[m] = critical_rolls[i]
                tgt[m] = targets[i]
                raw_tgt[m] = raw_targets[i]
                wound_strength[m] = armour_strength_hits[i]
                m += 1
        if m == 0:
            return rc
        if src.monster_slayer_eff:
            for i in range(m):
                if raw_tgt[i] > 4:
                    t = s_def.toughness[wound_rows[i]]
                    if wound_strength[i] < t:
                        wound_strength[i] = <int16_t>t
        # Criticals: at most one per attacker row and close-combat phase.
        critical = <int8_t*>malloc(m * sizeof(int8_t))
        if critical == NULL:
            rc = -1
            return rc
        for i in range(m):
            # The Hellblade crits on a five once its wound target is four
            # or less; Achilles Heel scores even on a target of six.
            crit_need = src.critical_threshold
            if src.hellblade and tgt[i] <= 4 and crit_need > 5:
                crit_need = 5
            critical[i] = 1 if (not auto_w[i] and crit_roll[i] >= crit_need
                                and (tgt[i] < 6 or src.critical_when_needing_six)) else 0
        if src.no_critical:
            for i in range(m):
                critical[i] = 0
        claim_criticals_c(critical, wound_rows, m, s_atk, critical)
        # Hardy Constitution: a 4+ save against criticals.  The NumPy engine
        # draws one value per wound row when any critical is present.
        if src.hardy:
            any_crit = 0
            for i in range(m):
                if critical[i]:
                    any_crit = 1
                    break
            if any_crit:
                # One draw per wound row (NumPy draws the full array), then a 4+
                # save only for rows that actually scored a critical.
                for i in range(m):
                    if critical[i] and rng_draw_safe(rng, 1, 6) >= 5:
                        critical[i] = 0
                        s_atk.critical_used[wound_rows[i]] = 0
        # Store the separate basic critical-table result in the critical array;
        # zero still means an ordinary wound throughout the remaining filters.
        for i in range(m):
            if critical[i]:
                critical[i] = <int8_t>(rng_draw_safe(rng, 1, 6) + crit_bonus)
        # Armour save (phased draw over the rows with a save target).
        save_target = <int8_t*>malloc(m * sizeof(int8_t))
        saved = <int8_t*>malloc(m * sizeof(int8_t))
        if save_target == NULL or saved == NULL:
            rc = -1
            return rc
        for i in range(m):
            save_target[i] = <int8_t>armour_target_c(
                defender, wound_strength[i], src, src.magical,
                critical[i] >= 3
                # Misericordia: armour is ignored against a Knocked Down foe.
                or (src.effect.v[<int>F_IGNORE_ARMOUR_AGAINST_KNOCKED_DOWN]
                    and s_def.condition[wound_rows[i]] == KNOCKED_DOWN)
                # Achilles Heel: a stampeding charge wound of five or more
                # finds the gap and ignores armour entirely.
                or (src.achilles_stampede and first_round
                    and charging is not NULL and charging[wound_rows[i]]
                    and crit_roll[i] >= 5))
            # An attack carrying the Djinn's Curse worsens the armour save.
            if s_atk.djinn_power[wound_rows[i]] == 1:
                save_target[i] = <int8_t>(save_target[i] + 1)
            saved[i] = 0
        for i in range(m):
            if save_target[i] <= 6:
                t = save_target[i]
                if t < 2:
                    t = 2
                # The armour die belongs to the defender.
                if owned_attack_d6_c(
                        s_def, defender, wound_rows[i], rng,
                        attack_key + ".armour" if attack_key is not None else "armour",
                        decisions, cache, defender_py, 1, &owned_wound_rerolled) >= t:
                    saved[i] = 1
        if defender.eshin_robes:
            # Eshin Assassin robes reroll every failed armour save once; the
            # reroll replaces, rather than consumes, the Luck skill's.
            for i in range(m):
                if save_target[i] <= 6 and not saved[i]:
                    if rng_draw_safe(rng, 1, 6) >= max(2, save_target[i]):
                        saved[i] = 1
        elif defender.luck:
            for i in range(m):
                row = wound_rows[i]
                if save_target[i] <= 6 and not saved[i] and not s_def.luck_used[row]:
                    if rng_draw_safe(rng, 1, 6) >= max(2, save_target[i]):
                        saved[i] = 1
                    s_def.luck_used[row] = 1
        if defender.mark:
            for i in range(m):
                row = wound_rows[i]
                if save_target[i] <= 6 and not saved[i] and not s_def.mark_of_old_ones_used[row]:
                    saved[i] = 1
                    s_def.mark_of_old_ones_used[row] = 1
        k = 0
        for i in range(m):
            if not saved[i]:
                wound_rows[k] = wound_rows[i]
                critical[k] = critical[i]
                k += 1
        m = k
        if m == 0:
            return rc
        # The Dodge trick is an unmodifiable 4+ melee save the declaring
        # bearer gets in place of (or better than) its printed ward.
        if defender.confound_and_confuse:
            k = 0
            for i in range(m):
                if (s_def.dodge_trick_active[wound_rows[i]]
                        and rng_draw_safe(rng, 1, 6) >= 4):
                    continue
                wound_rows[k] = wound_rows[i]
                critical[k] = critical[i]
                k += 1
            m = k
            if m == 0:
                return rc
        # Ward and regeneration are per row: the Djinn's Luck and the
        # Shadows Coil improve the defender's ward, while an attack carrying
        # the Djinn's Curse worsens both saves by one
        # (``modular/contexts.py::prepare_special_save_context``).
        k = 0
        for i in range(m):
            row = wound_rows[i]
            ward_t = src.ward
            if s_def.dance_shadows_coil[row] and ward_t > 4:
                ward_t = 4
            if s_def.djinn_power[row] == 2:
                # Luck grants 4+, or only 6+ where no ordinary ward applies.
                ward_t = 6 if ward_t > 6 else 4
            regen_t = src.regeneration
            if src.no_saves:
                # Ruling D13: the wound allows no saving throw of any kind.
                ward_t = 7
                regen_t = 7
            if s_atk.djinn_power[row] == 1:
                ward_t += 1
                regen_t += 1
            if ward_t <= 6 and rng_draw_safe(rng, 1, 6) >= ward_t:
                continue
            if regen_t <= 6 and rng_draw_safe(rng, 1, 6) >= regen_t:
                continue
            wound_rows[k] = wound_rows[i]
            critical[k] = critical[i]
            k += 1
        m = k
        if m == 0:
            return rc
        # Injury profile 2: any unsaved wound takes the warrior out.  The
        # oracle returns ``damage=1`` and leaves the Wound total untouched,
        # so nothing is subtracted here.
        if defender.injury_profile == 2:
            for i in range(m):
                s_def.condition[wound_rows[i]] = OUT
            return rc
        # Helpless defenders are removed before damage is applied (the phase
        # snapshot is used when the phase-level runner supplied one).
        helpless = <int8_t*>malloc(m * sizeof(int8_t))
        if helpless == NULL:
            rc = -1
            return rc
        for i in range(m):
            row = wound_rows[i]
            if phase_condition is not NULL:
                t = phase_condition[row]
            else:
                t = s_def.condition[row]
            # The oracle's ``helpless_at_start``: a defender already Knocked
            # Down when the pool began (``modular/pools.py``).  It is taken
            # out with ``damage=1`` and its Wound total is left untouched, so
            # the row is removed from the damage pass entirely.  A Paralyzed
            # defender is hit automatically but its wound resolves normally.
            helpless[i] = 1 if (t == KNOCKED_DOWN and not src.non_melee) else 0
            if helpless[i]:
                s_def.condition[row] = OUT
        # Damage application.
        damage_values = <int*>malloc(m * sizeof(int))
        if damage_values == NULL:
            rc = -1
            return rc
        total = 0
        for i in range(m):
            damage = src.damage
            if eff.v[<int>F_DAMAGE_DIE_SIDES]:
                damage = rng_draw_safe(rng, 1, eff.v[<int>F_DAMAGE_DIE_SIDES])
            if critical[i] and damage < 2:
                damage = 2
            if src.flammable_double:
                damage *= 2
            if src.marine_hunter:
                damage *= 2
            if helpless[i]:
                # No Wound is subtracted and no injury is rolled for a
                # helpless victim; the oracle records one point of damage.
                damage = 0
            damage_values[i] = damage
            total += damage
        damage_rows = <int*>malloc(total * sizeof(int))
        damage_critical = <int8_t*>malloc(total * sizeof(int8_t))
        damage_helpless = <int8_t*>malloc(total * sizeof(int8_t))
        wounds_before = <int16_t*>malloc(m * sizeof(int16_t))
        if (damage_rows == NULL or damage_critical == NULL or damage_helpless == NULL
                or wounds_before == NULL):
            rc = -1
            return rc
        k = 0
        for i in range(m):
            for j in range(damage_values[i]):
                damage_rows[k] = wound_rows[i]
                damage_critical[k] = critical[i]
                damage_helpless[k] = helpless[i]
                k += 1
        # Pre-subtraction wounds per distinct row (affected rows = run starts).
        # Zero-damage entries (a helpless kill leaves the Wound total
        # untouched) never enter ``damage_rows``, so they must not own a
        # ``wounds_before`` slot either: the injury loop below advances one
        # slot per *damage* run, and a skipped entry would desynchronise every
        # later row's pre-subtraction Wounds.
        k = 0
        c2 = -1
        for i in range(m):
            if damage_values[i] == 0:
                continue
            if c2 == -1 or wound_rows[i] != c2:
                wounds_before[k] = s_def.wounds[wound_rows[i]]
                k += 1
            c2 = wound_rows[i]
        # np.subtract.at: every damage instance subtracts one wound.
        for i in range(total):
            s_def.wounds[damage_rows[i]] = <int16_t>(s_def.wounds[damage_rows[i]] - 1)
        # Acid Blood: the defender strikes back once per damage instance.
        dmg_counts = <int*>malloc(s_def.n * sizeof(int))
        if dmg_counts == NULL:
            rc = -1
            return rc
        for i in range(s_def.n):
            dmg_counts[i] = 0
        for i in range(total):
            dmg_counts[damage_rows[i]] += 1
        # A helpless kill subtracts no Wound but records one point of damage,
        # so the wound reactions fire exactly once for it
        # (``modular/attacks.py`` damage = 1, ``aftermath._react_to_wound``).
        for i in range(m):
            if helpless[i] and dmg_counts[wound_rows[i]] == 0:
                dmg_counts[wound_rows[i]] = 1
        t = 0
        for i in range(s_def.n):
            if dmg_counts[i] > t:
                t = dmg_counts[i]
        if defender.acid_blood:
            reactive_rows = <int*>malloc(s_def.n * sizeof(int))
            if reactive_rows == NULL:
                rc = -1
                return rc
            for j in range(t):
                n_react = 0
                for i in range(s_def.n):
                    if dmg_counts[i] > j:
                        reactive_rows[n_react] = i
                        n_react += 1
                if n_react == 0:
                    continue
                prepared_ok = prepare_attack_c(defender, atk, acid_src, reactive_rows,
                                               n_react, NULL, s_def, s_atk, rng, 0,
                                               &acid_prep)
                if prepared_ok < 0:
                    rc = -1
                    return rc
                if prepared_ok > 0:
                    if resolve_weapon_c(d, 1 - atk_side, acid_src, &acid_prep, NULL,
                                        s_def, s_atk, rng, 0, NULL, 0, NULL, 0,
                                        0, None, 1, None, None, None) < 0:
                        prepared_free(&acid_prep)
                        rc = -1
                        return rc
                    prepared_free(&acid_prep)
        # Contagious answers every close-combat wound that leaves the bearer
        # out of action; a helpless kill never reaches the injury loop below,
        # so it is tested here (``modular/aftermath.py``).
        if defender.contagious and not atk.undead_or_possessed and not src.non_melee:
            c2 = -1
            for i in range(m):
                row = wound_rows[i]
                if not helpless[i] or row == c2:
                    continue
                c2 = row
                if s_atk.condition[row] == OUT:
                    continue
                if not characteristic_test_one_c(atk, s_atk, row, s_atk.toughness[row], rng, 1):
                    s_atk.wounds[row] = <int16_t>(s_atk.wounds[row] - 1)
                    if s_atk.wounds[row] <= 0:
                        s_atk.condition[row] = OUT
        # Nightshade poison: initiative penalty per wound.
        if src.nightshade:
            for i in range(m):
                s_def.initiative_penalty[wound_rows[i]] = <int8_t>(
                    s_def.initiative_penalty[wound_rows[i]] + damage_values[i]
                )
        # The Cursed Hillman gets one attempt for each lost Wound; a
        # transformation replaces injury resolution and takes the source's
        # own W2 wolf profile.
        if src.lycanthrope:
            for i in range(total):
                row = damage_rows[i]
                if s_def.hillman_wolf[row] or s_def.condition[row] == OUT:
                    continue
                if rng_draw_safe(rng, 1, 6) >= 4:
                    s_def.hillman_wolf[row] = 1
                    s_def.wounds[row] = 2
                    s_def.condition[row] = STANDING
                    s_def.weapon_skill[row] = 4
                    s_def.strength[row] = 4
                    s_def.toughness[row] = 4
                    s_def.initiative[row] = 5
                    s_def.attacks[row] = 2
                    s_def.parry_remaining[row] = 0
        # The Torturer saps a living victim's Strength with every wound it
        # actually suffers.
        if src.torturer and not src.non_melee:
            # One point of Strength per wounding attack, whatever its damage
            # (``modular/aftermath.py``: ``reactive_damage > 0``).
            c2 = -1
            for i in range(m):
                row = wound_rows[i]
                if row == c2 or dmg_counts[row] == 0:
                    continue
                c2 = row
                if s_def.strength[row] > 1:
                    s_def.strength[row] = <int16_t>(s_def.strength[row] - 1)
                s_def.torture_strength_loss[row] = <int8_t>(
                    s_def.torture_strength_loss[row] + 1)
        # Injury rolls: one per damage instance that reaches zero wounds.
        injury_rows = <int*>malloc(total * sizeof(int))
        injury_crit = <int8_t*>malloc(total * sizeof(int8_t))
        if injury_rows == NULL or injury_crit == NULL:
            rc = -1
            return rc
        j = 0
        for pos in range(total):
            row = damage_rows[pos]
            if pos == 0 or row != damage_rows[pos - 1]:
                wb = wounds_before[run_index]
                run_index += 1
                j = 0
            j += 1
            if not damage_helpless[pos] and (wb <= 0 or j >= wb):
                injury_rows[inj_count] = row
                injury_crit[inj_count] = damage_critical[pos]
                inj_count += 1
        if inj_count == 0:
            return rc
        # Injury profile 4: each injured row is taken out immediately.
        if defender.injury_profile == 4:
            for i in range(inj_count):
                if i == 0 or injury_rows[i] != injury_rows[i - 1]:
                    s_def.condition[injury_rows[i]] = OUT
            return rc
        # Injury rolls: D6 plus modifiers, plus the critical bonus.
        injury_rolls = <int8_t*>malloc(inj_count * sizeof(int8_t))
        if injury_rolls == NULL:
            rc = -1
            return rc
        for i in range(inj_count):
            # The injury die belongs to the attacker (the oracle resolves it
            # through ``attacker_dice``).
            t = owned_attack_d6_c(
                s_atk, atk, injury_rows[i], rng,
                attack_key + ".injury." + str(i) if attack_key is not None else "injury",
                decisions, cache, attacker_py, 1, &owned_wound_rerolled
            ) + eff.v[<int>F_INJURY_MODIFIER] + s_atk.injury_bonus_row[injury_rows[i]]
            if src.knife_fighting_injury:
                t += 1
            if src.blessing_of_morr:
                t += 1
            if defender.inured_to_pain:
                t -= 1
            if defender.lycanthrope_self and not s_def.hillman_wolf[injury_rows[i]]:
                # One point of Injury while the curse has not yet taken it.
                t -= 1
            if injury_crit[i] >= 5:
                t += 2
            injury_rolls[i] = <int8_t>t
        # Injury reroll (Hard to Kill / Tough as Steel).  The oracle's
        # production pipeline substitutes ``AlwaysAccept`` before any attack
        # resolves, so without an explicit policy every eligible Injury
        # result is re-rolled -- not only Out of Action -- and the re-roll
        # carries the same modifiers as the first roll.
        if defender.injury_reroll_out and not src.fire:
            for i in range(inj_count):
                if decisions is not None and attack_key is not None:
                    if not decide_cached_c(decisions, cache,
                                           attack_key + ".injury." + str(i) + ".reroll-choice",
                                           int(injury_rows[i])):
                        continue
                t = (rng_draw_safe(rng, 1, 6) + eff.v[<int>F_INJURY_MODIFIER]
                     + s_atk.injury_bonus_row[injury_rows[i]])
                if src.knife_fighting_injury:
                    t += 1
                if src.blessing_of_morr:
                    t += 1
                if defender.inured_to_pain:
                    t -= 1
                if defender.lycanthrope_self and not s_def.hillman_wolf[injury_rows[i]]:
                    t -= 1
                if injury_crit[i] >= 5:
                    t += 2
                injury_rolls[i] = <int8_t>t
        # Injury conditions.
        injury = <int8_t*>malloc(inj_count * sizeof(int8_t))
        if injury == NULL:
            rc = -1
            return rc
        for i in range(inj_count):
            injury[i] = <int8_t>injury_condition_c(
                injury_rolls[i], defender, src,
                s_def.condition[injury_rows[i]] == STANDING,
                s_def.death_fighting[injury_rows[i]],
            )
            # The construct shrugs the Injury result off (it has still lost
            # the Wound); Inured to Pain's printed zero ignores the damage,
            # which gives the lost Wound back.
            if (defender.undead_construct and not src.magical_attack
                    and rng_draw_safe(rng, 1, 6)
                        >= 4 + (1 if s_atk.djinn_power[injury_rows[i]] == 1 else 0)):
                injury[i] = -1
            elif defender.inured_to_pain and injury_rolls[i] <= 0:
                s_def.wounds[injury_rows[i]] = <int16_t>(s_def.wounds[injury_rows[i]] + 1)
                if src.nightshade:
                    s_def.initiative_penalty[injury_rows[i]] = <int8_t>(
                        s_def.initiative_penalty[injury_rows[i]] - 1)
                injury[i] = -1
        # Drop the instances the two clauses above cancelled.
        k = 0
        for i in range(inj_count):
            if injury[i] < 0:
                continue
            injury[k] = injury[i]
            injury_rows[k] = injury_rows[i]
            injury_crit[k] = injury_crit[i]
            k += 1
        inj_count = k
        if inj_count == 0:
            return rc
        # Collapse multiple injury instances for one duel row before helmet or
        # Thick Skull reacts. NumPy aggregates the highest injury per row first;
        # drawing a reaction per damage instance changes both outcomes and the
        # subsequent RNG stream when one hit deals multiple wounds.
        k = 0
        i = 0
        while i < inj_count:
            row = injury_rows[i]
            highest = injury[i]
            highest_crit = injury_crit[i]
            j = i + 1
            while j < inj_count and injury_rows[j] == row:
                if injury[j] > highest:
                    highest = injury[j]
                    highest_crit = injury_crit[j]
                j += 1
            injury_rows[k] = row
            injury[k] = <int8_t>highest
            injury_crit[k] = <int8_t>highest_crit
            k += 1
            i = j
        inj_count = k
        # Thick Skull / helmet stun recovery (one full-array draw per injured
        # duel row, after highest-injury aggregation, matching NumPy).
        # No Pain rewrites the aggregated result before the helmet reacts.
        for i in range(inj_count):
            if defender.veskit_no_pain and injury[i] != OUT:
                injury[i] = STANDING
            if defender.marianna_jump_up and injury[i] == KNOCKED_DOWN:
                injury[i] = STANDING
        # Hard to Rattle caps the helmet face it reacts on; Basha worsens a
        # helmet reaction, never Thick Skull's replacement reaction.
        helmet = defender.helmet_save
        if defender.hard_to_rattle and not src.fire:
            if helmet > 4:
                helmet = 4
        if src.skull_busta and helmet <= 6 and not defender.thick_skull:
            helmet = 6
        if defender.thick_skull:
            t = 2 if defender.helmet_save <= 4 else 3
            for i in range(inj_count):
                if injury[i] == STUNNED and rng_draw_safe(rng, 1, 6) >= t:
                    injury[i] = KNOCKED_DOWN
        elif helmet <= 6:
            for i in range(inj_count):
                if injury[i] == STUNNED and rng_draw_safe(rng, 1, 6) >= helmet:
                    injury[i] = KNOCKED_DOWN
        # A Stunned victim of Needle and Thread has its mouth sewn shut.
        if src.needle_and_thread:
            for i in range(inj_count):
                if injury[i] == STUNNED:
                    s_def.mouth_sewn[injury_rows[i]] = 1
        # Highest injury per row, then apply condition and frenzy.
        contagious = <int*>malloc(m * sizeof(int))
        if contagious == NULL:
            rc = -1
            return rc
        i = 0
        while i < inj_count:
            row = injury_rows[i]
            highest = 0
            j = i
            while j < inj_count and injury_rows[j] == row:
                if injury[j] > highest:
                    highest = injury[j]
                j += 1
            if s_def.condition[row] < highest:
                s_def.condition[row] = <int8_t>highest
            if highest != STANDING:
                s_def.frenzy[row] = 0
            if (highest == OUT and src.great_thirster
                    and s_atk.condition[row] == STANDING):
                # The kill itself rouses the Great Thirster.
                s_atk.frenzy[row] = 1
            if (highest == OUT and defender.contagious and not atk.undead_or_possessed
                    and not src.non_melee):
                contagious[n_contagious] = row
                n_contagious += 1
            i = j
        # Contagious: the attacker tests Toughness (a six always fails) or loses
        # a wound and falls out of the fight.
        if n_contagious:
            cont_targets = <int*>malloc(n_contagious * sizeof(int))
            cont_results = <int8_t*>malloc(n_contagious * sizeof(int8_t))
            if cont_targets == NULL or cont_results == NULL:
                rc = -1
                return rc
            for i in range(n_contagious):
                cont_targets[i] = s_atk.toughness[contagious[i]]
            characteristic_tests_c(atk, contagious, n_contagious, cont_targets, rng,
                                   1, cont_results)
            for i in range(n_contagious):
                if not cont_results[i]:
                    row = contagious[i]
                    s_atk.wounds[row] = <int16_t>(s_atk.wounds[row] - 1)
                    if s_atk.wounds[row] <= 0:
                        s_atk.condition[row] = OUT
    finally:
        free(hit_values)
        free(strength_hits)
        free(armour_strength_hits)
        free(automatic_wound)
        free(raw_targets)
        free(targets)
        free(wound_rolls)
        free(critical_rolls)
        free(wounded)
        free(extra_hits)
        free(barrage_rows)
        free(extra_wounds)
        free(rerolls)
        free(auto_w)
        free(crit_roll)
        free(tgt)
        free(raw_tgt)
        free(wound_rows)
        free(wound_strength)
        free(critical)
        free(save_target)
        free(saved)
        free(helpless)
        free(damage_rows)
        free(damage_critical)
        free(damage_helpless)
        free(damage_values)
        free(wounds_before)
        free(dmg_counts)
        free(reactive_rows)
        free(spittle_targets)
        free(spittle_rows)
        free(spittle_results)
        free(infection_rows)
        free(infection_rows2)
        free(infection_targets)
        free(infection_results)
        free(injury_rows)
        free(injury_crit)
        free(injury_rolls)
        free(injury)
        free(contagious)
        free(cont_targets)
        free(cont_results)
        if expanded:
            free(hit_rows)
            free(hit_positions)
    return rc


cdef void claim_criticals_c(int8_t* candidate, int* rows, int n,
                            StateC* atk_state, int8_t* accepted) noexcept:
    """At most one critical per attacker row and close-combat phase."""
    cdef int i, row
    for i in range(n):
        if not candidate[i]:
            accepted[i] = 0
            continue
        row = rows[i]
        if atk_state.critical_used[row]:
            # ``candidate`` and ``accepted`` may alias in the native caller.
            # Explicitly clear rejected candidates to enforce one critical per
            # attacker row and phase, matching vectorized._claim_criticals.
            accepted[i] = 0
            continue
        accepted[i] = 1
        atk_state.critical_used[row] = 1


cdef inline bint parry_succeeds_c(FighterC* defender, SourceC* src, int roll,
                                  int hit_value, int defender_ws) noexcept:
    """Port of ``phases.resolve_parry``'s ``succeeds``, in the oracle's order.

    Darting Steel caps the parry at the blow it answers, the Estalian pair
    turns the parry into a roll under the defender's Weapon Skill, and the
    Starblade keeps its own fixed face; otherwise the parry must match or
    beat the hit, depending on the equality grant.
    """
    if src.parry_max_roll and roll > hit_value:
        return 0
    if src.parry_roll_under:
        return roll < defender_ws
    if defender.parry_starblade:
        return roll >= 4
    if defender.parry_match_allowed:
        return roll >= hit_value
    return roll > hit_value


cdef int parry_resolve_c(FighterC* defender, SourceC* src, int* hit_rows, int hit_n,
                         int* hit_values, int* hit_strength, StateC* def_state,
                         Rng* rng, const int* selected_rows, int selected_n,
                         bint selected_given, int* out_hit_rows,
                         int* out_parried, object decisions=None,
                         str attack_key=None, dict cache=None,
                         object defender_py=None) except -1:
    """Full port of vectorized._parry_hits.

    Returns the number of surviving hits (written first into out_hit_rows);
    parried rows follow in out_parried.  Consumes parry bookkeeping exactly
    like the NumPy engine, including the full-array second draw when a parry
    reroll is available.
    """
    cdef int i, j, k, row, surviving = 0, parried = 0, end, limit, pick
    cdef int best_pos, best_value, count, need_reroll, value, second, blocked_now
    cdef int8_t parry_owned = 0
    cdef int sel_pos = 0
    if src.effect.v[<int>F_CANNOT_BE_PARRIED] or hit_n == 0 or not defender.parry_parry:
        for i in range(hit_n):
            out_hit_rows[surviving] = hit_rows[i]
            surviving += 1
        return surviving
    cdef int8_t* eligible = <int8_t*>malloc(hit_n * sizeof(int8_t))
    cdef int8_t* chosen = <int8_t*>malloc(hit_n * sizeof(int8_t))
    cdef int8_t* blocked = <int8_t*>malloc(hit_n * sizeof(int8_t))
    cdef int* parry_rolls = <int*>malloc(hit_n * sizeof(int))
    cdef int8_t* success1 = <int8_t*>malloc(hit_n * sizeof(int8_t))
    if (eligible == NULL or chosen == NULL or blocked == NULL
            or parry_rolls == NULL or success1 == NULL):
        return -1
    for i in range(hit_n):
        eligible[i] = 0
        chosen[i] = 0
        blocked[i] = 0
        success1[i] = 0
    if selected_given:
        # Phase-level pipeline preselected the best one/two hits per row.
        # Selection can contain rows whose surviving hit was filtered by a
        # previous pool; membership must therefore be checked independently
        # for each hit row, like NumPy's np.isin.
        for i in range(hit_n):
            row = hit_rows[i]
            sel_pos = 0
            while sel_pos < selected_n and selected_rows[sel_pos] < row:
                sel_pos += 1
            if (def_state.condition[row] == STANDING
                    and def_state.parry_remaining[row] > 0
                    and hit_strength[i] < 2 * def_state.strength[row]
                    and (hit_values[i] != 6 or defender.parry_can_parry_six)
                    and not (src.killing_blow and hit_values[i] == 6)
                    and sel_pos < selected_n and selected_rows[sel_pos] == row):
                eligible[i] = 1

    else:
        # Standalone path: keep the best hits per row, up to the parries the
        # row still has available.
        count = 0
        for i in range(hit_n):
            row = hit_rows[i]
            if (def_state.condition[row] == STANDING
                    and def_state.parry_remaining[row] > 0
                    and hit_strength[i] < 2 * def_state.strength[row]
                    and (hit_values[i] != 6 or defender.parry_can_parry_six)):
                eligible[i] = 1
                count += 1
        if count:
            i = 0
            while i < hit_n:
                row = hit_rows[i]
                end = i
                while end < hit_n and hit_rows[end] == row:
                    end += 1
                limit = def_state.parry_remaining[row]
                pick = 0
                for k in range(i, end):
                    if eligible[k]:
                        pick += 1
                if pick > limit:
                    pick = limit
                for j in range(pick):
                    best_pos = -1
                    best_value = -1
                    for k in range(i, end):
                        if chosen[k] or not eligible[k]:
                            continue
                        if hit_values[k] > best_value:
                            best_value = hit_values[k]
                            best_pos = k
                    if best_pos >= 0:
                        chosen[best_pos] = 1
                i = end
            for i in range(hit_n):
                if not chosen[i]:
                    eligible[i] = 0
    need_reroll = 0
    for i in range(hit_n):
        if eligible[i]:
            need_reroll = 1
            break
    if not need_reroll:
        for i in range(hit_n):
            out_hit_rows[surviving] = hit_rows[i]
            surviving += 1
        free(eligible); free(chosen); free(blocked)
        free(parry_rolls); free(success1)
        return surviving
    # First parry-roll phase: a draw for every hit row (NumPy draws a full
    # array before any per-row filtering).
    for i in range(hit_n):
        # The parry die is the defender's own roll, so it carries the
        # personal re-roll resources the oracle offers at every owned roll.
        parry_rolls[i] = owned_attack_d6_c(
            def_state, defender, hit_rows[i], rng,
            attack_key + ".parry" if attack_key is not None else "parry",
            decisions, cache, defender_py, 1, &parry_owned)
    for i in range(hit_n):
        value = hit_values[i]
        if value == 6 and not defender.parry_can_parry_six:
            success1[i] = 0
        else:
            success1[i] = parry_succeeds_c(
                defender, src, parry_rolls[i], value,
                def_state.weapon_skill[hit_rows[i]])
    need_reroll = 0
    for i in range(hit_n):
        blocked[i] = 1 if eligible[i] and success1[i] else 0
        if not blocked[i]:
            need_reroll = 1
    if defender.parry_parry_reroll and need_reroll:
        # Second full-array draw whenever any hit row is not blocked.
        for i in range(hit_n):
            second = owned_attack_d6_c(
                def_state, defender, hit_rows[i], rng,
                attack_key + ".parry.reroll" if attack_key is not None else "parry.reroll",
                decisions, cache, defender_py, 1, &parry_owned)
            value = hit_values[i]
            if value == 6 and not defender.parry_can_parry_six:
                continue
            if eligible[i] and parry_succeeds_c(
                    defender, src, second, value,
                    def_state.weapon_skill[hit_rows[i]]):
                blocked[i] = 1
    # Bookkeeping: each eligible hit consumes one exceptional parry.
    for i in range(hit_n):
        row = hit_rows[i]
        if eligible[i]:
            def_state.parry_used[row] = 1
            def_state.parry_remaining[row] = <int8_t>(def_state.parry_remaining[row] - 1)
        if blocked[i]:
            out_parried[parried] = row
            parried += 1
        else:
            out_hit_rows[surviving] = row
            surviving += 1
    free(eligible); free(chosen); free(blocked)
    free(parry_rolls); free(success1)
    return surviving


cdef int apply_hit_defences_c(DuelC* d, int atk_side, SourceC* src,
                              PreparedC* prepared, const int8_t* charging,
                              StateC* s_atk, StateC* s_def, Rng* rng,
                              const int* parry_rows, int parry_rows_n,
                              bint parry_given, object decisions=None,
                              str attack_key=None, dict cache=None,
                              object defender_py=None) except -1:
    """Hit-to-parry boundary port of vectorized._apply_hit_defences.

    Filters OUT rows, resolves parries (plus the optional cutlass counter and
    lucky charm saves), and rewrites ``prepared`` hit rows/positions in place.
    Returns the surviving hit count.
    """
    cdef FighterC* atk = &d.first.f if atk_side == 0 else &d.second.f
    cdef FighterC* defender = &d.first.f if atk_side == 1 else &d.second.f
    cdef int i, j, row, n, survivor_n, charm_roll
    cdef int* hit_rows = prepared.hit_rows
    cdef int* hit_positions = prepared.hit_positions
    cdef int hit_n = prepared.hit_n
    cdef SourceC* counter_src = NULL
    cdef PreparedC counter_prep
    cdef int prepared_ok = 0
    cdef int* charm_rolls = NULL
    # Drop hits whose defender already left the fight.
    n = 0
    for i in range(hit_n):
        row = hit_rows[i]
        if s_def.condition[row] != OUT:
            hit_rows[n] = row
            hit_positions[n] = hit_positions[i]
            n += 1
    prepared.hit_n = n
    if n == 0:
        return 0
    cdef int* hit_values = <int*>malloc(n * sizeof(int))
    cdef int* hit_strength = <int*>malloc(n * sizeof(int))
    cdef int* survivors = <int*>malloc(n * sizeof(int))
    cdef int* parried = <int*>malloc(n * sizeof(int))
    if hit_values == NULL or hit_strength == NULL or survivors == NULL \
            or parried == NULL:
        return -1
    for i in range(n):
        hit_values[i] = prepared.rolls[hit_positions[i]]
        hit_strength[i] = prepared.strength[hit_positions[i]]
    survivor_n = parry_resolve_c(
        defender, src, hit_rows, n, hit_values, hit_strength, s_def, rng,
        parry_rows, parry_rows_n, parry_given, survivors, parried,
        decisions, attack_key, cache, defender_py,
    )
    if survivor_n < 0:
        return -1
    # Sword-breaker: a parried blow is trapped on 4+, breaking the hand that
    # held the striking weapon (the main hand only when its own weapon
    # struck).  The break survives the attack; the next phase's equipment
    # projection substitutes the backup weapon or the fist.
    if n - survivor_n and src.trap_blade:
        for i in range(n - survivor_n):
            row = parried[i]
            if rng_draw_safe(rng, 1, 6) >= 4:
                if not (s_atk.broken_hands[row] & 1) and src.trap_main:
                    s_atk.broken_hands[row] = <uint8_t>(s_atk.broken_hands[row] | 1)
                else:
                    s_atk.broken_hands[row] = <uint8_t>(s_atk.broken_hands[row] | 2)
    # Spider-infested defenders slow attackers whose hits were parried.
    if n - survivor_n and defender.spider_infested:
        for i in range(n - survivor_n):
            row = parried[i]
            s_atk.initiative_penalty[row] = <int8_t>(s_atk.initiative_penalty[row] + 1)
            s_atk.initiative_floor[row] = 0
    # Cutlass counter-attack: the defender strikes back after each parry.
    if n - survivor_n and src.counter_cutlass:
        counter_src = &d.first.counter if atk_side == 1 else &d.second.counter
        prepared_ok = prepare_attack_c(
            defender, atk, counter_src, parried, n - survivor_n, NULL, s_def,
            s_atk, rng, 0, &counter_prep,
        )
        if prepared_ok > 0:
            if resolve_weapon_c(
                    d, 1 - atk_side, counter_src, &counter_prep, NULL, s_def,
                    s_atk, rng, 0, NULL, 0, NULL, 0, 0, None, 1, None, None,
                    None,
            ) < 0:
                prepared_free(&counter_prep)
                return -1
            prepared_free(&counter_prep)
        elif prepared_ok < 0:
            return -1
    # Lucky charm: full-array draw over the surviving hits when any charm is
    # present (NumPy consumes one die per hit row), then keep rows whose charm
    # did not save them.
    cdef int kept = 0
    cdef int charm_count = 0
    for i in range(survivor_n):
        if s_def.lucky_charm[survivors[i]]:
            charm_count += 1
    charm_rolls = <int*>malloc(survivor_n * sizeof(int))
    if charm_rolls == NULL:
        return -1
    if charm_count:
        for i in range(survivor_n):
            charm_rolls[i] = rng_draw_safe(rng, 1, 6)
    # Rewrite the surviving hits in place.  ``survivors`` is a subsequence of
    # ``hit_rows`` with multiplicity preserved, so a single ordered pass over
    # the original hits reproduces the mapping without a per-hit search.
    j = 0
    for i in range(survivor_n):
        row = survivors[i]
        while hit_rows[j] != row:
            j += 1
        if charm_count and s_def.lucky_charm[row]:
            s_def.lucky_charm[row] = 0
            if charm_rolls[i] >= 4:
                j += 1
                continue
        hit_rows[kept] = hit_rows[j]
        hit_positions[kept] = hit_positions[j]
        kept += 1
        j += 1
    free(charm_rolls)
    prepared.hit_n = kept
    free(hit_values); free(hit_strength); free(survivors); free(parried)
    return kept


# ---------------------------------------------------------------------------
# Attack pipeline (port of vectorized.resolve_attacks)
# ---------------------------------------------------------------------------

cdef inline int search_position_c(const int* active, int active_n, int row) noexcept:
    """Position of ``row`` inside the sorted active pool (searchsorted)."""
    cdef int lo = 0, hi = active_n, mid
    while lo < hi:
        mid = (lo + hi) >> 1
        if active[mid] < row:
            lo = mid + 1
        else:
            hi = mid
    return lo


cdef int resolve_attacks_c(DuelC* d, int atk_side, const int* rows, int rows_n,
                           const int16_t* attacks, const int8_t* charging,
                           StateC* s_atk, StateC* s_def, Rng* rng,
                           bint first_round, object decisions,
                           object attacker_py, str decision_prefix,
                           const int8_t* def_charges=NULL) except -1:
    # One answer per decision key and pool, the convention every optimized
    # engine in this repository follows.
    cdef FighterC* atk = &d.first.f if atk_side == 0 else &d.second.f
    cdef FighterC* defender = &d.first.f if atk_side == 1 else &d.second.f
    cdef int n = s_def.n
    cdef int i, j, k, row, m, rc = 0
    cdef int index, e, ok, maximum, any_c
    cdef int8_t* phase_cond = NULL
    cdef int* work_rows = NULL
    cdef int* remaining = NULL
    cdef int* main_rows = NULL
    cdef int* off_rows = NULL
    cdef int* main_lim = NULL
    cdef int* off_lim = NULL
    cdef int lim_total, lim_off, lim_main, orig_main, orig_off, lim_pen
    cdef PreparedC** prepared = NULL
    cdef int* prepared_n = NULL  # scalar in a pointer cell for the cleanup path
    cdef int** selected = NULL
    cdef int* selected_counts = NULL
    cdef int* best_roll = NULL
    cdef int* owner = NULL
    cdef int* second_roll = NULL
    cdef int* second_owner = NULL
    cdef int* row_occ = NULL
    cdef int* row_a1 = NULL
    cdef int* row_p1 = NULL
    cdef int* row_a2 = NULL
    cdef int* row_p2 = NULL
    cdef int* hug_rows = NULL
    cdef int* hug_a_rolls = NULL
    cdef int* hug_d_rolls = NULL
    cdef int* won_rows = NULL
    cdef int8_t** remove_flags = NULL
    cdef PreparedC tmp_prep
    cdef PreparedC* tmp_ptr = NULL
    cdef SourceC* src = NULL
    cdef SourceC onslaught_src
    cdef bint two_parries, offhand, use_off, any_charging
    cdef int n_bull = 0, n_body = 0, n_main = 0, n_off = 0, surv_n
    cdef int prepared_count = 0, max_prepared = 0, n_hug = 0, n_won = 0
    cdef int remaining_n = rows_n
    cdef dict cache = {}
    cdef str attack_key
    cdef bint defences_resolved = 0
    cdef PreparedC bull_prep
    cdef PreparedC hug_prep
    cdef int* bh_values = NULL
    cdef int* bh_strength = NULL
    cdef int* bh_surv = NULL
    cdef int* bh_parried = NULL
    cdef int8_t* bh_charm = NULL
    try:
        """One close-combat phase for one fighter, port of resolve_attacks."""
        if rows_n == 0:
            return 0
        phase_cond = <int8_t*>malloc(n * sizeof(int8_t))
        work_rows = <int*>malloc(n * sizeof(int))
        remaining = <int*>malloc(rows_n * sizeof(int))
        main_rows = <int*>malloc(n * sizeof(int))
        off_rows = <int*>malloc(n * sizeof(int))
        main_lim = <int*>malloc(n * sizeof(int))
        off_lim = <int*>malloc(n * sizeof(int))
        if (phase_cond == NULL or work_rows == NULL or remaining == NULL
                or main_rows == NULL or off_rows == NULL
                or main_lim == NULL or off_lim == NULL):
            rc = -1
            return rc
        memcpy(phase_cond, s_def.condition, n)
        remaining_n = 0
        for i in range(rows_n):
            row = rows[i]
            # The Honourable strike nothing at a foe already Knocked Down or
            # Stunned: the whole pool is skipped before any attack resolves,
            # so a stunned foe is not finished either (``modular/pools.py``).
            if atk.main.honorable and (phase_cond[row] == KNOCKED_DOWN
                                       or phase_cond[row] == STUNNED):
                continue
            # The immediate finish of a phase-start-stunned defender is part
            # of resolving an attack: a pool whose every attack is suppressed
            # (Stupidity, burning) resolves nothing and leaves him Stunned.
            if phase_cond[row] == STUNNED and attacks[row] > 0:
                s_def.condition[row] = OUT
            remaining[remaining_n] = row
            remaining_n += 1
        # Bull-charge reaction (first round only).
        if first_round:
            for i in range(remaining_n):
                row = remaining[i]
                if charging[row] and atk.bull_charge:
                    work_rows[n_bull] = row
                    n_bull += 1
            if n_bull and not decide_c(decisions, decision_prefix + ".bull-charge", attacker_py):
                n_bull = 0
            if n_bull:
                src = &d.first.bull if atk_side == 0 else &d.second.bull
                ok = prepare_attack_c(atk, defender, src, work_rows, n_bull, charging,
                                      s_atk, s_def, rng, first_round, &bull_prep)
                if ok < 0:
                    rc = -1
                    return rc
                if ok > 0:
                    m = 0
                    for i in range(bull_prep.hit_n):
                        row = bull_prep.hit_rows[i]
                        if s_def.condition[row] != OUT:
                            bull_prep.hit_rows[m] = row
                            bull_prep.hit_positions[m] = bull_prep.hit_positions[i]
                            m += 1
                    if m:
                        bh_values = <int*>malloc(m * sizeof(int))
                        bh_strength = <int*>malloc(m * sizeof(int))
                        bh_surv = <int*>malloc(m * sizeof(int))
                        bh_parried = <int*>malloc(m * sizeof(int))
                        if (bh_values == NULL or bh_strength == NULL
                                or bh_surv == NULL or bh_parried == NULL):
                            free(bh_values); free(bh_strength)
                            free(bh_surv); free(bh_parried)
                            prepared_free(&bull_prep)
                            rc = -1
                            return rc
                        for i in range(m):
                            bh_values[i] = bull_prep.rolls[bull_prep.hit_positions[i]]
                            bh_strength[i] = bull_prep.strength[bull_prep.hit_positions[i]]
                        surv_n = parry_resolve_c(defender, src, bull_prep.hit_rows, m,
                                                 bh_values, bh_strength, s_def, rng,
                                                 NULL, 0, 0, bh_surv, bh_parried)
                        if surv_n < 0:
                            free(bh_values); free(bh_strength)
                            free(bh_surv); free(bh_parried)
                            prepared_free(&bull_prep)
                            rc = -1
                            return rc
                        if surv_n:
                            bh_charm = <int8_t*>malloc(surv_n * sizeof(int8_t))
                            if bh_charm == NULL:
                                free(bh_values); free(bh_strength)
                                free(bh_surv); free(bh_parried)
                                prepared_free(&bull_prep)
                                rc = -1
                                return rc
                            # Full-array charm draw (one roll per surviving hit).
                            for i in range(surv_n):
                                bh_charm[i] = <int8_t>rng_draw_safe(rng, 1, 6)
                            k = 0
                            for i in range(surv_n):
                                row = bh_surv[i]
                                if s_def.lucky_charm[row]:
                                    s_def.lucky_charm[row] = 0
                                    if bh_charm[i] >= 4:
                                        continue
                                bh_surv[k] = row
                                k += 1
                            surv_n = k
                            free(bh_charm)
                        for i in range(surv_n):
                            row = bh_surv[i]
                            if s_def.condition[row] == STANDING:
                                s_def.condition[row] = KNOCKED_DOWN
                        free(bh_values); free(bh_strength)
                        free(bh_surv); free(bh_parried)
                    prepared_free(&bull_prep)
                # Remove the bull-charge rows from the remaining pool.
                k = 0
                j = 0
                for i in range(remaining_n):
                    row = remaining[i]
                    while j < n_bull and work_rows[j] < row:
                        j += 1
                    if j < n_bull and work_rows[j] == row:
                        continue
                    remaining[k] = row
                    k += 1
                remaining_n = k
        # Maximum attack count over the remaining rows.
        maximum = 0
        for i in range(remaining_n):
            row = remaining[i]
            if attacks[row] > maximum:
                maximum = attacks[row]
        # Prepared-attack pool (allocated before the body-slam reaction so the
        # reaction can join the pool, mirroring NumPy's prepared_attacks list).
        max_prepared = maximum * 2 + atk.extra_count + 2
        prepared = <PreparedC**>malloc(max_prepared * sizeof(PreparedC*))
        selected = <int**>malloc(max_prepared * sizeof(int*))
        selected_counts = <int*>malloc(max_prepared * sizeof(int))
        if prepared == NULL or selected == NULL or selected_counts == NULL:
            rc = -1
            return rc
        for i in range(max_prepared):
            prepared[i] = NULL
            selected[i] = NULL
            selected_counts[i] = 0
        # Body-slam reaction (first round only).
        if first_round:
            for i in range(remaining_n):
                row = remaining[i]
                if charging[row] and atk.body_slam:
                    work_rows[n_body] = row
                    n_body += 1
            if n_body and not decide_c(decisions, decision_prefix + ".body-slam", attacker_py):
                n_body = 0
            if n_body:
                src = &d.first.body if atk_side == 0 else &d.second.body
                ok = prepare_attack_c(atk, defender, src, work_rows, n_body, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep,
                                  decisions, decision_prefix + ".attack." + str(prepared_count),
                                  cache, attacker_py, def_charges)
                if ok < 0:
                    rc = -1
                    return rc
                if ok > 0:
                    tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                    if tmp_ptr == NULL:
                        prepared_free(&tmp_prep)
                        rc = -1
                        return rc
                    tmp_ptr[0] = tmp_prep
                    prepared[prepared_count] = tmp_ptr
                    prepared_count += 1
                k = 0
                j = 0
                for i in range(remaining_n):
                    row = remaining[i]
                    while j < n_body and work_rows[j] < row:
                        j += 1
                    if j < n_body and work_rows[j] == row:
                        continue
                    remaining[k] = row
                    k += 1
                remaining_n = k
        # A hampered hand (Kusari-kama) removes that hand's weapon from the
        # allocation, keeping one attack (``vectorized._attacks`` port of
        # ``modular/pools.py``).  Rows without a penalty keep the legacy
        # index allocation below (``main_lim`` -1).
        for i in range(remaining_n):
            row = remaining[i]
            main_lim[row] = -1
            off_lim[row] = 0
            if ((s_atk.hampered_main[row] or s_atk.hampered_off[row]
                    or s_atk.attack_penalty[row])
                    and not atk.main_pistol and not atk.off_pistol):
                lim_total = attacks[row]
                lim_off = 1 if (atk.off_hand_attacks and atk.off_present != 0
                                and lim_total > 1) else 0
                lim_main = lim_total - lim_off
                orig_main = lim_main
                orig_off = lim_off
                if s_atk.hampered_main[row] + s_atk.hampered_off[row] > 0:
                    lim_pen = s_atk.hampered_main[row]
                else:
                    lim_pen = s_atk.attack_penalty[row]
                lim_main -= lim_pen
                if lim_main < 0:
                    lim_main = 0
                lim_off -= s_atk.hampered_off[row]
                if lim_off < 0:
                    lim_off = 0
                if lim_main + lim_off == 0 and lim_total > 0:
                    if orig_main > 0:
                        lim_main = 1
                    elif orig_off > 0:
                        lim_off = 1
                main_lim[row] = lim_main
                off_lim[row] = lim_off
        # Weapon allocation over the attack pool.
        for index in range(maximum):
            m = 0
            for i in range(remaining_n):
                row = remaining[i]
                # The blow the electrical touch forfeited is never allocated.
                if (((attacks[row] if main_lim[row] < 0 else main_lim[row] + off_lim[row]) > index)
                        and s_def.condition[row] != OUT
                        and s_atk.electrical_forfeit[row] != index):
                    work_rows[m] = row
                    m += 1
            if m == 0:
                continue
            offhand = (atk.off_hand_attacks and atk.off_present != 0
                       and (first_round or not atk.main_pistol))
            n_main = 0
            n_off = 0
            for i in range(m):
                row = work_rows[i]
                if atk.main_pistol:
                    use_off = offhand and (not first_round or index > 0)
                elif main_lim[row] >= 0:
                    use_off = offhand and index >= main_lim[row]
                else:
                    use_off = offhand and index == attacks[row] - 1
                    if atk.off_pistol and not first_round:
                        use_off = 0
                if use_off:
                    off_rows[n_off] = row
                    n_off += 1
                else:
                    main_rows[n_main] = row
                    n_main += 1
            src = &atk.unpredictable if (index == 0 and atk.has_unpredictable) else &atk.main
            if not first_round and atk.main_pistol:
                # Match phase_equipment(): pistol is removed after first
                # round, then the other hand is promoted only when it can
                # provide attacks. Otherwise the fighter uses the compiled
                # unarmed fallback.
                src = &atk.off if (atk.off_present and atk.off_hand_attacks) else &atk.unarmed
            src.first_of_pool = index == 0
            ok = prepare_attack_c(atk, defender, src, main_rows, n_main, charging, s_atk,
                                  s_def, rng, first_round, &tmp_prep, decisions,
                                  decision_prefix + ".attack." + str(prepared_count),
                                  cache, attacker_py, def_charges)
            if ok < 0:
                rc = -1
                return rc
            if ok > 0:
                tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                if tmp_ptr == NULL:
                    prepared_free(&tmp_prep)
                    rc = -1
                    return rc
                tmp_ptr[0] = tmp_prep
                prepared[prepared_count] = tmp_ptr
                prepared_count += 1
            if not first_round and atk.main_pistol:
                # Promoted off-hand weapon is already represented by the main
                # source above; it must not be prepared a second time.
                n_off = 0
            if offhand:
                ok = prepare_attack_c(atk, defender, &atk.off, off_rows, n_off, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep,
                                  decisions, decision_prefix + ".attack." + str(prepared_count),
                                  cache, attacker_py, def_charges)
                if ok < 0:
                    rc = -1
                    return rc
                if ok > 0:
                    tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                    if tmp_ptr == NULL:
                        prepared_free(&tmp_prep)
                        rc = -1
                        return rc
                    tmp_ptr[0] = tmp_prep
                    prepared[prepared_count] = tmp_ptr
                    prepared_count += 1
        # Extra attacks (Horned One stays home unless any remaining row charged).
        for e in range(atk.extra_count):
            src = &atk.extras[e]
            if src.horned_one:
                any_charging = 0
                for i in range(remaining_n):
                    if charging[remaining[i]]:
                        any_charging = 1
                        break
                if not any_charging:
                    continue
            ok = prepare_attack_c(atk, defender, src, remaining, remaining_n, charging,
                                  s_atk, s_def, rng, first_round, &tmp_prep,
                                  decisions, decision_prefix + ".attack." + str(prepared_count),
                                  cache, attacker_py, def_charges)
            if ok < 0:
                rc = -1
                return rc
            if ok > 0:
                tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                if tmp_ptr == NULL:
                    prepared_free(&tmp_prep)
                    rc = -1
                    return rc
                tmp_ptr[0] = tmp_prep
                prepared[prepared_count] = tmp_ptr
                prepared_count += 1
        # The Giggle Juice spray replaces one allocated blow of the pool,
        # once per battle, at the position its bearer names.
        if atk.giggle_juice_spray and decisions is not None and prepared_count:
            n_main = 0
            for i in range(remaining_n):
                if not s_atk.giggle_juice_used[remaining[i]]:
                    n_main = 1
                    break
            if n_main and decide_cached_c(
                    decisions, cache, decision_prefix + ".giggle-juice-attack.0",
                    attacker_py):
                for i in range(remaining_n):
                    s_atk.giggle_juice_used[remaining[i]] = 1
                tmp_prep = prepared[0][0]
                prepared_free(prepared[0])
                src = &d.first.giggle if atk_side == 0 else &d.second.giggle
                ok = prepare_attack_c(atk, defender, src, main_rows, 0, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep)
                n_main = 0
                for i in range(remaining_n):
                    main_rows[n_main] = remaining[i]
                    n_main += 1
                ok = prepare_attack_c(atk, defender, src, main_rows, n_main, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep,
                                      decisions, decision_prefix + ".attack.0",
                                      cache, attacker_py, def_charges)
                if ok < 0:
                    rc = -1
                    return rc
                tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                if tmp_ptr == NULL:
                    if ok > 0:
                        prepared_free(&tmp_prep)
                    rc = -1
                    return rc
                if ok > 0:
                    tmp_ptr[0] = tmp_prep
                else:
                    memset(tmp_ptr, 0, sizeof(PreparedC))
                prepared[0] = tmp_ptr
        # Ravening Onslaught: a natural six in the prepared pool generates
        # another blow of that same weapon, which may itself generate more.
        if atk.ravening_onslaught:
            e = 0
            while e < prepared_count and prepared_count < max_prepared:
                tmp_prep = prepared[e][0]
                n_main = 0
                for i in range(tmp_prep.hit_n):
                    if tmp_prep.rolls[tmp_prep.hit_positions[i]] == 6:
                        main_rows[n_main] = tmp_prep.hit_rows[i]
                        n_main += 1
                e += 1
                if n_main == 0:
                    continue
                # ``prepare_attack_c`` clears its output before copying the
                # source, so the source must not live inside ``tmp_prep``.
                onslaught_src = tmp_prep.src
                ok = prepare_attack_c(atk, defender, &onslaught_src, main_rows, n_main,
                                      charging, s_atk, s_def, rng, first_round, &tmp_prep,
                                      decisions,
                                      decision_prefix + ".attack." + str(prepared_count),
                                      cache, attacker_py, def_charges)
                if ok < 0:
                    rc = -1
                    return rc
                if ok > 0:
                    tmp_ptr = <PreparedC*>malloc(sizeof(PreparedC))
                    if tmp_ptr == NULL:
                        prepared_free(&tmp_prep)
                        rc = -1
                        return rc
                    tmp_ptr[0] = tmp_prep
                    prepared[prepared_count] = tmp_ptr
                    prepared_count += 1
        # Selection: the highest one or two hits per duel row across the pool.
        best_roll = <int*>malloc(n * sizeof(int))
        owner = <int*>malloc(n * sizeof(int))
        if best_roll == NULL or owner == NULL:
            rc = -1
            return rc
        for i in range(n):
            best_roll[i] = -1
            owner[i] = -1
        two_parries = defender.parry_capacity == 2
        if two_parries:
            second_roll = <int*>malloc(n * sizeof(int))
            second_owner = <int*>malloc(n * sizeof(int))
            if second_roll == NULL or second_owner == NULL:
                rc = -1
                return rc
            for i in range(n):
                second_roll[i] = -1
                second_owner[i] = -1
        for index in range(prepared_count):
            tmp_prep = prepared[index][0]
            for i in range(tmp_prep.hit_n):
                row = tmp_prep.hit_rows[i]
                j = search_position_c(tmp_prep.active, tmp_prep.active_n, row)
                any_c = tmp_prep.rolls[j]
                # ``selected`` already encodes highest-hit ownership. Native
                # must use same membership for every selected row; natural-six
                # handling only removes that row from a single-parry pool.
                # Mirror the modular oracle's offer-from-the-highest-downwards.
                # A natural six closes this defender's single-parry capacity
                # for the whole attack pool. It cannot be replaced by a lower
                # hit. With two parries, lower hits remain eligible.
                if (any_c == 6 and not defender.parry_can_parry_six):
                    if not two_parries:
                        s_def.parry_remaining[row] = 0
                    continue
                # A hit that cannot be parried (a cannot-be-parried effect or
                # strength >= 2x the defender's strength) does not own a slot.
                if (tmp_prep.src.effect.v[<int>F_CANNOT_BE_PARRIED]
                        or tmp_prep.strength[j] >= 2 * s_def.strength[row]):
                    continue
                if any_c > best_roll[row]:
                    if two_parries:
                        second_roll[row] = best_roll[row]
                        second_owner[row] = owner[row]
                    best_roll[row] = any_c
                    owner[row] = index
                elif two_parries and any_c > second_roll[row]:
                    second_roll[row] = any_c
                    second_owner[row] = index
        for index in range(prepared_count):
            k = 0
            for i in range(n):
                if owner[i] == index or (two_parries and second_owner[i] == index):
                    work_rows[k] = i
                    k += 1
            if k:
                selected[index] = <int*>malloc(k * sizeof(int))
                if selected[index] == NULL:
                    rc = -1
                    return rc
                memcpy(selected[index], work_rows, k * sizeof(int))
                selected_counts[index] = k
        # Bear Hug: pre-resolve defences, then replace one hit pair per row with
        # the opposed Strength test.
        if atk.bear_hug and prepared_count:
            for index in range(prepared_count):
                surv_n = apply_hit_defences_c(d, atk_side, &prepared[index][0].src,
                                              prepared[index], charging, s_atk,
                                              s_def, rng, selected[index],
                                              selected_counts[index], 1, decisions,
                                              decision_prefix + ".attack." + str(index),
                                              cache, None)
                if surv_n < 0:
                    rc = -1
                    return rc
                prepared[index][0].hit_n = surv_n
            row_occ = <int*>malloc(n * sizeof(int))
            row_a1 = <int*>malloc(n * sizeof(int))
            row_p1 = <int*>malloc(n * sizeof(int))
            row_a2 = <int*>malloc(n * sizeof(int))
            row_p2 = <int*>malloc(n * sizeof(int))
            hug_rows = <int*>malloc(n * sizeof(int))
            remove_flags = <int8_t**>malloc(prepared_count * sizeof(int8_t*))
            if (row_occ == NULL or row_a1 == NULL or row_p1 == NULL
                    or row_a2 == NULL or row_p2 == NULL or hug_rows == NULL
                    or remove_flags == NULL):
                rc = -1
                return rc
            for i in range(n):
                row_occ[i] = 0
                row_a1[i] = -1
                row_p1[i] = -1
                row_a2[i] = -1
                row_p2[i] = -1
            for index in range(prepared_count):
                tmp_prep = prepared[index][0]
                remove_flags[index] = <int8_t*>calloc(tmp_prep.hit_n, sizeof(int8_t)) if tmp_prep.hit_n else NULL
                for i in range(tmp_prep.hit_n):
                    row = tmp_prep.hit_rows[i]
                    if row_occ[row] == 0:
                        row_a1[row] = index
                        row_p1[row] = i
                    elif row_occ[row] == 1:
                        row_a2[row] = index
                        row_p2[row] = i
                    row_occ[row] += 1
            for row in range(n):
                if row_occ[row] < 2:
                    continue
                if not decide_c(decisions, decision_prefix + ".bear-hug", {"row": row}):
                    continue
                remove_flags[row_a1[row]][row_p1[row]] = 1
                remove_flags[row_a2[row]][row_p2[row]] = 1
                hug_rows[n_hug] = row
                n_hug += 1
            for index in range(prepared_count):
                tmp_prep = prepared[index][0]
                k = 0
                for i in range(tmp_prep.hit_n):
                    if remove_flags[index][i]:
                        continue
                    tmp_prep.hit_rows[k] = tmp_prep.hit_rows[i]
                    tmp_prep.hit_positions[k] = tmp_prep.hit_positions[i]
                    k += 1
                # Write the shrunken count through the pointer: ``tmp_prep``
                # is a by-value copy, so assigning its ``hit_n`` would leave
                # the consumed hits in the pool (and duplicate shifted rows).
                prepared[index][0].hit_n = k
            if n_hug:
                hug_a_rolls = <int*>malloc(n_hug * sizeof(int))
                hug_d_rolls = <int*>malloc(n_hug * sizeof(int))
                won_rows = <int*>malloc(n_hug * sizeof(int))
                if hug_a_rolls == NULL or hug_d_rolls == NULL or won_rows == NULL:
                    rc = -1
                    return rc
                for i in range(n_hug):
                    hug_a_rolls[i] = rng_draw_safe(rng, 1, 6)
                for i in range(n_hug):
                    hug_d_rolls[i] = rng_draw_safe(rng, 1, 6)
                n_won = 0
                for i in range(n_hug):
                    row = hug_rows[i]
                    if (hug_a_rolls[i] + s_atk.strength[row]
                            >= hug_d_rolls[i] + s_def.strength[row]):
                        won_rows[n_won] = row
                        n_won += 1
                if n_won:
                    src = &d.first.hug if atk_side == 0 else &d.second.hug
                    ok = prepare_attack_c(atk, defender, src, won_rows, n_won, charging,
                                          s_atk, s_def, rng, first_round, &hug_prep)
                    if ok < 0:
                        rc = -1
                        return rc
                    if ok > 0:
                        if resolve_weapon_c(d, atk_side, src, &hug_prep, charging,
                                            s_atk, s_def, rng, first_round,
                                            phase_cond, 1, NULL, 0, 0, decisions,
                                            1, attacker_py, None, None) < 0:
                            prepared_free(&hug_prep)
                            rc = -1
                            return rc
                        prepared_free(&hug_prep)
            defences_resolved = 1
        for index in range(prepared_count):
            tmp_prep = prepared[index][0]
            # Prepared hits keep phase-start eligibility. A later hit in the
            # same pool still runs its wound/injury pipeline after an earlier
            # hit changes the defender to STUNNED; only a defender already
            # STUNNED when the pool starts is an immediate finish. This matches
            # modular.pools._resolve_attack_pool and the NumPy driver.
            attack_key = decision_prefix + ".attack." + str(index)
            if resolve_weapon_c(d, atk_side, &tmp_prep.src, prepared[index], charging,
                                s_atk, s_def, rng, first_round, phase_cond,
                                defences_resolved, selected[index],
                                selected_counts[index], 1, decisions, 1,
                                attacker_py, None, None, attack_key, cache) < 0:
                rc = -1
                return rc
            # Force of Will rescue is an immediate response to going Out of
            # Action, before the next prepared hit resolves (the oracle's
            # _react_to_wound contract).  Rescuing only after the whole pool
            # lets a rescued fighter skip the remaining attacks of the same
            # pool and inflated the FoW side's survival.
            if rescue_force_of_will_c(defender, s_def, rows,
                                      rows_n, rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(atk, s_atk, rows,
                                      rows_n, rng) < 0:
                rc = -1
                return rc
    finally:
        if prepared is not NULL:
            for i in range(max_prepared):
                if prepared[i] is not NULL:
                    prepared_free(prepared[i])
                    free(prepared[i])
            free(prepared)
        if selected is not NULL:
            for i in range(max_prepared):
                free(selected[i])
            free(selected)
        free(selected_counts)
        free(phase_cond)
        free(work_rows)
        free(remaining)
        free(main_rows)
        free(off_rows)
        free(main_lim)
        free(off_lim)
        free(best_roll)
        free(owner)
        free(second_roll)
        free(second_owner)
        free(row_occ)
        free(row_a1)
        free(row_p1)
        free(row_a2)
        free(row_p2)
        free(hug_rows)
        free(hug_a_rolls)
        free(hug_d_rolls)
        free(won_rows)
        if remove_flags is not NULL:
            for i in range(prepared_count):
                free(remove_flags[i])
            free(remove_flags)
    return rc


# ---------------------------------------------------------------------------
# Round loop (port of vectorized._simulate_batch_core)
# ---------------------------------------------------------------------------

cdef inline int priority_row_c(FighterC* f, bint first_round, int charging_row,
                               int charged_row, int stood_row,
                               bint woven_mist=0) noexcept:
    """Port of vectorized.priority (per row)."""
    cdef int value = f.weapon_priority + f.priority_global
    if f.strongman:
        value = f.priority_global
    if f.long_boat_hook and not first_round:
        value = f.priority_global
    # The spear's Strike First only applies in the first turn of hand-to-hand
    # combat, mirroring the long-boat-hook's first-round scope.
    if f.spear and not first_round:
        value = f.priority_global
    if f.strike_skinks_always:
        value = 20
    if f.trident and charged_row and value < 1:
        value = 1
    if first_round:
        if (f.weapon_priority >= 0 or f.strongman) and value < charging_row:
            value = charging_row
        if f.strike_skinks_first:
            value = 20
        if f.lightning_reflexes and charged_row and value < 1:
            value = 1
    if not f.always_strikes_first and stood_row:
        value = -1
    # Woven Mist lifts its dancer to at least the first tier.
    if woven_mist and value < 1:
        value = 1
    if f.frantic:
        # Frantic explicitly ignores weapon penalties and ordinary Initiative.
        value = 30
    return value


cdef inline int effective_initiative_c(FighterC* f, StateC* s, int row) noexcept:
    """Port of vectorized.effective_initiative (per row)."""
    cdef int value = (s.initiative[row] + f.initiative_bonus_total
                      + s.crimson_initiative[row] - s.initiative_penalty[row])
    if value < s.initiative_floor[row]:
        value = s.initiative_floor[row]
    return value


cdef inline FighterC* fighter_at(TablesC* t, int side, StateC* s, int row) noexcept:
    """The compiled fighter one row is simulated with (its projection)."""
    return &t.sides[side][s.projection[row]].f


cdef int attack_count_c(TablesC* t, int side, StateC* s, const int8_t* charging,
                        const int8_t* player_turn, bint first_round,
                        int16_t* out, int count, Rng* rng) except -1:
    """Port of vectorized.attack_count (state.attacks as base_attacks).

    Each row reads the fighter of its own projection, so a row whose
    equipment or shape diverged from the printed fighter is counted with the
    scalars of that projection.
    """
    cdef FighterC* f
    cdef int i, result, extra
    for i in range(count):
        f = fighter_at(t, side, s, i)
        # The pool is the first operation of the round that reads Attacks.
        require_characteristic_c(s, f, i, 4, rng, count)
        extra = f.extra_weapon_attack
        if f.fist_penalized:
            extra = 0
        result = s.attacks[i]
        if f.sabretusk_charge and charging[i]:
            # The printed clause replaces A1 with A2; it is not a generic +1.
            result = 2
        result += f.attacks_bonus_total
        if s.combat_charge_active[i]:
            result += 1
        if f.maddened and s.wounds[i] < f.w:
            result += 1
        if f.charge_attacks_bonus and charging[i]:
            result += f.charge_attacks_bonus
        if first_round and f.first_round_charge_attacks_bonus and charging[i]:
            result += f.first_round_charge_attacks_bonus
        if f.fist_penalized:
            result = 1
        if f.unarmed_bonus:
            result += 1
        if f.art_bonus:
            result += 1
        if f.inspiring and player_turn[i]:
            result += 1
        if first_round:
            result += f.first_round_attacks_bonus
        # Doubling is gated on the per-row frenzy state only (a knockdown
        # clears ``s.frenzy`` and the oracle never restores it).
        if s.frenzy[i]:
            result *= 2
        if first_round and f.ferocious_charge and charging[i]:
            result *= 2
        result += extra
        # The oracle re-applies the unarmed cap after Frenzy doubling and the
        # extra-weapon attack (``phases.build_attacks``: ``min(attacks, 1)``).
        if f.fist_penalized and result > 1:
            result = 1
        if f.vomit or f.sweep_main:
            result = 1
        if f.main_pistol and first_round:
            if f.off_pistol and f.off_hand_attacks:
                # Both pistols fire during the opening round.
                result = 2
            elif not f.off_hand_attacks:
                result = 1
        elif f.main_pistol and not first_round:
            # A spent main pistol leaves the compiled unarmed fallback, which
            # receives its normal attack count.
            if f.off_hand_attacks:
                result -= 1
                if result < 0:
                    result = 0
            else:
                result = 1
        elif f.off_pistol and not first_round and f.off_hand_attacks:
            result -= 1
            if result < 0:
                result = 0
        if first_round and charging[i] and f.body_bull_anvil:
            result = 1
        if f.death_blow:
            result = 1
        if f.energy_focus_active:
            result -= f.energy_focus_attacks
            if result < 0:
                result = 0
        # Per-turn Attack grants (the Rousing Sermon, the Black Hunger, the
        # Storm of Blades); Woven Mist trades one attack for its priority.
        result += s.attacks_bonus_row[i]
        result -= s.dance_woven_mist[i]
        result -= s.pool_loss_row[i]
        result -= s.attack_penalty[i]
        if result < 0:
            result = 0
        out[i] = <int16_t>result
    return 0


cdef int init_state_c(FighterC* f, StateC* s, int count, Rng* rng) except -1:
    """Port of ``modular.state.initialize_fighter`` for ``count`` rows.

    The columns ``state_alloc`` zeroed keep their zero; this writes the facts
    the oracle derives, in the oracle's order: the printed profile, the
    variable characteristics (left unrolled under Inconsistency, whose values
    are drawn by the operation that first reads them), the Crimson Shade die,
    the supplied condition deltas, the poet's inspiration, the supplied
    Disability result, the Guiding Dream die and the duel-start conditions.
    """
    cdef int i, d, k, dice, sides, bonus, total, stat, delta, before, value
    cdef int16_t* cols[5]
    cols[0] = s.weapon_skill
    cols[1] = s.strength
    cols[2] = s.toughness
    cols[3] = s.initiative
    cols[4] = s.attacks
    for i in range(count):
        s.weapon_skill[i] = <int16_t>f.ws
        s.strength[i] = <int16_t>f.s
        s.toughness[i] = <int16_t>(f.t + f.toughness_bonus)
        s.initiative[i] = <int16_t>f.ini
        s.attacks[i] = <int16_t>f.a
    if not f.inconsistency:
        for k in range(f.random_characteristics_count):
            stat = f.random_characteristics[k][0]
            dice = f.random_characteristics[k][1]
            sides = f.random_characteristics[k][2]
            bonus = f.random_characteristics[k][3]
            for i in range(count):
                total = bonus
                for d in range(dice):
                    total += rng_draw_safe(rng, 1, sides)
                cols[stat][i] = <int16_t>total
    # Crimson Shade: the oracle adds D3 to the Initiative value; the core
    # keeps the die in its own column, read by ``effective_initiative_c``.
    if f.crimson_shade and not f.initiative_missing:
        for i in range(count):
            s.crimson_initiative[i] = <int8_t>rng_draw_safe(rng, 1, 3)
    for k in range(f.condition_delta_count):
        stat = f.condition_deltas[k][0]
        delta = f.condition_deltas[k][1]
        if stat == 3 and f.initiative_missing:
            # An absent characteristic has no base to modify.
            continue
        for i in range(count):
            before = cols[stat][i]
            value = before + delta
            if not f.inconsistency and value < 1:
                value = 1
            cols[stat][i] = <int16_t>value
            if f.condition_deltas[k][2]:
                if stat == 1:
                    s.backley_strength[i] = <int8_t>(s.backley_strength[i] + before - value)
                elif stat == 3:
                    s.backley_initiative[i] = <int8_t>(s.backley_initiative[i] + before - value)
    if f.poetry_inspired:
        for i in range(count):
            s.weapon_skill[i] = <int16_t>(s.weapon_skill[i] + 1)
    for i in range(count):
        # The permanent table result is supplied at construction and already
        # priced into the profile; the duel records it and rolls nothing.
        s.disability[i] = <int8_t>f.supplied_disability
    if f.guiding_dream:
        for i in range(count):
            s.guiding_dream_result[i] = <int8_t>rng_draw_safe(rng, 1, 6)
    if f.guiding_dream_nominated:
        for i in range(count):
            if s.guiding_dream_result[i] == 4 or s.guiding_dream_result[i] == 5:
                s.strength[i] = <int16_t>(s.strength[i] + 1)
    for i in range(count):
        s.wounds[i] = <int16_t>f.starting_wounds
        s.starting_wounds[i] = <int16_t>f.starting_wounds
        s.condition[i] = KNOCKED_DOWN if f.netted_init else STANDING
        s.netted[i] = 1 if f.netted_init else 0
        s.initiative_floor[i] = 1
        s.initiative_missing[i] = 1 if f.initiative_missing else 0
        s.lucky_charm[i] = 1 if f.lucky_charm_init else 0
        s.parry_remaining[i] = <int8_t>f.parry_capacity
        s.stupidity_failed[i] = 1 if f.stupidity_failed_init else 0
        s.massively_built_lost_turn[i] = 1 if f.massively_built_init else 0
        s.danse_macabre_controlled[i] = 1 if f.danse_macabre_init else 0
        s.hillman_wolf[i] = 1 if f.hillman_wolf_init else 0
        s.mutation_tail[i] = -1
        s.projection[i] = 0
        # Psychology immunity suppresses the initial Frenzy; the two explicit
        # exceptions are persistent Frenzy and Snorri's supplied Frenzy.
        s.frenzy[i] = 1 if (f.persistent_frenzy or (
            (f.frenzy_init or (f.guiding_dream_nominated and s.guiding_dream_result[i] == 6))
            and not f.netted_init and f.frenzy_permitted)) else 0
        if f.inconsistency:
            # The supplied fixed deltas an Inconsistency profile keeps for the
            # whole duel: current value minus the printed characteristic.
            s.random_modifiers[0 * count + i] = <int16_t>(s.weapon_skill[i] - f.ws)
            s.random_modifiers[1 * count + i] = <int16_t>(s.strength[i] - f.s)
            s.random_modifiers[2 * count + i] = <int16_t>(s.toughness[i] - f.t)
            s.random_modifiers[3 * count + i] = <int16_t>(s.initiative[i] - f.ini)
            s.random_modifiers[4 * count + i] = <int16_t>(s.attacks[i] - f.a)
    return 0


cdef void refresh_random_characteristics_c(FighterC* f, StateC* s,
                                           const int* rows, int rows_n,
                                           Rng* rng) except *:
    """Refresh Condemned/Inconsistency WS, S, T and A per later turn."""
    cdef int key, i, d, total, stat, dice, sides, bonus
    cdef bint has_ws = 0
    cdef bint has_s = 0
    cdef bint has_t = 0
    cdef bint has_a = 0
    for key in range(f.random_characteristics_count):
        stat = f.random_characteristics[key][0]
        if stat == 0: has_ws = 1
        elif stat == 1: has_s = 1
        elif stat == 2: has_t = 1
        elif stat == 4: has_a = 1
    if not (has_ws and has_s and has_t and has_a):
        return
    for key in range(f.random_characteristics_count):
        stat = f.random_characteristics[key][0]
        dice = f.random_characteristics[key][1]
        sides = f.random_characteristics[key][2]
        bonus = f.random_characteristics[key][3]
        for i in range(rows_n):
            total = bonus
            for d in range(dice):
                total += rng_draw_safe(rng, 1, sides)
            if stat == 0: s.weapon_skill[rows[i]] = <int16_t>total
            elif stat == 1: s.strength[rows[i]] = <int16_t>total
            elif stat == 2: s.toughness[rows[i]] = <int16_t>(total + f.toughness_bonus)
            elif stat == 4: s.attacks[rows[i]] = <int16_t>total


cdef int netter_charge_c(FighterC* netter, FighterC* target, const int* rows,
                         int rows_n, StateC* target_state, Rng* rng) except -1:
    """Port of vectorized._resolve_netter_charge (no state needed from netter)."""
    if rows_n == 0 or not netter.netter:
        return 0
    cdef int target_score = 7 - netter.ballistic_skill
    if target_score < 2:
        target_score = 2
    cdef int* targets = <int*>malloc(rows_n * sizeof(int))
    cdef int8_t* hits = <int8_t*>malloc(rows_n * sizeof(int8_t))
    cdef int8_t* escape = <int8_t*>malloc(rows_n * sizeof(int8_t))
    if targets == NULL or hits == NULL or escape == NULL:
        free(targets); free(hits); free(escape)
        return -1
    for i in range(rows_n):
        targets[i] = target_state.strength[rows[i]]
        hits[i] = 1 if rng_draw_safe(rng, 1, 6) >= target_score else 0
    characteristic_tests_c(target, rows, rows_n, targets, rng, 0, escape)
    for i in range(rows_n):
        if hits[i] and not escape[i]:
            target_state.condition[rows[i]] = KNOCKED_DOWN
    free(targets); free(hits); free(escape)
    return 0


cdef int resolve_spines_c(DuelC* d, const int* rows, int rows_n,
                          const int8_t* charge1, const int8_t* charge2,
                          StateC* s1, StateC* s2, Rng* rng) except -1:
    """Simultaneous non-critical Spines hits at phase start (both prep first)."""
    cdef PreparedC prep1, prep2
    cdef bint have1 = 0, have2 = 0
    cdef int ok
    if d.first.f.spines:
        ok = prepare_attack_c(&d.first.f, &d.second.f, &d.first.spines, rows, rows_n,
                              charge1, s1, s2, rng, 0, &prep1)
        if ok < 0:
            return -1
        have1 = ok > 0
    if d.second.f.spines:
        ok = prepare_attack_c(&d.second.f, &d.first.f, &d.second.spines, rows, rows_n,
                              charge2, s2, s1, rng, 0, &prep2)
        if ok < 0:
            if have1:
                prepared_free(&prep1)
            return -1
        have2 = ok > 0
    if have1:
        if resolve_weapon_c(d, 0, &d.first.spines, &prep1, charge1, s1, s2, rng,
                            0, NULL, 0, NULL, 0, 0, None, 1, None, None,
                            None) < 0:
            if have2:
                prepared_free(&prep2)
            prepared_free(&prep1)
            return -1
        prepared_free(&prep1)
    if have2:
        if resolve_weapon_c(d, 1, &d.second.spines, &prep2, charge2, s2, s1, rng,
                            0, NULL, 0, NULL, 0, 0, None, 1, None, None,
                            None) < 0:
            prepared_free(&prep2)
            return -1
        prepared_free(&prep2)
    return 0


cdef int rescue_force_of_will_c(FighterC* f, StateC* s, const int* rows,
                                int rows_n, Rng* rng) except -1:
    """Port of vectorized._rescue_force_of_will."""
    if not f.force_of_will or rows_n == 0:
        return 0
    cdef int* eligible = <int*>malloc(rows_n * sizeof(int))
    cdef int* targets = <int*>malloc(rows_n * sizeof(int))
    cdef int8_t* results = <int8_t*>malloc(rows_n * sizeof(int8_t))
    if eligible == NULL or targets == NULL or results == NULL:
        free(eligible); free(targets); free(results)
        return -1
    cdef int m = 0
    for i in range(rows_n):
        row = rows[i]
        if s.condition[row] == OUT and not s.force_of_will_used[row]:
            eligible[m] = row
            m += 1
    if m:
        for i in range(m):
            s.force_of_will_used[eligible[i]] = 1
            targets[i] = s.toughness[eligible[i]]
        # Natural 6 always fails (six_always_fails=1), like the oracle and
        # the NumPy _characteristic_test default; the broken port passed 0
        # and rescued fights on a 6, inflating Force of Will survival.
        characteristic_tests_c(f, eligible, m, targets, rng, 1, results)
        for i in range(m):
            if results[i]:
                s.condition[eligible[i]] = STANDING
                s.wounds[eligible[i]] = 1
                s.force_of_will_active[eligible[i]] = 1
    free(eligible); free(targets); free(results)
    return 0


cdef int sustain_force_of_will_c(FighterC* f, StateC* s, Rng* rng,
                                 const int* rows, int rows_n) except -1:
    """Port of vectorized._sustain_force_of_will."""
    if not f.force_of_will:
        return 0
    cdef int* active = <int*>malloc(s.n * sizeof(int))
    cdef int* targets = <int*>malloc(s.n * sizeof(int))
    cdef int8_t* results = <int8_t*>malloc(s.n * sizeof(int8_t))
    if active == NULL or targets == NULL or results == NULL:
        free(active); free(targets); free(results)
        return -1
    cdef int m = 0
    if rows is NULL:
        for i in range(s.n):
            if s.force_of_will_active[i] and s.condition[i] != OUT:
                active[m] = i
                m += 1
    else:
        for i in range(rows_n):
            row = rows[i]
            if s.force_of_will_active[row] and s.condition[row] != OUT:
                active[m] = row
                m += 1
    if m:
        for i in range(m):
            row = active[i]
            s.force_of_will_penalty[row] = <int8_t>(s.force_of_will_penalty[row] + 1)
            targets[i] = s.toughness[row] - s.force_of_will_penalty[row]
            if targets[i] < 0:
                targets[i] = 0
        # Same contract as the rescue: natural 6 always fails and Blessed
        # Sight rerolls.  The broken port used raw ``roll > target`` with no
        # six-fails rule and no reroll, sustaining fighters that should have
        # dropped (results below hold pass=1, so removal inverts them).
        characteristic_tests_c(f, active, m, targets, rng, 1, results)
        for i in range(m):
            if not results[i]:
                row = active[i]
                s.condition[row] = OUT
                s.force_of_will_active[row] = 0
    free(active); free(targets); free(results)
    return 0


cdef int black_hunger_backlash_c(DuelC* d, int side, StateC* s, Rng* rng,
                                 const int* rows, int rows_n) except -1:
    """Port of vectorized._black_hunger_backlash."""
    cdef FighterC* f = &d.first.f if side == 0 else &d.second.f
    if not f.black_hunger or rows_n == 0:
        return 0
    cdef int* active = <int*>malloc(rows_n * sizeof(int))
    cdef int* hit_rows = <int*>malloc(rows_n * sizeof(int))
    cdef int8_t* hits = <int8_t*>malloc(rows_n * sizeof(int8_t))
    if active == NULL or hit_rows == NULL or hits == NULL:
        free(active); free(hit_rows); free(hits)
        return -1
    cdef int m = 0
    for i in range(rows_n):
        row = rows[i]
        if s.black_hunger_active[row] and s.condition[row] != OUT:
            active[m] = row
            m += 1
    cdef PreparedC prep
    cdef SourceC* backlash = &d.first.backlash if side == 0 else &d.second.backlash
    cdef int ok, k, index
    if m:
        for i in range(m):
            hits[i] = <int8_t>rng_draw_safe(rng, 1, 3)
        for index in range(3):
            # The oracle resolves one backlash hit at a time against the
            # live state and stops as soon as the bearer is out of action, so
            # the row set is re-filtered before every hit and no Force of
            # Will rescue runs inside the backlash.
            k = 0
            for i in range(m):
                if hits[i] > index and s.condition[active[i]] != OUT:
                    hit_rows[k] = active[i]
                    k += 1
            if k == 0:
                continue
            ok = prepare_attack_c(f, f, backlash, hit_rows, k, NULL, s, s, rng,
                                  0, &prep)
            if ok < 0:
                free(active); free(hit_rows); free(hits)
                return -1
            if ok > 0:
                if resolve_weapon_c(d, side, backlash, &prep, NULL, s, s, rng,
                                    0, NULL, 0, NULL, 0, 0, None, 1, None,
                                    None, None) < 0:
                    prepared_free(&prep)
                    free(active); free(hit_rows); free(hits)
                    return -1
                prepared_free(&prep)
    free(active); free(hit_rows); free(hits)
    # The oracle stops the sequence at OUT and only then offers its rescue.
    return rescue_force_of_will_c(f, s, rows, rows_n, rng)


cdef int resolve_fire_c(DuelC* d, int victim_side, StateC* s_victim,
                        StateC* s_opponent, Rng* rng, const int* rows,
                        int rows_n) except -1:
    """Recovery-phase fire test and S4 hit (port of vectorized._resolve_fire)."""
    cdef int* burning = <int*>malloc(s_victim.n * sizeof(int))
    if burning == NULL:
        return -1
    cdef int m = 0
    if rows is NULL:
        for i in range(s_victim.n):
            if s_victim.on_fire[i] and s_victim.condition[i] != OUT:
                burning[m] = i
                m += 1
    else:
        for i in range(rows_n):
            row = rows[i]
            if s_victim.on_fire[row] and s_victim.condition[row] != OUT:
                burning[m] = row
                m += 1
    if m == 0:
        free(burning)
        return 0
    cdef int* still = <int*>malloc(m * sizeof(int))
    cdef int8_t* extinguished = <int8_t*>malloc(m * sizeof(int8_t))
    if still == NULL or extinguished == NULL:
        free(burning); free(still); free(extinguished)
        return -1
    cdef int k = 0
    for i in range(m):
        extinguished[i] = 1 if rng_draw_safe(rng, 1, 6) >= 4 else 0
    for i in range(m):
        if extinguished[i]:
            s_victim.on_fire[burning[i]] = 0
        else:
            still[k] = burning[i]
            k += 1
    free(extinguished)
    if k == 0:
        free(burning); free(still)
        return 0
    cdef int atk_side = 1 - victim_side
    cdef FighterC* atk = &d.first.f if atk_side == 0 else &d.second.f
    cdef FighterC* defender = &d.first.f if victim_side == 0 else &d.second.f
    cdef SourceC* fire_src = &d.first.fire if atk_side == 0 else &d.second.fire
    cdef PreparedC prep
    cdef int ok = prepare_attack_c(atk, defender, fire_src, still, k, NULL,
                                   s_opponent, s_victim, rng, 0, &prep)
    if ok < 0:
        free(burning); free(still)
        return -1
    if ok > 0:
        if resolve_weapon_c(d, atk_side, fire_src, &prep, NULL, s_opponent,
                            s_victim, rng, 0, NULL, 0, NULL, 0, 0, None, 1,
                            None, None, None) < 0:
            prepared_free(&prep)
            free(burning); free(still)
            return -1
        prepared_free(&prep)
    free(burning); free(still)
    return 0


cdef int resolve_entangle_c(DuelC* d, int atk_side, const int* rows, int rows_n,
                            const int8_t* charging, StateC* s_atk, StateC* s_def,
                            Rng* rng) except -1:
    """Chained-squig entangle hit (port of the inline NumPy block)."""
    if rows_n == 0:
        return 0
    cdef FighterC* atk = &d.first.f if atk_side == 0 else &d.second.f
    cdef FighterC* defender = &d.first.f if atk_side == 1 else &d.second.f
    cdef SourceC* src = &d.first.entangle if atk_side == 0 else &d.second.entangle
    cdef PreparedC prep
    cdef int ok = prepare_attack_c(atk, defender, src, rows, rows_n, charging, s_atk,
                                   s_def, rng, 0, &prep)
    if ok < 0:
        return -1
    if ok > 0:
        if resolve_weapon_c(d, atk_side, src, &prep, charging, s_atk, s_def,
                            rng, 0, NULL, 0, NULL, 0, 0, None, 1, None, None,
                            None) < 0:
            prepared_free(&prep)
            return -1
        prepared_free(&prep)
    return 0


cdef object observe_state_c(StateC* state):
    """Copy terminal state while the native buffers still belong to the batch.

    The resource markers carry the oracle's ``resources_spent`` names, the
    same seven ``vectorized._driver._resource_observation`` publishes.
    """
    cdef int i
    cdef int n = state.n
    return (
        np.asarray([state.wounds[i] for i in range(n)], dtype=np.int16),
        np.asarray([state.condition[i] for i in range(n)], dtype=np.int8),
        (
            ("lucky-charm", np.asarray([not state.lucky_charm[i] for i in range(n)], dtype=bool)),
            ("force-of-will", np.asarray([state.force_of_will_used[i] for i in range(n)], dtype=bool)),
            ("mark-of-the-old-ones", np.asarray([state.mark_of_old_ones_used[i] for i in range(n)], dtype=bool)),
            ("luck", np.asarray([state.luck_used[i] for i in range(n)], dtype=bool)),
            ("magic-acorn", np.asarray([state.magic_acorn_used[i] for i in range(n)], dtype=bool)),
            ("rememberer", np.asarray([state.rememberer_used[i] for i in range(n)], dtype=bool)),
            ("giggle-juice", np.asarray([state.giggle_juice_used[i] for i in range(n)], dtype=bool)),
        ),
    )


# ---------------------------------------------------------------------------
# Row groups by projection pair
# ---------------------------------------------------------------------------

cdef void groups_free(GroupsC* g) noexcept:
    free(g.starts); free(g.p1); free(g.p2); free(g.rows)
    memset(g, 0, sizeof(GroupsC))


cdef int group_rows_c(StateC* s1, StateC* s2, const int* rows, int n, GroupsC* g) except -1:
    """Partition ascending ``rows`` by their (first, second) projection pair.

    Groups keep first-appearance order and every group keeps its rows
    ascending, which the attack core's position search requires.  ``s2`` may
    be NULL for a single-side operation.  A batch whose rows all keep the
    printed fighters yields exactly one group.
    """
    cdef int i, k, m, a, b
    cdef bint found
    memset(g, 0, sizeof(GroupsC))
    g.starts = <int*>malloc((n + 1) * sizeof(int))
    g.p1 = <int*>malloc((n if n > 0 else 1) * sizeof(int))
    g.p2 = <int*>malloc((n if n > 0 else 1) * sizeof(int))
    g.rows = <int*>malloc((n if n > 0 else 1) * sizeof(int))
    if g.starts == NULL or g.p1 == NULL or g.p2 == NULL or g.rows == NULL:
        groups_free(g)
        return -1
    for i in range(n):
        a = s1.projection[rows[i]]
        b = s2.projection[rows[i]] if s2 != NULL else 0
        found = 0
        for k in range(g.n_groups):
            if g.p1[k] == a and g.p2[k] == b:
                found = 1
                break
        if not found:
            g.p1[g.n_groups] = a
            g.p2[g.n_groups] = b
            g.n_groups += 1
    m = 0
    for k in range(g.n_groups):
        g.starts[k] = m
        for i in range(n):
            a = s1.projection[rows[i]]
            b = s2.projection[rows[i]] if s2 != NULL else 0
            if a == g.p1[k] and b == g.p2[k]:
                g.rows[m] = rows[i]
                m += 1
    g.starts[g.n_groups] = m
    return 0


cdef inline void view_c(TablesC* t, int p1, int p2, DuelC* v) noexcept:
    v.first = t.sides[0][p1]
    v.second = t.sides[1][p2]


# ---------------------------------------------------------------------------
# Projection tables
# ---------------------------------------------------------------------------

cdef void tables_free(TablesC* t) noexcept:
    cdef int side, i
    for side in range(2):
        for i in range(t.n[side]):
            free(t.sides[side][i])
        free(t.sides[side])
    memset(t, 0, sizeof(TablesC))


cdef int tables_add_c(TablesC* t, int side, object compiled) except -1:
    """Append one ``compile_side`` view to a side's table; returns its index."""
    cdef SideC* entry = <SideC*>calloc(1, sizeof(SideC))
    cdef SideC** grown
    cdef int new_cap
    if entry == NULL:
        return -1
    try:
        fill_side(compiled, entry)
    except Exception:
        free(entry)
        raise
    if t.n[side] == t.cap[side]:
        new_cap = 4 if t.cap[side] < 4 else t.cap[side] * 2
        grown = <SideC**>realloc(t.sides[side], new_cap * sizeof(SideC*))
        if grown == NULL:
            free(entry)
            return -1
        t.sides[side] = grown
        t.cap[side] = new_cap
    t.sides[side][t.n[side]] = entry
    t.n[side] += 1
    return t.n[side] - 1


cdef int sync_projections_c(TablesC* t, object table) except -1:
    """Mirror every ``ProjectionTable`` entry the C tables do not hold yet."""
    cdef int side, index
    for side in range(2):
        compiled = table.compiled["first" if side == 0 else "second"]
        for index in range(t.n[side], len(compiled)):
            if tables_add_c(t, side, compiled[index]) < 0:
                return -1
    return 0


# ---------------------------------------------------------------------------
# Contextual facts
# ---------------------------------------------------------------------------

cdef void context_free(ContextC* c) noexcept:
    free(c.participants); free(c.distances)
    memset(c, 0, sizeof(ContextC))


cdef int fill_context(object d, ContextC* out) except -1:
    """Fill ``ContextC`` from ``_combat_compile.compile_context``."""
    cdef int i, j, n
    cdef ParticipantC* p
    memset(out, 0, sizeof(ContextC))
    if d is None:
        return 0
    out.present = 1
    rows = d["participants"]
    n = len(rows)
    out.n = n
    out.participants = <ParticipantC*>calloc(n if n > 0 else 1, sizeof(ParticipantC))
    out.distances = <double*>malloc((n * n if n > 0 else 1) * sizeof(double))
    if out.participants == NULL or out.distances == NULL:
        context_free(out)
        return -1
    for i in range(n):
        row = rows[i]
        flags = row["flags"]
        p = &out.participants[i]
        p.side = <int>row["side"]
        p.condition = <int>row["condition"]
        p.has_leadership = row["leadership"] is not None
        p.leadership = <int>row["leadership"] if p.has_leadership else 0
        p.has_movement = row["movement"] is not None
        p.movement = <int>row["movement"] if p.has_movement else 0
        p.bands = <uint64_t>row["bands"]
        p.leader_six = _flag(flags, "mechanic.leader-six")
        p.leader_twelve = _flag(flags, "mechanic.leader-twelve")
        p.leader_four = _flag(flags, "mechanic.leader-four")
        p.dim_witted_leader = _flag(flags, "mechanic.dim-witted-leader")
        p.leader_fallback = _flag(flags, "mechanic.leader-fallback")
        p.relay_orders = _flag(flags, "mechanic.relay-orders")
        p.songster = _flag(flags, "mechanic.songster")
        p.slave_driver = _flag(flags, "mechanic.slave-driver")
        p.scourge = 1 if (flags.get("condition.scourge-armed") or flags.get("weapon.pirate-scourge")) else 0
        p.bear_handler = _flag(flags, "mechanic.bear-handler")
        p.handler_leadership = _flag(flags, "mechanic.handler-leadership")
        p.mouth_sewn = _flag(flags, "condition.mouth-sewn")
        p.hero = _flag(flags, "fighter-kind.hero")
        p.skaven = _flag(flags, "species.skaven")
        p.squig_herder = 1 if row.get("squig_herder") else 0
        p.squig_prodder = _flag(flags, "weapon.squig-prodder")
        p.undivided_leader = _flag(flags, "mechanic.undivided-leader")
        p.wizened_halfling = _flag(flags, "mechanic.wizened-halfling")
        p.halfling = _flag(flags, "species.halfling")
        p.undead = _flag(flags, "nature.undead")
        p.vampire = _flag(flags, "species.vampire")
        p.necromancer = _flag(flags, "identity.necromancer")
        p.printed_skaven_bits = <int>row.get("printed_skaven_bits", 0)
    distances = d["distances"]
    for i in range(n):
        for j in range(n):
            out.distances[i * n + j] = <double>distances[i][j]
    charging = d["charging"]
    out.explicit_charging = charging is not None
    if charging is not None:
        out.first_charges = 1 if charging[0] else 0
        out.second_charges = 1 if charging[1] else 0
    active = d["active_first"]
    out.has_active = active is not None
    out.active_first = 1 if active else 0
    out.has_contacts = d["contacts"] is not None
    out.duelists_in_contact = 1 if d["duelists_in_contact"] else 0
    return 0


cdef inline double ctx_distance_c(ContextC* c, int a, int b) noexcept:
    """Supplied edge-to-edge inches between two participants, ``-1`` if unknown."""
    if not c.present or a < 0 or b < 0 or a >= c.n or b >= c.n:
        return -1.0
    return c.distances[a * c.n + b]


# ---------------------------------------------------------------------------
# Decisions and phase tracing
# ---------------------------------------------------------------------------


#: The fixed phase pipeline of one round, in the order of the oracle's
#: ``modular/rounds.py::resolve_round``.  Every phase runs every round; a
#: phase whose rules are not ported yet is an explicit no-op hook, so the
#: trace of an observed batch documents exactly where a later port lands.
ROUND_PHASES = (
    "round-start",
    "own-turn-recovery",
    "characteristics",
    "equipment",
    "sustain",
    "stand-up",
    "declarations",
    "psychology",
    "pre-combat",
    "reactions",
    "pools",
    "attacks",
    "aftermath",
)


cdef inline void trace_phase_c(str name):
    if _phase_trace is not None:
        _phase_trace.append(name)


# ---------------------------------------------------------------------------
# Batch: compiled tables, both states, context, generator and round scratch
# ---------------------------------------------------------------------------

cdef struct BatchC:
    #: Per side, the whole-pool replacement projections of
    #: ``select_attack_replacement`` and the index each one interned to.
    int replacement_index[2][6]
    int gauche_index[2][2]
    int shifty_index[2][2]
    int shifty_count[2]
    int8_t* shifty_on[2]
    int8_t* shifty_slot[2]
    int8_t* jolt_on[2]
    int8_t* jolt_slot[2]
    int8_t* jolt_done[2]
    int8_t* shifty_done[2]
    int16_t* deathblow_pool[2]
    int16_t* shifty_saved
    int32_t* shifty_projection
    int shifty_choice[2]
    int whip_index[2]
    int whip_count[2]
    int8_t* whip_on[2]
    int8_t* whip_slot[2]
    int8_t* whip_done[2]
    int replacement_count[2]
    TablesC tables
    StateC s1
    StateC s2
    ContextC ctx
    Rng rng
    int count
    int maximum_rounds
    int round_index
    bint first_round
    bint insignia_window
    int8_t* first_charges
    int8_t* second_charges
    int8_t* initial_first_turn
    int8_t* engaged
    int8_t* unresolved
    int8_t* charge1
    int8_t* charge2
    int8_t* player_turn1
    int8_t* player_turn2
    int8_t* stood1
    int8_t* stood2
    int16_t* attacks1
    int16_t* attacks2
    int8_t* p1
    int8_t* p2
    int16_t* ini1
    int16_t* ini2
    int8_t* first_acts
    int* active_rows
    int n_active
    int* rows
    int* reply
    int* paralyze_rows
    int* paralyze_targets
    int8_t* paralyze_results


cdef void batch_free_c(BatchC* b) noexcept:
    free(b.first_charges); free(b.second_charges); free(b.initial_first_turn)
    free(b.engaged); free(b.unresolved)
    free(b.charge1); free(b.charge2); free(b.player_turn1); free(b.player_turn2)
    free(b.stood1); free(b.stood2); free(b.attacks1); free(b.attacks2)
    free(b.p1); free(b.p2); free(b.ini1); free(b.ini2); free(b.first_acts)
    free(b.jolt_on[0]); free(b.jolt_on[1])
    free(b.jolt_slot[0]); free(b.jolt_slot[1])
    free(b.jolt_done[0]); free(b.jolt_done[1])
    free(b.shifty_on[0]); free(b.shifty_on[1])
    free(b.shifty_slot[0]); free(b.shifty_slot[1])
    free(b.shifty_done[0]); free(b.shifty_done[1])
    free(b.whip_on[0]); free(b.whip_on[1])
    free(b.whip_slot[0]); free(b.whip_slot[1])
    free(b.whip_done[0]); free(b.whip_done[1])
    free(b.deathblow_pool[0]); free(b.deathblow_pool[1])
    free(b.shifty_saved); free(b.shifty_projection)
    free(b.active_rows); free(b.rows); free(b.reply)
    free(b.paralyze_rows); free(b.paralyze_targets); free(b.paralyze_results)
    state_free(&b.s1)
    state_free(&b.s2)
    context_free(&b.ctx)
    tables_free(&b.tables)
    memset(b, 0, sizeof(BatchC))


cdef int batch_alloc_c(BatchC* b, int count) except -1:
    cdef int n = count if count > 0 else 1
    b.count = count
    b.first_charges = <int8_t*>calloc(n, 1)
    b.second_charges = <int8_t*>calloc(n, 1)
    b.initial_first_turn = <int8_t*>calloc(n, 1)
    b.engaged = <int8_t*>calloc(n, 1)
    b.unresolved = <int8_t*>calloc(n, 1)
    b.charge1 = <int8_t*>calloc(n, 1)
    b.charge2 = <int8_t*>calloc(n, 1)
    b.player_turn1 = <int8_t*>calloc(n, 1)
    b.player_turn2 = <int8_t*>calloc(n, 1)
    b.stood1 = <int8_t*>calloc(n, 1)
    b.stood2 = <int8_t*>calloc(n, 1)
    b.attacks1 = <int16_t*>calloc(n, sizeof(int16_t))
    b.attacks2 = <int16_t*>calloc(n, sizeof(int16_t))
    b.p1 = <int8_t*>calloc(n, 1)
    b.p2 = <int8_t*>calloc(n, 1)
    b.ini1 = <int16_t*>calloc(n, sizeof(int16_t))
    b.ini2 = <int16_t*>calloc(n, sizeof(int16_t))
    b.first_acts = <int8_t*>calloc(n, 1)
    b.jolt_on[0] = <int8_t*>calloc(n, 1)
    b.jolt_on[1] = <int8_t*>calloc(n, 1)
    b.jolt_slot[0] = <int8_t*>calloc(n, 1)
    b.jolt_slot[1] = <int8_t*>calloc(n, 1)
    b.jolt_done[0] = <int8_t*>calloc(n, 1)
    b.jolt_done[1] = <int8_t*>calloc(n, 1)
    b.shifty_on[0] = <int8_t*>calloc(n, 1)
    b.shifty_on[1] = <int8_t*>calloc(n, 1)
    b.shifty_slot[0] = <int8_t*>calloc(n, 1)
    b.shifty_slot[1] = <int8_t*>calloc(n, 1)
    b.shifty_done[0] = <int8_t*>calloc(n, 1)
    b.shifty_done[1] = <int8_t*>calloc(n, 1)
    b.whip_on[0] = <int8_t*>calloc(n, 1)
    b.whip_on[1] = <int8_t*>calloc(n, 1)
    b.whip_slot[0] = <int8_t*>calloc(n, 1)
    b.whip_slot[1] = <int8_t*>calloc(n, 1)
    b.whip_done[0] = <int8_t*>calloc(n, 1)
    b.whip_done[1] = <int8_t*>calloc(n, 1)
    b.deathblow_pool[0] = <int16_t*>calloc(n, sizeof(int16_t))
    b.deathblow_pool[1] = <int16_t*>calloc(n, sizeof(int16_t))
    b.shifty_saved = <int16_t*>calloc(n, sizeof(int16_t))
    b.shifty_projection = <int32_t*>calloc(n, sizeof(int32_t))
    b.active_rows = <int*>calloc(n, sizeof(int))
    b.rows = <int*>calloc(n, sizeof(int))
    b.reply = <int*>calloc(n, sizeof(int))
    b.paralyze_rows = <int*>calloc(n, sizeof(int))
    b.paralyze_targets = <int*>calloc(n, sizeof(int))
    b.paralyze_results = <int8_t*>calloc(n, 1)
    state_alloc(&b.s1, count)
    state_alloc(&b.s2, count)
    if (b.first_charges == NULL or b.second_charges == NULL or b.initial_first_turn == NULL
            or b.engaged == NULL or b.unresolved == NULL or b.charge1 == NULL
            or b.charge2 == NULL or b.player_turn1 == NULL or b.player_turn2 == NULL
            or b.stood1 == NULL or b.stood2 == NULL or b.attacks1 == NULL
            or b.attacks2 == NULL or b.p1 == NULL or b.p2 == NULL or b.ini1 == NULL
            or b.ini2 == NULL or b.first_acts == NULL or b.active_rows == NULL
            or b.jolt_on[0] == NULL or b.jolt_on[1] == NULL
            or b.jolt_slot[0] == NULL or b.jolt_slot[1] == NULL
            or b.jolt_done[0] == NULL or b.jolt_done[1] == NULL
            or b.shifty_on[0] == NULL or b.shifty_on[1] == NULL
            or b.shifty_slot[0] == NULL or b.shifty_slot[1] == NULL
            or b.whip_on[0] == NULL or b.whip_on[1] == NULL
            or b.whip_slot[0] == NULL or b.whip_slot[1] == NULL
            or b.whip_done[0] == NULL or b.whip_done[1] == NULL
            or b.rows == NULL or b.reply == NULL or b.paralyze_rows == NULL
            or b.paralyze_targets == NULL or b.paralyze_results == NULL
            or not state_ok(&b.s1) or not state_ok(&b.s2)):
        return -1
    return 0


cdef int refresh_unresolved_c(BatchC* b) noexcept:
    """Recompute the live rows (both in action and still engaged)."""
    cdef int i
    b.n_active = 0
    for i in range(b.count):
        b.unresolved[i] = 1 if (b.s1.condition[i] != OUT and b.s2.condition[i] != OUT
                                and b.engaged[i]) else 0
        if b.unresolved[i]:
            b.active_rows[b.n_active] = i
            b.n_active += 1
    return b.n_active


cdef int init_charges_c(BatchC* b) except -1:
    """Port of the charge, player-turn and engagement facts of
    ``modular.state.initialize_duel``.

    Only legal initial chargers are sampled; a supplied contact between the
    duelists is an established engagement that owns no charge; a supplied
    contact set that does not join them leaves the row unengaged, so the duel
    ends unresolved without a round, exactly as the oracle's loop does.
    """
    cdef bint allowed0 = b.tables.sides[0][0].f.can_charge
    cdef bint allowed1 = b.tables.sides[1][0].f.can_charge
    cdef bint base_contact = b.ctx.present and b.ctx.has_contacts and b.ctx.duelists_in_contact
    cdef bint sampled_contact = (not b.ctx.present) or (not b.ctx.has_contacts) or base_contact
    cdef bint legacy, fc, sc
    cdef int i
    for i in range(b.count):
        if b.ctx.present and b.ctx.explicit_charging:
            legacy = 1
            fc = b.ctx.first_charges
            sc = b.ctx.second_charges
        else:
            if allowed0 != allowed1:
                legacy = allowed0
            else:
                legacy = 1 if rng_coin(&b.rng) else 0
            fc = legacy and allowed0
            sc = (not legacy) and allowed1
        if base_contact:
            fc = 0
            sc = 0
        b.first_charges[i] = fc
        b.second_charges[i] = sc
        if b.ctx.present:
            b.initial_first_turn[i] = b.ctx.active_first if b.ctx.has_active else legacy
        else:
            b.initial_first_turn[i] = fc
        b.engaged[i] = 1 if sampled_contact else (1 if (fc or sc) else 0)
    return 0


# ---------------------------------------------------------------------------
# Psychology and Leadership (ports of modular/leadership.py,
# modular/psychology.py and the charm block of modular/rounds.py)
#
# The tests run over row sets of one side; a decision key is asked once per
# row set (the NumPy convention), every die is drawn per row through the
# owned-roll wrapper, and every once-per-battle resource is a state column.
# The fighter facts are the printed side's (entry zero of its table), exactly
# as the oracle tests the compiled fighter the round projected.
# ---------------------------------------------------------------------------

#: Participant identifiers of the current batch's context (``ParticipantC``
#: index -> id), for the oracle's ``{key}.leader.{id}``/``{key}.handler.{id}``
#: decision keys.  Module scope for the same reason as ``_rng_callback``.
cdef object _ctx_ids = None

#: Charge gates by ``FighterC.charge_gate`` code (``_combat_compile.CHARGE_GATES``).
CHARGE_GATES = ("", "ashamed-and-afraid", "slaanesh-charge",
                "hypnotic-musk-charge", "charismatic-charge")
#: The Vampire control powers in the oracle's ``CONTROL_POWERS`` order.
CONTROL_POWERS = ("hypnotic-gaze", "lahmia-seduction", "lahmian-seduction")
#: The Dark Jester's three trick slots, in the printed order his chooser
#: offers them; each name is at once the oracle's ``FighterState`` field, the
#: compiled state column and the decision key's own suffix.
JESTER_TRICK_SLOTS = ("dodge_trick_active", "banter_trick_active",
                      "trip_trick_active")
#: The learned Shadow Dances, in ``modular/rounds.py::SHADOW_DANCES`` order.
SHADOW_DANCES = ("whirling-death", "storm-of-blades", "the-shadows-coil",
                 "woven-mist")
#: The two Djinn powers, in the order the oracle offers them.
DJINN_POWERS = ("curse", "luck")
#: ``seduction_controlled`` bits: the Lahmia copy (released only by a hit)
#: and the Khemrian copy (released by any attack).
cdef enum:
    SEDUCTION_LAHMIA = 1
    SEDUCTION_LAHMIAN = 2



cdef inline StateC* side_state(BatchC* b, int side) noexcept:
    return &b.s1 if side == 0 else &b.s2


cdef inline int8_t* side_charges(BatchC* b, int side) noexcept:
    return b.first_charges if side == 0 else b.second_charges


cdef inline int8_t* side_turn(BatchC* b, int side) noexcept:
    return b.player_turn1 if side == 0 else b.player_turn2


cdef inline FighterC* printed(BatchC* b, int side) noexcept:
    return &b.tables.sides[side][0].f


cdef int owned_d6_c(BatchC* b, int side, FighterC* f, int row, str key,
                    object decisions, dict cache, object subject,
                    bint close_combat, int8_t* rerolled) except -1:
    """One owned Leadership D6, plus the ``skill.luck`` re-roll that only the
    Leadership sites offer (the attack pipeline spends Luck at its own
    printed hit and wound sites)."""
    cdef StateC* s = side_state(b, side)
    cdef int value = owned_attack_d6_c(s, f, row, &b.rng, key, decisions, cache,
                                       subject, close_combat, rerolled)
    if (decisions is not None and f.luck and not s.luck_used[row]
            and not rerolled[0] and ".reroll" not in key
            and decide_cached_c(decisions, cache, key + ".luck", subject)):
        s.luck_used[row] = 1
        value = rng_draw_safe(&b.rng, 1, 6)
        rerolled[0] = 1
    return value


cdef int leadership_dice_c(BatchC* b, int side, FighterC* f, int row, str key, int count,
                           object decisions, dict cache, object subject, bint close_combat,
                           bint discard_highest, bint discard_lowest, int8_t* any_rerolled) except -1:
    """Port of ``phases.resolve_leadership``'s dice reading over owned dice."""
    cdef int index, value, total = 0, lowest = 7, highest = 0
    cdef int8_t rerolled
    any_rerolled[0] = 0
    for index in range(count):
        value = owned_d6_c(b, side, f, row, f"{key}.{index}", decisions, cache, subject,
                           close_combat, &rerolled)
        if rerolled:
            any_rerolled[0] = 1
        total += value
        if value < lowest:
            lowest = value
        if value > highest:
            highest = value
    if discard_lowest:
        return total - lowest
    if discard_highest:
        return total - highest
    return total


cdef inline int leader_radius_c(ParticipantC* p) noexcept:
    return 12 if p.leader_twelve else 4 if p.leader_four else 6


cdef int supplied_provider_c(ParticipantC* p, uint64_t bands, int* radius) noexcept:
    """``modular/leadership.py::_supplied_provider``: 0 none, 1 leader, 2 relay, 3 songster."""
    if p.slave_driver:
        radius[0] = 6 if p.scourge else 3
        return 1
    if p.songster:
        radius[0] = 6
        return 3
    if not (p.bands & bands):
        return 0
    if p.relay_orders:
        radius[0] = leader_radius_c(p)
        return 2
    if p.leader_six:
        radius[0] = 6 if p.dim_witted_leader else leader_radius_c(p)
        return 1
    return 0


cdef int relayed_leader_c(ContextC* c, int provider, uint64_t bands) noexcept:
    """The supplied Leader an Adjutant relays; -1 while he cannot use one."""
    cdef int i
    cdef ParticipantC* p = &c.participants[provider]
    cdef ParticipantC* q
    for i in range(2, c.n):
        if i == provider:
            continue
        q = &c.participants[i]
        if (q.side != p.side or q.condition != 0 or not (q.bands & bands) or not q.leader_six):
            continue
        if ctx_distance_c(c, provider, i) >= 0 and ctx_distance_c(c, provider, i) <= leader_radius_c(q):
            return i
    return -1


cdef bint instructing_leader_c(ContextC* c, int me, int side, uint64_t bands, double inches) noexcept:
    cdef int i
    cdef ParticipantC* q
    for i in range(2, c.n):
        q = &c.participants[i]
        if q.side != side or q.condition == 4 or not (q.bands & bands) or not q.leader_six:
            continue
        if ctx_distance_c(c, me, i) >= 0 and ctx_distance_c(c, me, i) <= inches:
            return 1
    return 0


cdef int leadership_c(BatchC* b, int side, FighterC* f, const int* rows, int n, str key,
                      object decisions, dict cache, object subject,
                      int psychology_mode, const int8_t* psychology_rows,
                      bint stupidity, bint fear, bint discard_lowest, bint own_value_only,
                      bint contacting, bint close_combat, const int8_t* opponent_charges,
                      int8_t* out) except -1:
    """Port of ``modular.leadership.resolve_local_leadership`` over ``rows``.

    ``psychology_mode`` is 0 (not a Psychology test), 1 (it is) or 2 (per row,
    read from ``psychology_rows`` by simulation row).  ``out`` is aligned to
    ``rows``.  Only the rows that actually test spend dice and resources.
    """
    cdef StateC* s = side_state(b, side)
    cdef ContextC* c = &b.ctx
    cdef ParticipantC* me = NULL
    cdef ParticipantC* p
    cdef uint64_t bands = 0
    cdef int i, row, k, value, value_base, radius, contract, relayed, lent
    cdef int count, total, reroll_value
    cdef bint handler_only, supplied_reroll = 0, songster_reroll = 0, broken_pass = 0
    cdef bint psych, settled, passed, first_failed, eligible, discard_highest, borrowed, senior
    cdef bint usable_fallback
    cdef int8_t any_rerolled, ignored
    cdef int* usable = NULL
    cdef int* usable_value = NULL
    cdef int usable_n = 0
    if n == 0:
        return 0
    handler_only = f.squig_recipient or f.handler_leadership
    value_base = f.leadership if f.has_leadership else -1
    if handler_only and f.has_stupidity_leadership:
        value_base = f.stupidity_leadership
    if c.present:
        me = &c.participants[side]
        bands = me.bands
        # A local side and canonical band identify the supported warband
        # group: a leader's value is never lent across sides or bands.
        if handler_only and not own_value_only:
            for i in range(2, c.n):
                p = &c.participants[i]
                if f.squig_recipient:
                    eligible = p.squig_herder and (p.bands & bands) != 0 and p.handler_leadership
                    radius = 12 if p.squig_prodder else 6
                else:
                    eligible = p.bear_handler
                    radius = 6
                if (p.side == me.side and p.condition != 4 and eligible
                        and ctx_distance_c(c, side, i) >= 0 and ctx_distance_c(c, side, i) <= radius
                        and decide_cached_c(decisions, cache, f"{key}.handler.{_ctx_ids[i]}", subject)):
                    value_base = p.leadership if p.has_leadership else -1
                    break
        if f.broken_spirit:
            # Printed Broken Spirit: an automatic pass while the band's Leader
            # is not out of action; the clause prints no range.
            for i in range(2, c.n):
                p = &c.participants[i]
                if p.side == me.side and p.condition != 4 and (p.bands & bands) and p.leader_six:
                    broken_pass = 1
                    break
        if f.devoted and instructing_leader_c(c, side, me.side, bands, 12):
            supplied_reroll = 1
        for i in range(2, c.n):
            p = &c.participants[i]
            contract = supplied_provider_c(p, bands, &radius)
            if p.side != me.side or p.condition == 4 or contract != 3:
                continue
            if ctx_distance_c(c, side, i) >= 0 and ctx_distance_c(c, side, i) <= radius:
                songster_reroll = 1
        if not handler_only and not own_value_only and not f.own_leadership:
            usable = <int*>malloc((c.n if c.n > 0 else 1) * sizeof(int))
            usable_value = <int*>malloc((c.n if c.n > 0 else 1) * sizeof(int))
            if usable == NULL or usable_value == NULL:
                free(usable); free(usable_value)
                return -1
            for i in range(2, c.n):
                p = &c.participants[i]
                if p.side != me.side or p.condition != 0 or p.mouth_sewn:
                    continue
                if p.slave_driver and not f.slave:
                    continue
                contract = supplied_provider_c(p, bands, &radius)
                if contract == 0:
                    continue
                if ctx_distance_c(c, side, i) < 0 or ctx_distance_c(c, side, i) > radius:
                    continue
                if contract == 3:
                    songster_reroll = 1
                    continue
                if contract == 2:
                    relayed = relayed_leader_c(c, i, bands)
                    if relayed < 0:
                        continue
                    lent = c.participants[relayed].leadership if c.participants[relayed].has_leadership else -1
                else:
                    lent = 7 if p.dim_witted_leader else (p.leadership if p.has_leadership else -1)
                usable[usable_n] = i
                usable_value[usable_n] = lent
                usable_n += 1
            # Second in Command: the fallback Leader is offered only while no
            # other standing leader of the band can lend his Leadership.
            senior = 0
            for k in range(usable_n):
                if not c.participants[usable[k]].leader_fallback:
                    senior = 1
            borrowed = 0
            for k in range(usable_n):
                p = &c.participants[usable[k]]
                if p.undivided_leader or (p.wizened_halfling and f.halfling):
                    supplied_reroll = 1
                if senior and p.leader_fallback:
                    continue
                if not borrowed and decide_cached_c(decisions, cache, f"{key}.leader.{_ctx_ids[usable[k]]}", subject):
                    value_base = usable_value[k]
                    borrowed = 1
            free(usable); free(usable_value)
    for i in range(n):
        row = rows[i]
        out[i] = 1
        psych = psychology_mode == 1 or (psychology_mode == 2 and psychology_rows[row] != 0)
        settled = 0
        if psych and (s.frenzy[row] or f.psychology_immunity
                      or s.righteous_active[row]):
            settled = 1
        # Instinctual Violence exempts only the target of an Undead charger.
        if fear and f.fear_immunity_undead_chargers and opponent_charges != NULL and opponent_charges[row]:
            settled = 1
        if fear and (f.fear_immunity or f.undead_foes_no_fear):
            settled = 1
        if f.automatic_leadership:
            settled = 1
        if not settled and f.holy_relic and not s.holy_relic_used[row]:
            s.holy_relic_used[row] = 1
            settled = 1
        if not settled and f.sigmar_enlightened:
            settled = 1
        if not settled and broken_pass:
            settled = 1
        if settled:
            continue
        value = value_base
        if f.poetry_victorious_leader and not s.poetry_first_used[row]:
            s.poetry_first_used[row] = 1
            if value >= 0:
                value += 1
        # Printed Mob: the caller supplies the allied Peasants within three inches.
        if value >= 0 and f.mob_leadership:
            value += f.mob_allies
        # Enchanting Beauty applies in base contact only.
        if contacting and value >= 0 and f.enchanting_beauty:
            value -= 1
        # Ghostly Howl: D6 off the tested enemy's Leadership on a Fear test.
        if fear and f.opponent_ghostly_howl:
            value -= rng_draw_safe(&b.rng, 1, 6)
        if stupidity and value >= 0:
            value += f.stupidity_leadership_bonus
        if value < 0:
            raise ValueError("Leadership test requires explicit non-negative integer Leadership")
        discard_highest = (f.cold_blooded_leadership or (psych and f.cold_blooded_psychology)) and not discard_lowest
        count = 3 if (discard_highest or discard_lowest) else 2
        total = leadership_dice_c(b, side, f, row, key, count, decisions, cache, subject,
                                  close_combat, discard_highest, discard_lowest, &any_rerolled)
        passed = total <= value
        # Declining the first failure does not reserve a later failure instead.
        first_failed = f.first_failed_leadership_reroll and not s.first_failed_used[row] and not passed
        if first_failed:
            s.first_failed_used[row] = 1
        eligible = (first_failed or f.mandatory_leadership_reroll or supplied_reroll or songster_reroll
                    or f.leadership_reroll or f.questing_vow_reroll
                    or (f.raise_our_insignia and b.insignia_window)
                    or (fear and f.fear_reroll))
        if (not passed and eligible and not any_rerolled
                and (f.mandatory_leadership_reroll
                     or decide_cached_c(decisions, cache, f"{key}.reroll", subject))):
            # Reuse the chosen threshold and dice convention; never re-roll a
            # die a personal resource already re-rolled.
            reroll_value = (value + 1 if value + 1 < 10 else 10) if songster_reroll else value
            total = leadership_dice_c(b, side, f, row, f"{key}.reroll", count, decisions, cache,
                                      subject, close_combat, discard_highest, discard_lowest, &ignored)
            passed = total <= reroll_value
        out[i] = 1 if passed else 0
    return 0


cdef int refresh_engaged_c(BatchC* b, const int* rows, int n, const int8_t* failed0,
                           const int8_t* failed1) noexcept:
    """``engaged = engaged and (any(charges) or not failed_charges)`` per row."""
    cdef int i, row
    for i in range(n):
        row = rows[i]
        if b.engaged[row] and not (b.first_charges[row] or b.second_charges[row]):
            if failed0 == NULL or failed0[row] or failed1[row]:
                b.engaged[row] = 0
    return 0


cdef int stupidity_c(BatchC* b, int side, object decisions, object subject) except -1:
    """Port of ``modular.psychology.resolve_stupidity`` for the active player's fighter."""
    cdef StateC* s = side_state(b, side)
    cdef FighterC* f = printed(b, side)
    cdef int8_t* charges = side_charges(b, side)
    cdef int8_t* turn = side_turn(b, side)
    cdef ContextC* c = &b.ctx
    cdef ParticipantC* p
    cdef int i, row, m = 0, t = 0, my_side = 0
    cdef bint heroes_exist = 0, near_hero = 0, skaven_exempt = 0, handler_exists = 0, near_handler = 0
    cdef bint passed, failed
    cdef int* gated = <int*>malloc((b.count if b.count > 0 else 1) * sizeof(int))
    cdef int* tested = <int*>malloc((b.count if b.count > 0 else 1) * sizeof(int))
    cdef int8_t* pre = <int8_t*>calloc(b.count if b.count > 0 else 1, 1)
    cdef int8_t* psych = <int8_t*>calloc(b.count if b.count > 0 else 1, 1)
    cdef int8_t* results = <int8_t*>calloc(b.count if b.count > 0 else 1, 1)
    cdef dict cache = {}
    cdef str key = round_key(b.round_index, side) + ".stupidity"
    if gated == NULL or tested == NULL or pre == NULL or psych == NULL or results == NULL:
        free(gated); free(tested); free(pre); free(psych); free(results)
        return -1
    try:
        for i in range(b.n_active):
            row = b.active_rows[i]
            if (turn[row] and s.condition[row] != OUT
                    and (s.lunatic_stupidity[row] or f.stupidity
                         or s.drunken_result[row] == 1 or s.bitten_result[row] == 1
                         or s.disability[row] == 6)):
                gated[m] = row
                m += 1
        if m == 0:
            return 0
        if c.present:
            my_side = c.participants[side].side
            for i in range(2, c.n):
                p = &c.participants[i]
                if p.hero:
                    heroes_exist = 1
                    if (p.side == my_side and p.condition != 4
                            and ctx_distance_c(c, side, i) >= 0 and ctx_distance_c(c, side, i) <= 6):
                        near_hero = 1
                    # The printed Rat Ogre exemption: a Skaven Hero of the
                    # bearer's own side within six inches, scoped to the bands
                    # that print it.
                    if (p.side == my_side and p.condition != 4
                            and (p.skaven or (p.printed_skaven_bits & f.printed_skaven_bits))
                            and ctx_distance_c(c, side, i) >= 0 and ctx_distance_c(c, side, i) <= 6):
                        skaven_exempt = 1
                if p.bear_handler:
                    handler_exists = 1
                    if (p.side == my_side and p.condition != 4
                            and ctx_distance_c(c, side, i) >= 0 and ctx_distance_c(c, side, i) <= 6):
                        near_handler = 1
        for i in range(m):
            row = gated[i]
            passed = (s.frenzy[row] or f.stupidity_exempt
                      or (b.first_round and charges[row] and f.impetuous_charge
                          and not s.impetuous_released[row]))
            if not passed and s.disability[row] == 6:
                passed = near_hero or (f.disability_hero_nearby and not heroes_exist)
            if not passed and f.stupidity and (f.skaven_group or f.printed_skaven_bits):
                passed = skaven_exempt
            if not passed and f.bear_handler_recipient:
                passed = near_handler or (f.bear_handler_nearby and not handler_exists)
            pre[row] = 1 if passed else 0
            if not passed:
                tested[t] = row
                t += 1
                psych[row] = 1 if (s.drunken_result[row] != 1 and not s.lunatic_stupidity[row]) else 0
        if t:
            if leadership_c(b, side, f, tested, t, key, decisions, cache, subject,
                            2, psych, 1, 0, 0, 0, 1, 0, NULL, results) < 0:
                return -1
        t = 0
        for i in range(m):
            row = gated[i]
            if pre[row]:
                failed = 0
            else:
                failed = not results[t]
                t += 1
            s.stupidity_failed[row] = 1 if failed else 0
            # The initial voluntary charge cannot establish contact after a
            # failed test.
            if failed and b.first_round and charges[row]:
                charges[row] = 0
                if not (b.first_charges[row] or b.second_charges[row]):
                    b.engaged[row] = 0
    finally:
        free(gated); free(tested); free(pre); free(psych); free(results)
    return 0


cdef bint needs_fear_test_c(BatchC* b, int side, int row) noexcept:
    # A Righteous Charge carries Fear and Psychology immunity for its round.
    """``resolve_fear``'s ``needs_test`` for one row of ``side``."""
    cdef FighterC* f = printed(b, side)
    cdef FighterC* enemy = printed(b, 1 - side)
    cdef StateC* s = side_state(b, side)
    cdef StateC* o = side_state(b, 1 - side)
    cdef bint charging = side_charges(b, side)[row] != 0
    cdef bint base = s.condition[row] == STANDING and o.condition[row] != OUT
    if not base:
        return 0
    if (f.ere_we_go and charging) or (f.impetuous_charge and charging) or f.accustomed_to_fear:
        return 0
    if f.morrs_special or f.fears_foe_fire:
        # These sources expressly override the Undead Psychology exemptions.
        return 1
    if s.righteous_active[row]:
        return 0
    return ((enemy.causes_fear or o.righteous_active[row])
            and (not (f.causes_fear or s.righteous_active[row]) or f.craven)
            and not s.frenzy[row]
            and not f.fear_immunity and not f.undead_foes_no_fear and not f.psychology_immunity)


cdef int fear_c(BatchC* b, object decisions, object first_py, object second_py) except -1:
    """Port of ``modular.psychology.resolve_fear`` (round zero only)."""
    cdef int side, i, row, m
    cdef FighterC* f
    cdef int8_t* charges
    cdef StateC* s
    cdef bint ordinary
    cdef int n = b.count if b.count > 0 else 1
    cdef int8_t* failed0 = <int8_t*>calloc(n, 1)
    cdef int8_t* failed1 = <int8_t*>calloc(n, 1)
    cdef int* testing = <int*>malloc(n * sizeof(int))
    cdef int8_t* results = <int8_t*>malloc(n)
    cdef dict cache = {}
    cdef str label
    cdef object subject
    if failed0 == NULL or failed1 == NULL or testing == NULL or results == NULL:
        free(failed0); free(failed1); free(testing); free(results)
        return -1
    try:
        if not b.first_round or b.n_active == 0:
            return 0
        # The charge gates: a voluntary charge must pass the singer's test.
        for side in range(2):
            f = printed(b, side)
            charges = side_charges(b, side)
            s = side_state(b, side)
            label = "first" if side == 0 else "second"
            subject = first_py if side == 0 else second_py
            if f.charge_gate:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if b.engaged[row] and charges[row]:
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, side, f, testing, m, f"round.0.{label}.{CHARGE_GATES[f.charge_gate]}",
                                      decisions, cache, subject, 0, NULL, 0, 0, 0, 0, 0, 0, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if not results[i]:
                        charges[testing[i]] = 0
                        (failed0 if side == 0 else failed1)[testing[i]] = 1
            if f.beauty_target and not f.impetuous_charge:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if b.engaged[row] and charges[row]:
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, side, f, testing, m, f"round.0.{label}.beauty-charge",
                                      decisions, cache, subject, 1, NULL, 0, 0, 0, 0, 1, 0, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if results[i]:
                        s.beauty_passed[testing[i]] = 1
                    else:
                        charges[testing[i]] = 0
                        (failed0 if side == 0 else failed1)[testing[i]] = 1
        refresh_engaged_c(b, b.active_rows, b.n_active, failed0, failed1)
        if not (printed(b, 0).causes_fear or printed(b, 1).causes_fear):
            return 0
        # A voluntary charge must succeed before contact/charged reactions exist.
        for side in range(2):
            f = printed(b, side)
            charges = side_charges(b, side)
            s = side_state(b, side)
            label = "first" if side == 0 else "second"
            subject = first_py if side == 0 else second_py
            ordinary = not (f.morrs_special or f.fears_foe_fire)
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if b.engaged[row] and charges[row] and needs_fear_test_c(b, side, row):
                    testing[m] = row
                    m += 1
            if m and leadership_c(b, side, f, testing, m, f"round.0.{label}.fear.charge",
                                  decisions, cache, subject, 1 if ordinary else 0, NULL, 0, ordinary,
                                  0, 0, 0, 0, side_charges(b, 1 - side), results) < 0:
                return -1
            for i in range(m):
                if results[i]:
                    continue
                if f.wheelo_impact:
                    s.fear_hit_sixes[testing[i]] = 1
                else:
                    charges[testing[i]] = 0
                    (failed0 if side == 0 else failed1)[testing[i]] = 1
        refresh_engaged_c(b, b.active_rows, b.n_active, failed0, failed1)
        for side in range(2):
            f = printed(b, side)
            charges = side_charges(b, 1 - side)
            s = side_state(b, side)
            label = "first" if side == 0 else "second"
            subject = first_py if side == 0 else second_py
            ordinary = not (f.morrs_special or f.fears_foe_fire)
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if b.engaged[row] and charges[row] and needs_fear_test_c(b, side, row):
                    testing[m] = row
                    m += 1
            if m and leadership_c(b, side, f, testing, m, f"round.0.{label}.fear.charged",
                                  decisions, cache, subject, 1 if ordinary else 0, NULL, 0, ordinary,
                                  0, 0, 1, 1, charges, results) < 0:
                return -1
            for i in range(m):
                if not results[i]:
                    s.fear_hit_sixes[testing[i]] = 1
    finally:
        free(failed0); free(failed1); free(testing); free(results)
    return 0


cdef inline bint owner_ready_c(BatchC* b, int owner, int row) noexcept:
    """The owner of a charm acts while standing, not stupid and not held."""
    cdef StateC* o = side_state(b, owner)
    return (o.condition[row] == STANDING and not o.stupidity_failed[row]
            and not o.grappled[row] and not o.grappling[row])


cdef int djinn_powers_c(BatchC* b, object decisions, object first_py,
                        object second_py) except -1:
    """Port of the Djinn's Curse declaration (``modular/rounds.py``).

    The bearer nominates one of the two powers on his own turn and keeps it
    until his next one; the power he took last turn is never offered again.
    A bearer who is not Standing, who has just cut free of a net, who is held
    or holding, or who has lost his turn to Massively Built declares nothing,
    and whatever he carried lapses with that declaration.
    """
    cdef int side, i, row, power
    cdef StateC* s
    cdef int8_t* turn
    cdef dict cache = {}
    cdef object subject
    cdef str key
    for side in range(2):
        if not printed(b, side).djinns_curse:
            continue
        s = side_state(b, side)
        turn = side_turn(b, side)
        subject = first_py if side == 0 else second_py
        key = round_key(b.round_index, side) + ".djinn-power."
        for i in range(b.n_active):
            row = b.active_rows[i]
            if not turn[row]:
                # Rows that are not on their own turn keep what they carry.
                continue
            s.djinn_power[row] = 0
            if (s.condition[row] != STANDING or s.netted[row]
                    or s.massively_built_lost_turn[row]
                    or s.grappled[row] or s.grappling[row]):
                s.last_djinn_power[row] = 0
                continue
            # The two powers are offered in the printed order and the first
            # accepted offer stops the search; the power taken last turn is
            # not offered again.
            for power in (1, 2):
                if s.last_djinn_power[row] == power:
                    continue
                if decide_cached_c(decisions, cache, key + DJINN_POWERS[power - 1], subject):
                    s.djinn_power[row] = <int8_t>power
                    break
            s.last_djinn_power[row] = s.djinn_power[row]
    return 0


cdef int shadow_dances_c(BatchC* b, object decisions, object first_py,
                         object second_py) except -1:
    """Port of ``modular.rounds.select_shadow_dance`` for one combat phase.

    One learned dance is applied per phase and only the last one is
    remembered, so it cannot be repeated next phase.  A Wardancer that is not
    Standing, or that is held or holding, dances nothing and forgets what it
    danced.
    """
    cdef int side, i, row, dance
    cdef StateC* s
    cdef dict cache = {}
    cdef object subject
    cdef str key
    cdef bint any_available
    for side in range(2):
        if not printed(b, side).dances:
            continue
        s = side_state(b, side)
        subject = first_py if side == 0 else second_py
        key = round_key(b.round_index, side) + ".dance."
        for i in range(b.n_active):
            row = b.active_rows[i]
            s.dance_shadows_coil[row] = 0
            s.dance_woven_mist[row] = 0
            if (s.condition[row] != STANDING or s.grappled[row] or s.grappling[row]):
                s.last_dance[row] = 0
                continue
            any_available = 0
            for dance in range(4):
                if (printed(b, side).dances & (1 << dance)) and s.last_dance[row] != dance + 1:
                    any_available = 1
            if not any_available:
                s.last_dance[row] = 0
                continue
            for dance in range(4):
                if not (printed(b, side).dances & (1 << dance)):
                    continue
                if s.last_dance[row] == dance + 1:
                    continue
                if not decide_cached_c(decisions, cache, key + SHADOW_DANCES[dance], subject):
                    continue
                s.last_dance[row] = <int8_t>(dance + 1)
                if dance == 0:
                    s.injury_bonus_row[row] = <int8_t>(s.injury_bonus_row[row] + 1)
                elif dance == 1:
                    s.attacks_bonus_row[row] = <int8_t>(s.attacks_bonus_row[row] + 1)
                elif dance == 2:
                    s.dance_shadows_coil[row] = 1
                else:
                    s.dance_woven_mist[row] = 1
                break
            else:
                raise ValueError(
                    "a Wardancer must choose an available learned Shadow Dance")
    return 0


cdef int main_gauche_c(BatchC* b, object decisions, object first_py,
                       object second_py) except -1:
    """One Main Gauche mode is declared per combat turn: the blade is kept
    back to parry, or used as a dagger."""
    cdef int side, i, row
    cdef StateC* s
    cdef dict cache = {}
    for side in range(2):
        if not printed(b, side).main_gauche_modes or b.gauche_index[side][0] == 0:
            continue
        s = side_state(b, side)
        parry = decide_cached_c(
            decisions, cache,
            round_key(b.round_index, side) + ".main-gauche-parry",
            first_py if side == 0 else second_py)
        for i in range(b.n_active):
            row = b.active_rows[i]
            s.main_gauche_attacks[row] = 0 if parry else 1
            s.projection[row] = b.gauche_index[side][0 if parry else 1]
    return 0


cdef int mutations_c(BatchC* b, object decisions, object table, object first_py,
                     object second_py) except -1:
    """The Inquisitor's judgement and the per-row mutation projection.

    ``modular/rounds.py::_inquisitor_brands`` opens the combat phase: on a
    judgement of six the Inquisitor brands his enemy with one result of his
    own printed D66 chart, and the branded row is then simulated by the
    fighter that chart produces.  Every row that already carries a brand
    re-selects its tail for this phase and is projected again, exactly as
    ``resolve_round`` re-projects it before the pool is counted.

    The chart itself stays in ``modular.mutations``; only the per-row state
    and the projection index live here.
    """
    cdef int side, victim, i, row, result, index
    cdef StateC* s
    cdef StateC* vs
    cdef dict cache = {}
    cdef object subject, option
    cdef str key, label
    cdef object dice = NativeDice()
    for side in range(2):
        victim = 1 - side
        s = side_state(b, side)
        vs = side_state(b, victim)
        subject = first_py if side == 0 else second_py
        label = "first" if victim == 0 else "second"
        if not printed(b, side).solkan_inquisitor:
            continue
        key = round_key(b.round_index, side) + ".inquisitor"
        for i in range(b.n_active):
            row = b.active_rows[i]
            if s.condition[row] == OUT or vs.condition[row] == OUT:
                continue
            if rng_draw_safe(&b.rng, 1, 6) != 6:
                continue
            result = 10 * rng_draw_safe(&b.rng, 1, 6) + rng_draw_safe(&b.rng, 1, 6)
            option = table.mutation_option("first" if side == 0 else "second", result)
            if option is None:
                raise ValueError(
                    "Inquisitor requires its complete source D66 mutation chart "
                    f"(missing {result})")
            table.brand_row(label, row, option, dice, decisions,
                            key + ".mutation." + str(result))
            vs.mutation_count[row] = <int8_t>table.row_brand_count(label, row)
    # Re-project every row that carries a brand.
    for side in range(2):
        s = side_state(b, side)
        label = "first" if side == 0 else "second"
        subject = first_py if side == 0 else second_py
        for i in range(b.n_active):
            row = b.active_rows[i]
            if not s.mutation_count[row] and not s.hillman_wolf[row]:
                continue
            if (s.condition[row] != STANDING or s.grappled[row] or s.grappling[row]
                    or s.stupidity_failed[row]):
                continue
            index = <int>table.project_row(
                label, row, decisions,
                round_key(b.round_index, side) + ".mutation", b.first_round)
            if index:
                if sync_projections_c(&b.tables, table) < 0:
                    return -1
                s.projection[row] = index
    return 0


cdef int songs_and_belches_c(BatchC* b, object decisions, object first_py,
                             object second_py) except -1:
    """The Sea Shanty, the Ogre's belch and the Halfling Elder's belch.

    All three open the combat phase from the singer's side and each costs
    its listener something different: the Shanty and the Ogre's belch make
    the enemy test Leadership -- a failure costs one attack, or one point of
    To Hit -- while the Halfling Elder's timed belch makes the enemy's very
    first blow miss (``modular/rounds.py``).
    """
    cdef int side, enemy, i, row, m
    cdef StateC* s
    cdef StateC* es
    cdef FighterC* f
    cdef FighterC* ef
    cdef dict cache = {}
    cdef object subject
    cdef str key
    cdef int* scratch = b.reply
    cdef int8_t* results = b.paralyze_results
    for side in range(2):
        for i in range(b.count):
            side_state(b, side).pool_loss_row[i] = 0
            side_state(b, side).hit_penalty_row[i] = 0
            side_state(b, side).miss_first_attack[i] = 0
    for side in range(2):
        enemy = 1 - side
        f = printed(b, side)
        ef = printed(b, enemy)
        s = side_state(b, side)
        es = side_state(b, enemy)
        subject = first_py if side == 0 else second_py
        key = round_key(b.round_index, side)
        # The singer must be standing, free and in contact to be heard.
        m = 0
        for i in range(b.n_active):
            row = b.active_rows[i]
            if (b.engaged[row] and s.condition[row] == STANDING
                    and not s.stupidity_failed[row] and not s.grappled[row]
                    and not s.grappling[row] and es.condition[row] != OUT):
                scratch[m] = row
                m += 1
        if m == 0:
            continue
        if f.sea_shanty or f.sea_shanty_psychology:
            # The Shanty reaches a living listener; its Psychology copy is
            # refused by a frenzied or immune one.
            if not ((f.sea_shanty and f.shanty_excluded)
                    or (f.sea_shanty_psychology and f.shanty_psych_excluded)):
                if decide_cached_c(decisions, cache, key + ".sea-shanty", subject):
                    if leadership_c(b, enemy, ef, scratch, m,
                                    key + ".sea-shanty.leadership", decisions, cache,
                                    subject, 0, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                        return -1
                    for i in range(m):
                        row = scratch[i]
                        if f.sea_shanty_psychology and es.frenzy[row]:
                            continue
                        if not results[i]:
                            es.pool_loss_row[row] = <int8_t>(es.pool_loss_row[row] + 1)
        if f.crude_belch_ogre:
            if decide_cached_c(decisions, cache, key + ".crude-belch-ogre", subject):
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (b.engaged[row] and s.condition[row] == STANDING
                            and not s.crude_belch_used[row]
                            and not s.stupidity_failed[row] and not s.grappled[row]
                            and not s.grappling[row] and es.condition[row] != OUT):
                        scratch[m] = row
                        m += 1
                if m:
                    for i in range(m):
                        s.crude_belch_used[scratch[i]] = 1
                    if leadership_c(b, enemy, ef, scratch, m,
                                    key + ".crude-belch-ogre.leadership", decisions,
                                    cache, subject, 0, NULL, 0, 0, 0, 0, 1, 1,
                                    NULL, results) < 0:
                        return -1
                    for i in range(m):
                        if not results[i]:
                            es.hit_penalty_row[scratch[i]] = <int8_t>(
                                es.hit_penalty_row[scratch[i]] + 1)
        # The Halfling Elder's belch is timed for the opening round only.
        if f.crude_belch_halfling and b.first_round:
            if decide_cached_c(decisions, cache, key + ".crude-belch", subject):
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (s.condition[row] == STANDING and es.condition[row] != OUT):
                        scratch[m] = row
                        m += 1
                if m:
                    if leadership_c(b, enemy, ef, scratch, m,
                                    key + ".crude-belch.leadership", decisions, cache,
                                    subject, 0, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                        return -1
                    for i in range(m):
                        if not results[i]:
                            es.miss_first_attack[scratch[i]] = 1
    return 0


cdef int grapple_c(BatchC* b, object decisions, object first_py,
                   object second_py) except -1:
    """The Torturer's hold: one declaration per side and phase.

    A declared hold is the warrior's whole pool, so the held pair strike no
    independent blows until the victim's own Strength test frees it
    (``modular/rounds.py``).
    """
    cdef int side, enemy, i, row, m
    cdef StateC* s
    cdef StateC* es
    cdef dict cache = {}
    for side in range(2):
        enemy = 1 - side
        if not printed(b, side).gaoler_grapple:
            continue
        s = side_state(b, side)
        es = side_state(b, enemy)
        m = 0
        for i in range(b.n_active):
            row = b.active_rows[i]
            if (s.condition[row] == STANDING and es.condition[row] != OUT
                    and not s.on_fire[row] and not s.animosity_failed[row]
                    and not s.stupidity_failed[row] and not s.charm_attack_blocked[row]
                    and not s.danse_macabre_controlled[row]
                    and not s.grappled[row] and not s.grappling[row]):
                b.reply[m] = row
                m += 1
        if m == 0:
            continue
        if not decide_cached_c(decisions, cache,
                               round_key(b.round_index, side) + ".torturer-grapple",
                               first_py if side == 0 else second_py):
            continue
        for i in range(m):
            row = b.reply[i]
            s.grappling[row] = 1
            es.grappled[row] = 1
    return 0


cdef int jester_tricks_c(BatchC* b, object decisions, object first_py,
                         object second_py) except -1:
    """Port of ``mechanic.confound-and-confuse``'s per-turn chooser.

    The three printed slots are offered in order, the first accepted offer
    lights exactly its own slot and every other slot goes dark; a bearer who
    accepts no offer keeps every slot dark.  The declaration also hands the
    Trip trick's own wound replacement back.  A bearer that is held, holding
    or no longer engaged declares nothing and keeps the trick it declared on
    its previous turn, exactly as the oracle's ``continue`` does.
    """
    cdef int side, i, row, slot, accepted
    cdef StateC* s
    cdef dict cache = {}
    cdef object subject
    cdef str key
    for side in range(2):
        if not printed(b, side).confound_and_confuse:
            continue
        s = side_state(b, side)
        subject = first_py if side == 0 else second_py
        key = round_key(b.round_index, side) + ".jester-trick."
        accepted = -1
        for slot in range(3):
            if decide_cached_c(decisions, cache, key + JESTER_TRICK_SLOTS[slot], subject):
                accepted = slot
                break
        for i in range(b.n_active):
            row = b.active_rows[i]
            if not b.engaged[row] or s.grappled[row] or s.grappling[row]:
                continue
            s.trip_trick_used[row] = 0
            s.dodge_trick_active[row] = 1 if accepted == 0 else 0
            s.banter_trick_active[row] = 1 if accepted == 1 else 0
            s.trip_trick_active[row] = 1 if accepted == 2 else 0
    return 0


cdef int charms_c(BatchC* b, object decisions, object first_py, object second_py) except -1:
    """Port of the charm block of ``modular/rounds.py::resolve_round``.

    Per target, in the oracle's order: the Mesmerising Dance, Beauty of the
    Sea, the Eye Pendant and the Mark of Shornaal (which set the phase's
    ``charm_attack_blocked``/``charm_auto_hit`` afresh), then the Hypnotist,
    Tranquil Fauna, the two Lahmia powers and the three control powers.
    """
    cdef int target, owner, i, row, m, k, power, bit
    cdef FighterC* f
    cdef FighterC* of
    cdef StateC* s
    cdef StateC* o
    cdef int n = b.count if b.count > 0 else 1
    cdef int8_t* blocked = <int8_t*>calloc(n, 1)
    cdef int8_t* auto_hit = <int8_t*>calloc(n, 1)
    cdef int8_t* allowed = <int8_t*>calloc(n, 1)
    cdef int* testing = <int*>malloc(n * sizeof(int))
    cdef int8_t* results = <int8_t*>malloc(n)
    cdef dict cache = {}
    cdef str label, owner_label, key, name
    cdef object subject, owner_subject
    cdef bint controlled
    if blocked == NULL or auto_hit == NULL or allowed == NULL or testing == NULL or results == NULL:
        free(blocked); free(auto_hit); free(allowed); free(testing); free(results)
        return -1
    try:
        for target in (1, 0):
            owner = 1 - target
            f = printed(b, target)
            of = printed(b, owner)
            s = side_state(b, target)
            o = side_state(b, owner)
            label = "first" if target == 0 else "second"
            owner_label = "first" if owner == 0 else "second"
            subject = first_py if target == 0 else second_py
            owner_subject = first_py if owner == 0 else second_py
            key = round_key(b.round_index, target)
            for i in range(b.n_active):
                row = b.active_rows[i]
                blocked[row] = 0
                auto_hit[row] = 0
            if f.dance_target:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if owner_ready_c(b, owner, row) and s.condition[row] == STANDING:
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, target, f, testing, m, key + ".mesmerising-dance", decisions, cache,
                                      subject, 0, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if not results[i]:
                        blocked[testing[i]] = 1
            if f.beauty_target:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (side_charges(b, owner)[row] and not s.beauty_passed[row]
                            and s.condition[row] == STANDING and o.condition[row] != OUT):
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, target, f, testing, m, key + ".beauty", decisions, cache,
                                      subject, 1, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if results[i]:
                        s.beauty_passed[testing[i]] = 1
                    else:
                        blocked[testing[i]] = 1
            # The Eye Pendant is an attack restriction, not Psychology.
            if f.pendant_target:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (b.engaged[row] and o.condition[row] != OUT and s.condition[row] == STANDING):
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, target, f, testing, m, key + ".eye-pendant", decisions, cache,
                                      subject, 0, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if not results[i]:
                        blocked[testing[i]] = 1
            if f.shornaal_target:
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (owner_ready_c(b, owner, row) and s.condition[row] == STANDING
                            and not s.shornaal_passed[row]):
                        testing[m] = row
                        m += 1
                if m and leadership_c(b, target, f, testing, m, key + ".shornaal", decisions, cache,
                                      subject, 1, NULL, 0, 0, 1, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if results[i]:
                        s.shornaal_passed[testing[i]] = 1
                    else:
                        blocked[testing[i]] = 1
                        auto_hit[testing[i]] = 1
            for i in range(b.n_active):
                row = b.active_rows[i]
                s.charm_attack_blocked[row] = blocked[row]
                s.charm_auto_hit[row] = auto_hit[row]
        # Hypnotist: a captor may release an entranced enemy; a fresh stare
        # entrances a standing, unfrenzied target that fails its test.
        for target in (1, 0):
            owner = 1 - target
            f = printed(b, target)
            s = side_state(b, target)
            o = side_state(b, owner)
            owner_label = "first" if owner == 0 else "second"
            subject = first_py if target == 0 else second_py
            owner_subject = first_py if owner == 0 else second_py
            if not f.foe_hypnotist:
                continue
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if s.entranced[row] and not o.grappled[row] and not o.grappling[row]:
                    testing[m] = row
                    m += 1
            if m and decide_cached_c(decisions, cache, f"round.{b.round_index}.{owner_label}.end-hypnosis", owner_subject):
                for i in range(m):
                    s.entranced[testing[i]] = 0
            if not f.hypnotist_target:
                continue
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if owner_ready_c(b, owner, row) and s.condition[row] == STANDING and not s.frenzy[row]:
                    testing[m] = row
                    m += 1
            key = f"round.{b.round_index}.{owner_label}.hypnotist"
            if m and decide_cached_c(decisions, cache, key, subject):
                if leadership_c(b, target, f, testing, m, key, decisions, cache, subject,
                                0, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    s.entranced[testing[i]] = 0 if results[i] else 1
        # Tranquil Fauna prevents attacks, never the charge or contact.  A
        # handled or large animal tests its qualified handler's Leadership on
        # two plain dice; an ordinary animal is barred outright.
        for target in (1, 0):
            owner = 1 - target
            f = printed(b, target)
            s = side_state(b, target)
            o = side_state(b, owner)
            if not f.fauna_mode:
                continue
            for i in range(b.n_active):
                row = b.active_rows[i]
                if o.condition[row] == OUT or s.condition[row] != STANDING:
                    continue
                if f.fauna_mode == 2:
                    if rng_draw_safe(&b.rng, 1, 6) + rng_draw_safe(&b.rng, 1, 6) > f.animal_handler_leadership:
                        s.charm_attack_blocked[row] = 1
                else:
                    s.charm_attack_blocked[row] = 1
        # The two Lahmia powers test the nominated enemy; a failure bars its
        # attacks for this phase (Deceive with its own Leadership only) and a
        # hypnotized victim is hit at +1 for the rest of the turn.
        for power in range(2):
            for target in (1, 0):
                owner = 1 - target
                f = printed(b, target)
                s = side_state(b, target)
                label = "first" if target == 0 else "second"
                subject = first_py if target == 0 else second_py
                if not (f.deceive_target if power == 0 else f.hypnotize_target):
                    continue
                name = "deceive" if power == 0 else "hypnotize"
                key = f"round.{b.round_index}.{label}.{name}"
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if owner_ready_c(b, owner, row) and s.condition[row] == STANDING:
                        testing[m] = row
                        m += 1
                if m == 0 or not decide_cached_c(decisions, cache, key, subject):
                    continue
                if leadership_c(b, target, f, testing, m, key, decisions, cache, subject,
                                1, NULL, 0, 0, 0, power == 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if not results[i]:
                        s.charm_attack_blocked[testing[i]] = 1
                        if power == 1:
                            s.hypnotized[testing[i]] = 1
        # Hypnotic Gaze and the two Seduction copies.
        for power in range(3):
            bit = SEDUCTION_LAHMIA if power == 1 else SEDUCTION_LAHMIAN if power == 2 else 0
            for target in (1, 0):
                owner = 1 - target
                f = printed(b, target)
                of = printed(b, owner)
                s = side_state(b, target)
                o = side_state(b, owner)
                label = "first" if target == 0 else "second"
                owner_label = "first" if owner == 0 else "second"
                subject = first_py if target == 0 else second_py
                owner_subject = first_py if owner == 0 else second_py
                if not f.foe_controls[power]:
                    continue
                name = CONTROL_POWERS[power]
                key = f"round.{b.round_index}.{label}.{name}"
                if f.control_excluded[power]:
                    # The printed exemption also ends a control this clause
                    # could not have established on such a model.
                    for i in range(b.n_active):
                        s.seduction_controlled[b.active_rows[i]] = 0
                    continue
                # The victim's own Recovery phase offers the test that throws
                # the control off.
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (s.seduction_controlled[row] and side_turn(b, target)[row]
                            and s.condition[row] == STANDING):
                        testing[m] = row
                        m += 1
                if m and decide_cached_c(decisions, cache, key + ".regain-control", subject):
                    if leadership_c(b, target, f, testing, m, key + ".regain-control", decisions, cache,
                                    subject, 0, NULL, 0, 0, 0, 0, 1, 0, NULL, results) < 0:
                        return -1
                    for i in range(m):
                        if results[i]:
                            s.seduction_controlled[testing[i]] = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    allowed[row] = 0
                    if s.seduction_controlled[row]:
                        # A controlled warrior strikes nobody while it holds.
                        s.charm_attack_blocked[row] = 1
                        continue
                    if not owner_ready_c(b, owner, row) or s.condition[row] != STANDING:
                        continue
                    if power == 1 and not side_turn(b, owner)[row]:
                        continue
                    if power == 1 and not f.male:
                        continue
                    allowed[row] = 1
                if power == 2:
                    # The Khemrian copy prints the Vampire's own test first.
                    m = 0
                    for i in range(b.n_active):
                        row = b.active_rows[i]
                        if allowed[row]:
                            testing[m] = row
                            m += 1
                    if m and leadership_c(b, owner, of, testing, m,
                                          f"round.{b.round_index}.{owner_label}.{name}.own-test",
                                          decisions, cache, owner_subject, 0, NULL, 0, 0, 0, 0, 1, 1,
                                          NULL, results) < 0:
                        return -1
                    for i in range(m):
                        if not results[i]:
                            allowed[testing[i]] = 0
                m = 0
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if allowed[row]:
                        testing[m] = row
                        m += 1
                if m == 0 or not decide_cached_c(decisions, cache, key, subject):
                    continue
                if leadership_c(b, target, f, testing, m, key, decisions, cache, subject,
                                1, NULL, 0, 0, 0, 0, 1, 1, NULL, results) < 0:
                    return -1
                for i in range(m):
                    if not results[i]:
                        row = testing[i]
                        s.charm_attack_blocked[row] = 1
                        if power == 0:
                            s.charm_auto_hit[row] = 1
                        else:
                            s.seduction_controlled[row] = <int8_t>bit
    finally:
        free(blocked); free(auto_hit); free(allowed); free(testing); free(results)
    return 0


cdef int seduction_release_c(BatchC* b) noexcept:
    """Seduction's printed release after the blows: the Khemrian copy ends
    when the Vampire attacks her victim at all, the Lahmia copy only when an
    attack hits.  An unattacked control survives into the next phase."""
    cdef int side, i, row
    cdef StateC* s
    cdef StateC* o
    for side in range(2):
        s = side_state(b, side)
        o = side_state(b, 1 - side)
        for i in range(b.n_active):
            row = b.active_rows[i]
            if not s.seduction_controlled[row] or not o.attacked_this_phase[row]:
                continue
            if s.hit_this_phase[row] or not (s.seduction_controlled[row] & SEDUCTION_LAHMIA):
                s.seduction_controlled[row] = 0
    return 0


# --- Phases, in the oracle's order -------------------------------------------

cdef int phase_round_start_c(BatchC* b) except -1:
    """Per-round facts the oracle resets at the top of ``resolve_round``:
    the Inconsistency roll mask, Fear's natural-sixes fact, persistent Frenzy,
    this round's player turn and the charge flags (round zero only)."""
    cdef int i
    # Raise Our Insignia lights with the opening round and expires at the
    # Shooting boundary, after the round-zero Psychology tests.
    b.insignia_window = b.first_round
    for i in range(b.count):
        b.s1.random_rolled[i] = 0
        b.s2.random_rolled[i] = 0
        b.s1.fear_hit_sixes[i] = 0
        b.s2.fear_hit_sixes[i] = 0
        b.s1.hypnotized[i] = 0
        b.s2.hypnotized[i] = 0
        b.s1.hit_this_phase[i] = 0
        b.s2.hit_this_phase[i] = 0
        b.s1.attacked_this_phase[i] = 0
        b.s2.attacked_this_phase[i] = 0
        if fighter_at(&b.tables, 0, &b.s1, i).persistent_frenzy:
            b.s1.frenzy[i] = 1
        if fighter_at(&b.tables, 1, &b.s2, i).persistent_frenzy:
            b.s2.frenzy[i] = 1
        b.player_turn1[i] = b.initial_first_turn[i] if (b.round_index % 2 == 0) else 1 - b.initial_first_turn[i]
        b.player_turn2[i] = 1 - b.player_turn1[i]
        b.charge1[i] = b.first_charges[i] if b.first_round else 0
        b.charge2[i] = b.second_charges[i] if b.first_round else 0
        b.stood1[i] = 0
        b.stood2[i] = 0
    return 0


cdef int phase_own_turn_recovery_c(BatchC* b, object decisions, object first_py,
                                   object second_py) except -1:
    """The active player's own-turn recovery options, in the oracle's order.

    ``modular/rounds.py::resolve_round`` resolves them before the Psychology
    gates: the Revenant's regeneration, the Alchemist's brew, Herb Lore, the
    Rousing Sermon and the Black Hunger activation.  Each writes the state
    columns the later phases read; the per-turn Attack grants accumulate in
    ``attacks_bonus_row``, which the pool reads.

    Still unported and landing here: Drenok's Berserker, the Impetuous
    release, Petru's potions, the Danse Macabre release, the Bitten
    transform, Lunatics, the Djinn declaration and Devoted to the Vampire.
    """
    cdef int side, i, row, maximum, roll, m
    cdef StateC* s
    cdef FighterC* f
    cdef int8_t* turn
    cdef dict cache = {}
    cdef object subject
    cdef str key
    cdef int* scratch = b.rows
    cdef int8_t* results = b.paralyze_results
    for side in range(2):
        s = side_state(b, side)
        f = printed(b, side)
        turn = side_turn(b, side)
        subject = first_py if side == 0 else second_py
        key = round_key(b.round_index, side)
        # Every per-turn Attack grant is re-derived each round.
        for i in range(b.count):
            s.attacks_bonus_row[i] = 0
            s.injury_bonus_row[i] = 0
            s.black_hunger_active[i] = 0
        maximum = f.base_wounds
        # The Revenant's regeneration: one 5+ attempt per own turn, never
        # remembered when it fails.
        if f.revenant:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if (turn[row] and s.condition[row] != OUT and s.wounds[row] < maximum
                        and rng_draw_safe(&b.rng, 1, 6) >= 5):
                    s.wounds[row] = <int16_t>(s.wounds[row] + 1)
        # The Alchemist's brew, once at the start of this fighter's own turn.
        if f.alchemist_backley:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if not (turn[row] and s.condition[row] != OUT) or s.backley_used[row]:
                    continue
                # A Toughness test restores only the penalty actually applied:
                # a characteristic already at one was never reduced.
                if characteristic_test_one_c(f, s, row, s.toughness[row], &b.rng, 0):
                    s.strength[row] = <int16_t>(s.strength[row] + s.backley_strength[row])
                    s.initiative[row] = <int16_t>(s.initiative[row] + s.backley_initiative[row])
                    s.random_modifiers[1 * b.count + row] = <int16_t>(
                        s.random_modifiers[1 * b.count + row] + s.backley_strength[row])
                    s.random_modifiers[3 * b.count + row] = <int16_t>(
                        s.random_modifiers[3 * b.count + row] + s.backley_initiative[row])
                    s.backley_strength[row] = 0
                    s.backley_initiative[row] = 0
                    s.backley_used[row] = 1
        if f.alchemist_addicted:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if (not turn[row] or s.addiction_cured[row]
                        or s.condition[row] != STANDING):
                    continue
                if rng_draw_safe(&b.rng, 1, 6) == 6:
                    s.addiction_cured[row] = 1
                    if not f.alchemist_vigortia:
                        s.strength[row] = <int16_t>(s.strength[row] + 1)
                        s.toughness[row] = <int16_t>(s.toughness[row] + 1)
                        s.random_modifiers[1 * b.count + row] = <int16_t>(
                            s.random_modifiers[1 * b.count + row] + 1)
                        s.random_modifiers[2 * b.count + row] = <int16_t>(
                            s.random_modifiers[2 * b.count + row] + 1)
        # Herb Lore heals on a 4+; the printed outside-combat copy is the same
        # test with a recovery-contact exclusion.
        if f.herb_lore or f.herb_lore_outside:
            if decide_cached_c(decisions, cache, key + ".herb-lore", subject):
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if not turn[row] or s.condition[row] == OUT:
                        continue
                    if not f.herb_lore and b.engaged[row]:
                        continue
                    if (s.massively_built_lost_turn[row] or s.grappled[row]
                            or s.grappling[row] or s.netted[row]):
                        continue
                    if s.wounds[row] >= maximum:
                        continue
                    if rng_draw_safe(&b.rng, 1, 6) >= 4:
                        s.wounds[row] = <int16_t>(s.wounds[row] + 1)
        # The Rousing Sermon belongs to the preacher's own combat phase and
        # is preached once per battle; it grants that phase one Attack.
        if f.rousing_sermon:
            if decide_cached_c(decisions, cache, key + ".rousing-sermon", subject):
                for i in range(b.n_active):
                    row = b.active_rows[i]
                    if (turn[row] and not s.rousing_sermon_used[row]
                            and not s.massively_built_lost_turn[row]
                            and not s.grappled[row] and not s.grappling[row]
                            and not s.netted[row]
                            and (s.condition[row] == STANDING
                                 or s.condition[row] == KNOCKED_DOWN)):
                        s.rousing_sermon_used[row] = 1
                        s.attacks_bonus_row[row] = <int8_t>(s.attacks_bonus_row[row] + 1)
            # The compelled Impetuous charge may be thrown off at round zero.
        if b.first_round and f.impetuous_charge:
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if turn[row] and s.massively_built_lost_turn[row]:
                    continue
                scratch[m] = row
                m += 1
            if m and decide_cached_c(decisions, cache,
                                     key + ".impetuous-avoid-compulsion", subject):
                if leadership_c(b, side, f, scratch, m, key + ".impetuous-release",
                                decisions, cache, subject, 0, NULL, 0, 0, 0, 0, 1, 0,
                                NULL, results) < 0:
                    return -1
                for i in range(m):
                    if results[i]:
                        s.impetuous_released[scratch[i]] = 1
        # Petru's three potions each lapse on their own printed face.
        if f.petru_debilitating or f.petru_strength or f.petru_resilience:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if not turn[row] or s.condition[row] == OUT or s.petru_spent[row]:
                    continue
                roll = rng_draw_safe(&b.rng, 1, 6)
                if f.petru_debilitating and roll == 6:
                    s.toughness[row] = <int16_t>(s.toughness[row] + 1)
                    s.petru_spent[row] = 1
                elif (f.petru_strength or f.petru_resilience) and roll == 1:
                    if f.petru_strength and s.strength[row] > 1:
                        s.strength[row] = <int16_t>(s.strength[row] - 1)
                    if f.petru_resilience and s.toughness[row] > 1:
                        s.toughness[row] = <int16_t>(s.toughness[row] - 1)
                    s.petru_spent[row] = 1
        # Feral Instinct is taken on the beast's own turn: the test spends
        # this row's Leadership resources and dice, and records its failure.
        if f.feral_instinct:
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if turn[row] and s.condition[row] != OUT:
                    scratch[m] = row
                    m += 1
            if m and leadership_c(b, side, f, scratch, m,
                                  key + ".feral-instinct", decisions, cache, subject,
                                  0, NULL, 0, 0, 0, 0, 1, 0, NULL, results) < 0:
                return -1
            for i in range(m):
                s.feral_instinct_failed[scratch[i]] = 0 if results[i] else 1
        # The Danse Macabre control ends on its victim's own turn; a failure
        # at round zero also cancels that warrior's own initial charge.
        if 1:
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if turn[row] and s.condition[row] != OUT and s.danse_macabre_controlled[row]:
                    scratch[m] = row
                    m += 1
            if m:
                if leadership_c(b, side, f, scratch, m, key + ".danse-macabre",
                                decisions, cache, subject, 0, NULL, 0, 0, 0, 0, 1, 0,
                                NULL, results) < 0:
                    return -1
                for i in range(m):
                    row = scratch[i]
                    s.danse_macabre_controlled[row] = 0 if results[i] else 1
                    if (not results[i] and b.first_round
                            and side_charges(b, side)[row]):
                        side_charges(b, side)[row] = 0
                        if not (b.first_charges[row] or b.second_charges[row]):
                            b.engaged[row] = 0
        # The Bitten's transform is rolled on its own turn; a six enters the
        # form and casts the kit off, a one reverts it.  Madness (a one) is a
        # this-turn Stupidity, bounded by the turn that rolled it.
        if f.bitten_transform:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if s.bitten_result[row] == 1:
                    s.stupidity_failed[row] = 0
                s.bitten_result[row] = 0
                if not turn[row] or (s.transformed[row] and b.engaged[row]):
                    continue
                roll = rng_draw_safe(&b.rng, 1, 6)
                s.bitten_result[row] = <int8_t>roll
                if roll == 1:
                    # Reverting is a result of one, not an injury: the kit
                    # the form cast off is not recovered.
                    s.transformed[row] = 0
                elif roll == 6:
                    s.transformed[row] = 1
                    s.equipment_cast_off[row] = 1
                if s.transformed[row]:
                    s.frenzy[row] = 1
        # Lunatics prints EACH turn, so the producer runs every player turn.
        if f.lunatics:
            for i in range(b.n_active):
                row = b.active_rows[i]
                roll = rng_draw_safe(&b.rng, 1, 6)
                s.lunatic_result[row] = <int8_t>roll
                if roll <= 3:
                    s.frenzy[row] = 1
                else:
                    s.lunatic_stupidity[row] = 1
        # Devoted to the Vampire: the only Frenzy that ends by itself.
        if f.devoted_to_vampire:
            for i in range(b.n_active):
                row = b.active_rows[i]
                avenging = (f.devoted_vampire_killed
                            and side_state(b, 1 - side).condition[row] != OUT)
                if avenging or f.devoted_vampire_down:
                    s.frenzy[row] = 1
                    s.devoted_frenzy[row] = 1
                elif s.devoted_frenzy[row]:
                    s.frenzy[row] = 1 if f.frenzy_init else 0
                    s.devoted_frenzy[row] = 0
        # The Centigor's drunken result lasts only its own turn.
        for i in range(b.n_active):
            row = b.active_rows[i]
            if s.drunken_result[row] and not turn[row]:
                s.drunken_result[row] = 0
                s.stupidity_failed[row] = 0
                s.frenzy[row] = 1 if f.frenzy_init else 0
        if f.centigor_drunken:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if not turn[row]:
                    continue
                roll = rng_draw_safe(&b.rng, 1, 6)
                s.drunken_result[row] = <int8_t>roll
                s.frenzy[row] = 1 if roll == 6 else 0
                s.stupidity_failed[row] = 0
        # Animosity is tested only in the warrior's own turn: a one fails,
        # and the Fungus Brew's Rowdy result widens the band to one or two.
        for i in range(b.n_active):
            row = b.active_rows[i]
            s.animosity_failed[row] = 0
        if f.animosity:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if turn[row] and s.condition[row] == STANDING:
                    s.animosity_failed[row] = 1 if rng_draw_safe(&b.rng, 1, 6) <= (
                        2 if f.animosity_wide else 1) else 0
        # The poet's inspiration lifts Weapon Skill for the opening round only.
        if f.poetry_inspired:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if b.first_round:
                    s.poetry_active[row] = 1
                elif s.poetry_active[row]:
                    s.poetry_active[row] = 0
                    if s.weapon_skill[row] > 0:
                        s.weapon_skill[row] = <int16_t>(s.weapon_skill[row] - 1)
                    s.random_modifiers[0 * b.count + row] = <int16_t>(
                        s.random_modifiers[0 * b.count + row] - 1)
        # The already-active Command conditions and the Righteous Charge.
        for i in range(b.n_active):
            row = b.active_rows[i]
            s.follow_me_active[row] = 1 if (f.follow_me and b.first_round) else 0
            s.righteous_active[row] = 1 if (
                f.righteous_charge and b.first_round and printed(b, side).mounted
                and side_charges(b, 1 - side)[row]) else 0
            # Art Thou Ready To Die Fighting raises the threshold for its own
            # window: the opening round, and the bearer's own second one.
            s.death_fighting[row] = 1 if (f.death_fighting and (
                b.round_index < (2 if b.initial_first_turn[row] == (side == 0) else 1))) else 0
        # The Black Hunger activates on the bearer's own turn and grants one
        # Attack to the pool it opens; its backlash follows the blows.
        if f.black_hunger:
            for i in range(b.n_active):
                row = b.active_rows[i]
                if (turn[row] and not s.grappled[row] and not s.grappling[row]
                        and not s.netted[row] and s.condition[row] != OUT):
                    s.black_hunger_active[row] = 1
                    s.attacks_bonus_row[row] = <int8_t>(s.attacks_bonus_row[row] + 1)
    return 0


cdef int phase_characteristics_c(BatchC* b) except -1:
    """Refresh the variable profile (later rounds) and the Spawn's random
    attack count, each row through its own projection."""
    cdef GroupsC g
    cdef int k, i, j, side, row, stat, dice, sides, bonus, total
    cdef StateC* s
    cdef FighterC* f
    if b.round_index:
        for side in range(2):
            s = &b.s1 if side == 0 else &b.s2
            if group_rows_c(s, NULL, b.active_rows, b.n_active, &g) < 0:
                return -1
            try:
                for k in range(g.n_groups):
                    refresh_random_characteristics_c(
                        &b.tables.sides[side][g.p1[k]].f, s, g.rows + g.starts[k],
                        g.starts[k + 1] - g.starts[k], &b.rng)
            finally:
                groups_free(&g)
    for i in range(b.count):
        if fighter_at(&b.tables, 0, &b.s1, i).spawn:
            b.s1.attacks[i] = <int16_t>(rng_draw_safe(&b.rng, 1, 6) + 1)
        if fighter_at(&b.tables, 1, &b.s2, i).spawn:
            b.s2.attacks[i] = <int16_t>(rng_draw_safe(&b.rng, 1, 6) + 1)
    return 0


cdef int phase_equipment_c(BatchC* b, object table, object row_projections) except -1:
    """Project each row's effective fighter and clamp its Wounds.

    ``row_projections`` is the per-row projection request of this batch
    (``{"first": {row: CompiledFighter}, "second": {...}}``): each fighter is
    interned once in the ``ProjectionTable``, folded through ``compile_side``
    and mirrored into the C tables; the row then carries only the index.  The
    rule ports that produce a projection (a broken hand, the Bitten transform,
    the Hillman wolf, an acquired brand) write ``projection`` the same way.
    Equipment that is gone takes its numeric bonuses with it, so a row's
    Wounds cannot exceed the maximum of its projection
    (``modular/rounds.py`` post-projection clamp).
    """
    cdef int i, side, index, r
    cdef StateC* s
    cdef FighterC* f
    if row_projections is not None:
        for side in range(2):
            label = "first" if side == 0 else "second"
            mapping = row_projections.get(label) if hasattr(row_projections, "get") else None
            if not mapping:
                continue
            s = &b.s1 if side == 0 else &b.s2
            for row, fighter in mapping.items():
                i = <int>row
                if i < 0 or i >= b.count:
                    raise IndexError(f"row projection {row} outside the batch")
                index = <int>table.intern(label, fighter)
                if sync_projections_c(&b.tables, table) < 0:
                    return -1
                s.projection[i] = index
    # A broken hand (Sword-breaker) or the Bitten's transformation changes the
    # equipment this row fights with (``modular.equipment.equipment_for_state``
    # through the NumPy engine's ``phase_equipment``).  Only rows this step
    # projected itself are re-projected; other projections keep their owner.
    for side in range(2):
        label = "first" if side == 0 else "second"
        s = &b.s1 if side == 0 else &b.s2
        owned = None
        for i in range(b.n_active):
            r = b.active_rows[i]
            if not (s.broken_hands[r] or s.transformed[r] or s.equipment_cast_off[r]):
                continue
            if owned is None:
                owned = table.equipment_indices[label]
            if s.projection[r] != 0 and s.projection[r] not in owned:
                continue
            index = <int>table.equipment_row(
                label, s.broken_hands[r], s.transformed[r], s.equipment_cast_off[r],
                b.first_round)
            if sync_projections_c(&b.tables, table) < 0:
                return -1
            s.projection[r] = index
    for i in range(b.n_active):
        index = b.active_rows[i]
        f = fighter_at(&b.tables, 0, &b.s1, index)
        if b.s1.wounds[index] > f.starting_wounds:
            b.s1.wounds[index] = <int16_t>f.starting_wounds
        f = fighter_at(&b.tables, 1, &b.s2, index)
        if b.s2.wounds[index] > f.starting_wounds:
            b.s2.wounds[index] = <int16_t>f.starting_wounds
    return 0


cdef int phase_sustain_c(BatchC* b) except -1:
    """Later rounds: Force of Will is sustained, the burning fighter's own
    turn rolls its extinguish test and S4 hit, then rescues follow.  Returns
    the number of rows still live afterwards."""
    cdef GroupsC g
    cdef DuelC v
    cdef int k, i, row, m, side, gn
    cdef int* gr
    cdef StateC* s
    if b.round_index:
        for side in range(2):
            s = &b.s1 if side == 0 else &b.s2
            if group_rows_c(s, NULL, b.active_rows, b.n_active, &g) < 0:
                return -1
            try:
                for k in range(g.n_groups):
                    if sustain_force_of_will_c(&b.tables.sides[side][g.p1[k]].f, s, &b.rng,
                                               g.rows + g.starts[k],
                                               g.starts[k + 1] - g.starts[k]) < 0:
                        return -1
            finally:
                groups_free(&g)
        # Fire recovery is player-turn scoped like the oracle's _fire_recovery.
        for side in range(2):
            m = 0
            for i in range(b.n_active):
                row = b.active_rows[i]
                if (b.player_turn1[row] if side == 0 else b.player_turn2[row]):
                    b.rows[m] = row
                    m += 1
            if group_rows_c(&b.s1, &b.s2, b.rows, m, &g) < 0:
                return -1
            try:
                for k in range(g.n_groups):
                    view_c(&b.tables, g.p1[k], g.p2[k], &v)
                    if not (v.first.f.can_burn if side == 0 else v.second.f.can_burn):
                        continue
                    gr = g.rows + g.starts[k]
                    gn = g.starts[k + 1] - g.starts[k]
                    if side == 0:
                        if resolve_fire_c(&v, 0, &b.s1, &b.s2, &b.rng, gr, gn) < 0:
                            return -1
                    else:
                        if resolve_fire_c(&v, 1, &b.s2, &b.s1, &b.rng, gr, gn) < 0:
                            return -1
            finally:
                groups_free(&g)
        if rescue_force_of_will_rows_c(b, b.active_rows, b.n_active) < 0:
            return -1
    return refresh_unresolved_c(b)


cdef int rescue_force_of_will_rows_c(BatchC* b, const int* rows, int n) except -1:
    """Both sides' Force of Will rescue over ``rows``, per projection."""
    cdef GroupsC g
    cdef int k, side
    cdef StateC* s
    for side in range(2):
        s = &b.s1 if side == 0 else &b.s2
        if group_rows_c(s, NULL, rows, n, &g) < 0:
            return -1
        try:
            for k in range(g.n_groups):
                if rescue_force_of_will_c(&b.tables.sides[side][g.p1[k]].f, s,
                                          g.rows + g.starts[k],
                                          g.starts[k + 1] - g.starts[k], &b.rng) < 0:
                    return -1
        finally:
            groups_free(&g)
    return 0


cdef int phase_stand_up_c(BatchC* b, object round_counts) except -1:
    """Round bookkeeping and the player-turn scoped recovery
    (``modular/aftermath.py::_start_round_state`` and the paralysis and net
    steps of ``resolve_round``): the live rows are counted, the per-phase
    resources reset, a Paralyzed fighter tests Toughness in its own turn, a
    netted fighter cuts itself free (to Knocked Down) and then Knocked Down
    stands while Stunned recovers to Knocked Down."""
    cdef GroupsC g
    cdef int i, k, row, side, n_paralyze
    cdef StateC* s
    cdef int8_t* player_turn
    cdef int8_t* stood
    for i in range(b.n_active):
        row = b.active_rows[i]
        if round_counts is not None:
            round_counts[row] += 1
    for i in range(b.count):
        b.s1.parry_used[i] = 0
        b.s2.parry_used[i] = 0
        b.s1.seaguard_used[i] = 0
        b.s2.seaguard_used[i] = 0
        b.s1.corruption_used[i] = 0
        b.s2.corruption_used[i] = 0
        b.s1.parry_remaining[i] = <int8_t>fighter_at(&b.tables, 0, &b.s1, i).parry_capacity
        b.s2.parry_remaining[i] = <int8_t>fighter_at(&b.tables, 1, &b.s2, i).parry_capacity
        b.s1.critical_used[i] = 0
        b.s2.critical_used[i] = 0
        b.s1.attack_penalty[i] = 0
        b.s2.attack_penalty[i] = 0
        b.s1.hampered_main[i] = 0
        b.s2.hampered_main[i] = 0
        b.s1.hampered_off[i] = 0
        b.s2.hampered_off[i] = 0
    for side in range(2):
        s = &b.s1 if side == 0 else &b.s2
        player_turn = b.player_turn1 if side == 0 else b.player_turn2
        stood = b.stood1 if side == 0 else b.stood2
        # Paralyzed recovery: a Toughness test in the fighter's own turn.
        n_paralyze = 0
        for i in range(b.count):
            if s.condition[i] == PARALYZED and player_turn[i]:
                b.paralyze_rows[n_paralyze] = i
                n_paralyze += 1
        if n_paralyze:
            if group_rows_c(s, NULL, b.paralyze_rows, n_paralyze, &g) < 0:
                return -1
            try:
                for k in range(g.n_groups):
                    for i in range(g.starts[k], g.starts[k + 1]):
                        b.paralyze_targets[i] = s.toughness[g.rows[i]]
                    characteristic_tests_c(&b.tables.sides[side][g.p1[k]].f,
                                           g.rows + g.starts[k], g.starts[k + 1] - g.starts[k],
                                           b.paralyze_targets + g.starts[k], &b.rng, 0,
                                           b.paralyze_results + g.starts[k])
                for i in range(g.starts[g.n_groups]):
                    if b.paralyze_results[i]:
                        s.condition[g.rows[i]] = STANDING
            finally:
                groups_free(&g)
        for i in range(b.count):
            if not player_turn[i]:
                continue
            # Cutting free is the netted victim's own recovery: it drops to
            # Knocked Down and stands in the same recovery; a Stunned victim
            # first recovers to Knocked Down and stays caught this turn.
            if s.netted[i] and (s.condition[i] == STANDING or s.condition[i] == KNOCKED_DOWN):
                s.netted[i] = 0
                s.condition[i] = KNOCKED_DOWN
            if s.condition[i] == STUNNED:
                s.condition[i] = KNOCKED_DOWN
            elif s.condition[i] == KNOCKED_DOWN:
                s.condition[i] = STANDING
                stood[i] = 1
    return 0


cdef int phase_declarations_c(BatchC* b, object decisions, object replacements,
                              object first_py, object second_py) except -1:
    """The whole-pool attack replacements, plus the hooks still to be ported.

    ``select_attack_replacement`` offers Wraith Touch, the Vomit Attack, the
    Serpent Staff and the Death Blow removal in the oracle's printed order
    and stops at the first accepted offer.  Each offer is a projection that
    was interned before the batch, so an accepted offer simply moves the
    row's projection index and the whole pipeline then reads that fighter's
    own compiled scalars.

    Still unported and landing here: the Djinn's power, the grapple escape
    test, the Centigor's drunken result, Devoted to the Vampire and Animosity.
    """
    cdef int side, i, row, offer
    cdef bint removal, taken
    cdef str name
    cdef StateC* s
    cdef object subject
    cdef dict cache = {}
    if replacements is None:
        return 0
    if djinn_powers_c(b, decisions, first_py, second_py) < 0:
        return -1
    for side in range(2):
        if b.replacement_count[side] == 0:
            continue
        s = side_state(b, side)
        subject = first_py if side == 0 else second_py
        names = replacements["first" if side == 0 else "second"]
        for offer in range(b.replacement_count[side]):
            name = names[offer]
            # ``anvil-head`` and ``death-blow`` are removals: the projection
            # is taken when the player DECLINES, and Anvil Head only in the
            # first round and only on a charging row.
            removal = name == "anvil-head" or name == "death-blow"
            taken = decide_cached_c(decisions, cache,
                                    round_key(b.round_index, side) + "." + name,
                                    subject)
            if removal:
                taken = not taken
            if not taken:
                continue
            for i in range(b.n_active):
                row = b.active_rows[i]
                if name == "anvil-head" and not (
                        b.first_round and side_charges(b, side)[row]):
                    continue
                if s.projection[row] == 0:
                    s.projection[row] = b.replacement_index[side][offer]
            if not removal:
                # The oracle returns at the first accepted replacement.
                break
    return 0


cdef int phase_psychology_c(BatchC* b, object decisions, object first_py, object second_py) except -1:
    """Stupidity (every round, the active player's fighter) and Fear (round
    zero): ports of ``modular/psychology.py``.  They write
    ``stupidity_failed``, ``fear_hit_sixes``, the initial charge flags and
    ``engaged``; the Leadership tests read the supplied participants, sides,
    bands and distances of ``ContextC``.  Returns the live row count."""
    if stupidity_c(b, 0, decisions, first_py) < 0:
        return -1
    if stupidity_c(b, 1, decisions, second_py) < 0:
        return -1
    if refresh_unresolved_c(b) == 0:
        return 0
    if b.first_round:
        if fear_c(b, decisions, first_py, second_py) < 0:
            return -1
    b.insignia_window = 0
    return refresh_unresolved_c(b)


cdef int phase_pre_combat_c(BatchC* b, object decisions, object table,
                            object first_py, object second_py) except -1:
    """The combat-phase openers.  The charm block (Mesmerising Dance, Beauty
    of the Sea, the Eye Pendant, the Mark of Shornaal, the Hypnotist, Tranquil
    Fauna, the Lahmia powers and the Vampire control powers) is ported; the
    remaining openers (Crude Belch, the Inquisitor's brands, the mutation
    tail, Main Gauche modes, the Jester's trick, the Shadow Dance, the Sea
    Shanty, the Mantle of Crows) still land here."""
    cdef int side, i, row
    cdef StateC* s
    cdef FighterC* f
    if songs_and_belches_c(b, decisions, first_py, second_py) < 0:
        return -1
    if mutations_c(b, decisions, table, first_py, second_py) < 0:
        return -1
    if main_gauche_c(b, decisions, first_py, second_py) < 0:
        return -1
    if shadow_dances_c(b, decisions, first_py, second_py) < 0:
        return -1
    if jester_tricks_c(b, decisions, first_py, second_py) < 0:
        return -1
    if charms_c(b, decisions, first_py, second_py) < 0:
        return -1
    if grapple_c(b, decisions, first_py, second_py) < 0:
        return -1
    # Combat Charge is phase-local and follows the finalized charge gates.
    if b.first_round:
        for side in range(2):
            s = side_state(b, side)
            for i in range(b.n_active):
                row = b.active_rows[i]
                f = fighter_at(&b.tables, side, s, row)
                if side_charges(b, side)[row] and f.combat_charge:
                    require_characteristic_c(s, f, row, 0, &b.rng, b.count)
                    s.weapon_skill[row] += 1
                    s.combat_charge_active[row] = 1
    return 0


cdef int phase_reactions_c(BatchC* b) except -1:
    """The Netter's charge (round zero), the mutual Spines hits, the
    Chained Squig's entangle hits and the Force of Will rescue that follows."""
    cdef GroupsC g
    cdef DuelC v
    cdef PreparedC crow_prep
    cdef SourceC* src
    cdef SideC* mine
    cdef SideC* foe
    cdef int k, i, row, m, gn, side, ok
    cdef int impact_max, impact_index, impact_n
    cdef int* gr
    if b.first_round:
        for side in range(2):
            m = 0
            for i in range(b.count):
                if b.unresolved[i] and (b.charge1[i] if side == 0 else b.charge2[i]):
                    b.rows[m] = i
                    m += 1
            if group_rows_c(&b.s1, &b.s2, b.rows, m, &g) < 0:
                return -1
            try:
                for k in range(g.n_groups):
                    view_c(&b.tables, g.p1[k], g.p2[k], &v)
                    gr = g.rows + g.starts[k]
                    gn = g.starts[k + 1] - g.starts[k]
                    if side == 0:
                        if v.first.f.netter and netter_charge_c(&v.first.f, &v.second.f, gr, gn, &b.s2, &b.rng) < 0:
                            return -1
                    else:
                        if v.second.f.netter and netter_charge_c(&v.second.f, &v.first.f, gr, gn, &b.s1, &b.rng) < 0:
                            return -1
            finally:
                groups_free(&g)
    # The Wheelo's collision is resolved before crew and enemy weapon blows.
    for side in range(2):
        if not (printed(b, side).wheelo_impact and b.first_round):
            continue
        if group_rows_c(&b.s1, &b.s2, b.active_rows, b.n_active, &g) < 0:
            return -1
        try:
            for k in range(g.n_groups):
                view_c(&b.tables, g.p1[k], g.p2[k], &v)
                if side == 0:
                    mine = v.first
                    foe = v.second
                else:
                    mine = v.second
                    foe = v.first
                # The impact needs the charge it rides in on, or the spear
                # fitting's printed counter-charge.
                m = 0
                for i in range(g.starts[k], g.starts[k + 1]):
                    row = g.rows[i]
                    if (side_charges(b, side)[row]
                            or (mine.f.wheelo_spear and side_charges(b, 1 - side)[row])):
                        b.rows[m] = row
                        m += 1
                if m == 0:
                    continue
                # A charging Wheelo lands (D6+1)//2 impacts; the spear's
                # counter-impact is a single hit.  Only the first impact of a
                # morning star resolves at Strength 5.
                impact_max = 1
                for i in range(m):
                    row = b.rows[i]
                    if side_charges(b, side)[row]:
                        b.reply[i] = (rng_draw_safe(&b.rng, 1, 6) + 1) // 2
                    else:
                        b.reply[i] = 1
                    if b.reply[i] > impact_max:
                        impact_max = b.reply[i]
                for impact_index in range(impact_max):
                    impact_n = 0
                    for i in range(m):
                        row = b.rows[i]
                        if (b.reply[i] > impact_index
                                and side_state(b, side).condition[row] != OUT
                                and side_state(b, 1 - side).condition[row] != OUT):
                            b.paralyze_rows[impact_n] = row
                            impact_n += 1
                    if impact_n == 0:
                        continue
                    src = &mine.impact if impact_index == 0 else &mine.impact_more
                    ok = prepare_attack_c(&mine.f, &foe.f, src, b.paralyze_rows, impact_n, NULL,
                                          side_state(b, side), side_state(b, 1 - side),
                                          &b.rng, 0, &crow_prep)
                    if ok < 0:
                        return -1
                    if ok > 0:
                        if resolve_weapon_c(&v, side, src, &crow_prep, NULL,
                                            side_state(b, side), side_state(b, 1 - side),
                                            &b.rng, 0, NULL, 0, NULL, 0, 0, None, 1,
                                            None, None, None) < 0:
                            prepared_free(&crow_prep)
                            return -1
                        prepared_free(&crow_prep)
        finally:
            groups_free(&g)
    # The Crow Master's Mantle opens the combat phase, before the mutual
    # Spines hits and before any warrior's own blows.
    for side in range(2):
        if not printed(b, side).mantle_of_crows:
            continue
        if group_rows_c(&b.s1, &b.s2, b.active_rows, b.n_active, &g) < 0:
            return -1
        try:
            for k in range(g.n_groups):
                view_c(&b.tables, g.p1[k], g.p2[k], &v)
                src = &v.first.crows if side == 0 else &v.second.crows
                gr = g.rows + g.starts[k]
                gn = g.starts[k + 1] - g.starts[k]
                ok = prepare_attack_c(
                    &v.first.f if side == 0 else &v.second.f,
                    &v.second.f if side == 0 else &v.first.f,
                    src, gr, gn, NULL,
                    side_state(b, side), side_state(b, 1 - side), &b.rng, 0, &crow_prep)
                if ok < 0:
                    return -1
                if ok > 0:
                    if resolve_weapon_c(&v, side, src, &crow_prep, NULL,
                                        side_state(b, side), side_state(b, 1 - side),
                                        &b.rng, 0, NULL, 0, NULL, 0, 0, None, 1,
                                        None, None, None) < 0:
                        prepared_free(&crow_prep)
                        return -1
                    prepared_free(&crow_prep)
        finally:
            groups_free(&g)
    if group_rows_c(&b.s1, &b.s2, b.active_rows, b.n_active, &g) < 0:
        return -1
    try:
        for k in range(g.n_groups):
            view_c(&b.tables, g.p1[k], g.p2[k], &v)
            if v.first.f.spines or v.second.f.spines:
                if resolve_spines_c(&v, g.rows + g.starts[k], g.starts[k + 1] - g.starts[k],
                                    b.charge1, b.charge2, &b.s1, &b.s2, &b.rng) < 0:
                    return -1
    finally:
        groups_free(&g)
    for side in range(2):
        m = 0
        for i in range(b.count):
            if not b.unresolved[i]:
                continue
            if side == 1 and b.s1.entangled[i] and b.s2.condition[i] == STANDING:
                b.rows[m] = i
                m += 1
            elif side == 0 and b.s2.entangled[i] and b.s1.condition[i] == STANDING:
                b.rows[m] = i
                m += 1
        if group_rows_c(&b.s1, &b.s2, b.rows, m, &g) < 0:
            return -1
        try:
            for k in range(g.n_groups):
                view_c(&b.tables, g.p1[k], g.p2[k], &v)
                gr = g.rows + g.starts[k]
                gn = g.starts[k + 1] - g.starts[k]
                if side == 1 and v.second.f.entangle:
                    if resolve_entangle_c(&v, 1, gr, gn, b.charge2, &b.s2, &b.s1, &b.rng) < 0:
                        return -1
                elif side == 0 and v.first.f.entangle:
                    if resolve_entangle_c(&v, 0, gr, gn, b.charge1, &b.s1, &b.s2, &b.rng) < 0:
                        return -1
        finally:
            groups_free(&g)
    return rescue_force_of_will_rows_c(b, b.active_rows, b.n_active)


cdef int phase_pools_c(BatchC* b, object decisions, object first_py,
                       object second_py) except -1:
    """Attack counts, the opponent's incoming modifiers, the suppressed pools
    and the acting order (priority, Initiative, a coin for exact ties)."""
    cdef int i, index
    cdef FighterC* f1
    cdef FighterC* f2
    if attack_count_c(&b.tables, 0, &b.s1, b.charge1, b.player_turn1, b.first_round,
                      b.attacks1, b.count, &b.rng) < 0:
        return -1
    if attack_count_c(&b.tables, 1, &b.s2, b.charge2, b.player_turn2, b.first_round,
                      b.attacks2, b.count, &b.rng) < 0:
        return -1
    for i in range(b.count):
        f1 = fighter_at(&b.tables, 0, &b.s1, i)
        f2 = fighter_at(&b.tables, 1, &b.s2, i)
        if b.attacks1[i] > 0:
            b.attacks1[i] = <int16_t>(b.attacks1[i] + f2.incoming_attacks_modifier)
            if b.attacks1[i] < 1:
                b.attacks1[i] = 1
        else:
            b.attacks1[i] = 0
        if b.attacks2[i] > 0:
            b.attacks2[i] = <int16_t>(b.attacks2[i] + f1.incoming_attacks_modifier)
            if b.attacks2[i] < 1:
                b.attacks2[i] = 1
        else:
            b.attacks2[i] = 0
        if f1.animal_friendship_effective:
            b.attacks2[i] = 0
        if f2.animal_friendship_effective:
            b.attacks1[i] = 0
        if b.first_round:
            # A charging bearer keeps the Whipcrack bonus inside its pool;
            # the charged bearer's bonus is split into its own Strike First
            # event by ``schedule_whip_c`` below (``modular/rounds.py``).
            if f1.serpent_whip and b.charge1[i] and b.attacks1[i] > 0:
                b.attacks1[i] = <int16_t>(b.attacks1[i] + 1)
            if f2.serpent_whip and b.charge2[i] and b.attacks2[i] > 0:
                b.attacks2[i] = <int16_t>(b.attacks2[i] + 1)
            if f1.boar_spear and b.charge2[i]:
                b.attacks2[i] = <int16_t>(b.attacks2[i] - 1)
                if b.attacks2[i] < 1:
                    b.attacks2[i] = 1
            if f2.boar_spear and b.charge1[i]:
                b.attacks1[i] = <int16_t>(b.attacks1[i] - 1)
                if b.attacks1[i] < 1:
                    b.attacks1[i] = 1
            if f1.sigmar_effective and b.attacks2[i] > 0:
                b.attacks2[i] = <int16_t>(b.attacks2[i] - 1)
                if b.attacks2[i] < 1:
                    b.attacks2[i] = 1
            if f2.sigmar_effective and b.attacks1[i] > 0:
                b.attacks1[i] = <int16_t>(b.attacks1[i] - 1)
                if b.attacks1[i] < 1:
                    b.attacks1[i] = 1
        # The oracle silences the whole pool of a warrior on fire, held or
        # holding, controlled by the Danse Macabre, failing Stupidity or still
        # addicted to its own brew (``modular/rounds.py`` pool suppression).
        if (b.s1.on_fire[i] or b.s1.stupidity_failed[i] or b.s1.danse_macabre_controlled[i]
                or b.s1.grappled[i] or b.s1.grappling[i] or b.s1.charm_attack_blocked[i]
                or b.s1.entranced[i] or b.s1.animosity_failed[i]
                or (f1.alchemist_addicted and not b.s1.addiction_cured[i])):
            b.attacks1[i] = 0
        if (b.s2.on_fire[i] or b.s2.stupidity_failed[i] or b.s2.danse_macabre_controlled[i]
                or b.s2.grappled[i] or b.s2.grappling[i] or b.s2.charm_attack_blocked[i]
                or b.s2.entranced[i] or b.s2.animosity_failed[i]
                or (f2.alchemist_addicted and not b.s2.addiction_cured[i])):
            b.attacks2[i] = 0
        b.p1[i] = <int8_t>priority_row_c(f1, b.first_round, b.charge1[i], b.charge2[i],
                                         b.stood1[i], b.s1.dance_woven_mist[i])
        b.p2[i] = <int8_t>priority_row_c(f2, b.first_round, b.charge2[i], b.charge1[i],
                                         b.stood2[i], b.s2.dance_woven_mist[i])
        b.ini1[i] = <int16_t>effective_initiative_c(f1, &b.s1, i)
        b.ini2[i] = <int16_t>effective_initiative_c(f2, &b.s2, i)
        b.first_acts[i] = 1 if (b.p1[i] > b.p2[i]
                                or (b.p1[i] == b.p2[i] and b.ini1[i] > b.ini2[i])) else 0
    # Capture the allocation before any readiness clamp can zero it: the
    # printed Deathblow reads "the remainder of his attacks".
    for i in range(b.count):
        b.deathblow_pool[0][i] = b.attacks1[i]
        b.deathblow_pool[1][i] = b.attacks2[i]
    # Only a warrior standing when the pools are allocated strikes this round
    # (``modular/rounds.py``: ``condition != STANDING`` zeroes the count).  A
    # fighter down now and rescued later in the phase (Force of Will) does
    # not gain a pool of its own in the same round.
    for i in range(b.count):
        if b.s1.condition[i] != STANDING:
            b.attacks1[i] = 0
        if b.s2.condition[i] != STANDING:
            b.attacks2[i] = 0
    for i in range(b.count):
        if b.p1[i] == b.p2[i] and b.ini1[i] == b.ini2[i]:
            b.first_acts[i] = <int8_t>rng_coin(&b.rng)
    if schedule_whip_c(b) < 0:
        return -1
    if schedule_shifty_c(b, decisions, first_py, second_py) < 0:
        return -1
    return schedule_electrical_c(b, decisions, first_py, second_py)


cdef int schedule_whip_c(BatchC* b) except -1:
    """Schedule the charged bearer's Whipcrack bonus.

    The printed bonus joins the bearer's pool when he charges; only when he
    is *charged* is it split out as its own earlier event at the whip's
    Strike First tier, ``max(1, whip.priority)``, ordered against the
    enemy's pool by tier, Initiative and the printed tie roll
    (``modular/rounds.py`` whipcrack insertion).
    """
    cdef int side, i, row, bp, ep, oini, eini
    cdef FighterC* bonus
    cdef StateC* s
    cdef bint before
    for side in range(2):
        for i in range(b.count):
            b.whip_on[side][i] = 0
            b.whip_slot[side][i] = 0
            b.whip_done[side][i] = 0
        if not b.first_round or b.whip_count[side] == 0:
            continue
        s = side_state(b, side)
        bonus = &b.tables.sides[side][b.whip_index[side]].f
        for i in range(b.n_active):
            row = b.active_rows[i]
            # Only a charged, standing bearer with a live pool splits the
            # bonus out (a suppressed pool resolves nothing at all).
            if not side_charges(b, 1 - side)[row] or s.condition[row] != STANDING:
                continue
            if (b.attacks1[row] if side == 0 else b.attacks2[row]) <= 0:
                continue
            b.whip_on[side][row] = 1
            bp = bonus.weapon_priority
            if bp < 1:
                bp = 1
            ep = (b.p2[row] if side == 0 else b.p1[row])
            oini = (b.ini1[row] if side == 0 else b.ini2[row])
            eini = (b.ini2[row] if side == 0 else b.ini1[row])
            if bp > ep:
                before = 1
            elif bp < ep:
                before = 0
            else:
                before = oini > eini
                if oini == eini:
                    before = rng_coin(&b.rng)
            b.whip_slot[side][row] = 0 if before else 1
    return 0


cdef int whip_event_c(BatchC* b, int side, bint leading, object decisions,
                      object subject) except -1:
    """Resolve the scheduled Whipcrack bonus strikes due to strike now.

    One attack with the whip-only projection, exactly like the Shifty bonus:
    ``leading`` selects the rows whose bonus beat the enemy's earlier pool;
    otherwise it resolves immediately before its bearer's own pool.
    """
    cdef int i, row, m = 0
    cdef int16_t* one
    cdef StateC* s = side_state(b, side)
    if b.whip_count[side] == 0 or not b.first_round:
        return 0
    for i in range(b.n_active):
        row = b.active_rows[i]
        if not b.whip_on[side][row] or b.whip_done[side][row]:
            continue
        if leading and b.whip_slot[side][row] != 0:
            continue
        if s.condition[row] != STANDING:
            continue
        # ``b.rows``/``b.reply`` hold the caller's pool row lists; use the
        # recovery scratch, which is idle during the attack phase.
        b.paralyze_rows[m] = row
        m += 1
    if m == 0:
        return 0
    one = b.attacks1 if side == 0 else b.attacks2
    for i in range(m):
        row = b.paralyze_rows[i]
        b.whip_done[side][row] = 1
        b.shifty_saved[row] = one[row]
        one[row] = 1
        b.shifty_projection[row] = s.projection[row]
        s.projection[row] = b.whip_index[side]
    if attack_event_c(b, side, b.paralyze_rows, m, decisions,
                      None, ".whipcrack") < 0:
        return -1
    for i in range(m):
        row = b.paralyze_rows[i]
        one[row] = b.shifty_saved[row]
        s.projection[row] = b.shifty_projection[row]
    return 0


cdef int schedule_electrical_c(BatchC* b, object decisions, object first_py,
                               object second_py) except -1:
    """Declare the electrical jolt and place it in the phase's order.

    The bearer forfeits one blow of its own pool for a jolt whose Strength
    reads the victim's armour.  The oracle offers each allocated attack
    index in turn and takes the first the player accepts, then inserts the
    jolt into the event list at its own priority -- one point of Initiative
    above the bearer's ordinary blows (``modular/rounds.py``).
    """
    cdef int side, i, row, index, jolt_priority, jolt_ini, enemy
    cdef StateC* s
    cdef FighterC* f
    cdef dict cache = {}
    cdef object subject
    cdef bint before
    cdef str label
    for side in range(2):
        s = side_state(b, side)
        for i in range(b.count):
            b.jolt_on[side][i] = 0
            b.jolt_slot[side][i] = 0
            b.jolt_done[side][i] = 0
            s.electrical_forfeit[i] = -1
        f = printed(b, side)
        if not f.electrical_touch:
            continue
        subject = first_py if side == 0 else second_py
        label = round_key(b.round_index, side) + ".electrical-touch.forfeit."
        for i in range(b.n_active):
            row = b.active_rows[i]
            # The jolt is spent and recharges: it waits out its own cooldown.
            if (b.round_index < s.electrical_available_at[row]
                    or s.condition[row] != STANDING
                    or s.grappled[row] or s.grappling[row]):
                continue
            # Each allocated attack is offered in turn; the first accepted
            # index is the blow the jolt replaces.
            for index in range((b.attacks1 if side == 0 else b.attacks2)[row]):
                if decide_cached_c(decisions, cache, label + str(index), subject):
                    s.electrical_forfeit[row] = <int8_t>index
                    b.jolt_on[side][row] = 1
                    break
            if not b.jolt_on[side][row]:
                continue
            jolt_priority = priority_row_c(
                f, b.first_round, side_charges(b, side)[row],
                side_charges(b, 1 - side)[row],
                (b.stood1 if side == 0 else b.stood2)[row], s.dance_woven_mist[row])
            # The jolt strikes one point of Initiative ahead of its bearer.
            jolt_ini = effective_initiative_c(f, s, row) + 1
            enemy = (b.p2[row] if side == 0 else b.p1[row])
            if jolt_priority > enemy:
                before = 1
            elif jolt_priority < enemy:
                before = 0
            else:
                before = jolt_ini > (b.ini2[row] if side == 0 else b.ini1[row])
                if jolt_ini == (b.ini2[row] if side == 0 else b.ini1[row]):
                    before = rng_coin(&b.rng)
            b.jolt_slot[side][row] = 0 if before else 1
    return 0


cdef int jolt_event_c(BatchC* b, int side, bint leading, object decisions,
                      object subject) except -1:
    """Resolve the jolt for the rows due to strike now, then recharge it."""
    cdef int i, row, m = 0, k, ok, recharge
    cdef GroupsC g
    cdef DuelC v
    cdef SideC* mine
    cdef SideC* foe
    cdef PreparedC prep
    cdef StateC* s = side_state(b, side)
    cdef StateC* es = side_state(b, 1 - side)
    if not printed(b, side).electrical_touch:
        return 0
    for i in range(b.n_active):
        row = b.active_rows[i]
        if not b.jolt_on[side][row] or b.jolt_done[side][row]:
            continue
        if leading and b.jolt_slot[side][row] != 0:
            continue
        if s.condition[row] != STANDING:
            continue
        b.rows[m] = row
        m += 1
    if m == 0:
        return 0
    for i in range(m):
        b.jolt_done[side][b.rows[i]] = 1
    if group_rows_c(&b.s1, &b.s2, b.rows, m, &g) < 0:
        return -1
    try:
        for k in range(g.n_groups):
            view_c(&b.tables, g.p1[k], g.p2[k], &v)
            if side == 0:
                mine = v.first
                foe = v.second
            else:
                mine = v.second
                foe = v.first
            ok = prepare_attack_c(&mine.f, &foe.f, &mine.jolt,
                                  g.rows + g.starts[k],
                                  g.starts[k + 1] - g.starts[k], NULL,
                                  s, es, &b.rng, b.first_round, &prep)
            if ok < 0:
                return -1
            if ok > 0:
                if resolve_weapon_c(&v, side, &mine.jolt, &prep, NULL, s, es,
                                    &b.rng, b.first_round, NULL, 0, NULL, 0, 0,
                                    decisions, 1, subject, None, None) < 0:
                    prepared_free(&prep)
                    return -1
                prepared_free(&prep)
    finally:
        groups_free(&g)
    # The jolt recharges on its own D3 before it can be used again.
    for i in range(m):
        row = b.rows[i]
        recharge = rng_draw_safe(&b.rng, 1, 3)
        s.electrical_available_at[row] = <int8_t>(b.round_index + recharge)
    return 0


cdef int schedule_shifty_c(BatchC* b, object decisions, object first_py,
                           object second_py) except -1:
    """Nominate the Shifty strike and place it in the phase's order.

    Printed Shifty: a warrior that is charged in the first round strikes one
    extra blow with a weapon it nominates.  The oracle gives that blow its
    own priority -- at least the first tier -- and inserts it into the
    phase's event list, where it precedes its bearer's ordinary pool on an
    equal priority and is otherwise ordered against the enemy's pool by the
    same key the two pools use (``modular/rounds.py``).

    ``shifty_slot`` records, per row, whether the bonus strikes before the
    enemy's pool (0) or after it (1); the bonus always precedes its own
    bearer's ordinary pool, which is the oracle's same-side tie rule.
    """
    cdef int side, i, row, enemy, bonus_priority, bonus_ini
    cdef StateC* s
    cdef FighterC* bonus
    cdef dict cache = {}
    cdef object subject
    cdef bint before
    for side in range(2):
        for i in range(b.count):
            b.shifty_on[side][i] = 0
            b.shifty_slot[side][i] = 0
            b.shifty_done[side][i] = 0
        if not b.first_round or b.shifty_count[side] == 0:
            continue
        s = side_state(b, side)
        subject = first_py if side == 0 else second_py
        # The nomination is one declaration for the phase: the main weapon,
        # or the off hand when the player declines it.
        index = 0
        if b.shifty_count[side] > 1 and not decide_cached_c(
                decisions, cache,
                round_key(b.round_index, side) + ".shifty.main-weapon", subject):
            index = 1
        bonus = &b.tables.sides[side][b.shifty_index[side][index]].f
        for i in range(b.n_active):
            row = b.active_rows[i]
            # Only a warrior that is charged strikes the bonus blow, and a
            # silenced or non-standing pool strikes nothing at all.
            if not side_charges(b, 1 - side)[row] or s.condition[row] != STANDING:
                continue
            if (b.attacks1[row] if side == 0 else b.attacks2[row]) <= 0:
                continue
            b.shifty_choice[side] = index
            b.shifty_on[side][row] = 1
            bonus_priority = priority_row_c(
                bonus, 1, side_charges(b, side)[row], side_charges(b, 1 - side)[row],
                (b.stood1 if side == 0 else b.stood2)[row], s.dance_woven_mist[row])
            if bonus_priority >= 0 and bonus_priority < 1:
                bonus_priority = 1
            bonus_ini = effective_initiative_c(bonus, s, row)
            enemy = (b.p2[row] if side == 0 else b.p1[row])
            if bonus_priority > enemy:
                before = 1
            elif bonus_priority < enemy:
                before = 0
            else:
                before = bonus_ini > (b.ini2[row] if side == 0 else b.ini1[row])
                if bonus_ini == (b.ini2[row] if side == 0 else b.ini1[row]):
                    before = rng_coin(&b.rng)
            b.shifty_slot[side][row] = 0 if before else 1
    return 0


cdef int attack_event_c(BatchC* b, int side, const int* rows, int n, object decisions,
                        object attacker_py, str suffix=None) except -1:
    """One side's attack pool over ``rows``, each row group through its own
    pair of projections, followed by both Force of Will rescues."""
    cdef GroupsC g
    cdef DuelC v
    cdef int k
    cdef str prefix = round_key(b.round_index, side) + (suffix if suffix is not None else "")
    cdef int i
    cdef const int16_t* attacks = b.attacks1 if side == 0 else b.attacks2
    cdef StateC* s = &b.s1 if side == 0 else &b.s2
    if n == 0:
        return 0
    # The pool was taken against its victim (Seduction's printed release).
    for i in range(n):
        if attacks[rows[i]] > 0:
            s.attacked_this_phase[rows[i]] = 1
    if group_rows_c(&b.s1, &b.s2, rows, n, &g) < 0:
        return -1
    try:
        for k in range(g.n_groups):
            view_c(&b.tables, g.p1[k], g.p2[k], &v)
            if side == 0:
                if resolve_attacks_c(&v, 0, g.rows + g.starts[k], g.starts[k + 1] - g.starts[k],
                                     b.attacks1, b.charge1, &b.s1, &b.s2, &b.rng, b.first_round,
                                     decisions, attacker_py, prefix, b.charge2) < 0:
                    return -1
            else:
                if resolve_attacks_c(&v, 1, g.rows + g.starts[k], g.starts[k + 1] - g.starts[k],
                                     b.attacks2, b.charge2, &b.s2, &b.s1, &b.rng, b.first_round,
                                     decisions, attacker_py, prefix, b.charge1) < 0:
                    return -1
    finally:
        groups_free(&g)
    return rescue_force_of_will_rows_c(b, rows, n)


cdef int shifty_event_c(BatchC* b, int side, bint leading, object decisions,
                        object subject) except -1:
    """Resolve the one-attack Shifty bonus for the rows due to strike now.

    ``leading`` selects the rows whose bonus must also precede the enemy's
    earlier pool (the oracle's insertion found a position ahead of it);
    otherwise every remaining row of this side strikes its bonus here, which
    is immediately before its own pool -- the same-side tie rule.
    """
    cdef int i, row, m = 0
    cdef int16_t* one
    cdef StateC* s = side_state(b, side)
    if b.shifty_count[side] == 0 or not b.first_round:
        return 0
    for i in range(b.n_active):
        row = b.active_rows[i]
        if not b.shifty_on[side][row] or b.shifty_done[side][row]:
            continue
        if leading and b.shifty_slot[side][row] != 0:
            continue
        if s.condition[row] != STANDING:
            continue
        b.rows[m] = row
        m += 1
    if m == 0:
        return 0
    # One attack, struck with the nominated weapon's own projection.
    one = b.attacks1 if side == 0 else b.attacks2
    for i in range(m):
        row = b.rows[i]
        b.shifty_done[side][row] = 1
        b.shifty_saved[row] = one[row]
        one[row] = 1
        b.shifty_projection[row] = s.projection[row]
        s.projection[row] = b.shifty_index[side][b.shifty_choice[side]]
    if attack_event_c(b, side, b.rows, m, decisions,
                      None, ".shifty") < 0:
        return -1
    for i in range(m):
        row = b.rows[i]
        one[row] = b.shifty_saved[row]
        s.projection[row] = b.shifty_projection[row]
    return 0


cdef int phase_attacks_c(BatchC* b, object decisions, object first_py, object second_py) except -1:
    """The acting fighter strikes, the surviving target replies; then the
    other orientation.  Reply rows are scanned from the replying fighter's own
    standing state, never derived from the primary's row set."""
    cdef int i, n_rows, n_reply
    # A bonus whose priority beat the enemy's pool strikes before everything.
    if shifty_event_c(b, 0, 1, decisions, first_py) < 0:
        return -1
    if whip_event_c(b, 0, 1, decisions, first_py) < 0:
        return -1
    if shifty_event_c(b, 1, 1, decisions, second_py) < 0:
        return -1
    if whip_event_c(b, 1, 1, decisions, second_py) < 0:
        return -1
    if jolt_event_c(b, 0, 1, decisions, first_py) < 0:
        return -1
    if jolt_event_c(b, 1, 1, decisions, second_py) < 0:
        return -1
    # A silenced warrior (Stupidity, fire, a charm...) contributes no pool at
    # all, so its independent extra attacks do not strike either: only rows
    # with an allocated pool take part (``vectorized._driver`` event rows).
    # First fighter acts first.
    n_rows = 0
    for i in range(b.count):
        if (b.unresolved[i] and b.s1.condition[i] == STANDING and b.first_acts[i]
                and b.attacks1[i] > 0):
            b.rows[n_rows] = i
            n_rows += 1
    if shifty_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if whip_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if jolt_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if attack_event_c(b, 0, b.rows, n_rows, decisions, first_py) < 0:
        return -1
    n_reply = 0
    for i in range(b.count):
        if (b.unresolved[i] and b.s2.condition[i] == STANDING and b.first_acts[i]
                and b.attacks2[i] > 0):
            b.reply[n_reply] = i
            n_reply += 1
    if shifty_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if whip_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if jolt_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if attack_event_c(b, 1, b.reply, n_reply, decisions, second_py) < 0:
        return -1
    # Second fighter acts first.
    n_rows = 0
    for i in range(b.count):
        if (b.unresolved[i] and b.s2.condition[i] == STANDING and not b.first_acts[i]
                and b.attacks2[i] > 0):
            b.rows[n_rows] = i
            n_rows += 1
    if shifty_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if whip_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if jolt_event_c(b, 1, 0, decisions, second_py) < 0:
        return -1
    if attack_event_c(b, 1, b.rows, n_rows, decisions, second_py) < 0:
        return -1
    n_reply = 0
    for i in range(b.count):
        if (b.unresolved[i] and b.s1.condition[i] == STANDING and not b.first_acts[i]
                and b.attacks1[i] > 0):
            b.reply[n_reply] = i
            n_reply += 1
    if shifty_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if whip_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if jolt_event_c(b, 0, 0, decisions, first_py) < 0:
        return -1
    if attack_event_c(b, 0, b.reply, n_reply, decisions, first_py) < 0:
        return -1
    if slayer_deathblow_c(b, decisions, first_py, second_py) < 0:
        return -1
    return last_events_c(b, decisions, first_py, second_py)


cdef int slayer_deathblow_c(BatchC* b, object decisions, object first_py,
                            object second_py) except -1:
    """Printed Deathblow: a Slayer taken out of action in hand-to-hand is
    entitled to the attacks he has still to make.

    The pool the phase allocated was captured before his own readiness could
    zero it, so a Slayer who went down during this very phase reuses exactly
    that allocation (``modular/rounds.py``).
    """
    cdef int side, i, row, m
    cdef StateC* s
    cdef StateC* es
    cdef dict cache = {}
    cdef object subject
    for side in range(2):
        if not printed(b, side).slayer_deathblow:
            continue
        s = side_state(b, side)
        es = side_state(b, 1 - side)
        subject = first_py if side == 0 else second_py
        m = 0
        for i in range(b.n_active):
            row = b.active_rows[i]
            if (s.condition[row] == OUT and es.condition[row] != OUT
                    and b.deathblow_pool[side][row] > 0):
                b.rows[m] = row
                m += 1
        if m == 0:
            continue
        if not decide_cached_c(decisions, cache,
                               round_key(b.round_index, side) + ".deathblow", subject):
            continue
        for i in range(m):
            row = b.rows[i]
            (b.attacks1 if side == 0 else b.attacks2)[row] = b.deathblow_pool[side][row]
        if attack_event_c(b, side, b.rows, m, decisions, subject, ".deathblow") < 0:
            return -1
    return 0


cdef int last_events_c(BatchC* b, object decisions, object first_py,
                       object second_py) except -1:
    """The separately timed blows that follow both warriors' weapon attacks.

    The Noblesse stomp is one extra blow against a foe already on the
    ground, inserted immediately after its bearer's own pool; the Priest's
    bite is its own final event, which is why the pool never allocated it.
    """
    cdef int side, i, row, m, e, k, ok
    cdef GroupsC g
    cdef DuelC v
    cdef SourceC* src
    cdef SideC* mine
    cdef SideC* foe
    cdef StateC* s
    cdef StateC* es
    cdef PreparedC prep
    cdef object subject
    cdef dict cache = {}
    for side in range(2):
        s = side_state(b, side)
        es = side_state(b, 1 - side)
        subject = first_py if side == 0 else second_py
        m = 0
        for i in range(b.n_active):
            row = b.active_rows[i]
            if (s.condition[row] == STANDING and es.condition[row] != OUT
                    and not s.grappling[row] and not s.grappled[row]
                    and (b.attacks1 if side == 0 else b.attacks2)[row] > 0):
                b.reply[m] = row
                m += 1
        if m == 0:
            continue
        if group_rows_c(&b.s1, &b.s2, b.reply, m, &g) < 0:
            return -1
        try:
            for k in range(g.n_groups):
                view_c(&b.tables, g.p1[k], g.p2[k], &v)
                # The stomp only reaches a foe already knocked down.
                if (printed(b, side).noblesse_stomp
                        and es.condition[g.rows[g.starts[k]]] == KNOCKED_DOWN):
                    src = &v.first.stomp if side == 0 else &v.second.stomp
                    ok = prepare_attack_c(
                        &v.first.f if side == 0 else &v.second.f,
                        &v.second.f if side == 0 else &v.first.f, src,
                        g.rows + g.starts[k], g.starts[k + 1] - g.starts[k],
                        NULL, s, es, &b.rng, b.first_round, &prep)
                    if ok < 0:
                        return -1
                    if ok > 0:
                        if resolve_weapon_c(&v, side, src, &prep, NULL, s, es, &b.rng,
                                            b.first_round, NULL, 0, NULL, 0, 0,
                                            decisions, 1, subject, None, None) < 0:
                            prepared_free(&prep)
                            return -1
                        prepared_free(&prep)
                if side == 0:
                    mine = v.first
                    foe = v.second
                else:
                    mine = v.second
                    foe = v.first
                for e in range(mine.f.last_bite_count):
                    src = &mine.f.last_bite[e]
                    ok = prepare_attack_c(&mine.f, &foe.f, src,
                                          g.rows + g.starts[k],
                                          g.starts[k + 1] - g.starts[k],
                                          NULL, s, es, &b.rng, b.first_round, &prep)
                    if ok < 0:
                        return -1
                    if ok > 0:
                        if resolve_weapon_c(&v, side, src, &prep, NULL, s, es, &b.rng,
                                            b.first_round, NULL, 0, NULL, 0, 0,
                                            decisions, 1, subject, None, None) < 0:
                            prepared_free(&prep)
                            return -1
                        prepared_free(&prep)
        finally:
            groups_free(&g)
    return 0


cdef int phase_aftermath_c(BatchC* b) except -1:
    """Seduction's release and the Black Hunger's backlash on its bearer."""
    cdef GroupsC g
    cdef DuelC v
    cdef int k, side, i
    cdef StateC* s
    seduction_release_c(b)
    if group_rows_c(&b.s1, &b.s2, b.active_rows, b.n_active, &g) < 0:
        return -1
    try:
        for k in range(g.n_groups):
            view_c(&b.tables, g.p1[k], g.p2[k], &v)
            for side in range(2):
                if (v.first.f.black_hunger if side == 0 else v.second.f.black_hunger):
                    if black_hunger_backlash_c(&v, side, &b.s1 if side == 0 else &b.s2, &b.rng,
                                               g.rows + g.starts[k],
                                               g.starts[k + 1] - g.starts[k]) < 0:
                        return -1
    finally:
        groups_free(&g)
    for side in range(2):
        s = side_state(b, side)
        for i in range(b.count):
            if s.combat_charge_active[i]:
                s.weapon_skill[i] -= 1
                s.combat_charge_active[i] = 0
    return 0


cdef int simulate_batch_c(BatchC* b, uint64_t seed, object callback, object decisions,
                          object first_py, object second_py, object table,
                          object row_projections, object observation,
                          int* out_a, int* out_b, int* out_u,
                          object replacements=None) except -1:
    """Run ``count`` duels end to end through the fixed phase pipeline."""
    cdef int i, round_index, wins_a = 0, wins_b = 0
    cdef object round_counts = None
    global _active_rng
    rng_init(&b.rng, seed, callback)
    _active_rng = &b.rng
    if init_state_c(&b.tables.sides[0][0].f, &b.s1, b.count, &b.rng) < 0:
        return -1
    if init_state_c(&b.tables.sides[1][0].f, &b.s2, b.count, &b.rng) < 0:
        return -1
    if init_charges_c(b) < 0:
        return -1
    if observation is not None:
        round_counts = np.zeros(b.count, dtype=np.int64)
    for round_index in range(b.maximum_rounds):
        b.round_index = round_index
        b.first_round = round_index == 0
        if refresh_unresolved_c(b) == 0:
            break
        trace_phase_c("round-start")
        if phase_round_start_c(b) < 0:
            return -1
        trace_phase_c("own-turn-recovery")
        if phase_own_turn_recovery_c(b, decisions, first_py, second_py) < 0:
            return -1
        trace_phase_c("characteristics")
        if phase_characteristics_c(b) < 0:
            return -1
        trace_phase_c("equipment")
        if phase_equipment_c(b, table, row_projections) < 0:
            return -1
        trace_phase_c("sustain")
        if phase_sustain_c(b) == 0:
            break
        trace_phase_c("stand-up")
        if phase_stand_up_c(b, round_counts) < 0:
            return -1
        trace_phase_c("declarations")
        if phase_declarations_c(b, decisions, replacements, first_py, second_py) < 0:
            return -1
        trace_phase_c("psychology")
        if phase_psychology_c(b, decisions, first_py, second_py) == 0:
            break
        trace_phase_c("pre-combat")
        if phase_pre_combat_c(b, decisions, table, first_py, second_py) < 0:
            return -1
        trace_phase_c("reactions")
        if phase_reactions_c(b) < 0:
            return -1
        trace_phase_c("pools")
        if phase_pools_c(b, decisions, first_py, second_py) < 0:
            return -1
        trace_phase_c("attacks")
        if phase_attacks_c(b, decisions, first_py, second_py) < 0:
            return -1
        trace_phase_c("aftermath")
        if phase_aftermath_c(b) < 0:
            return -1
    # Winner accounting (accumulates across batches: the driver passes the
    # same out slots for every batch of one simulation run).
    for i in range(b.count):
        if b.s2.condition[i] == OUT and b.s1.condition[i] != OUT:
            wins_a += 1
        elif b.s1.condition[i] == OUT and b.s2.condition[i] != OUT:
            wins_b += 1
    out_a[0] += wins_a
    out_b[0] += wins_b
    out_u[0] += b.count - wins_a - wins_b
    if observation is not None:
        from mordheim_combat.vectorized._types import VectorBatchObservation
        first_state = observe_state_c(&b.s1)
        second_state = observe_state_c(&b.s2)
        winner = np.zeros(b.count, dtype=np.int8)
        for i in range(b.count):
            if b.s2.condition[i] == OUT and b.s1.condition[i] != OUT:
                winner[i] = 1
            elif b.s1.condition[i] == OUT and b.s2.condition[i] != OUT:
                winner[i] = -1
        observation["result"] = VectorBatchObservation(
            winner, round_counts, first_state[0], second_state[0],
            first_state[1], second_state[1], first_state[2], second_state[2],
        )
        observation["projection"] = (
            np.asarray([b.s1.projection[i] for i in range(b.count)], dtype=np.int32),
            np.asarray([b.s2.projection[i] for i in range(b.count)], dtype=np.int32),
        )
    return 0


cdef int _run_batch(object table, int count, uint64_t seed, int maximum_rounds,
                    object decisions, object first_py, object second_py,
                    int* a, int* b_out, int* u,
                    object callback, object context, object observation,
                    object row_projections, object trace) except -1:
    global _rng_callback, _batch_running, _decision_log, _phase_trace, _ctx_ids
    cdef BatchC b
    cdef int _side, _offer
    cdef str _label
    cdef object _modes
    if _batch_running:
        raise RuntimeError("nested native combat batches are not supported")
    if count < 1 or maximum_rounds < 0:
        raise ValueError("native batch requires count >= 1 and maximum_rounds >= 0")
    _batch_running = True
    memset(&b, 0, sizeof(BatchC))
    try:
        if trace is not None:
            _decision_log = []
            _phase_trace = []
        b.maximum_rounds = maximum_rounds
        if batch_alloc_c(&b, count) < 0:
            raise MemoryError("native batch allocation failed")
        if sync_projections_c(&b.tables, table) < 0:
            raise MemoryError("native projection table allocation failed")
        # Intern the whole-pool replacements once, before the first round.
        for _side in range(2):
            _label = "first" if _side == 0 else "second"
            _offers = (getattr(table, "replacements", None) or {}).get(_label, ())
            b.replacement_count[_side] = min(len(_offers), 6)
            for _offer in range(b.replacement_count[_side]):
                b.replacement_index[_side][_offer] = <int>table.intern(
                    _label, table.replacement_fighters[_label][_offer])
            _modes = (getattr(table, "gauche_fighters", None) or {}).get(_label, ())
            for _offer in range(min(len(_modes), 2)):
                b.gauche_index[_side][_offer] = <int>table.intern(_label, _modes[_offer])
            _modes = (getattr(table, "shifty_fighters", None) or {}).get(_label, ())
            b.shifty_count[_side] = min(len(_modes), 2)
            for _offer in range(b.shifty_count[_side]):
                b.shifty_index[_side][_offer] = <int>table.intern(_label, _modes[_offer])
            _modes = (getattr(table, "whip_fighters", None) or {}).get(_label, ())
            b.whip_count[_side] = min(len(_modes), 1)
            if b.whip_count[_side]:
                b.whip_index[_side] = <int>table.intern(_label, _modes[0])
        if sync_projections_c(&b.tables, table) < 0:
            raise MemoryError("native projection table allocation failed")
        if fill_context(context, &b.ctx) < 0:
            raise MemoryError("native context allocation failed")
        _ctx_ids = None if context is None else [row["id"] for row in context["participants"]]
        if simulate_batch_c(&b, seed, callback, decisions, first_py, second_py, table,
                            row_projections, observation, a, b_out, u,
                            None if table is None else getattr(table, "replacements", None)) < 0:
            return -1
        if trace is not None:
            trace["phases"] = list(_phase_trace)
            trace["decisions"] = list(_decision_log)
    finally:
        batch_free_c(&b)
        _rng_callback = None
        _decision_log = None
        _phase_trace = None
        _ctx_ids = None
        _active_rng = NULL
        _batch_running = False
    return 0


# ---------------------------------------------------------------------------
# Public entry points consumed by mordheim_combat.vectorized
# ---------------------------------------------------------------------------

def supports_plan(plan):
    """Capacity gate evaluated by the vectorized dispatch before selection."""
    from mordheim_combat._combat_compile import MAX_EXTRA_ATTACKS
    if len(plan.first.extra_attacks) > MAX_EXTRA_ATTACKS:
        return False
    if len(plan.second.extra_attacks) > MAX_EXTRA_ATTACKS:
        return False
    return True


def _prepare(first, second, context):
    """Validate the duel start as the oracle does and fold its inputs."""
    from mordheim_combat._combat_compile import NotSupported
    from mordheim_combat._combat_compile import ProjectionTable
    from mordheim_combat._combat_compile import compile_context
    from mordheim_combat._combat_compile import compile_duel
    from mordheim_combat.vectorized._state import validate_duel_start
    from mordheim_core.context import prepare_duel_context
    validate_duel_start(first, second, context)
    try:
        compile_duel(first, second)
        table = ProjectionTable(first, second)
    except NotSupported as error:
        raise RuntimeError(
            f"native combat backend does not support this duel plan: {error}"
        ) from error
    return table, compile_context(prepare_duel_context(first, second, context))


def simulate_duel(request, plan):
    """Run a duel request through the compiled core (mirror of the NumPy
    driver; per-batch PCG32 streams derived from the request seed)."""
    from mordheim_core.models import DuelResult
    from mordheim_core.models import SimulationCancelled
    table, context = _prepare(request.first, request.second, request.context)
    cdef uint64_t seed
    cdef int a, b, u
    remaining = request.simulations
    a = 0
    b = 0
    u = 0
    batch_index = 0
    while remaining:
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise SimulationCancelled("simulation cancelled")
        count = min(remaining, request.batch_size)
        seed = (<uint64_t>(int(request.seed) & 0xFFFFFFFFFFFFFFFF)
                + <uint64_t>batch_index * 0x9E3779B97F4A7C15ULL)
        if _run_batch(table, count, seed, request.maximum_rounds,
                      request.decision_policy, request.first, request.second,
                      &a, &b, &u, None, context, None, None, None) < 0:
            raise RuntimeError("native combat backend failed")
        remaining -= count
        batch_index += 1
    return DuelResult(a, b, u, request.simulations)


def simulate_batch_observed(first, second, count, rng, maximum_rounds,
                            decisions=None, context=None, *,
                            row_projections=None, trace=None):
    """Replay the real native batch core with a NumPy-style scripted source.

    Integer calls use NumPy's exclusive high bound; charge and priority ties
    consume ``random(1)``.  Observations own their buffers after core cleanup.
    Native batches reject reentry while a callback or decision is executing.

    ``row_projections`` requests per-row effective fighters
    (``{"first": {row: CompiledFighter}, "second": {...}}``), applied every
    round in the equipment phase.  ``trace`` is a dict that receives the
    ``phases`` executed and the ``decisions`` asked, in order.
    """
    if rng is None:
        raise ValueError("observed native batch requires an explicit RNG source")
    table, prepared = _prepare(first, second, context)
    observation = {}
    cdef int a = 0, b = 0, u = 0
    if _run_batch(table, count, 0, maximum_rounds, decisions, first, second,
                  &a, &b, &u, rng, prepared, observation, row_projections, trace) < 0:
        raise RuntimeError("native combat backend failed")
    if trace is not None:
        trace["projection"] = observation["projection"]
    return observation["result"]
