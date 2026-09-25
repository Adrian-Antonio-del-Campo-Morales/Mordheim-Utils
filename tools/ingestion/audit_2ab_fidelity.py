# -*- coding: utf-8 -*-
"""Fidelidad y cobertura del staging 2A/2B contra las fuentes originales.

Dos direcciones, por banda:

**Paquete → fuente (fiel).** Cada artefacto debe rastrearse hasta la fuente: el
nombre (perfil, regla, lista, objeto), la fila de características y la prosa del
`effect`. La prosa se compara por cobertura de tokens en orden — coincidencia
literal, casi literal (≥ 0.9), condensada (≥ 0.6) o ausente — y se contrasta
también con el texto canónico de las reglas compartidas de la KB y con los
documentos suplementarios cacheados, para no marcar como divergencia lo que
simplemente viene de otro documento.

**Fuente → paquete (completa).** Cada línea de perfil impresa (nombre + nueve
características) debe tener un perfil; las que no lo tienen se listan para
revisión. Una fila que no está en el paquete pero sí en otro documento del mismo
árbol (antologías KAZ/REL/MiM, tablas de máximos, monturas del catálogo) se
informa aparte como `source-row-other-document`, no como hueco.

La fila impresa se lee por **estructura**, en las tres formas en que las fuentes
la imprimen: la línea física de la página (la fila con su nombre en la celda que
lleva los valores), el orden de lectura de la columna (la fila en su propia línea,
sin nombre, titulada por el encabezado de su entrada —los Dramatis y las páginas a
dos columnas de Relics of the Crusades—) y el documento de la página web de 2A (la
fila leída de su tabla, una celda por columna, con el nombre del encabezado que la
titula cuando la tabla no lo imprime). La ventana de tokens del texto aplanado
queda sólo como respaldo de la fuente que no tiene lectura estructural: además de
mezclar la fila con la prosa de la columna vecina, un paréntesis la hace inventar
una fila que la página no imprime.

Los paquetes que comparten un documento impreso (declarados en `packages` del
manifiesto) resuelven la misma fuente en caché, de modo que ninguno queda sin
cotejar.

Normalización del texto extraído: comillas tipográficas, guiones de corte de
línea, palabras partidas por el extractor («T ongue»), diacríticos, mayúsculas,
plurales y puntuación. Las bandas escaneadas (sin capa de texto) se marcan
`source-scanned`: sus datos se verificaron por imagen y este auditor no puede
juzgarlas.

Uso::

    python tools/ingestion/audit_2ab_fidelity.py                 # 2A + 2B
    python tools/ingestion/audit_2ab_fidelity.py --tree 2B
    python tools/ingestion/audit_2ab_fidelity.py --band house-guard-sc --show 20
    python tools/ingestion/audit_2ab_fidelity.py --json > build/cache/fidelity.json
"""
from __future__ import annotations

import argparse
import difflib
import functools
import glob
import json
import os
import pathlib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from typing import Mapping, Sequence

import yaml

# La lectura de la fuente es la del lector compartido (``printed_entries``), no la
# extracción con ``pdftotext -layout``: una tabla o una lista se leen de la línea
# y de la celda que las imprimen, con las columnas separadas por el canal de la
# página, en vez de una ventana del texto aplanado que mezcla la columna vecina.
# Las páginas web de 2A se leen por la **estructura del documento** que ya usa su
# cotejo (encabezados, tramos y tablas), y las páginas a dos columnas por el orden
# de lectura del lector: en ninguno de los dos casos queda una fila leída de una
# ventana de tokens de prosa. El lector vive en ``tools/knowledge``: es permanente,
# no propio de esta fase.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "knowledge"))
from printed_entries import (HtmlDocument, PdfCorpus, cell_value, cells as printed_cells,
                             fee_line, flat, list_rows, price_rows, profile_name,
                             profile_tables, stat_header)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TREES = ('2A', '2B')
SOURCE_TEXT = {'2A': 'build/cache/2a-sources/text', '2B': 'build/cache/2b-pdfs/text'}
# Las páginas web de 2A se cachean en HTML: su documento es la otra lectura de la
# fuente, y la que lee sus tablas de perfil por estructura.
SOURCE_HTML = {'2A': 'build/cache/2a-sources/pages', '2B': None}
# El árbol cuyo documento impreso se lee por geometría. 2A no tiene PDF cacheado:
# sus fuentes son páginas web y su lector propio es el de ``audit_2a_sources``.
SOURCE_PDF = {'2A': None, '2B': 'build/cache/2b-pdfs'}
SOURCE_EXTRA = {'2A': None, '2B': 'build/cache/2b-pdfs/extra'}
KB_SHARED = 'sources/knowledge/catalog/rules'
# Bandas cuyo PDF no tiene capa de texto: verificadas leyendo la imagen.
SCANNED = {'clan-angrund-kep', 'crooked-moon-kep', 'slave-uprising-kep'}
# Las palabras con que una fuente imprime el nombre de un objeto del catálogo, con el
# sitio donde se leyó cada una, viven en un solo registro compartido con los otros dos
# cotejos (`printed_wordings`): la fila se coteja con la palabra que la fuente escribe
# —«Holy Water» para `blessed_water`, «Wardog» para `warhound`, «Horsemens Hammer» para
# `horsemans_hammer` y «Warplock Pistol» para `warp_pistol`— y el id y el nombre del KB
# no se renombran. El mismo registro lleva las listas que la fuente **delega** al
# reglamento en vez de imprimirlas (el KAZ skaven): sus filas no están en el corpus y se
# declaran con ese motivo, no como hueco. La adjudicación de cada pareja está en
# `sources/2A/discrepancy-verdicts.md` §9 y `sources/2B/discrepancy-verdicts.md` §7/§15.4.
import printed_wordings as wordings

CELL = re.compile(r'^(?:\d{1,2}[A-Za-z*]?|2D6|D6|D3|\d\+|-$)$')
PAGE = re.compile(r'^=+ page \d+ =+$')
STAT_WORDS = {'m', 'ws', 'bs', 's', 't', 'w', 'i', 'a', 'ld'}
VOWELS = 0.9
NEAR = 0.9
CONDENSED = 0.6
# A rule that only points at another rule or at the rulebook carries no prose of its
# own, so its effect cannot be compared against the source.
CROSS_REF = re.compile(r'^(?:see|ver)\b[^.]{0,110}\.?$', re.IGNORECASE)
# The labels a source prints for its own rules: «Label: prose» inline special rules and
# short standalone headings followed by a sentence (skill entries, sub-sections).
LABEL_LINE = re.compile(r"^([A-Z][A-Za-z'\u2019\-\u00ad ]{2,38}):\s+\S")
HEADING_LINE = re.compile(r"^([A-Z][A-Za-z'\u2019\-\u00ad ]{2,38})$")
# Structural words a source uses as column headers, not as rule names.
LABEL_NOISE = {
    'availability', 'range', 'strength', 'special rules', 'special rule', 'cost', 'costs', 'profile',
    'base', 'weapons', 'armour', 'equipment list', 'note', 'notes', 'see above', 'choice of warriors',
    'starting experience', 'henchmen', 'heroes', 'mordheim', 'total', 'skills', 'wargear', 'save',
    'movement', 'skill', 'hand-to-hand combat weapons', 'missile weapons', 'miscellaneous equipment',
    'shields', 'maximum characteristics', 'characteristic increase', 'starting gold', 'hire', 'upkeep',
    'rating', 'may be hired', 'restrictions', 'special', 'description', 'effect', 'duration',
    'difficulty', 'type', 'name', 'result', 'roll', 'd6', 'save modifier', 'range strength',
    # Weapon and armour rule labels: the catalogue items carry these, not the band.
    'two-handed', 'two handed', 'one or two-handed', 'parry', 'concussion', 'scales', 'heavy',
    'cannot be parried', 'strike first', 'strike last', 'critical damage', 'small target',
    'whipcrack', 'thrown weapon', 'thrown weapons', 'armour save', 'armor', 'cavalry bonus',
    'pair', 'miscellaneous', 'rare', 'acquiring', 'range strength special rules',
}
# A line that is a table header or a split stat row ("Name Range Strength Special
# Rules", "S T W I A Ld"), not a rule the source prints.
TABLE_HEADER = re.compile(
    r'^(?:names?|m|ws|bs|s|t|w|i|a|ld|gc|roll|d6|d3|\dx|statistics?|profile)\b[\s\w]*$',
    re.IGNORECASE)
# Fiction bylines ("By Jack Yeovil") introduced by the anthology, not rules.
BYLINE = re.compile(r'^by [a-z]', re.IGNORECASE)
# A rule name never ends in one of these; a sentence fragment lifted by the label
# regex always does ("Standing on the disputed border of", "Hero's XP value in").
STOP_TAIL = frozenset({
    'the', 'of', 'in', 'and', 'to', 'a', 'an', 'or', 'with', 'on', 'for', 'at', 'by',
    'from', 'as', 'into', 'over', 'that', 'they', 'are', 'there', 'is', 'its', 'his',
    'her', 'their', 'this', 'these', 'those', 'if', 'when', 'has', 'have', 'was', 'were',
})
# Rule names in these sources are short; a longer run is prose the label regex caught.
LABEL_MAX_WORDS = 5


def is_label_noise(label: str) -> bool:
    """Whether a candidate label is a header, a stat fragment, a byline or prose."""
    tokens = label.split()
    if not tokens or len(tokens) > LABEL_MAX_WORDS:
        return True
    if BYLINE.match(label) and len(tokens) <= 3:
        return True
    if TABLE_HEADER.match(label):
        return True
    if all(token.lower().rstrip('.') in STAT_WORDS or token.lower() in ('ld', 'gc')
           for token in tokens):
        return True
    if sum(1 for token in tokens if len(token) == 1) > 1:
        return True
    # Estructura impresa, no reglas: titulares en mayúsculas («BRIGAND SKILL TABLE»),
    # encabezados de tabla de habilidades y de listas de hechizos.
    if label.isupper():
        return True
    low = [token.lower() for token in tokens]
    if 'skill' in low and any(token in ('table', 'tables', 'list', 'lists') for token in low):
        return True
    if low[:2] == ['spells', 'of']:
        return True
    if tokens[-1].lower().rstrip(',;:') in STOP_TAIL:
        return True
    return False


