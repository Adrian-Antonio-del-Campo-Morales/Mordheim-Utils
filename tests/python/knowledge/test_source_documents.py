"""Guards for the permanent entry→source resolver (``tools/knowledge/source_documents``).

El cotejo de catálogo contra fuente empieza por saber **qué documento imprime la
entrada**, y eso lo declara el registro de documentos fuente de la KB
(``sources/knowledge/registry/source-documents.yaml``) con las citas del propio
catálogo. Esta batería fija lo que lo hace permanente:

1. **Completitud.** Ninguna cita con URL de los catálogos de hirelings —la KB y el
   árbol de 2B que se promociona a ella— se queda sin documento declarado. Una
   cita nueva sin declarar falla aquí, en vez de degradar a un «sin fuente que
   cotejar» que se lee como «no hay nada que comparar».
2. **Una cita, un documento.** Cada URL la declara un solo documento, y cada
   documento declara la copia que ocupa en el espejo, relativa y sin repetir.
3. **La resolución no depende del driver.** La URL se busca por su forma canónica
   (ruta descodificada, sin barra final), el orden de cita se conserva, el mismo
   documento citado dos veces se lee una vez y una cita sin documento se declara.

Nada de esto necesita la caché: el espejo sólo dice si la copia está descargada, y
sin ella se declara el hueco con la ruta que falta.
"""
from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
# El resolvedor vive en el utillaje permanente de la KB; su registro, en la KB.
TOOLS = ROOT / "tools" / "knowledge"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

sd = pytest.importorskip("source_documents")

#: Los catálogos cuyas citas tienen que resolver. El árbol 2B entra mientras es el
#: staging que se promociona a la KB: cuando se promocione, sus dos documentos
#: ocupan el mismo sitio en ``sources/knowledge`` y esta lista se acorta sola.
CATALOGUES = (
    "sources/knowledge/catalog/hirelings",
    "sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml",
    "sources/2B/catalog/hirelings",
    "sources/2B/catalog/hired-swords-and-dramatis-2b.yaml",
)

#: Las claves con las que los catálogos publican listas de registros.
RECORD_KEYS = ("profiles", "rules", "hired_swords", "dramatis_personae")


def cited_records() -> list[tuple[str, dict]]:
    """Cada registro de los catálogos con su fichero, para recorrer las citas."""
    out: list[tuple[str, dict]] = []
    for entry in CATALOGUES:
        path = ROOT / entry
        documents = sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
        for document in documents:
            payload = yaml.safe_load(document.read_text(encoding="utf-8")) or {}
            for key in RECORD_KEYS:
                for record in payload.get(key) or []:
                    out.append((document.relative_to(ROOT).as_posix(), record))
    return out


def registered_sources() -> set[str]:
    """Los ids de manual que la KB tiene registrados."""
    path = ROOT / "sources/knowledge/registry/sources.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(entry["id"]) for entry in payload.get("sources") or []}


# --------------------------------------------------------------------------- #
# El registro completo
# --------------------------------------------------------------------------- #

def test_every_cited_url_is_declared() -> None:
    """Ningún catálogo cita un documento que el registro no declare."""
    documents = sd.SourceDocuments.load()
    records = cited_records()
    # Una ruta mal escrita dejaría la comprobación vacía y pasaría en verde.
    assert len(records) >= 250, len(records)
    undeclared = sorted({url for _, record in records for url in documents.undeclared(record)})
    assert undeclared == []


def test_every_citation_names_the_manual_of_its_document() -> None:
    """La cita dice de dónde viene el texto y el documento dónde se lee: el mismo manual."""
    documents = sd.SourceDocuments.load()
    for name, record in cited_records():
        for citation in sd.citations_of(record):
            document = documents.document_for(citation.url)
            if document is None:
                continue
            assert citation.manual == document.manual, f"{name}: {citation.url}"


def test_the_declared_manuals_are_registered_sources() -> None:
    """Un documento pertenece a un manual registrado, no a una cadena suelta."""
    manuals = {document.manual for document in sd.SourceDocuments.load()}
    assert manuals and manuals <= registered_sources()


def test_the_registry_declares_both_source_families() -> None:
    """Los PDFs de 2B y las páginas de 2A cotejan por el mismo registro."""
    documents = sd.SourceDocuments.load()
    assert len(documents) >= 16
    assert {document.kind for document in documents} == {"pdf", "page"}


def test_the_registry_path_is_the_one_in_the_knowledge_base() -> None:
    assert sd.registry_path() == ROOT / "sources/knowledge/registry/source-documents.yaml"


# --------------------------------------------------------------------------- #
# Una cita, un documento, una copia
# --------------------------------------------------------------------------- #

def test_a_url_is_claimed_by_one_document() -> None:
    """Dos documentos no pueden pelearse la misma cita: el registro lo rechaza."""
    url = "https://example.invalid/a.pdf"
    document = sd.SourceDocument
    with pytest.raises(ValueError, match="la declaran dos documentos"):
        sd.SourceDocuments([
            document(id="a", manual="broheim.net", kind="pdf", mirror="a.pdf", urls=(url,)),
            document(id="b", manual="broheim.net", kind="pdf", mirror="b.pdf", urls=(url,)),
        ])


def test_a_document_may_declare_the_same_url_twice() -> None:
    """Repetir una forma de citar el mismo documento es inocuo."""
    url = "https://example.invalid/a.pdf"
    documents = sd.SourceDocuments([
        sd.SourceDocument(id="a", manual="broheim.net", kind="pdf", mirror="a.pdf",
                          urls=(url, url)),
    ])
    assert documents.document_for(url).id == "a"


