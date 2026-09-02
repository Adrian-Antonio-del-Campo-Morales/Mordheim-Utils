"""API pública del motor modular escalar."""
from .duel import simulate_duel
from .rounds import resolve_round

__all__ = ["resolve_round", "simulate_duel"]
