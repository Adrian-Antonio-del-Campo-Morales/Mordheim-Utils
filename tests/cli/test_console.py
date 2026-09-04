import argparse

from mordheim_combat_lab.console import HelpFormatter
from mordheim_combat_lab.console import style_help

SAMPLE = (
    "usage: tool [opts]\n"
    "\n"
    "description line\n"
    "\n"
    "options:\n"
    "  --flag VAL    help for flag\n"
    "  -n N, --num N  extra help\n"
)


def test_style_is_plain_when_stdout_is_not_a_terminal():
    # pytest capture is never a tty, so the auto path must stay plain.
    assert style_help(SAMPLE) == SAMPLE


def test_force_color_marks_usage_headings_and_names():
    styled = style_help(SAMPLE, color=True)
    assert "\x1b[1musage: tool [opts]\x1b[0m" in styled
    assert "\x1b[1;36moptions:\x1b[0m" in styled
    # A single flag keeps its metavar inside the colored token.
    assert "\x1b[1;33m--flag VAL\x1b[0m" in styled
    # Combined short/long flags are colored as one invocation.
    assert "\x1b[1;33m-n N, --num N\x1b[0m" in styled
    # Prose stays uncolored.
    assert "description line" in styled
    assert "help for flag" in styled


def test_metavar_listings_are_not_mistaken_for_headings():
    styled = style_help("  {a,b,c}\n  Engines, parity and benchmarks\n", color=True)
    assert styled == (
        "  {a,b,c}\n" + "\x1b[1;36m  Engines, parity and benchmarks\x1b[0m\n"
    )


def test_no_color_environment_wins_over_force(monkeypatch):
    monkeypatch.setenv("MORDHEIM_FORCE_COLOR", "1")
    monkeypatch.setenv("NO_COLOR", "1")
    assert style_help(SAMPLE) == SAMPLE
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("MORDHEIM_NO_COLOR", "1")
    assert style_help(SAMPLE) == SAMPLE


def test_formatter_applies_the_palette_when_forced_and_plain_otherwise():
    def build(formatter_class):
        parser = argparse.ArgumentParser(
            prog="probe", add_help=False, formatter_class=formatter_class,
        )
        parser.add_argument("--thing", metavar="V", help="a flag with help")
        return parser.format_help()

    assert "\x1b[" not in build(HelpFormatter)
    forced = build(lambda prog: HelpFormatter(prog, color=True))
    assert "\x1b[1;33m--thing V\x1b[0m" in forced
    assert "a flag with help" in forced
