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
from libc.stdint cimport int8_t
from libc.stdint cimport uint32_t
from libc.stdint cimport uint64_t
from libc.stdlib cimport free
from libc.stdlib cimport malloc
from libc.string cimport memcpy
from libc.string cimport memset




# Combat conditions, matching mordheim_combat.phases.Condition.
cdef enum:
    STANDING = 0
    KNOCKED_DOWN = 1
    STUNNED = 2
    PARALYZED = 3
    OUT = 4


# Effect value layout: index order MUST equal kernel.EFFECT_VALUE_FIELDS
# (verified at import time against the runtime kernel tuple).
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
    F_MAXIMUM_WOUND_TARGET = 45
    F_ARMOUR_SAVE_FLOOR = 46
    F_ARMOUR_CANNOT_BE_IGNORED = 47
    F_WARD_SAVE_MUNDANE_ONLY = 48
    F_NATURAL_ARMOUR_NEGATED_BY_MAGIC = 49
    F_REGENERATION_BLOCKED_BY_FIRE = 50
    F_REGENERATION_BLOCKED_BY_BLESSED = 51
    F_IGNITION_THRESHOLD = 52
    F_CAUGHT_FIRE_THRESHOLD = 53

N_EFFECT_FIELDS = 54

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


cdef struct Rng:
    PCG32 pcg
    bint use_callback


cdef inline void rng_init(Rng* r, uint64_t seed, object callback) noexcept:
    global _rng_callback
    pcg32_seed(&r.pcg, seed)
    _rng_callback = callback
    r.use_callback = callback is not None


cdef int rng_draw_cb(Rng* r, int low, int high) except -1:
    arr = _rng_callback.integers(low, high, 1)
    return int(arr[0])


cdef inline int rng_draw(Rng* r, int low, int high) noexcept:
    if not r.use_callback:
        return <int>pcg32_bounded(&r.pcg, <uint32_t>(high - low + 1)) + low
    # Callback errors are routed by the calling site (draw helpers are used
    # from ``except *`` core functions through rng_draw_cb below).
    return 0


cdef inline int rng_draw_safe(Rng* r, int low, int high) except -1:
    """Draw helper callable from functions that propagate exceptions."""
    if not r.use_callback:
        return <int>pcg32_bounded(&r.pcg, <uint32_t>(high - low + 1)) + low
    return rng_draw_cb(r, low, high)


# ---------------------------------------------------------------------------
# Compiled data structures (filled once per duel from _combat_compile dicts)
# ---------------------------------------------------------------------------

cdef struct EffectC:
    int v[54]


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
    bint kusara
    bint chained
    bint anvil
    bint counter_cutlass
    bint flammable_double
    bint nightshade
    bint spider_spittle
    bint web_of_steel
    bint poisonous_injury
    bint head_crusher
    bint fire
    bint horned_one
    int critical_threshold
    int ignition
    int ward
    int regeneration
    int damage


cdef struct FighterC:
    int ws, s, t, w, ini, a
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
    int out_of_action_threshold
    bint poison_immune
    int incoming_strength_modifier
    int incoming_attacks_modifier
    bint thick_skull
    bint injury_reroll_out
    bint hard_to_kill
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
    # parry flags (defender role)
    bint parry_parry
    bint parry_match_allowed
    bint parry_starblade
    bint parry_can_parry_six
    bint parry_dwarf_axes
    bint parry_parry_reroll
    # attack sources (weapon + merged effect per attack type)
    SourceC main
    SourceC unpredictable
    SourceC off
    bint has_unpredictable
    bint off_present
    SourceC extras[MAX_EXTRA_ATTACKS]
    int extra_count
    # random characteristics: rows of (stat_index, dice, sides, bonus)
    int random_characteristics[MAX_RANDOM_CHARACTERISTICS][4]
    int random_characteristics_count


cdef struct DuelC:
    FighterC first
    FighterC second
    SourceC bull_first, bull_second
    SourceC body_first, body_second
    SourceC spines_first, spines_second
    SourceC backlash_first, backlash_second
    SourceC fire_first, fire_second
    SourceC entangle_first, entangle_second
    SourceC hug_first, hug_second
    SourceC acid_first, acid_second
    SourceC counter_first, counter_second


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
    out.kusara = _flag(f, "kusara")
    out.chained = _flag(f, "chained")
    out.anvil = _flag(f, "anvil")
    out.counter_cutlass = _flag(f, "counter_cutlass")
    out.flammable_double = _flag(f, "flammable_double")
    out.nightshade = _flag(f, "nightshade")
    out.spider_spittle = _flag(f, "spider_spittle")
    out.web_of_steel = _flag(f, "web_of_steel")
    out.poisonous_injury = _flag(f, "poisonous_injury")
    out.head_crusher = _flag(f, "head_crusher")
    out.fire = _flag(f, "fire")
    out.horned_one = _flag(f, "horned_one")
    out.critical_threshold = <int>d["critical_threshold"]
    out.ignition = <int>d["ignition"]
    out.ward = <int>d["ward"]
    out.regeneration = <int>d["regeneration"]
    out.damage = <int>d["damage"]


cdef void fill_fighter(object d, FighterC* out, object sources, object reactions,
                       SourceC* bull, SourceC* body, SourceC* spines, SourceC* backlash,
                       SourceC* fire, SourceC* entangle, SourceC* hug, SourceC* acid,
                       SourceC* counter) except *:
    out.ws = _int(d, "ws")
    out.s = _int(d, "s")
    out.t = _int(d, "t")
    out.w = _int(d, "w")
    out.ini = _int(d, "ini")
    out.a = _int(d, "a")
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
    out.out_of_action_threshold = _int(d, "out_of_action_threshold")
    out.poison_immune = _flag(d, "poison_immune")
    out.incoming_strength_modifier = _int(d, "incoming_strength_modifier")
    out.incoming_attacks_modifier = _int(d, "incoming_attacks_modifier")
    out.thick_skull = _flag(d, "thick_skull")
    out.injury_reroll_out = _flag(d, "injury_reroll_out")
    out.hard_to_kill = _flag(d, "hard_to_kill")
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
    fill_source(reactions["bull"], bull)
    fill_source(reactions["body"], body)
    fill_source(reactions["spines"], spines)
    fill_source(reactions["backlash"], backlash)
    fill_source(reactions["fire"], fire)
    fill_source(reactions["entangle"], entangle)
    fill_source(reactions["hug"], hug)
    fill_source(reactions["acid"], acid)
    fill_source(reactions["counter"], counter)
    cdef object rc_list = d.get("random_characteristics") or ()
    out.random_characteristics_count = min(len(rc_list), MAX_RANDOM_CHARACTERISTICS)
    cdef dict stat_index = {"WS": 0, "S": 1, "T": 2, "I": 3, "A": 4}
    for i in range(out.random_characteristics_count):
        row = rc_list[i]
        out.random_characteristics[i][0] = stat_index[row[0]]
        out.random_characteristics[i][1] = <int>row[1]
        out.random_characteristics[i][2] = <int>row[2]
        out.random_characteristics[i][3] = <int>row[3]


# ---------------------------------------------------------------------------
# State lifecycle
# ---------------------------------------------------------------------------

