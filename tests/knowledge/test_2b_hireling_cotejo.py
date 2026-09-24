"""Guards for the hireling source cotejo of sources/2B (``check_2b_hirelings``).

The cotejo compares each printed entry of the MiM / Miracle Workers / Karak Azgal
/ Relics pages against its staged package. It is only worth a green run if three
things hold, and this module pins all three:

1. the printed block is read **per column**: the neighbour's fee, stat row and
   rating never count for the entry being checked (the Halfling Pimp's +10, not
   the Fence's +15; the Fire-Eater's +30, not the Sister's +15);
2. a stat row is read in **table order** even when the extractor scatters it —
   the Fire-Eater prints ``4(6) 2 3 3 4 2 2 1 7`` and the Movement digit comes
   out of the geometry on a different line than the other eight;
3. the printed **currency** is compared, so re-encoding the Albino Stormvermin's
   ``75 warp tokens`` as 75 gold crowns is a finding instead of silence.

The first three are fixture tests and need nothing cached. The integration tests
read the cached PDFs (``build/cache/2b-pdfs``, not versioned) and skip when they
are absent, exactly like the ingest tool they guard; the mutation runs against a
throwaway copy under ``build/cache`` and writes its report to a temporary
directory, so the staging tree and the built report are only ever read.
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

cotejo = pytest.importorskip("check_2b_hirelings")

CACHED = pytest.mark.skipif(
    cotejo.pdf_for("MiM Specialists") is None
    or cotejo.pdf_for("adventurers-kaz") is None,
    reason="2B source PDFs are not cached (offline checkout)",
)

# Los siete hallazgos que la pasada de adjudicación cerró: seis eran artefactos
# del extractor (el dato del paquete era el impreso) y uno una divisa convertida.
ADJUDICATED = (
    "Bog Hunter", "Midshipman", "Halfling Pimp", "Albino Stormvermin",
    "Norse Bearman Bodyguard", "Fire-Eater", "Priest of Verena",
)
CHECKS = ("block", "fee", "stats", "rating", "rules")


def line(text: str, words: list[tuple[int, int, str]]) -> dict:
    """Una línea física tal y como la devuelve la lectura por geometría."""
    return {"text": text, "top": 0, "left": min((w[0] for w in words), default=0),
            "words": words}


# --------------------------------------------------------------------------- #
# Las tres clases de artefacto que la pasada cerró
# --------------------------------------------------------------------------- #

def test_flat_undoes_the_dotted_filler() -> None:
    """Relics imprime el punto del formulario entre las palabras de la tarifa."""
    assert cotejo.fees_in("Hire Fee: .85.dinars.to.hire;.+.45.dinars.upkeep.cost .") \
        == [(85, "dinars", 45, "dinars")]


def test_fees_in_reads_both_printed_forms() -> None:
    assert cotejo.fees_in("75 warp tokens to hire +30 warp tokens upkeep") \
        == [(75, "warp tokens", 30, "warp tokens")]
    assert cotejo.fees_in("Hire Fee : 40GC, upkeep: 25GC") \
        == [(40, "gold crowns", 25, "gold crowns")]
    assert cotejo.fees_in("30 gold crowns to hire +15 upkeep") \
        == [(30, "gold crowns", 15, None)]


def test_unit_of_sees_the_unit_glued_to_the_amount() -> None:
    assert cotejo.unit_of("Hire Fee : 40GC") == "gold crowns"
    assert cotejo.unit_of("75 warp tokens") == "warp tokens"


def test_entries_keep_the_neighbour_column_out() -> None:
    """Dos entradas a dos columnas: cada una con su tarifa y su rating."""
    def block(left: int, name: str, fee: str, rating: str) -> list[dict]:
        return [
            line(name, [(left, 10, name.split()[0]), (left + 48, 10, name.split()[-1])]),
            line(fee, [(left + i, 20, token) for i, token in
                       enumerate(fee.split())]),
            line(f"Rating: A {name.title()} increases the warband's",
                 [(left, 30, "Rating:"), (left + 128, 30, "rating")]),
            line(f"rating by {rating} points, plus 1 point for each",
                 [(left, 40, "rating"), (left + 28, 40, rating), (left + 48, 40, "points,")]),
        ]

    found = cotejo.entries(block(72, "Halfling fence", "30 gold crowns to hire +15 gold crowns upkeep", "+15")
                           + block(470, "Halfling pimp", "20 gold crowns to hire +10 gold crowns upkeep", "+10"))
    assert [entry["heading"] for entry in found] == ["Halfling fence", "Halfling pimp"]
    assert cotejo.fees_in(found[1]["text"]) == [(20, "gold crowns", 10, "gold crowns")]
    assert cotejo.ratings_in(found[1]["text"]) == [10]
    assert "30 gold crowns" not in found[1]["text"]


def test_stat_row_is_read_in_table_order() -> None:
    """El Fire-Eater imprime ``4(6)`` y el extractor suelta la fila en dos líneas."""
    entry = {"line_words": [
        [(106, 100, "Profile"), (150, 100, "M"), (170, 100, "WS"), (200, 100, "BS"),
         (230, 100, "S"), (250, 100, "T"), (270, 100, "W"), (290, 100, "I"),
         (310, 100, "A"), (330, 100, "Ld")],
        [(121, 112, "(6)"), (150, 112, "2"), (162, 112, "3"), (174, 112, "3"),
         (186, 112, "4"), (198, 112, "2"), (210, 112, "2"), (222, 112, "1"),
         (234, 112, "7")],
        [(106, 124, "Fire-eater"), (200, 124, "4")],
    ], "text": ""}
    assert cotejo.stat_rows(entry) == ["423342217"]


def test_stat_row_without_the_word_profile() -> None:
    """Los Dramatis de Karak Azgal empiezan la tabla directamente en las columnas."""
    entry = {"line_words": [
        [(135, 700, "M"), (160, 700, "WS"), (185, 700, "BS"), (210, 700, "S"),
         (230, 700, "T"), (250, 700, "WI"), (280, 700, "A"), (300, 700, "LD")],
        [(129, 712, "Aldred"), (200, 712, "4"), (212, 712, "6"), (224, 712, "4"),
         (236, 712, "4"), (248, 712, "4"), (260, 712, "2"), (272, 712, "4"),
         (284, 712, "2"), (296, 712, "8")],
    ], "text": ""}
    assert cotejo.stat_rows(entry) == ["464442428"]


# --------------------------------------------------------------------------- #
# El cotejo real, contra los PDFs cacheados
# --------------------------------------------------------------------------- #

def run_cotejo(only: set[str], output: Path) -> list[dict]:
    """El informe del cotejo con la salida escrita fuera del árbol de build."""
    original_out, original_argv = cotejo.OUT, sys.argv
    cotejo.OUT = output
    sys.argv = ["check_2b_hirelings.py", *sorted(only)]
    try:
        assert cotejo.main() == 0
    finally:
        cotejo.OUT, sys.argv = original_out, original_argv
    return json.loads((output / "hirelings_check.json").read_text(encoding="utf-8"))


@CACHED
def test_adjudicated_cases_verify_every_check(tmp_path) -> None:
    """Los siete casos adjudicados cotejan hoy sin hallazgos ni chequeos de menos."""
    report = {entry["name"]: entry for entry in run_cotejo(set(ADJUDICATED), tmp_path)}
    assert set(report) == set(ADJUDICATED)
    for name, entry in report.items():
        assert entry["findings"] == [], name
        assert set(entry["checks"]) == set(CHECKS), name


@CACHED
def test_currency_regression_is_a_finding(tmp_path, monkeypatch) -> None:
    """La mutación: devolver la tarifa del Albino a coronas exige el hallazgo.

    Es el caso que la pasada cerró, así que la batería que hoy pasa tiene que
    fallar si alguien vuelve a convertir la divisa impresa: la tarifa impresa
    son 75 *warp tokens*, no 75 coronas.
    """
    document = yaml.safe_load(cotejo.CAMPAIGN_DOC.read_text(encoding="utf-8"))
    for entry in document["hired_swords"]:
        if entry["profile_id"] == "hireling.hired-sword.albino-stormvermin":
            entry["hiring_fee"]["resources"]["gold_crowns"]["cost"] = 75
            entry["upkeep"]["resources"]["gold_crowns"]["cost"] = 30
    mutated = tmp_path / "campaign.yaml"
    mutated.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    monkeypatch.setattr(cotejo, "CAMPAIGN_DOC", mutated)
    report = run_cotejo({"Albino Stormvermin"}, tmp_path)
    assert report and "fee" not in report[0]["checks"]
    assert "warp tokens" in " ".join(report[0]["findings"])
