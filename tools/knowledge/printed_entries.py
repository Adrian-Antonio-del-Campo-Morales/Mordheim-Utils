# -*- coding: utf-8 -*-
"""Lector único de **entradas impresas** para el cotejo de fuentes.

Herramienta permanente del utillaje de la KB (`tools/knowledge`): nació en la fase de
ingesta de 2A/2B y se promocionó aquí con sus tests (`test_printed_entries.py`), porque
el cotejo de catálogo contra fuentes sobrevive a esa fase —la KB tiene catálogo de
hired swords y Dramatis Personae de todos los grados—.

Los cotejos de catálogo —hirelings de 2B y Dramatis Personae de 2A hoy, el que resuelva
la KB mañana— comparan lo que una fuente imprime con lo que el paquete declara. Antes
cada uno leía la fuente a su manera, y el de 2A no la leía por entradas: partía del
texto aplanado y atribuía a un personaje la tarifa y el rating del vecino de columna
(Gwen aparecía con los 75/30 del Dark Jester y el Foole con los 70/35 de Sigmund, que
son los del personaje contiguo). Aquí vive una sola lectura, para que lo que los
dos comparten no pueda divergir:

1. **Lectura por geometría.** Una entrada se lee como la lee una persona.
   ``PdfCorpus`` agrupa las palabras de cada página por su coordenada
   (``pdftohtml -xml``), encuentra el canal entre columnas y devuelve primero la
   izquierda y después la derecha. ``HtmlCorpus`` lee la estructura del documento
   (una entrada por ``div.fighter``, una fila por ``tr`` con una celda por
   columna), que es la geometría que la página web ya trae escrita.
   ``TextCorpus`` lee el texto plano, donde el ancla ``Source:`` separa las
   entradas. Los tres producen la **misma** entrada —encabezado, líneas, palabras
   y texto—, así que los chequeos y la cobertura son los mismos.
2. **Comparación de divisa.** ``fees_in`` lee las dos formas impresas de tarifa,
   con o sin ``to hire``, y la divisa que nombran, pegada al importe (``40GC``) o
   separada (``75 warp tokens``), porque el contrato guarda la expresión impresa
   cuando la fuente no cobra en coronas.
3. **Cobertura por chequeo.** ``Coverage`` cuenta lo comparado y lo no comparable
   de un personaje y ``Ledger`` lo agregado de un cotejo con muchas unidades (las
   19 bandas de 2A), y los dos lo imprimen: un «0 hallazgos» sin filas comparadas no
   es lo mismo que un «0 comprobado».

Lo que el módulo **no** decide es la adjudicación: qué es un hallazgo y qué una
nota en cada árbol, qué perfiles son ``out_of_scope`` y qué etiquetas de regla
son editoriales (no impresas) lo declara cada driver. Aquí no hay rutas de
ningún árbol: los corpus reciben sus directorios y un documento de tarifas se lee
con ``fee_index``.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple

import yaml

# Los cuatro chequeos comparables más el bloque impreso. El orden es el de la
# línea de cobertura.
CHECKS = ("block", "fee", "stats", "rating", "rules")

# --------------------------------------------------------------------------- #
# Tipografía y texto
# --------------------------------------------------------------------------- #

# Los encabezados de display de los suplementos de 2B salen del extractor en la
# zona de uso privado de Unicode (la fuente mapea sus glifos ahí).
PUA = "\ue000-\uf8ff"

# Guion suave y anchos cero: la fuente de 2A imprime ``Schäke­stange`` con un
# guion suave dentro de la palabra, y sin quitarlo el nombre impreso no coincide
# con el del catálogo.
SOFT = "\u00ad\u200b\u200c\u200d\u2060"


def decode(text: str) -> str:
    """Descifra la tipografía de display cuando sale en PUA.

    El extractor devuelve los encabezados de display como los glifos de la fuente
    en la zona privada de Unicode, desplazados ``0xF000`` respecto del ASCII (el
    encabezado del Priest of Verena sale ``<F050 F072 F069 ...>``). El
    desplazamiento se comprobó contra los encabezados que el documento imprime
    además en texto normal; lo que no cae en ASCII imprimible se deja tal cual.
    """
    out = []
    for char in text:
        code = ord(char)
        out.append(chr(code - 0xF000) if 0xF020 <= code <= 0xF07E else char)
    return "".join(out)


def visible(text: str) -> str:
    """El texto como lo lee una persona: descifrado y sin caracteres invisibles."""
    return re.sub(f"[{SOFT}]", "", decode(text))


def flat(text: str) -> str:
    """Texto listo para cotejar, en una línea.

    Algunas páginas de Relics imprimen entre palabras el punto del formulario
    (``Hire Fee: .85.dinars.to.hire``), así que un punto que separa palabras no
    puede seguir contando como el final de una frase cuando se busca una tarifa,
    una fila o un rating.
    """
    return re.sub(r"\s+", " ", re.sub(r"(?<=\S)\.(?=\S)", " ", visible(text))).strip()


def prose(text: str) -> str:
    """Texto de un bloque como lo imprime la fuente, sin tocar su puntuación.

    ``flat`` quita el punto de relleno de las páginas escaneadas y no vale para
    una página web: ahí el punto significa lo que significa, y una cifra como
    ``15+D6`` o una abreviatura tienen que llegar intactas al cotejo.
    """
    return re.sub(r"\s+", " ", visible(text)).strip()


def normalize(text: str) -> str:
    """Clave de cotejo de un nombre impreso: minúsculas, sin comillas tipográficas.

    La fuente imprime ``“Busty” Gwen`` y el catálogo guarda el mismo nombre con
    comillas tipográficas y con guion suave en otro caso; comparar los nombres
    literales dejaría entradas sin localizar por tipografía.
    """
    return (
        flat(text)
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .lower()
    )


# --------------------------------------------------------------------------- #
# Dinero
# --------------------------------------------------------------------------- #

# Divisas que estos suplementos imprimen. ``gold coins`` y ``cold crowns`` son las
# variantes que el propio árbol ya reconoce en los costes de héroe.
UNITS = {
    "gc": "gold crowns",
    "gcs": "gold crowns",
    "gold crown": "gold crowns",
    "gold crowns": "gold crowns",
    "crown": "gold crowns",
    "crowns": "gold crowns",
    "gold coin": "gold crowns",
    "gold coins": "gold crowns",
    "gold": "gold crowns",
    "wt": "warp tokens",
    "warp token": "warp tokens",
    "warp tokens": "warp tokens",
    "dinar": "dinars",
    "dinars": "dinars",
    "doubloon": "doubloons",
    "doubloons": "doubloons",
    "cold crown": "cold crowns",
    "cold crowns": "cold crowns",
}
UNIT_PATTERN = "|".join(re.escape(unit) for unit in sorted(UNITS, key=len, reverse=True))
UNIT_WORDS = sorted({unit for unit in UNITS.values()}, key=len, reverse=True)

# Las dos formas de tarifa impresa, con y sin "to hire". El prefijo "Hire Fee:"
# lo llevan los Dramatis Personae de Karak Azgal y los de Relics.
FEE_HEAD = re.compile(r"\d+\s*(?:" + UNIT_PATTERN + r")?\s*to hire\b", re.I)
FEE_ALT = re.compile(r"\bhire fee\b\s*:?\s*\d+\s*(?:" + UNIT_PATTERN + r")?\b", re.I)

# Entre la tarifa impresa y su upkeep hay separadores, nunca letras: ``; +30``,
# ``* + 30``, ``, +35``, ``. +45``, `` +30``. Se acepta esa clase corta —y no
# cualquier cosa— para que un número de la prosa no pase por upkeep; de todos
# modos el upkeep sólo se lee si después viene la palabra "upkeep".
FEE_SEPARATOR = r"[\s,;.+*\u2020\u2021]{0,6}"

# Una fila de características: nueve dígitos, con o sin espacios entre ellos.
ROW_RUN = re.compile(r"\d(?:[\d\s]{5,}\d)")


class Fee(NamedTuple):
    """Una tarifa declarada: el importe y la divisa que la expresión nombra."""

    amount: int
    unit: str | None = None


def unit_of(text: str) -> str | None:
    """Divisa que nombra un texto impreso ('75 warp tokens' -> warp tokens).

    Sin frontera de palabra a la izquierda: la fuente pega la divisa al importe
    (``40GC``) y ``\\bgc\\b`` no la vería.
    """
    lowered = flat(text).lower()
    for word in UNIT_WORDS + [c for c in sorted(UNITS, key=len, reverse=True)]:
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", lowered):
            return UNITS.get(word, word)
    return None


def amount_of(value) -> int | None:
    """El importe de una tarifa: el número, o el primero de su expresión impresa."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.match(r"\s*(\d+)", str(value))
    return int(match.group(1)) if match else None


def fees_in(text: str) -> list[tuple[int, str | None, int | None, str | None]]:
    """Tarifas impresas: (importe, divisa, upkeep, divisa del upkeep)."""
    body = flat(text)
    out: list[tuple[int, str | None, int | None, str | None]] = []
    for match in FEE_HEAD.finditer(body):
        amount = int(re.match(r"\d+", match.group(0)).group(0))
        tail = body[match.end():match.end() + 60]
        upkeep = re.match(FEE_SEPARATOR + r"\+?\s*(\d+)\s*([A-Za-z ]{0,14}?)\s*upkeep\b",
                          tail, re.I)
        out.append((amount, unit_of(match.group(0)),
                    int(upkeep.group(1)) if upkeep else None,
                    unit_of(upkeep.group(2)) if upkeep and upkeep.group(2).strip() else None))
    for match in FEE_ALT.finditer(body):
        tail = body[match.end():match.end() + 60]
        upkeep = re.match(FEE_SEPARATOR + r"upkeep\s*:?\s*(\d+)\s*([A-Za-z ]{0,14}?)"
                          r"(?=[\s,;.]|$)", tail, re.I)
        fee_part = match.group(0)[match.group(0).lower().index("fee") + 3:].lstrip(" :")
        pair = (int(re.match(r"\d+", fee_part).group(0)), unit_of(match.group(0)),
                int(upkeep.group(1)) if upkeep else None,
                unit_of(upkeep.group(2)) if upkeep and upkeep.group(2).strip() else None)
        if pair not in out:
            out.append(pair)
    return list(dict.fromkeys(out))


