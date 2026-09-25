# -*- coding: utf-8 -*-
"""Cotejo permanente de los hirelings contra los documentos que los imprimen.

Herramienta permanente del utillaje de la KB (``tools/knowledge``): coteja el catálogo de
hirelings —las dos familias, ``hired-swords`` y ``dramatis-personae``, de todos los grados—
contra lo que imprimen sus documentos fuente, con las dos piezas permanentes que tiene al
lado: el resolvedor de «entrada → documento fuente» (``source_documents``) y el lector de
entradas impresas (``printed_entries``).

Qué coteja
----------
De cada perfil: **qué documento lo imprime** (la URL de sus ``source_refs`` resuelve en el
registro ``registry/source-documents.yaml`` al documento y a su copia del espejo), **qué
declara el catálogo** (características, ``warband_rating``, sus reglas y la tarifa —importe
y divisa— de su entrada de campaña) y **qué se adjudica**, que queda como nota y nunca como
un verde silencioso. La entrada impresa se localiza como la lee una persona: el encabezado
puntúa más que la fila de stats, y una entrada que no trae ni uno ni otro no puede tomarse
por la del personaje —identificarlo por su nombre en la prosa del vecino es lo que atribuía
al Fire-Eater la tarifa del Midshipman—.

Dos lecturas, una por familia de documento
------------------------------------------
- Una **página** trae sus entradas escritas (un bloque por personaje) y su tabla de perfiles
  por celdas, así que se leen tal cual.
- Un **PDF** se lee por geometría (``pdftohtml``), con un prefiltro por texto plano que
  descarta las páginas que ni nombran al personaje ni llevan su fila de stats —contigua, que
  es como la imprime la fuente— y con el desbordamiento de la página contigua cuando la
  entrada termina al pie (las reglas de Snorri están en la p63 y su perfil en la p62).

Los dos catálogos que sirve
---------------------------
``--tree kb`` (por defecto) coteja los catálogos publicados
(``sources/knowledge/catalog/hirelings`` con el documento de contratación de la KB);
``--tree 2b`` coteja el staging que se promociona a ellos
(``sources/2B/catalog/hirelings`` con su ``hired-swords-and-dramatis-2b.yaml``). Cada
catálogo declara su adjudicación propia —las etiquetas de regla que escribe y la fuente no
imprime como etiqueta— y escribe su informe aparte. Cuando 2B se promueva, la orden de la KB
cotejará también sus grados y la del staging desaparecerá.

Salida
------
``build/cache/hireling-sources/<catálogo>/check.json`` con las verificaciones, los hallazgos y
la **cobertura por chequeo** —un «0 hallazgos» sin filas comparadas no es lo mismo que un «0
comprobado»—, y las entradas extraídas en ``…/blocks/`` para lectura manual. Que la copia del
documento no esté descargada en el espejo (``build/cache``) se declara con la ruta que falta,
nunca se compara contra una página vacía.

Uso::

    python tools/knowledge/check_hireling_sources.py                  # la KB, todo
    python tools/knowledge/check_hireling_sources.py --tree 2b        # el staging de 2B
    python tools/knowledge/check_hireling_sources.py "The Foole"      # un perfil
"""
from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Las dos piezas permanentes viven al lado: el cotejo las re-exporta para sus pruebas y
# funciona igual invocado como script (sin PYTHONPATH) que importado por ellas.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from printed_entries import (  # noqa: F401
    CHECKS,
    Coverage,
    Package,
    compare,
    digits_row,
    entries,
    fee_index,
    fees_in,
    merge,
    normalize,
    package_fee,
    print_report,
    ratings_in,
    stat_rows,
    unit_of,
    write_report,
)
from source_documents import (  # noqa: F401
    DocumentReader,
    SourceDocuments,
    SourceMirror,
)

ROOT = Path(__file__).resolve().parents[2]

