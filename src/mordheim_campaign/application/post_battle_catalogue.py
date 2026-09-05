"""application.post_battle_catalogue: KB read model for the post-battle UI.

Follows the pattern of ``README-HOWTO.md`` (application use case between the
KB loaders and the widgets): the Tk screens ask this catalogue for the
canonical offers a pending post-battle may consume, and it answers with flat
DTOs built from the validated campaign catalogues (trading post, hiring
catalogue, warband groups, hireling profiles) through ``KnowledgePort``.

Scope: *content* a screen can present — which items are common/rare for this
warband at the Trading Post, which Hired Swords/Dramatis entries can be
searched — plus the KB provenance of each of the eight UI actions.  It does
not decide rules and does not touch campaign state: availability rolls,
treasury checks and purchases remain application/persistence work.
"""
from __future__ import annotations

from dataclasses import dataclass

from mordheim_campaign.application.hire_eligibility import DecisionKind, WarbandHireContext, context_from_roster, dynamic_rules_for_profile, evaluate_rule
from mordheim_campaign.application.knowledge_port import KnowledgePort


#: Trading-post restriction kinds that limit whole warbands.
_WARBAND_RESTRICTIONS = frozenset({"warband_only", "warband_forbidden"})

#: UI post-battle actions → indexes into the normative KB sequence
#: (post-battle-sequence.yaml, ten steps).  Steps 6+7 (rare items and Dramatis
#: Personae) share the "Searches" action and the rating step is derived into
#: Final Review, so the UI exposes eight actions over the ten KB steps.
KB_SEQUENCE_INDEXES_PER_ACTION = (
    (0,),          # Injuries              -> campaign.step.serious-injuries
    (1,),          # Experience            -> campaign.step.experience
    (2,),          # Exploration           -> campaign.step.exploration
    (3,),          # Sell Wyrdstone        -> campaign.step.sell-wyrdstone
    (4,),          # Veterans              -> campaign.step.veterans
    (5, 6),        # Rare Items & Dramatis -> rare-items + dramatis-personae
    (7,),          # Recruitment           -> recruit-and-buy-common
    (8,),          # Equipment             -> reallocate-equipment
)

_RESOURCE_LABELS = {
    "gold_crowns": "gc",
    "wyrdstone_fragments": "wyrdstone",
    "treasures": "treasures",
    "campaign_points": "campaign points",
}

_AVAILABILITY_LABELS = {
    "common": "Common",
    "construction": "Construction",
    "hero_replacement": "Hero replacement",
    "summoning": "Summoning",
    "special_scenario": "Special scenario",
}


@dataclass(frozen=True, slots=True)
class TradingPostOffer:
    """A Trading Post item the current warband may buy."""

    item_id: str
    name: str
    kind: str  # "common" | "rare"
    rarity: int | None
    price_label: str
    source: str  # trading-post entry id


@dataclass(frozen=True, slots=True)
class HirelingOffer:
    """A hiring entry (Hired Sword or Dramatis Persona) with costs."""

    entry_id: str
    profile_id: str
    kind: str  # "hired-sword" | "dramatis"
    name: str
    availability_label: str
    fee_label: str | None
    upkeep_label: str | None
    #: Result of the 18 dynamic campaign-eligibility rules: "eligible",
    #: "conditional" (acceptance roll), "variant" (Mercenary variant needed)
    #: or "ineligible". Ineligible offers are not returned.
    eligibility: str = "eligible"
    eligibility_note: str = ""


@dataclass(frozen=True, slots=True)
class PostBattleSources:
    """KB provenance of one of the eight post-battle UI actions."""

    action_index: int
    kb_step_ids: tuple[str, ...]
    resolved_catalogues: tuple[str, ...]  # file names of catalog/campaign


def _dice_label(dice: dict) -> str:
    count = int(dice.get("count") or 1)
    sides = int(dice.get("sides") or 6)
    return f"{count}D{sides}" if count != 1 else f"D{sides}"


def _price_label(price: dict | None) -> str | None:
    """Human label for a trading-post price block."""
    if not isinstance(price, dict):
        return None
    parts = []
    if "base_gc" in price:
        parts.append(f"{price['base_gc']} gc")
    elif "multiplier" in price:
        parts.append(f"{price['multiplier']}× base price")
    variable = price.get("optional_variable_cost")
    if isinstance(variable, dict):
        dice = _dice_label(variable.get("dice") or {})
        multiplier = variable.get("multiplier")
        parts.append(f"{dice}" + (f" × {multiplier}" if multiplier else ""))
    if "per" in price:
        parts.append(f"per {price['per']}")
    return " + ".join(parts) if parts else None


