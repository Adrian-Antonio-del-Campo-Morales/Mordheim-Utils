# -*- coding: utf-8 -*-
"""Resolvedor permanente de «entrada → documento fuente» del cotejo de catálogo.

Herramienta permanente del utillaje de la KB (`tools/knowledge`), hermana del lector de
entradas impresas: éste lee el documento, aquél dice **cuál** es.

El cotejo de catálogo contra fuente empieza por saber qué documento imprime la entrada, y
eso lo declara la propia entrada: sus ``source_refs`` llevan el manual, la página, la
sección y la URL, y la URL resuelve en el registro de documentos fuente
(``sources/knowledge/registry/source-documents.yaml``) al documento que la imprime, con
las demás formas con que el catálogo lo cita y con la copia local del espejo. Un
documento que el catálogo cite y el registro no declare es un **error del cotejo**, no un
hueco silencioso: los cotejos ya no adivinan el nombre del fichero.

Qué aporta frente a cablear el nombre en cada driver
----------------------------------------------------
Los drivers de la fase de ingesta resolvían el documento con tablas propias —los alias
del nombre de descarga al de la caché, el prefijo ``dramatis-`` de las páginas— y una
cita que no estaba en la tabla degradaba a «sin fuente que cotejar», que se lee igual que
un «no hay nada que comparar». Aquí la tabla es el registro versionado, y el conjunto de
citas de los catálogos es el que manda: lo que falte se ve.

Qué **no** decide
-----------------
La adjudicación: qué es hallazgo y qué una nota, qué perfiles son ``out_of_scope`` y qué
etiquetas de regla son editoriales lo declara cada driver. El espejo tampoco decide: que
la copia no esté descargada es un hueco que se declara con la ruta que falta —la
instrucción para rellenarlo—, nunca un verde.
"""
from __future__ import annotations

import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# El espejo entrega el documento ya legible, así que el resolvedor conoce el lector.
from printed_entries import HtmlCorpus, PdfCorpus, TextCorpus

#: Qué documentos sabe leer el cotejo, y con qué corpus.
KINDS = ("pdf", "page")

#: Dónde vive el registro de documentos fuente, relativo a la raíz del checkout.
REGISTRY_PATH = ("sources", "knowledge", "registry", "source-documents.yaml")


