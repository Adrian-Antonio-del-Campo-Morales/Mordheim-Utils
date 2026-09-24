"""Guards for the printed-row reading of the 2A/2B fidelity audit.

``tools/ingestion/audit_2ab_fidelity.py`` asks every printed table row two
questions: *does the page print a row the package does not model?* and, before
that, *is what it read really a row?* The audit now reads those rows from the
page's own structure — the physical line and the cells it prints, the reading
order of the column, and the tables of a web page — instead of a window of nine
consecutive tokens of the flattened text, and this module pins the rules that
change makes load bearing:

1. the row's **name** is the one printed in the cell that carries its values, in
   the cell before them («Thieves.» | «Halfling» | «4 5 7 3 3 3 9 4 10») or in the
   heading that titles a table whose rows print no name at all («1 Halfling
   Elder»), and never the tail of the prose the neighbouring column leaves at the
   same height («… their ascension. They» | «Spirit 5 5 0 4 3 4 5 3 9»);
2. the values of a row are split across cells («Dwarf 3 3» | «2» | «3 4 1 2 1 9»)
   and are read as **values**: a dash is a characteristic the row does not have,
   the parenthetical of «Giant Spider 7 3 0 3(4) 3 1 4 1 4» is a variant and not a
   tenth value, and what the line prints after them is the neighbouring column's
   prose; the treasure table the KAZ pages carry («D3 Gems worth 10 gc each 4+»)
   still never reaches nine values;
3. a printed name that matches a profile the active KB defines only counts as
   modelled when the KB also carries those characteristics — the KB's «Boss»
   (4 3 4 3 3 1 4 1 7) does not cover the KAZ's printed «Boss»
   (4 4 3 4 4 1 3 1 8).

The first two are fixture tests. The last ones read the cached PDFs and web pages
(``build/cache/2b-pdfs`` and ``build/cache/2a-sources``, not versioned) and skip
when they are absent, exactly like the ingest tool they guard.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
# The 2A/2B ingestion tools live in tools/ingestion (temporary: see its README).
TOOLS = ROOT / "tools" / "ingestion"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

pe = pytest.importorskip("printed_entries")
# El registro compartido de las palabras que una fuente imprime para un objeto del
# catálogo: una sola tabla para los tres cotejos (`test_printed_wordings.py` fija el
# registro y aquí se fija lo que el cotejo hace con él).
pw = pytest.importorskip("printed_wordings")

spec = importlib.util.spec_from_file_location(
    "audit_2ab_fidelity", ROOT / "tools/ingestion/audit_2ab_fidelity.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

Cell = pe.Cell


def cells(*texts: str) -> list:
    """Las celdas de una línea física, de izquierda a derecha."""
    return [Cell(left, left + 10 * len(text), text)
            for left, text in enumerate(texts) if text]


# --------------------------------------------------------------------------- #
# El nombre de la fila
# --------------------------------------------------------------------------- #

def test_row_name_is_the_one_the_cell_with_the_numbers_prints() -> None:
    """La prosa que la columna vecina deja en la línea no bautiza la fila."""
    found = cells("artefact or incantation necessary for their ascension. They",
                  "Spirit 5 5 0 4 3 4 5 3 9")
    assert audit.printed_row(found) == ("Spirit", ("5", "5", "0", "4", "3", "4", "5", "3", "9"))


def test_row_with_the_numbers_in_later_cells_keeps_its_own_name() -> None:
    """El extractor parte la fila: el nombre sigue en la celda que abre la fila."""
    assert audit.printed_row(cells("Boss", "4", "4 3 4 4 1 3 1 8")) == \
        ("Boss", ("4", "4", "3", "4", "4", "1", "3", "1", "8"))


def test_a_heading_is_not_a_row() -> None:
    """La cabecera de la tabla no imprime cifras y no es una fila."""
    assert audit.printed_row(cells("Profile M WS BS S T W I A Ld")) is None


# --------------------------------------------------------------------------- #
# Las cifras de la fila
# --------------------------------------------------------------------------- #

def test_numbers_split_across_cells_are_read_in_order() -> None:
    """«Dwarf 3 3» | «2» | «3 4 1 2 1 9» es una fila de nueve cifras."""
    assert audit.printed_row(cells("Dwarf 3 3", "2", "3 4 1 2 1 9")) == \
        ("Dwarf", ("3", "3", "2", "3", "4", "1", "2", "1", "9"))


def test_the_treasure_table_is_not_a_stat_row() -> None:
    """La tabla de tesoros del KAZ: «D3 Gems worth 10 gc each 4+» no es un perfil."""
    found = cells("D3 Gems worth 10 gc each 4+", "(5 5 5 5 5 5) Warrior Training Ground")
    assert audit.printed_row(found) is None


def test_the_neighbouring_column_is_not_a_tenth_value() -> None:
    """La distancia que la columna vecina deja a la misma altura no es un valor.  """
    assert audit.printed_row(cells('Warrior-priest 4 3 3 3 3 1 3 1 8', '3"')) == \
        ('Warrior-priest', ('4', '3', '3', '3', '3', '1', '3', '1', '8'))


def test_a_row_that_prints_a_parenthetical_reads_its_base_value() -> None:
    """«Giant Spider 7 3 0 3(4) 3 1 4 1 4»: el paréntesis es la variante, no un valor."""
    assert audit.printed_row(cells('Giant Spider 7 3 0 3(4) 3 1 4 1 4')) == \
        ('Giant Spider', ('7', '3', '0', '3', '3', '1', '4', '1', '4'))


def test_a_row_whose_name_is_in_the_cell_before_it() -> None:
    """«Thieves.» | «Halfling» | «4 5 7 3 3 3 9 4 10»: el nombre es el de la celda vecina."""
    assert audit.printed_row(cells('Thieves.', 'Halfling', '4 5 7 3 3 3 9 4 10')) == \
        ('Halfling', ('4', '5', '7', '3', '3', '3', '9', '4', '10'))


# --------------------------------------------------------------------------- #
# La fila que la página imprime sin su nombre
# --------------------------------------------------------------------------- #

def test_row_values_stop_where_the_line_stops_printing_values() -> None:
    """Lo que la columna vecina deja a la misma altura no es un décimo valor."""
    assert audit.row_values(["5 5 5 4 4 1 7 1 8 Same as Hired"]) == \
        ["5", "5", "5", "4", "4", "1", "7", "1", "8"]
    assert audit.row_values(["D3 Gems worth 10 gc each 4+"]) == ["D3"]
    # Un guion es una característica que la fila no tiene y cuenta como uno.
    assert audit.row_values(["- 3 0 2 2 1 4 1 8"]) == \
        ["-", "3", "0", "2", "2", "1", "4", "1", "8"]


def test_column_row_reads_the_line_that_is_the_row_and_nothing_else() -> None:
    """Las páginas a dos columnas imprimen la fila en su propia línea."""
    assert audit.column_row("4 4 4 3 3 1 4 1 8") == ("4", "4", "4", "3", "3", "1", "4", "1", "8")
    assert audit.column_row("4 4 5 2 2 3 3 1 10") == ("4", "4", "5", "2", "2", "3", "3", "1", "10")
    assert audit.column_row("Profile M WS BS S T W I A Ld") is None
    # Con el nombre delante la línea no es la fila: eso lo lee ``printed_row``.
    assert audit.column_row("Mamluks 4 4 4 3 3 1 3 1 7") is None


# La entrada que el lector compartido arma para los Dramatis de Karak Azgal y las
# páginas a dos columnas de Relics of the Crusades.
ENTRY = {"heading": "0-1 Scholar", "lines": [
    "0-1 Scholar", "30 dinars to hire",
    "The reputation of the scholars of Araby extends throughout.",
    "therefore a very difficult one.", "Profile M WS BS S T W I A Ld", "4 2 2 3 3 1 3 1 7"]}


def test_entry_row_takes_the_name_of_the_heading_that_titles_the_table() -> None:
    """La fila de la entrada no imprime su nombre: lo lleva su encabezado."""
    assert audit.entry_row(ENTRY) == ("Scholar", ("4", "2", "2", "3", "3", "1", "3", "1", "7"))
    assert audit.entry_row({"heading": "Scholar", "lines": ["Profile M WS BS S T W I A Ld"]}) is None


def test_title_above_skips_the_price_the_prose_and_the_column_header() -> None:
    """El título de la tabla no es la tarifa ni la prosa que la antecede."""
    lines = [{"text": text} for text in ENTRY["lines"]]
    assert audit.title_above(lines, 5) == "Scholar"
    assert audit.title_above([{"text": "SPECIAL RULES"}, {"text": "Profile M WS"}], 1) == ""


def test_name_before_reads_the_cell_that_names_the_row() -> None:
    """«Thieves.» | «Halfling» | «4 5 7 3 3 3 9 4 10»: el nombre es el de al lado."""
    assert audit.name_before(cells("Thieves.", "Halfling")) == "Halfling"
    assert audit.name_before(cells("4 5 7 3 3 3 9 4 10")) == ""


# --------------------------------------------------------------------------- #
# El objeto contra la fila de la lista
# --------------------------------------------------------------------------- #

def test_a_list_row_matches_the_name_with_the_source_punctuation() -> None:
    """La fila lleva la decoración y la puntuación de la fuente, no las del catálogo."""
    assert audit.in_list("blunderbuss", ["Blunderbuss*"])
    assert audit.in_list("lock picks", ["Lock picks**"])
    assert audit.in_list("cat o' nine tails", ["Cat O\u2019 Nine Tails"])
    assert audit.in_list("double-handed weapon", ["Double Handed Weapon"])
    assert not audit.in_list("blunderbuss", ["Handgun*"])


def test_a_cell_that_prints_two_objects_names_both_of_them() -> None:
    """«Mace/Hammer»: la celda que imprime dos objetos nombra a los dos."""
    assert audit.in_list("mace", ["Mace/Hammer"])
    assert audit.in_list("hammer", ["Mace/Hammer"])
    assert audit.in_list("shield", ["Shield/Buckler"])
    assert not audit.in_list("spear", ["Mace/Hammer"])


def test_a_combined_entry_matches_the_order_the_list_prints_it_in() -> None:
    """El catálogo nombra la entrada combinada «Mace Hammer» y la página «Hammer/Mace»."""
    assert audit.in_list("mace hammer", ["Hammer/Mace . . . . 3 gc"])
    assert audit.in_list("staff club mace", ["Hammer mace staff club"])
    assert not audit.in_list("mace hammer", ["Sword . . . . 10 gc"])


def test_a_name_composed_with_a_dash_needs_both_of_its_parts() -> None:
    """«Swivel Gun — Ball Shot»: la lista titula el padre y tasa la variante."""
    labels = ["Swivel Gun . . . . 65 gc", "Ball Shot . . . . 5 gc"]
    assert audit.in_list("Swivel Gun \u2014 Ball Shot", labels)
    assert not audit.in_list("Swivel Gun \u2014 Chain Shot", labels)


# La palabra con que una fuente imprime el nombre de un objeto del catálogo, leída en la
# fila verbatim de la que se adjudicó con su tarifa (§9 de los verdictos de 2A y §15.4 de
# los de 2B). La pareja vive en el registro compartido y es lo que hace que el objeto
# cuente como impreso cuando el catálogo lo llama de otro modo.
SOURCE_WORDING_ROWS = {
    ('2A', 'blessed_water', 'Holy Water'): 'Holy Water . . . . . . . . . . . . . 5 gc*',
    ('2A', 'sigmarite_hammer', 'Sigmarite Warhammer'):
        'Sigmarite Warhammer . . . . . . . . 15 gc*',
    ('2B', 'horsemans_hammer', 'Horsemens Hammer'):
        'Horsemens Hammer . . . . . . . . . . . . 30GC',
    ('2B', 'warhound', 'Wardog'): 'Wardog',
    ('2B', 'warp_pistol', 'Warplock Pistol'):
        'Warplock Pistol . . . . . . . 35 gc (70 for a brace)',
    ('2B', 'halberd', 'Halbard'): 'Halbard   10 gc',              # errata de la fuente
    ('2B', 'superior_blackpowder', 'Superiour Black Powder'):
        'Superiour Black Powder.....................................20gc',
    ('2B', 'two_handed_weapon', 'Double-handed weapon'):
        'Double-handed weapon................................. 15 gc',
    ('2B', 'great_weapon', 'double handed weapon'): 'Double Handed Weapon 15 gc',
    ('2B', 'great_weapon', 'two-handed weapon'): 'Two-handed Weapon                     10 gc',
}


@pytest.mark.parametrize('site,row', SOURCE_WORDING_ROWS.items())
def test_every_recorded_source_wording_reads_its_own_printed_row(site, row) -> None:
    """Cada palabra registrada está en el registro y se lee en la fila de la que salió."""
    tree, item_id, word = site
    assert word in pw.words_for_item(item_id, tree or '2A'), site
    assert audit.in_list(word, [row]), site


def test_a_recorded_word_does_not_invent_a_row_the_list_does_not_print() -> None:
    """El registro es un cotejo, no un comodín: sin fila no hay acierto."""
    assert not audit.in_list('Wardog', ['Wardancers . . . . 35 gc'])
    assert not audit.in_list('Holy Water', ['Holy Relic . . . . 15 gc*'])
    assert not audit.in_list('Halbard', ['Halberd . . . . 10 gc'])


def test_the_list_the_source_delegates_is_adjudicated_not_a_hole() -> None:
    """El KAZ no imprime lista skaven: la remite al reglamento y se declara (§7)."""
    reason = pw.delegated_reason('2B', 'skaven-of-clan-mors-kaz', 'skaven-hero-equipment-list')
    assert reason and 'rulebook' in reason
    assert pw.delegated_reason('2B', 'skaven-of-clan-skryre-kaz', 'skaven-hero-equipment-list')
    # La adjudicación es de la lista delegada, no de cualquier objeto sin fila.
    assert pw.delegated_reason('2B', 'knights-of-the-bitter-moors-mim',
                               'knights-equipment-list') is None
    # Y el cotejo la usa: es el mismo registro, no una copia.
    assert audit.wordings.delegated_reason is pw.delegated_reason
    assert audit.wordings.words_for_item is pw.words_for_item


# --------------------------------------------------------------------------- #
# El perfil que el KB define
# --------------------------------------------------------------------------- #

KB = ({("4", "3", "4", "3", "3", "1", "4", "1", "7")}, {"Boss"})


def test_the_kb_covers_a_row_only_with_its_name_and_its_characteristics() -> None:
    assert audit.kb_models_row("Boss", ("4", "3", "4", "3", "3", "1", "4", "1", "7"), KB)
    assert not audit.kb_models_row("Boss", ("4", "4", "3", "4", "4", "1", "3", "1", "8"), KB)


# --------------------------------------------------------------------------- #
# La tabla real, contra los PDFs cacheados
# --------------------------------------------------------------------------- #

# La caché es lo que falta en un checkout sin descargas: `page_reader` devuelve un
# lector mientras el árbol declare su documento, y `source_groups` lee el manifiesto
# versionado, así que ninguno de los dos detecta la ausencia de caché.
CACHE = ROOT / "build" / "cache"
CACHED = pytest.mark.skipif(
    not (CACHE / "2b-pdfs" / "text-geometry").is_dir()
    or not (CACHE / "2a-sources" / "pages" / "halflings-mic.html").is_file(),
    reason="2A pages and 2B PDFs are not cached (offline checkout)",
)


@CACHED
def test_the_printed_table_gives_every_row_its_printed_name() -> None:
    """Los ocho paquetes del KAZ comparten documento: la fila se lee con su nombre."""
    rows = {row: name for name, row in audit.printed_stat_rows("2B", "dwarf-slayers-kaz")}
    assert rows[("4", "4", "3", "4", "4", "1", "3", "1", "8")] == "Boss"
    assert rows[("7", "3", "0", "3", "4", "1", "3", "1", "3")] == "War Boar"
    assert rows[("4", "6", "4", "4", "4", "2", "4", "2", "8")] == "Aldred"
    assert ("3", "10", "4", "5", "5", "5", "5", "5", "5") not in rows


@CACHED
def test_the_two_column_chapter_gives_every_row_its_entry_name() -> None:
    """Relics of the Crusades: la tabla vive en la columna de su entrada."""
    rows = {row: name for name, row in audit.printed_stat_rows("2B", "ghutani-rel")}
    assert rows[("4", "4", "4", "3", "3", "1", "4", "1", "8")] == "Emir"
    assert rows[("4", "2", "2", "3", "3", "1", "3", "1", "7")] == "Scholar"
    assert rows[("4", "3", "2", "3", "3", "1", "3", "1", "6")] == "Townsman"


@CACHED
def test_the_web_page_gives_every_row_its_profile_name() -> None:
    """Los Halflings imprimen la tabla sin nombre: lo lleva el encabezado del perfil."""
    rows = {row: name for name, row in audit.printed_stat_rows("2A", "halflings-mic")}
    assert rows[("4", "3", "5", "3", "3", "1", "5", "1", "9")] == "Halfling Elder"
    assert rows[("5", "4", "0", "3", "4", "1", "3", "1", "4")] == "Piggies"
    # Los familiares imprimen su característica ausente con un guion largo.
    familiars = {row: name for name, row in audit.printed_stat_rows("2A", "sorcerous-society-lotd4")}
    assert familiars[("6", "4", "-", "3", "3", "1", "4", "1", "5")] == "Dog"