def _resource_label(resources: dict) -> str | None:
    if not resources:
        return None
    pieces = []
    for name, amount in resources.items():
        if not isinstance(amount, dict) or amount.get("cost") is None:
            continue
        unit = _RESOURCE_LABELS.get(name, name.replace("_", " "))
        pieces.append(f"{amount['cost']} {unit}")
    return " + ".join(pieces)


class PostBattleCatalogue:
    """KB offers and provenance for one warband's post-battle screens."""

    def __init__(
        self,
        port: KnowledgePort,
        collection: str,
        band_id: str,
        *,
        ruleset: str = "mordheim",
        member_profile_ids: frozenset[str] = frozenset(),
        variant: str | None = None,
    ) -> None:
        self.port = port
        self.collection = collection
        self.band_id = band_id
        self.ruleset = ruleset
        #: Roster facts the dynamic eligibility rules read. ``member_profile_ids``
        #: are the warband members; hired Hired Swords are not tracked by the
        #: prototype state yet, so they default to none.
        self._hire_context: WarbandHireContext = context_from_roster(
            port,
            collection=collection,
            band_id=band_id,
            member_profile_ids=frozenset(member_profile_ids),
            variant=variant,
        )

    # ---------------------------------------------------------- eligibility

    def _band_group_ids(self) -> frozenset[str]:
        band_groups = []
        for group in self.port.warband_groups():
            if self.band_id in set(group.get("band_ids") or ()):
                band_groups.append(str(group.get("id") or ""))
        return frozenset(band_groups)

    def _restriction_allows(self, restrictions: list | None) -> bool:
        """True when no warband-level restriction excludes this warband."""
        for restriction in restrictions or ():
            if restriction.get("type") not in _WARBAND_RESTRICTIONS:
                continue
            if restriction["type"] == "warband_forbidden":
                band_ids = set(restriction.get("band_ids") or ())
                groups = set(restriction.get("groups") or ())
                if self.band_id in band_ids or self._band_group_ids() & groups:
                    return False
            else:
                band_ids = set(restriction.get("band_ids") or ())
                groups = set(restriction.get("groups") or ())
                if not band_ids and not groups:
                    continue
                if self.band_id in band_ids or self._band_group_ids() & groups:
                    return True
                return False
        return True

    def _entry_static_allows(self, entry: dict) -> bool:
        """Static eligibility of a hiring entry for this warband.

        An entry without a static eligibility block is fully delegated to the
        dynamic campaign-eligibility rules and passes this static gate.
        """
        eligibility = entry.get("eligibility") or {}
        if not eligibility:
            return True  # dynamic rule: decided by the application, not here
        expression = eligibility.get("expression")
        if expression is not None:
            return self._expression_allows(expression)
        allowed_groups = set(eligibility.get("allow_groups") or ())
        allowed_bands = set(eligibility.get("allow_band_ids") or ())
        forbidden_groups = set(eligibility.get("forbid_groups") or ())
        forbidden_bands = set(eligibility.get("forbid_band_ids") or ())
        if self.band_id in forbidden_bands or self._band_group_ids() & forbidden_groups:
            return False
        if allowed_groups or allowed_bands:
            return self.band_id in allowed_bands or bool(self._band_group_ids() & allowed_groups)
        return True

    def _expression_allows(self, node) -> bool:
        if isinstance(node, list):
            return any(self._expression_allows(child) for child in node) if node else False
        if not isinstance(node, dict):
            return False
        if "not" in node:
            return not self._expression_allows(node["not"])
        if "all_of" in node:
            return all(self._expression_allows(child) for child in node["all_of"])
        if "any_of" in node:
            return any(self._expression_allows(child) for child in node["any_of"])
        if "band_id" in node:
            return node["band_id"] == self.band_id
        if "group_id" in node:
            return node["group_id"] in self._band_group_ids()
        return False

    def _dynamic_decisions(self, profile_id: str) -> tuple:
        """Decisions of the profile's campaign-eligibility rules, if any."""
        decisions = []
        for rule_id in dynamic_rules_for_profile(self.port, profile_id):
            try:
                decisions.append(evaluate_rule(rule_id, self._hire_context))
            except KeyError:
                continue
        return tuple(decisions)

    @staticmethod
    def _merge_decisions(decisions: tuple) -> str:
        """Combine rule decisions: any rejection wins; variant need wins over
        conditional; all allowed is eligible."""
        if not decisions:
            return "eligible"
        kinds = {decision.kind for decision in decisions}
        if DecisionKind.REJECTED in kinds:
            return "ineligible"
        if DecisionKind.NEEDS_VARIANT in kinds:
            return "variant"
        if DecisionKind.CONDITIONAL in kinds:
            return "conditional"
        return "eligible"

    # ------------------------------------------------------- trading post

    def trading_post_offers(self, kind: str) -> tuple[TradingPostOffer, ...]:
        """Common or rare Trading Post items available to this warband."""
        catalog = self.port.campaign_catalog()
        trading = catalog.catalogue("trading-post.yaml")
        items = trading.get("items") or ()
        offers = []
        for entry in items:
            availability = entry.get("availability") or {}
            if availability.get("kind") != kind:
                continue
            if not self._restriction_allows(entry.get("restrictions")):
                continue
            item_id = str(entry.get("item_id") or "")
            price_label = _price_label(entry.get("price"))
            if price_label is None:
                continue
            override = self.port.price_override(self.collection, self.band_id, item_id)
            if override is not None:
                price_label = f"{override} gc"  # confirmed market exception
            offers.append(TradingPostOffer(
                item_id=item_id,
                name=str(self.port.item_name(item_id) or item_id),
                kind=kind,
                rarity=availability.get("rarity"),
                price_label=price_label,
                source=str(entry.get("id") or ""),
            ))
        ordering = (lambda offer: (offer.rarity or 0, offer.name.casefold())) if kind == "rare" \
            else (lambda offer: offer.name.casefold())
        return tuple(sorted(offers, key=ordering))

    def common_items(self) -> tuple[TradingPostOffer, ...]:
        return self.trading_post_offers("common")

    def rare_items(self) -> tuple[TradingPostOffer, ...]:
        return self.trading_post_offers("rare")

    # -------------------------------------------------------------- hiring

    def _hiring_offers(self, kind: str) -> tuple[HirelingOffer, ...]:
        """Offers of one hiring kind: static eligibility + the 18 dynamic rules."""
        if not self.band_id:
            return ()
        document = self.port.campaign_catalog().catalogue("hired-swords-and-dramatis.yaml")
        entries = document.get("hired_swords") if kind == "hired-sword" else document.get("dramatis_personae")
        hireling_names = {
            str(row.get("id") or ""): str(row.get("name") or row.get("id") or "")
            for row in self.port.hireling_catalogue().profiles
        }
        offers = []
        for entry in entries or ():
            profile_id = str(entry.get("profile_id") or "")
            if not self._entry_static_allows(entry):
                continue
            decisions = self._dynamic_decisions(profile_id)
            eligibility = self._merge_decisions(decisions)
            if eligibility == "ineligible":
                continue
            availability = entry.get("availability") or {}
            availability_label = _AVAILABILITY_LABELS.get(
                availability.get("kind"), "Search procedure"
            )
            note = " ".join(
                decision.note for decision in decisions
                if decision.kind in (DecisionKind.CONDITIONAL, DecisionKind.NEEDS_VARIANT)
            )
            offers.append(HirelingOffer(
                entry_id=str(entry.get("id") or ""),
                profile_id=profile_id,
                kind=kind,
                name=hireling_names.get(profile_id, profile_id),
                availability_label=availability_label,
                fee_label=_resource_label((entry.get("hiring_fee") or {}).get("resources")),
                upkeep_label=_resource_label((entry.get("upkeep") or {}).get("resources")),
                eligibility=eligibility,
                eligibility_note=note.strip(),
            ))
        return tuple(sorted(offers, key=lambda offer: (offer.eligibility != "eligible", offer.name.casefold())))

    def hired_swords(self) -> tuple[HirelingOffer, ...]:
        return self._hiring_offers("hired-sword")

    def dramatis_personae(self) -> tuple[HirelingOffer, ...]:
        return self._hiring_offers("dramatis")

    # ---------------------------------------------------------- provenance

    def action_sources(self) -> tuple[PostBattleSources, ...]:
        """KB provenance for each of the eight post-battle UI actions."""
        sequence = self.port.post_battle_sequence()
        kb_steps = sequence.steps
        result = []
        for index, kb_indexes in enumerate(KB_SEQUENCE_INDEXES_PER_ACTION):
            steps = [kb_steps[i] for i in kb_indexes if i < len(kb_steps)]
            result.append(PostBattleSources(
                action_index=index,
                kb_step_ids=tuple(step.id for step in steps),
                resolved_catalogues=tuple(step.resolves for step in steps),
            ))
        return tuple(result)