cdef void state_alloc(StateC* s, int n) noexcept:
    s.n = n
    s.wounds = <int16_t*>malloc(n * sizeof(int16_t))
    s.condition = <int8_t*>malloc(n * sizeof(int8_t))
    s.initiative_penalty = <int8_t*>malloc(n * sizeof(int8_t))
    s.initiative_floor = <int8_t*>malloc(n * sizeof(int8_t))
    s.frenzy = <int8_t*>malloc(n * sizeof(int8_t))
    s.lucky_charm = <int8_t*>malloc(n * sizeof(int8_t))
    s.crimson_initiative = <int8_t*>malloc(n * sizeof(int8_t))
    s.attack_penalty = <int8_t*>malloc(n * sizeof(int8_t))
    s.entangled = <int8_t*>malloc(n * sizeof(int8_t))
    s.parry_used = <int8_t*>malloc(n * sizeof(int8_t))
    s.parry_remaining = <int8_t*>malloc(n * sizeof(int8_t))
    s.critical_used = <int8_t*>malloc(n * sizeof(int8_t))
    s.force_of_will_used = <int8_t*>malloc(n * sizeof(int8_t))
    s.force_of_will_active = <int8_t*>malloc(n * sizeof(int8_t))
    s.force_of_will_penalty = <int8_t*>malloc(n * sizeof(int8_t))
    s.disability = <int8_t*>malloc(n * sizeof(int8_t))
    s.mark_of_old_ones_used = <int8_t*>malloc(n * sizeof(int8_t))
    s.luck_used = <int8_t*>malloc(n * sizeof(int8_t))
    s.on_fire = <int8_t*>malloc(n * sizeof(int8_t))
    s.weapon_skill = <int16_t*>malloc(n * sizeof(int16_t))
    s.strength = <int16_t*>malloc(n * sizeof(int16_t))
    s.toughness = <int16_t*>malloc(n * sizeof(int16_t))
    s.initiative = <int16_t*>malloc(n * sizeof(int16_t))
    s.attacks = <int16_t*>malloc(n * sizeof(int16_t))


cdef void state_free(StateC* s) noexcept:
    free(s.wounds); free(s.condition); free(s.initiative_penalty)
    free(s.initiative_floor); free(s.frenzy); free(s.lucky_charm)
    free(s.crimson_initiative); free(s.attack_penalty); free(s.entangled)
    free(s.parry_used); free(s.parry_remaining); free(s.critical_used)
    free(s.force_of_will_used); free(s.force_of_will_active)
    free(s.force_of_will_penalty); free(s.disability)
    free(s.mark_of_old_ones_used); free(s.luck_used); free(s.on_fire)
    free(s.weapon_skill); free(s.strength); free(s.toughness)
    free(s.initiative); free(s.attacks)
    memset(s, 0, sizeof(StateC))


# ---------------------------------------------------------------------------
# Pure scalar operators (canonical ports of the vectorized arithmetic forms)
# ---------------------------------------------------------------------------

cdef inline int hit_target_c(int aws, int dws) noexcept:
    if dws == 0:
        return 2
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


cdef int injury_condition_c(
    int total, int out_threshold, int injury_profile, bint hard_to_kill,
    bint concussion, bint concussion_immune, bint fragile, bint poisonous,
    bint survivor, bint head_crusher, bint ignore_pain, bint jump_up,
    bint mandrake,
) noexcept:
    cdef int result
    if total >= out_threshold:
        result = OUT
    elif total >= 3:
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
    if concussion and not concussion_immune and 2 <= total <= 4:
        result = STUNNED
    if injury_profile == 1:
        if total >= 4:
            result = OUT
        elif total >= 2:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    elif injury_profile == 3:
        if total >= 4:
            result = OUT
        else:
            result = KNOCKED_DOWN
    if fragile and total == 2:
        result = STUNNED
    if poisonous:
        if total >= 5:
            result = OUT
        elif total >= 2:
            result = STUNNED
        else:
            result = KNOCKED_DOWN
    if survivor and result == OUT:
        result = STUNNED
    if head_crusher and result == KNOCKED_DOWN:
        result = STUNNED
    cdef bint knocked_down_by_no_pain = ignore_pain and result == STUNNED
    if knocked_down_by_no_pain:
        result = KNOCKED_DOWN
    if jump_up and result == KNOCKED_DOWN and not knocked_down_by_no_pain:
        result = STANDING
    if mandrake and result == STUNNED:
        result = KNOCKED_DOWN
    return result


