"""Guards for the permanent hireling source cotejo (``tools/knowledge/check_hireling_sources``).

El cotejo compara cada entrada impresa de una página o de un PDF con el perfil de su
catálogo y con su entrada de contratación. Vale la pena por tres cosas, y este módulo
fija las tres:

1. **La entrada impresa se lee como la imprime el documento**: en una página, un bloque
   por personaje (``div.fighter``) y las celdas de su tabla; en un PDF, por geometría, con
   la columna izquierda antes que la derecha. La tarifa, la fila y el rating del vecino
   nunca cuentan para la entrada cotejada —la lectura plana daba a ``“Busty” Gwen`` los
   75/30 del Dark Jester y al Foole los 70/35 de Sigmund, y la columna vecina de un PDF
   daba al Fire-Eater el +30 de la hermana—;
2. **cada entrada resuelve su documento**: la URL de sus ``source_refs`` resuelve en el
   registro de documentos fuente —el de la KB, no una tabla del tool— y el registro se
   exige completo sobre los catálogos de las dos familias.

Las dos familias publicadas (``hired-swords`` y ``dramatis-personae``)
se cotejan con la misma lectura del catálogo canónico. Las pruebas que leen documentos
reales no forman parte de este módulo: ``sources/origins`` no está versionado, así que
solo pueden ejecutarse en un checkout que tenga las copias.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# El cotejo y sus dos piezas viven en el utillaje permanente de la KB.
TOOLS = ROOT / "tools" / "knowledge"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

cotejo = pytest.importorskip("check_hireling_sources")
source_documents = pytest.importorskip("source_documents")

#: El catálogo publicado de la KB.
KB = cotejo.CATALOGUES["kb"]

# El registro declara los documentos; el espejo dice si la copia está descargada y dónde.
DOCUMENTS = cotejo.SOURCE_DOCUMENTS
SPECIALISTS = DOCUMENTS.by_id("broheim.mutinyinmarienburg.specialists")

def line(text: str, words: list[tuple[int, int, str]]) -> dict:
    """Una línea física tal y como la devuelve la lectura por geometría."""
    return {"text": text, "top": 0, "left": min((w[0] for w in words), default=0),
            "words": words}


# De la entrada al documento fuente: el registro, no una tabla del tool

def test_the_public_catalogue_has_both_families() -> None:
    """El cotejo permanente cubre las dos familias y todos los grados del catálogo.

    Los dos drivers de la fase de ingesta cubrían una familia cada uno —los Dramatis
    Personae de la KB por un lado y los hirelings de 2B por otro— y los 72 hired
    swords publicados no los cotejaba nadie; la orden de la KB los recorre todos.
    """
    families = {profile["_file"].split("/")[0] for profile in KB.profiles()}
    assert families == {"hired-swords", "dramatis-personae"}
    # Los grados publicados hoy: 30 Dramatis Personae y 72 hired swords.
    assert len(KB.profiles()) >= 102


@pytest.mark.evidence
def test_every_kb_profile_resolves_through_the_registry() -> None:
    """Ningún perfil del catálogo publicado cita un documento que el registro no declare.

    Es la mitad permanente del cotejo: qué documento imprime a cada personaje sale del
    registro de documentos fuente, no de una tabla del tool, y una cita nueva sin
    declarar se ve aquí en vez de degradar a «sin documento que cotejar», que se lee
    como «no hay nada que comparar».
    """
    profiles = KB.profiles()
    for profile in profiles:
        assert DOCUMENTS.undeclared(profile) == [], profile["name"]
        assert DOCUMENTS.resolve(profile), profile["name"]


@pytest.mark.evidence
def test_the_dramatis_personae_print_on_the_four_grade_pages() -> None:
    """El registro declara las cuatro páginas de grado que cita la familia de Dramatis.

    La promoción de 2B publica además cinco Dramatis Personae en `grade-2b`, que se
    cotejan contra los PDF de Karak Azgal y de Relics of the Crusades 2; las cuatro
    páginas de grado siguen siendo las que imprime la familia histórica.
    """
    documents = {resolution.document.id.split(".")[-1]
                 for profile in KB.profiles()
                 if profile["_file"].startswith("dramatis-personae")
                 for resolution in DOCUMENTS.resolve(profile)}
    assert {"grade-1a", "grade-1b", "grade-1c", "grade-2a"} <= documents
    assert documents == {"grade-1a", "grade-1b", "grade-1c", "grade-2a",
                         "karak-azgal", "relics-of-the-crusades-2"}




@pytest.mark.evidence
def test_a_profile_takes_the_document_from_the_registry() -> None:
    """El Albino Stormvermin sale en el PDF de Specialists, con su copia del espejo."""
    profiles = {profile["name"]: profile for profile in KB.profiles()}
    resolved = DOCUMENTS.resolve(profiles["Albino Stormvermin"])
    assert [resolution.document.id for resolution in resolved] == [SPECIALISTS.id]
    assert resolved[0].document.mirror == SPECIALISTS.mirror




# La lectura del lector compartido, sin documento delante

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