def repair_split(text: str, vocab: set[str]) -> str:
    """«T wo-handed» → «Two-handed»: the extractor splits a word after its first letter.

    The merge only happens when the joined word is a word the corpus already uses, so
    ordinary prose («A model…») is never glued together.
    """
    def join(match: re.Match) -> str:
        merged = match.group(1) + match.group(2)
        return merged if stem(normalize(merged)) in vocab else match.group(0)
    return re.sub(r'\b([A-Za-z])\s+([a-z][A-Za-z\'-]+)', join, text)


def rule_names(tree: str) -> set[str]:
    """Normalized names of every rule and band the tree writes.

    Labels are compared against these names, so a source typo («Beserker») still finds
    the package's own rule («Berserker»).
    """
    out: set[str] = set()
    for path in sorted(glob.glob(os.path.join(ROOT, 'sources', tree, 'bands', '*', '*', '*.yaml'))):
        for doc in docs(path):
            for key in ('rules', 'profiles', 'equipment_lists'):
                for entry in doc.get(key) or []:
                    if isinstance(entry, dict) and entry.get('name'):
                        out.add(normalize(str(entry['name'])))
            if doc.get('name'):
                out.add(normalize(str(doc['name'])))
    return out


def band_names(tree: str) -> set[str]:
    """Band names of the tree: another warband's chapter heading is not this band's rule."""
    out: set[str] = set()
    for path in sorted(glob.glob(os.path.join(ROOT, 'sources', tree, 'bands', '*', '*', 'band.yaml'))):
        for doc in docs(path):
            for key in ('name', 'canonical_family'):
                if doc.get(key):
                    out.add(normalize(str(doc[key])))
    return out


def catalogue_names(tree: str) -> set[str]:
    """Names of the catalogued entries a source label may legitimately be.

    Band special skills, equipment special rules, prayers and spells are catalogued
    (the KB keeps them in `catalog/skills`, `catalog/items`, `catalog/mechanics`), so a
    source label that names one of them is modelled even when the band package only
    references it by id.
    """
    out: set[str] = set()
    for _, entry in catalogue_entries(tree):
        name = str(entry.get('name') or '')
        if name:
            out.add(normalize(name))
    return out


def catalogue_entries(tree: str) -> list[tuple[str, dict]]:
    """Every catalogued entry of the KB and of the staging tree, at any depth.

    Weapon and equipment special rules («Swift», «Wicked Edge», «Beastbane») are
    sub-entries of the item that prints them — `special_rules` of the item, or a
    mechanic of the KB — so the walk is recursive and the name of every dict counts.
    """
    out: list[tuple[str, dict]] = []
    patterns = [os.path.join(ROOT, 'sources', 'knowledge', 'catalog', '**', '*.yaml'),
                os.path.join(ROOT, 'sources', tree, 'catalog', '**', '*.yaml')]
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            for doc in docs(path):
                stack = [doc]
                while stack:
                    node = stack.pop()
                    if isinstance(node, dict):
                        if node.get('name'):
                            out.append((path, node))
                        stack.extend(node.values())
                    elif isinstance(node, list):
                        stack.extend(node)
    return out


def catalogue_text(tree: str) -> str:
    """Normalized prose of the catalogue: where an item defines its special rules."""
    if tree not in _CATALOGUE_TEXT:
        # Every string of every catalogue document counts, not only `effect` fields: a
        # chart keeps its entries as `- roll: 3 / result: 'Gglbddlh: …'` and a companion
        # as its own sub-entry, and both are catalogued content.
        chunks: list[str] = []
        for pattern in (os.path.join(ROOT, 'sources', 'knowledge', 'catalog', '**', '*.yaml'),
                        os.path.join(ROOT, 'sources', tree, 'catalog', '**', '*.yaml')):
            for path in glob.glob(pattern, recursive=True):
                for doc in docs(path):
                    stack = [doc]
                    while stack:
                        node = stack.pop()
                        if isinstance(node, str):
                            chunks.append(node)
                        elif isinstance(node, dict):
                            stack.extend(node.values())
                        elif isinstance(node, list):
                            stack.extend(node)
        _CATALOGUE_TEXT[tree] = normalize('\n'.join(chunks))
    return _CATALOGUE_TEXT[tree]

def band_region(text: str, section: str) -> str:
    """The part of a shared document that belongs to this package's own section.

    Anthology extracts (KAZ, REL, MiM) carry the whole campaign book, so the labels of
    every other chapter would look unmodelled; scanning from the package's own section
    heading forward keeps the comparison inside its region.
    """
    if not section:
        return text
    head = [word for word in normalize(section).split() if len(word) > 2][:2]
    if not head:
        return text
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if phrase_near(head, words(line), window=4):
            return '\n'.join(lines[index:])
    return text


def source_rule_labels(text: str, section: str) -> list[str]:
    """Rule labels the source prints (see `LABEL_LINE` / `HEADING_LINE`)."""
    lines = band_region(text, section).splitlines()
    out: list[str] = []
    for index, line in enumerate(lines):
        line = line.rstrip()
        match = LABEL_LINE.match(line)
        if match:
            out.append(match.group(1).strip())
            continue
        match = HEADING_LINE.match(line)
        if match and index + 1 < len(lines):
            following = lines[index + 1]
            if len(following.split()) >= 5 and following[:1].isupper():
                out.append(match.group(1).strip())
    return out
# «M 6, WS 4, BS 4, S 6, …» inside a maximum-characteristics rule.
STAT_ROW_PROS = re.compile(
    r'M\s*[=:]?\s*(\d+)\s*[,\s]+WS\s*[=:]?\s*(\d+)\s*[,\s]+BS\s*[=:]?\s*(\d+)'
    r'\s*[,\s]+S\s*[=:]?\s*(\d+)\s*[,\s]+T\s*[=:]?\s*(\d+)\s*[,\s]+W\s*[=:]?\s*(\d+)'
    r'\s*[,\s]+I\s*[=:]?\s*(\d+)\s*[,\s]+A\s*[=:]?\s*(\d+(?:\+\d+)?)\s*[,\s]+Ld\s*[=:]?\s*(\d+)',
    re.IGNORECASE)


def deaccent(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in text if not unicodedata.combining(char))


