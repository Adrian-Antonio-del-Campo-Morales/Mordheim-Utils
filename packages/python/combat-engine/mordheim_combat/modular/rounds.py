"""combat: Per-round state machine of the modular engine."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import dataclass, replace
from mordheim_combat.modular.aftermath import _black_hunger
from mordheim_combat.modular.aftermath import _revenant_recovery
from mordheim_combat.modular.aftermath import _characteristic_test
from mordheim_combat.modular.aftermath import _fire_recovery
from mordheim_combat.modular.aftermath import _force_of_will
from mordheim_combat.modular.aftermath import _netter
from mordheim_combat.modular.aftermath import _spines
from mordheim_combat.modular.aftermath import _start_round_state
from mordheim_combat.modular.state import _refresh_random_characteristics
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear, resolve_stupidity
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import CombatRoundResult
from mordheim_combat.modular.state import DuelState
from mordheim_combat.modular.equipment import equipment_for_state, is_pistol, whipcrack_weapon
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import PriorityContext
from mordheim_combat.phases import build_attacks
from mordheim_combat.phases import first_acts_before
from mordheim_combat.phases import has_tag
from mordheim_combat.phases import resolve_priority
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


SHADOW_DANCES = (
    "whirling-death", "storm-of-blades", "the-shadows-coil", "woven-mist",
)

# The two Lahmia Vampire powers that open the combat phase with a Leadership
# test on a supplied in-contact enemy: (tag, printed exclusions, key, own value).
# Deceive prints "using its own Leadership" and its failure bars only attacks
# against the Lahmia Vampire; Hypnotize prints no value qualifier and its
# failure bars the target's attacks and makes its assailants hit on +1.
LAHMIA_POWERS = (
    ("mechanic.lahmia-deceive",
     ("nature.undead", "nature.daemon", "mechanic.psychology-immunity"),
     "deceive", True),
    ("mechanic.lahmian-hypnotize",
     ("mechanic.psychology-immunity",),
     "hypnotize", False),
)


# The printed own-turn animosity contracts that suppress the bearer's attacks for
# turn: the ordinary Goblin squabble (a 1) and the Fungus Brew's Rowdy result
# (1-2), which shares the consumer and widens only the printed band.
ANIMOSITY_SOURCES = ("mechanic.goblin-squabble", "mechanic.fungus-rowdy")

# The Dark Jester's printed per-round trick slots.  Confound and Confuse is one
# printed choice with three distinct consequences (the Sidestepper dodge, the
# Babbling Banter modifier pair, the Trip wound replacement), so each round one
# of the three may be active and the choice is supplied by the application, not
# simulated: no round ever activates two tricks of the same rule.
JESTER_TRICK_STATES = ("dodge_trick_active", "banter_trick_active", "trip_trick_active")


@dataclass(frozen=True, slots=True)
class ControlPower:
    """One printed Vampire power that spends a Leadership test to bar a foe.

    ``own_test`` is the Khemrian Seduction's opening test of the Vampire
    herself, ``own_turn_only`` the Lahmia Seduction's "during each Vampire
    turn", ``male_only`` its printed male recipient, ``persistent`` the lasting
    control the two Seduction copies establish (kept on the victim's spent
    resources, ended by the printed Recovery-phase regain test and by the
    printed attack) and ``auto_hit`` Hypnotic Gaze's "all attacks against it hit
    automatically".
    """

    tag: str
    exclusions: tuple[str, ...]
    name: str
    own_value_only: bool = False
    auto_hit: bool = False
    own_turn_only: bool = False
    own_test: bool = False
    male_only: bool = False
    persistent: bool = False


# Hypnotic Gaze and the two Seduction copies.  Each is read from its own printed
# origin, so each carries exactly the exclusions and qualifiers that clause
# prints and never a broader shared list.
CONTROL_POWERS = (
    ControlPower("mechanic.hypnotic-gaze", ("mechanic.psychology-immunity",),
                 "hypnotic-gaze", own_value_only=True, auto_hit=True),
    ControlPower("mechanic.lahmia-seduction",
                 ("mechanic.psychology-immunity", "nature.undead", "nature.daemon",
                  "mechanic.stupidity"),
                 "lahmia-seduction", own_value_only=True, own_turn_only=True,
                 male_only=True, persistent=True),
    ControlPower("mechanic.lahmian-seduction", ("mechanic.psychology-immunity",),
                 "lahmian-seduction", own_value_only=True, own_test=True,
                 persistent=True),
)

# The lasting control of the two Seduction copies lives on the victim's spent
# resources: it must outlive the phase that established it, and the resource
# also names its printed release, because the Khemrian copy ends on any attack
# by the Vampire while the Lahmia copy ends only on one that hits.
SEDUCTION_RESOURCES = ("seduction.controlled.lahmia", "seduction.controlled.lahmian")
CONTROL_RESOURCES = {
    "mechanic.lahmia-seduction": "seduction.controlled.lahmia",
    "mechanic.lahmian-seduction": "seduction.controlled.lahmian",
}
LAHMIA_SEDUCTION_RESOURCE = "seduction.controlled.lahmia"


def select_shadow_dance(fighter, current, decisions, *, key):
    """Apply one learned dance for this combat phase, remembering only the last."""
    available = [dance for dance in SHADOW_DANCES
        if has_tag(fighter.global_effects, f"dance.{dance}")
        and dance != current.last_shadow_dance]
    if current.condition != Condition.STANDING or not available:
        return fighter, replace(current, last_shadow_dance=None)
    selected = next((dance for dance in available
        if decisions.choose(f"{key}.dance.{dance}", tuple(available))), None)
    if selected is None:
        raise ValueError("a Wardancer must choose an available learned Shadow Dance")
    effect = fighter.global_effects
    if selected == "whirling-death":
        effect = replace(effect, injury_modifier=effect.injury_modifier + 1)
    elif selected == "storm-of-blades":
        effect = replace(effect, attacks_bonus=effect.attacks_bonus + 1)
    elif selected == "the-shadows-coil":
        effect = replace(effect, tags=(*effect.tags, "dance.shadows-coil-active"))
    else:
        effect = replace(effect, tags=(*effect.tags, "dance.woven-mist-active"))
    return replace(fighter, global_effects=effect), replace(current, last_shadow_dance=selected)


def resolve_round(
    first: CompiledFighter, second: CompiledFighter, state: DuelState,
    dice: DiceSource, decisions: DecisionPolicy | None = None,
) -> CombatRoundResult:
    """Resolve one complete scalar round through the fixed phase pipeline."""
    decisions = decisions or AlwaysAccept()
    # Only already-active individual Command effects are supplied; no casting,
    # issuing Knight, range or group lifecycle is simulated.
    initial_first = (state.first_charged if state.initial_first_player_turn is None
                     else state.initial_first_player_turn)
    for owner_first, fighter in ((True, first), (False, second)):
        effect = fighter.global_effects
        if (state.round_index == 0 and fighter.mounted
                and state.initial_charge_flags[int(not owner_first)]
                and has_tag(effect, "condition.righteous-charge")):
            effect = replace(effect, tags=(*effect.tags, "condition.righteous-charge-active",
                "mechanic.causes-fear", "mechanic.psychology-immunity"))
        if (state.round_index == 0 and has_tag(effect,
                "condition.command.follow-me-mine-pugnacious-ones")):
            effect = replace(effect, tags=(*effect.tags, "condition.command.follow-me-active"))
        if (state.round_index < (2 if initial_first == owner_first else 1)
                and has_tag(effect, "condition.command.art-thou-ready-to-die-fighting")):
            effect = replace(effect, out_of_action_threshold=6)
        fighter = replace(fighter, global_effects=effect)
        if owner_first:
            first = fighter
        else:
            second = fighter
    label = "first" if state.first_player_turn else "second"
    fighter = first if state.first_player_turn else second
    current = _revenant_recovery(fighter, getattr(state, label), dice,
                                f"round.{state.round_index}.{label}.revenant")
    state = replace(state, **{label: current})
    # The Sermon's self-bonus belongs to the active player's combat phase only.
    sermon_key = f"round.{state.round_index}.rousing-sermon"
    if (current.condition in (phases.Condition.STANDING, phases.Condition.KNOCKED_DOWN)
            and has_tag(fighter.global_effects, "mechanic.rousing-sermon")
            and "rousing-sermon" not in current.resources_spent
            and decisions.choose(f"round.{state.round_index}.{label}.rousing-sermon", fighter)):
        current = current.spend("rousing-sermon").spend(sermon_key)
        state = replace(state, **{label: current})
    if sermon_key in current.resources_spent:
        fighter = replace(fighter, global_effects=replace(fighter.global_effects,
            attacks_bonus=fighter.global_effects.attacks_bonus + 1))
        if state.first_player_turn:
            first = fighter
        else:
            second = fighter
    first, second = (apply_opponent_leadership(first, second, state),
                     apply_opponent_leadership(second, first, state))
    # Transform belongs to the bearer's own turn and is read before the round's
    # equipment is projected, because entering the form discards equipment in
    # that same turn.  The roll happens whether or not blows are exchanged; only
    # a Transformed bearer in combat is exempt, and the form outlives the turn
    # that rolled it.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.bitten-transform"):
            continue
        current = state.first if is_first else state.second
        label = "first" if is_first else "second"
        # Madness prints "Stupidity this turn", so the failure it caused is
        # bounded by the turn that rolled it: the result is dropped here, and
        # with it the one Stupidity failure that the result of 1 caused, so a
        # Madness never bars a later phase.
        madness_this_turn = bool(getattr(current, "bitten_result", 0) == 1)
        current = replace(current, bitten_result=0,
            stupidity_failed=current.stupidity_failed and not madness_this_turn)
        if is_first == state.first_player_turn and not (current.transformed and state.engaged):
            roll = dice.roll(RollRequest(f"round.{state.round_index}.{label}.bitten"))
            if roll == 1:
                # Reverting is a result of 1, not an injury: the discarded form
                # stays gone and the equipment it cast off is not recovered.
                current = replace(current, bitten_result=1, transformed=False)
            elif roll == 6:
                current = replace(current, bitten_result=6, transformed=True)
            else:
                current = replace(current, bitten_result=roll)
        # A Transformed Bitten keeps the Frenzy the form prints; the form is lost
        # only to the printed result of 1.
        current = replace(current, frenzy=fighter.global_effects.frenzy or current.transformed)
        if current.transformed:
            # "suffer no penalties for fighting unarmed" is the penalty-removal
            # the attack pool already consumes; it lasts exactly as long as the
            # form does and never forces the fists on a retained dagger.
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "rule.unarmed-without-penalties")))
        state = replace(state, **{"first" if is_first else "second": current})
        if is_first:
            first = fighter
        else:
            second = fighter
    # Lunatics (Lustria Pygmies) is a rolled own-turn state, not a passive
    # trait: at the start of each of its turns the bearer rolls the printed D6,
    # where 1-3 gains Frenzy and 4-6 gains Stupidity.  The two grants last as
    # their own printed rules do, so they are carried on the state: the Frenzy
    # ends when the warrior is Knocked Down or Stunned and the Stupidity keeps
    # applying for the rest of the duel.  Because the grant is this same printed
    # profile's own consequence it is set directly and is never suppressed by its
    # printed Immunity to Psychology; while the Frenzy holds, the shared Frenzy
    # exemption skips the Stupidity test and, once it is lost, the Stupidity
    # applies normally again.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.lunatics"):
            continue
        label = "first" if is_first else "second"
        current = state.first if is_first else state.second
        if is_first == state.first_player_turn:
            roll = dice.roll(RollRequest(f"round.{state.round_index}.{label}.lunatics"))
            current = replace(current, lunatic_result=roll,
                frenzy=current.frenzy or roll <= 3,
                lunatic_stupidity=current.lunatic_stupidity or roll >= 4)
        state = replace(state, **{label: current})
    if not state.engaged:
        return CombatRoundResult(state, ())
    # The Dark Jester's Confound and Confuse: the printed chooser names one
    # trick per combat turn, so each of the three printed tricks is offered and
    # the first accepted selection lights exactly its own slot.  The shared
    # selection condition ("one trick per round") is the trick record's own
    # fact, supplied by the trick rules themselves, never a simulated
    # subsystem; a bearer that accepts no offer keeps every slot dark.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.confound-and-confuse"):
            continue
        label = "first" if is_first else "second"
        current = state.first if is_first else state.second
        accepted = []
        for slot in JESTER_TRICK_STATES:
            if decisions.choose(f"round.{state.round_index}.{label}.jester-trick.{slot}", fighter):
                accepted.append(slot)
                break
        current = replace(current, resources_spent=current.resources_spent - {"jester.trip"},
            **{slot: slot in accepted for slot in JESTER_TRICK_STATES})
        state = replace(state, **{label: current})
    first_state = replace(state.first, fear_hit_sixes=False)
    second_state = replace(state.second, fear_hit_sixes=False)
    original_first, original_second = first, second
    outcomes: list[AttackOutcome] = []
    first_round = state.round_index == 0
    first_misses = second_misses = False
    if not first_round:
        first_state = _refresh_random_characteristics(
            first, first_state, dice, f"round.{state.round_index}.first"
        )
        second_state = _refresh_random_characteristics(
            second, second_state, dice, f"round.{state.round_index}.second"
        )
    first = equipment_for_state(first, first_state, first_round=first_round)
    second = equipment_for_state(second, second_state, first_round=first_round)
    if not first_round:
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force", sustain=True)
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force", sustain=True)
        if state.first_player_turn:
            first_state, second_state, fire = _fire_recovery(
                first, second, first_state, second_state, dice, f"round.{state.round_index}.first.fire")
        else:
            second_state, first_state, fire = _fire_recovery(
                second, first, second_state, first_state, dice, f"round.{state.round_index}.second.fire")
        outcomes.extend(fire)
    if state.first_player_turn and first_state.condition == Condition.PARALYZED and _characteristic_test(
        first_state.toughness, dice, f"round.{state.round_index}.first.paralysis",
        reroll=phases.has_tag(first.global_effects, "skill.blessed-sight"),
    ):
        first_state = replace(first_state, condition=Condition.STANDING)
    if not state.first_player_turn and second_state.condition == Condition.PARALYZED and _characteristic_test(
        second_state.toughness, dice, f"round.{state.round_index}.second.paralysis",
        reroll=phases.has_tag(second.global_effects, "skill.blessed-sight"),
    ):
        second_state = replace(second_state, condition=Condition.STANDING)
    first_state, first_stood = _start_round_state(first, first_state, recover=state.first_player_turn)
    second_state, second_stood = _start_round_state(second, second_state, recover=not state.first_player_turn)
    first, first_state = select_shadow_dance(first, first_state, decisions,
        key=f"round.{state.round_index}.first")
    second, second_state = select_shadow_dance(second, second_state, decisions,
        key=f"round.{state.round_index}.second")
    # Drunken results apply only during the Centigor player's current turn.
    if first_state.drunken_result and not state.first_player_turn:
        first_state = replace(first_state, drunken_result=0, stupidity_failed=False, frenzy=first.global_effects.frenzy)
    if second_state.drunken_result and state.first_player_turn:
        second_state = replace(second_state, drunken_result=0, stupidity_failed=False, frenzy=second.global_effects.frenzy)
    if has_tag(first.global_effects, "mechanic.centigor-drunken") and state.first_player_turn:
        roll = dice.roll(RollRequest(f"round.{state.round_index}.first.drunken"))
        first_state = replace(first_state, drunken_result=roll, frenzy=roll == 6, stupidity_failed=False)
    if has_tag(second.global_effects, "mechanic.centigor-drunken") and not state.first_player_turn:
        roll = dice.roll(RollRequest(f"round.{state.round_index}.second.drunken"))
        second_state = replace(second_state, drunken_result=roll, frenzy=roll == 6, stupidity_failed=False)
    for is_first in (True, False):
        current = first_state if is_first else second_state
        fighter = first if is_first else second
        if current.drunken_result in (1, 6):
            tags = (*fighter.global_effects.tags, "mechanic.psychology-immunity")
            if current.drunken_result == 1:
                tags += ("mechanic.stupidity",)
            fighter = replace(fighter, global_effects=replace(fighter.global_effects, tags=tags))
            if is_first:
                first = fighter
            else:
                second = fighter
        # Madness is a this-turn Stupidity, granted to the bearer of the result
        # and to no other Psychology consequence.
        if bool(getattr(current, "bitten_result", 0) == 1):
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "mechanic.stupidity")))
            if is_first:
                first = fighter
            else:
                second = fighter
    # Devoted to the Vampire re-reads the supplied condition of the Lahmian
    # Vampire its recipient follows every combat phase.  Its Frenzy is therefore
    # the only Frenzy that ends by itself: when she stands up, and when her
    # killer dies.  It is never confused with a permanent or rolled Frenzy.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.devoted-to-the-vampire"):
            continue
        current = first_state if is_first else second_state
        killer = second_state if is_first else first_state
        avenging = (has_tag(fighter.global_effects, "condition.devoted-vampire-killed")
                    and killer.condition != Condition.OUT)
        caused = avenging or has_tag(fighter.global_effects, "condition.devoted-vampire-down")
        if caused:
            current = replace(current, frenzy=True, devoted_frenzy=True)
        elif current.devoted_frenzy:
            current = replace(current, frenzy=fighter.global_effects.frenzy, devoted_frenzy=False)
        if avenging:
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "condition.devoted-killer-hatred")))
        if is_first:
            first, first_state = fighter, current
        else:
            second, second_state = fighter, current
    for is_first, fighter in ((True, first), (False, second)):
        current = first_state if is_first else second_state
        failed = False
        if (is_first == state.first_player_turn and current.condition == Condition.STANDING
                and any(has_tag(fighter.global_effects, tag) for tag in ANIMOSITY_SOURCES)):
            label = "first" if is_first else "second"
            # The Fungus Brew's Rowdy result widens the printed own-turn band to
            # 1-2; the ordinary goblin squabble still fails on a 1 only.
            threshold = 2 if has_tag(fighter.global_effects, "mechanic.fungus-rowdy") else 1
            failed = dice.roll(RollRequest(f"round.{state.round_index}.{label}.animosity")) <= threshold
        current = replace(current, animosity_failed=failed)
        if is_first:
            first_state = current
        else:
            second_state = current
    state = resolve_stupidity(first, second, replace(state, first=first_state, second=second_state), dice, decisions)
    first_state, second_state = state.first, state.second
    if not state.engaged:
        return CombatRoundResult(replace(state, round_index=state.round_index + 1), ())
    if first_round:
        state = resolve_fear(first, second, replace(state, first=first_state, second=second_state), dice, decisions)
        first_state, second_state = state.first, state.second
        if not state.engaged:
            return CombatRoundResult(replace(state, round_index=state.round_index + 1), ())
        second_misses, state = resolve_crude_belch(first, second, state, dice, decisions, first=True)
        first_misses, state = resolve_crude_belch(second, first, state, dice, decisions, first=False)
        first_state, second_state = state.first, state.second
    # Both dances act from the same combat-start snapshot; defence remains available.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        owner_state = second_state if target_first else first_state
        blocked = False
        if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.mesmerising-dance")
                and not any(has_tag(target.global_effects, tag) for tag in
                    ("nature.undead", "species.lizardman", "mechanic.charm-immunity"))):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.mesmerising-dance",
                first=target_first, opponent=owner, return_state=True)
            blocked = not passed
        if (has_tag(owner.global_effects, "mechanic.beauty-of-the-sea")
                and has_tag(target.global_effects, "sex.male")
                and not has_tag(target.global_effects, "species.animal")
                and state.initial_charge_flags[int(target_first)]
                and "beauty.passed" not in current.resources_spent
                and current.condition == Condition.STANDING and owner_state.active):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.beauty",
                first=target_first, psychology=True, opponent=owner, return_state=True)
            if passed:
                current = current.spend("beauty.passed")
            else:
                blocked = True
        auto_hit = False
        resource = "mark-of-shornaal.passed"
        if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.mark-of-shornaal")
                and resource not in current.resources_spent
                and not has_tag(target.global_effects, "mechanic.charm-immunity")):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.shornaal",
                first=target_first, psychology=True, discard_lowest=True, opponent=owner, return_state=True)
            if passed:
                current = current.spend(resource)
            else:
                blocked = auto_hit = True
        current = replace(current, charm_attack_blocked=blocked, charm_auto_hit=auto_hit)
        if target_first:
            first_state = current
        else:
            second_state = current
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        owner_state = second_state if target_first else first_state
        owner_label = "second" if target_first else "first"
        if has_tag(owner.global_effects, "mechanic.hypnotist"):
            if current.entranced and decisions.choose(
                    f"round.{state.round_index}.{owner_label}.end-hypnosis", owner):
                current = replace(current, entranced=False)
            if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                    and current.condition == Condition.STANDING and not current.frenzy
                    and not any(has_tag(target.global_effects, tag) for tag in
                        ("nature.undead", "nature.daemon", "mechanic.psychology-immunity", "mechanic.charm-immunity"))
                    and decisions.choose(f"round.{state.round_index}.{owner_label}.hypnotist", target)):
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{owner_label}.hypnotist", first=target_first,
                    opponent=owner, return_state=True)
                current = replace(current, entranced=not passed)
            if target_first:
                first_state = current
            else:
                second_state = current
    # Tranquil Fauna prevents attacks, never the charge or established contact.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        own = second_state if target_first else first_state
        if (own.active and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.taal-tranquil-fauna")
                and has_tag(target.global_effects, "species.animal")):
            conditional = any(has_tag(target.global_effects, tag) for tag in
                ("fauna-animal.handled", "fauna-animal.large-predator"))
            ordinary = has_tag(target.global_effects, "fauna-animal.ordinary") or has_tag(target.global_effects, "species.normal-animal")
            if not conditional and not ordinary:
                raise ValueError("Tranquil Fauna requires the animal's explicit ordinary/handled/large-predator qualification")
            blocked = True
            if conditional:
                if target.animal_handler_leadership is None:
                    raise ValueError("Tranquil Fauna requires the qualified Animal Handler's Leadership")
                # Only the qualified handler's supplied value belongs to this test;
                # do not borrow a nearby leader or the animal's Psychology exemptions.
                passed = phases.resolve_leadership(target.animal_handler_leadership, dice,
                    f"round.{state.round_index}.{'first' if target_first else 'second'}.tranquil-fauna")
                blocked = not passed
            current = replace(current, charm_attack_blocked=current.charm_attack_blocked or blocked)
        if target_first:
            first_state = current
        else:
            second_state = current
    # The Lahmia powers act once per turn, which one combat phase satisfies; the
    # duel has a single opponent, so the printed "may attack another model in
    # base contact" remainder has no second target to name and is recorded
    # rather than simulated.
    hypnotized = [False, False]
    for power, exclusions, name, own_only in LAHMIA_POWERS:
        for target_first in (False, True):
            owner = second if target_first else first
            target = first if target_first else second
            if not has_tag(owner.global_effects, power):
                continue
            current = first_state if target_first else second_state
            owner_state = second_state if target_first else first_state
            label = "first" if target_first else "second"
            if (owner_state.condition != Condition.STANDING or owner_state.stupidity_failed
                    or current.condition != Condition.STANDING):
                continue
            if any(has_tag(target.global_effects, tag) for tag in exclusions):
                continue
            if not decisions.choose(f"round.{state.round_index}.{label}.{name}", target):
                continue
            if own_only:
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{label}.{name}", first=target_first,
                    psychology=True, return_state=True, own_value_only=True, opponent=owner)
            else:
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{label}.{name}", first=target_first,
                    psychology=True, return_state=True)
            if not passed:
                current = replace(current, charm_attack_blocked=True)
                if power == "mechanic.lahmian-hypnotize":
                    # Index 0 is the first participant: the target is first
                    # exactly when it was tested as such.
                    hypnotized[0 if target_first else 1] = True
            # The test's own consumption (a carried relic, a first-failure
            # reroll) must persist on the success path too, so the returned state
            # is stored whether the power passed or failed.
            if target_first:
                first_state = current
            else:
                second_state = current

    def _store(target_is_first, updated):
        """Store one participant's updated state beside its sibling."""
        return ((updated, second_state) if target_is_first
                else (first_state, updated))

    # Hypnotic Gaze and the two Seduction copies.  The gaze bars the target for
    # the phase and makes every attack against it hit automatically; each
    # Seduction establishes a lasting control that the victim's own Recovery
    # phase may end and that the printed attack releases (see the release below
    # the attack resolution).
    for power in CONTROL_POWERS:
        for target_first in (False, True):
            owner = second if target_first else first
            target = first if target_first else second
            if not has_tag(owner.global_effects, power.tag):
                continue
            current = first_state if target_first else second_state
            owner_state = second_state if target_first else first_state
            label = "first" if target_first else "second"
            key = f"round.{state.round_index}.{label}.{power.name}"
            controlled = bool(current.resources_spent.intersection(SEDUCTION_RESOURCES))
            if any(has_tag(target.global_effects, tag) for tag in power.exclusions):
                # The printed exemption also ends a control this clause could not
                # have established on such a model.
                if controlled:
                    current = replace(current, resources_spent=(
                        current.resources_spent - set(SEDUCTION_RESOURCES)))
                first_state, second_state = _store(target_first, current)
                continue
            if controlled:
                if (state.first_player_turn == target_first
                        and current.condition == Condition.STANDING
                        and decisions.choose(f"{key}.regain-control", target)):
                    # Printed Recovery phase: the warrior's own turn offers its
                    # owner the Leadership test that throws the control off.
                    passed, current = resolve_local_leadership(target,
                        replace(state, first=current if target_first else first_state,
                            second=second_state if target_first else current),
                        dice, decisions, f"{key}.regain-control", first=target_first,
                        opponent=owner, return_state=True)
                    if passed:
                        current = replace(current, resources_spent=(
                            current.resources_spent - set(SEDUCTION_RESOURCES)))
                        controlled = False
                if controlled:
                    # A controlled warrior strikes nobody while the control
                    # holds; the printed bar is re-derived here because the charm
                    # flag is reset with each phase.
                    current = replace(current, charm_attack_blocked=True)
            if (owner_state.condition != Condition.STANDING or owner_state.stupidity_failed
                    or current.condition != Condition.STANDING
                    or controlled
                    or (power.own_turn_only
                        and state.first_player_turn != (not target_first))):
                first_state, second_state = _store(target_first, current)
                continue
            if power.male_only:
                # Printed "one male enemy": the fact is supplied, never inferred
                # from the profile or the warband.
                if not any(has_tag(target.global_effects, tag)
                           for tag in ("sex.male", "sex.female")):
                    raise ValueError(
                        "Lahmia Seduction requires the opponent's explicit male/female fact")
                if not has_tag(target.global_effects, "sex.male"):
                    first_state, second_state = _store(target_first, current)
                    continue
            if power.own_test:
                # The Khemrian copy prints the Vampire's own Leadership test
                # before her choice, so a failure leaves the victim alone.
                owner_label = "first" if not target_first else "second"
                passed, owner_state = resolve_local_leadership(owner,
                    replace(state, first=current if target_first else owner_state,
                        second=owner_state if target_first else current),
                    dice, decisions,
                    f"round.{state.round_index}.{owner_label}.{power.name}.own-test",
                    first=not target_first, opponent=target, return_state=True)
                first_state, second_state = (
                    (first_state, owner_state) if target_first
                    else (owner_state, second_state))
                if not passed:
                    continue
            if not decisions.choose(key, target):
                continue
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                key, first=target_first, psychology=True,
                opponent=owner, return_state=True)
            if not passed:
                current = replace(current, charm_attack_blocked=True,
                    charm_auto_hit=current.charm_auto_hit or power.auto_hit)
                if power.persistent:
                    current = replace(current, resources_spent=(
                        current.resources_spent | {CONTROL_RESOURCES[power.tag]}))
            first_state, second_state = _store(target_first, current)
    for index, target in enumerate((first, second)):
        if hypnotized[index]:
            # Every attack directed against the hypnotized model gains +1 To Hit
            # for the rest of that turn.
            tagged = replace(target.global_effects,
                tags=(*target.global_effects.tags, "condition.hypnotized"))
            if index:
                second = replace(second, global_effects=tagged)
            else:
                first = replace(first, global_effects=tagged)
    first_charged, second_charged = state.initial_charge_flags
    first_charging = first_round and first_charged
    second_charging = first_round and second_charged
    # Keep incoming charge provenance separate from the duelist's own charge.
    for side, charged in (("first", second_charging), ("second", first_charging)):
        fighter = first if side == "first" else second
        if charged:
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "condition.being-charged")))
        if side == "first":
            first = fighter
        else:
            second = fighter
    if first_charging and not first_state.charm_attack_blocked:
        second_state = _netter(first, second, first_state, second_state, dice, "round.0.first.netter")
    if second_charging and not second_state.charm_attack_blocked:
        first_state = _netter(second, first, second_state, first_state, dice, "round.0.second.netter")
    # A Wheelo's collision is resolved before crew and enemy weapon blows.
    for owner, target, owner_first, charging in (
            (first, second, True, first_charging), (second, first, False, second_charging)):
        own = first_state if owner_first else second_state
        other = second_state if owner_first else first_state
        counter = (first_round and (second_charging if owner_first else first_charging)
                   and has_tag(owner.global_effects, "wheelo.fitting.spear"))
        if not ((charging or counter) and own.active and other.active and not own.charm_attack_blocked
                and has_tag(owner.global_effects, "mechanic.wheelo-impact")):
            continue
        label = "first" if owner_first else "second"
        count = (dice.roll(RollRequest(f"round.0.{label}.impact-count")) + 1) // 2 if charging else 1
        morning_star = (has_tag(owner.global_effects, "wheelo.fitting.morning-star")
                        and "wheelo.first-impact" not in own.resources_spent)
        own = replace(own, resources_spent=own.resources_spent | {"wheelo.first-impact"})
        collision = replace(owner, global_effects=EffectSet())
        weapon = EffectSet(fixed_strength=5 if morning_star else 4, automatic_hit=True,
            cannot_be_parried=True,
            armour_penetration=int(has_tag(owner.global_effects, "wheelo.fitting.axe")),
            concussion=has_tag(owner.global_effects, "wheelo.fitting.club"))
        from mordheim_combat.modular.aftermath import _react_to_wound
        for index in range(count):
            if not own.active or not other.active:
                break
            key = f"round.0.{label}.impact.{index}"
            result = resolve_reference_attack(collision, target, own, other, weapon, dice,
                key=key, melee_attack=False, decisions=decisions)
            result = _react_to_wound(owner, target, result, dice, key)
            own, other = result.attacker, result.defender
            outcomes.append(result)
        if owner_first:
            first_state, second_state = own, other
        else:
            second_state, first_state = own, other
    # Mantle of Crows (the Crow Master) opens each combat phase: every enemy in
    # base contact - in this 1v1 duel, the single opponent - suffers one
    # automatic Strength 2 hit before any blows are struck, with no to-hit
    # roll. This is a hand-to-hand hit, so contact defences and Thin Flesh
    # apply, but the isolated attacker contributes no personal weapon effects.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        own = second_state if target_first else first_state
        other = first_state if target_first else second_state
        if not (has_tag(owner.global_effects, "mechanic.mantle-of-crows")
                and own.active and other.active):
            continue
        crows = EffectSet(
            tags=("mechanic.mantle-of-crows",),
            fixed_strength=2, automatic_hit=True, cannot_be_parried=True,
        )
        label = "first" if target_first else "second"
        attack_key = f"round.{state.round_index}.{label}.mantle-of-crows"
        # Fixed-strength crows are not the bearer's weapon blows: no personal
        # poison, hit, damage or Strength contribution is inherited.
        crow_attacker = replace(owner, global_effects=EffectSet())
        result = resolve_reference_attack(crow_attacker, target, own, other, crows, dice,
            key=attack_key)
        from mordheim_combat.modular.aftermath import _react_to_wound
        result = _react_to_wound(owner, target, result, dice, attack_key)
        if target_first:
            second_state = result.attacker
            first_state = result.defender
        else:
            first_state = result.attacker
            second_state = result.defender
        outcomes.append(result)
    # Resolve both Spines attacks from one snapshot.  A simultaneous mutation
    # still retaliates when the opposing Spines hit takes it out of action.
    before_first, before_second = first_state, second_state
    _, second_state, first_spines = _spines(
        first, second, before_first, before_second, dice,
        f"round.{state.round_index}.first.spines",
    )
    _, first_state, second_spines = _spines(
        second, first, before_second, before_first, dice,
        f"round.{state.round_index}.second.spines",
    )
    outcomes.extend((*first_spines, *second_spines))
    entangle = EffectSet(
        tags=("effect.chained-squig-entangle",), fixed_strength=3,
        automatic_hit=True,
    )
    if first_state.entangled and second_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            second, first, second_state, first_state, entangle, dice,
            key=f"round.{state.round_index}.first.entangled",
        )
        second_state, first_state = result.attacker, result.defender
        outcomes.append(result)
    if second_state.entangled and first_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            first, second, first_state, second_state, entangle, dice,
            key=f"round.{state.round_index}.second.entangled",
        )
        first_state, second_state = result.attacker, result.defender
        outcomes.append(result)
    first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-spines")
    second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-spines")

    first_attack_fighter = first if first_state.stupidity_failed else select_attack_replacement(
        first, first_round=first_round, charging=first_charging,
        decisions=decisions, key=f"round.{state.round_index}.first",
    )
    second_attack_fighter = second if second_state.stupidity_failed else select_attack_replacement(
        second, first_round=first_round, charging=second_charging,
        decisions=decisions, key=f"round.{state.round_index}.second",
    )
    if has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        first_state = replace(first_state, parries_remaining=0)
    if has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        second_state = replace(second_state, parries_remaining=0)
    first_priority = phases.resolve_priority(PriorityContext(
        first_attack_fighter, second, first_round, first_charging, second_charging, first_stood,
        first_state.initiative_penalty,
        initiative_bonus=first_state.initiative - first.characteristics.initiative,
        initiative_floor=first_state.initiative_floor,
    ))
    second_priority = phases.resolve_priority(PriorityContext(
        second_attack_fighter, first, first_round, second_charging, first_charging, second_stood,
        second_state.initiative_penalty,
        initiative_bonus=second_state.initiative - second.characteristics.initiative,
        initiative_floor=second_state.initiative_floor,
    ))
    first_acts = phases.first_acts_before(
        first_priority, second_priority, dice, key=f"round.{state.round_index}.priority-tie",
    )

    first_count = phases.build_attacks(AttackPoolContext(
        first_attack_fighter, first_round, first_charging, second_charging,
        first_state.frenzy, first_state.wounds < first.characteristics.wounds,
        0, first_state.attacks, state.first_player_turn,
    )).attacks
    second_count = phases.build_attacks(AttackPoolContext(
        second_attack_fighter, first_round, second_charging, first_charging,
        second_state.frenzy, second_state.wounds < second.characteristics.wounds,
        0, second_state.attacks, not state.first_player_turn,
    )).attacks
    first_count = resolve_spawn_attack_count(
        first_attack_fighter, first_count, dice, f"round.{state.round_index}.first.spawn-attacks"
    )
    second_count = resolve_spawn_attack_count(
        second_attack_fighter, second_count, dice, f"round.{state.round_index}.second.spawn-attacks"
    )
    first_shifty = (first_round and second_charging and has_tag(first.global_effects, "skill.shifty")
        and not has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    second_shifty = (first_round and first_charging and has_tag(second.global_effects, "skill.shifty")
        and not has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    # Add after Frenzy, before whole-warrior attack reductions. Split off only
    # this one attack below; ordinary attacks retain their original priority.
    if first_shifty and not (has_tag(first_attack_fighter.main_weapon, "weapon.fist")
            and not phases.ignores_unarmed_penalties(first.global_effects)):
        first_count += 1
    if second_shifty and not (has_tag(second_attack_fighter.main_weapon, "weapon.fist")
            and not phases.ignores_unarmed_penalties(second.global_effects)):
        second_count += 1
    first_count = apply_round_weapon_attack_modifiers(
        first, second, first_count, first_round=first_round,
        charging=first_charging, charged=second_charging,
    )
    second_count = apply_round_weapon_attack_modifiers(
        second, first, second_count, first_round=first_round,
        charging=second_charging, charged=first_charging,
    )
    first_count = apply_opponent_attack_modifiers(
        first, second, first_count, first_round=first_round, defer_grapple=True)
    second_count = apply_opponent_attack_modifiers(
        second, first, second_count, first_round=first_round, defer_grapple=True)
    if first_state.on_fire or first_state.animosity_failed or first_state.stupidity_failed or first_state.charm_attack_blocked or first_state.condition != Condition.STANDING:
        first_count = 0
    if second_state.on_fire or second_state.animosity_failed or second_state.stupidity_failed or second_state.charm_attack_blocked or second_state.condition != Condition.STANDING:
        second_count = 0
    first_shifty = first_shifty and first_count > 0
    second_shifty = second_shifty and second_count > 0
    # The Priest's bite is its own final event, after both warriors' weapon
    # attacks. Ordinary pools exclude this separately scheduled contribution.
    last_attacks = []
    for attacker, defender, is_first, count, label in (
        (first_attack_fighter, second, True, first_count, 'first'),
        (second_attack_fighter, first, False, second_count, 'second'),
    ):
        if count > 0:
            for weapon in attacker.extra_attacks:
                if has_tag(weapon, 'rule.strikes-last-bite'):
                    bite = replace(attacker, main_weapon=weapon, off_hand=None,
                        off_hand_attacks=False, extra_attacks=(), main_hand_slot='natural',
                        main_weapon_without_poison=None, off_hand_without_poison=None)
                    current = first_state if is_first else second_state
                    initiative = max(current.initiative_floor,
                        current.initiative + attacker.global_effects.initiative_bonus
                        - current.initiative_penalty)
                    last_attacks.append((bite, defender, is_first, 1,
                        phases.PriorityResult(-2, initiative), f'{label}.last-bite'))
    events = [
        (first_attack_fighter, second, True, first_count - int(first_shifty), first_priority, 'first'),
        (second_attack_fighter, first, False, second_count - int(second_shifty), second_priority, 'second'),
    ]
    if not first_acts:
        events.reverse()
    # A charged whip's bonus has its own Strike First timing. Its ordinary
    # attacks retain their own priority and cannot borrow that bonus's tier.
    for owner, charged in ((True, second_charging), (False, first_charging)):
        for index, event in enumerate(events):
            attacker, defender, is_first, count, priority, label = event
            whip = whipcrack_weapon(attacker)
            if is_first != owner or not charged or not count or whip is None:
                continue
            events[index] = (*event[:3], count - 1, priority, label)
            bonus_fighter = replace(attacker, main_weapon=whip, off_hand=None,
                off_hand_attacks=False, extra_attacks=(), main_hand_slot=(
                    attacker.main_hand_slot if whip == attacker.main_weapon else attacker.off_hand_slot))
            bonus_priority = phases.PriorityResult(1, priority.initiative)
            bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.whipcrack')
            position = len(events)
            for candidate_index, candidate in enumerate(events):
                if phases.first_acts_before(bonus_priority, candidate[4], dice,
                        key=f'round.{state.round_index}.{label}.whip-priority-tie'):
                    position = candidate_index
                    break
            events.insert(position, bonus)
            break
    # Ties belong to the two warriors at a given tier/Initiative, not to every
    # event. Reuse the ordinary tie when their bonus attacks share that tier.
    ties = {first_priority: first_acts} if first_priority == second_priority else {}
    for attacker, defender, is_first, active, stood, fighter_state in (
        (first, second, True, first_shifty, first_stood, first_state),
        (second, first, False, second_shifty, second_stood, second_state),
    ):
        if not active:
            continue
        label = 'first' if is_first else 'second'
        bonus_fighter = select_shifty_weapon(attacker, decisions, key=f"round.{state.round_index}.{label}.shifty")
        bonus_priority = resolve_priority(PriorityContext(
            bonus_fighter, defender, first_round, first_charging if is_first else second_charging,
            second_charging if is_first else first_charging, stood, fighter_state.initiative_penalty,
            initiative_bonus=fighter_state.initiative - attacker.characteristics.initiative,
            initiative_floor=fighter_state.initiative_floor,
        ))
        if bonus_priority.priority >= 0:
            bonus_priority = replace(bonus_priority, priority=max(1, bonus_priority.priority))
        bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.shifty')
        position = len(events)
        for index, candidate in enumerate(events):
            candidate_priority = candidate[4]
            if bonus_priority == candidate_priority:
                if candidate[2] == is_first:
                    before = True
                else:
                    if bonus_priority not in ties:
                        # Whipcrack may already have resolved this exact tie.
                        peer = next((i for i, event in enumerate(events)
                            if event[2] == is_first and event[4] == bonus_priority), None)
                        winner = (peer < index if peer is not None else
                            first_acts_before(bonus_priority, candidate_priority, dice,
                                key=f"round.{state.round_index}.{label}.shifty-priority-tie"))
                        ties[bonus_priority] = winner if is_first else not winner
                    before = ties[bonus_priority] == is_first
            else:
                before = (bonus_priority.priority, bonus_priority.initiative) > (
                    candidate_priority.priority, candidate_priority.initiative)
            if before:
                position = index
                break
        events.insert(position, bonus)
    # Eagles are separate Strike First weapon contributions directed by their
    # Priestess, not independent combatants or extra copies of her hand weapon.
    for attacker, defender, is_first, count in (
            (first, second, True, first_count), (second, first, False, second_count)):
        if count <= 0 or any(has_tag(defender.global_effects, tag) for tag in
                ("mechanic.taal-tranquil-fauna", "mechanic.animal-friendship", "animal_friendship")):
            continue
        current = first_state if is_first else second_state
        priority = phases.PriorityResult(1, max(current.initiative_floor,
            current.initiative + attacker.global_effects.initiative_bonus - current.initiative_penalty))
        for bird_index, weapon in enumerate(weapon for weapon in attacker.extra_attacks
                                           if has_tag(weapon, "rule.eagle-friend")):
            eagle = replace(attacker, main_weapon=weapon, off_hand=None, off_hand_attacks=False,
                extra_attacks=(), main_hand_slot='companion', main_weapon_without_poison=None,
                off_hand_without_poison=None)
            label = f"{'first' if is_first else 'second'}.eagle.{bird_index}"
            position = len(events)
            for index, candidate in enumerate(events):
                if priority == candidate[4]:
                    if candidate[2] == is_first:
                        before = True
                    else:
                        if priority not in ties:
                            winner = first_acts_before(priority, candidate[4], dice,
                                key=f"round.{state.round_index}.eagle-priority-tie")
                            ties[priority] = winner if is_first else not winner
                        before = ties[priority] == is_first
                else:
                    before = (priority.priority, priority.initiative) > (candidate[4].priority, candidate[4].initiative)
                if before:
                    position = index
                    break
            events.insert(position, (eagle, defender, is_first, 1, priority, label))
    if len(last_attacks) == 2 and not first_acts_before(
            last_attacks[0][4], last_attacks[1][4], dice,
            key=f'round.{state.round_index}.last-bite-priority-tie'):
        last_attacks.reverse()
    events.extend(last_attacks)
    already_attacked = {True: False, False: False}
    # Seduction's printed release reads the round's own attacks: while a control
    # holds, its victim cannot strike, so the attack that can end it is the
    # Vampire's (see the release below the attack resolution).
    control_attacked = {True: False, False: False}
    control_hits = {True: False, False: False}
    for event_index, (attacker, defender, is_first, count, _, label) in enumerate(events):
        current = first_state if is_first else second_state
        if current.hillman_wolf:
            source = original_first if is_first else original_second
            attacker = equipment_for_state(source, current, first_round=first_round)
            count = current.attacks
            defender = second if is_first else first
        opposing = second_state if is_first else first_state
        if opposing.hillman_wolf:
            defender = equipment_for_state(original_second if is_first else original_first,
                opposing, first_round=first_round)
        initial = before_first if is_first else before_second
        if (label in ('first', 'second') and (first_shifty if is_first else second_shifty)
                and current.broken_hands != initial.broken_hands):
            # Trap Blade can break the bonus's weapon before the ordinary hit
            # rolls exist. Those later attacks must use the surviving equipment.
            source = original_first if is_first else original_second
            usable = equipment_for_state(replace(source, global_effects=attacker.global_effects),
                current, first_round=first_round)
            count = max(0, count - int(attacker.off_hand_attacks and not usable.off_hand_attacks))
            if has_tag(usable.main_weapon, 'weapon.fist') and not phases.ignores_unarmed_penalties(usable.global_effects):
                count = min(count, 1)
            attacker = usable
        # Kusara's minimum belongs to the warrior's whole phase, including
        # separately timed Whipcrack attacks. Consume each suppression once.
        other_attacks = already_attacked[is_first] or any(
            event[2] == is_first and event[3] > 0 for event in events[event_index + 1:])
        minimum_attacks = 0 if other_attacks else 1
        if is_first:
            first_state, second_state, resolved = _resolve_attack_pool(
                attacker, defender, first_state, second_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=first_charging, decisions=decisions,
                defender_condition_at_start=before_second.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith(('.shifty', '.last-bite')) or '.eagle.' in label,
                miss_first_attack=first_misses,
            )
        else:
            second_state, first_state, resolved = _resolve_attack_pool(
                attacker, defender, second_state, first_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=second_charging, decisions=decisions,
                defender_condition_at_start=before_first.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith(('.shifty', '.last-bite')) or '.eagle.' in label,
                miss_first_attack=second_misses,
            )
        if resolved:
            if is_first: first_misses = False
            else: second_misses = False
            control_attacked[is_first] = True
            control_hits[is_first] = control_hits[is_first] or any(
                outcome.hit for outcome in resolved)
        already_attacked[is_first] = already_attacked[is_first] or bool(resolved)
        outcomes.extend(resolved)
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-attack")
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-attack")

    first_state, backlash = _black_hunger(first, first_state, dice, f"round.{state.round_index}.first.black-hunger")
    outcomes.extend(backlash)
    first_state = _force_of_will(
        first, first_state, dice, f"round.{state.round_index}.first.force.after-black-hunger"
    )
    second_state, backlash = _black_hunger(second, second_state, dice, f"round.{state.round_index}.second.black-hunger")
    outcomes.extend(backlash)
    second_state = _force_of_will(
        second, second_state, dice, f"round.{state.round_index}.second.force.after-black-hunger"
    )
    # Seduction's printed release.  The Khemrian copy ends the control when the
    # Vampire attacks her victim at all; the Lahmia copy only when an attack
    # hits.  A control that was not attacked survives into the next phase, where
    # the victim's own Recovery-phase test may still throw it off.
    for target_first in (True, False):
        current = first_state if target_first else second_state
        held = current.resources_spent.intersection(SEDUCTION_RESOURCES)
        if not held or not control_attacked[not target_first]:
            continue
        if control_hits[not target_first] or LAHMIA_SEDUCTION_RESOURCE not in held:
            current = replace(current, resources_spent=(
                current.resources_spent - set(SEDUCTION_RESOURCES)))
            if target_first:
                first_state = current
            else:
                second_state = current
    trace = tuple(dict.fromkeys((
        *(state.trace if state.round_index == 0 else ()), Phase.PRIORITY, Phase.ATTACKS,
        *(phase for outcome in outcomes for phase in outcome.trace), Phase.AFTERMATH,
    )))
    return CombatRoundResult(
        replace(state, first=first_state, second=second_state,
                round_index=state.round_index + 1, trace=trace),
        tuple(outcomes),
    )


def apply_opponent_leadership(
    fighter: CompiledFighter, opponent: CompiledFighter, state: DuelState,
) -> CompiledFighter:
    """Apply the Leadership facts an opponent supplies to this fighter.

    Questing Vow qualifies all local Leadership tests against a Fear-causer, and
    Enchanting Beauty drops the Leadership of a *living* contacting enemy.  The
    printed clause exempts Undead and Daemons and names nothing else, so a
    Possessed, Chaos-mutated or otherwise non-living-typed mortal is still
    affected; only those two natures keep the source's exemption.
    """
    effect = fighter.global_effects
    if (has_tag(opponent.global_effects, "mechanic.enchanting-beauty")
            and not any(has_tag(effect, tag) for tag in ("nature.undead", "nature.daemon"))):
        effect = replace(effect, tags=(*effect.tags, "condition.enchanting-beauty"))
    if (has_tag(effect, "mechanic.questing-vow")
            and (state.engaged or any(state.initial_charge_flags))
            and causes_fear(opponent, fighter)):
        effect = replace(effect, tags=(*effect.tags, "mechanic.leadership-reroll"))
    if effect is fighter.global_effects:
        return fighter
    return replace(fighter, global_effects=effect)


def select_shifty_weapon(
    fighter: CompiledFighter, decisions: DecisionPolicy, *, key: str,
) -> CompiledFighter:
    """Project one nominated melee attack, preserving its original hand slot.

    Mixed kits retain their melee nomination. The F005 user ruling permits a
    pistol-only bonus as a separate strike in addition to the ordinary pistol pool.
    """
    weapon, clean, slot = fighter.main_weapon, fighter.main_weapon_without_poison, fighter.main_hand_slot
    off = fighter.off_hand if fighter.off_hand_attacks else None
    if off is not None and not is_pistol(off) and (
        is_pistol(weapon) or (off != weapon and not decisions.choose(f'{key}.main-weapon', fighter))
    ):
        weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    elif is_pistol(weapon) and off is not None and off != weapon:
        if not decisions.choose(f'{key}.main-weapon', fighter):
            weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    return replace(fighter, main_weapon=weapon, main_weapon_without_poison=clean,
        main_hand_slot=slot, off_hand=None, off_hand_without_poison=None,
        off_hand_attacks=False, extra_attacks=())


def select_attack_replacement(
    fighter: CompiledFighter, *, first_round: bool, charging: bool,
    decisions: DecisionPolicy, key: str,
) -> CompiledFighter:
    """Apply optional whole-pool replacements before attack count and resolution."""
    if (has_tag(fighter.global_effects, "mechanic.wraith-touch")
            and decisions.choose(f"{key}.wraith-touch", fighter)):
        return replace(fighter, main_weapon=EffectSet(
            tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"),
            strength_bonus=-1, target_armour_bonus=1),
            main_weapon_without_poison=None, off_hand=None, off_hand_without_poison=None,
            off_hand_attacks=False, extra_attacks=())
    if fighter.vomit_attack is not None and decisions.choose(f"{key}.vomit-attack", fighter):
        return replace(fighter, main_weapon=fighter.vomit_attack,
            main_weapon_without_poison=None, off_hand=None, off_hand_without_poison=None,
            off_hand_attacks=False, extra_attacks=())
    if (has_tag(fighter.main_weapon, "weapon.serpent-staff")
            and decisions.choose(f"{key}.serpent-staff", fighter)):
        return replace(fighter, main_weapon=EffectSet(
            tags=("effect.serpent-staff-power",), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    removable = []
    if (has_tag(fighter.global_effects, "mechanic.anvil-head")
            and first_round and charging
            and not decisions.choose(f"{key}.anvil-head", fighter)):
        removable.append("mechanic.anvil-head")
    if (has_tag(fighter.global_effects, "mechanic.death-blow")
            and fighter.characteristics.attacks >= 2
            and not decisions.choose(f"{key}.death-blow", fighter)):
        removable.append("mechanic.death-blow")
    if not removable:
        return fighter
    effects = replace(
        fighter.global_effects,
        tags=tuple(tag for tag in fighter.global_effects.tags if tag not in removable),
    )
    return replace(fighter, global_effects=effects)


def resolve_crude_belch(owner, enemy, state, dice, decisions, *, first: bool):
    """Return the duel enemy's timed first-attack loss, separate from count clamps."""
    if not has_tag(owner.global_effects, "skill.crude-belch-halfling"):
        return False, state
    owner_state = state.first if first else state.second
    enemy_state = state.second if first else state.first
    if owner_state.condition != Condition.STANDING or not enemy_state.active:
        return False, state
    context = state.context
    if context is not None:
        own_id = context.facts.first_id if first else context.facts.second_id
        enemy_id = context.facts.second_id if first else context.facts.first_id
        contacts = context.facts.contacts
        # The duel has two mutable combat states. Do not silently omit another
        # supplied enemy that the printed area effect must also affect.
        own_side = context.participant(own_id).side_id
        if any(own_id in pair and context.participant(next(pid for pid in pair if pid != own_id)).side_id != own_side
               and enemy_id not in pair for pair in contacts or ()):
            raise ValueError("Crude Belch additional enemy contacts require multi-participant resolution")
        if contacts is not None and not any({a, b} == {own_id, enemy_id} for a, b in contacts):
            return False, state
    key = f"round.{state.round_index}.{'first' if first else 'second'}.crude-belch"
    if not decisions.choose(key, owner):
        return False, state
    passed, current = resolve_local_leadership(
        enemy, state, dice, decisions, key + '.leadership', first=not first,
        opponent=owner, return_state=True)
    return not passed, replace(state, **{"second" if first else "first": current})


def resolve_spawn_attack_count(
    fighter: CompiledFighter, ordinary_count: int, dice: DiceSource, key: str,
) -> int:
    if has_tag(fighter.main_weapon, "weapon.vomit-attack"):
        return ordinary_count
    if phases.has_tag(fighter.global_effects, "mechanic.spawn-special-attacks"):
        return dice.roll(RollRequest(key)) + 1
    return ordinary_count


def apply_opponent_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *, first_round: bool,
    defer_grapple: bool = False,
) -> int:
    if not count:
        return 0
    if (
        (phases.has_tag(defender.global_effects, "animal_friendship")
         or phases.has_tag(defender.global_effects, "mechanic.animal-friendship"))
        and phases.has_tag(attacker.global_effects, "species.normal-animal")
    ):
        return 0
    if (
        first_round
        and phases.has_tag(defender.global_effects, "skill.sigmar-s-sign")
        and phases.has_tag(attacker.global_effects, "undead_or_possessed")
        and not phases.has_tag(attacker.global_effects, "nature.daemon")
    ):
        count = max(1, count - 1)
    modifier = defender.global_effects.incoming_attacks_modifier
    if defer_grapple and modifier < 0 and has_tag(defender.global_effects, "rule.tentacle-grapple"):
        # Keep Tentacle's one optional loss for the allocated pool; other
        # incoming reductions retain their usual count/floor semantics.
        modifier += 1
    return max(1, count + modifier)


def apply_round_weapon_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *,
    first_round: bool, charging: bool, charged: bool,
) -> int:
    """Apply weapon rules that change the pool because either fighter charged."""
    if not count or not first_round:
        return count
    if whipcrack_weapon(attacker) is not None and (charging or charged):
        count += 1
    if phases.has_tag(defender.main_weapon, "weapon.boar-spear") and charging:
        count = max(1, count - 1)
    return count