def package_fee(entry: dict | None) -> Fee | None:
    """La tarifa que el paquete declara, con la divisa que su expresión nombra.

    El contrato guarda la expresión impresa en ``cost`` cuando la fuente no cobra
    en coronas ('40 dinars'), así que la divisa que el paquete declara es la que
    nombra su propia expresión, y coronas cuando es un número.
    """
    resources = ((entry or {}).get("resources") or {})
    for cost in resources.values():
        printed = (cost or {}).get("cost")
        unit = unit_of(printed) if isinstance(printed, str) else "gold crowns"
        return Fee(amount_of(printed) or 0, unit)
    return None


def fee_index(path: Path) -> dict[str, dict]:
    """``{profile_id: entry}`` de un documento de contratación (staging o KB).

    La forma es la misma en los dos árboles: ``hired_swords`` y
    ``dramatis_personae`` con ``profile_id``, ``hiring_fee`` y ``upkeep``.
    """
    if not path.is_file():
        return {}
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, dict] = {}
    for entry in (list(document.get("hired_swords") or [])
                  + list(document.get("dramatis_personae") or [])):
        out[str(entry.get("profile_id"))] = entry
    return out


# --------------------------------------------------------------------------- #
# Entradas
# --------------------------------------------------------------------------- #

STEP = 10  # separación con la que se sintetiza la geometría de una página web


@dataclass
class Block:
    """Un bloque de un documento: encabezado, línea de texto o fila de tabla.

    ``cells`` lleva las celdas de una fila en el orden del documento —que es el
    orden de sus columnas— y ``strongs`` los tramos en negrita del bloque, que es
    lo que distingue el nombre de un hechizo de su dificultad cuando la fuente los
    imprime en el mismo párrafo.
    """

    kind: str                 # "heading" | "line" | "row"
    text: str = ""
    level: int = 0
    cells: tuple[str, ...] = ()
    header: bool = False
    strongs: tuple[str, ...] = ()
    table: int = 0            # a qué tabla pertenece una fila, en orden


def line_at(index: int, text: str, tokens: Iterable[str] | None = None) -> dict:
    """Una línea con sus palabras posicionadas, en el orden en que se imprimen.

    Se usa para las fuentes cuya geometría ya viene escrita: cada celda de una
    tabla y cada palabra de un párrafo reciben su coordenada a partir del orden
    del documento, que para esas páginas *es* el orden de lectura.
    """
    parts = list(tokens) if tokens is not None else text.split()
    return {"text": text, "top": index * 100, "left": 0,
            "words": [(position * STEP, index * 100, part)
                      for position, part in enumerate(parts)]}


def entry_of(heading: str, blocks: Sequence[Block], last: bool = False,
             page: int | None = None, spillover: str = "") -> dict:
    """La entrada que comparten los tres corpus.

    ``blocks`` es el tramo de bloques del documento que la entrada ocupa: la fila
    de una tabla llega con una celda por palabra, que es lo que permite leerla en
    el orden de sus columnas en vez del orden del extractor.
    """
    lines: list[dict] = []
    for index, block in enumerate(blocks):
        if block.kind == "row":
            cells = [str(cell) for cell in block.cells if str(cell).strip()]
            lines.append(line_at(index, " ".join(cells), cells))
        else:
            lines.append(line_at(index, block.text))
    return {"heading": heading.strip(), "lines": [line["text"] for line in lines],
            "line_words": [line["words"] for line in lines],
            "last_on_page": last, "page": page, "spillover": spillover,
            "text": prose(" ".join(line["text"] for line in lines))}


def fee_line(text: str) -> bool:
    """Una línea abre una entrada si imprime su tarifa, en cualquiera de sus formas."""
    return bool(FEE_HEAD.search(text) or FEE_ALT.search(text))


def is_heading(line: str) -> bool:
    """Una línea que puede ser el encabezado de una entrada.

    Los encabezados van en una tipografía de display que el extractor devuelve a
    veces como letras sueltas, así que no se reconoce el nombre: se reconoce la
    forma — corta, de letras, sin puntuación de prosa ni cifras.
    """
    text = visible(line).strip()
    if not text or len(text) > 60 or len(text.split()) > 8:
        return False
    if re.search(r"[:;.!?]", text) or re.search(r"\d{2,}", text):
        return False
    return bool(re.search(rf"[{PUA}A-Za-z]{{3,}}", text))


def entries(lines: Sequence[dict], separator=None) -> list[dict]:
    """Entradas de una página: encabezado, líneas de contenido y su texto.

    Sin ``separator`` una entrada empieza en su tarifa impresa y se le busca el
    encabezado por encima —la línea con forma de encabezado por encima de la
    tarifa, aunque la tarifa venga tras la prosa, como en los Dramatis de Karak
    Azgal— y termina donde empieza la siguiente. Un texto de regla que la fuente
    imprime al principio de la columna siguiente (el caso de ``Drunken``, tercera
    regla del Norse Bearman impresa sobre la columna del Whaler) queda dentro de
    su entrada porque el orden de lectura lo sitúa entre su encabezado y el del
    vecino.

    Con ``separator`` la fuente declara dónde empieza cada entrada (el ancla
    ``Source:`` del texto plano de 2A) y ésta empieza en la línea que lo precede:
    así se leen las fuentes de una sola columna cuyo encabezado no se distingue
    de la prosa por su forma.
    """
    if separator is not None:
        starts = [max(0, index - 1) for index, line in enumerate(lines)
                  if separator(line["text"])]
    else:
        fees = [index for index, line in enumerate(lines) if fee_line(flat(line["text"]))]
        starts = []
        for index, fee_index in enumerate(fees):
            floor = fees[index - 1] + 1 if index else 0
            start = fee_index
            for above in range(fee_index - 1, floor - 1, -1):
                if is_heading(lines[above]["text"]):
                    start = above
                    break
            starts.append(start)
    out: list[dict] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        chunk = lines[start:end]
        heading = next((line["text"] for line in reversed(chunk[:1])
                        if is_heading(line["text"])), "")
        if not heading:
            above = [line["text"] for line in lines[max(0, start - 2):start]]
            heading = next((text for text in reversed(above) if is_heading(text)), "")
        out.append({"heading": heading.strip(),
                    "lines": [line["text"] for line in chunk],
                    "line_words": [line["words"] for line in chunk],
                    "last_on_page": index == len(starts) - 1, "page": None,
                    "spillover": "",
                    "text": flat(" ".join(line["text"] for line in chunk))})
    return out


# --------------------------------------------------------------------------- #
# Fila de características y rating
# --------------------------------------------------------------------------- #

# Encabezado de la fila de características. Los Dramatis de Karak Azgal no
# imprimen la palabra 'Profile': su tabla empieza directamente en las columnas, y
# en la fuente pegada una columna puede salir en un solo token ('WI' es W e I).
# La tabla de 2A puede añadir una columna que el catálogo no modela ('Save'), y
# entonces también es una columna de la tabla.
COLUMN_HEAD = re.compile(r"^(?:profile|[mwsbtiald]{1,3}|save)$", re.I)


def digits_row(digits: str, swap: bool = False) -> str:
    chars = list(re.sub(r"\D", "", digits))
    if swap and len(chars) >= 9:
        # Los suplementos MIM imprimen A antes que I; el árbol usa el orden KB.
        chars[6], chars[7] = chars[7], chars[6]
    return "".join(chars)


def row_header(words: list[tuple[int, int, str]]) -> bool:
    """Una línea que es el encabezado de columnas de una fila de características."""
    tokens = [word[2].strip() for word in words if word[2].strip()]
    return len(tokens) >= 6 and all(COLUMN_HEAD.fullmatch(token) for token in tokens)


def stat_header(words: list[tuple[int, int, str]]) -> bool:
    """Una línea que encabeza una tabla de características.

    La tabla puede anunciarse con el título «Profile» o empezar directamente en sus
    columnas (los Dramatis de Karak Azgal no lo imprimen).
    """
    return (any(re.fullmatch(r"Profile", word[2].strip(), re.I) for word in words)
            or row_header(words))


def stat_rows(entry: dict) -> list[str]:
    """Las filas de características de la entrada, en el orden en que se imprimen.

    Una entrada puede imprimir más de una —el Wolf-Priest de Ulric lleva la suya
    y la de su lobo, y los Dramatis de 2A con montura llevan jinete y montura— y
    la fila puede quedar partida entre líneas físicas o traer dígitos pegados
    (``41`` es I4 A1). Se toman las líneas que siguen al encabezado ``Profile`` y
    se leen **ordenadas por su margen izquierdo**, que es el orden de las columnas
    de la tabla: en el Fire-Eater el ``4`` de Movement sale de la geometría en una
    línea distinta a la de los otros ocho dígitos y leerlo en el orden del
    extractor daría una fila rotada. Los grupos entre paréntesis no cuentan: el
    Fire-Eater imprime ``4(6)`` porque el 6 es la variante de los Ogre Maneaters.
    """
    def digits_in(line: list[tuple[int, int, str]]) -> str:
        return "".join(re.sub(r"\D", "", word[2]) for word in line
                       if not re.fullmatch(r"\(.*\)", word[2]))

    rows: list[str] = []
    line_words = entry.get("line_words") or []
    for index, words in enumerate(line_words):
        if not stat_header(words):
            continue
        band: list[list[tuple[int, int, str]]] = []
        for following in line_words[index + 1:index + 4]:
            band.append(following)
            if len("".join(digits_in(line) for line in band)) >= 9:
                break
        ordered = sorted(band, key=lambda line: min((w[0] for w in line), default=0))
        digits = "".join(digits_in(line) for line in ordered)
        # Nueve dígitos son una fila; más es una fila con una característica de dos
        # dígitos (Ld 10) o, si son muchos más, prosa de la columna vecina que la
        # lectura por geometría no pudo separar de la fila.
        if 9 <= len(digits) <= 12:
            rows.append(digits)
    if not rows and not any(entry.get("line_words") or []):
        # Respaldo sin geometría: las tandas de nueve dígitos junto a 'Profile'.
        body = re.sub(r"\([^)]*\)", " ", entry.get("text", ""))
        for match in ROW_RUN.finditer(body):
            digits = re.sub(r"\D", "", match.group(0))
            if 9 <= len(digits) <= 12:
                rows.append(digits)
    return list(dict.fromkeys(rows))