cdef int armour_target_c(FighterC* d, int strength, SourceC* src,
                         bint magical_attack, bint ignored) noexcept:
    cdef int modifier = 0
    cdef int delta = strength - 3
    if delta > 0:
        modifier = delta
    modifier += src.effect.v[<int>F_ARMOUR_PENETRATION]
    modifier -= src.effect.v[<int>F_TARGET_ARMOUR_BONUS]
    cdef int armour = d.armour_save + modifier
    cdef int natural = d.natural_armour_save
    if not d.natural_armour_unmodified:
        natural += modifier
    if natural > d.natural_armour_worst_save:
        natural = d.natural_armour_worst_save
    if d.natural_armour_negated_by_magic and magical_attack:
        natural = 7
    cdef int target = armour if armour < natural else natural
    if ignored:
        if d.armour_cannot_be_ignored and not magical_attack:
            target = d.armour_save_floor
        else:
            target = 7
    if d.armour_save_floor <= 6 and target > d.armour_save_floor:
        target = d.armour_save_floor
    return target


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
                          PreparedC* out) except -1:
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
    cdef int i, row, count = 0, strength, aws, target, roll, hit_n = 0
    cdef int defender_cond, modifier, armour_strength
    cdef bint charging_row, helpless, sweep, any_failed, use_luck
    # Kill STUNNED defenders in the active set and drop OUT rows.
    for i in range(active_n):
        row = active_in[i]
        if def_state.condition[row] == STUNNED:
            def_state.condition[row] = OUT
    for i in range(active_n):
        row = active_in[i]
        if def_state.condition[row] != OUT:
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
        if first_round and eff.v[<int>F_CHARGE_STRENGTH_BONUS] and charging_row:
            if not src.mounted_only or atk.mounted:
                strength += eff.v[<int>F_CHARGE_STRENGTH_BONUS]
        armour_strength = strength
        if eff.v[<int>F_ARMOUR_STRENGTH_MODIFIER]:
            armour_strength += eff.v[<int>F_ARMOUR_STRENGTH_MODIFIER]
        if defender.incoming_strength_modifier:
            strength += defender.incoming_strength_modifier
            if strength < 1:
                strength = 1
        out.strength[i] = <int16_t>strength
        out.armour_strength[i] = <int16_t>armour_strength
        aws = atk_state.weapon_skill[row]
        if weapon.v[<int>F_WEAPON_SKILL_BONUS]:
            aws += weapon.v[<int>F_WEAPON_SKILL_BONUS]
        if src.knife_fighting:
            aws += 1
        if first_round and eff.v[<int>F_CHARGE_WS_BONUS] and charging_row:
            aws += eff.v[<int>F_CHARGE_WS_BONUS]
        target = hit_target_c(aws, def_state.weapon_skill[row])
        modifier = src.hit_mod_base
        if first_round and src.bellowing:
            modifier -= 1
        target = _clip_int(target - modifier, 2, 6)
        if src.berserker and charging_row:
            target = _clip_int(target - 1, 2, 6)
        if first_round and atk.ferocious_charge and charging_row:
            target = _clip_int(target + 1, 2, 6)
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
            targets[i] = def_state.initiative[out.active[i]]
        char_results = <int8_t*>malloc(count * sizeof(int8_t))
        if char_results == NULL:
            return -1
        characteristic_tests_c(defender, out.active, count, targets, rng, 0,
                               char_results)
    for i in range(count):
        row = out.active[i]
        charging_row = charging is not NULL and charging[row] != 0
        if sweep:
            successful[i] = 1 if not char_results[i] else 0
            out.rolls[i] = 6 if not char_results[i] else 1
        else:
            if eff.v[<int>F_AUTOMATIC_HIT]:
                roll = 6
            else:
                roll = rng_draw_safe(rng, 1, 6)
            out.rolls[i] = <int8_t>roll
            successful[i] = 1 if roll >= out.hit_target[i] else 0
        defender_cond = def_state.condition[row]
        helpless = defender_cond == KNOCKED_DOWN or defender_cond == PARALYZED
        if helpless:
            successful[i] = 1
            out.rolls[i] = 1
        if not successful[i]:
            want_reroll[i] = src.reroll_base
            if charging_row and src.reroll_charge:
                want_reroll[i] = 1
            if charging_row and first_round and src.reroll_charge_fr:
                want_reroll[i] = 1
            if (first_round and src.reroll_fr_all) or src.reroll_all:
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
            roll = rng_draw_safe(rng, 1, 6)
            out.rolls[i] = <int8_t>roll
            if roll >= out.hit_target[i]:
                successful[i] = 1
            if luck_used_here[i]:
                atk_state.luck_used[out.active[i]] = 1
    free(want_reroll)
    free(luck_used_here)
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
                          object defender_py, object observation) except -1:
    cdef FighterC* atk = &d.first if atk_side == 0 else &d.second
    cdef FighterC* defender = &d.first if atk_side == 1 else &d.second
    cdef EffectC* eff = &src.effect
    cdef int i, j, k, row, n, m, total, damage
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
    cdef int16_t* wounds_before = NULL
    cdef int* dmg_counts = NULL
    cdef int* reactive_rows = NULL
    cdef int* spittle_targets = NULL
    cdef int8_t* spittle_results = NULL
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
    cdef SourceC* acid_src = &d.acid_first if atk_side == 1 else &d.acid_second
    cdef PreparedC acid_prep
    cdef int n_react = 0, prepared_ok = 0
    cdef int inj_count = 0
    cdef int pos = 0
    cdef int wb = 0, c2 = 0, run_index = 0
    cdef int crit_bonus = 2 + (1 if src.web_of_steel else 0) + eff.v[<int>F_CRITICAL_INJURY_BONUS]
    cdef int n_contagious = 0
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
                                    parry_given) < 0:
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
            for i in range(n):
                if hit_values[i] >= 5:
                    s_def.attack_penalty[hit_rows[i]] = <int8_t>(s_def.attack_penalty[hit_rows[i]] + 1)
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
        # Automatic wounds (effect tag, or natural six with black lotus/wight).
        if src.automatic_wound_tag:
            for i in range(n):
                automatic_wound[i] = 1
        elif src.auto_wound_six:
            for i in range(n):
                automatic_wound[i] = 1 if hit_values[i] == 6 else 0
        else:
            for i in range(n):
                automatic_wound[i] = 0
        # To-wound targets.
        for i in range(n):
            raw = wound_target_c(strength_hits[i], s_def.toughness[hit_rows[i]],
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
            wound_rolls[i] = <int8_t>rng_draw_safe(rng, 1, 6)
            critical_rolls[i] = wound_rolls[i]
            wounded[i] = 1 if automatic_wound[i] or wound_rolls[i] >= targets[i] else 0
        # Rapier: an extra hit and an extra wound roll for every failed row, in
        # two full-array passes (NumPy draw order).
        if src.rapier:
            extra_hits = <int8_t*>malloc(n * sizeof(int8_t))
            extra_wounds = <int8_t*>malloc(n * sizeof(int8_t))
            if extra_hits == NULL or extra_wounds == NULL:
                rc = -1
                return rc
            for i in range(n):
                extra_hits[i] = 0
                if not wounded[i]:
                    extra_hits[i] = <int8_t>rng_draw_safe(rng, 1, 6)
            for i in range(n):
                extra_wounds[i] = 0
                if not wounded[i]:
                    extra_wounds[i] = <int8_t>rng_draw_safe(rng, 1, 6)
            for i in range(n):
                if not wounded[i]:
                    t = prepared.hit_target[hit_positions[i]] + 1
                    if t > 6:
                        t = 6
                    if extra_hits[i] >= t and extra_wounds[i] >= targets[i]:
                        wounded[i] = 1
            free(extra_hits)
            free(extra_wounds)
            extra_hits = NULL
            extra_wounds = NULL
        # Manbane: a natural 1 on the wound roll always fails.
        if src.manbane:
            for i in range(n):
                if wounded[i] and wound_rolls[i] == 1:
                    wounded[i] = 0
        # Rerolled wound rolls (single full-array draw over the failed rows).
        if eff.v[<int>F_REROLL_WOUNDS]:
            rerolls = <int8_t*>malloc(n * sizeof(int8_t))
            if rerolls == NULL:
                rc = -1
                return rc
            for i in range(n):
                rerolls[i] = 0
                if not wounded[i]:
                    rerolls[i] = <int8_t>rng_draw_safe(rng, 1, 6)
            for i in range(n):
                if not wounded[i] and rerolls[i] >= targets[i]:
                    wounded[i] = 1
                    wound_rolls[i] = rerolls[i]
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
            critical[i] = 1 if (not auto_w[i] and crit_roll[i] >= src.critical_threshold
                                and tgt[i] < 6) else 0
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
                    if rng_draw_safe(rng, 1, 6) >= 5 and critical[i]:
                        critical[i] = 0
        # Armour save (phased draw over the rows with a save target).
        save_target = <int8_t*>malloc(m * sizeof(int8_t))
        saved = <int8_t*>malloc(m * sizeof(int8_t))
        if save_target == NULL or saved == NULL:
            rc = -1
            return rc
        for i in range(m):
            save_target[i] = <int8_t>armour_target_c(defender, wound_strength[i], src,
                                                     src.magical, 0)
            saved[i] = 0
        for i in range(m):
            if save_target[i] <= 6:
                t = save_target[i]
                if t < 2:
                    t = 2
                if rng_draw_safe(rng, 1, 6) >= t:
                    saved[i] = 1
        k = 0
        for i in range(m):
            if not saved[i]:
                wound_rows[k] = wound_rows[i]
                critical[k] = critical[i]
                k += 1
        m = k
        if m == 0:
            return rc
        # Ward save.
        if src.ward <= 6:
            k = 0
            for i in range(m):
                if rng_draw_safe(rng, 1, 6) >= src.ward:
                    continue
                wound_rows[k] = wound_rows[i]
                critical[k] = critical[i]
                k += 1
            m = k
            if m == 0:
                return rc
        # Regeneration save.
        if src.regeneration <= 6:
            k = 0
            for i in range(m):
                if rng_draw_safe(rng, 1, 6) >= src.regeneration:
                    continue
                wound_rows[k] = wound_rows[i]
                critical[k] = critical[i]
                k += 1
            m = k
            if m == 0:
                return rc
        # Injury profile 2: any unsaved wound takes the warrior out.
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
            helpless[i] = 1 if t == KNOCKED_DOWN or t == PARALYZED else 0
            if helpless[i]:
                s_def.condition[row] = OUT
        # Damage application.
        damage = src.damage
        if src.flammable_double:
            damage *= 2
        total = m * damage
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
            for j in range(damage):
                damage_rows[k] = wound_rows[i]
                damage_critical[k] = critical[i]
                damage_helpless[k] = helpless[i]
                k += 1
        # Pre-subtraction wounds per distinct row (affected rows = run starts).
        k = 0
        for i in range(m):
            if i == 0 or wound_rows[i] != wound_rows[i - 1]:
                wounds_before[k] = s_def.wounds[wound_rows[i]]
                k += 1
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
        # Nightshade poison: initiative penalty per wound.
        if src.nightshade:
            for i in range(m):
                s_def.initiative_penalty[wound_rows[i]] = <int8_t>(s_def.initiative_penalty[wound_rows[i]] + 1)
        # Spider-spittle poison: Toughness test or paralysis.
        if src.spider_spittle:
            spittle_targets = <int*>malloc(m * sizeof(int))
            spittle_results = <int8_t*>malloc(m * sizeof(int8_t))
            if spittle_targets == NULL or spittle_results == NULL:
                rc = -1
                return rc
            for i in range(m):
                spittle_targets[i] = s_def.toughness[wound_rows[i]]
            characteristic_tests_c(defender, wound_rows, m, spittle_targets, rng, 0,
                                   spittle_results)
            for i in range(m):
                if not spittle_results[i] and s_def.condition[wound_rows[i]] == STANDING:
                    s_def.condition[wound_rows[i]] = PARALYZED
        # Injury rolls: one per damage instance that reaches zero wounds.
        injury_rows = <int*>malloc(total * sizeof(int))
        injury_crit = <int8_t*>malloc(total * sizeof(int8_t))
        if injury_rows == NULL or injury_crit == NULL:
            rc = -1
            return rc
        i = 0
        while i < m:
            row = wound_rows[i]
            wb = wounds_before[run_index]
            run_index += 1
            c2 = 1
            while i + c2 < m and wound_rows[i + c2] == row:
                c2 += 1
            for j in range(c2 * damage):
                if not damage_helpless[pos] and (wb <= 0 or j + 1 >= wb):
                    injury_rows[inj_count] = row
                    injury_crit[inj_count] = damage_critical[pos]
                    inj_count += 1
                pos += 1
            i += c2
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
            t = rng_draw_safe(rng, 1, 6) + eff.v[<int>F_INJURY_MODIFIER]
            if src.knife_fighting:
                t += 1
            if injury_crit[i]:
                t += crit_bonus
            injury_rolls[i] = <int8_t>t
        # Injury reroll on high rolls (Hard to Kill / Tough as Steel).
        if defender.injury_reroll_out and not src.fire:
            t = 6 if defender.hard_to_kill else defender.out_of_action_threshold
            for i in range(inj_count):
                if injury_rolls[i] >= t:
                    injury_rolls[i] = <int8_t>rng_draw_safe(rng, 1, 6)
        # Injury conditions.
        injury = <int8_t*>malloc(inj_count * sizeof(int8_t))
        if injury == NULL:
            rc = -1
            return rc
        for i in range(inj_count):
            injury[i] = <int8_t>injury_condition_c(
                injury_rolls[i], defender.out_of_action_threshold, defender.injury_profile,
                defender.hard_to_kill, eff.v[<int>F_CONCUSSION] != 0, defender.concussion_immune,
                defender.fragile, src.poisonous_injury, defender.survivor, src.head_crusher,
                defender.ignore_pain, defender.jump_up, defender.mandrake,
            )
        # Thick Skull / helmet stun recovery (full-array draws over injury rows).
        if defender.thick_skull:
            t = 2 if defender.helmet_save <= 4 else 3
            for i in range(inj_count):
                if injury[i] == STUNNED and rng_draw_safe(rng, 1, 6) >= t:
                    injury[i] = KNOCKED_DOWN
        elif defender.helmet_save <= 6:
            for i in range(inj_count):
                if injury[i] == STUNNED and rng_draw_safe(rng, 1, 6) >= defender.helmet_save:
                    injury[i] = KNOCKED_DOWN
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
            if highest == OUT and defender.contagious and not atk.undead_or_possessed:
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
        free(wounds_before)
        free(dmg_counts)
        free(reactive_rows)
        free(spittle_targets)
        free(spittle_results)
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
            continue
        row = rows[i]
        if atk_state.critical_used[row]:
            continue
        accepted[i] = 1
        atk_state.critical_used[row] = 1


cdef int parry_resolve_c(FighterC* defender, SourceC* src, int* hit_rows, int hit_n,
                         int* hit_values, int* hit_strength, StateC* def_state,
                         Rng* rng, const int* selected_rows, int selected_n,
                         bint selected_given, int* out_hit_rows,
                         int* out_parried) except -1:
    """Full port of vectorized._parry_hits.

    Returns the number of surviving hits (written first into out_hit_rows);
    parried rows follow in out_parried.  Consumes parry bookkeeping exactly
    like the NumPy engine, including the full-array second draw when a parry
    reroll is available.
    """
    cdef int i, j, k, row, surviving = 0, parried = 0, end, limit, pick
    cdef int best_pos, best_value, count, need_reroll, value, second
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
        # An empty selection means no hit of this attack may be parried,
        # mirroring NumPy's ``np.isin`` with an empty row array.
        for i in range(hit_n):
            row = hit_rows[i]
            while sel_pos < selected_n and selected_rows[sel_pos] < row:
                sel_pos += 1
            if (def_state.condition[row] == STANDING
                    and def_state.parry_remaining[row] > 0
                    and hit_strength[i] < 2 * def_state.strength[row]
                    and (hit_values[i] != 6 or defender.parry_can_parry_six)
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
        parry_rolls[i] = rng_draw_safe(rng, 1, 6)
    for i in range(hit_n):
        value = hit_values[i]
        if value == 6 and not defender.parry_can_parry_six:
            success1[i] = 0
        elif defender.parry_starblade:
            success1[i] = 1 if parry_rolls[i] >= 4 else 0
        elif defender.parry_match_allowed:
            success1[i] = 1 if parry_rolls[i] >= value else 0
        else:
            success1[i] = 1 if parry_rolls[i] > value else 0
    need_reroll = 0
    for i in range(hit_n):
        blocked[i] = 1 if eligible[i] and success1[i] else 0
        if not blocked[i]:
            need_reroll = 1
    if defender.parry_parry_reroll and need_reroll:
        # Second full-array draw whenever any hit row is not blocked.
        for i in range(hit_n):
            second = rng_draw_safe(rng, 1, 6)
            value = hit_values[i]
            if value == 6 and not defender.parry_can_parry_six:
                continue
            if defender.parry_starblade:
                if second >= 4 and eligible[i]:
                    blocked[i] = 1
            elif defender.parry_match_allowed:
                if second >= value and eligible[i]:
                    blocked[i] = 1
            else:
                if second > value and eligible[i]:
                    blocked[i] = 1
    # Bookkeeping: every eligible attempt marks the row, but the remaining
    # count is decremented once per distinct row.  NumPy's buffered fancy
    # ``parry_remaining[rows] -= 1`` applies once per unique index even when
    # a row has two eligible hits (parry capacity 2), so mirror that here.
    for i in range(hit_n):
        row = hit_rows[i]
        if eligible[i]:
            def_state.parry_used[row] = 1
            if i == 0 or row != hit_rows[i - 1]:
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
                              bint parry_given) except -1:
    """Hit-to-parry boundary port of vectorized._apply_hit_defences.

    Filters OUT rows, resolves parries (plus the optional cutlass counter and
    lucky charm saves), and rewrites ``prepared`` hit rows/positions in place.
    Returns the surviving hit count.
    """
    cdef FighterC* atk = &d.first if atk_side == 0 else &d.second
    cdef FighterC* defender = &d.first if atk_side == 1 else &d.second
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
    )
    if survivor_n < 0:
        return -1
    # Spider-infested defenders slow attackers whose hits were parried.
    if n - survivor_n and defender.spider_infested:
        for i in range(n - survivor_n):
            row = parried[i]
            s_atk.initiative_penalty[row] = <int8_t>(s_atk.initiative_penalty[row] + 1)
            s_atk.initiative_floor[row] = 0
    # Cutlass counter-attack: the defender strikes back after each parry.
    if n - survivor_n and src.counter_cutlass:
        counter_src = &d.counter_first if atk_side == 1 else &d.counter_second
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
                           object attacker_py, str decision_prefix) except -1:
    cdef FighterC* atk = &d.first if atk_side == 0 else &d.second
    cdef FighterC* defender = &d.first if atk_side == 1 else &d.second
    cdef int n = s_def.n
    cdef int i, j, k, row, m, rc = 0
    cdef int index, e, ok, maximum, any_c
    cdef int8_t* phase_cond = NULL
    cdef int* work_rows = NULL
    cdef int* remaining = NULL
    cdef int* main_rows = NULL
    cdef int* off_rows = NULL
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
    cdef bint two_parries, offhand, use_off, any_charging
    cdef int n_bull = 0, n_body = 0, n_main = 0, n_off = 0, surv_n
    cdef int prepared_count = 0, max_prepared = 0, n_hug = 0, n_won = 0
    cdef int remaining_n = rows_n
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
        if (phase_cond == NULL or work_rows == NULL or remaining == NULL
                or main_rows == NULL or off_rows == NULL):
            rc = -1
            return rc
        memcpy(phase_cond, s_def.condition, n)
        for i in range(rows_n):
            remaining[i] = rows[i]
        # Bull-charge reaction (first round only).
        if first_round:
            for i in range(remaining_n):
                row = remaining[i]
                if charging[row] and atk.bull_charge:
                    work_rows[n_bull] = row
                    n_bull += 1
            if n_bull and decisions is not None and not decisions.choose(
                    decision_prefix + ("bull-charge" if not decision_prefix
                                       else ".bull-charge"), attacker_py):
                n_bull = 0
            if n_bull:
                src = &d.bull_first if atk_side == 0 else &d.bull_second
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
            if n_body and decisions is not None and not decisions.choose(
                    decision_prefix + ("body-slam" if not decision_prefix
                                       else ".body-slam"), attacker_py):
                n_body = 0
            if n_body:
                src = &d.body_first if atk_side == 0 else &d.body_second
                ok = prepare_attack_c(atk, defender, src, work_rows, n_body, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep)
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
        # Weapon allocation over the attack pool.
        for index in range(maximum):
            m = 0
            for i in range(remaining_n):
                row = remaining[i]
                if attacks[row] > index and s_def.condition[row] != OUT:
                    work_rows[m] = row
                    m += 1
            if m == 0:
                continue
            offhand = atk.off_hand_attacks and atk.off_present != 0
            n_main = 0
            n_off = 0
            for i in range(m):
                row = work_rows[i]
                if atk.main_pistol:
                    use_off = offhand and (not first_round or index > 0)
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
            ok = prepare_attack_c(atk, defender, src, main_rows, n_main, charging, s_atk,
                                  s_def, rng, first_round, &tmp_prep)
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
            if offhand:
                ok = prepare_attack_c(atk, defender, &atk.off, off_rows, n_off, charging,
                                      s_atk, s_def, rng, first_round, &tmp_prep)
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
                                  s_atk, s_def, rng, first_round, &tmp_prep)
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
                # Mirror the modular oracle's offer-from-the-highest-downwards:
                # a hit that can never be parried (a natural 6 without
                # can_parry_six, a cannot_be_parried effect, or strength >= 2x
                # the defender's strength) never owns a parry slot, so the slot
                # lands on the best parryable hit.
                if (any_c == 6 and not defender.parry_can_parry_six) \
                        or tmp_prep.src.effect.v[<int>F_CANNOT_BE_PARRIED] \
                        or tmp_prep.strength[j] >= 2 * s_def.strength[row]:
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
                                              selected_counts[index], 1)
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
                remove_flags[index] = <int8_t*>malloc(tmp_prep.hit_n) if tmp_prep.hit_n else NULL
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
                if decisions is not None and not decisions.choose(
                        decision_prefix + ("bear-hug" if not decision_prefix
                                           else ".bear-hug"), {"row": row}):
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
                tmp_prep.hit_n = k
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
                    src = &d.hug_first if atk_side == 0 else &d.hug_second
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
            # Mirror the modular oracle's per-attack rule: a defender that is
            # STUNNED when this attack begins (stunned by an earlier attack of
            # the same pool) is taken out instantly - no further hit, wound or
            # injury rolls.  Preparation rolls every attack of the pool
            # upfront, so the STUNNED check cannot live at prepare time; it
            # runs here between resolutions.  Only a *landed* follow-up hit
            # triggers it: the oracle skips the attack entirely when the
            # pre-rolled hit missed, leaving the stunned defender in place
            # until round recovery.
            if index:
                for i in range(tmp_prep.hit_n):
                    row = tmp_prep.hit_rows[i]
                    if s_def.condition[row] == STUNNED:
                        s_def.condition[row] = OUT
            if resolve_weapon_c(d, atk_side, &tmp_prep.src, prepared[index], charging,
                                s_atk, s_def, rng, first_round, phase_cond,
                                defences_resolved, selected[index],
                                selected_counts[index], 1, decisions, 1,
                                attacker_py, None, None) < 0:
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
                               int charged_row, int stood_row) noexcept:
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
        if value < charging_row:
            value = charging_row
        if f.strike_skinks_first:
            value = 20
        if f.lightning_reflexes and charged_row and value < 1:
            value = 1
        # Spear: strikes first in the first turn of close combat, even if
        # charged, outranking the charger's own strike-first tier.  An
        # opponent with Always Strikes First keeps its unconditional priority
        # and the pair resolves by Initiative instead.
        if f.spear and charged_row and not f.opponent_always_first and value < 2:
            value = 2
    if not f.always_strikes_first and stood_row:
        value = -1
    return value