def test_an_unknown_kind_is_refused() -> None:
    """Un documento que el cotejo no sepa leer se declara, no se adivina."""
    with pytest.raises(ValueError, match="kind 'scan'"):
        sd.SourceDocuments([
            sd.SourceDocument(id="a", manual="broheim.net", kind="scan", mirror="a.pdf",
                              urls=("https://example.invalid/a.pdf",)),
        ])


def test_the_mirror_names_are_relative_and_unique() -> None:
    """Cada documento ocupa una copia distinta del espejo, dentro de su raíz."""
    documents = sd.SourceDocuments.load()
    mirrors = [document.mirror for document in documents]
    assert len(set(mirrors)) == len(mirrors), mirrors
    mirror = sd.SourceMirror(ROOT / "build/cache")
    for document in documents:
        path = PurePosixPath(document.mirror)
        assert not path.is_absolute() and ".." not in path.parts, document.id
        assert mirror.declared(document) == ROOT / "build/cache" / document.mirror


def test_the_dramatis_page_of_a_grade_is_the_documented_snapshot() -> None:
    """La página del grado se lee del snapshot cacheado y, a falta de él, de su texto.

    Es la copia con la que el cotejo de 2A venía leyendo (``dramatis-<grado>.html``
    bajo ``build/cache/2a-dp/``), y el respaldo de texto plano el mismo gemelo que
    antes se buscaba a mano.
    """
    document = sd.SourceDocuments.load().by_id("mordheimer.net.dramatis-personae.grade-2a")
    assert document.kind == "page" and document.mirror == "2a-dp/dramatis-grade-2a.html"
    mirror = sd.SourceMirror(ROOT / "build/cache")
    html, text = mirror.candidates(document)
    assert html == ROOT / "build/cache/2a-dp/dramatis-grade-2a.html"
    assert text == html.with_suffix(".txt")
    # Sin caché no hay copia: se declara el hueco, no se falla, y sin copia no hay lector.
    assert mirror.path(document) in (None, html, text)
    assert (mirror.reader(document) is None) is (mirror.path(document) is None)


# --------------------------------------------------------------------------- #
# La resolución de una entrada
# --------------------------------------------------------------------------- #

def test_resolution_keeps_the_citation_order_and_reads_a_document_once() -> None:
    """Dos formas de citar el mismo PDF son un documento, y la primera es la cita."""
    documents = sd.SourceDocuments.load()
    record = {"source_refs": [
        {"manual": "mordheimer.net", "printed_page": 0, "section": "A",
         "url": "https://mordheimer.net/docs/campaigns/dramatis-personae/grade-2a"},
        {"manual": "broheim.net", "printed_page": 3, "section": "B",
         "url": "https://broheim.net/downloads/hiredswords/mutinyinmarienburg/MiM%20Specialists.pdf"},
        {"manual": "broheim.net", "printed_page": 5, "section": "C",
         "url": "https://broheim.net/downloads/hiredswords/mutinyinmarienburg/Specialists.pdf"},
    ]}
    resolved = documents.resolve(record)
    assert [item.document.id for item in resolved] == [
        "mordheimer.net.dramatis-personae.grade-2a",
        "broheim.mutinyinmarienburg.specialists",
    ]
    assert resolved[1].citation.where == "B / p. 3"
    # La página 0 es una página web: no se imprime en una nota.
    assert resolved[0].citation.where == "A"


def test_the_singular_source_of_a_band_record_resolves() -> None:
    """Los perfiles y reglas de banda declaran su cita con ``source``, no ``source_refs``.

    La cita es la misma —el resolvedor lee las dos claves—, y sirve para las páginas
    de banda el día que el registro las declare junto a las de hirelings.
    """
    documents = sd.SourceDocuments.load()
    record = {"source": {"manual": "mordheimer.net", "printed_page": 0, "section": "Aenur",
                         "url": "https://mordheimer.net/docs/campaigns/dramatis-personae/grade-1a"}}
    assert [(item.document.id, item.citation.section) for item in documents.resolve(record)] == [
        ("mordheimer.net.dramatis-personae.grade-1a", "Aenur")]


def test_a_citation_with_an_unknown_url_is_reported() -> None:
    """Una cita que el registro no declare se dice, no se ignora."""
    documents = sd.SourceDocuments.load()
    record = {"source_refs": [{"manual": "broheim.net", "printed_page": 1, "section": "X",
                               "url": "https://broheim.net/downloads/unknown/New.pdf"}]}
    assert documents.undeclared(record) == ["https://broheim.net/downloads/unknown/New.pdf"]
    assert documents.resolve(record) == []


def test_a_record_without_provenance_resolves_to_nothing() -> None:
    documents = sd.SourceDocuments.load()
    assert documents.resolve({}) == [] and documents.undeclared({}) == []


def test_the_canonical_form_folds_the_citation_spellings() -> None:
    """La ruta descodificada y sin barra final: dos formas de la misma cita coinciden."""
    documents = sd.SourceDocuments.load()
    specialists = documents.by_id("broheim.mutinyinmarienburg.specialists")
    for url in specialists.urls:
        assert documents.document_for(url) is specialists
    # Sin decodificar, la cita con ``%20`` no encontraría el documento.
    assert sd.normalize_url("https://mordheimer.net/docs/campaigns/dramatis-personae/grade-2a/") \
        == sd.normalize_url("https://mordheimer.net/docs/campaigns/dramatis-personae/grade-2a#x")
