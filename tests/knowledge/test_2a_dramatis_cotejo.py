"""Guards for the Dramatis Personae source cotejo of 2A (``check_2a_dramatis``).

The cotejo compares each printed entry of the grade-2a page against its catalogue
profile and its hiring entry. Two things make it worth running, and this module
pins both:

1. the printed block is read **as the page structures it** — one entry per
   ``div.fighter`` — so the neighbour's fee, stat row and rating never count for
   the entry being checked. That was the defect: the cotejo read flat text and
   reported ``“Busty” Gwen`` with the Dark Jester's 75/30 and ``The Foole`` with
   Sigmund's 70/35, and left four of the seven profiles unlocated;
2. a package that drifts from the page has to show up. The mutation runs against
   a throwaway copy of the contract under ``tmp_path``, so the knowledge tree is
   only ever read.

The integration tests read the cached page (``build/cache/2a-dp``, not versioned)
and skip when it is absent, exactly like the ingest tools they guard.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
# The 2A/2B ingestion tools live in tools/ingestion (temporary: see its README).
TOOLS = ROOT / "tools" / "ingestion"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

cotejo = pytest.importorskip("check_2a_dramatis")

PAGE = ROOT / "build" / "cache" / "2a-dp" / "dramatis-grade-2a.html"
CACHED = pytest.mark.skipif(not PAGE.exists(),
                            reason="mordheimer.net page snapshot is not cached (offline checkout)")

GRADE_2A = (
    "Aksho'akhash the Vile Dreadwing, Lord of the Carrion Throne",
    "\u201cBusty\u201d Gwen",
    "The Dark Jester in Mordheim",
    "The Headless Horseman",
    "The Foole",
    "Sigmund Spindle, the Harvester of Flesh",
    "William Sch\u00e4kestange, Master Bard",
)
# La cobertura que el cotejo tiene que declarar: el Horseman imprime tarifa y
# tabla de jinete y montura y el catálogo no lo modela (está adjudicado
# `out_of_scope`), así que su tarifa y su fila no son comparables y se anotan.
COVERAGE = {"block": 7, "fee": 6, "stats": 6, "rating": 7, "rules": 7}


def run_cotejo(tmp_path, monkeypatch, campaign: Path | None = None) -> list[dict]:
    """El informe del cotejo con su salida escrita fuera del árbol de build."""
    # El cotejo filtra por ``sys.argv`` (los nombres que se le pasan a mano); sin
    # esto tomaría los argumentos de pytest por nombres de perfil.
    monkeypatch.setattr(sys, "argv", ["check_2a_dramatis.py"])
    monkeypatch.setattr(cotejo, "OUT", tmp_path / "dp_check.json")
    monkeypatch.setattr(cotejo, "BLOCKS", tmp_path / "blocks")
    if campaign is not None:
        monkeypatch.setattr(cotejo, "CAMPAIGN_DOC", campaign)
    assert cotejo.main() == 0
    return json.loads((tmp_path / "dp_check.json").read_text(encoding="utf-8"))


def grade_2a(rows: list[dict]) -> dict[str, dict]:
    return {row["name"]: row for row in rows if row["name"] in GRADE_2A}


# --------------------------------------------------------------------------- #
# La lectura de la página real
# --------------------------------------------------------------------------- #

@CACHED
def test_the_page_is_read_one_entry_per_printed_block() -> None:
    """Cada personaje con su tarifa y su fila, sin la del vecino de columna."""
    corpus, kind = cotejo.corpus_for("grade-2a")
    assert kind == "html"
    entries = {entry["heading"]: entry for entry in corpus.entries()}
    assert "\u201cBusty\u201d Gwen" in entries
    gwen = entries["\u201cBusty\u201d Gwen"]
    jester = entries["The Dark Jester in Mordheim"]
    # Gwen cobra por el escenario: su entrada no imprime tarifa, y los 75/30 que el
    # cotejo anterior le atribuía son los del Dark Jester, que es el vecino.
    assert cotejo.fees_in(gwen["text"]) == []
    assert cotejo.fees_in(jester["text"]) == [(75, "gold crowns", 30, "gold crowns")]
    # Y la fila de dos cifras (Ld 10) del Aksho se conserva entera.
    aksho = entries["Aksho'akhash the Vile Dreadwing, Lord of the Carrion Throne"]
    assert cotejo.stat_rows(aksho) == ["4534335210"]


@CACHED
def test_the_seven_grade_2a_entries_verify_without_findings(tmp_path, monkeypatch) -> None:
    rows = grade_2a(run_cotejo(tmp_path, monkeypatch))
    assert set(rows) == set(GRADE_2A)
    for name, row in rows.items():
        assert row["findings"] == [], name
        assert row["comparable"] is True, name
        assert {"block", "rating", "rules"} <= set(row["checks"]), name


@CACHED
def test_the_report_declares_its_coverage(tmp_path, monkeypatch) -> None:
    """Un «0 hallazgos» sin filas comparadas no es un «0 comprobado»."""
    rows = [row for row in run_cotejo(tmp_path, monkeypatch) if row["comparable"]]
    comparable = [row for row in rows if row["name"] in GRADE_2A]
    counts = {check: sum(1 for row in comparable if check in row["checks"])
              for check in cotejo.CHECKS}
    assert counts == COVERAGE
    assert all(row["findings"] == [] for row in rows)


@CACHED
def test_the_profile_without_a_modelled_table_is_not_compared(tmp_path, monkeypatch) -> None:
    """El Horseman es jinete y montura y el catálogo lo deja sin tabla: se anota."""
    horseman = grade_2a(run_cotejo(tmp_path, monkeypatch))["The Headless Horseman"]
    assert horseman["checks"] == ["block", "rating", "rules"]
    notes = " ".join(horseman["notes"])
    assert "out_of_scope" in notes
    assert "la fuente imprime la tarifa 100 gold crowns" in notes
    assert "ni la fuente ni el paquete declaran características" in notes


# --------------------------------------------------------------------------- #
# El cotejo tiene que poder fallar
# --------------------------------------------------------------------------- #

@CACHED
def test_a_fee_that_drifts_from_the_page_is_a_finding(tmp_path, monkeypatch) -> None:
    """La mutación: cambiar la tarifa de Sigmund en el contrato exige el hallazgo."""
    document = yaml.safe_load(cotejo.CAMPAIGN_DOC.read_text(encoding="utf-8"))
    for entry in document["dramatis_personae"]:
        if entry["profile_id"] == "hireling.dramatis.sigmund-spindle-the-harvester-of-flesh":
            entry["hiring_fee"]["resources"]["gold_crowns"]["cost"] = 35
    mutated = tmp_path / "hired-swords-and-dramatis.yaml"
    mutated.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    row = grade_2a(run_cotejo(tmp_path, monkeypatch, campaign=mutated))[
        "Sigmund Spindle, the Harvester of Flesh"]
    assert "fee" not in row["checks"]
    assert any("tarifa impresa" in finding and "70" in finding
               for finding in row["findings"])


@CACHED
def test_a_stat_row_that_drifts_from_the_page_is_a_finding(tmp_path, monkeypatch) -> None:
    """Y una fila de stats: la del Foole contra la de su vecino."""
    catalog = cotejo.CATALOGUE
    document = yaml.safe_load((catalog / "grade-2a.yaml").read_text(encoding="utf-8"))
    for profile in document["profiles"]:
        if profile["id"].endswith("the-foole"):
            profile["characteristics"]["Ld"] = 8
    sandbox = tmp_path / "dramatis-personae"
    sandbox.mkdir()
    (sandbox / "grade-2a.yaml").write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(cotejo, "CATALOGUE", sandbox)
    row = grade_2a(run_cotejo(tmp_path, monkeypatch))["The Foole"]
    assert "stats" not in row["checks"]
    assert any("444431417" in finding for finding in row["findings"])


@CACHED
def test_an_editorial_rule_label_is_a_note_and_not_a_finding(tmp_path, monkeypatch) -> None:
    """La etiqueta que el árbol escribe para un hecho que la fuente imprime aparte."""
    william = grade_2a(run_cotejo(tmp_path, monkeypatch))[
        "William Sch\u00e4kestange, Master Bard"]
    assert "rules" in william["checks"]
    assert william["findings"] == []
    assert any("Conditional Acceptance" in note for note in william["notes"])
