"""Source-qualified local Leadership tests; geometry is supplied by the caller."""
from mordheim_combat import phases
from mordheim_combat.modular.state import DuelState, FighterState
from mordheim_core.dice import DecisionPolicy, DiceSource, RollRequest
from mordheim_core.models import CompiledFighter


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
    holy_relic = phases.has_tag(fighter.global_effects, "defence.holy-relic")
    if (first_failure or holy_relic) and not return_state:
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
    context = state.context
    if context is not None and not handler_only and not own_value_only:
        participant_id = context.facts.first_id if first else context.facts.second_id
        side = context.participant(participant_id).side_id
        # A local side and canonical band identify this supported warband group.
        # Do not lend a leader's value to opposing or foreign-band participants.
        bands = {tag for tag in fighter.global_effects.tags if tag.startswith("band.")}
        borrowed = False
        for provider in context.facts.nearby:
            # Needle and Thread: a model whose mouth was sewn cannot use its
            # leader ability.  The duel can only sew a combatant (state.mouth_sewn
            # is set when this bearer stuns an opponent), while a Leader is used
            # as a supplied non-combatant fact, so the printed denial reaches
            # this loop as the supplied sewn-mouth fact on the provider.  A
            # duel participant is never itself a supplied provider: nearby
            # identifiers are distinct from first_id/second_id by validation.
            if (phases.has_tag(provider.fighter.global_effects, "condition.mouth-sewn")
                    or provider.side_id != side or provider.condition != "standing"
                    or not bands.intersection(provider.fighter.global_effects.tags)
                    or not phases.has_tag(provider.fighter.global_effects, "mechanic.leader-six")):
                continue
            radius = (12 if phases.has_tag(provider.fighter.global_effects, "mechanic.leader-twelve")
                      else 4 if phases.has_tag(provider.fighter.global_effects, "mechanic.leader-four") else 6)
            if context.distance(participant_id, provider.participant_id) > radius:
                continue
            if phases.has_tag(provider.fighter.global_effects, "mechanic.leader-fallback") and any(
                    other.side_id == side and other.condition == "standing"
                    and other.fighter.fighter_id.endswith(":witch-doctor")
                    and bands.intersection(other.fighter.global_effects.tags)
                    and phases.has_tag(other.fighter.global_effects, "mechanic.leader-six")
                    and context.distance(participant_id, other.participant_id) <= 6
                    for other in context.facts.nearby):
                continue
            provider_effect = provider.fighter.global_effects
            supplied_reroll = supplied_reroll or phases.has_tag(provider_effect, "mechanic.undivided-leader") or (
                phases.has_tag(provider_effect, "mechanic.wizened-halfling")
                and phases.has_tag(fighter.global_effects, "species.halfling"))
            if not borrowed and decisions.choose(f"{key}.leader.{provider.participant_id}", fighter):
                value = provider.fighter.characteristics.leadership
                borrowed = True
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
    passed = phases.resolve_leadership(value, dice, key, discard_highest=discard_highest and not discard_lowest, discard_lowest=discard_lowest)
    first_failed = first_failure and "leadership.first-failed" not in current.resources_spent and not passed
    if first_failed:
        # Declining the first failure does not reserve a later failure instead.
        current = current.spend("leadership.first-failed")
    mandatory = phases.has_tag(fighter.global_effects, "mechanic.mandatory-leadership-reroll")
    eligible = (first_failed or mandatory or supplied_reroll or phases.has_tag(fighter.global_effects, "mechanic.leadership-reroll")
                or fear and phases.has_tag(fighter.global_effects, "mechanic.fear-reroll"))
    if not passed and eligible and (mandatory or decisions.choose(f"{key}.reroll", fighter)):
        # Reuse the chosen threshold and dice convention; never reroll a reroll.
        passed = phases.resolve_leadership(value, dice, f"{key}.reroll", discard_highest=discard_highest and not discard_lowest, discard_lowest=discard_lowest)
    return result(passed)