# Etiquetas de regla que el catálogo escribe y la fuente no imprime como etiqueta. La regla
# se coteja por su hecho impreso —que sí está en la entrada— y la etiqueta queda como nota
# con su evidencia.
EDITORIAL = {
    "Conditional Acceptance — Good-Aligned Employers": (
        "la fuente imprime la elegibilidad como el párrafo «May Be Hired: Any "
        "Mercenaries, Sisters of Sigmar and Witch Hunters may hire William. "
        "Furthermore, any good-aligned warband may hire William on a roll of 4+», "
        "y el catálogo la modela como regla del perfil; el mismo hecho está en "
        "`eligibility.allow_groups` del documento de campaña"),
}

# Nombre del perfil tal y como lo imprime la fuente cuando difiere del nombre del catálogo
# ('Cleric of Law' es el perfil de ambos sacerdotes de Verena/Solkan).
PRINTED_ANCHORS = {
    "Priest of Verena": "Cleric of Law",
    "Snorri Nosebiter": "Snorri",
    "Aldred Fellblade": "Aldred",
    "Mariner-Priest of Manann": "Mariner-priest",
    "Grave Warden": "Grave Warden",
    "Ogre Treasure-Hunter": "Scrap-Dealer",
    "Albino Stormvermin": "Albino Guard",
}


