"""combat: Prepared per-attack contexts shared by orchestration and verification."""
from __future__ import annotations
from mordheim_combat import phases

from mordheim_combat.modular.state import FighterState, _parry_capacity
from mordheim_combat.phases import ArmourContext
from mordheim_combat.phases import HitContext
from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import ParryContext
from mordheim_combat.phases import SpecialSaveContext
from mordheim_combat.phases import WoundContext
from mordheim_combat.phases import has_tag
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.dice import RollRequest


class OwnedRollDice:
    """Offer personal once-per-battle choices at an explicitly owned roll site."""

    def __init__(self, dice, fighter, state, decisions=None, *, modifiable=True,
                 close_combat=False):
        self.dice, self.fighter, self.state = dice, fighter, state
        self.decisions, self.modifiable = decisions, modifiable
        # Explicit combat scope: True only where the call site is resolving a
        # close-combat melee action (attack resolution and its melee wound
        # rolls).  Initialisation, preparations, recovery and post-battle
        # bookkeeping construct this wrapper without it, so ownership or being
        # inside a duel alone never authorises a reroll rule.
        self.close_combat = close_combat
        self.original_roll = None
        self.rerolled = False
        self._rerolled_results = {}

    def roll(self, request):
        if request.key in self._rerolled_results:
            self.rerolled = True
            return self._rerolled_results[request.key]
        self.rerolled = False
        value = self.dice.roll(request)
        self.original_roll = value
        if self.decisions is None:
            return value
        effects = self.fighter.global_effects
        if (self.modifiable and has_tag(effects, "mechanic.ranalds-luck")
                and "ranalds-luck" not in self.state.resources_spent):
            context = (self.fighter, request, value)
            if self.decisions.choose(f"{request.key}.ranalds-luck.plus", context):
                value += 1
                self.state = self.state.spend("ranalds-luck")
            elif self.decisions.choose(f"{request.key}.ranalds-luck.minus", context):
                value -= 1
                self.state = self.state.spend("ranalds-luck")
        if (any(has_tag(effects, tag) for tag in
                ("mechanic.oracle", "mechanic.augur-one-roll-reroll"))
                and "one-roll-reroll" not in self.state.resources_spent
                and ".reroll" not in request.key
                and self.decisions.choose(f"{request.key}.one-roll-reroll",
                                          (self.fighter, request, value))):
            self.state = self.state.spend("one-roll-reroll")
            value = self.dice.roll(RollRequest(f"{request.key}.reroll", request.sides))
            self.original_roll = value
            self.rerolled = True
            self._rerolled_results[f"{request.key}.reroll"] = value
        if (has_tag(effects, 'skill.luck') and 'luck' not in self.state.resources_spent
                and not self.rerolled and '.reroll' not in request.key
                and self.decisions.choose(f'{request.key}.luck', (self.fighter, request, value))):
            self.state = self.state.spend('luck')
            value = self.dice.roll(RollRequest(f'{request.key}.reroll', request.sides))
            self.original_roll = value
            self.rerolled = True
            self._rerolled_results[f'{request.key}.reroll'] = value
        # Scryer (Private Sleuth, watchmen-mim): "A Sleuth can re-roll any rolls
        # in close combat (the second result must be accepted)".  These dice are
        # already owned by the roller, so an enemy die is never touched.  The
        # player chooses per roll and the second result stands, so a roll
        # already re-rolled (its key carries .reroll or self.rerolled is set)
        # is not re-rolled again, and the rule grants no per-battle or per-round
        # resource, hence nothing is spent.  Exploration is out of scope here.
        if (self.close_combat and self.modifiable and has_tag(effects, "mechanic.scryer")
                and not self.rerolled and '.reroll' not in request.key
                and self.decisions.choose(f"{request.key}.scryer",
                                          (self.fighter, request, value))):
            value = self.dice.roll(RollRequest(f"{request.key}.scryer.reroll", request.sides))
            self.original_roll = value
            self.rerolled = True
            self._rerolled_results[f"{request.key}.scryer.reroll"] = value
            # Ordinary hit/wound/save rerolls must accept this second result
            # too, rather than rolling the same die again under their key.
            self._rerolled_results[f"{request.key}.reroll"] = value
        return value

    def unmodifiable(self, request):
        previous = self.modifiable
        self.modifiable = False
        try:
            return self.roll(request)
        finally:
            self.modifiable = previous


def _combined_effect(fighter: CompiledFighter, weapon: EffectSet) -> EffectSet:
    return weapon if any(has_tag(weapon, tag) for tag in (
        "mechanic.body-slam", "mechanic.giggle-juice-spray-attack",
        "mechanic.electrical-touch-attack")) else merge_effects(weapon, fighter.global_effects)


