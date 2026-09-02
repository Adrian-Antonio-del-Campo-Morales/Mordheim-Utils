# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

"""Native kernel for duels without special rules."""

from libc.stdint cimport uint32_t, uint64_t


cdef int STANDING = 0
cdef int KNOCKED_DOWN = 1
cdef int STUNNED = 2
cdef int OUT = 4

cdef int SWORD = 0
cdef int MACE = 1
cdef int DAGGER = 2
cdef int TWO_HANDED = 3
cdef int AXE = 4
cdef int FLAIL = 5
cdef int MORNING_STAR = 6
cdef int HALBERD = 7
cdef int SPEAR = 8

cdef int OFF_NONE = -1
cdef int OFF_SHIELD = -2
cdef int OFF_BUCKLER = -3


cdef inline uint32_t pcg32(uint64_t* state) noexcept nogil:
    cdef uint64_t old = state[0]
    cdef uint32_t shift
    cdef uint32_t word
    state[0] = old * 6364136223846793005ULL + 1442695040888963407ULL
    shift = <uint32_t>(old >> 59)
    word = <uint32_t>(((old >> 18) ^ old) >> 27)
    return (word >> shift) | (word << ((32 - shift) & 31))


cdef inline int d6(uint64_t* state) noexcept nogil:
    cdef uint32_t value
    # 2^32 is not divisible by six. Re-roll these four values.
    while True:
        value = pcg32(state)
        if value >= 4:
            return <int>(value % 6) + 1


cdef inline int to_hit(int attacker, int defender) noexcept nogil:
    if defender == 0:
        return 2
    if attacker > defender:
        return 3
    if defender > 2 * attacker:
        return 5
    return 4


cdef inline int to_wound(int strength, int resistance) noexcept nogil:
    cdef int difference = strength - resistance
    if difference >= 2:
        return 2
    if difference == 1:
        return 3
    if difference == 0:
        return 4
    if difference == -1:
        return 5
    if difference >= -3:
        return 6
    return 7


cdef inline int weapon_strength(int strength, int weapon, bint first_round) noexcept nogil:
    if weapon == TWO_HANDED or weapon == FLAIL:
        return strength + (2 if weapon == TWO_HANDED or first_round else 0)
    if weapon == MORNING_STAR:
        return strength + (1 if first_round else 0)
    if weapon == HALBERD:
        return strength + 1
    return strength


cdef inline int priority(int weapon, bint first_round, bint charging, bint stood) noexcept nogil:
    if stood or weapon == TWO_HANDED:
        return 2
    if charging or (first_round and weapon == SPEAR):
        return 0
    return 1


cdef inline int injury(uint64_t* random_state, int weapon, int modifier) noexcept nogil:
    cdef int roll = d6(random_state) + modifier
    if roll > 6:
        roll = 6
    if weapon == MACE:
        if roll == 1:
            return KNOCKED_DOWN
        if roll <= 4:
            return STUNNED
        return OUT
    if roll <= 2:
        return KNOCKED_DOWN
    if roll <= 4:
        return STUNNED
    return OUT


cdef inline int attack_count(long long[:] fighter) noexcept nogil:
    return <int>fighter[5] + (1 if fighter[7] >= 0 else 0)


cdef inline int attack_weapon(long long[:] fighter, int attack) noexcept nogil:
    if attack < fighter[5]:
        return <int>fighter[6]
    return <int>fighter[7]