@dataclass
class Catalogue:
    """Un catálogo de hirelings: sus perfiles, su documento de tarifas y su adjudicación.

    La forma es la misma en los dos árboles —``profiles`` en cualquier YAML bajo la raíz del
    catálogo, y las tarifas en el documento de campaña indexadas por ``profile_id``—, así que
    el cotejo los recorre con la misma lectura y sólo cambia lo que cada uno adjudica.
    """

    name: str
    root: Path
    campaign: Path
    out: Path
    editorial: dict = field(default_factory=dict)

    @property
    def report(self) -> Path:
        """El informe JSON del catálogo."""
        return self.out / "check.json"

    @property
    def blocks(self) -> Path:
        """Las entradas impresas leídas, en orden de lectura."""
        return self.out / "blocks"

    def profiles(self) -> list[dict]:
        """Los perfiles del catálogo, con el fichero del que salen.

        Cualquier YAML bajo la raíz: los hired swords de la KB viven en su subcarpeta y los
        del staging planos, y los Dramatis Personae en ``dramatis-personae/``.
        """
        out: list[dict] = []
        for path in sorted(self.root.rglob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for profile in document.get("profiles") or []:
                profile["_file"] = path.relative_to(self.root).as_posix()
                out.append(profile)
        return out


CATALOGUES: dict[str, Catalogue] = {
    "kb": Catalogue(
        name="kb",
        root=ROOT / "sources/knowledge/catalog/hirelings",
        campaign=ROOT / "sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml",
        out=ROOT / "build/cache/hireling-sources/kb",
        editorial=EDITORIAL,
    ),
    "2b": Catalogue(
        name="2b",
        root=ROOT / "sources/2B/catalog/hirelings",
        campaign=ROOT / "sources/2B/catalog/hired-swords-and-dramatis-2b.yaml",
        out=ROOT / "build/cache/hireling-sources/2b",
    ),
}

# El registro declara qué documento imprime cada cita y dónde está su copia; el espejo del
# checkout es ``build/cache`` y las cachés de página del lector viven con los informes.
SOURCE_DOCUMENTS = SourceDocuments.load()
MIRROR = SourceMirror(
    ROOT / "build/cache",
    words=ROOT / "build/cache/hireling-sources/words",
    texts=ROOT / "build/cache/hireling-sources/text",
)


# --------------------------------------------------------------------------- #
# El paquete y la entrada impresa
# --------------------------------------------------------------------------- #

def printed_name_candidates(name: str) -> list[str]:
    """Formas con las que la entrada puede nombrar al personaje.

    Sólo formas de cinco letras o más: un recorte corto (``Fire`` de Fire-Eater) aparece en
    la prosa de cualquier vecino —«set on fire»— y haría que la entrada de ese vecino se
    tomara por la del personaje. El nombre con el que la fuente lo imprime cuando difiere del
    catálogo viaja declarado en ``PRINTED_ANCHORS``.
    """
    candidates = [name, name.replace("Necromancer", "").strip(),
                  " ".join(name.split()[-2:]), name.split(",")[0].strip(),
                  name.split("-")[0].split(",")[0].strip()]
    candidates += [part.strip() for part in re.split(r"[,\-—]", name)]
    anchor = PRINTED_ANCHORS.get(name)
    if anchor:
        candidates.append(anchor)
    return [c for c in dict.fromkeys(candidates) if len(c) >= 5]


def package_of(profile: dict, campaign: dict) -> Package:
    """Lo que el paquete declara del personaje, listo para cotejar."""
    rating = profile.get("warband_rating") or {}
    return Package(
        stats="".join(str(v) for v in (profile.get("characteristics") or {}).values()) or None,
        # Un ``base: 0`` con ``per_experience_point`` es la valoración que la fuente no
        # imprime: el chequeo se da por verificado por ausencia en los dos lados, no como
        # un cero.
        rating=rating.get("base", rating.get("value")) or None,
        rules=tuple(str(rule.get("name") or "") for rule in profile.get("rules") or []),
        fee=package_fee(campaign.get("hiring_fee")),
        upkeep=package_fee(campaign.get("upkeep")),
    )


def locate_entry(profile: dict, printed: Sequence[dict]) -> dict | None:
    """La entrada impresa del perfil dentro de una página, por encabezado y fila de stats.

    Cada entrada se puntúa por su encabezado (el nombre que la fuente imprime) y por su fila
    de stats (lo que imprime), y el personaje es la entrada mejor puntuada. La fila sola no
    basta cuando dos vecinos comparten fila —el Halfling Fence y el Halfling Pimp imprimen
    los mismos nueve dígitos— y el encabezado solo no basta cuando la fila del paquete está
    mal y hay que enseñarla.
    """
    digits = "".join(str(v) for v in (profile.get("characteristics") or {}).values())
    candidates = printed_name_candidates(profile["name"])
    wanted = {digits_row(digits), digits_row(digits, swap=True)} if digits else set()
    best: tuple[int, dict] | None = None
    for entry in printed:
        heading_hit = any(normalize(c) in normalize(entry["heading"]) for c in candidates)
        row_hit = bool(wanted & set(stat_rows(entry)))
        if not (heading_hit or row_hit):
            continue
        score = (2 if heading_hit else 0) + (1 if row_hit else 0)
        if best is None or score > best[0]:
            best = (score, entry)
    return best[1] if best else None


def locate_in_pdf(profile: dict, reader: DocumentReader,
                  tree_names: Sequence[str]) -> tuple[int, dict | None] | None:
    """Página y entrada del perfil dentro de un PDF.

    El prefiltro por texto plano descarta las páginas que ni nombran al personaje ni llevan
    su fila de stats; la geometría se lee sólo en las candidatas, que es lo caro.
    """
    corpus, stem = reader.corpus, reader.name
    digits = "".join(str(v) for v in (profile.get("characteristics") or {}).values())
    candidates = printed_name_candidates(profile["name"])
    wanted = {digits_row(digits), digits_row(digits, swap=True)} if digits else set()
    pages: list[int] = []
    for page in range(1, corpus.page_count(stem) + 1):
        text = corpus.page_text(stem, page)
        lowered = normalize(text)
        page_digits = re.sub(r"\D", "", normalize(text))
        if (any(normalize(c) in lowered for c in candidates)
                or any(w and w in page_digits for w in wanted)):
            pages.append(page)
    best: tuple[int, int, dict] | None = None
    for page in pages:
        for entry in corpus.entries(stem, page):
            heading_hit = any(normalize(c) in normalize(entry["heading"]) for c in candidates)
            row_hit = bool(wanted & set(stat_rows(entry)))
            if not (heading_hit or row_hit):
                continue
            score = (2 if heading_hit else 0) + (1 if row_hit else 0)
            if best is None or score > best[0]:
                best = (score, page, entry)
    if best is not None:
        entry = dict(best[2])
        entry["spillover"] = (corpus.continuation(stem, best[1], profile["name"], tree_names,
                                                 candidates_for=printed_name_candidates)
                              if entry.get("last_on_page") else "")
        return best[1], entry
    if pages:
        return pages[0], None
    return None


def locate(profile: dict, reader: DocumentReader,
           tree_names: Sequence[str]) -> tuple[int | None, dict | None] | None:
    """Página y entrada del perfil en el documento que lo imprime.

    ``None`` cuando el documento no imprime ninguna entrada que pueda ser la del personaje;
    una tupla con ``entry=None`` cuando lo nombra pero no imprime su entrada —el perfil sólo
    vive en las listas de contratación—.
    """
    if reader.kind == "pdf":
        return locate_in_pdf(profile, reader, tree_names)
    return None, locate_entry(profile, reader.corpus.entries())


# --------------------------------------------------------------------------- #
# El cotejo
# --------------------------------------------------------------------------- #

def check_one(profile: dict, campaign: dict, catalogue: Catalogue,
              tree_names: Sequence[str]) -> dict:
    """Coteja un perfil contra los documentos que lo imprimen."""
    row = {"name": profile["name"], "file": profile["_file"], "id": profile.get("id"),
           "checks": [], "findings": [], "notes": [], "comparable": False}
    adjudicated = profile.get("normalization_status") == "out_of_scope"
    for url in SOURCE_DOCUMENTS.undeclared(profile):
        row["notes"].append(f"cita sin documento declarado en el registro: {url}")
    coverages: list[Coverage] = []
    for resolution in SOURCE_DOCUMENTS.resolve(profile):
        reader = MIRROR.reader(resolution.document)
        if reader is None:
            row["notes"].append(f"sin copia local: {resolution.document.mirror}")
            continue
        hit = locate(profile, reader, tree_names)
        if hit is None:
            row["notes"].append(f"{resolution.document.mirror} no imprime una entrada propia "
                                f"del personaje (lo nombra la prosa o la lista del documento)")
            continue
        page, entry = hit
        if entry is None:
            row["notes"].append(f"{resolution.document.mirror} p{page} nombra al personaje "
                                f"pero no imprime su entrada (el perfil sólo vive en las "
                                f"listas de contratación)")
            continue
        where = f" p{page}" if page else ""
        (catalogue.blocks / f"{profile['name'].replace(',', '').replace(' ', '_')}.txt").write_text(
            f"### {resolution.document.mirror}{where}\n" + "\n".join(entry["lines"]) + "\n",
            encoding="utf-8")
        coverage = Coverage()
        compare(entry, package_of(profile, campaign), coverage, editorial=catalogue.editorial)
        coverages.append(coverage)
    if not coverages:
        if adjudicated:
            row["notes"].append(f"adjudicado `out_of_scope`: "
                                f"{profile.get('out_of_scope_reason') or 'sin entrada impresa'}")
        if not row["notes"]:
            row["notes"].append("sin documento que cotejar")
        return row
    if adjudicated:
        row["notes"].append(f"adjudicado `out_of_scope`: "
                            f"{profile.get('out_of_scope_reason') or 'sin entrada impresa'}"
                            f" — se coteja lo que la fuente imprime")
    report = merge(coverages).report()
    # El cotejo se suma a lo que la fila ya anotó (la adjudicación del perfil).
    report["notes"] = row["notes"] + report["notes"]
    row.update(report)
    row["comparable"] = True
    return row


def run(catalogue: Catalogue, names: Sequence[str] = ()) -> list[dict]:
    """Coteja los perfiles del catálogo y deja el informe y los bloques escritos."""
    only = set(names)
    catalogue.blocks.mkdir(parents=True, exist_ok=True)
    fees = fee_index(catalogue.campaign)
    profiles = catalogue.profiles()
    tree_names = [profile["name"] for profile in profiles]
    rows = [
        check_one(profile, fees.get(str(profile.get("id"))) or {}, catalogue, tree_names)
        for profile in profiles
        if not only or profile["name"] in only
    ]
    write_report(rows, catalogue.report)
    print_report(rows, f"hirelings {catalogue.name}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coteja los hirelings contra sus fuentes.")
    parser.add_argument("--tree", choices=sorted(CATALOGUES), default="kb",
                        help="catálogo a cotejar: la KB publicada (kb) o el staging de 2B (2b)")
    parser.add_argument("names", nargs="*", help="perfiles a cotejar (por defecto, todos)")
    args = parser.parse_args(argv)
    run(CATALOGUES[args.tree], args.names)
    return 0


if __name__ == "__main__":
    sys.exit(main())
