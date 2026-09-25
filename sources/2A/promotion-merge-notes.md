# Notas de fusión de 2A

Lo que exige `sources/2A/README.md` §5.3: una banda de 2A puede referenciar el `item_id`
**provisional** que ya existe en `sources/2B/catalog/items/`, y la promoción debe
materializar **una sola** entrada en la KB con todos sus `source_refs` en vez de duplicar
el objeto.

Estado: borrador de la fase de staging. La decisión de identidad la toma T04; aquí solo se
registra la correspondencia y la evidencia de dónde se leyó.

Revisión de esta anotación: 2026-09-25, rama `2A2B`, HEAD `a31bd8d`. Origen: inventario de
T01 y el cotejo por página de T02 (`docs/knowledge/2a2b/tasks/T01.md`, `.../T02.md`).

## 1. Objetos que 2A referencia y que solo existen como provisionales en 2B

Ninguno de los tres existe en `sources/knowledge/catalog/items/`, así que la promoción los
crea **una sola vez**, con los `source_refs` de las dos ramas en la misma entrada.

| `item_id` | Definición provisional (2B) | ¿En la KB activa? | Referencias en 2A | Acción en la promoción |
|---|---|---|---|---|
| `katana` | `sources/2B/catalog/items/sar-sartosa-gear.yaml` (Katana) | No | `nipponese-expedition-web`: `nippon-warrior-equipment-list`, `nippon-noble-equipment-list`, `shinobi-equipment-list`, `monk-equipment-list` — 20 gc en las cuatro | Una entrada con los `source_refs` de SAR y de la expedición Nipponese |
| `shovel` | `sources/2B/catalog/items/hireling-gear.yaml` (Shovel) | No | `grave-robbers-sylv`: `hero-equipment-list`, `henchmen-equipment-list` — 10 gc, «Counts as a Halberd» | Ídem |
| `warplock_pistol` | `sources/2B/catalog/items/mim-special-equipment-a.yaml` (Warplock Pistol) | No | `skaven-of-clan-moulder-web`: `heroes-equipment-list` — 35 wt (70 el par) | Ídem. Ojo: 2A lo tarifa en **warp tokens** y 2B en coronas; el mercado debe conservar cada contexto y no convertir una divisa en la otra |

El precio particular de cada lista se queda en `equipment-access.yaml` de su banda; el
`trading-post-2a.yaml` lleva una entrada por objeto (35 objetos, 1:1), generada por el
normalizador. La promoción del objeto no debe llevarse consigo el descuento local.

## 2. Objetos de 2A con el mismo nombre que uno de la KB y distinto `item_id`

| `item_id` (2A) | Nombre en 2A | `item_id` en la KB | Estado |
|---|---|---|---|
| `society_familiar` | Familiar | `familiar` | **Sin resolver**: mismo nombre, id distinto. T04 decide entre reusar el id canónico o declarar variante independiente, comparando mecánica y procedencia (los objetos de la KB viven en otro contexto de banda) |
| `repeater_pistol_moh` | Repeater Pistol (Masters of Horror) | `repeater_pistol` | El sufijo `_moh` parece deliberado (variante de la banda); T04 confirma que la KB conserva las dos entradas y que ninguna sustituye a la otra |

`horsemans_hammer` y `hunting_arrows` de 2B también comparten id con la KB, pero eso lo
declara `sources/2B/catalog/promotion-merge-notes.md` y no afecta a 2A.

## 3. Colisiones

Ningún `item_id` de los 35 objetos provisionales de 2A coincide con un `item_id` de la KB
(0 colisiones) ni con un `item_id` de 2B, salvo los tres objetos de §1. Las colisiones de
*identidad de banda* frente a la KB y frente a 2B son cero: los 19 ids de banda de 2A no
existen en `sources/knowledge/bands/mordheim/` ni en `sources/2B/bands/mordheim/`.
