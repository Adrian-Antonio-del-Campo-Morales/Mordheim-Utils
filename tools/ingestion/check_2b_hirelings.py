# -*- coding: utf-8 -*-
"""Cotejo de hirelings y Dramatis Personae de 2B contra sus PDFs fuente.

De cada personaje, este driver resuelve **qué fuente lo imprime** y **qué declara
el paquete**, y el cotejo en sí lo hace el lector compartido
(``printed_entries``), el mismo que usa el cotejo de Dramatis Personae de 2A.
Aquí vive sólo lo que es de este árbol:

1. **Qué PDF imprime a cada personaje** (``reference_stems``): los ficheros
   citados por ``source_refs``, con el nombre con el que el árbol referencia cada
   suplemento. La página se lee por geometría, así que la tarifa, la fila de
   stats y el rating del vecino de columna no pueden atribuirse al personaje.
2. **Qué declara el paquete**: ``characteristics``, ``warband_rating``, ``rules``
   y la tarifa —importe **y divisa**— de su entrada de campaña en
   ``sources/2B/catalog/hired-swords-and-dramatis-2b.yaml``, que es donde vive la
   tarifa desde que el árbol tomó la forma de promoción.
3. **Qué se adjudica**: los perfiles ``out_of_scope`` y las etiquetas de regla
   editoriales. Se compara lo que la fuente imprime —el Horseman de 2B sólo se
   menciona en las listas de contratación, así que no hay nada que comparar— y la
   adjudicación queda como nota, nunca como un verde silencioso.

Salida: JSON con verificaciones y hallazgos más la cobertura por chequeo —un «0
hallazgos» sin filas comparadas no es lo mismo que un «0 comprobado»— y las
entradas extraídas, en orden de lectura, en
``build/cache/2b-hirelings/hireling-blocks/`` para lectura manual.

Requiere ``pdftohtml`` y ``pdftotext`` (poppler); sin ellos se salta las páginas
en vez de fallar, como el resto de los auditores de fuente.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# La lectura por geometría, la comparación de divisa y la cobertura viven en el
# lector compartido; el driver re-exporta las piezas que usa su batería de pruebas
# (``fees_in``, ``unit_of``, ``entries``, ``stat_rows``, ``ratings_in``).
from printed_entries import (  # noqa: F401
    Coverage,
    Package,
    PdfCorpus,
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

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build/cache/2b-pdfs"
OUT = ROOT / "build/cache/2b-hirelings"
BLOCKS = OUT / "hireling-blocks"
WORDS = OUT / "words"
TEXT = OUT / "text"

CORPUS = PdfCorpus(CACHE, WORDS, TEXT)

# Cualquier YAML bajo catalog/hirelings/: los hired swords están hoy planos y los
# Dramatis Personae en su subcarpeta, como en la KB. Las tarifas viven en el
# documento de campaña, que es donde el árbol las guarda desde que tomó la forma
# de promoción (las constantes dejan que la batería de pruebas apunte a otra copia).
STAGING_HIRELINGS = ROOT / "sources/2B/catalog/hirelings"
CAMPAIGN_DOC = ROOT / "sources/2B/catalog/hired-swords-and-dramatis-2b.yaml"

# Nombres de fichero con los que el árbol referencia cada PDF (el manifest usa el
# nombre de la descarga, la carpeta de caché el del fichero).
ALIASES = {
    "Karak Azgal": "adventurers-kaz",
    "97RelicsoftheCrusadesPt2": "fallen-the-rel",
    "Specialists": "MiM Specialists",
    "Miracle-workers-in-Mordheim": "Miracle Workers",
    "Lords of the Marsh": "lords-of-the-marsh-mim",
    "Shallows Beasts": "shallows-beasts-mim",
}

# Nombre del perfil tal y como lo imprime la fuente cuando difiere del nombre del
# catálogo ('Cleric of Law' es el perfil de ambos sacerdotes de Verena/Solkan).
PROFILE_ANCHORS = {
    "Priest of Verena": "Cleric of Law",
    "Snorri Nosebiter": "Snorri",
    "Aldred Fellblade": "Aldred",
    "Mariner-Priest of Manann": "Mariner-priest",
    "Grave Warden": "Grave Warden",
    "Ogre Treasure-Hunter": "Scrap-Dealer",
    "Albino Stormvermin": "Albino Guard",
}

TREE_NAMES: list[str] = []


def pdf_for(stem: str) -> Path | None:
    return CORPUS.pdf_for(stem)


# --------------------------------------------------------------------------- #
# El paquete
# --------------------------------------------------------------------------- #

def profiles() -> list[dict]:
    """Los perfiles de hireling y Dramatis Personae del árbol de staging."""
    out = []
    for path in sorted(STAGING_HIRELINGS.rglob("*.yaml")):
        document = safe_load(path)
        for profile in document.get("profiles") or []:
            profile["_file"] = str(path.relative_to(STAGING_HIRELINGS))
            out.append(profile)
    return out


def safe_load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def staged_fees() -> dict[str, dict]:
    """``{profile_id: entry}`` de las entradas de contratación del árbol."""
    return fee_index(CAMPAIGN_DOC)


def reference_stems(profile: dict) -> list[str]:
    """Nombres de fichero (stem) de los PDFs que el árbol cita para el perfil."""
    stems: list[str] = []
    for ref in profile.get("source_refs") or []:
        url = str(ref.get("url") or "")
        stem = url.rsplit("/", 1)[-1].replace(".pdf", "").replace("%20", " ")
        stem = ALIASES.get(stem, stem)
        if CORPUS.pdf_for(stem) is not None and stem not in stems:
            stems.append(stem)
    return stems


def printed_name_candidates(name: str) -> list[str]:
    """Formas con las que la entrada puede nombrar al personaje.

    Sólo formas de cinco letras o más: un recorte corto (``Fire`` de Fire-Eater)
    aparece en la prosa de cualquier vecino —«set on fire»— y haría que la entrada
    de ese vecino se tomara por la del personaje.
    """
    candidates = [name, name.replace("Necromancer", "").strip(),
                  " ".join(name.split()[-2:]), name.split("-")[0].split(",")[0].strip()]
    candidates += [part.strip() for part in re.split(r"[,\-]", name)]
    anchor = PROFILE_ANCHORS.get(name)
    if anchor:
        candidates.append(anchor)
    return [c for c in dict.fromkeys(candidates) if len(c) >= 5]


def package_of(profile: dict, campaign: dict) -> Package:
    """Lo que el paquete declara del personaje, listo para cotejar."""
    rating = profile.get("warband_rating") or {}
    return Package(
        stats="".join(str(v) for v in (profile.get("characteristics") or {}).values()) or None,
        # Un ``base: 0`` con ``per_experience_point`` es la valoración que la fuente
        # no imprime (el rating de estos sacerdotes es experiencia): el chequeo se
        # da por verificado por ausencia en los dos lados, no como un cero.
        rating=rating.get("base", rating.get("value")) or None,
        rules=tuple(str(rule.get("name") or "") for rule in profile.get("rules") or []),
        fee=package_fee(campaign.get("hiring_fee")),
        upkeep=package_fee(campaign.get("upkeep")),
    )


# --------------------------------------------------------------------------- #
# Localización de la entrada impresa
# --------------------------------------------------------------------------- #

def locate(profile: dict, stem: str) -> tuple[int, dict | None] | None:
    """Página y entrada impresa del perfil dentro de un PDF.

    El prefiltro por texto plano descarta las páginas que ni nombran al personaje
    ni llevan su fila de stats (contigua, que es como la imprime la fuente); la
    geometría se lee sólo en las candidatas, que es lo caro.

    Cada entrada candidata se puntúa por su encabezado (el nombre que la fuente
    imprime) y por su fila de stats (lo que imprime); el personaje es la entrada
    mejor puntuada. La fila sola no basta cuando dos vecinos comparten fila —el
    Halfling Fence y el Halfling Pimp imprimen los mismos nueve dígitos—, y el
    encabezado solo no basta cuando la fila del paquete está mal y hay que
    enseñarla. Identificar al personaje por su nombre en la prosa del vecino es lo
    que atribuía al Fire-Eater la tarifa del Midshipman («set on fire» vive en la
    regla Rigger): eso ya no se hace — sin fila ni encabezado se declara sin
    entrada en vez de inventar un hallazgo.
    """
    digits = "".join(str(v) for v in (profile.get("characteristics") or {}).values())
    candidates = printed_name_candidates(profile["name"])
    wanted = {digits_row(digits), digits_row(digits, swap=True)} if digits else set()
    pages: list[int] = []
    for page in range(1, CORPUS.page_count(stem) + 1):
        text = CORPUS.page_text(stem, page)
        lowered = normalize(text)
        page_digits = re.sub(r"\D", "", normalize(text))
        if (any(normalize(c) in lowered for c in candidates)
                or any(w and w in page_digits for w in wanted)):
            pages.append(page)
    best: tuple[int, int, dict] | None = None
    for page in pages:
        for entry in CORPUS.entries(stem, page):
            heading_hit = any(normalize(c) in normalize(entry["heading"]) for c in candidates)
            row_hit = bool(wanted & set(stat_rows(entry)))
            if not (heading_hit or row_hit):
                continue
            score = (2 if heading_hit else 0) + (1 if row_hit else 0)
            if best is None or score > best[0]:
                best = (score, page, entry)
    if best is not None:
        entry = dict(best[2])
        entry["spillover"] = (CORPUS.continuation(stem, best[1], profile["name"], TREE_NAMES,
                                                  candidates_for=printed_name_candidates)
                              if entry.get("last_on_page") else "")
        return best[1], entry
    if pages:
        return pages[0], None
    return None


# --------------------------------------------------------------------------- #
# El cotejo
# --------------------------------------------------------------------------- #

def check_one(profile: dict, campaign: dict) -> dict:
    """Coteja un perfil contra la fuente que lo imprime."""
    row = {"name": profile["name"], "file": profile["_file"], "id": profile.get("id"),
           "checks": [], "findings": [], "notes": [], "comparable": False}
    adjudicated = profile.get("normalization_status") == "out_of_scope"
    coverages: list[Coverage] = []
    for stem in reference_stems(profile):
        hit = locate(profile, stem)
        if hit is None:
            row["notes"].append(f"PDF no cacheado: {stem}")
            continue
        page, entry = hit
        if entry is None:
            row["notes"].append(
                f"{stem} p{page} nombra al personaje pero no imprime su entrada de "
                f"contratación (perfil sólo en las listas de contratación)")
            continue
        (BLOCKS / f"{profile['name'].replace(',', '').replace(' ', '_')}.txt").write_text(
            f"### {stem} p{page}\n" + "\n".join(entry["lines"]) + "\n", encoding="utf-8")
        coverage = Coverage()
        compare(entry, package_of(profile, campaign), coverage)
        coverages.append(coverage)
    if not coverages:
        if adjudicated:
            row["notes"].append(f"adjudicado `out_of_scope`: "
                                f"{profile.get('out_of_scope_reason') or 'sin entrada impresa'}")
        if not row["notes"]:
            row["notes"].append("sin fuente cacheada que cotejar")
        return row
    if adjudicated:
        row["notes"].append(f"adjudicado `out_of_scope`: "
                            f"{profile.get('out_of_scope_reason') or 'sin entrada impresa'}"
                            f" — se coteja lo que la fuente imprime")
    report = merge(coverages).report()
    # El cotejo se suma a lo que el driver ya anotó (la adjudicación del perfil).
    report["notes"] = row["notes"] + report["notes"]
    row.update(report)
    row["comparable"] = True
    return row


def main() -> int:
    only = set(sys.argv[1:])
    BLOCKS.mkdir(parents=True, exist_ok=True)
    fees = fee_index(CAMPAIGN_DOC)
    document = profiles()
    TREE_NAMES[:] = [profile["name"] for profile in document]
    rows = []
    for profile in document:
        if only and profile["name"] not in only:
            continue
        rows.append(check_one(profile, fees.get(str(profile.get("id"))) or {}))
    write_report(rows, OUT / "hirelings_check.json")
    print_report(rows, "hirelings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