def weapon_against_opponent(attacker: CompiledFighter, defender: CompiledFighter,
                            weapon: EffectSet) -> EffectSet:
    """Select the poison-free contribution before adding transient attack effects."""
    if not (defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")):
        return weapon
    if weapon == attacker.main_weapon and attacker.main_weapon_without_poison is not None:
        return attacker.main_weapon_without_poison
    if weapon == attacker.off_hand and attacker.off_hand_without_poison is not None:
        return attacker.off_hand_without_poison
    for poisoned, clean in attacker.extra_attacks_without_poison:
        if weapon == poisoned:
            return clean
    return weapon


def _attack_strength(
    attacker: CompiledFighter, defender: CompiledFighter,
    state: FighterState, weapon: EffectSet, effect: EffectSet,
    first_round: bool, charging: bool, *, melee_attack: bool = True,
) -> tuple[int, int]:
    strength = effect.fixed_strength or state.strength + effect.strength_bonus
    if phases.ignores_unarmed_penalties(effect) and phases.has_tag(weapon, "weapon.fist"):
        strength += 1
    if phases.has_tag(effect, "mechanic.energy-focus") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        strength += effect.energy_focus_attacks
    retains = phases.has_tag(effect, "mechanic.retain-flail-morning-star-strength-bonus") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.flail", "weapon.morning-star")
    )
    if first_round or phases.has_tag(effect, "skill.tireless") or phases.has_tag(effect, "skill.mighty-biceps") or retains:
        strength += weapon.first_round_strength_bonus
    if first_round and phases.has_tag(weapon, "weapon.spear") and phases.has_tag(effect, "mechanic.seaguard-spear-master"):
        strength += 1
    if first_round and charging:
        mounted_only = any(phases.has_tag(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength += effect.charge_strength_bonus
    if (melee_attack and first_round and charging
            and has_tag(attacker.global_effects, "rule.slay-large-creature")
            and has_tag(defender.global_effects, "size.large")):
        strength += 1
    if (has_tag(defender.global_effects, "mechanic.foul-odour")
            and has_tag(effect, "attack.fire")):
        strength += 1
    if phases.has_tag(weapon, "rule.eagle-friend"):
        strength = 3  # Directed bird weapon: never the Priestess's personal Strength bonuses.
    if any(has_tag(weapon, tag) for tag in ('rule.scorpion-tail', 'rule.poisonous-bite')):
        strength = 2 if (defender.global_effects.poison_immunity
            or has_tag(defender.global_effects, 'poison_immune')) else 5
    armour_strength = strength + effect.armour_strength_modifier
    if phases.has_tag(effect, "mechanic.wolf-rat-bite"):
        # Its printed S4 wounds normally but contributes no armour modifier.
        strength = 4
        armour_strength = 3
    strength = max(1, strength + defender.global_effects.incoming_strength_modifier)
    return strength, armour_strength


def vengeful_enmity_target(effect: EffectSet, enemy_tags: tuple[str, ...]) -> bool:
    """Bitter Enmity's supplied relationship target, read on the enemy's identity.

    The serious injury prints four kinds of hated enemy, and the campaign supplies
    the concrete identity the further D6 determined.  Three kinds name an
    instance: the warrior who caused the injury, that same warrior as its
    warband's leader, or the warband instance it belongs to.  Those are the
    caller's own supplied keys -- ``instance_id`` and ``warband_instance`` -- and
    never a catalogue profile or band, so two warriors of one profile and two
    rosters built from one catalogue list stay distinct.  Only the fourth kind,
    every warband of a type, is a category, read on the opponent's compiled
    warband group.  No kind matches every enemy, a missing or unsupplied target
    never grants the reroll. The leader kind names the individual determined
    when the injury occurred; permanent Hatred does not require that individual
    to retain the Leader rule, nor transfer to a replacement leader.
    """
    marker = next((tag for tag in effect.tags if tag.startswith("enmity-target.")), None)
    if marker is None:
        return False
    # Only the two leading separators split; a supplied instance key may be dotted.
    kind, _, target = marker.partition(".")[2].partition(".")
    if not target:
        return False
    if kind == "individual":
        return f"instance.{target}" in enemy_tags
    if kind == "leader":
        return f"instance.{target}" in enemy_tags
    if kind == "warband":
        return f"warband-instance.{target}" in enemy_tags
    if kind == "warband-type":
        return f"warband-group.{target}" in enemy_tags
    return False


def _hit_reroll(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
    effect: EffectSet, first_round: bool, charging: bool, *, frenzy: bool = False,
) -> bool:
    pride = False
    if first_round and has_tag(effect, "mechanic.dueling-pride"):
        if not any(tag.startswith("house-guard.") for tag in effect.tags):
            raise ValueError("Dueling Pride requires an explicit House Guard house")
        if has_tag(effect, "house-guard.fierezza") and has_tag(effect, "fighter-kind.hero"):
            if not any(tag.startswith("fighter-kind.") for tag in defender.global_effects.tags):
                raise ValueError("Dueling Pride requires the opponent's explicit fighter role")
            pride = has_tag(defender.global_effects, "fighter-kind.hero")
    enemy_tags = defender.global_effects.tags
    amazon_enemy = any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in enemy_tags
    )
    kindred = False
    if first_round and not frenzy and has_tag(effect, "mechanic.kindred-hatred") and "species.vampire" in enemy_tags:
        bloodlines = [tag for tag in enemy_tags if tag.startswith("vampire-bloodline.")]
        if len(bloodlines) != 1:
            raise ValueError("Kindred Hatred requires the opposing Vampire's explicit bloodline")
        kindred = bloodlines[0] != "vampire-bloodline.strigoi"
    # A printed grant carried by the defender: the clause belongs to this
    # fighter's profile and gives a qualifying attacker the first-round reroll
    # against her.  The source's express grant to all Vampires is retained even
    # though they are ordinarily immune to psychology, exactly like Kindred
    # Hatred, and no other Undead receives it.
    imposed_hatred = (
        first_round
        and has_tag(defender.global_effects, "mechanic.fighting-undead")
        and "species.vampire" in attacker.global_effects.tags
    )
    psychology_allowed = not frenzy and not phases.has_tag(attacker.global_effects, "mechanic.psychology-immunity")
    hatred = first_round and psychology_allowed and (
        phases.has_tag(effect, "skill.hatred")
        or has_tag(effect, "mechanic.burn-the-witch") and "identity.spellcaster" in enemy_tags
        or has_tag(effect, "mechanic.hang-the-bandit") and "warband-group.bandit" in enemy_tags
        or has_tag(effect, "mechanic.profound-hatred") and not bool(
            {"band.sisters-of-sigmar", "band.trollheim-sisters-of-sigmar"}.intersection(enemy_tags))
        or has_tag(defender.global_effects, "mechanic.greenskin-traitor")
        and bool({"species.orc", "species.goblin", "species.black-orc"}.intersection(
            attacker.global_effects.tags))
        or has_tag(effect, "skill.righteous-fury") and (
            bool({"species.skaven", "nature.undead", "nature.possessed",
                  "species.beastman", "species.dark-elf"}.intersection(enemy_tags))
            or "warband-group.chaotic" in enemy_tags
            or "identity.chaos-follower" in enemy_tags
            or "warband-group.evil" in enemy_tags and not bool(
                {"warband-group.human", "warband-group.human-mercenary"}.intersection(enemy_tags))
        )
        or has_tag(effect, "mechanic.noble-disdain") and "condition.ranged-armed" in enemy_tags
        or has_tag(effect, "mechanic.hatred-human-warband") and bool(
            {"warband-group.human", "warband-group.human-mercenary", "warband-group.chaos-human"}.intersection(enemy_tags))
        or has_tag(effect, "mechanic.ulric-intense-rivals") and "identity.ulric-rival" in enemy_tags
        or has_tag(effect, "mechanic.hatred-chaotic-warband") and "warband-group.chaotic" in enemy_tags
        or has_tag(effect, "mechanic.gaoler-hatred") and bool({
            "warband-group.skaven", "warband-group.beastmen", "warband-group.undead",
            "band.cult-of-the-possessed", "band.trollheim-cult-of-the-possessed",
            "band.carnival-of-chaos"}.intersection(enemy_tags))
        # Fanatical: the eleven warband categories the source prints, each read on the
        # opponent's own canonical identity.  Middenheimers are the Mercenary variant,
        # and no species-only identity stands in for a named category.
        or has_tag(effect, "mechanic.fanatical-hatred") and bool({
            "warband-group.orcs-and-goblins", "band.black-orcs", "band.forest-goblins",
            "band.forest-goblins-lus", "band.horned-hunters", "band.sisters-of-sigmar",
            "mercenary-origin.middenheim", "warband-group.skaven", "warband-group.undead",
            "warband-group.beastmen", "band.cult-of-the-possessed",
            "band.trollheim-cult-of-the-possessed",
            "band.carnival-of-chaos"}.intersection(enemy_tags))
        or has_tag(effect, "mechanic.man-hater") and {"species.human", "sex.male"}.issubset(enemy_tags)
        or "identity.greenskin" in enemy_tags and any(has_tag(effect, tag) for tag in (
            "mechanic.hatred-orcs-goblins", "mechanic.hatred-skaven-orcs-goblins"))
        or any(has_tag(effect, tag) and any(f"species.{species}" in enemy_tags for species in targets)
            for tag, targets in (("mechanic.hatred-orcs-goblins", ("orc", "goblin")),
                                 ("mechanic.hatred-skaven", ("skaven",)),
                                 ("mechanic.hatred-dwarfs", ("dwarf",)),
                                 ("mechanic.hatred-skaven-orcs-goblins", ("skaven", "orc", "goblin")),
                                 ("mechanic.hatred-dwarfs-skaven", ("dwarf", "skaven"))))
        or has_tag(effect, "mechanic.despise-despoilers") and "identity.necromancer" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-undead") and "nature.undead" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-beastmen") and "species.beastman" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-dark-elves") and "species.dark-elf" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-high-elves") and "species.high-elf" in enemy_tags
        # Vengeful Hatred (Bitter Enmity): the campaign's further D6 and the printed
        # selector supply one concrete hated enemy, never a category of convenience.
        or has_tag(effect, "mechanic.vengeful-hatred") and vengeful_enmity_target(effect, enemy_tags)
        # Free the Slaves!: the hated group is the opponent's own slaver identity, so belonging to a
        # slave-taking warband is not by itself enough, and a slaver identity that is not printed
        # leaves ordinary combat.
        or phases.has_tag(effect, "mechanic.hatred-slavers") and "identity.slaver" in enemy_tags
        or phases.has_tag(effect, "mechanic.amazon-isolationists") and amazon_enemy
    )
    return bool(
        effect.reroll_hits
        or pride
        or first_round and has_tag(effect, "mechanic.pikewall")
        and has_tag(effect, "condition.being-charged") and weapon.priority > 0
        or charging and effect.charge_reroll_hits
        or charging and phases.has_tag(effect, "rule.berserk-charge") and (
            any(phases.has_tag(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            ))
        )
        or hatred
        or first_round and has_tag(effect, "mechanic.devoted-killer-hatred")
        and has_tag(effect, "condition.devoted-killer-hatred")
        or kindred
        or imposed_hatred
        or charging and phases.has_tag(effect, "skill.infallible")
        or charging and first_round and phases.has_tag(effect, "skill.axe-expert") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.axe", "weapon.dwarf-axe")
        )
        or charging and first_round and phases.has_tag(effect, "skill.expert-swordsman") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.sword", "weapon.weeping-blades")
        )
        or first_round and phases.has_tag(effect, "skill.crack-shot") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol")
        )
        or charging and phases.has_tag(attacker.global_effects, "dagger_master") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")
        )
        or phases.has_tag(effect, "skill.weapons-of-the-north") and (
            any(phases.has_tag(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            ))
        )
        or first_round and phases.has_tag(effect, "skill.duellist")
        or phases.has_tag(effect, "skill.virtue-of-valour")
        and defender.characteristics.strength > attacker.characteristics.strength
    )