# El cupo que un encabezado imprime delante del nombre del perfil («0 – 2 Snotling
# BigSnotz», «1 Halfling Elder»): el nombre del perfil es el que queda.
QUOTA = re.compile(r"^[^A-Za-z]*")


def profile_name(heading: str) -> str:
    """El nombre de un perfil sin el cupo que su encabezado imprime delante."""
    return QUOTA.sub("", heading).strip() or heading.strip()


def ratings_in(text: str) -> list[int]:
    """Ratings impresos ('+30 points')."""
    body = flat(text)
    out = [int(m.group(1)) for m in
           re.finditer(r"rating by\s*\+?\s*(\d+)\s*points?", body, re.I)]
    if not out:
        out = [int(m.group(1)) for m in
               re.finditer(r"rating\s*(?:of|by|is)?\s*\+?(\d+)\b", body, re.I)]
    return out


def rule_terms(name: str) -> list[str]:
    """Los términos con los que una etiqueta de regla se busca en lo impreso.

    Dos palabras de cuatro letras o más: una etiqueta corta ('Fear') se busca por
    ella misma, y una larga ('Aethereal Hoarder') por sus dos primeras palabras,
    que es lo que la fuente imprime separado del texto de la regla.
    """
    return re.findall(r"[A-Za-z']{4,}", name)[:2]


# --------------------------------------------------------------------------- #
# Corpus: las tres formas de leer una fuente
# --------------------------------------------------------------------------- #

# Un tramo de puntos dentro de una palabra. La capa de texto de varios suplementos
# —los de Ricco's Eternal Life, y páginas sueltas de los KAZ— escribe los espacios
# entre palabras como puntos: el nodo dice «A.Revenant.starts.with.20.experience»
# donde la página imprime «A Revenant starts with 20 experience». El punto separa
# palabras ahí; el que **termina** la frase es puntuación y se conserva.
WORD_DOTS = re.compile(r"\.+")


def _node_words(text: str) -> list[str]:
    """Las palabras que imprime un nodo de texto, deshaciendo sus puntos-separador.

    Los puntos que separan palabras se cortan («20.experience» son dos), y el punto
    final se queda donde la capa lo puso, que es donde termina la frase. Una tirada
    de puntos sola —el punteado guía de las listas de precio— se deja entera.
    """
    words: list[str] = []
    for token in text.split():
        trailing = ""
        if len(token) > 1 and token.endswith("."):
            token, trailing = token[:-1], "."
        parts = [part for part in WORD_DOTS.split(token) if part]
        if not parts:
            words.append(trailing or token)
            continue
        parts[-1] += trailing
        words.extend(parts)
    return words


def _xml_words(xml: str) -> list[tuple[int, int, float, str]]:
    words: list[tuple[int, int, float, str]] = []
    pattern = re.compile(
        r'<text top="(-?\d+)" left="(-?\d+)" width="(-?\d+)"[^>]*>(.*?)</text>', re.S)
    for match in pattern.finditer(xml):
        top, left, width = int(match.group(1)), int(match.group(2)), int(match.group(3))
        text = html.unescape(re.sub(r"<[^>]+>", "", match.group(4))).strip()
        if not text:
            continue
        parts = _node_words(text)
        for index, part in enumerate(parts):
            # Un nodo puede traer varias palabras: su posición se reparte en su caja.
            words.append((top, int(left + width * index / len(parts)),
                          max(width / len(parts), 2.0), part))
    return words


def column_split(words: list[tuple[int, int, float, str]]) -> int | None:
    """Coordenada del canal entre las dos columnas, o ``None`` si hay una sola.

    Se busca la vertical que menos palabras cruzan en la banda central de la
    página; una página a dos columnas la deja prácticamente vacía y una a una
    columna la cruzan todas las líneas de prosa, así que el umbral separa los dos
    casos con holgura. Una página que no se deja separar se lee entera, y el
    cotejo dirá que no pudo leer la entrada en vez de inventar un hallazgo.
    """
    if not words:
        return None
    right = max(left + width for _top, left, width, _text in words)
    best: int | None = None
    best_x: int | None = None
    for x in range(int(0.30 * right), int(0.70 * right)):
        crossing = sum(1 for _top, left, width, _text in words if left < x < left + width)
        if best is None or crossing < best:
            best, best_x = crossing, x
    if best is None or best_x is None or best > max(2, int(0.005 * len(words))):
        return None
    return best_x


def raw_lines(words: list[tuple[int, int, float, str]]) -> list[list[tuple[int, int, float, str]]]:
    """Palabras agrupadas por su coordenada vertical, de izquierda a derecha."""
    rows: dict[int, list[tuple[int, int, float, str]]] = {}
    for word in sorted(words):
        key = next((k for k in rows if abs(k - word[0]) <= 4), None)
        if key is None:
            rows[word[0]] = [word]
        else:
            rows[key].append(word)
    return [sorted(rows[k], key=lambda w: w[1]) for k in sorted(rows)]


# Hueco mínimo para considerar que una línea física son dos líneas de columnas
# distintas (el canal de estas páginas mide entre 15 y 40 pt).
GUTTER_GAP = 14


def pieces(row: list[tuple[int, int, float, str]],
           split: int | None) -> list[list[tuple[int, int, float, str]]]:
    """Trocea una línea física en sus tramos de columna.

    Una tarifa como ``45 gold crowns to hire`` puede rebasar el canal: sus
    palabras están a los dos lados aunque la línea sea una sola. Sólo se corta
    donde el hueco entre palabras cruza el canal, que es lo que separa la última
    palabra de una columna de la primera de la otra; repartir por la posición de
    cada palabra partiría esa tarifa y la dejaría sin leer.
    """
    if split is None:
        return [row]
    out: list[list[tuple[int, int, float, str]]] = [[]]
    for word in row:
        previous = out[-1][-1] if out[-1] else None
        if previous and word[1] - (previous[1] + previous[2]) > GUTTER_GAP \
                and previous[1] < split <= word[1] + word[2]:
            out.append([word])
        else:
            out[-1].append(word)
    return [piece for piece in out if piece]


# --------------------------------------------------------------------------- #
# De la geometría a la celda, la fila y la lista de precios
# --------------------------------------------------------------------------- #

# Hueco (pt) a partir del cual una línea imprime dos columnas. Medido sobre las
# páginas de los dos árboles: la prosa separa sus palabras con menos de 2 pt y
# una tabla separa sus columnas con más de 18 —el nombre de su fila, más de 50—,
# así que el umbral distingue las dos cosas sin partir ninguna frase.
CELL_GAP = 12.0

# El nombre de una fila y el precio que imprime su celda están separados por el
# punteado guía y, en las listas del KAZ, por un simple espacio.
LEADER = re.compile(r"[\s.\u00b7\u2026/_\-]+")
LETTERS = re.compile(r"[A-Za-z]")
# Lo que una celda imprime antes de su tarifa sin nombrar a nadie: la forma
# «1st free/2 gc» imprime el primer precio y el segundo en la misma celda, así que
# su texto de delante es tarifa, no nombre («1 SCARFACE . . . 70 gc» no lo es).
PSEUDO_PRICE = re.compile(r"^\W*(?:\d+(?:st|nd|rd|th)?\s*)?(?:free|each|ea|only|per)\W*$", re.I)
# La etiqueta que anuncia la tarifa en vez de nombrarla («Cost: 90 GCs», «Hire
# fee: 25 gc»): el nombre de esa fila es el que imprime la línea de arriba.
PRICE_LABEL = re.compile(r"^\W*(?:cost|price|hire\s*fee|fee|costs?)\W*:?\W*$", re.I)

# Toda divisa con la que las fuentes tasan una lista: coronas (gc), tokens de
# disformidad (wt/tc, las listas skaven) y dinares (las árabes). El patrón se ancla
# al importe, y admite la forma «1st free/2 gc», que imprime dos.
CURRENCY = (r"gcs?|gc's|gold[\s.\u00b7]*crowns?|gold[\s.\u00b7]*cronws?|gold|coronas?|crowns?|"
            r"warps?[\s.\u00b7]*tokens?|wt|tc|dinars?")
# Entre el importe y su divisa puede no haber espacio: las páginas de Relics of the
# Crusades separan las palabras con un punto («Dagger .. .. .. .. 2.dinars»).
GAP = r"[\s.\u00b7]*"
PRICE_LINE = re.compile(rf"(?<![0-9A-Za-z])(\d{{1,4}}){GAP}(?:/{GAP}(\d{{1,4}}){GAP})?"
                        rf"(?:{CURRENCY})\b", re.I)
# Un precio de fórmula lleva su cifra base («75+5D6 gold crowns», «100 + D6x10 gold
# crowns»), que es la que el catálogo guarda: los dados suman sobre ella.
FORMULA_BASE = re.compile(r"(\d{1,4})\s*(?:\+\s*D6\s*[x\u00d7]\s*\d+"
                          r"|(?:\+|x)\s*(?:\d+\s*)?D6)", re.I)
# La tarifa impresa puede ser un multiplicador en vez de un importe: el suplemento
# tasa el objeto con el precio de otro («Ithilmar weapon * 2 x price», «Gromril
# Weapon 3x the cost»). La cifra que lleva multiplica, no tasa: la fila se lee como
# una de fórmula —el nombre es el texto que la precede y su importe no es un precio
# en coronas—, y sin reconocerla la fila no se leía y el objeto parecía no imprimirse.
MULTIPLIER = re.compile(r"(?<![0-9])(?:\d{1,3}\s*(?:[x\u00d7]|times)\s*(?:the\s+)?(?:cost|price)s?"
                        r"|(?:cost|price)s?\s*[x\u00d7]\s*\d{1,3})\b", re.I)


class Cell(NamedTuple):
    """Un tramo continuo de una línea impresa: lo que una columna imprime."""

    left: float
    right: float
    text: str


