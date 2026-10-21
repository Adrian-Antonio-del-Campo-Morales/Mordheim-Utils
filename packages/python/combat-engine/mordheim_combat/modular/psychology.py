"""Initial duel charges and source-specific Fear consequences."""
from dataclasses import replace

from mordheim_combat import phases
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.leadership import undead_foes_fear_immunity
from mordheim_combat.modular.state import DuelState
from mordheim_core.dice import DecisionPolicy, DiceSource
from mordheim_core.models import CompiledFighter


def fears_opponent_fire(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    return (phases.has_tag(fighter.global_effects, "mechanic.fears-fire")
            and (phases.has_tag(enemy.global_effects, "condition.open-flame")
                 or phases.has_tag(enemy.global_effects, "attack.fire")
                 or any(phases.has_tag(weapon, "attack.fire")
                        for weapon in (enemy.main_weapon, enemy.off_hand) if weapon is not None)))


def causes_fear(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    if (phases.has_tag(enemy.global_effects, "mechanic.fear-of-snakes")
            and any(phases.has_tag(fighter.global_effects, tag) for tag in
                    ("species.snake", "species.serpent"))):
        return True
    if (phases.has_tag(enemy.global_effects, "mechanic.fear-of-elves")
            and any(phases.has_tag(fighter.global_effects, tag) for tag in
                    ("species.elf", "species.high-elf", "species.dark-elf", "species.wood-elf"))):
        return True
    if (phases.has_tag(fighter.global_effects, "mechanic.fear-beastmen")
            and phases.has_tag(enemy.global_effects, "species.beastman")):
        return True
    if (phases.has_tag(fighter.global_effects, "mechanic.morrs-servant")
            and phases.has_tag(enemy.global_effects, "nature.undead")):
        return True
    if phases.has_tag(fighter.global_effects, "mechanic.beauty-of-the-sea"):
        if not any(phases.has_tag(enemy.global_effects, tag) for tag in ("sex.male", "sex.female")):
            raise ValueError("Beauty of the Sea requires the opponent's explicit male/female fact")
        if phases.has_tag(enemy.global_effects, "sex.female"):
            return True
    if (phases.has_tag(fighter.global_effects, "mechanic.fear-human")
            and phases.has_tag(enemy.global_effects, "species.human")):
        return True
    if fears_opponent_fire(enemy, fighter):
        return True
    if phases.has_tag(fighter.global_effects, "mechanic.causes-fear"):
        return True
    # Beastbane belongs to a wielded weapon and affects animals only. An
    # animal frightening ordinary warriors does not imply the reverse.
    return (phases.has_tag(enemy.global_effects, "species.animal")
            and any(phases.has_tag(weapon, "weapon.beastlash")
                    for weapon in (fighter.main_weapon, fighter.off_hand) if weapon is not None))


def resolve_stupidity(first, second, state, dice, decisions):
    """Refresh the active duelist's Psychology result until its next own turn."""
    is_first = state.first_player_turn
    fighter = first if is_first else second
    current = state.first if is_first else state.second
    if not current.active or not (current.lunatic_stupidity or phases.has_tag(fighter.global_effects, "mechanic.stupidity")
                                  or "disability.6" in current.resources_spent):
        return state
    label = "first" if is_first else "second"
    passed = (current.frenzy or phases.has_tag(fighter.global_effects, "condition.stupidity-exempt")
        or state.round_index == 0 and state.initial_charge_flags[int(not is_first)]
        and phases.has_tag(fighter.global_effects, "condition.impetuous-charge"))
    if not passed and "disability.6" in current.resources_spent:
        supplied_hero = phases.has_tag(fighter.global_effects, "condition.disability-hero-nearby")
        heroes = ()
        if state.context is not None:
            context = state.context
            participant = context.facts.first_id if is_first else context.facts.second_id
            side = context.participant(participant).side_id
            heroes = tuple(record for record in context.facts.nearby
                if phases.has_tag(record.fighter.global_effects, "fighter-kind.hero"))
            passed = any(record.side_id == side and record.condition != "out"
                and context.distance(participant, record.participant_id) <= 6 for record in heroes)
        passed = passed or supplied_hero and not heroes
    # The printed Rat Ogre exemption: a Skaven Hero supplied within six inches
    # exempts the bearer, with no Stupidity test at all.  The nearby records and
    # distances are caller-supplied duel facts; the clause never simulates the
    # surrounding warband or a board.  The bearer's own warband group scopes the
    # concession to the Skaven warriors that print it, so another stupid
    # creature standing beside a supplied Skaven Hero does not borrow it.
    # The printed clause is shared by the Skaven bands whose Rat Ogres print it:
    # Clan Mors, Clan Moulder and Clan Pristekk.
    printed_bands = ("band.skaven-of-clan-mors-kaz",
                     "band.skaven-of-clan-moulder-web",
                     "band.skaven-of-clan-pristekk-sc")
    own_band = next((band for band in printed_bands
                     if phases.has_tag(fighter.global_effects, band)), None)
    if (not passed and phases.has_tag(fighter.global_effects, "mechanic.stupidity")
            and (phases.has_tag(fighter.global_effects, "warband-group.skaven")
                 or own_band is not None)):
        exempting = ()
        if state.context is not None:
            context = state.context
            participant = context.facts.first_id if is_first else context.facts.second_id
            side = context.participant(participant).side_id
            exempting = tuple(record for record in context.facts.nearby
                if record.side_id == side and record.condition != "out"
                and phases.has_tag(record.fighter.global_effects, "fighter-kind.hero")
                and (phases.has_tag(record.fighter.global_effects, "species.skaven")
                     or own_band is not None
                     and phases.has_tag(record.fighter.global_effects, own_band)))
            passed = any(context.distance(participant, record.participant_id) <= 6
                         for record in exempting)
    if not passed and phases.has_tag(fighter.global_effects, 'mechanic.bear-handler-recipient'):
        supplied = phases.has_tag(fighter.global_effects, 'condition.bear-handler-nearby')
        providers = ()
        if state.context is not None:
            context = state.context
            participant = context.facts.first_id if is_first else context.facts.second_id
            side = context.participant(participant).side_id
            providers = tuple(provider for provider in context.facts.nearby
                if phases.has_tag(provider.fighter.global_effects, 'mechanic.bear-handler'))
            passed = any(provider.side_id == side and provider.condition != 'out'
                and context.distance(participant, provider.participant_id) <= 6
                for provider in providers)
        # The supplied condition is the qualified nearby Tamer fact. Explicit
        # provider records take precedence when they contradict that fact.
        passed = passed or supplied and not providers
    if not passed:
        passed, current = resolve_local_leadership(
            fighter, state, dice, decisions, f"round.{state.round_index}.{label}.stupidity",
            first=is_first, psychology=current.drunken_result != 1 and not current.lunatic_stupidity,
            stupidity=True,
            opponent=second if is_first else first, return_state=True)
    failed = not passed
    current = replace(current, stupidity_failed=failed)
    state = replace(state, **{label: current})
    # The initial voluntary charge cannot establish contact after a failed test.
    if failed and state.round_index == 0 and state.initial_charge_flags[int(not is_first)]:
        charges = list(state.initial_charge_flags)
        charges[int(not is_first)] = False
        state = replace(state, first_charged=charges[0], second_charged=charges[1],
            initial_first_player_turn=is_first, engaged=state.engaged and any(charges),
            failed_charges=state.failed_charges | {label})
    return state


def resolve_fear(
    first: CompiledFighter, second: CompiledFighter, state: DuelState,
    dice: DiceSource, decisions: DecisionPolicy,
) -> DuelState:
    if state.round_index != 0 or not state.engaged:
        return state
    # Calling both verifies required opponent facts before any roll.
    first_fear, second_fear = causes_fear(first, second), causes_fear(second, first)
    charges = list(state.initial_charge_flags)
    states = [state.first, state.second]
    for index, (target, singer) in enumerate(((first, second), (second, first))):
        gate = None
        if (phases.has_tag(target.global_effects, "mechanic.ashamed-and-afraid")
                and phases.has_tag(singer.global_effects, "identity.sigmarite-opponent")):
            gate = "ashamed-and-afraid"
        elif phases.has_tag(singer.global_effects, "mechanic.slaanesh-charge-test"):
            gate = "slaanesh-charge"
        elif (phases.has_tag(singer.global_effects, "mechanic.hypnotic-musk")
                and not target.mounted
                and not phases.has_tag(target.global_effects, "condition.goading-charge")
                and any(phases.has_tag(target.global_effects, tag) for tag in
                        ("species.animal", "species.normal-animal", "species.beast"))):
            gate = "hypnotic-musk-charge"
        elif phases.has_tag(singer.global_effects, "mechanic.opposite-sex-charge-test"):
            sexes = tuple(next((sex for sex in ("male", "female")
                if phases.has_tag(f.global_effects, "sex." + sex)), None) for f in (target, singer))
            if None in sexes:
                raise ValueError("Charismatic requires both duelists' explicit male/female facts")
            if sexes[0] != sexes[1]:
                gate = "charismatic-charge"
        compelled = phases.has_tag(target.global_effects, "condition.impetuous-charge")
        if gate is not None and charges[index]:
            passed, states[index] = resolve_local_leadership(target,
                replace(state, first=states[0], second=states[1]), dice, decisions,
                f"round.0.{'first' if index == 0 else 'second'}.{gate}",
                first=index == 0, opponent=singer, return_state=True, contacting=False)
            if not passed:
                charges[index] = False
                state = replace(state, failed_charges=state.failed_charges | {"first" if index == 0 else "second"})
        if (charges[index] and phases.has_tag(singer.global_effects, "mechanic.beauty-of-the-sea")
                and phases.has_tag(target.global_effects, "sex.male")
                and not phases.has_tag(target.global_effects, "species.animal") and not compelled):
            passed, states[index] = resolve_local_leadership(target,
                replace(state, first=states[0], second=states[1]), dice, decisions,
                f"round.0.{'first' if index == 0 else 'second'}.beauty-charge",
                first=index == 0, psychology=True, opponent=singer, return_state=True)
            if passed:
                states[index] = states[index].spend("beauty.passed")
            else:
                charges[index] = False
                state = replace(state, failed_charges=state.failed_charges | {"first" if index == 0 else "second"})
    state = replace(state, first=states[0], second=states[1],
        first_charged=charges[0], second_charged=charges[1],
        initial_first_player_turn=state.first_player_turn,
        engaged=state.engaged and (any(charges) or not state.failed_charges))
    if not state.engaged or not (first_fear or second_fear):
        return state
    fighters = (first, second)
    states = [state.first, state.second]
    charges = list(state.initial_charge_flags)
    failed = set(state.failed_charges)

    def morrs_servant(index):
        return (phases.has_tag(fighters[1 - index].global_effects, "mechanic.morrs-servant")
                and phases.has_tag(fighters[index].global_effects, "nature.undead"))

    def needs_test(index):
        enemy = fighters[1 - index]
        if (charges[index] and phases.has_tag(fighters[index].global_effects, "mechanic.ere-we-go")):
            return False
        if charges[index] and phases.has_tag(fighters[index].global_effects, "condition.impetuous-charge"):
            return False
        if (phases.has_tag(fighters[index].global_effects, "mechanic.accustomed-to-fear")
                and any(phases.has_tag(enemy.global_effects, tag) for tag in
                        ("species.vampire", "undead-kind.skeleton", "undead-kind.spirit"))):
            return False
        if morrs_servant(index):
            # This source expressly overrides Undead Psychology exemptions.
            return states[index].condition == phases.Condition.STANDING and states[1 - index].active
        if fears_opponent_fire(fighters[index], fighters[1 - index]):
            return states[index].condition == phases.Condition.STANDING and states[1 - index].active
        return (states[index].condition == phases.Condition.STANDING
                and states[1 - index].active
                and causes_fear(fighters[1 - index], fighters[index])
                and (not causes_fear(fighters[index], fighters[1 - index])
                     or phases.has_tag(fighters[index].global_effects, "mechanic.craven"))
                and not states[index].frenzy
                and not phases.has_tag(fighters[index].global_effects, "mechanic.fear-immunity")
                and not undead_foes_fear_immunity(fighters[index], fighters[1 - index])
                and not phases.has_tag(fighters[index].global_effects, "mechanic.psychology-immunity"))

    def test_fear(index, label, suffix):
        ordinary_fear = not (morrs_servant(index) or fears_opponent_fire(fighters[index], fighters[1 - index]))
        passed, states[index] = resolve_local_leadership(
            fighters[index], replace(state, first=states[0], second=states[1]), dice, decisions,
            f"round.0.{label}.fear.{suffix}", first=index == 0,
            psychology=ordinary_fear, fear=ordinary_fear,
            opponent=fighters[1 - index], return_state=True, contacting=suffix != "charge",
            close_combat=suffix == "charged")
        return passed

    # A voluntary charge must succeed before contact/charged reactions exist.
    for index, label in enumerate(("first", "second")):
        if charges[index] and needs_test(index) and not test_fear(index, label, "charge"):
            if phases.has_tag(fighters[index].global_effects, "mechanic.wheelo-impact"):
                states[index] = replace(states[index], fear_hit_sixes=True)
            else:
                charges[index] = False
                failed.add(label)
    engaged = state.engaged and (any(charges) or not failed)
    if engaged:
        for index, label in enumerate(("first", "second")):
            if charges[1 - index] and needs_test(index) and not test_fear(index, label, "charged"):
                states[index] = replace(states[index], fear_hit_sixes=True)
    if (states == [state.first, state.second] and tuple(charges) == state.initial_charge_flags
            and failed == set(state.failed_charges)):
        return state
    return replace(state, first=states[0], second=states[1],
        first_charged=charges[0], second_charged=charges[1],
        initial_first_player_turn=state.first_player_turn,
        failed_charges=frozenset(failed), engaged=engaged)
