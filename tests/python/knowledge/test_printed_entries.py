"""Guards for the shared printed-entry reader (``tools/knowledge/printed_entries``).

The 2A and 2B source cotejos both compare *what a source prints* against *what the
package declares*, and both do it through this module. It is only worth a green
run of either cotejo if three things hold, and this module pins all three:

1. an entry is read with the geometry of its source — the neighbour column's fee,
   stat row and rating never count for the entry being checked, whether the
   geometry comes from a two-column PDF page or from the structure of a web page
   (one entry per ``div.fighter``, one cell per table column);
2. a stat row is compared in **table order** and survives a characteristic of two
   digits (Ld 10), while surplus digits that a shared physical line brought in from
   the neighbouring column are not read as the row;
3. a check that could not be compared is a **note** and lowers the coverage — it
   never passes for a green — and a printed fee in another currency than the
   package declares is a finding.

None of these need anything cached: the HTML and text corpora are built over
throwaway files under ``tmp_path``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
# El lector de entradas impresas es permanente: vive en tools/knowledge.
TOOLS = ROOT / "tools" / "knowledge"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

pe = pytest.importorskip("printed_entries")


# --------------------------------------------------------------------------- #
# La geometría de una página web
# --------------------------------------------------------------------------- #

FIGHTER = """<!doctype html><html><body>
<div class="nav">Grade 2A Dramatis Personae</div>
<div class="fighter">
  <h2 class="anchor">&#8220;Busty&#8221; Gwen</h2>
  <p><em>Source: Fanatic Online 89</em></p>
  <p><strong>Hire Fee:</strong> See special rules.</p>
  <p><strong>Rating:</strong> Gwen increases your warband rating by +40 points, plus
     1 point for each experience point she has.</p>
  <table><thead><tr><th>Profile</th><th>M</th><th>WS</th><th>BS</th><th>S</th><th>T</th>
    <th>W</th><th>I</th><th>A</th><th>Ld</th></tr></thead>
    <tbody><tr><td></td><td>4</td><td>4</td><td>1</td><td>4</td><td>4</td><td>2</td>
      <td>3</td><td>2</td><td>8</td></tr></tbody></table>
  <h4>SPECIAL RULES</h4>
  <p><strong>Massively Built:</strong> She may show her stuff to any visible male target.</p>
</div>
<div class="fighter">
  <h2 class="anchor">The Dark Jester in Mordheim</h2>
  <p><em>Source: Fanatic Online 17</em></p>
  <p>75 gold crowns to hire; +30 gold crowns upkeep cost.</p>
  <p><strong>Rating:</strong> The Dark Jester increases a warband&#8217;s rating by +55 points.</p>
  <table><thead><tr><th></th><th>M</th><th>WS</th><th>BS</th><th>S</th><th>T</th>
    <th>W</th><th>I</th><th>A</th><th>Ld</th></tr></thead>
    <tbody><tr><td>Jester</td><td>4</td><td>3</td><td>3</td><td>3</td><td>3</td><td>2</td>
      <td>6</td><td>2</td><td>7</td></tr></tbody></table>
  <h4>SPECIAL RULES</h4>
  <p><strong>Loner:</strong> He never has to test for being All-alone.</p>
