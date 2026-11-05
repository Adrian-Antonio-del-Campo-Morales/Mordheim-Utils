"""Specialized field-copy replace for the hot immutable state transitions.

``dataclasses.replace`` dominates the scalar engine's profile (over 1.6
million calls per few hundred duels) because it re-enters ``__init__`` with
every field as a keyword. For the two state classes the engine rebuilds on
nearly every step, this module compiles a direct copier: same resulting
object, a fraction of the cost.

The debugging guarantees of ``dataclasses.replace`` are preserved:

* an unknown field name raises ``TypeError`` (a typo must never become a
  silent no-op);
* a class with ``__post_init__`` is refused at registration, so a future
  invariant cannot silently stop running — such a class keeps the stdlib
  path;
* with ``MORDHEIM_DEBUG_FAST_REPLACE=1`` every call is cross-checked
  against ``dataclasses.replace`` and any divergence raises immediately.

``replace`` below is a drop-in dispatcher: registered classes take the fast
path, every other dataclass falls through to ``dataclasses.replace``
unchanged (the modular modules also rebuild ``EffectSet``,
``Characteristics`` and compiled fighters, which keep their validation).
"""
from __future__ import annotations

import dataclasses
import os

_DEBUG_CROSS_CHECK = os.environ.get("MORDHEIM_DEBUG_FAST_REPLACE") == "1"

#: type -> compiled copier, populated by :func:`register`.
_COPIERS: dict[type, object] = {}


def _compile_copier(cls: type):
    """Build a direct field copier for one frozen, slotted dataclass."""
    if getattr(cls, "__post_init__", None) is not None:
        raise TypeError(
            f"{cls.__name__} defines __post_init__; its invariants must keep "
            "running, so it cannot take the fast replace path")
    names = tuple(field.name for field in dataclasses.fields(cls))
    name_set = frozenset(names)
    # Generated like dataclasses generates __init__: direct attribute reads
    # beat a getattr loop by ~2x on a 63-field state.
    lines = [
        "def copier(obj, changes):",
        "    unknown = changes.keys() - _names",
        "    if unknown:",
        "        raise TypeError(f\"replace() got unexpected field(s) for \"",
        f"                        f\"{cls.__name__}: {{', '.join(sorted(unknown))}}\")",
        "    new = _new(_cls)",
    ]
    for name in names:
        lines.append(
            f"    _set(new, {name!r}, changes[{name!r}] "
            f"if {name!r} in changes else obj.{name})")
    lines.append("    return new")
    scope = {"_new": object.__new__, "_set": object.__setattr__,
             "_cls": cls, "_names": name_set}
    exec("\n".join(lines), scope)
    return scope["copier"]


def register(cls: type) -> None:
    """Enable the fast path for one dataclass (refused with __post_init__)."""
    _COPIERS[cls] = _compile_copier(cls)


def replace(obj, **changes):
    """Drop-in ``dataclasses.replace`` with a fast path for registered classes."""
    copier = _COPIERS.get(type(obj))
    if copier is None:
        return dataclasses.replace(obj, **changes)
    if _DEBUG_CROSS_CHECK:
        fast = copier(obj, changes)
        reference = dataclasses.replace(obj, **changes)
        if fast != reference:
            raise AssertionError(
                f"fast replace diverged from dataclasses.replace for "
                f"{type(obj).__name__}: {fast!r} != {reference!r}")
        return fast
    return copier(obj, changes)