def normalize(text: str) -> str:
    text = text.replace('\u00ad', '')
    text = re.sub(r'-\s*\n\s*', '', text)
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u00d7', 'x')
    text = deaccent(text).lower()
    # Parentheses are separators, not content: an editorial suffix («Equipment List
    # (Town Crier 6)») or a decorated cell («3(4)») must not glue itself to the next word.
    text = re.sub(r'[^a-z0-9\'".:%+*/\s-]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def simple_value(token: str) -> str:
    """A characteristic token stripped of its printed decoration.

    Sources print `1+1` for «one attack plus the bite» and `3(4)` for a Strength that
    changes under a special rule; the package stores the base value.
    """
    match = re.fullmatch(r'(\d+)(?:\+\d+)?(?:\(\d+\))?', token)
    return match.group(1) if match else token


def stem(word: str) -> str:
    """Plural-insensitive comparison key («heroes»/«hero», «houses»/«house»)."""
    if len(word) > 4 and word.endswith('es'):
        word = word[:-2]
    elif len(word) > 3 and word.endswith('s') and not word.endswith('ss'):
        word = word[:-1]
    return word[:-1] if len(word) > 4 and word.endswith('e') else word


def loose(text: str) -> str:
    """Comparison key that ignores apostrophes and hyphen/space/slash spelling.

    The KB keeps the object's canonical name («Cat O Nine Tails», «Thing Catcher»)
    while the printed list writes it its own way («Cat o' nine tails»,
    «Thing-catcher»); neither is a divergence, so the catalogue cross-check folds
    both spellings together. The slash is a separator too: the KB spells a
    combined entry with an underscore (`mace_hammer`) and the printed list with a
    slash («Mace/Hammer»).
    """
    text = text.replace("'", '').replace('’', '')
    return re.sub(r'[\s/-]+', ' ', text).strip()


def words(text: str) -> list[str]:
    """Tokens de cotejo, sin el punto con el que el extractor escribe el espacio.

    El ``text layer`` de las páginas de Relics separa las palabras con puntos
    (``the.Bitter.`` / ``Enmity.result``), así que un token que es sólo puntos, o
    que acaba en punto, no lleva texto: dejarlo dentro del flujo parte en dos la
    frase que la página imprime junta (``bitter . enmity``) y ningún nombre ni
    efecto casa. No ocurre con la puntuación real de una frase, que aquí no se
    coteja: los cotejos de este auditor son de palabras, no de sintaxis.
    """
    return [token for token in (token.strip('.') for token in normalize(text).split())
            if token]


def coverage(package_words: list[str], source_words: list[str]) -> float:
    if not package_words:
        return 1.0
    matcher = difflib.SequenceMatcher(None, package_words, source_words, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return matched / len(package_words)


def join_spaced_letters(source_words: list[str], vocab: set[str]) -> list[str]:
    out: list[str] = []
    index = 0
    while index < len(source_words):
        if index + 1 < len(source_words) and len(source_words[index]) == 1:
            candidate = source_words[index] + source_words[index + 1]
            if candidate in vocab:
                out.append(candidate)
                index += 2
                continue
        out.append(source_words[index])
        index += 1
    return out


def phrase_near(needle: list[str], haystack: list[str], window: int = 3) -> bool:
    """Whether `needle` appears in order in `haystack`, allowing gaps and plurals.

    The gap is measured from the last matched token (not from the match count, which
    is what made a two-word needle behave differently in long documents).
    """
    if not needle:
        return True
    position = 0
    last = -1
    for index, word in enumerate(haystack):
        if stem(word) == stem(needle[position]):
            position += 1
            last = index
            if position == len(needle):
                return True
        elif position and index - last > window:
            # too far apart: this token may still open a fresh run
            position = 1 if stem(word) == stem(needle[0]) else 0
            last = index if position else -1
    return False


def numbers_in_order(numbers: list[str], haystack: list[str], window: int = 5) -> bool:
    """Whether a run of characteristic values appears in the extracted tokens.

    A maximum-characteristics rule prints its values as prose («M 6, WS 6, …») while
    the source prints them as a table row («Troll 6 6 3 6 5 5 4 6 6»); comparing the
    values in order, with gaps for the interleaved header cells, ties both together.
    """
    position = 0
    last = -1
    for index, word in enumerate(haystack):
        if word == numbers[position]:
            position += 1
            last = index
            if position == len(numbers):
                return True
        elif position and index - last > window:
            position = 1 if word == numbers[0] else 0
            last = index if position else -1
    return False


def band_dir(tree: str, band: str) -> str:
    return os.path.join(ROOT, 'sources', tree, 'bands', 'mordheim', band)


def docs(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as handle:
        return [d for d in yaml.safe_load_all(handle) if isinstance(d, dict)]


@functools.lru_cache(maxsize=None)
def read_source(path: str) -> str:
    # Supplement caches are not all UTF-8 (some carry latin-1 bytes from the PDF text layer).
    raw = open(path, encoding='utf-8', errors='replace').read()
    return '\n'.join(line for line in raw.splitlines() if not PAGE.match(line.strip()))


_READERS: dict[tuple[str, str], object] = {}


def page_reader(tree: str, which: str = 'band'):
    """El lector compartido de la geometría de las páginas del árbol, o None.

    ``band`` lee el documento de cada paquete; ``extra`` los capítulos
    suplementarios que el árbol cachea aparte (anuales y especialistas), que antes
    se leían también con ``pdftotext -layout``.
    """
    key = (tree, which)
    if key not in _READERS:
        base = SOURCE_EXTRA[tree] if which == 'extra' else SOURCE_PDF[tree]
        if not base:
            _READERS[key] = None
        else:
            cache = pathlib.Path(ROOT, base)
            suffix = '-extra' if which == 'extra' else ''
            _READERS[key] = PdfCorpus(cache, cache / f'words{suffix}',
                                      cache / f'text-geometry{suffix}')
    return _READERS[key]


def source_groups(tree: str) -> dict[str, list[str]]:
    """Band id → the manifest source ids whose cached text carries it.

    Two packages may share one printed document (the manifest declares them under a
    single row's `packages`), so their source text is cached once under the row id.
    """
    groups: dict[str, list[str]] = {}
    path = os.path.join(ROOT, 'sources', tree, 'manifest.yaml')
    if not os.path.exists(path):
        return groups
    with open(path, encoding='utf-8') as handle:
        manifest = yaml.safe_load(handle) or {}
    for row in manifest.get('bands') or []:
        row_id = str(row.get('id') or '')
        members = [row_id] + [str(item) for item in row.get('packages') or []]
        for member in members:
            if member:
                groups[member] = members
    return groups


_DOCUMENTS: dict[tuple[str, str], HtmlDocument | None] = {}


def page_document(tree: str, band: str) -> HtmlDocument | None:
    """El documento de la página web del árbol, leído por su estructura, o ``None``.

    Es la lectura que el cotejo de 2A ya hace de sus páginas —el documento con sus
    encabezados, sus tramos y sus tablas— y la que permite leer sus tablas de
    perfil por sus celdas en vez de por una ventana de tokens de su texto.
    """
    key = (tree, band)
    if key not in _DOCUMENTS:
        base = SOURCE_HTML[tree]
        path = pathlib.Path(ROOT, base, f'{band}.html') if base else None
        _DOCUMENTS[key] = (HtmlDocument(path.read_text(encoding='utf-8', errors='replace'))
                           if path and path.is_file() else None)
    return _DOCUMENTS[key]


def source_documents(tree: str, band: str) -> list[tuple[str, str]]:
    """(label, text) of every reading of the document that may carry this band's data.

    La lectura plana del caché —la primera, la que da el orden de las líneas del
    extractor—, la lectura por geometría del lector compartido, que sustituye a la
    extracción con ``pdftotext -layout`` (aquélla conservaba las columnas a costa de
    comprimir sus desplazamientos, ésta las lee enteras y en su orden), y el
    documento de la página web leído por su estructura, que es como se leen las
    páginas de 2A: sus encabezados, sus tramos y sus tablas.
    """
    out: list[tuple[str, str]] = []
    ids = source_groups(tree).get(band) or [band]
    for source_id in ids:
        primary = os.path.join(ROOT, SOURCE_TEXT[tree], f'{source_id}.txt')
        if os.path.exists(primary):
            label = 'primary' if source_id == ids[0] else f'primary:{source_id}'
            out.append((label, read_source(primary)))
    reader = page_reader(tree)
    if reader is not None:
        for source_id in ids:
            if reader.pdf_for(source_id) is None:
                continue
            label = 'geometry' if source_id == ids[0] else f'geometry:{source_id}'
            out.append((label, reader.text(source_id)))
    document = page_document(tree, band)
    if document is not None:
        out.append(('page', document.text()))
    return out


_TREE_BLOBS: dict[str, str] = {}


def tree_yaml_blob(tree: str) -> str:
    """Every YAML document of the tree, raw: used to look up rows modelled elsewhere."""
    if tree not in _TREE_BLOBS:
        pattern = os.path.join(ROOT, 'sources', tree, '**', '*.yaml')
        files = sorted(glob.glob(pattern, recursive=True))
        _TREE_BLOBS[tree] = '\n'.join(
            open(path, encoding='utf-8', errors='replace').read() for path in files)
    return _TREE_BLOBS[tree]


_NORM_BLOBS: dict[str, tuple[str, set[str]]] = {}


def tree_norm_blob(tree: str) -> tuple[str, set[str]]:
    """Normalized text and comparison vocabulary of everything the tree models."""
    if tree not in _NORM_BLOBS:
        text = normalize(tree_yaml_blob(tree) + tree_doc_blob(tree))
        _NORM_BLOBS[tree] = (text, {stem(token) for token in text.split()})
    return _NORM_BLOBS[tree]


_CATALOGUE_TEXT: dict[str, str] = {}
_TREE_DOCS: dict[str, str] = {}


def tree_doc_blob(tree: str) -> str:
    """The staging prose of the tree (reviews, verdicts, merge notes).

    A row that only appears in these documents is one a reviewer already wrote out by
    hand — adjudicated evidence, not a modelled profile — so it is counted separately.
    """
    if tree not in _TREE_DOCS:
        pattern = os.path.join(ROOT, 'sources', tree, '**', '*.md')
        files = sorted(glob.glob(pattern, recursive=True))
        _TREE_DOCS[tree] = '\n'.join(
            open(path, encoding='utf-8', errors='replace').read() for path in files)
    return _TREE_DOCS[tree]


_FAMILIES: dict[str, tuple[set[str], set[tuple[str, ...]]]] = {}


def kb_family(family: str) -> tuple[set[str], set[tuple[str, ...]]]:
    """Names and characteristic rows the active KB band `family` defines.

    A package that declares `canonical_family` inherits its profiles from that KB
    band («use the exact same rules as the Da Mob Warband»), so they have no printed
    row in the package's own source.
    """
    if family not in _FAMILIES:
        names: set[str] = set()
        rows: set[tuple[str, ...]] = set()
        for path in glob.glob(os.path.join(ROOT, 'sources', 'knowledge', 'bands', '*', family,
                                           'profiles.yaml')):
            for doc in docs(path):
                for profile in doc.get('profiles') or []:
                    names.add(normalize(str(profile.get('name') or '')))
                    chars = profile.get('characteristics') or {}
                    rows.add(tuple(str(chars.get(key, '')) for key in
                                   ('M', 'WS', 'BS', 'S', 'T', 'W', 'I', 'A', 'Ld')))
        _FAMILIES[family] = (names, rows)
    return _FAMILIES[family]


def row_pattern(cells: list[str]) -> str:
    """Tolerant search pattern for a printed row inside YAML text.

    A '-' cell (no characteristic) may be modelled as a null value, so the cell
    matches any of the ways the trees spell it.
    """
    parts = []
    for cell in cells:
        if cell.isdigit():
            parts.append(re.escape(cell))
        else:
            # '-' (no characteristic) may be modelled as a null cell or simply omitted.
            parts.append(r'(?:-|null|none)?')
    return r'(?<![0-9])' + r'[\s\S]{0,90}?'.join(parts) + r'(?![0-9])'


def extra_documents(tree: str) -> list[tuple[str, str]]:
    """Supplementary chapters of the tree (MiM/MW/Marienburg chapters, provenance PDFs).

    Los capítulos suplementarios se leen con el mismo lector que el documento de la
    banda: son PDFs cacheados aparte y su lectura con ``pdftotext -layout`` era la
    otra mitad del mismo defecto.
    """
    out: list[tuple[str, str]] = []
    reader = page_reader(tree, 'extra')
    extra_dir = SOURCE_EXTRA[tree]
    # Sin caché el suplemento no existe: se declara el hueco, no se falla en seco.
    if reader is not None and extra_dir and os.path.isdir(os.path.join(ROOT, extra_dir)):
        for name in sorted(os.listdir(os.path.join(ROOT, extra_dir))):
            if not name.lower().endswith('.pdf'):
                continue
            stem = os.path.splitext(name)[0]
            if reader.pdf_for(stem) is None:
                continue
            out.append((f'extra-{stem}.txt', reader.text(stem)))
    text_dir = os.path.join(ROOT, SOURCE_TEXT[tree])
    for path in sorted(glob.glob(os.path.join(text_dir, '*-provenance*.txt'))):
        out.append((os.path.basename(path), read_source(path)))
    return out


def kb_models_row(name: str, cells: tuple[str, ...],
                  kb: tuple[set[tuple[str, ...]], set[str]]) -> bool:
    """¿El KB ya modela esta fila, con este nombre **y** estas características?

    El nombre solo no basta: el KB tiene un «Boss» de 4 3 4 3 3 1 4 1 7 y las
    páginas del KAZ imprimen un «Boss» de 4 4 3 4 4 1 3 1 8 que el KB no modela,
    así que darlo por cubierto por el nombre ocultaría la fila que el paquete
    tiene que modelar.
    """
    rows, names = kb
    if cells not in rows:
        return False
    wanted = normalize(name).split()
    return any(phrase_near(wanted, [row_name]) for row_name in
               (normalize(known) for known in names) if row_name)


def kb_rows() -> tuple[set[tuple[str, ...]], set[str]]:
    """Characteristic rows and profile names the active KB already defines."""
    rows: set[tuple[str, ...]] = set()
    names: set[str] = set()
    for path in glob.glob(os.path.join(ROOT, 'sources', 'knowledge', 'bands', '*', '*', 'profiles.yaml')):
        for doc in docs(path):
            for profile in doc.get('profiles') or []:
                chars = profile.get('characteristics') or {}
                rows.add(tuple(str(chars.get(key, '')) for key in ('M', 'WS', 'BS', 'S', 'T', 'W', 'I', 'A', 'Ld')))
                names.add(normalize(str(profile.get('name') or '')))
    return rows, names


def item_names(tree: str) -> dict[str, set[str]]:
    """Catalogue id → printed names, from the KB and from the staging catalogues."""
    out: dict[str, set[str]] = defaultdict(set)
    pattern = [os.path.join(ROOT, 'sources', 'knowledge', 'catalog', 'items', '*.yaml'),
               os.path.join(ROOT, 'sources', tree, 'catalog', 'items', '*.yaml')]
    for files in pattern:
        for path in sorted(glob.glob(files)):
            for doc in docs(path):
                for item in doc.get('items') or []:
                    item_id = str(item.get('id') or '')
                    name = str(item.get('name') or '')
                    if item_id:
                        out[item_id]
                        if name:
                            out[item_id].add(name)
    return out


def kb_shared_texts() -> list[tuple[str, list[str]]]:
    """(name, effect words) of the shared catalogue rules of the KB."""
    out: list[tuple[str, list[str]]] = []
    for path in sorted(glob.glob(os.path.join(ROOT, KB_SHARED, '*.yaml'))):
        for doc in docs(path):
            for rule in doc.get('rules') or []:
                words_ = words(str(rule.get('effect') or ''))
                if words_:
                    out.append((normalize(str(rule.get('name') or '')), words_))
    return out


def plausible_row(cells: list[str]) -> bool:
    """Nine characteristic cells that look like a stat line rather than a price run."""
    if not all(CELL.match(cell) for cell in cells):
        return False
    if sum(1 for cell in cells if re.fullmatch(r'\d+', cell)) < 6:
        return False
    numbers = [int(cell) if cell.isdigit() else 10 for cell in cells]
    if not 1 <= numbers[0] <= 10:                       # M
        return False
    if not 1 <= numbers[8] <= 10:                       # Ld
        return False
    for cell, index in zip(cells, range(9)):
        if cell.isdigit() and index != 8 and int(cell) > 10:
            return False
    return True


def candidate_rows(source_words: list[str]) -> list[tuple[str, tuple[str, ...]]]:
    """Printed stat rows: a short name followed by nine characteristic cells.

    Respaldo del cotejo: es la lectura que queda cuando la fuente no tiene lectura
    estructural —ni geometría de página cacheada ni documento—, y la que se retiró
    de las fuentes que sí la tienen, porque una ventana de nueve tokens del texto
    aplanado mezcla la fila con la prosa de la columna vecina y, con un paréntesis
    de por medio («3(4)»), inventa una fila que la página no imprime.
    """
    out: list[tuple[str, tuple[str, ...]]] = []
    seen: set[tuple[str, ...]] = set()
    for index in range(len(source_words) - 9):
        cells = source_words[index:index + 9]
        if not plausible_row(cells):
            continue
        key = tuple(cells)
        name_tokens: list[str] = []
        back = index - 1
        while back >= 0 and len(name_tokens) < 3 and re.fullmatch(r"[a-z'.-]+[a-z]", source_words[back]):
            if source_words[back] in {'gc', 'wt', 'gold', 'crowns'}:
                break
            name_tokens.insert(0, source_words[back])
            back -= 1
        if not name_tokens:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append((' '.join(name_tokens), key))
    return out


# El nombre que abre la fila impresa: la primera celda de la línea, hasta su
# primera cifra («Dwarf 3 3» → «Dwarf»).
ROW_NAME = re.compile(r"([A-Za-z][A-Za-z'\-\. ]*?)\s*(?=\d|$)")
# El grupo que la fila anota sobre una característica («3(4)», «1+1»): la variante
# que alcanza bajo una regla, no una característica más de la fila.
PARENTHETICAL = re.compile(r'\([^)]*\)')


def row_items(text: str) -> list[str]:
    """Los valores que una celda imprime en la fila: sus cifras y sus guiones.

    La fila se lee por sus **valores**, no por sus cifras: un guion es una
    característica que la fila no tiene —el Movimiento del Ivy Ferret, que la fuente
    imprime «- 3 0 2 2 1 4 1 8»— y cuenta como uno. Los grupos entre paréntesis no
    cuentan, porque son la variante que la fila anota sobre la característica
    («3(4)» es Fuerza 3, y 4 el valor que alcanza bajo una regla) y no un décimo
    valor: sin esta regla el Giant Spider del KAZ («Giant Spider 7 3 0 3(4) 3 1 4 1
    4») imprimía diez cifras y la fila quedaba sin leer.
    """
    return [item for item in PARENTHETICAL.sub(' ', text).split() if item]


def row_values(texts: Sequence[str]) -> list[str]:
    """Los valores de una fila impresa: los de sus celdas, mientras sean valores.

    Un valor es una cifra —la de ``Ld`` puede tener dos dígitos—, la tirada que
    alguna fuente imprime en su lugar («2D6» en el Movimiento de los Sea Squigs) o un
    guion (una característica que la fila no tiene). Lo que la línea imprime después
    de los nueve valores no es un valor más: es la prosa de la columna vecina que el
    extractor deja a la misma altura («Assasin 5 5 5 4 4 1 7 1 8 Same as Hired
    Sword») o la distancia que anota la fila de al lado.
    """
    out: list[str] = []
    for text in texts:
        for item in row_items(text):
            if not CELL.match(item):
                return out
            out.append(item)
    return out


def name_before(found: Sequence) -> str:
    """El nombre que toma una fila que no lo imprime en su propia celda.

    Las fuentes imprimen la fila con el nombre en una celda y los valores en la
    siguiente («Thieves.» | «Halfling» | «4 5 7 3 3 3 9 4 10»), así que el nombre es
    el de la celda con letras que precede a los valores.
    """
    for cell in reversed(list(found)):
        head = ROW_NAME.match(cell.text.strip())
        if head and head.group(1).strip():
            return head.group(1).strip()
    return ''


def printed_row(found: Sequence) -> tuple[str, tuple[str, ...]] | None:
    """El nombre y los valores de la fila que una línea impresa imprime, o None.

    La línea física mezcla lo que la página imprime a la misma altura, así que la
    fila se busca **celda a celda**: la celda que la abre lleva su nombre delante
    («Spirit 5 5 0 4 3 4 5 3 9») o el nombre lo lleva la celda con letras que la
    precede («Boss» | «4» | «4 3 4 4 1 3 1 8», «Dwarf 3 3» | «2» | «3 4 1 2 1 9»), y
    sus valores son los suyos y los de las celdas que la siguen (``row_values``).
    Cuando la línea mezcla la prosa de la columna vecina con la fila («… their
    ascension. They» | «Spirit 5 5 0 4 3 4 5 3 9»), la celda de la prosa no abre la
    fila y la fila se llama «Spirit». Y la tabla de tesoros que imprimen las páginas
    de «Warrior Training Ground» («D3 Gems worth 10 gc each 4+») no llega a nueve
    valores.
    """
    for start, cell in enumerate(found):
        head = ROW_NAME.match(cell.text.strip())
        values = row_values([cell.text[head.end():] if head else cell.text]
                            + [later.text for later in found[start + 1:]])
        if len(values) != 9 or not plausible_row(values):
            continue
        name = (head.group(1).strip() if head else '') or name_before(found[:start])
        if name:
            return ' '.join(name.split()[-3:]), tuple(values)
    return None


def column_row(text: str) -> tuple[str, ...] | None:
    """Las nueve cifras de una línea que **es** la fila de características y nada más.

    En una página a dos columnas la tabla de cada perfil vive en **su** columna, y la
    fila sale en su propia línea: nueve celdas —una por característica, la de ``Ld``
    incluida cuando vale 10— y ningún nombre, que lo lleva el título que encabeza la
    tabla. La línea física, en cambio, es la altura de la página y mezcla las dos
    columnas (las dos tablas caen a la misma altura), así que esta lectura es la del
    **orden de lectura**, que es el de la columna.
    """
    cells = [cell_value(cell) for cell in text.split()]
    if len(cells) != 9 or not all(CELL.match(cell) for cell in cells):
        return None
    return tuple(cells)


def price_labels(reader, stem: str) -> list[str]:
    """Las etiquetas con las que las listas de un documento nombran cada fila.

    Cada fila de una lista imprime su nombre en la celda de la tarifa, en la de su
    izquierda (las listas a dos columnas parten la celda entre dos líneas) o en el
    tramo de prosa que abre la tarifa dentro de la propia celda: una línea de prosa
    tasa dos veces («Dark Venom at a cost of 20 gold crowns and Black Lotus …») y el
    nombre de la segunda no es el que abre la línea.
    """
    out: list[str] = []
    tail: list[dict] = []
    for page in reader.pages(stem):
        lines = reader.physical_lines(stem, page)
        for row in price_rows(tail + lines, context=len(tail)):
            out += [row['name'], row['above'], *(row.get('names') or [])]
        tail = lines[-2:]
    return [label.strip() for label in out if label and label.strip()]


_LIST_LABELS: dict[tuple[str, str], list[str]] = {}


def printed_list_labels(tree: str, band: str) -> list[str]:
    """Las etiquetas que las **listas impresas** del documento de la banda nombran.

    Son las filas de sus listas —la geometría de la página en 2B (``price_rows``) y
    las tablas de la página web en 2A (``list_rows``)—, no el nombre suelto en su
    prosa: eso es lo que hacía pasar por impreso un objeto que la lista no lleva.
    """
    key = (tree, band)
    if key not in _LIST_LABELS:
        out: list[str] = []
        reader = page_reader(tree)
        if reader is not None:
            for source_id in source_groups(tree).get(band) or [band]:
                if reader.pdf_for(source_id) is not None:
                    out += price_labels(reader, source_id)
        document = page_document(tree, band)
        if document is not None:
            out += [name for name, _cost in list_rows(document)]
        _LIST_LABELS[key] = out
    return _LIST_LABELS[key]


_SHARED_LISTS: dict[str, dict[str, list[str]]] = {}


def shared_list_labels(tree: str) -> dict[str, list[str]]:
    """Las listas de cada capítulo que el árbol comparte entre paquetes.

    Son los anuales y especialistas que el manifiesto no asigna a ninguna banda: de
    ahí salen los objetos que la banda no imprime en su propio documento.
    """
    if tree not in _SHARED_LISTS:
        out: dict[str, list[str]] = {}
        extra, extra_dir = page_reader(tree, 'extra'), SOURCE_EXTRA[tree]
        if extra is not None and extra_dir:
            for name in sorted(os.listdir(os.path.join(ROOT, extra_dir))):
                if not name.lower().endswith('.pdf'):
                    continue
                stem = os.path.splitext(name)[0]
                if extra.pdf_for(stem) is not None:
                    out[f'extra-{name}'] = price_labels(extra, stem)
        _SHARED_LISTS[tree] = out
    return _SHARED_LISTS[tree]


# La decoración con la que la lista marca una fila por su disponibilidad o por una
# nota: el asterisco pegado al nombre («Elven Cloak*», «Lock picks**»), la cruz y
# el grado. No es parte del nombre del objeto y sin quitarla la fila no coteja.
LIST_MARK = '*\u2020\u2021\u00b0\u00a7'


def list_words(text: str) -> list[str]:
    """Palabras de una fila de lista, sin la decoración que la fuente le pega.

    La celda de una lista junta a veces dos objetos («Mace/Hammer», «Dagger/Pointy
    Stick»), marca la disponibilidad con asteriscos y escribe el apóstrofo y el
    guion a su manera («Cat o' nine tails», «Double Handed Weapon»), así que la
    clave de cotejo es la palabra: el nombre del catálogo es una de las palabras de
    la fila, o la fila una de las del nombre, y la puntuación de la fuente no
    decide el cotejo. El punto del relleno de las listas y el que el extractor
    escribe entre palabras no llevan texto, así que tampoco cuentan.
    """
    return [cleaned for cleaned in
            (token.strip(LIST_MARK + '.') for token in loose(normalize(text)).split())
            if cleaned]


def in_list(phrase: str, labels: Sequence[str]) -> bool:
    """¿Una fila de la lista imprime ese nombre?

    El nombre llega con la puntuación del catálogo y la fila con la de la fuente
    («Pairing Knife( Dagger ) **»), y la lista escribe junto el compuesto que el
    catálogo separa («long bow» para `longbow`), así que se coteja por palabras en
    su orden y por la forma compacta, no por el texto literal.

    El catálogo compone el nombre de la variante con el de su padre separados por un
    guion largo («Swivel Gun — Ball Shot») mientras la lista titula el padre
    aparte y tasa la variante por su nombre corto, así que un nombre partido así se
    coteja por sus partes: cada una tiene que ser una fila —lo que también impide
    que la parte del padre pase por la variante—.
    """
    parts = [part for part in re.split(r'\s[\u2010-\u2015]\s', phrase) if part.strip()]
    if len(parts) > 1:
        return all(in_list(part, labels) for part in parts)
    needle = list_words(phrase)
    if not needle:
        return False
    compact = ''.join(needle)
    for label in labels:
        words_ = list_words(label)
        if not words_:
            continue
        if (phrase_near(needle, words_) or compact in ''.join(words_)
                # El catálogo nombra la entrada combinada en un orden y la lista la
                # imprime en el contrario («Mace Hammer» del catálogo, «Hammer/Mace»
                # de la página): las mismas palabras, y la fila no coteja por su
                # orden sino por nombrar las dos.
                or set(needle) <= set(words_)):
            return True
    return False


# Hasta cuántas líneas hacia arriba se busca el título que encabeza una tabla.
TITLE_ABOVE = 24


def title_above(lines: Sequence[Mapping], index: int, lookback: int = TITLE_ABOVE) -> str:
    """El título que encabeza una tabla, buscado hacia arriba en el orden de lectura.

    La fila de algunas fuentes no imprime su nombre y la entrada que la titula no
    llega a formarse —las páginas del KAZ anuncian sus equipos con una tarifa («0-1
    Skaven Gutter Runners Tunnel Team . . . 145 gc per team») que no es una tarifa de
    contratación—, así que el título se busca hacia arriba en el **orden de lectura**
    —el de su columna, que por eso no cruza a la del vecino— saltando lo que no
    titula nada: la cabecera de columnas, las líneas de propiedad («Hire Fee: …»,
    «Rating: …», que se anuncian con dos puntos), la prosa (que cierra su frase) y
    los subtítulos en mayúsculas («SPECIAL RULES»).
    """
    for above in range(index - 1, max(-1, index - 1 - lookback), -1):
        text = flat(str(lines[above].get("text") or "")).strip()
        if not text or len(text) > 60 or len(text.split()) > 8:
            continue
        if stat_header([(0, 0, token) for token in text.split()]) or fee_line(text):
            continue
        if re.search(r"[:;]", text) or text[-1:] in ".!?":
            continue
        if text.isupper():
            continue
        return profile_name(text)
    return ""


def entry_row(entry: Mapping) -> tuple[str, tuple[str, ...]] | None:
    """La fila de características de una entrada y el nombre que la titula.

    La entrada del lector compartido ya trae su encabezado y sus líneas —el orden de
    lectura de su columna—, así que la fila de su tabla se lee **dentro de ella**: la
    cabecera de columnas y, en la línea que la sigue, la fila. Es la misma lectura
    con la que se cotejan los hirelings (``stat_rows``), con las celdas de la fila en
    vez de sus dígitos, y el nombre es el del encabezado que titula la tabla («0-1
    Mamluks», su tarifa, su prosa y su tabla), que es el que la fila no imprime.
    """
    lines = entry.get('lines') or []
    for index, line in enumerate(lines):
        if not stat_header([(0, 0, token) for token in line.split()]):
            continue
        for following in lines[index + 1:index + 3]:
            cells = column_row(following)
            if cells is not None:
                return profile_name(str(entry.get('heading') or '')), cells
        return None
    return None


_ROWS_CACHE: dict[tuple[str, str], list[tuple[str, tuple[str, ...]]]] = {}


def printed_stat_rows(tree: str, band: str) -> list[tuple[str, tuple[str, ...]]]:
    """Las filas de características que la **tabla impresa** declara en sus páginas.

    Tres lecturas, una por forma de imprimir la tabla:

    - la **línea física** de la página (``printed_row``): la fila con el nombre en su
      propia celda o en la celda que la precede, que es como la imprimen los
      suplementos de 2B;
    - el **orden de lectura** de su columna: la misma fila con el nombre en la línea
      (``printed_row``), la fila dentro de la entrada que la titula (``entry_row``) y
      la fila impresa en su propia línea, sin nombre, con el del título que encabeza
      su tabla (``column_row`` + ``title_above``), que es como la imprimen los
      Dramatis y las páginas a dos columnas de Relics of the Crusades;
    - el **documento** de la página web (``profile_tables``): la fila leída de su
      tabla, una celda por columna, que es como la imprimen las páginas de 2A.

    En ninguna de las tres se lee una fila de una ventana de tokens del texto
    aplanado, que era lo que hacía pasar por fila lo que la columna vecina había
    dejado junto en el flujo.
    """
    key = (tree, band)
    if key in _ROWS_CACHE:
        return _ROWS_CACHE[key]
    out: list[tuple[str, tuple[str, ...]]] = []
    seen: set[tuple[str, ...]] = set()

    def add(name: str, values: Sequence[str]) -> None:
        row = tuple(values)
        if len(row) != 9 or row in seen or not plausible_row(list(row)):
            return
        seen.add(row)
        out.append((name, row))

    reader = page_reader(tree)
    if reader is not None:
        for source_id in source_groups(tree).get(band) or [band]:
            if reader.pdf_for(source_id) is None:
                continue
            for page in reader.pages(source_id):
                for line in reader.physical_lines(source_id, page):
                    found = printed_cells(line)
                    row = printed_row(found) if found else None
                    if row is not None:
                        add(row[0], row[1])
                lines = reader.lines(source_id, page)
                for line in reader.entries(source_id, page):
                    row = entry_row(line)
                    if row is not None:
                        add(row[0], row[1])
                for index, line in enumerate(lines):
                    found = printed_cells(line)
                    row = printed_row(found) if found else None
                    if row is not None:                 # la fila con su nombre en la línea
                        add(row[0], row[1])
                    named = column_row(str(line.get('text') or ''))
                    if named is not None:               # la fila sin nombre, titulada arriba
                        add(title_above(lines, index), named)
    document = page_document(tree, band)
    if document is not None:
        for name, row in profile_tables(document):
            add(name, row)
    _ROWS_CACHE[key] = out
    return out


# Findings verified by hand against the source, with the reason they are not defects.
# Key: (kind, band or None, substring of the row or None). Kept beside the auditor so
# the report stays signal-only; every entry is argued in
# `sources/2A/discrepancy-verdicts.md` / `sources/2B/discrepancy-verdicts.md`.
ADJUDICATED: list[tuple[str, str | None, str | None, str]] = [
    ('source-row-unmatched', None, '8 6 0 6 6 6 3 5 8',
     'Karak Azgal Dragonslayer scenario monster (Dragon wakes and attacks); not a warband member'),
    ('source-row-unmatched', None, '7 3 0 3 4 1 3 1 3',
     'Savage Orc pet War Boar: modelled as promotion notes on the KB item, list already references it'),
    ('source-row-unmatched', None, '9 3 0 3 3 1 4 1 4',
     'Savage Orc pet Giant Wolf: modelled as promotion notes on the KB item'),
    ('source-row-other-document', 'snotlings-web', '4 4 4 3 3 2 9 4 6',
     'the printed row is the maximum-characteristics table the page heads «Profile»: «Snotling '
     'maximums: M 4, WS 4, BS 4, S 3, T 3, W 2, I 9, A 4, Ld 6». The package states it inside '
     'its «Characteristic Increase» rule, not as a profile, and the auditor reads it there'),
    ('profile-stats-unverified', 'savage-orcs-sar', 'Sea Squigs',
     'movement printed as prose in the special rules (2D6-1"), not as a table row'),
    ('profile-stats-unverified', 'orc-pirates-sar', 'Sea Squigs',
     'movement printed as prose in the special rules (2D6-1"), not as a table row'),
    ('profile-stats-unverified', 'snotlings-web', 'Snotling Wheelo',
     'the source prints M as "*" (1D6" walking / 2D6" running); 0 plus the note carries it'),
    ('band-name-missing', 'militiant-mootlanders-mim', 'Militiant Mootlanders',
     'the printed heading is "Militiant Mootlanders" (source spelling), which the package keeps'),
    # Editorial headings: the package titles a section the source prints shorter, and every
    # word of the title is the source\'s own.
    ('rule-name-missing', 'protectorate-of-sigmar-lotd3', 'Huntsman Hero Slot',
     'editorial title for the printed «Huntsman: You may choose to replace one Templar with a Huntsman»'),
    ('rule-effect-absent', 'protectorate-of-sigmar-lotd3', 'Huntsman Hero Slot',
     'the rule states the printed hero-slot substitution; the source prints it as a one-line list entry'),
    ('rule-name-missing', 'dwarf-slayers-kaz', 'Slayer Skill Column',
     'editorial title for the printed Slayer skill table'),
    ('rule-name-missing', 'savage-orcs-sar', 'Base Rules (Da Mob)',
     'editorial title; the source reads «The Savage Orcs use the exact same rules as the Da Mob Warband»'),
    ('rule-effect-absent', 'savage-orcs-sar', 'Roster (Da Mob Composition)',
     'the expansion of a one-line source reference to the Da Mob warband composition'),
    ('rule-name-missing', 'araby-smugglers-sar', 'Fine Craftsmanship',
     'the source prints the rule name as «Fine Craftmenship» (source typo); the package normalizes it'),
    ('rule-name-editorial', 'araby-smugglers-sar', 'Fine Craftsmanship',
     'the same case, classified by its name: read from the page geometry the effect is '
     'near-verbatim, so what differs is the label — the source typo the package normalizes'),
    ('rule-effect-absent', 'araby-smugglers-sar', 'Slavers',
     'the source entry is a three-line list; the effect restates it with its corpus reference'),
    ('rule-name-missing', 'disciples-of-maldred-mou', 'Gifts of Tzeentch',
     'the source prints «Gifts of Tzentch» (source typo); the package normalizes it'),
    ('rule-effect-absent', 'low-kings-mim', 'Mobsmen Special Equipment',
     'the effect summarizes the special-equipment block; the items and their rules live in the catalogue'),
    ('rule-effect-absent', 'knights-of-the-bitter-moors-mim', 'Field Trebuchet',
     'the effect condenses the printed three-column siege-weapon block into one paragraph'),
    # Labels the source prints in a section that is not a warband rule: equipment
    # special rules (the catalogue item carries them), a spell of the band's list, a
    # chapter heading, fiction and one source typo. Each was read against the source.
    ('source-rule-unmodelled', 'druchii-mic', 'Swift',
     'weapon special rule of the Draich in the printed special-equipment section; the '
     'divergence with the KB weapon.draich text (it strikes last there) is recorded as a '
     'promotion note, not fixed in staging'),
    ('source-rule-unmodelled', 'ghost-pirates-sar', 'Necromancers and Bokors make do',
     'fiction sentence that introduces the Bloated profile, not a rule'),
    ('source-rule-unmodelled', 'ghost-pirates-sar', 'Special Recruitment',
     'section heading of the recruited Bloated entry (modelled as a profile); it prints no '
     'separate rule'),
    ('source-rule-unmodelled', 'guild-of-disgraced-engineers-mim', 'Stablizers',
     'source typo; the package prints the standard spelling «Stabilizers»'),
    ('source-rule-unmodelled', 'sea-ghosts-mim', 'Guardians Of The Peace',
     'background section on the Mannikins of Elftown; it prints no warband rule'),
    ('source-rule-unmodelled', 'sea-ghosts-mim', 'WARDANCER SPECIAL SKILLS',
     'section heading of the Wardancer skill list; the four Shadow Dances carry its content'),
    ('rule-effect-absent', 'sea-ghosts-mim', 'Wardancer Special Skills',
     'section heading; the four Shadow Dances carry its content'),
    ('source-rule-unmodelled', 'skaven-of-clan-pristekk-sc', 'Breeder',
     'the word «breeders» inside the clan background prose, not a rule'),
]


def adjudicated(kind: str, band: str, row: str) -> str | None:
    """The recorded reason this finding is not a defect, or None."""
    for key_kind, key_band, key_row, reason in ADJUDICATED:
        if kind != key_kind:
            continue
        if key_band and key_band != band:
            continue
        if key_row and key_row not in row:
            continue
        return reason
    return None


def check_band(tree: str, band: str, extras: list[tuple[str, list[str]]],
               shared: tuple[list[tuple[str, list[str]]], dict[str, list[list[str]]]],
               kb: tuple[set, set],
               catalogue: dict[str, set[str]],
               context: dict,
               campaign_labels: frozenset[str] = frozenset(),
               strict_labels: bool = False) -> dict:
    report: dict[str, list] = defaultdict(list)
    shared_rules, shared_by_name = shared
    stats: Counter = Counter()
    documents = source_documents(tree, band)
    if not documents:
        return {'band': band, 'tree': tree, 'findings': {'source-missing': ['no cached source']}, 'stats': stats}
    raw = documents[0][1]
    if band in SCANNED or len(normalize(raw)) < 1200:
        return {'band': band, 'tree': tree,
                'findings': {'source-scanned': ['no text layer; verified by reading the pages']},
                'stats': stats}

    base = band_dir(tree, band)
    vocab: set[str] = set()
    kb_rows_set, kb_names = kb
    profiles: list[dict] = []
    profiles_path = os.path.join(base, 'profiles.yaml')
    if os.path.exists(profiles_path):
        for doc in docs(profiles_path):
            profiles += doc.get('profiles') or []
    for profile in profiles:
        vocab.update(words(str(profile.get('name') or '')))

    # Per-document word lists: the primary first, then layout, then supplements.
    doc_words: list[tuple[str, list[str]]] = []
    for label, text in documents:
        doc_words.append((label, join_spaced_letters(words(text), vocab)))
    for label, tokens in extras:          # already tokenized supplements
        doc_words.append((label, tokens))
    primary_words = doc_words[0][1]
    primary_joined = ' '.join(primary_words)
    labels_order = [label for label, _ in doc_words]
    # The band's own documents (PDF text + layout) outrank the shared chapters: a
    # plain substring match in a tree-wide supplement must not shadow the compact
    # spelling of the band's own list (`longbow` in the PDF vs `long bow` elsewhere).
    own_labels = labels_order[:len(documents)]
    tokens_of = dict(doc_words)
    joined_of = {label: ' '.join(tokens) for label, tokens in doc_words}
    loose_of = {label: loose(joined) for label, joined in joined_of.items()}
    compact_of = {label: value.replace(' ', '') for label, value in loose_of.items()}

    def _scan(order: list[str], table: dict[str, str], needle: str) -> str | None:
        for label in order:
            if needle in table[label]:
                return label
        return None

    def _exact(phrase: str, order: list[str]) -> str | None:
        needle = normalize(phrase)
        if not needle:
            return order[0] if order else None
        hit = _scan(order, joined_of, needle)
        if hit:
            return hit
        needle_words = needle.split()
        for label in order:
            if phrase_near(needle_words, tokens_of[label]):
                return label
        return None

    def _loose(phrase: str, order: list[str]) -> str | None:
        """`_exact` for names whose printed spelling differs in punctuation."""
        needle = loose(normalize(phrase))
        if not needle:
            return order[0] if order else None
        return _scan(order, loose_of, needle)

    def _compact(phrase: str, order: list[str]) -> str | None:
        """`_exact` for compounds the source prints as one word (`longbow`)."""
        needle = loose(normalize(phrase)).replace(' ', '')
        if not needle:
            return order[0] if order else None
        return _scan(order, compact_of, needle)

    def find(phrase: str, own_only: bool = False) -> str | None:
        order = own_labels if own_only else labels_order
        for matcher in (_exact, _loose, _compact):
            hit = matcher(phrase, order)
            if hit:
                return hit
        return None

    own_vocab = {stem(token) for _, tokens in doc_words[:len(documents)] for token in tokens}
    # Characteristic cells without their printed decoration (`1+1` → 1, `3(4)` → 3).
    simple_docs = [(label, [simple_value(token) for token in tokens])
                   for label, tokens in doc_words[:len(documents)]]

    def name_traced(phrase: str) -> bool:
        """Every content word of an editorial heading appears in the band's own source.

        Packages title a section with an expansion the source prints shorter
        («Special House Guard Equipment» for «Special equipment», «Mobsmen Special
        Skills» for the table heading), so the heading itself cannot be matched
        literally — only its words can be traced.
        """
        content = [stem(word) for word in normalize(phrase).split() if len(word) > 2]
        return len(content) >= 2 and all(word in own_vocab for word in content)

    band_docs = docs(os.path.join(base, 'band.yaml'))
    family_names: set[str] = set()
    family_rows: set[tuple[str, ...]] = set()
    if band_docs:
        family = str(band_docs[0].get('canonical_family') or '')
        if family:
            family_names, family_rows = kb_family(family)
        if family_names:
            stats['band-inherits-family'] += 1
    if band_docs:
        name = str(band_docs[0].get('name') or '')
        stats['band-name'] += 1
        name_tokens = normalize(re.sub(r'\(.*?\)', '', name)).split()
        # The package name often carries an editorial subtitle or a translation
        # («Dreamwalkers, Cult Of Morr» for the source's «Dreamwalkers»), so a
        # partial headline counts as traced.
        headline_found = any(
            phrase_near(name_tokens[:size], primary_words, window=6)
            for size in (3, 2, 1) if size <= len(name_tokens)
        )
        if not headline_found and not find(name) and not name_traced(name):
            report['band-name-missing'].append(name)
        elif headline_found != bool(len(name_tokens) <= 3):
            stats['band-name-editorial'] += 1

    profile_rows: set[tuple[str, ...]] = set()
    for profile in profiles:
        name = str(profile.get('name') or '')
        stats['profiles'] += 1
        chars = profile.get('characteristics') or {}
        row = tuple(str(chars.get(key, '')) for key in ('M', 'WS', 'BS', 'S', 'T', 'W', 'I', 'A', 'Ld'))
        profile_rows.add(row)
        bare_name = re.sub(r'\s*\(.*\)\s*$', '', name)
        # A package that inherits a KB family takes its names and rows from there.
        inherited_name = bool(family_names) and bare_name and any(
            normalize(bare_name) in family_name or family_name in normalize(bare_name)
            for family_name in family_names)
        if not (inherited_name or find(bare_name) or find(name) or name_traced(bare_name)):
            report['profile-name-missing'].append(name)
        # Warmachines and vehicles carry no stat line («None» cells).
        if any(cell in ('None', '', 'null') for cell in row):
            stats['profile-stats-abstract'] += 1
            continue
        row_text = ' '.join(row)
        if family_rows and row in family_rows:
            stats['profile-stats-inherited'] += 1
        elif not find(row_text) and not any(phrase_near(row_text.split(), tokens, window=3)
                                            for _, tokens in simple_docs):
            stats['profile-stats-unverified'] += 1
            report['profile-stats-unverified'].append(f'{name}: {row_text}')

    rules: list[dict] = []
    rules_path = os.path.join(base, 'special-rules.yaml')
    if os.path.exists(rules_path):
        for doc in docs(rules_path):
            rules += doc.get('rules') or []
    for rule in rules:
        name = str(rule.get('name') or '')
        stats['rules'] += 1
        if rule.get('rule_ref'):
            stats['rules-shared-ref'] += 1
            continue
        effect = str(rule.get('effect') or '')
        # «See the band Ethereal rule.» / «See Mordheim rulebook page 151.» carry no
        # prose of their own: the pointer is the content.
        if effect and CROSS_REF.match(effect.strip()):
            stats['rules-cross-ref'] += 1
            continue
        bare = re.sub(r'\s*\(.*\)\s*$', '', name)
        name_found = find(bare) or find(name) or name_traced(bare)
        if not effect:
            report['rule-effect-missing'].append(name)
            continue
        effect_words_ = words(effect)
        own = doc_words[:len(documents)]              # the band's own documents
        supplements = doc_words[len(documents):]      # chapters shared by the tree
        ratio = max(coverage(effect_words_, tokens) for _, tokens in own)
        stats['effects'] += 1
        if ratio >= NEAR:
            stats['effects-verbatim-or-near'] += 1
            if not name_found:
                report['rule-name-editorial'].append(name)
            continue
        # A maximum-characteristics rule restates a printed table: verify the values.
        stat_rows = [match.groups() for match in STAT_ROW_PROS.finditer(effect)]
        if stat_rows and all(numbers_in_order(list(row), primary_words) for row in stat_rows):
            stats['effects-max-table-verified'] += 1
            continue
        # The prose may be the KB's canonical text for a shared rule…
        if any(coverage(effect_words_, canon) > 0.95 for _, canon in shared_rules):
            stats['effects-canonical-kb'] += 1
            continue
        # …or the standard rule the source only *names* along the profile («No Pain»,
        # «Leader», «Fear»): the package restates it in its own words, exactly as the
        # active KB does in its 320 inlined shared rules. Wording equivalence is the
        # rule-equivalence review's job, not this auditor's.
        if shared_by_name.get(normalize(bare)):
            stats['effects-shared-name-inlined'] += 1
            continue
        # …or come from a chapter shared with other bands (MiM/MW/KAZ/REL).
        if supplements and max(coverage(effect_words_, tokens) for _, tokens in supplements) >= NEAR:
            stats['effects-in-supplement'] += 1
            continue
        if not name_found:
            report['rule-name-missing'].append(name)
        if ratio >= CONDENSED:
            stats['effects-condensed'] += 1
            report['rule-effect-condensed'].append(f'{name} ({ratio:.2f})')
        else:
            stats['effects-absent'] += 1
            report['rule-effect-absent'].append(f'{name} ({ratio:.2f})')

    # Las listas impresas de la fuente: sus filas son las que dicen que un objeto se
    # imprime, y su nombre en la prosa no. El propio documento de la banda primero y
    # los capítulos que el árbol comparte después.
    own_lists = printed_list_labels(tree, band)
    shared_lists = shared_list_labels(tree)

    def shared_label(candidates: Sequence[str]) -> str:
        """El capítulo compartido cuya lista imprime alguno de esos nombres, o ''."""
        for candidate in candidates:
            for label, labels in shared_lists.items():
                if in_list(candidate, labels):
                    return label
        return ''

    # La fila que la fuente delega al reglamento en vez de imprimirla: sus objetos no
    # están en el corpus y se declaran con el motivo compartido con el auditor de 2B
    # (``printed_wordings``), no como hueco. Key: 'lista/objeto' → motivo.
    delegated: dict[str, str] = {}

    access_path = os.path.join(base, 'equipment-access.yaml')
    if os.path.exists(access_path):
        for doc in docs(access_path):
            for entry in doc.get('equipment_lists') or []:
                list_name = str(entry.get('name') or '')
                list_id = str(entry.get('id') or '')
                stats['lists'] += 1
                if not (find(list_name) or name_traced(list_name)):
                    report['list-name-missing'].append(list_name)
                for item in entry.get('items') or []:
                    item_id = str(item.get('item_id') or '')
                    stats['items'] += 1
                    candidates = [item_id.replace('_', ' ').replace('-', ' ')]
                    candidates += sorted(catalogue.get(item_id) or [])
                    # Las palabras con que la fuente imprime el objeto, en su árbol: son
                    # la fila del objeto aunque el catálogo lo llame de otro modo.
                    candidates += list(wordings.words_for_item(item_id, tree))
                    # El objeto se coteja contra las listas impresas: la fila que
                    # imprime su nombre con su tarifa. La prosa del documento no
                    # lleva a la lista —un nombre suelto puede estar en cualquier
                    # prosa—, pero que se imprima en ella es otra cosa y se informa
                    # aparte para que el revisión la lea.
                    if any(in_list(candidate, own_lists) for candidate in candidates):
                        stats['items-in-list'] += 1
                        continue
                    # Los capítulos compartidos van después: un acierto en uno de
                    # ellos no puede tapar que la lista de la banda no lo imprima.
                    shared = shared_label(candidates)
                    if shared:
                        stats['items-in-supplement'] += 1
                        report['item-in-supplement'].append(f'{list_name}/{item_id} ({shared})')
                        continue
                    labels = [label for label in
                              (find(candidate, own_only=True) or find(candidate)
                               for candidate in candidates) if label]
                    if labels:
                        stats['items-outside-list'] += 1
                        report['item-outside-list'].append(f'{list_name}/{item_id} ({labels[0]})')
                    else:
                        reason = wordings.delegated_reason(tree, band, list_id)
                        if reason:
                            delegated[f'{list_name}/{item_id}'] = reason
                        else:
                            report['item-name-missing'].append(f'{list_name}/{item_id}')

    # Fuente → paquete: filas impresas que ningún perfil cubre. Se leen de la tabla
    # impresa —la línea y las celdas que la pagina imprime, el orden de lectura de su
    # columna y el documento de la página web— y no de una ventana de tokens de su
    # texto. La ventana queda como respaldo para la fuente que no tiene lectura
    # estructural (sin caché de geometría ni de documento), que es lo que mantiene el
    # cotejo en pie cuando el caché no está.
    table_rows = printed_stat_rows(tree, band)
    rows_found = table_rows or candidate_rows(primary_words)
    for name, cells in rows_found:
        if kb_models_row(name, cells, kb):
            stats['rows-matched-by-kb-name'] += 1
            continue
        if cells in profile_rows or cells in kb_rows_set or (family_rows and cells in family_rows):
            stats['rows-matched-by-values'] += 1
            continue
        # Anthologies (KAZ, REL, MiM) print several warbands in one document, and
        # maximum-characteristic / mount tables are modelled outside profiles.yaml, so a
        # row missing here may be modelled elsewhere in the same tree.
        row_text = ' '.join(cells)
        pattern = row_pattern(list(cells))
        if re.search(pattern, tree_yaml_blob(tree)):
            stats['rows-modelled-elsewhere'] += 1
            report['source-row-other-document'].append(f'{row_text}  ({name})')
            continue
        # The active KB models some table rows (miscellaneous gear, bestiary entries).
        if re.search(pattern, tree_yaml_blob('knowledge')):
            stats['rows-modelled-in-kb'] += 1
            continue
        # A row a reviewer transcribed into the tree's own review documents is
        # documented evidence: reported apart so it stays visible but not silent.
        if re.search(pattern, tree_doc_blob(tree)):
            stats['rows-documented-in-reviews'] += 1
            report['source-row-documented'].append(f'{row_text}  ({name})')
            continue
        stats['rows-unmatched'] += 1
        report['source-row-unmatched'].append(f'{row_text}  ({name})')

    # Fuente → paquete (completitud): reglas que el texto imprime y el paquete no modela.
    section = str(((band_docs[0].get('sources') or [{}])[0]).get('section') or '') if band_docs else ''
    package_text = normalize('\n'.join(
        open(path, encoding='utf-8', errors='replace').read()
        for path in sorted(glob.glob(os.path.join(base, '*.yaml')))))
    tree_text, tree_vocab_ = tree_norm_blob(tree)
    if strict_labels:
        # Completeness sweep: only the band's own package and the packages that share
        # its printed document count as modelling a label, so a rule that exists in
        # some other band still shows up as a gap here.
        shared_packages = [other for other in (source_groups(tree).get(band) or [band])
                           if os.path.isdir(band_dir(tree, other))]
        covered_text = normalize('\n'.join(
            open(path, encoding='utf-8', errors='replace').read()
            for other in shared_packages
            for path in sorted(glob.glob(os.path.join(band_dir(tree, other), '*.yaml')))))
        covered_vocab = {stem(token) for token in covered_text.split()}
    else:
        covered_text, covered_vocab = tree_text, tree_vocab_
    if band != 'knowledge':
        # A label may be spelled differently by the extractor (a word split after its
        # first letter) or by the source itself (its own typo, «Beserker» for the
        # package's «Berserker»); both resolve against the corpus vocabulary.
        source_vocab = {stem(token) for token in normalize(documents[0][1]).split()}
        label_vocab = covered_vocab | context['vocab'] | source_vocab
        for label in dict.fromkeys(source_rule_labels(documents[0][1], section)):
            key = label.lower().strip()
            if key in LABEL_NOISE or len(key) < 4 or key in campaign_labels:
                continue
            if is_label_noise(label):
                stats['source-rule-noise'] += 1
                continue
            if key in context['bands']:
                # Another warband's chapter heading carried into this extract.
                continue
            stats['source-rule-labels'] += 1
            repaired = repair_split(label, label_vocab)
            needle = normalize(repaired)
            if needle in package_text or needle in covered_text:
                continue
            content = [stem(word) for word in needle.split() if len(word) > 2]
            if content and all(word in covered_vocab for word in content):
                continue
            if needle in context['names'] or loose(needle) in context['loose_names']:
                stats['source-rule-in-catalogue'] += 1
                continue
            # Equipment entries print their own special rules («Special Rules: Critical
            # damage, Wicked edge», «Beastbane: …»); the catalogue carries them.
            if needle in context['catalogue_text']:
                stats['source-rule-in-catalogue'] += 1
                continue
            near = difflib.get_close_matches(needle, context['rule_names'], n=1, cutoff=0.86)
            if near:
                stats['source-rule-near-name'] += 1
                continue
            report['source-rule-unmodelled'].append(label)

    kept: dict[str, list] = {}
    known: dict[str, str] = {}
    for kind, rows in sorted(report.items()):
        open_rows = []
        for row in rows:
            reason = adjudicated(kind, band, row)
            if reason:
                stats[f'adjudicated-{kind}'] += 1
                known[f'{kind}|{row}'] = reason
                continue
            open_rows.append(row)
        if open_rows:
            kept[kind] = open_rows
    # La fila que la fuente no imprime porque delega la lista entera al reglamento: se
    # declara con el mismo motivo que el auditor de 2B, no como objeto perdido.
    for row, reason in sorted(delegated.items()):
        if f'item-name-missing|{row}' in known:
            continue
        stats['adjudicated-item-name-missing'] += 1
        known[f'item-name-missing|{row}'] = reason

    return {'band': band, 'tree': tree, 'findings': kept, 'adjudicated': known, 'stats': stats}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tree', default='all', help='2A, 2B or all (default)')
    parser.add_argument('--band', help='single band id')
    parser.add_argument('--show', type=int, default=6, help='examples per finding class')
    parser.add_argument('--all', action='store_true', help='include the adjudicated findings')
    parser.add_argument('--strict-labels', action='store_true',
                        help='completeness sweep: only the band\'s own documents count as modelling')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    trees = TREES if args.tree == 'all' else (args.tree,)
    kb = kb_rows()
    catalogue = {tree: item_names(tree) for tree in trees}
    # Reference material for judging a printed label: the catalogued entry names of the
    # KB and of the staging tree (band special skills, equipment special rules, prayers,
    # spells, mutations), the KB vocabulary and the tree's own rule names.
    context = {
        'names': set().union(*(catalogue_names(tree) for tree in (*trees, 'knowledge'))),
        'loose_names': set(),
        'vocab': tree_norm_blob('knowledge')[1],
        'catalogue_text': '',
        'rule_names': set(),
        'bands': set(),
    }
    totals: Counter = Counter()
    class_totals: Counter = Counter()
    reports = []
    shared_rules = kb_shared_texts()
    shared_by_name: dict[str, list[list[str]]] = defaultdict(list)
    for shared_name, shared_words in shared_rules:
        shared_by_name[shared_name].append(shared_words)
    # Labels any three bands of the tree print are campaign-wide content (chapter
    # titles of a shared anthology), not one warband's own rules.
    label_bands: dict[str, set[str]] = defaultdict(set)
    for tree in trees:
        pattern = os.path.join(ROOT, 'sources', tree, 'bands', '*', '*', 'band.yaml')
        for path in sorted(glob.glob(pattern)):
            band = os.path.basename(os.path.dirname(path))
            documents = source_documents(tree, band)
            if not documents or band in SCANNED:
                continue
            band_yaml = docs(path)
            section = str(((band_yaml[0].get('sources') or [{}])[0]).get('section') or '') \
                if band_yaml else ''
            for label in set(source_rule_labels(documents[0][1], section)):
                label_bands[label.lower().strip()].add(band)
    campaign_labels = frozenset(label for label, bands in label_bands.items()
                                if len(bands) >= 3)

    for tree in trees:
        extras = [(label, words(text)) for label, text in extra_documents(tree)]
        context['rule_names'] = rule_names(tree)
        context['bands'] = band_names(tree)
        context['catalogue_text'] = catalogue_text(tree)
        # El sitio del apóstrofo no es una divergencia («Morks' Blessing» / «Mork's Blessing»).
        context['loose_names'] = {loose(name) for name in context['names']}
        shared = (shared_rules, shared_by_name)
        pattern = os.path.join(ROOT, 'sources', tree, 'bands', '*', '*', 'band.yaml')
        for path in sorted(glob.glob(pattern)):
            band = os.path.basename(os.path.dirname(path))
            if args.band and band != args.band:
                continue
            report = check_band(tree, band, extras, shared, kb, catalogue[tree], context,
                                campaign_labels, args.strict_labels)
            if args.all:
                for key, reason in report.pop('adjudicated', {}).items():
                    kind, row = key.split('|', 1)
                    report['findings'].setdefault(kind, []).append(f'{row}  [known: {reason}]')
            else:
                report.pop('adjudicated', None)
            reports.append(report)
            totals.update(report['stats'])
            for kind, rows in report['findings'].items():
                class_totals[kind] += len(rows)

    if args.json:
        print(json.dumps({'findings': dict(class_totals), 'stats': dict(totals), 'bands': reports},
                         indent=1, ensure_ascii=False))
        return 0

    print('== paquete → fuente (fidelidad) ==')
    for key in sorted(totals):
        print(f'  {key:30s} {totals[key]}')
    print('== hallazgos por clase ==')
    for kind, count in sorted(class_totals.items()):
        print(f'  {kind:30s} {count}')
    print('\n== detalle por banda (solo bandas con hallazgos) ==')
    for report in reports:
        if not report['findings']:
            continue
        print(f"\n--- {report['tree']}/{report['band']}")
        for kind, rows in report['findings'].items():
            print(f'  [{kind}] {len(rows)}')
            for row in rows[: args.show]:
                print(f'      {row}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