cdef int resolve_attacks(
    long long[:] attacker,
    long long[:] defender,
    int* wounds,
    int* state,
    bint first_round,
    uint64_t* random_state,
) noexcept nogil:
    cdef int rolls[32]
    cdef int active[32]
    cdef int weapons[32]
    cdef int count = attack_count(attacker)
    cdef int hit_target = to_hit(<int>attacker[0], <int>defender[0])
    cdef int attempts = 0
    cdef int best = -1
    cdef int best_roll = 0
    cdef int parry_roll
    cdef int index
    cdef int weapon
    cdef int strength
    cdef int wound_target
    cdef int wound_roll
    cdef int critical_roll
    cdef int damage
    cdef int save_target
    cdef int modifier
    cdef int result
    cdef bint critical_used = False
    cdef bint started_knocked = state[0] == KNOCKED_DOWN
    cdef bint has_sword = defender[6] == SWORD or defender[7] == SWORD
    cdef bint has_buckler = defender[7] == OFF_BUCKLER
    cdef bint reroll_parry = defender[6] == SWORD and has_buckler

    if state[0] == STUNNED:
        state[0] = OUT
        return 1

    for index in range(count):
        weapon = attack_weapon(attacker, index)
        weapons[index] = weapon
        rolls[index] = 6 if started_knocked else d6(random_state)
        active[index] = 1 if started_knocked or rolls[index] >= hit_target else 0
        if active[index] and (has_sword or has_buckler):
            strength = weapon_strength(<int>attacker[1], weapon, first_round)
            if strength < 2 * defender[1] and rolls[index] > best_roll:
                best = index
                best_roll = rolls[index]

    if best >= 0:
        parry_roll = d6(random_state)
        if reroll_parry and parry_roll <= best_roll:
            parry_roll = d6(random_state)
        if parry_roll > best_roll:
            active[best] = 0

    for index in range(count):
        if not active[index]:
            continue
        weapon = weapons[index]
        strength = weapon_strength(<int>attacker[1], weapon, first_round)
        wound_target = to_wound(strength, <int>defender[2])
        if wound_target > 6:
            continue
        wound_roll = d6(random_state)
        if wound_roll < wound_target:
            continue

        damage = 1
        modifier = 0
        save_target = <int>defender[8]
        if weapon == DAGGER:
            save_target -= 1
            if save_target < 2:
                save_target = 2
            if save_target > 6:
                save_target = 6
        save_target += strength - 3 if strength > 3 else 0
        if weapon == AXE:
            save_target += 1

        if wound_roll == 6 and wound_target < 6 and not critical_used:
            critical_used = True
            critical_roll = d6(random_state)
            damage = 2
            if critical_roll >= 3:
                save_target = 7
            if critical_roll >= 5:
                modifier = 2

        if save_target <= 6 and d6(random_state) >= save_target:
            continue
        if started_knocked:
            state[0] = OUT
            return 1

        while damage > 0:
            wounds[0] -= 1
            if wounds[0] <= 0:
                result = injury(random_state, weapon, modifier)
                if result > state[0]:
                    state[0] = result
            damage -= 1
        if state[0] != STANDING:
            return 1
    return 0


cdef int one_duel(
    long long[:] candidate,
    long long[:] enemy,
    uint64_t* random_state,
) noexcept nogil:
    cdef int wounds1 = <int>candidate[3]
    cdef int wounds2 = <int>enemy[3]
    cdef int state1 = STANDING
    cdef int state2 = STANDING
    cdef int phase
    cdef int first
    cdef int p1
    cdef int p2
    cdef bint stood1
    cdef bint stood2
    cdef bint candidate_charges = (pcg32(random_state) & 1) == 0
    cdef bint first_round

    for phase in range(100):
        stood1 = False
        stood2 = False
        if phase % 2 == 0:
            if state1 == STUNNED:
                state1 = KNOCKED_DOWN
            elif state1 == KNOCKED_DOWN:
                state1 = STANDING
                stood1 = True
        else:
            if state2 == STUNNED:
                state2 = KNOCKED_DOWN
            elif state2 == KNOCKED_DOWN:
                state2 = STANDING
                stood2 = True

        first_round = phase == 0
        if state1 != STANDING and state2 != STANDING:
            continue
        if state1 != STANDING:
            first = 2
        elif state2 != STANDING:
            first = 1
        else:
            p1 = priority(<int>candidate[6], first_round, first_round and candidate_charges, stood1)
            p2 = priority(<int>enemy[6], first_round, first_round and not candidate_charges, stood2)
            if p1 != p2:
                first = 1 if p1 < p2 else 2
            elif candidate[4] != enemy[4]:
                first = 1 if candidate[4] > enemy[4] else 2
            else:
                first = 1 if (pcg32(random_state) & 1) == 0 else 2

        if first == 1:
            resolve_attacks(candidate, enemy, &wounds2, &state2, first_round, random_state)
            if state2 == OUT:
                return 1
            if state2 == STANDING:
                resolve_attacks(enemy, candidate, &wounds1, &state1, first_round, random_state)
        else:
            resolve_attacks(enemy, candidate, &wounds1, &state1, first_round, random_state)
            if state1 == OUT:
                return 0
            if state1 == STANDING:
                resolve_attacks(candidate, enemy, &wounds2, &state2, first_round, random_state)
        if state1 == OUT:
            return 0
        if state2 == OUT:
            return 1
    return -1


cpdef tuple simulate_simple(
    long long[:] candidate,
    long long[:] enemy,
    int total,
    unsigned long long seed,
):
    cdef uint64_t random_state = <uint64_t>seed + 0x9E3779B97F4A7C15ULL
    cdef int wins = 0
    cdef int resolved = 0
    cdef int result
    cdef int index
    with nogil:
        for index in range(total):
            result = one_duel(candidate, enemy, &random_state)
            if result >= 0:
                resolved += 1
                wins += result
    return wins, resolved
