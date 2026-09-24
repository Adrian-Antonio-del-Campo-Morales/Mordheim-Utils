# -*- coding: utf-8 -*-
"""Cotejo de los Dramatis Personae de 2A contra su fuente mordheimer.net.

Los perfiles ya promocionados viven en el catálogo del árbol de conocimiento
(``sources/knowledge/catalog/hirelings/dramatis-personae``) y su tarifa en el
documento de contratación de campaña, que es donde el árbol la guarda. La fuente
es la página de mordheimer.net, y la lectura la hace el lector compartido
(``printed_entries``): la página trae sus entradas como ``div`` con clase propia
y su tabla de perfiles como filas con una celda por columna, así que la lectura
por geometría aquí es la estructura del documento. Es lo que impide el defecto
que este cotejo tenía —partía del texto aplanado y atribuía al personaje la
tarifa y el rating del vecino de columna: Gwen aparecía con los 75/30 del Dark
Jester y el Foole con los 70/35 de Sigmund, que son los del personaje contiguo—.

Aquí vive sólo lo que es de este árbol: qué página imprime a cada personaje
(``source_for``, resuelta desde sus ``source_refs``), qué declara el catálogo y
qué etiquetas de regla son **editoriales** —las que el catálogo escribe y la
fuente no imprime como etiqueta, sino como un párrafo con otro nombre—, que se
declaran con su evidencia y quedan como nota en vez de como hallazgo.

Salida: JSON con verificaciones y hallazgos más la cobertura por chequeo, y las
entradas extraídas en ``build/cache/2a-dp/dramatis-blocks/`` para lectura manual.

Uso: python check_2a_dramatis.py [nombre del perfil ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# El driver re-exporta las piezas del lector que usa su batería de pruebas
# (``fees_in``, ``stat_rows``, ``CHECKS``) además de las que emplea.
from printed_entries import (  # noqa: F401
    CHECKS,
    Coverage,
    HtmlCorpus,
    Package,
    TextCorpus,
    compare,
    digits_row,
    fee_index,
    fees_in,
    merge,
    normalize,
    package_fee,
    print_report,
    stat_rows,
    write_report,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "sources/knowledge/catalog/hirelings/dramatis-personae"
CAMPAIGN_DOC = ROOT / "sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml"
CACHE = ROOT / "build/cache/2a-dp"
OUT = CACHE / "dp_check.json"
BLOCKS = CACHE / "dramatis-blocks"

# Etiquetas de regla que el catálogo escribe y la fuente no imprime como etiqueta.
# La regla se coteja por su hecho impreso —que sí está en la entrada— y la
# etiqueta queda como nota con su evidencia.
EDITORIAL = {
    "Conditional Acceptance — Good-Aligned Employers": (
        "la fuente imprime la elegibilidad como el párrafo «May Be Hired: Any "
        "Mercenaries, Sisters of Sigmar and Witch Hunters may hire William. "
        "Furthermore, any good-aligned warband may hire William on a roll of 4+», "
        "y el catálogo la modela como regla del perfil; el mismo hecho está en "
        "`eligibility.allow_groups` del documento de campaña"),
}


# --------------------------------------------------------------------------- #
# El paquete y la fuente
# --------------------------------------------------------------------------- #

def catalogue() -> list[dict]:
    """Los perfiles de Dramatis Personae del catálogo, con su fichero."""
    out = []
    for path in sorted(CATALOGUE.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for profile in document.get("profiles") or []:
            profile["_file"] = str(path.relative_to(CATALOGUE))
            out.append(profile)
    return out


def package_of(profile: dict, campaign: dict) -> Package:
    """Lo que el catálogo declara del personaje, listo para cotejar."""
    rating = profile.get("warband_rating") or {}
    return Package(
        stats="".join(str(v) for v in (profile.get("characteristics") or {}).values()) or None,
        # Un ``base: 0`` con ``per_experience_point`` es la valoración que la fuente
        # no imprime: el chequeo se da por verificado por ausencia en los dos lados.
        rating=rating.get("base", rating.get("value")) or None,
        rules=tuple(str(rule.get("name") or "") for rule in profile.get("rules") or []),
        fee=package_fee(campaign.get("hiring_fee")),
        upkeep=package_fee(campaign.get("upkeep")),
    )


def source_slugs(profile: dict) -> list[str]:
    """Los nombres con los que la página que imprime al perfil se cachea.

    El cotejo guarda cada página bajo ``dramatis-<slug>``, con el slug que su
    ``url`` de ``source_refs`` declara (``.../dramatis-personae/grade-2a``).
    """
    slugs: list[str] = []
    for ref in profile.get("source_refs") or []:
        url = str(ref.get("url") or "").rstrip("/")
        slug = url.rsplit("/", 1)[-1] if url else ""
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def corpus_for(slug: str):
    """La página cacheada de un slug: primero la estructura, luego su texto.

    El HTML es la lectura buena (trae las entradas y las celdas de la tabla); el
    texto plano es el respaldo, con el ancla ``Source:`` separando las entradas,
    y sin geometría no puede leer una fila partida ni una de dos cifras.
    """
    path = CACHE / f"dramatis-{slug}.html"
    if path.is_file():
        return HtmlCorpus(path), "html"
    path = CACHE / f"dramatis-{slug}.txt"
    if path.is_file():
        return TextCorpus(path), "text"
    return None, ""


def locate(profile: dict, entries: list[dict]) -> dict | None:
    """La entrada impresa del perfil dentro de una página.

    Se puntúa como en 2B: el encabezado impreso (el ``h2`` del personaje) vale
    más que la fila de stats, y una entrada que no trae ni uno ni otro no puede
    tomarse por la del personaje —identificarlo por su nombre en la prosa del
    vecino es lo que atribuía a Gwen la tarifa del Jester—.
    """
    digits = "".join(str(v) for v in (profile.get("characteristics") or {}).values())
    candidates = printed_name_candidates(profile["name"])
    wanted = {digits_row(digits), digits_row(digits, swap=True)} if digits else set()
    best: tuple[int, dict] | None = None
    for entry in entries:
        heading_hit = any(normalize(c) in normalize(entry["heading"]) for c in candidates)
        row_hit = bool(wanted & set(stat_rows(entry)))
        if not (heading_hit or row_hit):
            continue
        score = (2 if heading_hit else 0) + (1 if row_hit else 0)
        if best is None or score > best[0]:
            best = (score, entry)
    return best[1] if best else None


def printed_name_candidates(name: str) -> list[str]:
    """Formas con las que la entrada puede nombrar al personaje.

    Sólo formas de cinco letras o más: un recorte corto aparece en la prosa de
    cualquier vecino y haría que su entrada se tomara por la del personaje.
    """
    candidates = [name, " ".join(name.split()[-2:]), name.split(",")[0].strip()]
    candidates += [part.strip() for part in re.split(r"[,\-—]", name)]
    return [c for c in dict.fromkeys(candidates) if len(c) >= 5]


# --------------------------------------------------------------------------- #
# El cotejo
# --------------------------------------------------------------------------- #

def check_one(profile: dict, campaign: dict) -> dict:
    """Coteja un perfil contra la página que lo imprime."""
    row = {"name": profile["name"], "file": profile["_file"], "id": profile.get("id"),
           "checks": [], "findings": [], "notes": [], "comparable": False}
    if profile.get("normalization_status") == "out_of_scope":
        row["notes"].append(f"adjudicado `out_of_scope`: "
                            f"{profile.get('out_of_scope_reason') or 'sin entrada impresa'}"
                            f" — se coteja lo que la fuente imprime")
    coverages: list[Coverage] = []
    for slug in source_slugs(profile):
        corpus, kind = corpus_for(slug)
        if corpus is None:
            row["notes"].append(f"página no cacheada: dramatis-{slug}.html")
            continue
        entry = locate(profile, corpus.entries())
        if entry is None:
            row["notes"].append(f"{slug} no imprime una entrada propia del personaje "
                                f"(lo nombra la prosa o la lista de la página)")
            continue
        (BLOCKS / f"{profile['name'].replace(',', '').replace(' ', '_')}.txt").write_text(
            f"### dramatis-{slug} ({kind})\n" + "\n".join(entry["lines"]) + "\n",
            encoding="utf-8")
        coverage = Coverage()
        compare(entry, package_of(profile, campaign), coverage, editorial=EDITORIAL)
        coverages.append(coverage)
    if not coverages:
        if not row["notes"]:
            row["notes"].append("sin página cacheada que cotejar")
        return row
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
    rows = []
    for profile in catalogue():
        if only and profile["name"] not in only:
            continue
        rows.append(check_one(profile, fees.get(str(profile.get("id"))) or {}))
    write_report(rows, OUT)
    print_report(rows, "dramatis personae")
    return 0


if __name__ == "__main__":
    sys.exit(main())
