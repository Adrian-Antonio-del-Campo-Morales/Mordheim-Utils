"""Source-qualified local Leadership tests; geometry is supplied by the caller."""
from dataclasses import replace
from mordheim_combat import phases
from mordheim_combat.modular.state import DuelState, FighterState
from mordheim_core.dice import DecisionPolicy, DiceSource, RollRequest
from mordheim_core.models import CompiledFighter, EffectSet


def _leader_radius(effect) -> int:
    """The printed supplied-Leader radius of one provider's own effect set."""
    return (12 if phases.has_tag(effect, "mechanic.leader-twelve")
            else 4 if phases.has_tag(effect, "mechanic.leader-four")
            else 6)


def _supplied_provider(provider, bands):
    """Printed supplied-provider contract of one nearby local participant.

    Returns ``(radius, consequence)`` or ``None``.  ``consequence`` is one of
    ``leader`` (the provider lends his own Leadership), ``relay`` (the provider
    relays a leader's Leadership, never his own) or ``songster`` (the provider
    grants a re-roll with +1 without lending any value).
    """
    effect = provider.fighter.global_effects
    # Printed Slave Driver: the Overseer lends his Leadership within 3 inches,
    # widened to 6 while he carries a scourge (his own supplied fact).
    if phases.has_tag(effect, "mechanic.slave-driver"):
        scourge = phases.has_tag(effect, "condition.scourge-armed") or any(
            phases.has_tag(weapon, "weapon.pirate-scourge") for weapon in
            (provider.fighter.main_weapon, provider.fighter.off_hand or EffectSet()))
        return (6 if scourge else 3, "leader")
    if phases.has_tag(effect, "mechanic.songster"):
        return (6, "songster")
    if not bands.intersection(effect.tags):
        return None
    # Printed Relay Orders: the Adjutant relays the leader's Leadership within
    # six inches, twelve while he carries Battle Tongue.
    if phases.has_tag(effect, "mechanic.relay-orders"):
        return (_leader_radius(effect), "relay")
    # Printed Songster: a friendly model within six inches re-rolls a failed
    # Leadership test with +1 to Leadership; no Leadership value is lent.
    # The ordinary Leader rule, in its printed radius.
    if phases.has_tag(effect, "mechanic.leader-six"):
        return (6 if phases.has_tag(effect, "mechanic.dim-witted-leader") else _leader_radius(effect), "leader")
    return None


def _relayed_leader(context, provider, bands):
    """The supplied Leader an Adjutant relays, or ``None`` while he cannot use one.

    The printed prerequisite is that the Adjutant is able to use his leader's
    Leadership, so the leader must be supplied on the Adjutant's own side and
    band and be within the Adjutant's own borrow radius.
    """
    for candidate in context.facts.nearby:
        if candidate.participant_id == provider.participant_id:
            continue
        effect = candidate.fighter.global_effects
        if (candidate.side_id != provider.side_id or candidate.condition != "standing"
                or not bands.intersection(effect.tags)
                or not phases.has_tag(effect, "mechanic.leader-six")):
            continue
        if context.distance(provider.participant_id, candidate.participant_id) <= _leader_radius(effect):
            return candidate
    return None


def _instructing_leader(context, participant_id, side, bands, inches):
    """A supplied same-band Leader of ``side`` within ``inches`` and in action.

    The printed Devoted clause names the Warrior Priest and the printed Broken
    Spirit clause the Slave Merchant; each is that band's only Leader profile,
    so the supplied Leader of the recipient's own band is that named model.  A
    Warrior Priest who is only Knocked Down still grants the printed re-roll,
    because the clause prints no requirement that he stand.
    """
    for candidate in context.facts.nearby:
        effect = candidate.fighter.global_effects
        if (candidate.side_id != side or candidate.condition == "out"
                or not bands.intersection(effect.tags)
                or not phases.has_tag(effect, "mechanic.leader-six")):
            continue
        if context.distance(participant_id, candidate.participant_id) <= inches:
            return True
    return False


