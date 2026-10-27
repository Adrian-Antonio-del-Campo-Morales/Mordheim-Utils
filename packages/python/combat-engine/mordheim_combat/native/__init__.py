"""mordheim_combat.native: compiled Cython duel engine.

This package owns the whole native engine: the compile-time folding layer
(``_combat_compile``/``_helpers``), the public driver (``_driver``), the
observation contract and the extension sources ``_combat_native.pyx``/``.pxd``.

The built extension keeps the historical module name
``mordheim_combat._combat_native``; the public entry point is this package::

    from mordheim_combat.native import simulate_duel

There is no fallback engine: when the extension is missing or built for stale
layouts, ``available_backends()`` is empty and execution raises
:class:`NativeUnavailable`.
"""
from __future__ import annotations

from mordheim_combat.native._driver import NativeIncompatible
from mordheim_combat.native._driver import NativeUnavailable
from mordheim_combat.native._driver import available_backends
from mordheim_combat.native._driver import simulate_batch_observed
from mordheim_combat.native._driver import simulate_duel
from mordheim_combat.native._observations import VectorBatchObservation

__all__ = (
    "NativeIncompatible",
    "NativeUnavailable",
    "VectorBatchObservation",
    "available_backends",
    "simulate_batch_observed",
    "simulate_duel",
)
