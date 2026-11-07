"""Option names shared by every Combat Lab and verification tool.

One concept has one option name, with one meaning, in every tool:

``--scenarios``    what runs: a level (``small``, ``normal``, ``big``) or
                   scenario names; several values select their union
``--simulations``  duels per scenario (per case, per pair)
``--workers``      worker processes
``--backend``      engine(s)
``--batch-size``   duels per engine batch
``--seed``         random seed
``--output``       where the report is written

Options that a tool used to spell differently are kept as hidden *retired*
options: giving one stops with the name that replaced it, instead of the
generic "unrecognized arguments".  Parsing here never imports an engine.
"""
from __future__ import annotations

from argparse import SUPPRESS, Action

#: The levels of the precompiled catalogue, in containment order.  Duplicated
#: from ``tests.engines.fixtures.precompiled_catalog`` on purpose: building a
#: parser must not load the catalogue; a test keeps the two equal.
LEVELS = ("small", "normal", "big")


def add_scenarios(container, *, default: str, extra: str = "") -> None:
    """Declare ``--scenarios`` with the shared help text.

    ``default`` describes what runs without the option; ``extra`` names the
    additional values a tool accepts (E2E deliveries, battery profiles).
    """
    container.add_argument(
        "--scenarios", nargs="+", default=None, metavar="NAME",
        help="what to run: a level -- small (8 scenarios), normal (30) or big "
             "(all 43) -- or one or more scenario names such as basic or long; "
             "several values run their union" + (f"; {extra}" if extra else "")
             + f" (default: {default})",
    )


class _Retired(Action):
    """A former option name: stop and name its replacement."""

    def __init__(self, option_strings, dest, replacement: str, **_):
        super().__init__(option_strings, dest=SUPPRESS, nargs="*",
                         default=SUPPRESS, help=SUPPRESS)
        self.replacement = replacement

    def __call__(self, parser, namespace, values, option_string=None):
        parser.error(f"{option_string} was replaced: {self.replacement}")


def retire(parser, *names: str, replacement: str) -> None:
    """Register former option ``names`` that now fail with ``replacement``."""
    parser.add_argument(*names, action=_Retired, replacement=replacement)