def cells(line: Mapping) -> list[Cell]:
    """Las celdas de una línea impresa: se corta donde el hueco es de columna.

    Una línea sin geometría —las que se sintetizan para las fuentes que ya vienen
    estructuradas (``line_at``)— es una sola celda: ahí el reparto en columnas lo
    hizo el documento, no la posición de las palabras.
    """
    spans = line.get("spans") or []
    if not spans:
        text = " ".join(str(line.get("text") or "").split())
        return [Cell(0.0, 0.0, text)] if text else []
    first_left, _first_top, first_right, first_text = spans[0]
    out: list[list[tuple[float, float, str]]] = [
        [(float(first_left), float(first_right), first_text)]]
    for left, _top, right, text in spans[1:]:
        if float(left) - out[-1][-1][1] > CELL_GAP:
            out.append([])
        out[-1].append((float(left), float(right), text))
    return [Cell(piece[0][0], max(word[1] for word in piece),
                 " ".join(word[2] for word in piece)) for piece in out]


def covering_cell(above: Sequence[Cell], cell: Cell) -> Cell | None:
    """La celda de la línea de arriba que cubre la horizontal de ésta, si la hay.

    Las tablas de equipo de los suplementos parten su celda en dos líneas físicas:
    el nombre arriba y la tarifa debajo, dentro de la misma columna. El nombre es la
    celda de arriba cuyo tramo horizontal cubre el de la tarifa; una celda que ya
    imprime un precio no nombra a nadie.
    """
    best: Cell | None = None
    overlap = 0.0
    for candidate in above:
        if not LETTERS.search(candidate.text) or PRICE_LINE.search(candidate.text):
            continue
        shared = min(candidate.right, cell.right) - max(candidate.left, cell.left)
        if shared > overlap:
            best, overlap = candidate, shared
    return best


def covering_name(above: Sequence[Cell], cell: Cell) -> str:
    """El texto de esa celda."""
    found = covering_cell(above, cell)
    return found.text.strip() if found else ""


def wrapped_heading(history: Sequence[tuple[int, Sequence[Cell]]], cover: Cell,
                    cover_top: int) -> str:
    """La línea que continúa un nombre partido, si la hay.

    Un nombre largo se imprime en dos líneas dentro de su columna ("bramstetter's
    advanced" / "construct thesis") y la tarifa va debajo de la segunda: el nombre
    completo es la celda que la cubre más la de arriba que la solapa. Se busca
    entre las líneas por encima de la que imprime la celda —no sólo en la de
    justo encima, que puede ser la columna vecina del mismo pliego— y la
    distancia se mide desde esa celda, no desde la tarifa, porque las dos líneas
    del nombre están más juntas entre sí que la última con su precio.
    """
    best: tuple[float, str] | None = None
    for line_top, above in reversed(history):
        if line_top >= cover_top:
            continue                # la línea de la propia celda, o la tarjeta de al lado
        if cover_top - line_top > NAME_ABOVE:
            break
        for candidate in above:
            if not LETTERS.search(candidate.text) or PRICE_LINE.search(candidate.text):
                continue
            shared = min(candidate.right, cover.right) - max(candidate.left, cover.left)
            if shared > 0 and (best is None or shared > best[0]):
                best = (shared, candidate.text.strip())
    return best[1] if best else ""


# Distancia horizontal (pt) a la que el nombre que encabeza una tarjeta cubre su
# línea de precio. Las tarjetas de los suplementos ponen el nombre centrado sobre
# su columna —de unos 330 pt— y la tarifa al ras de su margen, así que el nombre
# queda a una decena de puntos del precio y el de la columna vecina, a más de
# cien. Sólo se usa cuando la página no declara su canal, que es cuando una tabla
# a toda página lo anula para las dos columnas.
NAME_GAP = 80.0

# Altura (pt) hasta la que se busca ese nombre: va inmediatamente encima de su
# tarifa —39 pt en las páginas de equipo especial—, aunque las líneas de la
# columna vecina se cuelen entre las dos (en una página a dos columnas, hasta
# tres). Más arriba ya es la prosa de otra entrada.
NAME_ABOVE = 60


def heading_above(history: Sequence[tuple[int, Sequence[Cell]]], cell: Cell,
                  gutter: float | None, top: int) -> str:
    """El nombre que encabeza la línea de precio, cuando no la cubre por horizontal.

    Las páginas de equipo especial imprimen su tarjeta así: el nombre del ítem
    centrado en su columna y, debajo, la tarifa al ras del margen. El nombre no
    solapa el tramo de la tarifa, así que se reconoce por la columna —la que el
    canal de la página declara cuando lo hay— y por cercanía: de las líneas que
    quedan por encima dentro de la altura de una tarjeta, es el nombre que está a
    menos distancia horizontal del precio, y sólo cuenta si esa distancia es la
    de una tarjeta. La línea que se lee de arriba es el historial, porque entre
    las dos puede imprimirse la columna de al lado.
    """
    side = None if gutter is None else (cell.left + cell.right) / 2 >= gutter
    best: tuple[float, Cell, int] | None = None
    boundary: tuple[int, Sequence[Cell]] | None = None
    for line_top, above in reversed(history):
        # La altura vuelve a empezar en cada pliego: una línea que la trae mayor que
        # la de la tarjeta es de la página anterior, y con ella se acaba lo que esta
        # página imprime por encima.
        if line_top > top:
            boundary = (line_top, above)
            break
        if top - line_top > NAME_ABOVE:
            break
        best = nearest_by_gap(best, above, cell, gutter, side, line_top)
    if best is None and boundary is not None:
        # El nombre que cierra una página y tasa en la siguiente se lee sólo cuando
        # ésta no imprime ninguno por encima: los tramos de la anterior repiten la
        # misma banda horizontal —su altura se cuenta desde cero—, así que si
        # compitieran por cercanía le ganarían al nombre que sí está al lado.
        best = nearest_by_gap(None, boundary[1], cell, gutter, side, boundary[0])
    if best is None:
        return ""
    _gap, candidate, line_top = best
    head = wrapped_heading(history, candidate, line_top)
    text = candidate.text.strip()
    return f"{head} {text}".strip() if head else text


def nearest_by_gap(best: tuple[float, Cell, int] | None, above: Sequence[Cell],
                   cell: Cell, gutter: float | None, side: bool | None,
                   line_top: int) -> tuple[float, Cell, int] | None:
    """El nombre de esa línea a menos distancia horizontal de la tarjeta.

    Distancia y no solape: el nombre de una tarjeta va centrado en su columna y su
    tarifa al ras del margen, así que los dos tramos no se tocan. Sólo cuenta si
    esa distancia es la de una tarjeta, y la columna se exige cuando la página
    declara su canal. La celda vuelve con su línea, que es lo que permite leer el
    nombre partido en dos.
    """
    for candidate in above:
        if not LETTERS.search(candidate.text) or PRICE_LINE.search(candidate.text):
            continue
        if side is not None and \
                ((candidate.left + candidate.right) / 2 >= gutter) != side:
            continue
        gap = max(candidate.left - cell.right, cell.left - candidate.right, 0.0)
        if side is None and gap > NAME_GAP:
            continue
        if best is None or gap < best[0]:
            best = (gap, candidate, line_top)
    return best


def page_entries(found: Sequence[Cell], gutter: float | None) -> list[list[Cell]]:
    """Las entradas de una línea física, cada una con sus propias celdas.

    Una línea imprime varias entradas a la vez: una lista de tres columnas pone tres
    ítems en la misma altura, y una página a dos columnas, dos. La unidad la cierra
    su propio precio —una celda que tasa cierra la entrada que venía nombrando— y,
    cuando el canal de la página está declarado, lo que cae al otro lado de él es
    otra entrada aunque no lleve precio («Sword» | «10 gc»).
    """
    groups: list[list[Cell]] = []
    current: list[Cell] = []
    priced = False
    side: bool | None = None
    for cell in found:
        edge = None if gutter is None else (cell.left + cell.right) / 2 >= gutter
        if current and (priced or (edge is not None and side is not None and edge != side)):
            groups.append(current)
            current, priced = [], False
        current.append(cell)
        side = edge if side is None or edge != side else side
        # Tasado por el mismo criterio con que ``price_rows`` lee la fila: el
        # importe, la fórmula de dados y el multiplicador del precio de otro objeto.
        priced = priced or priced_cell(cell, ()) is not None
    if current:
        groups.append(current)
    return groups


def before_name(found: Sequence[Cell], price: Cell) -> str:
    """El nombre impreso a la izquierda de la tarifa, en su propia línea.

    Es la forma de las listas que imprimen el nombre y la tarifa en la misma línea
    pero en celdas distintas («Dagger» | «2 gc»), y de las que parten el nombre
    entre las dos («Short» / «Bow . . . 10 gc»): la celda más cercana a la
    izquierda que imprima letras y no imprima ningún precio ella misma.
    """
    best = ""
    for cell in found:
        if cell is price or cell.left >= price.left:
            break
        if LETTERS.search(cell.text) and not PRICE_LINE.search(cell.text):
            best = cell.text
    return best.strip()


# Una celda que sólo imprime la divisa: la tarifa a la que el extractor le asignó
# otra altura («Blunderbuss . . . . 30» y, en la línea siguiente, «gc»).
CURRENCY_ONLY = re.compile(rf"(?:{CURRENCY})\W*$", re.I)
TRAILING_NUMBER = re.compile(r"\d\W*$")


def currency_below(below: Sequence[Cell], cell: Cell) -> str:
    """La divisa de la línea siguiente que cubre esta celda, si la hay.

    El extractor reparte a veces la tarifa entre dos líneas físicas: deja el
    importe al final de la celda y la divisa sola en la de abajo. Sin la divisa la
    celda no imprime un precio, así que se lee de donde se imprimió.
    """
    for candidate in below:
        if not CURRENCY_ONLY.fullmatch(candidate.text.strip()):
            continue
        if min(candidate.right, cell.right) - max(candidate.left, cell.left) > 0:
            return candidate.text.strip()
    return ""