def _parrying_weapons(defender):
    return (defender.main_weapon, defender.off_hand or EffectSet(),
        *(weapon for weapon in defender.extra_attacks if has_tag(weapon, 'mutation.carried-weapon')))


def _parry_context(
    defender: CompiledFighter, defender_state: FighterState,
    effect: EffectSet, strength: int, hit_roll: int, key: str,
    *, natural_hit_six: bool | None = None,
) -> ParryContext | None:
    if (defender_state.parries_remaining <= 0 or _parry_capacity(defender) <= 0
            or defender_state.condition != phases.Condition.STANDING):
        return None
    native_parry = any(weapon.parry for weapon in _parrying_weapons(defender))
    match_allowed = any(phases.has_tag(defender.global_effects, tag) for tag in (
        "skill.sword-master", "skill.swordmaster", "skill.unbeatable-warrior",
    )) or (
        phases.has_tag(defender.global_effects, "skill.defensive-stance") and native_parry
    )
    starblade = any(
        phases.has_tag(weapon, "weapon.starblade")
        for weapon in _parrying_weapons(defender)
    )
    # Miniath grants a parry to any weapon, but only native parrying weapons
    # gain the reroll (Lustria, High Elf Special Skills / Miniath).
    # Hochland Swordmaster changes equality only; it grants no reroll.
    reroll = native_parry and phases.has_tag(defender.global_effects, "skill.miniath")
    reroll = reroll or (
        phases.has_tag(defender.global_effects, "skill.chosen-of-the-white-tower")
        and any(phases.has_tag(candidate, tag)
                for candidate in (*_parrying_weapons(defender), defender.global_effects)
                for tag in ("weapon.sword", "defence.buckler"))
    )
    sword_and_buckler = (
        any(phases.has_tag(weapon, "weapon.sword") for weapon in _parrying_weapons(defender))
        and any(phases.has_tag(weapon, "defence.buckler") for weapon in (
            *_parrying_weapons(defender), defender.global_effects,
        ))
    )
    dwarf_axes = all(
        phases.has_tag(weapon, "weapon.dwarf-axe")
        for weapon in (defender.main_weapon, defender.off_hand)
        if weapon is not None
    ) and defender.off_hand is not None
    # Dwarf-slayer-cult printed Parry: two Dwarf axes, or a Dwarf axe and a sword
    # in either hand order, give up the second parry and gain a single
    # failed-parry reroll instead. Two ordinary swords keep no reroll.
    axe_and_sword = sorted(
        "axe" if phases.has_tag(weapon, "weapon.dwarf-axe")
        else "sword" if phases.has_tag(weapon, "weapon.sword")
        else "other"
        for weapon in (defender.main_weapon, defender.off_hand)
        if weapon is not None
    ) == ["axe", "sword"]
    sword_master_reroll = phases.has_tag(defender.global_effects, "skill.sword-master") and (
        not phases.has_tag(defender.global_effects, "rule.dwarf-axe-parry-reroll") or dwarf_axes
    )
    reroll = (reroll or sword_and_buckler or sword_master_reroll or dwarf_axes
              or axe_and_sword or phases.has_tag(defender.main_weapon, "weapon.fighting-claws"))
    reroll = reroll or phases.has_tag(defender.main_weapon, "weapon.double-bladed-sword")
    return ParryContext(
        hit_roll, strength, defender_state.strength,
        cannot_be_parried=effect.cannot_be_parried,
        match_allowed=match_allowed,
        fixed_target=4 if starblade else None,
        reroll=reroll,
        key=f"{key}.parry",
        can_parry_six=(phases.has_tag(defender.global_effects, "rule.blood-dragon-sword-master")
                      or _estalian_parry(defender)),
        roll_under=defender_state.weapon_skill if _estalian_parry(defender) else None,
        maximum_roll=hit_roll if _darting_steel_parry(defender) else None,
        natural_hit_six=natural_hit_six,
    )


