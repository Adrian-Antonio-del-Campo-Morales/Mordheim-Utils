"""Public API of the scalar modular engine."""
from .duel import simulate_duel
from .rounds import resolve_round

__all__ = ["resolve_round", "simulate_duel"]