def priced_cell(cell: Cell, below: Sequence[Cell]) -> str | None:
    """El texto con que una celda tasa, o ``None`` si no imprime ninguna tarifa.

    Es la prueba de que la celda es una fila de lista: imprime un importe, una
    fórmula de dados o un multiplicador del precio de otro objeto. El extractor
    separa las cifras del importe («10 0gc», «3 5 gc») y la tarifa puede continuar
    en la celda de debajo de la misma columna («30» arriba y «gc» abajo), que es lo
    que aquí se une antes de decidir.
    """
    text = re.sub(r"(?<=\d) (?=\d)", "", cell.text)
    if PRICE_LINE.search(text) or FORMULA_BASE.search(text) or MULTIPLIER.search(text):
        return text
    if TRAILING_NUMBER.search(text):
        currency = currency_below(below, cell)
        if currency:
            return f"{text} {currency}"
    return None


def tariffs_in(text: str) -> tuple[list[int], bool]:
    """Los importes que una celda tasa, y si su tarifa es de fórmula.

    La fórmula —los dados que suman sobre una cifra base y el multiplicador del
    precio de otro objeto— no lleva un importe en coronas: su cifra no es la tarifa
    de la fila, así que se declara aparte y no se suma a los importes.
    """
    prices: set[int] = set()
    formula = False
    for hit in PRICE_LINE.finditer(text):
        prices.add(int(hit.group(1)))
        if hit.group(2):
            prices.add(int(hit.group(2)))
    for hit in FORMULA_BASE.finditer(text):
        prices.add(int(hit.group(1)))
        formula = True
    if MULTIPLIER.search(text):
        formula = True
    return sorted(prices), formula


def price_rows(lines: Sequence[Mapping], context: int = 0) -> list[dict]:
    """Las filas que imprimen un precio, con el nombre que lo acompaña.

    El precio se lee de la celda que lo imprime y el nombre de esa misma celda
    (``Dagger . . . . 2 gc``), de la celda anterior de la línea, o de la que cubre
    su horizontal en la línea inmediatamente superior (las listas a dos columnas
    parten la celda: el nombre arriba y la tarifa debajo). Leerlo así —en la fila
    y no en una ventana del texto aplanado— es lo que impide atribuir a un ítem el
    precio de la fila vecina, que es el defecto que la ventana admitía.

    ``lines`` son las líneas **físicas** de la página (``PdfCorpus.rows``): una
    fila de tabla cruza a menudo el canal que separa las columnas de la prosa, así
    que se lee entera y son sus celdas las que reparten sus columnas.

    ``context`` declara cuántas de esas líneas vienen de la página anterior para
    que una lista que cruza el pliego —el nombre cierra una y la tarifa abre la
    siguiente— siga leyéndose: se usan como contexto, pero no tasan nada por sí
    solas, que ya se leyeron en su página.
    """
    out: list[dict] = []
    # Las últimas líneas leídas, con su altura: entre un nombre de tarjeta y su
    # tarifa pueden imprimirse las líneas de la columna vecina. Las ``context``
    # primeras son el final del pliego anterior y se conservan —el nombre que
    # cierra una página y tasa en la siguiente—; las de esta página se podan por
    # altura, no por número de líneas, porque la interlínea cambia mucho de una
    # página a otra y un tope fijo dejaba fuera la primera mitad de un nombre
    # partido en dos («bramstetter's advanced» / «construct thesis»).
    history: list[tuple[int, list[Cell]]] = []
    rows_of_cells = [cells(line) for line in lines]
    for index, line in enumerate(lines):
        found = rows_of_cells[index]
        below = rows_of_cells[index + 1] if index + 1 < len(rows_of_cells) else []
        gutter = line.get("gutter")
        top = line.get("top", 0)
        above = history[-1][1] if history else []
        if index < context:
            history.append((top, found))
            continue
        for entry in page_entries(found, gutter):
            # Cada celda de la línea que tasa es una fila: la tabla de los
            # suplementos reparte tres filas por línea física —«Axe 5 gc» | «Gromril
            # Weapon 3x the cost» | «Dagger 1st free/2gc»—, así que una sola fila
            # por línea dejaba las otras dos sin leer y el objeto que imprimen
            # parecía no estar en la lista.
            priced = [(cell, text) for cell, text in
                      ((cell, priced_cell(cell, below)) for cell in entry) if text]
            for price, text in priced:
                prices, formula = tariffs_in(text)
                # El nombre es el texto que precede a la tarifa, sea un importe o un
                # multiplicador («Gromril Weapon 3x the cost» nombra al arma de
                # Gromril).
                tail = (PRICE_LINE.search(text) or MULTIPLIER.search(text)
                        or FORMULA_BASE.search(text))
                named = LEADER.sub(" ", text[:tail.start()]).strip() if tail else ""
                # El nombre de la fila se lee así: el que su propia celda imprime
                # antes de la tarifa, o —cuando la celda sólo imprime tarifa o su
                # etiqueta, como la forma «1st free/2 gc» y «Cost: 90 GCs»— el que
                # imprime la celda de su izquierda; y si no hay ninguno, el de la
                # línea de arriba que cubre su horizontal (las listas a dos
                # columnas parten la celda entre dos líneas) o el que la encabeza.
                # ``above`` declara siempre el de la línea de arriba, que el driver
                # también coteja: la fila impresa es su celda y la que la cubre, y
                # hay formas —la tarjeta con el nombre en dos líneas, la regla que
                # tasa una mascota con «Cost:»— en las que el nombre está ahí aunque
                # la celda imprima algo delante.
                # Cada tarifa de la celda lleva delante el texto que la nombra: una
                # línea de prosa tasa dos veces («Dark Venom at a cost of 20 gold
                # crowns and Black Lotus at a cost of 10 gold crowns») y el nombre
                # de la segunda no es el que abre la línea.
                spans: list[str] = []
                seen = 0
                for hit in PRICE_LINE.finditer(text):
                    spans.append(LEADER.sub(" ", text[seen:hit.start()]).strip())
                    seen = hit.end()
                labelled = bool(named) and bool(PSEUDO_PRICE.match(named)
                                                or PRICE_LABEL.match(named))
                name = named if LETTERS.search(named) and not labelled else ""
                cover = covering_cell(above, price) if above else None
                if not name:
                    name = (before_name(entry, price) if labelled else "") \
                        or (cover.text.strip() if cover else "") \
                        or before_name(entry, price) \
                        or heading_above(history, price, gutter, top)
                if cover is not None and name == cover.text.strip():
                    head = wrapped_heading(history, cover,
                                           history[-1][0] if history else top)
                    name = f"{head} {name}".strip() if head else name
                out.append({"name": name, "above": cover.text.strip() if cover else "",
                            "names": [span for span in spans if span],
                            "prices": prices, "formula": formula,
                            "cell": price.text.strip(),
                            "raw": str(line.get("text") or ""), "top": top})
        history.append((top, found))
        while len(history) > context + 1 and top - history[context][0] > NAME_ABOVE * 2:
            del history[context]
    return out


