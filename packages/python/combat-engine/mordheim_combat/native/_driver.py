"""Public entry point of the compiled native combat engine.

The native engine is the only optimized backend: a ``DuelRequest`` is validated
against the native admission gate, lowered to a kernel plan, and executed by the
compiled extension.  There is no fallback to the modular engine or to NumPy; if
the extension is missing or stale, the call fails with an explicit error.

Seeds, batch partitioning, cancellation and result accumulation are the
extension's own contract: the compiled driver derives one PCG32 stream per
batch from the request seed and accumulates the three outcome counters across
batches, so passing the request through is all this entry point has to do.
"""
from __future__ import annotations

from mordheim_core.models import DuelContext
from mordheim_core.models import DuelRequest
from mordheim_core.models import DuelResult

from mordheim_combat.native._observations import VectorBatchObservation


class NativeUnavailable(RuntimeError):
    """The compiled extension is absent, incomplete or built for stale layouts."""


class NativeIncompatible(RuntimeError):
    """The extension cannot execute this duel plan (capacity gate)."""


_REQUIRED_ATTRIBUTES = ("simulate_duel", "simulate_batch_observed", "supports_plan")


def _extension():
    """Return the checked extension module, or raise :class:`NativeUnavailable`."""
    try:
        from mordheim_combat import _combat_native
    except ImportError as error:
        raise NativeUnavailable(
            "native combat extension is not available; install the project with "
            "a working C compiler and rebuild it"
        ) from error
    missing = [name for name in _REQUIRED_ATTRIBUTES if not hasattr(_combat_native, name)]
    if missing:
        raise NativeUnavailable(
            "native combat extension is incomplete (missing "
            + ", ".join(missing)
            + "); rebuild it"
        )
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS

    if getattr(_combat_native, "N_EFFECT_FIELDS", None) != len(EFFECT_VALUE_FIELDS):
        raise NativeUnavailable(
            "native combat effect layout is stale; rebuild the extension"
        )
    return _combat_native


def available_backends() -> tuple[str, ...]:
    """Return the executable optimized backend; empty when the extension is unusable."""
    try:
        _extension()
    except NativeUnavailable:
        return ()
    return ("native",)


def _prepare(first, second, context: DuelContext | None):
    """Validate admission and capacity, returning the extension and its plan."""
    from mordheim_combat.kernel import compile_duel_plan
    from mordheim_combat.native._combat_compile import MAX_RANDOM_CHARACTERISTICS

    # Admission and capacity are pure-Python decisions: they run before the
    # extension is loaded, so a refused duel is reported as an incompatibility
    # even on a machine where the extension cannot be imported.
    if any(len(fighter.random_characteristics) > MAX_RANDOM_CHARACTERISTICS
           for fighter in (first, second)):
        raise NativeIncompatible(
            "native combat backend does not support this duel plan"
        )
    # ``compile_duel_plan`` runs the native admission gate and prepares the
    # duel context; its ValueError is the documented "requires the modular
    # engine" refusal, which is an incompatibility rather than a divergence.
    plan = compile_duel_plan(first, second, context=context, backend="native")

    native = _extension()
    if context is not None and getattr(native, "CONTEXT_VERSION", None) != 1:
        raise NativeUnavailable(
            "native combat context layout is stale; rebuild the extension"
        )
    if not plan.optimization_eligible:
        raise NativeIncompatible(
            "native combat backend does not support this duel plan"
        )
    # ``supports_plan`` only sees the kernel plan; the extra-attack capacity is
    # the extension's own gate.
    if not native.supports_plan(plan):
        raise NativeIncompatible(
            "native combat backend does not support this duel plan"
        )
    return native, plan


def simulate_duel(request: DuelRequest) -> DuelResult:
    """Run a duel request through the compiled native core."""
    if not isinstance(request, DuelRequest):
        raise TypeError("simulate_duel requires a DuelRequest")
    native, plan = _prepare(request.first, request.second, request.context)
    return native.simulate_duel(request, plan)


def simulate_batch_observed(
    first, second, count: int, rng, maximum_rounds: int,
    decisions=None, *, context: DuelContext | None = None,
) -> VectorBatchObservation:
    """Run one observed batch from an explicit scripted draw source.

    ``rng`` must provide the NumPy-style ``integers`` and ``random`` calls the
    compiled core makes; observations own their buffers after core cleanup.
    """
    if rng is None:
        raise ValueError("observed native batch requires an explicit RNG source")
    native, _plan = _prepare(first, second, context)
    return native.simulate_batch_observed(
        first, second, count, rng, maximum_rounds, decisions, context=context,
    )


__all__ = (
    "NativeIncompatible",
    "NativeUnavailable",
    "VectorBatchObservation",
    "available_backends",
    "simulate_batch_observed",
    "simulate_duel",
)