</div>
</body></html>
"""


@pytest.fixture()
def page(tmp_path) -> pe.HtmlCorpus:
    path = tmp_path / "dramatis-grade-2a.html"
    path.write_text(FIGHTER, encoding="utf-8")
    return pe.HtmlCorpus(path)


def test_html_entries_are_split_by_the_document_structure(page) -> None:
    """Una entrada por `div.fighter`: la navegación no es una entrada."""
    assert [entry["heading"] for entry in page.entries()] == [
        "\u201cBusty\u201d Gwen", "The Dark Jester in Mordheim"]


def test_html_entry_reads_only_its_own_block(page) -> None:
    """La tarifa y el rating del vecino no cuentan (el defecto que 2A tenía)."""
    gwen, jester = page.entries()
    assert pe.fees_in(gwen["text"]) == []
    assert "75 gold crowns" not in gwen["text"]
    assert pe.ratings_in(gwen["text"]) == [40]
    assert pe.fees_in(jester["text"]) == [(75, "gold crowns", 30, "gold crowns")]
    assert pe.ratings_in(jester["text"]) == [55]


def test_html_stat_row_is_read_in_cell_order(page) -> None:
    """La fila se lee por celdas: el orden de la tabla, no el de la prosa."""
    gwen, jester = page.entries()
    assert pe.stat_rows(gwen) == ["441442328"]
    assert pe.stat_rows(jester) == ["433332627"]


def test_a_two_digit_characteristic_is_kept() -> None:
    """Ld 10 no cabe en nueve caracteres: truncar la fila perdería la última."""
    entry = {"line_words": [
        [(0, 0, "Profile"), (10, 0, "M"), (20, 0, "WS"), (30, 0, "BS"), (40, 0, "S"),
         (50, 0, "T"), (60, 0, "W"), (70, 0, "I"), (80, 0, "A"), (90, 0, "Ld")],
        [(0, 10, "4"), (10, 10, "5"), (20, 10, "3"), (30, 10, "4"), (40, 10, "3"),
         (50, 10, "3"), (60, 10, "5"), (70, 10, "2"), (80, 10, "10")],
    ], "text": ""}
    assert pe.stat_rows(entry) == ["4534335210"]


# --------------------------------------------------------------------------- #
# Una entrada de texto plano, con su ancla
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# La estructura de un documento cualquiera: encabezados, tramos y tablas
# --------------------------------------------------------------------------- #

DOCUMENT = """<!doctype html><html><body>
<h2>Druchii Equipment Lists</h2>
<h3>Corsair Equipment List</h3>
<table><thead><tr><th>Item</th><th>Cost</th></tr></thead><tbody>
  <tr><td>Sword</td><td>10 gc</td></tr>
  <tr><td>Sea Dragon Cloak</td><td>35 gc (70 for a brace)</td></tr>