class PdfCorpus:
    """Páginas de un PDF leídas por geometría, con su caché por página."""

    def __init__(self, cache: Path, words: Path, texts: Path) -> None:
        self.cache = cache
        self.words = words
        self.texts = texts
        self._lines: dict[tuple[str, int], list[dict]] = {}

    def pdf_for(self, stem: str) -> Path | None:
        """PDF de un nombre de referencia, en la caché o en su subcarpeta extra."""
        for candidate in (self.cache / f"{stem}.pdf", self.cache / "extra" / f"{stem}.pdf"):
            if candidate.is_file():
                return candidate
        return None

    def word_lines(self, stem: str, page: int) -> list[tuple[int, int, float, str]]:
        """Palabras de una página con su posición; el XML se cachea por página."""
        pdf = self.pdf_for(stem)
        if pdf is None:
            return []
        out = self.words / f"{stem}.p{page}.xml"
        if not out.exists():
            self.words.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(["pdftohtml", "-xml", "-hidden", "-f", str(page),
                                "-l", str(page), str(pdf), str(out.with_suffix(""))],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            except OSError:
                return []
            if not out.exists():
                return []
        return _xml_words(out.read_text(encoding="utf-8", errors="replace"))

    def plain_lines(self, stem: str, page: int) -> list[str]:
        """Texto de la página sin geometría (respaldo cuando ``pdftohtml`` falta)."""
        pdf = self.pdf_for(stem)
        if pdf is None:
            return []
        result = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace")
        return result.stdout.splitlines()

    def page_text(self, stem: str, page: int) -> str:
        """Texto plano de una página, cacheado (prefiltro barato de candidatas)."""
        cache = self.texts / f"{stem}.p{page}.txt"
        if not cache.exists():
            self.texts.mkdir(parents=True, exist_ok=True)
            cache.write_text("\n".join(self.plain_lines(stem, page)), encoding="utf-8")
        return cache.read_text(encoding="utf-8", errors="replace")

    def page_count(self, stem: str) -> int:
        pdf = self.pdf_for(stem)
        if pdf is None:
            return 0
        result = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
        return int(match.group(1)) if match else 0

    def lines(self, stem: str, page: int) -> list[dict]:
        """Líneas de la página en orden de lectura (columna izquierda, luego derecha).

        Cada línea guarda sus palabras con la **extensión** que ocupan (``spans``),
        que es lo que permite repartirla en celdas: ``words`` mantiene la forma que
        consumen los chequeos de perfil.
        """
        if (stem, page) in self._lines:
            return [dict(line) for line in self._lines[(stem, page)]]
        words = self.word_lines(stem, page)
        if not words:
            plain = [{"text": decode(line), "top": index, "left": 0, "words": [],
                      "spans": []}
                     for index, line in enumerate(self.plain_lines(stem, page))]
            self._lines[(stem, page)] = plain
            return [dict(line) for line in plain]
        split = column_split(words)
        columns: dict[int, list[list[tuple[int, int, float, str]]]] = {0: [], 1: []}
        for row in raw_lines(words):
            for piece in pieces(row, split):
                column = 1 if (split is not None and piece[0][1] >= split) else 0
                columns[column].append(piece)
        lines: list[dict] = []
        for column in (0, 1):
            for piece in sorted(columns[column], key=lambda p: (p[0][0], p[0][1])):
                lines.append({"text": decode(" ".join(word[3] for word in piece)),
                              "top": piece[0][0], "left": piece[0][1],
                              "words": [(word[1], word[0], decode(word[3])) for word in piece],
                              "spans": [(word[1], word[0], word[1] + word[2], decode(word[3]))
                                        for word in piece]})
        self._lines[(stem, page)] = lines
        return [dict(line) for line in lines]

    def pages(self, stem: str) -> list[int]:
        """Las páginas del documento, en orden (vacío si el PDF no está cacheado)."""
        return list(range(1, self.page_count(stem) + 1))

    def document_lines(self, stem: str, pages: Sequence[int] | None = None) -> list[dict]:
        """Las líneas de las páginas del documento, en orden de lectura."""
        out: list[dict] = []
        for page in (self.pages(stem) if pages is None else pages):
            for line in self.lines(stem, page):
                out.append({**line, "page": page})
        return out

    def text(self, stem: str, pages: Sequence[int] | None = None,
             markers: bool = True) -> str:
        """El documento en orden de lectura: el texto que antes daba ``pdftotext``.

        Sustituye a la extracción con ``-layout``, que conservaba el orden de las
        columnas a costa de comprimir sus desplazamientos y perder líneas al
        intercalarlas: aquí cada columna se lee entera, en su orden, y la página
        sigue declarándose con el mismo marcador que usa el árbol (``===== page
        N =====``), que es lo que permite atribuir una línea a su página.
        """
        out: list[str] = []
        for page in (self.pages(stem) if pages is None else pages):
            if markers:
                out.append(f"===== page {page} =====")
            out.extend(line["text"] for line in self.lines(stem, page))
        return "\n".join(out)

    def physical_lines(self, stem: str, page: int) -> list[dict]:
        """Las líneas **físicas** de la página: lo que se imprime en la misma
        altura, de izquierda a derecha, sin partir la página en columnas.

        Es la vista que necesita una tabla, porque una tabla no respeta el canal
        que separa las columnas de la prosa: la tabla de habilidades de una página
        a dos columnas ocupa la página entera, y sus encabezados —a la misma
        altura, a los dos lados del canal— son la **misma** fila.
        """
        if ("physical", stem, page) in self._lines:
            return [dict(line) for line in self._lines[("physical", stem, page)]]
        words = self.word_lines(stem, page)
        gutter = column_split(words)
        out: list[dict] = []
        if not words:
            out = [{"text": decode(line), "top": index, "left": 0, "words": [],
                    "spans": [], "gutter": None}
                   for index, line in enumerate(self.plain_lines(stem, page))]
        else:
            for row in raw_lines(words):
                spans = [(word[1], word[0], word[1] + word[2], decode(word[3]))
                         for word in row]
                out.append({"text": decode(" ".join(word[3] for word in row)),
                            "top": row[0][0], "left": row[0][1],
                            "words": [(span[0], span[1], span[3]) for span in spans],
                            "spans": spans, "gutter": gutter})
        self._lines[("physical", stem, page)] = out
        return [dict(line) for line in out]

    def physical(self, stem: str, pages: Sequence[int] | None = None) -> list[dict]:
        """Las líneas físicas de las páginas del documento, en orden."""
        return [{**line, "page": page}
                for page in (self.pages(stem) if pages is None else pages)
                for line in self.physical_lines(stem, page)]

    def rows(self, stem: str, page: int) -> list[Row]:
        """Filas de tabla de la página: sus líneas físicas partidas en celdas."""
        out: list[Row] = []
        for index, line in enumerate(self.physical_lines(stem, page)):
            found = cells(line)
            if len(found) < 2:
                continue
            out.append(Row(tuple(cell.text for cell in found), index,
                           spans=tuple(found), page=page))
        return out

    def entries(self, stem: str, page: int) -> list[dict]:
        found = entries(self.lines(stem, page))
        for entry in found:
            entry["page"] = page
        return found

    def continuation(self, stem: str, page: int, subject: str, names: Sequence[str],
                     candidates_for=None) -> str:
        """Texto que la fuente imprime al principio de la página siguiente.

        Una regla larga se desborda a la página contigua (las de Snorri están en
        la p63 aunque su perfil esté en la p62). Se lee hasta la tarifa de la
        siguiente entrada o hasta el encabezado que nombra a **otro** personaje
        del árbol; un subtítulo propio de la entrada —'SPECIAL RULES'— no la
        interrumpe.
        """
        if page >= self.page_count(stem):
            return ""
        out: list[str] = []
        for line in self.lines(stem, page + 1):
            text = flat(line["text"])
            if fee_line(text):
                break
            if is_heading(line["text"]) and names_another(text, subject, names,
                                                           candidates_for=candidates_for):
                break
            out.append(line["text"])
        return flat(" ".join(out))


def names_another(text: str, subject: str, names: Sequence[str],
                  candidates_for=None) -> bool:
    """Si el texto nombra a otro personaje del árbol (encabezado de otra entrada)."""
    candidates_for = candidates_for or (lambda name: [name])
    lowered = normalized_key(text)
    for name in names:
        if name == subject:
            continue
        if any(len(c) >= 6 and normalize(c) in lowered for c in candidates_for(name)):
            return True
    return False


def normalized_key(text: str) -> str:
    """Clave de búsqueda de un texto impreso (ver ``normalize``)."""
    return normalize(text)


@dataclass(frozen=True)
class Heading:
    """Un encabezado del documento, con el bloque que lo abre y su nivel."""

    level: int
    text: str
    index: int


@dataclass(frozen=True)
class Row:
    """Una fila de tabla: sus celdas en el orden de las columnas, y su bloque."""

    cells: tuple[str, ...]
    index: int
    header: bool = False
    table: int = 0
    spans: tuple[Cell, ...] = ()
    page: int = 0

    @property
    def text(self) -> str:
        return " ".join(cell for cell in self.cells if cell.strip())


class _Structure(HTMLParser):
    """Bloques de un documento HTML, en orden, con sus contenedores.

    Un encabezado, un párrafo, un ítem de lista y una fila de tabla son bloques: el
    texto de un bloque es el de sus etiquetas, y las celdas de una fila se leen en
    el orden del documento, que es el orden de sus columnas. Los ``div`` con clase
    se registran como **contenedores** con su tramo de bloques (``div.fighter``
    delimita una entrada de la página de los Dramatis Personae; la lista de una
    banda la delimita el encabezado que la publica), y los tramos en negrita se
    guardan por bloque. Leer por estructura es lo que hace que una celda con
    etiquetas dentro, una entidad escapada o un encabezado con enlaces no se
    pierdan ni se mezclen con la tabla del vecino.
    """

    LINE_TAGS = ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6")

    def __init__(self, container_classes: Sequence[str] = ()) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self.spans: list[tuple[str, int, int]] = []     # (clase, bloque inicial, final)
        self.container_classes = tuple(container_classes)
        self._containers: list[tuple[str, int]] = []
        self._divs: list[bool] = []
        self._line: list[str] | None = None
        self._level = 0
        self._strongs: list[str] = []
        self._strong: list[str] | None = None
        self._cells: list[str] | None = None
        self._cell: list[str] | None = None
        self._header = False
        self._tables = 0

    # -- bloques ---------------------------------------------------------- #

    def _line_open(self) -> None:
        if self._cells is None and self._line is None:
            self._line, self._strongs = [], []

    def _line_close(self) -> None:
        if self._line is None:
            self._level = 0
            return
        text = prose(" ".join(self._line))
        strongs = tuple(value for value in (prose(s) for s in self._strongs) if value)
        kind = "heading" if self._level else "line"
        level, self._line, self._level, self._strongs = self._level, None, 0, []
        if text:
            self.blocks.append(Block(kind=kind, text=text, level=level, strongs=strongs))

    # -- elementos -------------------------------------------------------- #

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "div":
            classes = (dict(attrs).get("class") or "").split()
            name = next((value for value in classes if value in self.container_classes), "")
            if name:
                self._containers.append((name, len(self.blocks)))
            self._divs.append(bool(name))
            return
        if tag == "table":
            self._tables += 1
            return
        if tag == "tr":
            self._cells, self._header = [], False
            return
        if tag in ("td", "th"):
            if self._cells is not None:
                self._cell, self._header = [], self._header or tag == "th"
            return
        if tag in ("strong", "b"):
            self._strong = [] if self._cells is None else None
            return
        if tag in self.LINE_TAGS:
            if tag.startswith("h") and tag[1:].isdigit():
                self._level = int(tag[1:])
            self._line_open()

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th"):
            if self._cells is not None and self._cell is not None:
                self._cells.append(prose(" ".join(self._cell)))
            self._cell = None
            return
        if tag == "tr":
            if self._cells is not None:
                cells = tuple(self._cells)
                self.blocks.append(Block(kind="row", cells=cells, header=self._header,
                                         table=self._tables,
                                         text=" ".join(cell for cell in cells if cell.strip())))
            self._cells, self._header = None, False
            return
        if tag in ("strong", "b"):
            if self._strong is not None:
                value = prose(" ".join(self._strong))
                if value:
                    self._strongs.append(value)
            self._strong = None
            return
        if tag == "div":
            self._line_close()
            if self._divs.pop() and self._containers:
                name, start = self._containers.pop()
                self.spans.append((name, start, len(self.blocks)))
            return
        if tag in self.LINE_TAGS:
            self._line_close()

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)
        elif self._line is not None:
            self._line.append(data)
        if self._strong is not None:
            self._strong.append(data)