cdef inline int effective_initiative_c(FighterC* f, StateC* s, int row) noexcept:
    """Port of vectorized.effective_initiative (per row)."""
    cdef int value = (s.initiative[row] + f.initiative_bonus_total
                      + s.crimson_initiative[row] - s.initiative_penalty[row])
    if value < s.initiative_floor[row]:
        value = s.initiative_floor[row]
    return value


cdef int attack_count_c(FighterC* f, StateC* s, const int8_t* charging,
                        bint first_round, int16_t* out, int count) except -1:
    """Port of vectorized.attack_count (state.attacks as base_attacks)."""
    cdef int extra = f.extra_weapon_attack
    if f.fist_penalized:
        extra = 0
    cdef int i, result
    for i in range(count):
        result = s.attacks[i] + f.attacks_bonus_total
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
        if f.inspiring:
            result += 1
        if first_round:
            result += f.first_round_attacks_bonus
        # Doubling is gated on the per-row frenzy state only.  The NumPy
        # operator doubles unconditionally when no state array is supplied
        # (its ``elif effect.frenzy`` default), but the driver always passes
        # the state; that default must not resurface here or a frenzied
        # fighter would regain doubled attacks after a knockdown cleared
        # ``s.frenzy``.
        if s.frenzy[i]:
            result *= 2
        if first_round and f.ferocious_charge and charging[i]:
            result *= 2
        result += extra
        if f.vomit or f.sweep_main:
            result = 1
        if f.main_pistol:
            if first_round:
                if not f.off_hand_attacks:
                    result = 1
            elif f.off_hand_attacks:
                result -= 1
                if result < 0:
                    result = 0
            else:
                result = 0
        elif f.off_pistol and not first_round:
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
        result -= s.attack_penalty[i]
        if result < 0:
            result = 0
        out[i] = <int16_t>result
    return 0