</tbody></table>
<h3>Beastmaster Equipment List</h3>
<table><tbody><tr><td>Spear</td><td>5 gc</td></tr></tbody></table>
<h2>Special Rules</h2>
<p>Nothing here.</p>
</body></html>
"""


def test_document_reads_headings_with_their_span() -> None:
    """El tramo de un encabezado es el suyo y el de sus descendientes, no más."""
    doc = pe.HtmlDocument(DOCUMENT)
    assert [(heading.level, heading.text) for heading in doc.headings] == [
        (2, "Druchii Equipment Lists"), (3, "Corsair Equipment List"),
        (3, "Beastmaster Equipment List"), (2, "Special Rules")]
    corsair = doc.text(*doc.span(1))
    assert corsair == ("Corsair Equipment List Item Cost Sword 10 gc "
                       "Sea Dragon Cloak 35 gc (70 for a brace)")
    assert "Spear" not in corsair
    assert "Special Rules" not in corsair
    assert doc.text(*doc.span(0)).count("Equipment List") == 3  # el padre y sus hijos


def test_document_rows_are_read_by_cells() -> None:
    """Las filas llegan con sus celdas en el orden de las columnas y su tabla."""
    doc = pe.HtmlDocument(DOCUMENT)
    rows = doc.rows(*doc.span(1))
    assert [row.cells for row in rows] == [
        ("Item", "Cost"), ("Sword", "10 gc"),
        ("Sea Dragon Cloak", "35 gc (70 for a brace)")]
    assert [row.header for row in rows] == [True, False, False]
    # Cada tabla lleva su número: las filas de una no se mezclan con las de la otra.
    assert len({row.table for row in doc.rows()}) == 2
    assert doc.rows(*doc.span(2))[0].cells == ("Spear", "5 gc")


def test_document_finds_a_heading_by_level_and_text() -> None:
    doc = pe.HtmlDocument(DOCUMENT)
    assert doc.heading_span_of(2, "Special Rules") is not None
    assert doc.heading_span_of(3, "Spear") is None
    assert doc.text(*doc.heading_span_of(2, "Special Rules")) == "Special Rules Nothing here."


# --------------------------------------------------------------------------- #
# La tabla de características de un documento
# --------------------------------------------------------------------------- #

# Las páginas de 2A imprimen sus perfiles de las dos formas: con el nombre en la
# primera columna de la tabla (los Outlaws de Stirwood) o sin él, colgando del
# encabezado que titula la entrada y con el cupo delante (los Halflings).
PROFILES = """<!doctype html><html><body>
<h2>heroes</h2>
<h3>0 – 2 Snotling BigSnotz</h3>
<p>Little creatures.</p>
<table><thead><tr><th>Profile</th><th>M</th><th>WS</th><th>BS</th><th>S</th><th>T</th><th>W</th><th>I</th><th>A</th><th>Ld</th></tr></thead>
<tbody><tr><td>Goblin</td><td>4</td><td>5</td><td>6</td><td>4</td><td>4</td><td>2</td><td>7</td><td>4</td><td>9</td></tr></tbody></table>
<h3>1 Halfling Elder</h3>
<table><thead><tr><th>M</th><th>WS</th><th>BS</th><th>S</th><th>T</th><th>W</th><th>I</th><th>A</th><th>Ld</th></tr></thead>
<tbody><tr><td>4</td><td>3</td><td>5</td><td>3</td><td>3</td><td>1</td><td>5</td><td>1</td><td>–</td></tr></tbody></table>
<h3>Equipment</h3>
<table><thead><tr><th>Item</th><th>Cost</th></tr></thead><tbody><tr><td>Sword</td><td>10 gc</td></tr></tbody></table>
</body></html>"""


def test_characteristic_columns_are_read_by_their_titles() -> None:
    """La tabla se reconoce por los títulos de sus columnas, no por su primera fila."""
    assert pe.characteristic_columns(
        ("Profile", "M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")) == tuple(range(1, 10))
    assert pe.characteristic_columns(("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")) == \
        tuple(range(9))
    # Una columna que el catálogo no modela se reconoce por su título y queda fuera.
    assert pe.characteristic_columns(
        ("Profile", "M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Save")) == \
        tuple(range(1, 10))
    assert pe.characteristic_columns(("Item", "Cost")) is None
    assert pe.characteristic_columns(("M", "WS", "BS", "S", "T", "W", "I", "A")) is None


def test_cell_value_folds_the_dash_the_page_prints() -> None:
    """Las páginas imprimen el guion largo para la característica que no hay."""
    assert pe.cell_value("\u2013") == "-"
    assert pe.cell_value("\u2014") == "-"
    assert pe.cell_value(" 4 ") == "4"


def test_profile_row_takes_the_name_it_prints_or_leaves_it_to_the_table() -> None:
    """La fila lleva su nombre en la primera columna, o no lo lleva."""
    header = ("Profile", "M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")
    assert pe.profile_row(header, ("Goblin", "4", "5", "6", "4", "4", "2", "7", "4", "9")) == \
        ("Goblin", ("4", "5", "6", "4", "4", "2", "7", "4", "9"))
    # Sin la columna del nombre la fila imprime sólo sus nueve valores.
    assert pe.profile_row(header, ("4", "5", "6", "4", "4", "2", "7", "4", "9")) == \
        ("", ("4", "5", "6", "4", "4", "2", "7", "4", "9"))
    assert pe.profile_row(("Item", "Cost"), ("Sword", "10 gc")) is None


def test_profile_tables_read_every_row_of_every_characteristic_table() -> None:
    """La tabla de perfiles se lee del documento: una celda por columna."""
    assert pe.profile_tables(pe.HtmlDocument(PROFILES)) == [
        ("Goblin", ("4", "5", "6", "4", "4", "2", "7", "4", "9")),
        # El nombre lo lleva el encabezado que titula la entrada, sin su cupo.
        ("Halfling Elder", ("4", "3", "5", "3", "3", "1", "5", "1", "-")),
    ]


def test_stat_header_reads_the_table_that_titles_its_columns() -> None:
    """La cabecera de la tabla, con el título «Profile» delante o sin él."""
    words = [(0, 0, word) for word in "Profile M WS BS S T W I A Ld".split()]
    assert pe.stat_header(words)
    assert pe.stat_header([(0, 0, word) for word in "M WS BS S T W I A Ld".split()])
    assert not pe.stat_header([(0, 0, word) for word in "Item Cost".split()])
    assert not pe.stat_header([(0, 0, word) for word in "weapons armour".split()])


# --------------------------------------------------------------------------- #
# La línea física y sus celdas: lo que leen las tablas y las listas de precios
# --------------------------------------------------------------------------- #

def physical(*texts: str, top: int = 0) -> dict:
    """Una línea física: cada texto, una celda, con la extensión que ocupa."""
    spans, words, left = [], [], 0
    for text in texts:
        words.append((left, top, text))
        spans.append((left, top, left + 8 * len(text), text))
        left += 8 * len(text) + 40
    return {"text": " ".join(texts), "top": top, "left": 0, "words": words, "spans": spans}


def test_cells_split_the_line_where_the_gap_is_a_column() -> None:
    """La línea se corta donde el hueco es de columna; sin geometría es una sola."""
    assert [cell.text for cell in pe.cells(physical("Dagger", "2 gc"))] == ["Dagger", "2 gc"]
    assert [cell.text for cell in pe.cells({"text": "Dagger 2 gc"})] == ["Dagger 2 gc"]


def test_price_row_reads_the_name_and_the_price_of_its_own_cell() -> None:
    """Dos listas en la misma línea: cada ítem con su tarifa, no la del vecino."""
    rows = pe.price_rows([physical("Dagger", "2 gc", "Sword", "10 gc")])
    assert [(row["name"], row["prices"]) for row in rows] == [("Dagger", [2]), ("Sword", [10])]


def test_price_row_reads_the_name_that_covers_it_above() -> None:
    """El nombre cierra una línea y la tarifa abre la siguiente (celdas partidas)."""
    row = pe.price_rows([physical("Bramble"), physical("2 gc")])[0]
    assert (row["name"], row["prices"], row["above"]) == ("Bramble", [2], "Bramble")


def test_price_row_without_a_name_is_not_baptised_by_its_neighbour() -> None:
    """Una cifra suelta se devuelve sin nombre, no con el de la línea de al lado."""
    rows = pe.price_rows([physical("Bramble"), physical("2 gc"), physical("42 gc", top=400)])
    assert (rows[1]["name"], rows[1]["prices"]) == ("", [42])


def test_price_row_keeps_the_formula_it_prints() -> None:
    """«75+5D6 gold crowns» guarda su cifra base y se declara fórmula."""
    row = pe.price_rows([physical("Ratling Gun", "75+5D6 gold crowns")])[0]
    assert (row["name"], row["prices"], row["formula"]) == ("Ratling Gun", [75], True)


def test_price_rows_read_every_row_the_line_prints() -> None:
    """La lista de tres columnas pone tres filas a la misma altura, cada una la suya."""
    rows = pe.price_rows([physical("Axe 5 gc", "Gromril Weapon 3x the cost",
                                   "Dagger 1st free/2gc")])
    assert [(row["name"], row["prices"], row["formula"]) for row in rows] == [
        ("Axe", [5], False), ("Gromril Weapon", [], True), ("Dagger 1st free", [2], False)]


def test_price_row_reads_the_multiplier_that_rates_with_another_price() -> None:
    """«Gromril Weapon 3x the cost»: la cifra multiplica, no tasa, y el nombre es de la celda."""
    row = pe.price_rows([physical("Gromril Weapon 3x the cost")])[0]
    assert (row["name"], row["prices"], row["formula"]) == ("Gromril Weapon", [], True)


def test_price_row_reads_the_multiplier_written_the_other_way_round() -> None:
    """«Ithilmar Weapon» con «Price x 2*» debajo: el nombre es el que la cubre."""
    row = pe.price_rows([physical("Ithilmar Weapon"), physical("Price x 2*")])[0]
    assert (row["name"], row["prices"], row["formula"]) == ("Ithilmar Weapon", [], True)


# La tabla de equipo de una página web, con las dos formas de tasa que imprime: el
# importe y el multiplicador del precio de otro objeto («2 x price»).
COSTS = """<!doctype html><html><body>
<h2>Equipment</h2>
<table><thead><tr><th>Item</th><th>Cost</th></tr></thead><tbody>
<tr><td>Ithilmar weapon *</td><td>2 x price</td></tr>
<tr><td>Ithilmar armour *</td><td>60 gc</td></tr>
<tr><td>Hand-to-hand Combat Weapons</td><td>Missile Weapons</td></tr>
</tbody></table>
</body></html>"""


def test_list_rows_read_a_multiplier_and_not_the_column_headers() -> None:
    """La fila de la lista se reconoce por su tasa; el encabezado de columna no es una."""
    assert pe.list_rows(pe.HtmlDocument(COSTS)) == [("Ithilmar weapon *", "2 x price"),
                                                    ("Ithilmar armour *", "60 gc")]


# --------------------------------------------------------------------------- #
# La cobertura de un cotejo con muchas unidades
# --------------------------------------------------------------------------- #

def test_ledger_declares_what_it_compared() -> None:
    """La línea dice unidades, valores, fallos, lo no comparable y el detalle."""
    ledger = pe.Ledger({"lists": ("listas", "filas")})
    ledger.cover("lists", 3)
    ledger.count("lists", ok=True, values=10)
    ledger.count("lists", ok=False, values=2)
    ledger.unobtainable("lists")
    ledger.detail("lists", "bajo un h2", 2)
    assert ledger.line() == ("cobertura por chequeo: lists 10/12 filas en 3 listas "
                            "(1 sin comparar) [bajo un h2: 2]")
    ledger.reset()
    assert ledger.measures["lists"].values == 0
    assert ledger.line() == "cobertura por chequeo: lists 0/0 filas"


def test_ledger_keeps_one_measure_per_check() -> None:
    """Cada chequeo lleva su propia cuenta: uno sin valores no hereda la del otro."""
    ledger = pe.Ledger({"a": ("bandas", "valores"), "b": ("listas", "filas")})
    ledger.cover("a")
    ledger.count("a", ok=True)
    assert list(ledger.measures) == ["a", "b"]
    assert (ledger.measures["a"].units, ledger.measures["a"].values) == (1, 1)
    assert ledger.measures["b"].values == 0
    assert "a 1/1 valores en 1 bandas" in ledger.line()
    assert "b 0/0 filas" in ledger.line()


def test_text_entries_start_at_the_declared_anchor(tmp_path) -> None:
    """En el texto de 2A cada entrada abre con su `Source:` y su nombre encima."""
    path = tmp_path / "dramatis-grade-2a.txt"
    path.write_text(
        "Grade 2A Dramatis Personae\n"
        "The Foole\n"
        "Source: Fanatic Online 89\n"
        "40 gold crowns to hire.\n"
        "Rating:\n"
        " The Foole increases the warband's rating by +30 points.\n"
        "Profile\nM\nWS\nBS\nS\nT\nW\nI\nA\nLd\n"
        "4\n4\n4\n4\n3\n1\n4\n1\n7\n"
        "Sigmund Spindle, the Harvester of Flesh\n"
        "Source: Sylvania Supplement\n"
        "70 gold crowns to hire, +35 gold crowns upkeep cost.\n",
        encoding="utf-8")
    entries = pe.TextCorpus(path).entries()
    assert [entry["heading"] for entry in entries] == ["The Foole",
                                                      "Sigmund Spindle, the Harvester of Flesh"]
    assert pe.fees_in(entries[0]["text"]) == [(40, "gold crowns", None, None)]
    assert pe.fees_in(entries[1]["text"]) == [(70, "gold crowns", 35, "gold crowns")]
    # Sin geometría la fila se lee igual, pero sólo si sus dígitos son inequívocos.
    assert pe.stat_rows(entries[0]) == ["444431417"]


# --------------------------------------------------------------------------- #
# Cómo se comparan los cuatro datos
# --------------------------------------------------------------------------- #

def entry(text: str = "", **line_words) -> dict:
    return {"heading": "", "lines": [text], "line_words": line_words.get("line_words") or [],
            "text": text, "spillover": ""}


def printed(**kwargs) -> dict:
    return entry(**kwargs)


def test_a_printed_fee_in_another_currency_is_a_finding() -> None:
    """La divisa impresa se compara: 75 warp tokens no son 75 coronas."""
    coverage = pe.Coverage()
    pe.compare(entry("75 warp tokens to hire +30 warp tokens upkeep"), pe.Package(
        fee=pe.Fee(75, "gold crowns"), upkeep=pe.Fee(30, "gold crowns")), coverage)
    assert "fee" not in coverage.verified
    assert any("warp tokens" in finding for finding in coverage.report()["findings"])


def test_a_fee_that_neither_side_declares_verifies_by_absence() -> None:
    """Gwen cobra por el escenario, no una tarifa: la ausencia es el cotejo."""
    coverage = pe.Coverage()
    pe.compare(entry("Hire Fee: See special rules."), pe.Package(), coverage)
    assert "fee" in coverage.verified


def test_a_datum_only_one_side_declares_is_a_note_not_a_finding() -> None:
    """Lo que no se pudo comparar baja la cobertura y se explica; no es un verde."""
    coverage = pe.Coverage()
    pe.compare(entry("No fee here."), pe.Package(fee=pe.Fee(40, "gold crowns")), coverage)
    report = coverage.report()
    assert report["findings"] == []
    assert "fee" not in report["checks"]
    assert any("no imprime tarifa" in note for note in report["notes"])


def test_a_stat_row_with_surplus_digits_from_the_shared_line_still_matches() -> None:
    """El Warrior-Priest imprime su fila y un `3"` de la prosa contigua en la misma línea."""
    coverage = pe.Coverage()
    pe.compare(entry("", line_words=[
        [(0, 0, "Profile"), (10, 0, "M"), (20, 0, "WS"), (30, 0, "BS"), (40, 0, "S"),
         (50, 0, "T"), (60, 0, "W"), (70, 0, "I"), (80, 0, "A"), (90, 0, "Ld")],
        [(0, 10, "Warrior-priest"), (10, 10, "4"), (20, 10, "3"), (30, 10, "3"),
         (40, 10, "3"), (50, 10, "3"), (60, 10, "1"), (70, 10, "3"), (80, 10, "1"),
         (90, 10, "8")],
        [(0, 12, "3"), (10, 12, '"')],
    ]), pe.Package(stats="433331318"), coverage)
    assert "stats" in coverage.verified
    assert coverage.report()["findings"] == []


def test_a_different_stat_row_is_a_finding() -> None:
    coverage = pe.Coverage()
    pe.compare(entry("", line_words=[
        [(0, 0, "Profile"), (10, 0, "M"), (20, 0, "WS"), (30, 0, "BS"), (40, 0, "S"),
         (50, 0, "T"), (60, 0, "W"), (70, 0, "I"), (80, 0, "A"), (90, 0, "Ld")],
        [(0, 10, "4"), (10, 10, "2"), (20, 10, "3"), (30, 10, "3"), (40, 10, "3"),
         (50, 10, "1"), (60, 10, "3"), (70, 10, "1"), (80, 10, "8")],
    ]), pe.Package(stats="433331318"), coverage)
    assert "stats" not in coverage.verified
    assert any("stats impresas" in finding for finding in coverage.report()["findings"])


def test_a_rule_is_compared_one_by_one() -> None:
    """Una etiqueta que no aparece es un hallazgo, no lo tapa otra que sí."""
    coverage = pe.Coverage()
    pe.compare(entry("Fear: it causes fear. Daemonic Flesh: 5+ save."),
               pe.Package(rules=("Fear", "Aethereal Hoarder")), coverage)
    findings = coverage.report()["findings"]
    assert any("Aethereal Hoarder" in finding for finding in findings)
    assert not any("'Fear'" in finding for finding in findings)


def test_an_editorial_label_is_a_note_with_its_reason() -> None:
    """La etiqueta que el árbol escribe y la fuente imprime con otro nombre."""
    coverage = pe.Coverage()
    pe.compare(entry("May Be Hired: any good-aligned warband may hire him on a 4+."),
               pe.Package(rules=("Conditional Acceptance — Good-Aligned Employers",)),
               coverage, editorial={"Conditional Acceptance — Good-Aligned Employers":
                                    "la fuente la imprime como «May Be Hired»"})
    report = coverage.report()
    assert report["findings"] == []
    assert "rules" in report["checks"]
    assert any("May Be Hired" in note for note in report["notes"])


def test_two_sources_must_both_agree() -> None:
    """El paquete tiene que coincidir con cada fuente que imprime el dato."""
    agree, disagree = pe.Coverage(), pe.Coverage()
    pe.compare(entry("30 gold crowns to hire"), pe.Package(fee=pe.Fee(30, "gold crowns")), agree)
    pe.compare(entry("50 gold crowns to hire"), pe.Package(fee=pe.Fee(30, "gold crowns")),
               disagree)
    merged = pe.merge([agree, disagree])
    assert "fee" not in merged.verified
    assert any("tarifa impresa" in finding for finding in merged.report()["findings"])


def test_merge_is_the_identity_for_one_source() -> None:
    single = pe.Coverage()
    pe.compare(entry("30 gold crowns to hire", line_words=[
        [(0, 0, "Profile"), (10, 0, "M"), (20, 0, "WS"), (30, 0, "BS"), (40, 0, "S"),
         (50, 0, "T"), (60, 0, "W"), (70, 0, "I"), (80, 0, "A"), (90, 0, "Ld")],
        [(0, 10, "4"), (10, 10, "3"), (20, 10, "3"), (30, 10, "3"), (40, 10, "3"),
         (50, 10, "1"), (60, 10, "3"), (70, 10, "1"), (80, 10, "8")],
    ]), pe.Package(stats="433331318", fee=pe.Fee(30, "gold crowns"),
                   upkeep=pe.Fee(0, "gold crowns")), single)
    assert pe.merge([single]).report() == single.report()


# --------------------------------------------------------------------------- #
# La tarifa que el paquete declara y el índice del documento
# --------------------------------------------------------------------------- #

def test_package_fee_reads_the_printed_expression() -> None:
    """El contrato guarda la expresión impresa cuando no se cobra en coronas."""
    assert pe.package_fee({"resources": {"gold_crowns": {"cost": 20}}}) == pe.Fee(20, "gold crowns")
    assert pe.package_fee({"resources": {"gold_crowns": {"cost": "40 dinars"}}}) \
        == pe.Fee(40, "dinars")
    assert pe.package_fee({"resources": {"warp_tokens": {"cost": "75 warp tokens"}}}) \
        == pe.Fee(75, "warp tokens")
    assert pe.package_fee(None) is None


def test_fee_index_reads_both_contract_blocks(tmp_path) -> None:
    path = tmp_path / "hired-swords-and-dramatis.yaml"
    path.write_text(yaml.safe_dump({
        "hired_swords": [{"profile_id": "hireling.hired-sword.bard",
                          "hiring_fee": {"resources": {"gold_crowns": {"cost": 20}}}}],
        "dramatis_personae": [{"profile_id": "hireling.dramatis.the-foole",
                               "hiring_fee": {"resources": {"gold_crowns": {"cost": 40}}}}],
    }, sort_keys=False), encoding="utf-8")
    index = pe.fee_index(path)
    assert set(index) == {"hireling.hired-sword.bard", "hireling.dramatis.the-foole"}
    assert pe.package_fee(index["hireling.dramatis.the-foole"]["hiring_fee"]) \
        == pe.Fee(40, "gold crowns")