class HtmlDocument:
    """Un documento HTML leído por su estructura: encabezados, tramos y tablas.

    Es la mitad que no depende de qué delimita una entrada. La página de una banda
    publica sus listas como encabezados con sus tablas debajo, y leerlas por
    estructura —en vez de por expresiones regulares sobre el HTML— es lo que hace
    que una fila con etiquetas dentro, una celda con entidades o un encabezado con
    enlaces no se pierdan ni se atribuyan a la tabla vecina.
    """

    def __init__(self, source: str, container_classes: Sequence[str] = ()) -> None:
        structure = _Structure(container_classes)
        structure.feed(source)
        structure.close()
        self.blocks = structure.blocks
        self.spans = structure.spans
        self.headings = [Heading(block.level, block.text, index)
                         for index, block in enumerate(self.blocks)
                         if block.kind == "heading"]

    def span(self, index: int) -> tuple[int, int]:
        """Tramo de bloques de un encabezado: el suyo y el de sus descendientes."""
        heading = self.headings[index]
        end = len(self.blocks)
        for following in self.headings[index + 1:]:
            if following.level <= heading.level:
                end = following.index
                break
        return heading.index, end

    def text(self, start: int = 0, end: int | None = None) -> str:
        """Texto de un tramo de bloques, en orden."""
        return prose(" ".join(block.text for block in self.blocks[start:end]))

    def rows(self, start: int = 0, end: int | None = None) -> list[Row]:
        """Filas de tabla de un tramo de bloques, en orden, con sus celdas."""
        return [Row(block.cells, index, block.header, block.table)
                for index, block in enumerate(self.blocks[start:end], start)
                if block.kind == "row" and any(cell.strip() for cell in block.cells)]

    def heading_span_of(self, level: int, text: str) -> tuple[int, int] | None:
        """Tramo del primer encabezado de ese nivel que dice eso (comparado sin
        mayúsculas ni puntuación), o ``None``."""
        wanted = normalized_key(text)
        for index, heading in enumerate(self.headings):
            if heading.level == level and normalized_key(heading.text) == wanted:
                return self.span(index)
        return None

    def containers(self, name: str) -> list[tuple[int, int]]:
        """Tramos de los contenedores de esa clase, en orden."""
        return [(start, end) for value, start, end in self.spans if value == name]


# Las nueve columnas de una tabla de características, en el orden en que la tabla
# las titula: es lo que la reconoce como tabla de características y no como una
# lista de equipo o una tabla de habilidades.
CHARACTERISTICS = ("m", "ws", "bs", "s", "t", "w", "i", "a", "ld")


def characteristic_columns(cells: Sequence[str]) -> tuple[int, ...] | None:
    """Las posiciones de las nueve columnas de características de un encabezado.

    Una tabla de características titula sus columnas con el nombre de cada una; la
    primera puede titular la tabla en vez de una característica («Profile»,
    «Race») y una columna que el catálogo no modela («Save») se reconoce por su
    título y queda fuera de la fila. Por eso la tabla se reconoce por los títulos
    —las nueve características **en su orden**— y no por las celdas de su primera
    fila: lo que la tabla imprime bajo «Ld» es Ld aunque lleve delante una columna
    que el catálogo no tenga.
    """
    titles = [normalized_key(cell) for cell in cells]
    at = [index for index, title in enumerate(titles) if title in CHARACTERISTICS]
    if [titles[index] for index in at] != list(CHARACTERISTICS):
        return None
    return tuple(at)


def profile_row(header: Sequence[str],
                cells: Sequence[str]) -> tuple[str, tuple[str, ...]] | None:
    """El nombre y las nueve cifras de una fila de una tabla de características.

    La tabla imprime sus filas de dos formas: con el nombre del guerrero en su
    primera columna —la que la cabecera titula «Profile»—, o sin él, y entonces el
    nombre lo lleva el encabezado que titula la tabla («1 Halfling Elder»: la tabla
    que sigue a su prosa lleva las cifras y ningún nombre). Las celdas se alinean
    con las columnas que la cabecera titula, no con las primeras: una columna que
    el catálogo no modela no corre la fila.
    """
    at = characteristic_columns(header)
    if at is None:
        return None
    values = [cell_value(cell) for cell in cells]
    if len(values) == len(header):
        picked = [values[index] for index in at]
        return (values[0] if 0 not in at else ""), tuple(picked)
    if len(values) == len(at):
        return "", tuple(values)
    return None


# El guion de una característica que la fila no tiene, en cualquiera de sus formas
# («–», «—», «‒»), y el que la fuente imprime como signo menos.
DASHES = re.compile(r"[-\u2010-\u2015\u2212]")


def cell_value(text: str) -> str:
    """El texto de una celda de tabla, con el guion de la fuente unificado.

    Las páginas imprimen el guion largo y el corto —«–», «—», «-»— para la
    característica que la fila no tiene: un guion es un guion, y el cotejo lee los
    tres como el mismo.
    """
    return DASHES.sub("-", visible(text)).strip()


# La forma con la que una lista tasa una fila sin cifra: el precio de otra cosa
# («Gromril Weapon 3x the cost»), un reparto («1st free/2 gc») o la tarjeta que
# anuncia el coste. Es lo que distingue la fila de una lista de la de cualquier
# otra tabla del documento (una tabla de habilidades, una de conjuros).
COSTLIKE = re.compile(rf"(?:{CURRENCY})\b|(?:{FORMULA_BASE.pattern})|(?:{MULTIPLIER.pattern})"
                      r"|\bfree\b|\bcost\b", re.I)


def list_rows(document: HtmlDocument, start: int = 0, end: int | None = None
              ) -> list[tuple[str, str]]:
    """Las filas de las **listas** de un tramo del documento: nombre y tarifa.

    Una lista es una tabla cuyas filas llevan el nombre en una celda y la tarifa en
    la siguiente; la fila de encabezado no es un dato y la de una tabla de
    habilidades o de conjuros no trae tarifa, así que no es una fila de lista. Se
    lee de la tabla —la celda que la fuente imprime— y no del texto de la página,
    que es lo que hacía pasar por impreso un objeto porque su nombre apareciera en
    cualquier prosa.
    """
    out: list[tuple[str, str]] = []
    for row in document.rows(start, end):
        cells = [cell_value(cell) for cell in row.cells]
        if row.header or len(cells) < 2 or not cells[0] or not cells[1]:
            continue
        if not COSTLIKE.search(cells[1]):
            continue
        out.append((cells[0], cells[1]))
    return out


def table_title(document: HtmlDocument, index: int) -> str:
    """El título que abre una tabla: el encabezado más cercano por encima, sin cupo.

    La página titula el perfil con el cupo delante («0 – 2 Snotling BigSnotz»,
    «1 Halfling Elder») y la tabla de algunas páginas no imprime el nombre en su
    fila: ahí el nombre del perfil es el del encabezado que lo titula.
    """
    heading = ""
    for sample in document.headings:
        if sample.index >= index:
            break
        heading = sample.text
    return profile_name(heading)


def profile_tables(document: HtmlDocument, start: int = 0, end: int | None = None
                   ) -> list[tuple[str, tuple[str, ...]]]:
    """(nombre, fila) de cada fila de las tablas de características del documento.

    Es la lectura por estructura de las tablas de perfil: la fila se lee de su
    tabla —una celda por columna— y no de una ventana de tokens de su texto, que
    mezcla la fila con la prosa del bloque vecino y pierde el nombre cuando la
    página lo imprime en el encabezado que titula la tabla.
    """
    out: list[tuple[str, tuple[str, ...]]] = []
    rows = document.rows(start, end)
    for index, row in enumerate(rows):
        if not row.header:
            continue
        for following in rows[index + 1:]:
            if following.header or following.table != row.table:
                break
            found = profile_row(row.cells, following.cells)
            if found is None:
                continue
            name, values = found
            out.append((profile_name(name) if name else table_title(document, row.index),
                        values))
    return out


class HtmlCorpus:
    """Entradas de una página web estructurada (una por ``div.fighter``)."""

    def __init__(self, path: Path, entry_class: str = "fighter") -> None:
        self.path = path
        document = HtmlDocument(path.read_text(encoding="utf-8", errors="replace"),
                                container_classes=(entry_class,))
        spans = document.containers(entry_class)
        self._entries = [
            entry_of(next((block.text for block in document.blocks[start:end]
                           if block.kind == "heading"), ""),
                     document.blocks[start:end], last=index == len(spans) - 1)
            for index, (start, end) in enumerate(spans)
        ]

    def entries(self) -> list[dict]:
        return [dict(entry) for entry in self._entries]


class TextCorpus:
    """Entradas de un texto plano, separadas por el ancla que la fuente declara."""

    def __init__(self, path: Path, anchor=None) -> None:
        self.path = path
        self.anchor = anchor or (lambda text: bool(re.match(r"\s*Source\s*:", text)))
        lines = [{"text": raw.rstrip("\r\n"), "top": index, "left": 0, "words": []}
                 for index, raw in enumerate(
                     path.read_text(encoding="utf-8", errors="replace").splitlines())]
        self._lines = [line for line in lines if line["text"].strip()]
        self._entries = entries(self._lines, separator=self.anchor)

    def lines(self) -> list[dict]:
        return [dict(line) for line in self._lines]

    def entries(self) -> list[dict]:
        return [dict(entry) for entry in self._entries]


# --------------------------------------------------------------------------- #
# Comparación y cobertura
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Package:
    """Lo que el paquete declara de un personaje, listo para cotejar."""

    stats: str | None = None
    rating: int | None = None
    rules: tuple[str, ...] = ()
    fee: Fee | None = None
    upkeep: Fee | None = None


def _printed_text(printed: Sequence[tuple[int, str | None, int | None, str | None]]) -> str:
    """Las tarifas impresas como se leen, para el informe."""
    parts = []
    for amount, unit, upkeep, upkeep_unit in printed:
        text = f"{amount} {unit or 'sin divisa'}"
        if upkeep is not None:
            text += f" + {upkeep} {upkeep_unit or 'sin divisa'}"
        parts.append(text)
    return " / ".join(parts)


def _fee_text(fee: Fee | None, upkeep: Fee | None) -> str:
    if fee is None:
        return "ninguna"
    head = f"{fee.amount}{' ' + fee.unit if fee.unit else ''}"
    if upkeep is None:
        return head
    return f"{head} + {upkeep.amount}{' ' + upkeep.unit if upkeep.unit else ''}"


def _row_agrees(package_stats: str, row: str) -> bool:
    """Si una fila impresa es la del paquete.

    La fuente imprime una celda por característica y el catálogo guarda el mismo
    orden, así que la comparación natural es la fila entera: es lo que hace falta
    cuando una característica ocupa dos cifras (Ld 10, la del Aksho de 2A). Pero
    cuando dos columnas comparten línea física —el encabezado de la fila y la
    prosa de al lado— la lectura por geometría no puede separarlas y la fila
    impresa arrastra dígitos del vecino por el final (el Warrior-Priest de Sigmar
    sale como ``43333131831``: su fila y un ``3"`` de la prosa contigua). Por eso
    se acepta también el recorte de la fila impresa a la longitud que el paquete
    declara: un sobrante por el final no es del personaje.
    """
    package_row = digits_row(package_stats)
    if not package_row:
        return False
    candidates = {package_row, digits_row(package_stats, swap=True)}
    return row in candidates or row[:len(package_row)] in candidates