def resolve_local_leadership(
    fighter: CompiledFighter, state: DuelState, dice: DiceSource,
    decisions: DecisionPolicy, key: str, *, first: bool, psychology: bool = False,
    stupidity: bool = False, fear: bool = False, discard_lowest: bool = False,
    opponent: CompiledFighter | None = None, return_state: bool = False,
    own_value_only: bool = False, contacting: bool = True,
) -> bool | tuple[bool, FighterState]:
    """Return the updated fighter state for tests with a persistent reroll resource."""
    current = state.first if first else state.second
    first_failure = phases.has_tag(fighter.global_effects, "mechanic.first-failed-leadership-reroll")
    poetry = phases.has_tag(fighter.global_effects, "condition.poetry-victorious-leader")
    holy_relic = phases.has_tag(fighter.global_effects, "defence.holy-relic")
    roll_resource = any(phases.has_tag(fighter.global_effects, tag) for tag in
        ("mechanic.ranalds-luck", "mechanic.oracle", "mechanic.augur-one-roll-reroll", "skill.luck"))
    if (first_failure or holy_relic or roll_resource or poetry) and not return_state:
        raise ValueError("persistent Leadership resource requires the returned fighter state")

    def result(passed):
        return (passed, current) if return_state else passed

    if psychology and (current.frenzy or phases.has_tag(fighter.global_effects, "mechanic.psychology-immunity")):
        return result(True)
    if fear and phases.has_tag(fighter.global_effects, "mechanic.fear-immunity"):
        return result(True)
    if phases.has_tag(fighter.global_effects, "mechanic.automatic-leadership"):
        return result(True)
    if holy_relic and "leadership.holy-relic" not in current.resources_spent:
        current = current.spend("leadership.holy-relic")
        return result(True)
    if phases.has_tag(fighter.global_effects, "mechanic.sigmar-enlightened"):
        if opponent is None:
            if state.context is None:
                raise ValueError("Enlightened requires the duel opponent's explicit facts")
            opponent_id = state.context.facts.second_id if first else state.context.facts.first_id
            opponent = state.context.participant(opponent_id).fighter
        if any(phases.has_tag(opponent.global_effects, tag) for tag in (
                "species.orc", "species.goblin", "warband-group.chaotic", "nature.daemon",
                "nature.possessed", "identity.chaos-follower")):
            return result(True)
    value = fighter.characteristics.leadership
    handler_only = phases.has_tag(fighter.global_effects, "mechanic.handler-leadership")
    if handler_only and fighter.stupidity_leadership is not None:
        value = fighter.stupidity_leadership
    supplied_reroll = False
    songster_reroll = False
    context = state.context
    # Deceive prints "using its own Leadership": the tested model may not borrow
    # a nearby leader's value, so the supplied-leader block is skipped entirely.
    if context is not None:
        participant_id = context.facts.first_id if first else context.facts.second_id
        side = context.participant(participant_id).side_id
        # A local side and canonical band identify this supported warband group.
        # Do not lend a leader's value to opposing or foreign-band participants.
        bands = {tag for tag in fighter.global_effects.tags if tag.startswith("band.")}
        if handler_only and not own_value_only:
            for provider in context.facts.nearby:
                if (provider.side_id == side and provider.condition != 'out'
                        and phases.has_tag(provider.fighter.global_effects, 'mechanic.bear-handler')
                        and context.distance(participant_id, provider.participant_id) <= 6
                        and decisions.choose(f"{key}.handler.{provider.participant_id}", fighter)):
                    value = provider.fighter.characteristics.leadership
                    break
        if phases.has_tag(fighter.global_effects, "mechanic.broken-spirit"):
            # Printed Broken Spirit: the Eunuch automatically passes while the
            # Slave Merchant is not out of action.  The clause prints no range,
            # so the supplied leader's distance is not read at all.
            for candidate in context.facts.nearby:
                effect = candidate.fighter.global_effects
                if (candidate.side_id == side and candidate.condition != "out"
                        and bands.intersection(effect.tags)
                        and phases.has_tag(effect, "mechanic.leader-six")):
                    return result(True)
        if (phases.has_tag(fighter.global_effects, "mechanic.devoted")
                and _instructing_leader(context, participant_id, side, bands, 12)):
            # Printed Devoted: the Hound re-rolls a failed Leadership check
            # while the Warrior Priest is within twelve inches.
            supplied_reroll = True
        # Printed Songster: any friendly model within six inches of the supplied
        # Minstrel may re-roll a failed Leadership test with +1 to Leadership.
        # The clause qualifies the recipient, not the Minstrel, so the gift does
        # not depend on the recipient borrowing a leader's value and a Knocked
        # Down Minstrel still sings; only his being out of action ends it.
        for provider in context.facts.nearby:
            contract = _supplied_provider(provider, bands)
            if (provider.side_id != side or provider.condition == "out"
                    or contract is None or contract[1] != "songster"):
                continue
            if context.distance(participant_id, provider.participant_id) <= contract[0]:
                songster_reroll = True
        if (not handler_only and not own_value_only
                and not phases.has_tag(fighter.global_effects, 'mechanic.own-leadership')):
            usable = []
            for provider in context.facts.nearby:
                if (provider.side_id != side or provider.condition != "standing"
                        or phases.has_tag(provider.fighter.global_effects, "condition.mouth-sewn")):
                    continue
                if (phases.has_tag(provider.fighter.global_effects, "mechanic.slave-driver")
                        and not phases.has_tag(fighter.global_effects, "identity.slave")):
                    continue
                contract = _supplied_provider(provider, bands)
                if contract is None:
                    continue
                radius, consequence = contract
                if context.distance(participant_id, provider.participant_id) > radius:
                    continue
                if consequence == "songster":
                    songster_reroll = True
                    continue
                if consequence == "relay":
                    relayed = _relayed_leader(context, provider, bands)
                    if relayed is None:
                        continue
                    usable.append((provider, provider.fighter.global_effects,
                                   relayed.fighter.characteristics.leadership))
                else:
                    usable.append((provider, provider.fighter.global_effects,
                                   7 if phases.has_tag(provider.fighter.global_effects, "mechanic.dim-witted-leader")
                                   else provider.fighter.characteristics.leadership))
            # Second in Command: the printed fallback Leader is offered only while
            # no other standing leader of the same warband can lend his Leadership
            # (directly or through a relay), and a fallback never suppresses
            # itself.  A knocked-down or absent senior leader leaves the fallback.
            senior = any(not phases.has_tag(provider_effect, "mechanic.leader-fallback")
                         for _, provider_effect, _ in usable)
            borrowed = False
            for provider, provider_effect, lent in usable:
                supplied_reroll = supplied_reroll or phases.has_tag(provider_effect, "mechanic.undivided-leader") or (
                    phases.has_tag(provider_effect, "mechanic.wizened-halfling")
                    and phases.has_tag(fighter.global_effects, "species.halfling"))
                if senior and phases.has_tag(provider_effect, "mechanic.leader-fallback"):
                    continue
                if not borrowed and decisions.choose(f"{key}.leader.{provider.participant_id}", fighter):
                    value = lent
                    borrowed = True
    if poetry and 'poetry-first-leadership' not in current.resources_spent:
        current = current.spend('poetry-first-leadership')
        if value is not None:
            value += 1
    if opponent is None and context is not None:
        enemy_id = context.facts.second_id if first else context.facts.first_id
        opponent = context.participant(enemy_id).fighter
    if (contacting and opponent is not None
            and phases.has_tag(opponent.global_effects, "mechanic.enchanting-beauty")
            and not any(phases.has_tag(fighter.global_effects, tag) for tag in ("nature.undead", "nature.daemon"))
            and value is not None):
        value -= 1
    # Ghostly Howl: the tested enemy's Leadership drops by D6 on a fear test
    # while the howling bearer faces it.  The duel supplies the proximity of its
    # two participants; the printed 6" radius to any other unit stays outside.
    if fear and opponent is not None and phases.has_tag(opponent.global_effects, "mechanic.ghostly-howl"):
        value -= dice.roll(RollRequest(f"{key}.ghostly-howl"))
    if stupidity and value is not None:
        value += fighter.stupidity_leadership_bonus
    # The tested model keeps its dice benefit when borrowing a leader's value.
    discard_highest = (phases.has_tag(fighter.global_effects, "mechanic.cold-blooded-leadership")
        or (psychology and phases.has_tag(fighter.global_effects, "mechanic.cold-blooded-psychology")))
    from mordheim_combat.modular.contexts import OwnedRollDice
    dice = OwnedRollDice(dice, fighter, current, decisions)
    passed = phases.resolve_leadership(value, dice, key, discard_highest=discard_highest and not discard_lowest, discard_lowest=discard_lowest)
    first_failed = first_failure and "leadership.first-failed" not in current.resources_spent and not passed
    if first_failed:
        # Declining the first failure does not reserve a later failure instead.
        current = current.spend("leadership.first-failed")
    mandatory = phases.has_tag(fighter.global_effects, "mechanic.mandatory-leadership-reroll")
    eligible = (first_failed or mandatory or supplied_reroll or songster_reroll or phases.has_tag(fighter.global_effects, "mechanic.leadership-reroll")
                or phases.has_tag(fighter.global_effects, "condition.command.raise-our-insignia-active")
                or fear and phases.has_tag(fighter.global_effects, "mechanic.fear-reroll"))
    if (not passed and eligible and not dice._rerolled_results
            and (mandatory or decisions.choose(f"{key}.reroll", fighter))):
        # Reuse the chosen threshold and dice convention; never reroll a reroll.
        passed = phases.resolve_leadership((min(10, value+1) if songster_reroll else value), dice, f"{key}.reroll", discard_highest=discard_highest and not discard_lowest, discard_lowest=discard_lowest)
    current = replace(current, resources_spent=current.resources_spent | dice.state.resources_spent)
    return result(passed)
