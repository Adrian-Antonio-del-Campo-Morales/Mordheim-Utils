"""Guards for the shared registry of printed wordings (``tools/ingestion/printed_wordings``).

Los tres cotejos que comparan objetos contra una fuente —`audit_2a_sources.py`,
`audit_2b.py` y `audit_2ab_fidelity.py`— necesitan las mismas parejas: la palabra que la
fuente imprime para un objeto que el catálogo llama de otro modo («Holy Water» para
`blessed_water`, «Wardog» para `warhound`, «Halbard» para `halberd`…) y el motivo de la
lista que la fuente **delega** al reglamento. Estaban triplicadas, y una pareja
adjudicada en una tabla se quedaba sin ver en las otras; este módulo fija que el registro
es uno solo y que los tres lo leen, y las dos reglas de sitio del registro:

1. el árbol, la banda o la lista **en blanco en la pareja** valen para cualquiera (el
   arma a dos manos la imprimen el reglamento y los suplementos de los dos árboles);
2. la lista en blanco **en la consulta** pregunta por cualquiera de las listas de esa
   banda —lo que sabe el auditor de 2B, cuya tabla siempre fue por banda—, y una palabra
   registrada en un árbol no vale en el otro («Halbard» es la errata de los Forest
   Goblins, no la palabra de la página de 2A).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
# The 2A/2B ingestion tools live in tools/ingestion (temporary: see its README).
TOOLS = ROOT / "tools" / "ingestion"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

wordings = pytest.importorskip("printed_wordings")


# --------------------------------------------------------------------------- #
# El registro
# --------------------------------------------------------------------------- #

def test_every_pair_names_an_object_and_the_words_its_source_prints() -> None:
    """Una pareja sin palabra no registra nada y una palabra vacía no se lee."""
    for entry in wordings.WORDINGS:
        assert entry.item_id, entry
        assert entry.words, entry
        for word in entry.words:
            assert word and word == word.strip(), entry
        assert entry.tree in ('', '2A', '2B'), entry


def test_a_site_is_recorded_once() -> None:
    """Dos parejas para el mismo objeto y el mismo sitio serían dos verdades."""
    sites = [(entry.tree, entry.band, entry.list_id, entry.item_id)
             for entry in wordings.WORDINGS]
    assert len(sites) == len(set(sites))


# --------------------------------------------------------------------------- #
# Las dos reglas de sitio
# --------------------------------------------------------------------------- #

def test_a_pair_without_a_site_is_read_in_every_tree() -> None:
    """El arma a dos manos: la imprimen el reglamento y los suplementos de los dos."""
    two_handed = wordings.words_at('2B', 'dwarf-guildsmen-kaz', 'dwarf-warrior-equipment-list',
                                   'great_weapon')
    assert 'double handed weapon' in two_handed      # la lista enana del KAZ
    assert 'double-handed weapon' in two_handed      # la lista de los caballeros
    assert ('two-handed weapon' in
            wordings.words_for_item('great_weapon', '2A'))


def test_a_pair_scoped_to_a_list_is_not_read_in_its_neighbours() -> None:
    """«Holy Water» es la fila de esa lista, no la de cualquier lista de la banda."""
    assert wordings.words_at('2A', 'protectorate-of-sigmar-lotd3',
                             'protectorate-equipment-list', 'blessed_water') == ('Holy Water',)
    assert wordings.words_at('2A', 'protectorate-of-sigmar-lotd3',
                             'huntsman-equipment-list', 'blessed_water') == ()


def test_a_band_query_reads_every_list_of_the_band() -> None:
    """El auditor de 2B pregunta por la banda, que es lo que su tabla sabía."""
    assert wordings.words_at('2B', 'forest-goblins-lus', '', 'halberd') == ('Halbard',)
    assert wordings.words_at('2B', 'forest-goblins-lus', 'hero-equipment-list',
                             'halberd') == ('Halbard',)


def test_a_word_of_one_tree_is_not_read_in_the_other() -> None:
    """La errata de una fuente no es la palabra con que la otra imprime el objeto."""
    assert wordings.words_for_item('halberd', '2B') == ('Halbard',)
    assert wordings.words_for_item('halberd', '2A') == ()
    assert wordings.words_for_item('blessed_water', '2A') == ('Holy Water',)
    assert wordings.words_for_item('blessed_water', '2B') == ()


def test_the_pairs_of_a_band_come_with_their_object_and_their_words() -> None:
    """La pregunta del auditor de 2A: qué objeto de la lista imprime esa fila."""
    pairs = wordings.pairs_at('2A', 'protectorate-of-sigmar-lotd3',
                              'protectorate-equipment-list')
    assert {(entry.item_id, entry.words) for entry in pairs} == {
        ('blessed_water', ('Holy Water',)),
        ('sigmarite_hammer', ('Sigmarite Warhammer',)),
        ('great_weapon', ('double-handed weapon', 'double handed weapon', 'two-handed weapon')),
    }


# --------------------------------------------------------------------------- #
# La lista que la fuente delega al reglamento
# --------------------------------------------------------------------------- #

def test_the_delegated_lists_carry_their_reason() -> None:
    for band in ('skaven-of-clan-mors-kaz', 'skaven-of-clan-skryre-kaz'):
        reason = wordings.delegated_reason('2B', band, 'skaven-hero-equipment-list')
        assert reason and 'rulebook' in reason, band
    assert 'handgun' in wordings.delegated_reason(
        '2B', 'dwarf-guildsmen-kaz', 'thunderer-equipment-list')
    # Una lista que su documento sí imprime no está delegada.
    assert wordings.delegated_reason(
        '2B', 'knights-of-the-bitter-moors-mim', 'knights-equipment-list') is None


# --------------------------------------------------------------------------- #
# Los tres cotejos leen el mismo registro
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('name', ['audit_2a_sources', 'audit_2b', 'audit_2ab_fidelity'])
def test_the_three_audits_read_the_one_registry(name: str) -> None:
    """Un solo registro: ningún auditor lleva su propia tabla de palabras."""
    audit = pytest.importorskip(name)
    assert audit.wordings is wordings
    assert not hasattr(audit, 'SOURCE_WORDING')
    assert not hasattr(audit, 'RULEBOOK_DELEGATED')
    assert not hasattr(audit, 'ITEM_ALIASES')