def _estalian_parry(defender: CompiledFighter) -> bool:
    return _darting_steel_parry(defender) or (has_tag(defender.global_effects, "mechanic.estalian-technique")
            and any(has_tag(weapon, "weapon.rapier") for weapon in
                    (defender.main_weapon, defender.off_hand or EffectSet()))
            and any(has_tag(weapon, "weapon.main-gauche") for weapon in
                    (defender.main_weapon, defender.off_hand or EffectSet())))


def _darting_steel_parry(defender: CompiledFighter) -> bool:
    return (has_tag(defender.global_effects, "mechanic.darting-steel")
            and any(has_tag(weapon, "weapon.sword") for weapon in
                    (defender.main_weapon, defender.off_hand or EffectSet()))
            and any(has_tag(weapon, "defence.buckler") for weapon in
                    (defender.main_weapon, defender.off_hand or EffectSet(), defender.global_effects)))


def _injury_context(defender: CompiledFighter, effect: EffectSet, key: str,
                    defender_state: FighterState | None = None,
                    injury_bonus: int = 0) -> InjuryContext:
    global_effects = defender.global_effects
    # The Count of Ventimiglia's Misericordia wounds on its own printed table:
    # stunned on 1-3 and out of action on 4-6, with no knocked-down band.  No
    # Pain still turns the stun into a knock-down for an Undead victim, which
    # is exactly the source's "Undead are knocked down as normal".
    artefact_chart = phases.has_tag(effect, "weapon.count-of-ventimiglias-misericordia")
    return InjuryContext(
        modifier=effect.injury_modifier + int(injury_bonus) + int(
            phases.has_tag(effect, "mechanic.blessing-of-morr")
            and phases.has_tag(global_effects, "nature.undead")
        ) + int(
            phases.has_tag(effect, "skill.knife-fighting")
            and any(phases.has_tag(effect, tag) for tag in ("weapon.dagger", "weapon.yambiya"))
        ) - int(has_tag(global_effects, "mechanic.inured-to-pain")),
        critical_bonus=0,
        out_threshold=(4 if artefact_chart
                       or phases.has_tag(global_effects, "mechanic.bat-injury-chart")
                       else global_effects.out_of_action_threshold),
        stun_threshold=1 if artefact_chart else 3,
        injury_profile=defender.injury_profile,
        hard_to_kill=(phases.has_tag(global_effects, "skill.hard-to-kill")
                      or phases.has_tag(global_effects, "mechanic.fen-hard-to-kill")
                      and not phases.has_tag(effect, "attack.fire")),
        # True Grit reaches the table from the printed skill tag and from the
        # declared variant the execution contract carries: the chart is 1-3
        # Knocked Down, 4-5 Stunned, 6 Out of Action, never the Hard to Kill
        # threshold alone.
        true_grit=(phases.has_tag(global_effects, "skill.tough-as-steel")
                   or global_effects.true_grit),
        concussion=effect.concussion,
        shock=phases.has_tag(effect, "weapon.shock-rod"),
        concussion_immune=phases.has_tag(global_effects, "concussion_immune"),
        fragile=phases.has_tag(global_effects, "fragile_halflings"),
        # Poisonous changes injuries inflicted by the attack, not injuries
        # received by the creature carrying the trait.
        poisonous=(phases.has_tag(effect, "poisonous_injury")
                   and not (global_effects.poison_immunity or phases.has_tag(global_effects, "poison_immune"))),
        survivor=phases.has_tag(global_effects, "survivor"),
        initial_condition=(defender_state.condition if defender_state is not None else phases.Condition.STANDING),
        head_crusher=phases.has_tag(effect, "skill.head-crusher"),
        ignore_pain=(phases.has_tag(global_effects, "skill.ignore-pain")
                     and not phases.has_tag(global_effects, "rule.squishy")),
        jump_up=phases.has_tag(global_effects, "skill.jump-up"),
        mandrake=phases.has_tag(global_effects, "preparation.mandrake-root"),
        key=f"{key}.injury",
    )