def registry_path() -> Path:
    """El registro de documentos fuente del checkout.

    Se localiza subiendo desde este fichero, así que no depende del directorio de
    trabajo; quien coteje otro árbol puede pasar su ruta explícita.
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent.joinpath(*REGISTRY_PATH)
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"no encuentro {'/'.join(REGISTRY_PATH)}; pasa la ruta del registro explícita"
    )


def normalize_url(url: str) -> str:
    """Forma canónica de una cita, para que dos formas de citar un documento coincidan.

    El catálogo cita el mismo PDF como ``Specialists.pdf`` y como ``MiM%20Specialists.pdf``,
    y la misma página con y sin barra final; el registro declara todas las formas y aquí se
    comparan en una sola: ruta descodificada, sin barra final, sin fragmento, y esquema y
    host en minúsculas. La ruta conserva su caja y su consulta —son parte de la identidad
    del documento—.
    """
    text = str(url or "").strip()
    if not text:
        return ""
    parts = urllib.parse.urlsplit(text)
    return urllib.parse.urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        urllib.parse.unquote(parts.path).rstrip("/"),
        parts.query,
        "",
    ))


@dataclass(frozen=True)
class SourceDocument:
    """Un documento fuente: dónde se cita, cómo se lee y dónde está su copia."""

    id: str
    manual: str
    kind: str
    mirror: str
    urls: tuple[str, ...]


@dataclass(frozen=True)
class Citation:
    """Una cita de ``source_refs``: dónde el registro sitúa el texto dentro del documento."""

    manual: str
    url: str
    printed_page: Any = None
    section: str = ""

    @property
    def where(self) -> str:
        """La cita como se imprime en una nota: página y sección, lo que haya."""
        parts = [str(self.section)] if self.section else []
        if self.printed_page not in (None, 0, "0"):
            parts.append(f"p. {self.printed_page}")
        return " / ".join(parts)


@dataclass(frozen=True)
class Resolution:
    """Una entrada del catálogo y el documento que la imprime según esa entrada."""

    document: SourceDocument
    citation: Citation


@dataclass(frozen=True)
class DocumentReader:
    """Un documento listo para leer: su corpus, cómo se llamó cada página y con qué se leyó."""

    document: SourceDocument
    corpus: Any
    name: str
    kind: str


def citations_of(record: Mapping) -> list[Citation]:
    """Las citas de provenance de un registro del catálogo, en su orden.

    ``source_refs`` es la forma canónica y ``source`` la singular que usan los perfiles y
    las reglas de banda; las dos llevan el mismo objeto de cita.
    """
    refs = record.get("source_refs")
    if refs is None and isinstance(record.get("source"), Mapping):
        refs = [record["source"]]
    out: list[Citation] = []
    for ref in refs or []:
        if not isinstance(ref, Mapping):
            continue
        out.append(Citation(
            manual=str(ref.get("manual") or ""),
            url=str(ref.get("url") or ""),
            printed_page=ref.get("printed_page"),
            section=str(ref.get("section") or ""),
        ))
    return out


class SourceDocuments:
    """El registro de documentos fuente: de una cita a su documento y a su copia."""

    def __init__(self, documents: Sequence[SourceDocument]) -> None:
        self.documents: tuple[SourceDocument, ...] = tuple(documents)
        self._by_id = {document.id: document for document in self.documents}
        self._by_url: dict[str, SourceDocument] = {}
        for document in self.documents:
            if document.kind not in KINDS:
                raise ValueError(
                    f"{document.id}: kind {document.kind!r} desconocido; los conocidos son {list(KINDS)}")
            for url in document.urls:
                key = normalize_url(url)
                claimed = self._by_url.get(key)
                if claimed is not None and claimed.id != document.id:
                    raise ValueError(
                        f"la URL {url!r} la declaran dos documentos: {claimed.id} y {document.id}")
                self._by_url[key] = document

    @classmethod
    def load(cls, path: Path | None = None) -> "SourceDocuments":
        """El registro del checkout, o el de la ruta que se le pase."""
        source = Path(path) if path is not None else registry_path()
        payload = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        documents = [
            SourceDocument(
                id=str(entry["id"]),
                manual=str(entry["manual"]),
                kind=str(entry["kind"]),
                mirror=str(entry["mirror"]),
                urls=tuple(str(url) for url in entry["urls"]),
            )
            for entry in payload.get("documents") or []
        ]
        return cls(documents)

    def __iter__(self):
        return iter(self.documents)

    def __len__(self) -> int:
        return len(self.documents)

    def by_id(self, document_id: str) -> SourceDocument | None:
        return self._by_id.get(document_id)

    def document_for(self, url: str) -> SourceDocument | None:
        """El documento que imprime esa URL, o ``None`` si el registro no lo declara."""
        return self._by_url.get(normalize_url(url))

    def resolve(self, record: Mapping) -> list[Resolution]:
        """Los documentos que imprimen la entrada, en orden de cita y sin repetir.

        Una entrada puede citar el mismo documento dos veces —el catálogo cita el PDF con
        dos formas— y el cotejo lo lee una: se conserva la primera cita, que es la que
        lleva la sección adjudicada. Una cita sin URL no resuelve: no hay documento que
        leer, y lo dice :meth:`undeclared`.
        """
        out: list[Resolution] = []
        seen: set[str] = set()
        for citation in citations_of(record):
            document = self.document_for(citation.url)
            if document is None or document.id in seen:
                continue
            seen.add(document.id)
            out.append(Resolution(document=document, citation=citation))
        return out

    def undeclared(self, record: Mapping) -> list[str]:
        """Las citas de la entrada que ningún documento del registro reclama.

        Es la lista que no puede tener nada cuando el registro está completo: el cotejo la
        revisa para fallar en vez de declarar un hueco que se lee como un «no comparable».
        """
        return [
            citation.url or "(sin url)"
            for citation in citations_of(record)
            if self.document_for(citation.url) is None
        ]


class SourceMirror:
    """Las copias descargadas de los documentos fuente, bajo la raíz del espejo.

    ``build/cache`` es el espejo del checkout, y el registro dice qué ruta ocupa cada
    documento. Un ``pdf`` se lee con el corpus de geometría —que además busca la copia en
    la subcarpeta ``extra`` del espejo— y una ``page`` con el HTML que trae la estructura o,
    a falta de él, con su gemelo de texto plano.
    """

    def __init__(self, root: Path, *, words: Path | None = None, texts: Path | None = None) -> None:
        self.root = Path(root)
        self.words = Path(words) if words is not None else self.root / "words"
        self.texts = Path(texts) if texts is not None else self.root / "text"
        self._corpora: dict[str, Any] = {}

    def declared(self, document: SourceDocument) -> Path:
        """La copia que el registro manda, exista o no; es lo que una nota declara que falta."""
        return self.root / document.mirror

    def candidates(self, document: SourceDocument) -> tuple[Path, ...]:
        """Dónde puede estar la copia de un documento, en orden de preferencia."""
        declared = self.declared(document)
        if document.kind == "pdf":
            return (declared, declared.parent / "extra" / declared.name)
        if declared.suffix.lower() in (".html", ".htm"):
            return (declared, declared.with_suffix(".txt"))
        return (declared,)

    def path(self, document: SourceDocument) -> Path | None:
        """La copia que el cotejo puede leer, o ``None`` si no está descargada."""
        for candidate in self.candidates(document):
            if candidate.is_file():
                return candidate
        return None

    def reader(self, document: SourceDocument) -> DocumentReader | None:
        """El documento preparado para leer, o ``None`` si falta su copia.

        El corpus del PDF se guarda por directorio —no por perfil— para que la caché de
        páginas del lector sobreviva a las entradas que comparten documento.
        """
        path = self.path(document)
        if path is None:
            return None
        if document.kind == "pdf":
            return DocumentReader(document=document, corpus=self._pdf(path),
                                  name=path.stem, kind="pdf")
        html = path.suffix.lower() in (".html", ".htm")
        corpus = HtmlCorpus(path) if html else TextCorpus(path)
        return DocumentReader(document=document, corpus=corpus, name=path.name,
                              kind="html" if html else "text")

    def _pdf(self, path: Path) -> PdfCorpus:
        corpus = self._corpora.get(str(path.parent))
        if corpus is None:
            corpus = PdfCorpus(path.parent, self.words, self.texts)
            self._corpora[str(path.parent)] = corpus
        return corpus