def _fee_agrees(package: Package, printed: tuple[int, str | None, int | None, str | None]) -> bool:
    """Si una tarifa impresa y la del paquete son el mismo precio en la misma divisa.

    Un lado que no nombra divisa no la contradice; un lado que la nombra distinta
    —la tarifa impresa en warp tokens guardada como coronas— sí: es el defecto que
    la pasada de adjudicación cerró.
    """
    amount, unit, upkeep, upkeep_unit = printed
    if package.fee is None or amount != package.fee.amount:
        return False
    if package.fee.unit and unit and package.fee.unit != unit:
        return False
    if package.upkeep is not None and upkeep is not None:
        if package.upkeep.amount != upkeep or (package.upkeep.unit and upkeep_unit
                                               and package.upkeep.unit != upkeep_unit):
            return False
    return True


@dataclass
class Coverage:
    """Lo comparado y lo hallado de un personaje, chequeo a chequeo.

    ``verified`` es lo que se comparó y coincidió; ``failed`` lo que se comparó y
    no, por chequeo; ``notes`` lo que no pudo compararse, con su razón. La
    cobertura cuenta los tres: un perfil con la tarifa ilegible baja la cobertura
    de ``fee`` en vez de pasar por buena.
    """

    verified: set[str] = field(default_factory=set)
    failed: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def block(self) -> None:
        self.verified.add("block")

    def ok(self, check: str) -> None:
        self.verified.add(check)

    def fail(self, check: str, message: str) -> None:
        self.failed.setdefault(check, []).append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def report(self) -> dict:
        return {"checks": [check for check in CHECKS if check in self.verified],
                "findings": [message for check in CHECKS
                             for message in self.failed.get(check, [])],
                "notes": list(self.notes)}


def merge(coverages: Sequence[Coverage]) -> Coverage:
    """Combina el cotejo de varias fuentes de un mismo personaje.

    El paquete tiene que coincidir con **cada** fuente que imprime el dato: el
    chequeo se da por verificado sólo si todas lo verifican, un desacuerdo es un
    hallazgo, y lo que no pudo compararse queda como nota. Con una sola entrada
    —el caso de todos los perfiles de hoy— es la identidad.
    """
    out = Coverage()
    for check in CHECKS:
        if coverages and all(check in cov.verified for cov in coverages):
            out.ok(check)
        for cov in coverages:
            for message in cov.failed.get(check, []):
                out.fail(check, message)
    for cov in coverages:
        out.notes.extend(cov.notes)
    out.notes = list(dict.fromkeys(out.notes))
    return out


def compare(entry: dict, package: Package, coverage: Coverage,
            editorial: Mapping[str, str] | None = None) -> None:
    """Coteja una entrada impresa con lo que el paquete declara.

    Cada chequeo tiene tres salidas y no dos: coinciden, discrepan, o no se pueden
    comparar. La tercera se anota con su razón en vez de contarse como verde —es
    el «0 hallazgos» que no era «0 comprobado»— y sólo la segunda es un hallazgo.
    """
    coverage.block()

    printed = fees_in(entry["text"])
    if printed:
        if package.fee is None:
            coverage.note(f"la fuente imprime la tarifa {_printed_text(printed)} y el "
                          f"paquete no declara ninguna")
        elif any(_fee_agrees(package, candidate) for candidate in printed):
            coverage.ok("fee")
        else:
            coverage.fail("fee", f"tarifa impresa {_printed_text(printed)} vs paquete "
                                 f"{_fee_text(package.fee, package.upkeep)}")
    elif package.fee is None:
        coverage.ok("fee")
    else:
        coverage.note(f"la fuente no imprime tarifa; el paquete declara "
                      f"{_fee_text(package.fee, package.upkeep)}")

    rows = stat_rows(entry)
    if package.stats:
        if rows:
            if any(_row_agrees(package.stats, row) for row in rows):
                coverage.ok("stats")
            else:
                coverage.fail("stats", f"stats impresas {rows} vs paquete {package.stats}")
        else:
            coverage.note("la fuente imprime la tabla y no se pudo leer su fila")
    elif rows:
        coverage.note(f"la fuente imprime la fila {rows} y el paquete no declara "
                      f"características")
    else:
        coverage.note("ni la fuente ni el paquete declaran características")

    printed_rates = ratings_in(entry["text"])
    if printed_rates and package.rating is not None:
        if int(package.rating) in printed_rates:
            coverage.ok("rating")
        else:
            coverage.fail("rating", f"rating impreso {printed_rates} vs paquete {package.rating}")
    elif printed_rates:
        coverage.note(f"la fuente imprime el rating {printed_rates} y el paquete no "
                      f"declara ninguno")
    elif package.rating is not None:
        coverage.note(f"la fuente no imprime rating; el paquete declara {package.rating}")
    else:
        coverage.ok("rating")

    text = normalized_key(entry["text"] + " " + entry.get("spillover", ""))
    missing = []
    for name in package.rules:
        if editorial and name in editorial:
            coverage.note(f"etiqueta editorial '{name}': {editorial[name]}")
            continue
        terms = rule_terms(name)
        if terms and not all(term.lower() in text for term in terms):
            missing.append(name)
    if missing:
        for name in missing:
            coverage.fail("rules", f"regla '{name}' no aparece")
    else:
        coverage.ok("rules")


@dataclass
class Measure:
    """Lo comparado de un chequeo a lo largo de un cotejo.

    ``units`` cuenta las unidades que cubrió (bandas, ficheros) y ``values`` los
    valores que comparó dentro de ellas (filas de tabla, precios, etiquetas);
    ``failed`` los que no coincidieron, ``unobtainable`` los que no pudo comparar y
    ``details`` los conteos que explican cómo (cuántas listas se publican bajo un
    ``h2``, por ejemplo).
    """

    unit_label: str = "unidades"
    value_label: str = "valores"
    units: int = 0
    values: int = 0
    failed: int = 0
    unobtainable: int = 0
    details: dict[str, int] = field(default_factory=dict)

    def line(self, check: str) -> str:
        text = f"{check} {self.values - self.failed}/{self.values} {self.value_label}"
        if self.units:
            text += f" en {self.units} {self.unit_label}"
        if self.unobtainable:
            text += f" ({self.unobtainable} sin comparar)"
        if self.details:
            text += " " + " ".join(f"[{key}: {value}]" for key, value in self.details.items())
        return text


class Ledger:
    """Cobertura por chequeo de un cotejo que recorre muchas unidades.

    Es el hermano agregado de ``Coverage``: aquél cuenta un personaje, éste un
    cotejo entero (las 19 bandas, los 30 Dramatis). ``count`` suma un valor
    comparado diciendo si coincidió, ``cover`` una unidad en la que el chequeo se
    pudo aplicar, ``unobtainable`` lo que no se pudo comparar y ``detail`` los
    conteos que explican cómo. La línea que imprime dice las tres cantidades,
    porque un «0 hallazgos» sin valores comparados no es un «0 comprobado».
    """

    def __init__(self, checks: Mapping[str, tuple[str, str]] | None = None) -> None:
        self.measures: dict[str, Measure] = {}
        for check, (unit_label, value_label) in (checks or {}).items():
            self.label(check, unit_label, value_label)

    def label(self, check: str, unit_label: str = "unidades",
              value_label: str = "valores") -> Measure:
        measure = self.measures.setdefault(check, Measure())
        measure.unit_label, measure.value_label = unit_label, value_label
        return measure

    def cover(self, check: str, units: int = 1) -> None:
        self.measures[check].units += units

    def count(self, check: str, ok: bool = True, values: int = 1) -> None:
        measure = self.measures[check]
        measure.values += values
        if not ok:
            measure.failed += values
        return None

    def unobtainable(self, check: str, values: int = 1) -> None:
        self.measures[check].unobtainable += values

    def detail(self, check: str, key: str, amount: int = 1) -> None:
        measure = self.measures[check]
        measure.details[key] = measure.details.get(key, 0) + amount

    def reset(self) -> None:
        for measure in self.measures.values():
            measure.units = measure.values = 0
            measure.failed = measure.unobtainable = 0
            measure.details.clear()

    def line(self) -> str:
        return "cobertura por chequeo: " + ", ".join(
            measure.line(check) for check, measure in self.measures.items())

    def print(self) -> None:
        print(self.line())


def print_report(rows: Sequence[dict], label: str) -> None:
    """La cobertura por chequeo y los hallazgos de un cotejo."""
    comparable = [row for row in rows if row.get("comparable")]
    counts = {check: sum(1 for row in comparable if check in row["checks"]) for check in CHECKS}
    print(f"{label}: {len(rows)} ({len(comparable)} con entrada impresa comparable, "
          f"{len(rows) - len(comparable)} sin entrada)")
    print("cobertura por chequeo: " + ", ".join(f"{check} {counts[check]}/{len(comparable)}"
                                                for check in CHECKS))
    print(f"con hallazgos: {sum(1 for row in rows if row['findings'])}")
    for row in rows:
        if not row["findings"]:
            continue
        print(f"  {row['name']}:")
        for finding in row["findings"]:
            print(f"    - {finding}")
    for row in comparable:
        missing = sorted({"fee", "stats", "rating"} - set(row["checks"]))
        if missing and not row["findings"]:
            detail = f" — {'; '.join(row['notes'])}" if row["notes"] else ""
            print(f"  {row['name']}: sin comparar {missing}{detail}")
    # Los perfiles sin entrada impresa comparable comparten casi siempre la razón
    # —la página no está cacheada, el perfil sólo vive en las listas—, así que se
    # agrupan en vez de repetir una línea por perfil.
    groups: dict[str, list[str]] = {}
    for row in rows:
        if row.get("comparable"):
            continue
        reason = "; ".join(row["notes"]) or "sin fuente que cotejar"
        groups.setdefault(reason, []).append(row["name"])
    for reason, names in groups.items():
        listed = ", ".join(sorted(names)[:3])
        if len(names) > 3:
            listed += f" y {len(names) - 3} más"
        print(f"  sin entrada impresa ({len(names)}): {listed} — {reason}")


def write_report(rows: Sequence[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(rows), indent=1, ensure_ascii=False), encoding="utf-8")
