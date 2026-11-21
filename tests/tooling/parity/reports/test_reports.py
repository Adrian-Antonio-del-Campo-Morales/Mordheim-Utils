"""The obligation report: payload fields and its Markdown rendering."""

from mordheim_combat_lab.verification.parity import (
    ParityObligation, ParityReport, parity_report_markdown, parity_report_payload,
)


def _report(*, complete=True, pending=(), divergences=()):
    return ParityReport(
        complete=complete,
        obligations=(ParityObligation("tag", "skill.luck", "operators.py", "test::x", True),),
        verified=("skill.luck",), pending=pending, divergences=divergences,
        exact_checks=("hit-targets", "armour"),
    )


def test_payload_records_the_obligations_and_the_elapsed_time():
    payload = parity_report_payload(_report(), elapsed_seconds=4.0)
    assert payload["complete"] is True and payload["elapsed_seconds"] == 4.0
    assert payload["exact_checks"] == ("hit-targets", "armour")
    assert payload["obligations"][0]["id"] == "skill.luck"
    assert payload["obligations"][0]["verified"] is True
    # An unmeasured run says so rather than claiming zero.
    assert parity_report_payload(_report())["elapsed_seconds"] is None


def test_markdown_lists_the_checks_and_every_unfinished_obligation():
    payload = parity_report_payload(
        _report(complete=False, pending=("tag:armour.attlas",), divergences=("priority",)),
        elapsed_seconds=1.0,
    )
    markdown = parity_report_markdown(payload)
    assert "- Complete: `False`" in markdown
    assert "`hit-targets`" in markdown
    assert "## Divergences" in markdown and "- priority" in markdown
    assert "## Pending" in markdown and "- tag:armour.attlas" in markdown
    # A clean report does not print empty sections.
    clean = parity_report_markdown(parity_report_payload(_report()))
    assert "## Divergences" not in clean and "## Pending" not in clean