cdef int init_state_c(FighterC* f, StateC* s, int count, Rng* rng) except -1:
    """Port of vectorized._new_state (per fighter)."""
    cdef int i, d, dice, sides, bonus, total, key
    for i in range(count):
        s.wounds[i] = <int16_t>f.base_wounds
        s.condition[i] = 0
        s.initiative_penalty[i] = 0
        s.initiative_floor[i] = 1
        s.frenzy[i] = 1 if f.frenzy_init else 0
        s.lucky_charm[i] = 1 if f.lucky_charm_init else 0
        s.attack_penalty[i] = 0
        s.entangled[i] = 0
        s.parry_used[i] = 0
        s.parry_remaining[i] = <int8_t>f.parry_capacity
        s.critical_used[i] = 0
        s.force_of_will_used[i] = 0
        s.force_of_will_active[i] = 0
        s.force_of_will_penalty[i] = 0
        s.disability[i] = 0
        s.mark_of_old_ones_used[i] = 0
        s.luck_used[i] = 0
        s.on_fire[i] = 0
        s.weapon_skill[i] = <int16_t>f.ws
        s.strength[i] = <int16_t>f.s
        s.toughness[i] = <int16_t>(f.t + f.toughness_bonus)
        s.initiative[i] = <int16_t>f.ini
        s.attacks[i] = <int16_t>f.a
    if f.crimson_shade:
        for i in range(count):
            s.crimson_initiative[i] = <int8_t>rng_draw_safe(rng, 1, 3)
    else:
        for i in range(count):
            s.crimson_initiative[i] = 0
    # Random characteristics: (stat 0-4, dice, sides, bonus) per entry.
    for key in range(f.random_characteristics_count):
        dice = f.random_characteristics[key][1]
        sides = f.random_characteristics[key][2]
        bonus = f.random_characteristics[key][3]
        for i in range(count):
            total = 0
            for d in range(dice):
                total += rng_draw_safe(rng, 1, sides)
            total += bonus
            if f.random_characteristics[key][0] == 0:
                s.weapon_skill[i] = <int16_t>total
            elif f.random_characteristics[key][0] == 1:
                s.strength[i] = <int16_t>total
            elif f.random_characteristics[key][0] == 2:
                s.toughness[i] = <int16_t>total
            elif f.random_characteristics[key][0] == 3:
                s.initiative[i] = <int16_t>total
            else:
                s.attacks[i] = <int16_t>total
    if f.disability:
        for i in range(count):
            d = rng_draw_safe(rng, 1, 6)
            s.disability[i] = <int8_t>d
            if d == 1:
                s.initiative[i] = <int16_t>(s.initiative[i] - 1 if s.initiative[i] > 1 else 1)
            elif d == 2:
                s.weapon_skill[i] = <int16_t>(s.weapon_skill[i] - 1 if s.weapon_skill[i] > 1 else 1)
            elif d == 4:
                s.toughness[i] = <int16_t>(s.toughness[i] - 1 if s.toughness[i] > 1 else 1)
            elif d == 5:
                s.strength[i] = <int16_t>(s.strength[i] - 1 if s.strength[i] > 1 else 1)
    return 0


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
    if d.first.spines:
        ok = prepare_attack_c(&d.first, &d.second, &d.spines_first, rows, rows_n,
                              charge1, s1, s2, rng, 0, &prep1)
        if ok < 0:
            return -1
        have1 = ok > 0
    if d.second.spines:
        ok = prepare_attack_c(&d.second, &d.first, &d.spines_second, rows, rows_n,
                              charge2, s2, s1, rng, 0, &prep2)
        if ok < 0:
            if have1:
                prepared_free(&prep1)
            return -1
        have2 = ok > 0
    if have1:
        if resolve_weapon_c(d, 0, &d.spines_first, &prep1, charge1, s1, s2, rng,
                            0, NULL, 0, NULL, 0, 0, None, 1, None, None,
                            None) < 0:
            if have2:
                prepared_free(&prep2)
            prepared_free(&prep1)
            return -1
        prepared_free(&prep1)
    if have2:
        if resolve_weapon_c(d, 1, &d.spines_second, &prep2, charge2, s2, s1, rng,
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
        characteristic_tests_c(f, eligible, m, targets, rng, 0, results)
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
        for i in range(m):
            results[i] = 1 if rng_draw_safe(rng, 1, 6) > targets[i] else 0
        for i in range(m):
            if results[i]:
                row = active[i]
                s.condition[row] = OUT
                s.force_of_will_active[row] = 0
    free(active); free(targets); free(results)
    return 0


cdef int black_hunger_backlash_c(DuelC* d, int side, StateC* s, Rng* rng,
                                 const int* rows, int rows_n) except -1:
    """Port of vectorized._black_hunger_backlash."""
    cdef FighterC* f = &d.first if side == 0 else &d.second
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
        if s.condition[row] != OUT:
            active[m] = row
            m += 1
    cdef PreparedC prep
    cdef SourceC* backlash = &d.backlash_first if side == 0 else &d.backlash_second
    cdef int ok, k
    if m:
        for i in range(m):
            hits[i] = <int8_t>rng_draw_safe(rng, 1, 3)
        for index in range(3):
            k = 0
            for i in range(m):
                if hits[i] > index:
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
            if rescue_force_of_will_c(f, s, hit_rows, k, rng) < 0:
                free(active); free(hit_rows); free(hits)
                return -1
    free(active); free(hit_rows); free(hits)
    return 0


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
    cdef FighterC* atk = &d.first if atk_side == 0 else &d.second
    cdef FighterC* defender = &d.first if victim_side == 0 else &d.second
    cdef SourceC* fire_src = &d.fire_first if atk_side == 0 else &d.fire_second
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
    cdef FighterC* atk = &d.first if atk_side == 0 else &d.second
    cdef FighterC* defender = &d.first if atk_side == 1 else &d.second
    cdef SourceC* src = &d.entangle_first if atk_side == 0 else &d.entangle_second
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


cdef int simulate_batch_c(DuelC* d, int count, uint64_t seed, int maximum_rounds,
                          object decisions, object first_py, object second_py,
                          int* out_a, int* out_b, int* out_u) except -1:
    cdef Rng rng
    cdef StateC s1, s2
    cdef int8_t* first_charges = <int8_t*>malloc(count)
    cdef int8_t* charge1 = <int8_t*>malloc(count)
    cdef int8_t* charge2 = <int8_t*>malloc(count)
    cdef int8_t* stood1 = <int8_t*>malloc(count)
    cdef int8_t* stood2 = <int8_t*>malloc(count)
    cdef int16_t* attacks1 = <int16_t*>malloc(count * sizeof(int16_t))
    cdef int16_t* attacks2 = <int16_t*>malloc(count * sizeof(int16_t))
    cdef int8_t* p1 = <int8_t*>malloc(count)
    cdef int8_t* p2 = <int8_t*>malloc(count)
    cdef int16_t* ini1 = <int16_t*>malloc(count * sizeof(int16_t))
    cdef int16_t* ini2 = <int16_t*>malloc(count * sizeof(int16_t))
    cdef int8_t* first_acts = <int8_t*>malloc(count)
    cdef int8_t* ties = <int8_t*>malloc(count)
    cdef int8_t* unresolved = <int8_t*>malloc(count)
    cdef int* active_rows = <int*>malloc(count * sizeof(int))
    cdef int* rows = <int*>malloc(count * sizeof(int))
    cdef int* reply = <int*>malloc(count * sizeof(int))
    cdef int* paralyze_rows = <int*>malloc(count * sizeof(int))
    cdef int* paralyze_targets = <int*>malloc(count * sizeof(int))
    cdef int8_t* paralyze_results = <int8_t*>malloc(count)
    cdef int i, row, m, k, n_rows, n_reply, rc = 0
    cdef int any_left, round_index, n_active, n_paralyze, p
    cdef int wins_a = 0, wins_b = 0
    cdef bint first_round
    try:
        """Run ``count`` duels end to end (port of vectorized._simulate_batch_core)."""
        rng_init(&rng, seed, None)
        state_alloc(&s1, count)
        state_alloc(&s2, count)
        if s1.wounds == NULL or s2.wounds == NULL:
            state_free(&s1)
            state_free(&s2)
            return -1
        if init_state_c(&d.first, &s1, count, &rng) < 0 or \
                init_state_c(&d.second, &s2, count, &rng) < 0:
            state_free(&s1)
            state_free(&s2)
            return -1
        if (first_charges == NULL or charge1 == NULL or charge2 == NULL
                or stood1 == NULL or stood2 == NULL or attacks1 == NULL
                or attacks2 == NULL or p1 == NULL or p2 == NULL or ini1 == NULL
                or ini2 == NULL or first_acts == NULL or ties == NULL
                or unresolved == NULL or active_rows == NULL or rows == NULL
                or reply == NULL or paralyze_rows == NULL
                or paralyze_targets == NULL or paralyze_results == NULL):
            rc = -1
            return rc
        for i in range(count):
            first_charges[i] = <int8_t>pcg32_bounded(&rng.pcg, 2)
        for round_index in range(maximum_rounds):
            any_left = 0
            for i in range(count):
                unresolved[i] = 1 if (s1.condition[i] != OUT
                                      and s2.condition[i] != OUT) else 0
                if unresolved[i]:
                    any_left = 1
            if not any_left:
                break
            if round_index:
                n_active = 0
                for i in range(count):
                    if unresolved[i]:
                        active_rows[n_active] = i
                        n_active += 1
                if sustain_force_of_will_c(&d.first, &s1, &rng, active_rows,
                                           n_active) < 0:
                    rc = -1
                    return rc
                if sustain_force_of_will_c(&d.second, &s2, &rng, active_rows,
                                           n_active) < 0:
                    rc = -1
                    return rc
                if d.first.can_burn:
                    if resolve_fire_c(d, 0, &s1, &s2, &rng, active_rows,
                                      n_active) < 0:
                        rc = -1
                        return rc
                if d.second.can_burn:
                    if resolve_fire_c(d, 1, &s2, &s1, &rng, active_rows,
                                      n_active) < 0:
                        rc = -1
                        return rc
                if rescue_force_of_will_c(&d.first, &s1, active_rows, n_active,
                                          &rng) < 0:
                    rc = -1
                    return rc
                if rescue_force_of_will_c(&d.second, &s2, active_rows, n_active,
                                          &rng) < 0:
                    rc = -1
                    return rc
            any_left = 0
            for i in range(count):
                unresolved[i] = 1 if (s1.condition[i] != OUT
                                      and s2.condition[i] != OUT) else 0
                if unresolved[i]:
                    any_left = 1
            if not any_left:
                break
            n_active = 0
            for i in range(count):
                if unresolved[i]:
                    active_rows[n_active] = i
                    n_active += 1
            for i in range(count):
                s1.parry_used[i] = 0
                s2.parry_used[i] = 0
                s1.parry_remaining[i] = <int8_t>d.first.parry_capacity
                s2.parry_remaining[i] = <int8_t>d.second.parry_capacity
                s1.critical_used[i] = 0
                s2.critical_used[i] = 0
            if d.first.spawn:
                for i in range(count):
                    s1.attacks[i] = <int16_t>(rng_draw_safe(&rng, 1, 6) + 1)
            if d.second.spawn:
                for i in range(count):
                    s2.attacks[i] = <int16_t>(rng_draw_safe(&rng, 1, 6) + 1)
            # Recovery: STUNNED -> KNOCKED_DOWN, KNOCKED_DOWN -> STANDING.
            for i in range(count):
                stood1[i] = 1 if s1.condition[i] == KNOCKED_DOWN else 0
                stood2[i] = 1 if s2.condition[i] == KNOCKED_DOWN else 0
                if s1.condition[i] == STUNNED:
                    s1.condition[i] = KNOCKED_DOWN
                elif s1.condition[i] == KNOCKED_DOWN:
                    s1.condition[i] = STANDING
                if s2.condition[i] == STUNNED:
                    s2.condition[i] = KNOCKED_DOWN
                elif s2.condition[i] == KNOCKED_DOWN:
                    s2.condition[i] = STANDING
            # Paralyzed recovery (Toughness tests for both fighters).
            n_paralyze = 0
            for i in range(count):
                if s1.condition[i] == PARALYZED:
                    paralyze_rows[n_paralyze] = i
                    paralyze_targets[n_paralyze] = s1.toughness[i]
                    n_paralyze += 1
            if n_paralyze:
                characteristic_tests_c(&d.first, paralyze_rows, n_paralyze,
                                       paralyze_targets, &rng, 0, paralyze_results)
                for i in range(n_paralyze):
                    if paralyze_results[i]:
                        s1.condition[paralyze_rows[i]] = STANDING
            n_paralyze = 0
            for i in range(count):
                if s2.condition[i] == PARALYZED:
                    paralyze_rows[n_paralyze] = i
                    paralyze_targets[n_paralyze] = s2.toughness[i]
                    n_paralyze += 1
            if n_paralyze:
                characteristic_tests_c(&d.second, paralyze_rows, n_paralyze,
                                       paralyze_targets, &rng, 0, paralyze_results)
                for i in range(n_paralyze):
                    if paralyze_results[i]:
                        s2.condition[paralyze_rows[i]] = STANDING
            first_round = round_index == 0
            for i in range(count):
                charge1[i] = first_charges[i] if first_round else 0
                charge2[i] = (1 - first_charges[i]) if first_round else 0
            if first_round:
                if d.first.netter:
                    n_rows = 0
                    for i in range(count):
                        if unresolved[i] and charge1[i]:
                            rows[n_rows] = i
                            n_rows += 1
                    if netter_charge_c(&d.first, &d.second, rows, n_rows, &s2,
                                       &rng) < 0:
                        rc = -1
                        return rc
                if d.second.netter:
                    n_rows = 0
                    for i in range(count):
                        if unresolved[i] and charge2[i]:
                            rows[n_rows] = i
                            n_rows += 1
                    if netter_charge_c(&d.second, &d.first, rows, n_rows, &s1,
                                       &rng) < 0:
                        rc = -1
                        return rc
            if d.first.spines or d.second.spines:
                if resolve_spines_c(d, active_rows, n_active, charge1, charge2,
                                    &s1, &s2, &rng) < 0:
                    rc = -1
                    return rc
            if rescue_force_of_will_c(&d.first, &s1, active_rows, n_active,
                                      &rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.second, &s2, active_rows, n_active,
                                      &rng) < 0:
                rc = -1
                return rc
            if d.second.entangle:
                n_rows = 0
                for i in range(count):
                    if s1.entangled[i] and s2.condition[i] == STANDING and unresolved[i]:
                        rows[n_rows] = i
                        n_rows += 1
                if resolve_entangle_c(d, 1, rows, n_rows, charge2, &s2, &s1,
                                      &rng) < 0:
                    rc = -1
                    return rc
            if d.first.entangle:
                n_rows = 0
                for i in range(count):
                    if s2.entangled[i] and s1.condition[i] == STANDING and unresolved[i]:
                        rows[n_rows] = i
                        n_rows += 1
                if resolve_entangle_c(d, 0, rows, n_rows, charge1, &s1, &s2,
                                      &rng) < 0:
                    rc = -1
                    return rc
            # Attack counts (charged = the opponent's charging mask).
            if attack_count_c(&d.first, &s1, charge1, first_round, attacks1,
                              count) < 0:
                rc = -1
                return rc
            if attack_count_c(&d.second, &s2, charge2, first_round, attacks2,
                              count) < 0:
                rc = -1
                return rc
            for i in range(count):
                if attacks1[i] > 0:
                    attacks1[i] = <int16_t>(attacks1[i] + d.second.incoming_attacks_modifier)
                    if attacks1[i] < 1:
                        attacks1[i] = 1
                else:
                    attacks1[i] = 0
                if attacks2[i] > 0:
                    attacks2[i] = <int16_t>(attacks2[i] + d.first.incoming_attacks_modifier)
                    if attacks2[i] < 1:
                        attacks2[i] = 1
                else:
                    attacks2[i] = 0
                if s1.on_fire[i]:
                    attacks1[i] = 0
                if s2.on_fire[i]:
                    attacks2[i] = 0
            if d.first.animal_friendship_effective:
                for i in range(count):
                    attacks2[i] = 0
            if d.second.animal_friendship_effective:
                for i in range(count):
                    attacks1[i] = 0
            for i in range(count):
                s1.attack_penalty[i] = 0
                s2.attack_penalty[i] = 0
            if first_round:
                if d.first.serpent_whip:
                    for i in range(count):
                        if charge1[i] or charge2[i]:
                            attacks1[i] = <int16_t>(attacks1[i] + 1)
                if d.second.serpent_whip:
                    for i in range(count):
                        if charge2[i] or charge1[i]:
                            attacks2[i] = <int16_t>(attacks2[i] + 1)
                if d.first.boar_spear:
                    for i in range(count):
                        if charge2[i]:
                            attacks2[i] = <int16_t>(attacks2[i] - 1)
                            if attacks2[i] < 1:
                                attacks2[i] = 1
                if d.second.boar_spear:
                    for i in range(count):
                        if charge1[i]:
                            attacks1[i] = <int16_t>(attacks1[i] - 1)
                            if attacks1[i] < 1:
                                attacks1[i] = 1
                if d.first.sigmar_effective:
                    for i in range(count):
                        if attacks2[i] > 0:
                            attacks2[i] = <int16_t>(attacks2[i] - 1)
                            if attacks2[i] < 1:
                                attacks2[i] = 1
                if d.second.sigmar_effective:
                    for i in range(count):
                        if attacks1[i] > 0:
                            attacks1[i] = <int16_t>(attacks1[i] - 1)
                            if attacks1[i] < 1:
                                attacks1[i] = 1
            # Priority, initiative and the acting order.
            for i in range(count):
                p1[i] = <int8_t>priority_row_c(&d.first, first_round, charge1[i],
                                               charge2[i], stood1[i])
                p2[i] = <int8_t>priority_row_c(&d.second, first_round, charge2[i],
                                               charge1[i], stood2[i])
                ini1[i] = <int16_t>effective_initiative_c(&d.first, &s1, i)
                ini2[i] = <int16_t>effective_initiative_c(&d.second, &s2, i)
            for i in range(count):
                first_acts[i] = 1 if (p1[i] > p2[i]
                                      or (p1[i] == p2[i] and ini1[i] > ini2[i])) else 0
                ties[i] = 1 if p1[i] == p2[i] and ini1[i] == ini2[i] else 0
            for i in range(count):
                if ties[i]:
                    first_acts[i] = <int8_t>pcg32_bounded(&rng.pcg, 2)
            # First fighter attacks, then surviving targets reply.
            n_rows = 0
            for i in range(count):
                if unresolved[i] and s1.condition[i] == STANDING and first_acts[i]:
                    rows[n_rows] = i
                    n_rows += 1
            if resolve_attacks_c(d, 0, rows, n_rows, attacks1, charge1, &s1, &s2,
                                 &rng, first_round, decisions, first_py, "") < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.first, &s1, rows, n_rows, &rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.second, &s2, rows, n_rows, &rng) < 0:
                rc = -1
                return rc
            # Reply rows are scanned from the reply fighter's OWN standing
            # state, never derived from the primary's row set: when the primary
            # is down (knocked down / stunned at round start) the standing
            # opponent must still strike and auto-out the helpless target,
            # exactly like the scalar oracle's independent pools.
            n_reply = 0
            for i in range(count):
                if unresolved[i] and s2.condition[i] == STANDING and first_acts[i]:
                    reply[n_reply] = i
                    n_reply += 1
            if resolve_attacks_c(d, 1, reply, n_reply, attacks2, charge2, &s2, &s1,
                                 &rng, first_round, decisions, second_py, "") < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.first, &s1, reply, n_reply, &rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.second, &s2, reply, n_reply, &rng) < 0:
                rc = -1
                return rc
            # Second fighter attacks, then surviving targets reply.
            n_rows = 0
            for i in range(count):
                if unresolved[i] and s2.condition[i] == STANDING and not first_acts[i]:
                    rows[n_rows] = i
                    n_rows += 1
            if resolve_attacks_c(d, 1, rows, n_rows, attacks2, charge2, &s2, &s1,
                                 &rng, first_round, decisions, second_py, "") < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.first, &s1, rows, n_rows, &rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.second, &s2, rows, n_rows, &rng) < 0:
                rc = -1
                return rc
            n_reply = 0
            for i in range(count):
                if unresolved[i] and s1.condition[i] == STANDING and not first_acts[i]:
                    reply[n_reply] = i
                    n_reply += 1
            if resolve_attacks_c(d, 0, reply, n_reply, attacks1, charge1, &s1, &s2,
                                 &rng, first_round, decisions, first_py, "") < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.first, &s1, reply, n_reply, &rng) < 0:
                rc = -1
                return rc
            if rescue_force_of_will_c(&d.second, &s2, reply, n_reply, &rng) < 0:
                rc = -1
                return rc
            if d.first.black_hunger:
                if black_hunger_backlash_c(d, 0, &s1, &rng, active_rows,
                                           n_active) < 0:
                    rc = -1
                    return rc
            if d.second.black_hunger:
                if black_hunger_backlash_c(d, 1, &s2, &rng, active_rows,
                                           n_active) < 0:
                    rc = -1
                    return rc
        # Winner accounting (accumulates across batches: the driver passes the
        # same out_a/out_b/out_u slots for every batch of one simulation run).
        wins_a = 0
        wins_b = 0
        for i in range(count):
            if s2.condition[i] == OUT and s1.condition[i] != OUT:
                wins_a += 1
            elif s1.condition[i] == OUT and s2.condition[i] != OUT:
                wins_b += 1
        out_a[0] += wins_a
        out_b[0] += wins_b
        out_u[0] += count - wins_a - wins_b
    finally:
        free(first_charges); free(charge1); free(charge2)
        free(stood1); free(stood2)
        free(attacks1); free(attacks2)
        free(p1); free(p2); free(ini1); free(ini2)
        free(first_acts); free(ties); free(unresolved)
        free(active_rows); free(rows); free(reply)
        free(paralyze_rows); free(paralyze_targets); free(paralyze_results)
        state_free(&s1)
        state_free(&s2)
    return rc


