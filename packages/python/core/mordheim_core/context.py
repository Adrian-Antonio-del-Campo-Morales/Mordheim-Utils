"""Validated preparation of explicitly supplied simulation facts."""
from __future__ import annotations

from dataclasses import dataclass
from mordheim_core.models import CompiledFighter, DuelContext, LocalParticipant


@dataclass(frozen=True, slots=True)
class PreparedDuelContext:
    facts: DuelContext
    participants: tuple[LocalParticipant, ...]

    def participant(self, participant_id: str) -> LocalParticipant:
        for participant in self.participants:
            if participant.participant_id == participant_id:
                return participant
        raise ValueError(f"unknown local participant: {participant_id}")

    def characteristic(self, participant_id: str, name: str) -> int:
        if name not in {"movement", "leadership"}:
            raise ValueError(f"unsupported contextual characteristic: {name}")
        value = getattr(self.participant(participant_id).fighter.characteristics, name)
        if value is None:
            raise ValueError(f"{participant_id} requires explicit {name}")
        return value

    def distance(self, first: str, second: str) -> float:
        self.participant(first)
        self.participant(second)
        for a, b, inches in self.facts.distances:
            if {a, b} == {first, second}:
                return inches
        raise ValueError(f"missing distance between {first} and {second}")

    def charge_flags(self, legacy_first_charged: bool) -> tuple[bool, bool]:
        if self.facts.charging is None:
            return legacy_first_charged, not legacy_first_charged
        return self.facts.first_id in self.facts.charging, self.facts.second_id in self.facts.charging

    def first_player_turn(self, legacy_first_charged: bool) -> bool:
        if self.facts.active_participant is None:
            return legacy_first_charged
        return self.facts.active_participant == self.facts.first_id


def prepare_duel_context(first: CompiledFighter, second: CompiledFighter,
                         context: DuelContext | None) -> PreparedDuelContext | None:
    """Shared by production drivers and verification; no inferred geometry."""
    if context is None:
        return None
    if not isinstance(context, DuelContext):
        raise ValueError("context must contain local duel facts")
    return PreparedDuelContext(context, (
        LocalParticipant(context.first_id, "first", first),
        LocalParticipant(context.second_id, "second", second),
        *context.nearby,
    ))
