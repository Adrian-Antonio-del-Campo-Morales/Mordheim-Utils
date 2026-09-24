"""Las palabras con que una fuente imprime el nombre de un objeto del catálogo.

La KB tiene un id canónico por objeto y el staging lo usa aunque la fuente escriba el
nombre a su manera («Double-handed weapon» → `great_weapon`), de modo que los **tres**
cotejos que comparan objetos contra una fuente —`audit_2a_sources.py`,
`audit_2b.py` y `audit_2ab_fidelity.py`— necesitan las mismas parejas. Estaban
triplicadas: cada auditor llevaba su tabla, y una pareja adjudicada en una se quedaba
sin ver en las otras (el cotejo de fidelidad declaraba huecos —objetos sin fila— que los
otros dos ya tenían adjudicados como la palabra de la fuente). Aquí hay un solo
registro, con el **sitio** donde se leyó cada palabra, y cada cotejo pregunta lo que
sabe:

- la fila de una lista —`words_at(tree, band, list_id, item_id)`—, que es lo que coteja
  el auditor de 2A por su lista impresa y el de 2B por su banda;
- todas las palabras registradas para un objeto en un árbol
  —`words_for_item(item_id, tree)`—, que es lo que necesita el cotejo de fidelidad,
  porque recorre objetos de los dos árboles y no una fila concreta;
- el motivo con que una lista se resuelve **delegada** al reglamento
  —`delegated_reason(tree, band, list_id)`—, que comparten el auditor de 2B (no imprime
  el precio) y el de fidelidad (no imprime la fila).

Un campo en blanco vale para cualquiera: la pareja del arma a dos manos no lleva árbol
ni banda porque la imprimen el reglamento y los suplementos de los dos. Una palabra
registrada en un árbol no vale en el otro: «Halbard» es la errata de la lista de los
Forest Goblins, no la palabra con que la página de 2A imprime el `halberd`.

El registro **no renombra nada**: el id y el nombre del KB se quedan como están y la
palabra impresa queda aquí. La adjudicación de cada pareja, con la fila verbatim y su
tarifa, está en `sources/2A/discrepancy-verdicts.md` §9 y `sources/2B/discrepancy-verdicts.md`
§7 y §15.4.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Wording:
    """Una pareja objeto ↔ palabra impresa, con el sitio donde se leyó.

    ``tree``, ``band`` y ``list_id`` en blanco valen para cualquiera: el árbol (2A/2B),
    cualquier banda del árbol y cualquier lista de la banda.
    """
    item_id: str
    words: tuple[str, ...]
    tree: str = ''
    band: str = ''
    list_id: str = ''
    note: str = ''


WORDINGS: tuple[Wording, ...] = (
    Wording('great_weapon', ('double-handed weapon', 'double handed weapon',
                             'two-handed weapon'),
            note='el reglamento y los suplementos lo imprimen así en los dos árboles'),
    # 2A: las palabras que la página imprime para un objeto del catálogo.
    Wording('blessed_water', ('Holy Water',), tree='2A',
            band='protectorate-of-sigmar-lotd3', list_id='protectorate-equipment-list',
            note='la KB lo llama «Blessed Water»; el capítulo de Miracle Workers '
                 'imprime «Blessed water»'),
    Wording('blessed_water', ('Holy Water',), tree='2A',
            band='vampire-hunters-of-sylvania-lotd5',
            list_id='vampire-hunters-hero-equipment-list'),
    Wording('sigmarite_hammer', ('Sigmarite Warhammer',), tree='2A',
            band='protectorate-of-sigmar-lotd3', list_id='protectorate-equipment-list',
            note='la KB lo llama «Sigmarite Hammer»'),
    Wording('long_bow', ('Long Bow Heroes only',), tree='2A',
            band='outlaws-of-stirwood-forest-redux-fbg', list_id='outlaws-equipment-list',
            note='la página funde la disponibilidad en la celda del nombre'),
    # 2B: ídem, y la lista que la fuente delega al reglamento en vez de imprimirla.
    Wording('halberd', ('Halbard',), tree='2B', band='forest-goblins-lus',
            note='errata de la fuente'),
    Wording('warhound', ('Wardog',), tree='2B', band='bretonnian-knights-errant-mou',
            note='el KB llama «Warhound» al objeto que la página imprime «Wardog»'),
    Wording('two_handed_weapon', ('Double-handed weapon',), tree='2B', band='channel-rats-mim'),
    Wording('horsemans_hammer', ('Horsemens Hammer',), tree='2B',
            band='knights-of-the-bitter-moors-mim'),
    Wording('toughened_leathers', ('Toughened leather',), tree='2B', band='silent-brotherhood-sc'),
    Wording('rope_hook', ('Rope and Hook',), tree='2B', band='guild-of-disgraced-engineers-mim'),
    Wording('superior_blackpowder', ('Superiour Black Powder',), tree='2B',
            band='guild-of-disgraced-engineers-mim', note='errata de la fuente'),
    Wording('ball_chain', ('Ball and Chain',), tree='2B', band='underworld-alliance-mim'),
    Wording('plague_censer', ('Plague Censor',), tree='2B',
            band='skaven-of-clan-pestilens-lus',
            note='la fuente imprime «Censor» (sic) en las dos páginas'),
    Wording('plague_censer', ('Plague Censor',), tree='2B',
            band='skaven-of-clan-pestilens-mou'),
    Wording('jezzail', ('Jezzail',), tree='2B', band='skaven-of-clan-skryre-kaz',
            note='la fuente imprime «Jezzail 175GC»'),
    Wording('warp_pistol', ('Warplock Pistol',), tree='2B',
            band='skaven-of-clan-pestilens-lus',
            note='el KB empareja los dos nombres en el mercado '
                 '(campaign.trading-post.warplock-pistol)'),
)

# Las listas que un documento resuelve **por delegación**: la fuente no imprime sus
# filas, remite al reglamento, y el cotejo las verifica contra la lista del reglamento
# que la KB transcribe con el mismo id. Key: (árbol, banda, lista) → el motivo.
_KAZ_SKAVEN = ("KAZ prints no Skaven list: 'All of the equipment lists from the rulebook "
               "apply'. The rows come from the rulebook list the KB transcribes as "
               "`skaven-clan-eshin` · `skaven-hero-equipment-list`.")

DELEGATED_LISTS: dict[tuple[str, str, str], str] = {
    ('2B', 'skaven-of-clan-mors-kaz', 'skaven-hero-equipment-list'): _KAZ_SKAVEN,
    ('2B', 'skaven-of-clan-skryre-kaz', 'skaven-hero-equipment-list'): _KAZ_SKAVEN,
    ('2B', 'dwarf-guildsmen-kaz', 'thunderer-equipment-list'):
        "KAZ references the list by name ('Dwarf Thunderers may be equipped with weapons "
        "and armour from the Dwarf Thunderers equipment list') but prints no handgun "
        "price; the rulebook list of the same id carries it.",
}


def _covers(entry: Wording, tree: str, band: str, list_id: str) -> bool:
    """¿Vale esta pareja para esa consulta?

    El árbol o la banda en blanco **en la pareja** valen para cualquiera; la lista en
    blanco **en la consulta** pregunta por cualquiera de las listas de esa banda, que es
    lo que sabe el auditor de 2B (su tabla siempre fue por banda).
    """
    if entry.tree not in ('', tree) or entry.band not in ('', band):
        return False
    return not list_id or entry.list_id in ('', list_id)


def words_at(tree: str, band: str, list_id: str, item_id: str) -> tuple[str, ...]:
    """Las palabras que la fuente imprime para ese objeto en esa fila, en su orden."""
    out: list[str] = []
    for entry in WORDINGS:
        if entry.item_id != item_id or not _covers(entry, tree, band, list_id):
            continue
        out += [word for word in entry.words if word not in out]
    return tuple(out)


def pairs_at(tree: str, band: str, list_id: str = '') -> tuple[Wording, ...]:
    """Las parejas registradas para esa banda: sus listas y las de cualquier lista."""
    return tuple(entry for entry in WORDINGS if _covers(entry, tree, band, list_id))


def words_for_item(item_id: str, tree: str) -> tuple[str, ...]:
    """Todas las palabras registradas para el objeto en ese árbol, en su orden."""
    out: list[str] = []
    for entry in WORDINGS:
        if entry.item_id != item_id or entry.tree not in ('', tree):
            continue
        out += [word for word in entry.words if word not in out]
    return tuple(out)


def delegated_reason(tree: str, band: str, list_id: str) -> str | None:
    """El motivo con que esa lista se resuelve delegada al reglamento, o None."""
    return DELEGATED_LISTS.get((tree, band, list_id))