cdef int _run_batch(object ctx, int count, uint64_t seed, int maximum_rounds,
                    object decisions, object first_py, object second_py,
                    int* a, int* b, int* u) except -1:
    cdef DuelC d
    # Conditional fields (has_unpredictable, off_present, source structs for
    # absent weapons/reactions) are only written when the fighter owns them, so
    # the stack struct must start zeroed or garbage leaks into the engine.
    memset(&d, 0, sizeof(DuelC))
    fill_fighter(ctx["first"], &d.first, ctx["sources_first"],
                 ctx["reactions_first"], &d.bull_first, &d.body_first,
                 &d.spines_first, &d.backlash_first, &d.fire_first,
                 &d.entangle_first, &d.hug_first, &d.acid_first,
                 &d.counter_first)
    fill_fighter(ctx["second"], &d.second, ctx["sources_second"],
                 ctx["reactions_second"], &d.bull_second, &d.body_second,
                 &d.spines_second, &d.backlash_second, &d.fire_second,
                 &d.entangle_second, &d.hug_second, &d.acid_second,
                 &d.counter_second)
    if simulate_batch_c(&d, count, seed, maximum_rounds, decisions, first_py,
                        second_py, a, b, u) < 0:
        return -1
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


def simulate_duel(request, plan):
    """Run a duel request through the compiled core (mirror of the NumPy
    driver; per-batch PCG32 streams derived from the request seed)."""
    from mordheim_combat._combat_compile import NotSupported
    from mordheim_combat._combat_compile import compile_duel
    from mordheim_core.models import DuelResult
    from mordheim_core.models import SimulationCancelled
    try:
        ctx = compile_duel(request.first, request.second)
    except NotSupported as error:
        raise RuntimeError(
            f"native combat backend does not support this duel plan: {error}"
        ) from error
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
        if _run_batch(ctx, count, seed, request.maximum_rounds,
                      request.decision_policy, request.first, request.second,
                      &a, &b, &u) < 0:
            raise RuntimeError("native combat backend failed")
        remaining -= count
        batch_index += 1
    return DuelResult(a, b, u, request.simulations)


# ---------------------------------------------------------------------------