def prepare_hit_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, first_round: bool = False,
    charging: bool = False, helpless_at_start: bool = False, key: str = "hit",
    melee_attack: bool = True, allow_luck: bool = True,
) -> HitContext:
    """The runtime and semantic tests share this contextual projection."""
    ws = attacker_state.weapon_skill + weapon.weapon_skill_bonus
    if first_round and charging:
        ws += effect.charge_ws_bonus
    modifier = effect.hit_modifier + defender.global_effects.incoming_hit_modifier
    # Hypnotize: every attack directed against the failed target gains +1 To Hit
    # for that combat phase; the tag is projected by the round consumer.
    if melee_attack and has_tag(defender.global_effects, "condition.hypnotized"):
        modifier += 1
    if melee_attack:
        modifier += int(has_tag(effect, "condition.ye-give-way-victorious"))
        modifier -= int(has_tag(effect, "condition.ye-give-way-refused"))
    if melee_attack and has_tag(defender.global_effects, "condition.djinns-curse-active"):
        modifier -= 1
    if melee_attack:
        modifier += int(first_round and charging
            and has_tag(attacker.global_effects, "skill.backstabber")
            and has_tag(attacker.global_effects, "condition.unseen-charge"))
        # Violent Entry: the supplied summon turn pays its +1 to hit only in the
        # charge itself, so the same first-round charge gate carries it.  The
        # Strength half is the mechanic's charge_strength_bonus; nothing is
        # granted from the fact alone, and the merge keeps one point.
        modifier += int(first_round and charging
            and has_tag(attacker.global_effects, "condition.summoned-this-turn"))
        modifier += int(attacker_state.banter_trick_active)
        modifier -= int(defender_state.banter_trick_active)
    if melee_attack and has_tag(attacker.global_effects, "condition.guiding-dream-target"):
        if not has_tag(defender.global_effects, "fighter-kind.hero"):
            raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
        if attacker_state.guiding_dream_result in (2, 3):
            modifier += 1
    if melee_attack and any(has_tag(fighter.global_effects, "condition.snorri-stench")
                            for fighter in (attacker, defender)):
        # All models fighting in contact are in the source's 2-inch aura,
        # including the bearer; unrelated models are outside this 1v1 duel.
        modifier -= 1
    if (has_tag(attacker.global_effects, "mechanic.flesh-peddler")
            and has_tag(attacker.global_effects, "condition.flesh-peddler-mark")):
        if not has_tag(defender.global_effects, "sex.female"):
            raise ValueError("Flesh-Peddler's nominated opponent requires an explicit female fact")
        modifier += 1
    if melee_attack and has_tag(defender.global_effects, "mechanic.unholy-stink"):
        modifier -= 1
    if melee_attack and any(has_tag(effect, tag) for tag in (
            "condition.command.follow-me-active", "condition.righteous-charge-active")):
        modifier += 1
    if (phases.has_tag(weapon, "weapon.hellblade")
            and not any(phases.has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.daemon"))):
        modifier += 1
    modifier += int(melee_attack and has_tag(attacker.global_effects, "mechanic.andanti-knowledge")
        and has_tag(defender.global_effects, "species.vampire"))
    modifier -= int(phases.has_tag(defender.main_weapon, "weapon.ball-and-chain"))
    if phases.has_tag(defender.global_effects, "rule.putrid-stench") and phases.has_tag(attacker.global_effects, "undead_or_possessed"):
        modifier += 1
    ws += int(phases.has_tag(effect, "skill.knife-fighting") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")
    ))
    if phases.has_tag(weapon, "effect.serpent-staff-power"):
        ws = 4
    modifier += int(charging and phases.has_tag(effect, "skill.berserker"))
    modifier -= int(first_round and charging and phases.has_tag(effect, "skill.ferocious-charge"))
    modifier -= int(first_round and phases.has_tag(defender.global_effects, "skill.bellowing-battle-roar"))
    modifier -= int(phases.has_tag(defender.global_effects, "cloud_of_flies"))
    if (melee_attack
            and phases.has_tag(defender.global_effects, phases.COLD_STEEL_TAG)
            and phases.cold_steel_metal_attack(weapon)
            and not phases.cold_steel_exempt(effect)):
        # Printed Cold Steel (Banshee): a steel or iron weapon can harm the
        # bearer but is at -1 to hit.  The printed exemptions -- blessed and
        # magic weapons hitting normally -- are tested on the incoming attack,
        # so they keep their ordinary to-hit instead of being zeroed by a
        # blanket immunity; an attack that carries no weapon identity at all is
        # not one of the clause's attacks and keeps its own resolution.
        modifier -= 1
    modifier -= int(melee_attack and has_tag(defender.global_effects, "mechanic.foul-odour")
        and not any(has_tag(attacker.global_effects, tag) for tag in
            ("nature.undead", "nature.possessed", "nature.daemon")))
    if melee_attack and has_tag(defender.global_effects, "mechanic.sigmar-symbol-of-unity"):
        named = any(has_tag(attacker.global_effects, tag) for tag in
                    ("band.witch-hunters", "band.trollheim-witch-hunters", "band.sisters-of-sigmar"))
        mercenary = has_tag(attacker.global_effects, "warband-group.human-mercenary")
        if mercenary and any(has_tag(attacker.global_effects, tag) for tag in
                            ("band.mercenaries", "band.trollheim-mercenaries")) and not any(
                tag.startswith("mercenary-origin.") for tag in attacker.global_effects.tags):
            raise ValueError("Symbol of Unity requires the generic mercenary warband's explicit origin")
        excluded = any(has_tag(attacker.global_effects, tag) for tag in
                       ("mercenary-origin.marienburg", "mercenary-origin.middenheim"))
        modifier -= int(named or (mercenary and not excluded))
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging, frenzy=attacker_state.frenzy)
    luck = allow_luck and phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent
    defender_ws = defender_state.weapon_skill
    if melee_attack and any(current.active and has_tag(fighter.global_effects, "mechanic.shallya-tranquil-aura")
            for fighter, current in ((attacker, attacker_state), (defender, defender_state))):
        for own, is_attacker in ((attacker, True), (defender, False)):
            if not any(has_tag(own.global_effects, tag) for tag in ("nature.daemon", "nature.undead")):
                if is_attacker:
                    ws = max(0, ws - 1)
                else:
                    defender_ws = max(0, defender_ws - 1)
    return HitContext(
        ws, defender_ws, modifier,
        automatic=effect.automatic_hit or helpless_at_start or defender_state.charm_auto_hit
            or defender_state.condition == phases.Condition.PARALYZED,
        reroll=reroll or luck, key=key, needs_sixes=attacker_state.fear_hit_sixes and melee_attack,
        fixed_target=2 if melee_attack and has_tag(effect, "mechanic.invincible-swordsman") else None,
    )


