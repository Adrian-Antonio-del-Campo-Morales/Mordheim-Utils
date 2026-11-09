"""Option names shared by every Combat Lab and verification tool.

One concept has one option name, with one meaning, in every tool:

``--scenarios``    what runs (same values everywhere, see ``SCENARIOS_HELP``)
``--simulations``  duels per scenario
``--workers``      worker processes
``--backend``      engine(s)
``--batch-size``   duels per engine batch
``--rounds``       round limit, overriding each scenario's own
``--seed``         random seed
``--output``       where the report is written
``--json``         print the report as JSON

Parsing here never imports an engine or loads a catalogue: the values are
resolved by ``tools.verification.parity_catalog`` after parsing.
"""
from __future__ import annotations

#: The levels of the precompiled catalogue, in containment order.  Duplicated
#: from ``tests.engines.fixtures.precompiled_catalog`` on purpose: building a
#: parser must not load the catalogue; a test keeps the two equal.
LEVELS = ("small", "normal", "big")

SCENARIOS_HELP = (
    "what to run, the same values in every tool: small (8 scenarios), normal "
    "(30) or big (all 43); realistic-50 or realistic-100 (the curated duels a "
    "performance run measures); e2e (every E2E delivery); battery (every "
    "battery case); or single cases -- a scenario name such as basic or long, "
    "realistic/<nnn>, an E2E case_key or audit_id::id, battery/<id>.  Several "
    "values run their union; a case a tool cannot run is listed with the reason"
)


def add_scenarios(container, *, default: str) -> None:
    """Declare ``--scenarios``; ``default`` describes what runs without it."""
    container.add_argument(
        "--scenarios", nargs="+", default=None, metavar="NAME",
        help=f"{SCENARIOS_HELP} (default: {default})",
    )


def size(value: str) -> int:
    """One positive count, with an optional k / m suffix (``100k``, ``1m``)."""
    token = value.strip().lower()
    multiplier = 1
    if token.endswith("k"):
        multiplier, token = 1_000, token[:-1]
    elif token.endswith("m"):
        multiplier, token = 1_000_000, token[:-1]
    try:
        parsed = int(token) * multiplier
    except ValueError:
        raise ValueError(f"invalid size {value!r}; use an integer or a k/m suffix") from None
    if parsed < 1:
        raise ValueError("sizes must be positive")
    return parsed


def sizes(value: str) -> tuple[int, ...]:
    """A comma separated list of sizes (``10k,100k``); one value is a list of one."""
    parsed = tuple(dict.fromkeys(size(token) for token in value.split(",") if token.strip()))
    if not parsed:
        raise ValueError("no size given")
    return parsed