def _supplied_ward(effects: EffectSet, *, suppress_step_aside: bool = False) -> int:
    """The special save one effect set supplies on its own."""
    ward = effects.ward_save
    if has_tag(effects, "mechanic.excellent-reflexes"):
        ward = min(ward, 4 if has_tag(effects, "condition.tomb-robber-dodge-known") else 5)
    if effects.step_aside and not suppress_step_aside:
        ward = min(ward, 4 if phases.has_tag(effects, "skill.vampire-reflexes") else 5)
    if (effects.step_aside and not suppress_step_aside
            and phases.has_tag(effects, "skill.elven-agility")):
        ward = min(ward, 4)
    return ward


def prepare_special_save_context(
    defender: CompiledFighter, incoming: EffectSet, *, key: str = "special",
    defender_state: FighterState | None = None, melee_attack: bool = True,
) -> SpecialSaveContext:
    if incoming.ignore_armour_except_shield_and_skills:
        # Printed Ladle clause: "The only saving throws allowed are from shields
        # or skills".  Read the special save from the shield and skill
        # selections alone, so an equipment defence (Enchanted Skins), a
        # mechanic-granted ward or a supplied trait cannot save while a skill's
        # own save (Step Aside, Elven Agility) still resolves.  A save source
        # that only reminds us for mundane attacks keeps that limit.
        allowed = defender.shield_and_skill_effects
        return SpecialSaveContext(
            _supplied_ward(allowed, suppress_step_aside=(
                has_tag(defender.global_effects, "mechanic.ethereal-hit-save")
                and not has_tag(incoming, "attack.magical")))
                + int(has_tag(incoming, "condition.djinns-curse-active")),
            allowed.regeneration_save + int(has_tag(incoming, "condition.djinns-curse-active")),
            ward_blocked=(
                allowed.ward_save_mundane_only and phases.has_tag(incoming, "attack.magical")
            ),
            regeneration_blocked=(
                allowed.regeneration_blocked_by_fire and phases.has_tag(incoming, "attack.fire")
                or allowed.regeneration_blocked_by_blessed and phases.has_tag(incoming, "attack.blessed")
            ),
            key=key,
        )
    ward = _supplied_ward(defender.global_effects, suppress_step_aside=(
        has_tag(defender.global_effects, "mechanic.ethereal-hit-save")
        and not has_tag(incoming, "attack.magical")))
    ward_blocked = defender.global_effects.ward_save_mundane_only and phases.has_tag(incoming, "attack.magical")
    if melee_attack and defender_state is not None and defender_state.dodge_trick_active:
        ward = 4 if ward_blocked else min(ward, 4)
        ward_blocked = False
    # This source treats its listed metals as magical only for this save.
    # Do not change the incoming attack's magic status or other wards.
    if (phases.has_tag(defender.global_effects, "mechanic.ghost-pirate-ethereal")
            and not any(phases.has_tag(incoming, tag) for tag in
                        ("attack.magical", "material.gromril", "material.ithilmar", "ammo.silver-bullets"))):
        ward = 4 if ward_blocked else min(ward, 4)
        ward_blocked = False
    if phases.has_tag(defender.global_effects, "dance.shadows-coil-active"):
        ward = 4 if ward_blocked else min(ward, 4)
        ward_blocked = False
    if phases.has_tag(incoming, "attack.magical"):
        for tag, threshold in (("mechanic.gypsy-ward", 5), ("mechanic.magical-void", 4)):
            if phases.has_tag(defender.global_effects, tag):
                ward = threshold if ward_blocked else min(ward, threshold)
                ward_blocked = False
    if has_tag(defender.global_effects, "condition.djinns-luck-active"):
        # Luck improves the ordinary save, but grants only 6+ when the
        # intrinsic Ethereal save does not apply (notably magical weapons).
        threshold = 6 if ward_blocked or ward > 6 else 4
        ward = threshold if ward_blocked else min(ward, threshold)
        ward_blocked = False
    blocked = (
        defender.global_effects.regeneration_blocked_by_fire and phases.has_tag(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed and phases.has_tag(incoming, "attack.blessed")
    )
    # The specific printed unmodifiable 5+ survives a general save penalty.
    # A stronger ordinary ward (including Luck) keeps its own modifiable source;
    # on equal final faces this also preserves its optional roll modifiers.
    intrinsic_djinn = (has_tag(defender.global_effects, "mechanic.djinn-ethereal")
        and not has_tag(defender.global_effects, "condition.djinns-luck-active")
        and not has_tag(incoming, "attack.magical") and not ward_blocked and ward >= 5)
    return SpecialSaveContext(
        ward + int(has_tag(incoming, "condition.djinns-curse-active") and not intrinsic_djinn),
        defender.global_effects.regeneration_save + int(has_tag(incoming, "condition.djinns-curse-active")),
        ward_blocked=ward_blocked,
        regeneration_blocked=blocked, key=key, ward_unmodifiable=intrinsic_djinn,
    )


def prepare_wound_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, hit_roll: int = 4,
    first_round: bool = False, charging: bool = False, key: str = "wound",
    melee_attack: bool = True, allow_luck: bool = True,
) -> WoundContext:
    strength, _ = _attack_strength(attacker, defender, attacker_state, weapon, effect, first_round, charging,
        melee_attack=melee_attack)
    toughness = max(1, defender_state.toughness - int(melee_attack
        and has_tag(defender.global_effects, "rule.thin-flesh")))
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")
    automatic = (phases.has_tag(effect, "effect.automatic-wound")
        or has_tag(weapon, "effect.wraith-touch") and not any(
            has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.possessed")))
    luck = (
        allow_luck and phases.has_tag(effect, "skill.luck")
        and "luck" not in attacker_state.resources_spent
        and not effect.reroll_wounds
    )
    lotus = phases.black_lotus_wounds(effect, defender.global_effects)
    failure_still_wounds = hit_roll == 6 and (
        phases.has_tag(effect, "wight_blades")
        or lotus and not poison_blocked)
    maximum = min(effect.maximum_wound_target, 4) if phases.has_tag(effect, "skill.monster-slayer") else effect.maximum_wound_target
    # Printed blessed-weapon clause: the blessed weapon wounds Undead and
    # Possessed on 2+, whatever the Strength gap; the victim's nature decides the
    # ceiling and the attack keeps its ordinary to-hit, save and injury sequence.
    if (phases.has_tag(weapon, "blessing.undead-possessed-on-two")
            and phases.has_tag(defender.global_effects, "undead_or_possessed")):
        maximum = min(maximum, 2)
    modifier = effect.wound_modifier + int(
        phases.has_tag(weapon, "weapon.sigmarite-hammer") and phases.has_tag(defender.global_effects, "undead_or_possessed")
    )
    critical_threshold = 5 if (
        phases.has_tag(effect, "poison.wolfsbane") and not poison_blocked
        or phases.has_tag(effect, "mechanic.body-slam")
        or phases.has_tag(effect, "skill.art-of-silent-death")
        or phases.has_tag(attacker.global_effects, "spiritual_weapons")
        or phases.has_tag(effect, "skill.unarmed-critical-strikes") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks"))
    ) else 6
    critical_threshold = min(critical_threshold, effect.critical_threshold)
    if (phases.has_tag(weapon, "weapon.hellblade")
            and max(2, phases.wound_target(strength, toughness, maximum) - modifier) <= 4):
        critical_threshold = min(critical_threshold, 5)
    return WoundContext(
        strength, toughness, modifier, maximum_target=maximum,
        # Lotus already wounds: its optional critical attempt is not a failed
        # wound eligible for Dark Steel/Sure Strike rerolls.
        automatic=automatic, reroll=(effect.reroll_wounds or luck or (
            phases.has_tag(effect, "skill.wound-valour")
            and defender.characteristics.strength > attacker.characteristics.strength
        )) and not (
            hit_roll == 6 and lotus and not poison_blocked
        ),
        critical_threshold=critical_threshold,
        critical_available=attacker_state.critical_available and not phases.has_tag(effect, "effect.no-critical"),
        critical_on_reroll=poison_blocked or not phases.has_tag(effect, "poison.devil-s-toxin"),
        critical_when_needing_six=has_tag(effect, "mechanic.achilles-heel"),
        failure_still_wounds=failure_still_wounds,
        # Printed Cold Steel: an attack the clause leaves unable to harm the
        # bearer never wounds her.  The wound step is where that is observable
        # -- no wound, no critical, no injury -- while the ordinary injury
        # procedure stays untouched for the attacks that can harm her.
        unharmed=phases.cold_steel_unharmed(defender.global_effects, weapon, effect),
        key=key,
    )


def prepare_armour_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, first_round: bool = False,
    charging: bool = False, key: str = "armour", melee_attack: bool = True,
) -> ArmourContext:
    strength, armour_strength = _attack_strength(attacker, defender, attacker_state, weapon, effect, first_round, charging,
        melee_attack=melee_attack)
    dagger_tags = ("weapon.dagger", "weapon.yambiya", "weapon.poisoned-daggers", "weapon.disease-dagger")
    daggers = (attacker.main_weapon, attacker.off_hand)
    dagger_pair = (
        attacker.main_weapon.paired and any(tag in attacker.main_weapon.tags for tag in dagger_tags)
        or attacker.off_hand is not None and all(
            any(tag in hand.tags for tag in dagger_tags) for hand in daggers
        )
    )
    cutthroat = int(phases.has_tag(effect, "skill.cutthroat") and dagger_pair
                   and any(tag in weapon.tags for tag in dagger_tags))
    if phases.has_tag(effect, "skill.monster-slayer-effective-strength-armour") and strength < defender_state.toughness:
        armour_strength = max(armour_strength, defender_state.toughness)
    armour_save = defender.armour_save
    if not melee_attack and has_tag(defender.global_effects, 'defence.sabertooth-hide'):
        # Only the admitted 6+ close-combat face, not the excluded missile 5+.
        armour_save += 1
    natural_armour_save = defender.natural_armour_save
    natural_armour_worst_save = defender.natural_armour_worst_save
    if (defender.global_effects.natural_armour_negated_by_fire
            and has_tag(effect, "attack.fire")):
        natural_armour_save = natural_armour_worst_save = 7
        # This natural save also contributed to the worn-armour combination.
        armour_save += max(0, 7 - defender.natural_armour_save)
    if (has_tag(defender.global_effects, "mechanic.daemonic-flesh")
            and has_tag(effect, "attack.blessed")):
        natural_armour_save = natural_armour_worst_save = 7
    if effect.ignore_armour_except_shield_and_skills:
        # Printed Ladle clause: only shields and skills may save, so the armour
        # the defender wears, its natural armour and every other provenance are
        # denied while the shield and skill selections keep their own save.
        armour_save = max(1, 7 - defender.shield_and_skill_effects.armour_save_bonus)
        natural_armour_save = 7
        natural_armour_worst_save = 7
    if (phases.has_tag(defender.global_effects, "mechanic.norse-bulwark")
            and phases.has_tag(defender.main_weapon, "weapon.axe")
            and defender.off_hand is not None and phases.has_tag(defender.off_hand, "defence.shield")):
        armour_save = max(2, armour_save - 1)
    ignore_armour = effect.ignore_armour or (
        effect.ignore_armour_against_knocked_down
        and defender_state.condition == phases.Condition.KNOCKED_DOWN
    )
    return ArmourContext(
        armour_save, natural_armour_save,
        natural_armour_worst_save, defender.natural_armour_unmodified,
        armour_strength, effect.armour_penetration + cutthroat,
        effect.target_armour_bonus - (
            weapon.target_armour_bonus
            if phases.has_tag(weapon, "weapon.fist") and phases.ignores_unarmed_penalties(effect) else 0
        ),
        ignore_armour, defender.global_effects.armour_save_floor,
        defender.global_effects.armour_cannot_be_ignored,
        phases.has_tag(effect, "attack.magical"), defender.global_effects.natural_armour_negated_by_magic,
        key=key,
        flaming_attack=has_tag(effect, "attack.fire"),
        natural_armour_negated_by_fire=defender.global_effects.natural_armour_negated_by_fire,
        incoming_save_modifier=int(has_tag(effect, "condition.djinns-curse-active")),
    )
