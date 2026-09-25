# Notas de fusión de 2A — decisiones de identidad de T04

Lo que exige `sources/2A/README.md` §5.3: una banda de 2A puede referenciar el `item_id`
**provisional** que ya existe en `sources/2B/catalog/items/`, y la promoción debe
materializar **una sola** entrada en la KB con todos sus `source_refs` en vez de duplicar
el objeto.

Estado: **decisiones tomadas por T04** el 2026-09-25 (rama `2A2B`, HEAD `b2e437c`). El
documento nació como borrador de la fase de staging; ese borrador queda sustituido por las
decisiones de abajo, que conservan su evidencia. Revisión de la anotación previa:
2026-09-25, HEAD `a31bd8d`, origen: inventario de T01 y cotejo por página de T02.

Regla aplicada en todas las decisiones: una coincidencia de nombre **no** demuestra
identidad; se conservan variantes separadas cuando cambian características, efectos,
destinatarios o procedencia. La evidencia de cada decisión va con su comando, para que T05
pueda reproducirla.

## 1. Objetos que 2A referencia y que solo existen como provisionales en 2B

Decisión T04: **alta única compartida**. Ninguno de los tres existe en
`sources/knowledge/catalog/items/`, así que la promoción los crea **una sola vez**, con los
`source_refs` de las dos ramas en la misma entrada. El precio particular de cada lista se
queda en el `equipment-access.yaml` de su banda; el `trading-post-2a.yaml` **no** lleva
entrada para ellos (sus 35 entradas son 1:1 con los 35 objetos propios de 2A), así que la
divisa local nunca se sustituye por el mercado global.

| `item_id` | Definición provisional (2B) | ¿En la KB activa? | Referencias en 2A (7 filas) | Precio impreso en la banda | Acción en la promoción |
|---|---|---|---|---|---|
| `katana` | `sources/2B/catalog/items/sar-sartosa-gear.yaml` (Katana) | No | `nipponese-expedition-web`: `nippon-warrior-equipment-list`, `nippon-noble-equipment-list`, `shinobi-equipment-list`, `monk-equipment-list` | 20 gc en las cuatro | Una entrada con los `source_refs` de SAR y de la expedición Nipponese |
| `shovel` | `sources/2B/catalog/items/hireling-gear.yaml` (Shovel) | No | `grave-robbers-sylv`: `hero-equipment-list`, `henchmen-equipment-list` | 10 gc, «Counts as a Halberd» | Ídem, con la nota de la banda intacta |
| `warplock_pistol` | `sources/2B/catalog/items/mim-special-equipment-a.yaml` (Warplock Pistol) | No | `skaven-of-clan-moulder-web`: `heroes-equipment-list` | **35 wt (70 el par)** | Ídem. 2A lo tarifa en **warp tokens** y 2B en coronas: cada contexto conserva su divisa y no se convierte una en la otra |

Verificación (7 filas, 0 de más): `grep -rn "katana\|shovel\|warplock_pistol" sources/2A/bands/`.

## 2. Identidades decididas

### 2.1 `society_familiar` (2A) frente a la KB `familiar` — **variante independiente**

| Campo | 2A `society_familiar` | KB `familiar` |
|---|---|---|
| Nombre | Familiar | Familiar |
| Archivo | `sources/2A/catalog/items/sorcerous-society-equipment.yaml` | `sources/knowledge/catalog/items/trollheim.yaml` |
| Procedencia | `mordheimer.net` · Sorcerous Society · *Special Equipment / Familiar* | `khemri` p. 59 · Mage Equipment List |
| Mecánica | Criatura acompañante con **cuatro perfiles** (Perro M6 HA4 F3 R3 H1 I4 A1 Ld5; Gato; Cuervo; Víbora) y reglas propias (Leal, Olfateo, ¡A los Ojos!, Volar, ¡Te Veo!, Veneno, En guardia). Se compra, tira heridas como un Secuaz, no cuenta para tamaño máximo ni Huida | **No** se compra como equipo: el coste paga el ritual de invocación; solo usuarios de conjuros pueden intentarlo; permite repetir una tirada de lanzamiento fallida por turno |

El borrador dejaba la decisión abierta. **Decisión: conservar las dos.** El texto, la
mecánica y los destinatarios son distintos (compañero con perfil de combate frente a mejora
de lanzamiento no comprable), y la KB no modela perfiles de familiar. La entrada de 2A no se
fusiona con la de la KB ni la sustituye.

Hallazgo añadido de T04 (barrido de nombres, no estaba en el borrador): la KB guarda **dos**
ids para el familiar ritual — `familiar` (khemri) y `arcane_familiar` (chaos-in-the-streets
p. 167, Arcane Society, texto paralelo) — y ninguno es el de 2A. Consolidar esos dos es
decisión de T07, no de T04. Ver §4.

### 2.2 `repeater_pistol_moh` (2A) frente a la KB `repeater_pistol` — **variante independiente**

| Campo | 2A `repeater_pistol_moh` | KB `repeater_pistol` |
|---|---|---|
| Nombre | Repeater Pistol (Masters of Horror) | Repeater Pistol |
| Procedencia | `sylvania-supplement` · Masters of Horror · *Special Equipment* | `mordheimer.net` · Gunnery School of Nuln · Marksman equipment list |
| Mecánica | Alcance **8"**, F4, −2 salvación, más **Too Much Tinkering** (tabla por disparo: 4+ funciona, 2-3 nada, 1 en la tabla de Fallo) y **Repeater** (hasta 3 disparos con −1 acumulativo) | Alcance **6"**, F4, −2 salvación. `combat_status: out_of_scope`, sin mecánica |

El propio texto impreso de 2A declara la diferencia («This is the Masters of Horror variant of
the trading-post Repeater Pistol; it has a longer range (8" instead of 6") and unique
tinkering and repeater mechanics»). **Decisión: conservar las dos**; el sufijo `_moh` es
deliberado y documenta el procedimiento. No se fusiona ni se re-punta ninguna banda.

### 2.3 `shield_of_sigmar` (2A) frente a la KB `sigmar_shield` — **variante independiente** (hallazgo nuevo de T04)

No estaba en el borrador: el barrido de nombres de T04 lo encontró porque los dos imprimen
las mismas palabras («Shield of Sigmar» / «Sigmar Shield»).

| Campo | 2A `shield_of_sigmar` | KB `sigmar_shield` |
|---|---|---|
| Procedencia | `mordheimer.net` · Protectorate of Sigmar · *Special Equipment / Shield of Sigmar* | `chaos-in-the-streets` pp. 152 · Devout / Warrior Equipment List |
| Mecánica | Escudo con aura: **6+ especial contra todo ataque a distancia** y sin el −1 por llevar escudo con Armadura Pesada; regla «Shield of Faith» | Escudo normal: salvación 6+, se combina con la armadura para +1 |

Los efectos son materialmente distintos (salvación especial contra disparo y exención de
penalización frente al escudo estándar), y la procedencia difiere. **Decisión: conservar las
dos**, sin colisión de id (los ids difieren). La coincidencia de **nombre ES** («Escudo de
Sigmar» en las dos) es un riesgo de presentación, no de datos: se declara en §5 para que el
propietario de traducción/presentación lo desambigüe.

## 3. Colisiones de id

- **0** `item_id` de los 35 objetos propios de 2A coinciden con un `item_id` de la KB.
- **0** `item_id` compartidos entre 2A y 2B.
- **0** `lore_id` de 2A existen en la KB y **0** `spell_id` de 2A existen ya en la KB o en 2B.
- **0** colisiones de identidad de banda: los 19 ids de banda de 2A no existen en
  `sources/knowledge/bands/mordheim/` ni en `sources/2B/bands/mordheim/`.
- **0** entradas de mercado compartidas: las 35 entradas de `trading-post-2a.yaml` son 1:1
  con los 35 objetos de 2A y ninguna coincide con una entrada de la KB.

Las únicas coincidencias son **de nombre**, y las tres están decididas en §2 (más las dos de
nombre ES de §5). Ninguna colisión queda silenciosa.

## 4. Inventario origen → destino de 2A (mapa para T05)

Evidencia: `build/cache/2ab-promotion-map.json` (generado por
`build/cache/2ab-t04-map.py`; helpers ignorados por git).

### Objetos (35)

- **33 altas** (id ausente de la KB activa; se promocionan como entradas nuevas):
  `darksteel_blade`, `whirling_blades`, `hooded_lantern_rig`, `pry_bar`, `surgeons_journal`,
  `finger_pendant`, `chainsaw_sword`, `electric_trident`, `bearcloak`, `beastwhip`,
  `thingcatcher`, `wolf_rat_mount`, `staff_of_damnation`, `unholy_relic`, `damned_book`,
  `kanabo`, `sashimono`, `horo`, `kusarigama`, `sharp_stuff`, `pigback_mount`,
  `shield_of_sigmar`, `blessed_bolts`, `small_pebble`, `slingshot`, `power_squig`,
  `wizards_staff`, `chest_talon`, `black_gold_wristbands`, `ring_of_strigos`, `cursed_book`,
  `silver_tip_stake`, `throat_guard`.
- **2 variantes conservadas** (coincidencia de nombre, id distinto, mecánica distinta):
  `society_familiar` (§2.1), `repeater_pistol_moh` (§2.2).
- **0 fusiones** y **0 re-direcciones** propias de 2A.

### Mercado (35 entradas en `catalog/trading-post-2a.yaml`)

1:1 con los 35 objetos, `id` `campaign.trading-post.<item>`; 0 entradas sin objeto y 0
objetos sin entrada. Precios particulares y divisas conservados verbatim; los objetos no
vendidos (`not_sold`) y los tarifados en warp tokens mantienen su prosa (`price: null` con la
nota de la fuente, como exige el contrato de mercado).

### Magia (12 lores, 69 conjuros)

Las 12 son **altas** y ningún `lore_id` ni `spell_id` colisiona con la KB ni con 2B:
`lore.dreaded-scrolls-of-nagash`(6), `lore.elemental-water`(6), `lore.elemental-fire`(6),
`lore.elemental-earth`(6), `lore.elemental-air`(6), `lore.funerary-rites-lotd5`(6),
`lore.snotling-waaagh-magic`(6), `lore.blessings-of-the-mare`(6), `lore.commands`(6),
`lore.woodland-incantations`(6), `lore.charms-and-hexes-strigos`(6),
`lore.dark-arts-strigos`(3).

Las dos que ya nacían como variantes declaradas se conservan como variantes:
`lore.funerary-rites-lotd5` (VARIANTE de la KB `lore.funerary-rites`; dificultades
3/5/6 distintas: Sanctity of the Fallen 5 vs 7, Do You Know Who I Am? 9 vs 7, I Am Death! 7
vs 8) y `lore.charms-and-hexes-strigos` (renombrada por `magic_promotion.LORE_RENAMES` desde
`lore.charms-and-hexes` para que no colisione con la lore de la KB). Ninguna se fusiona.

### Mercenarios

2A no aporta perfiles de mercenario propios: **0**.

## 5. Rulings que afectan a las bandas de 2A (para sus propietarios)

1. **Sin cambios de referencia en 2A.** Las 7 filas de §1 ya apuntan al id provisional
   correcto y el precio local sigue siendo el de la banda. T04 no pide ninguna edición de
   `sources/2A/bands/**`.
2. **Nombres ES duplicados entre objetos distintos** (riesgo de presentación, no de datos):
   «Familiar» en `society_familiar` y en la KB `familiar`/`arcane_familiar`; «Escudo de
   Sigmar» en `shield_of_sigmar` y en la KB `sigmar_shield`. El id no colisiona, así que no
   hay pérdida; desambiguar la cadena visible corresponde a traducción/presentación.
3. **Objetos 2A no vendidos** (`power_squig`, `wolf_rat_mount`, `pigback_mount`,
   `society_familiar`…): siguen `not_sold` en el mercado con la prosa de su fuente. No se
   convierten en comprables para «cerrar» la entrada.

## 6. Evidencia reproducible

```bash
PYTHONIOENCODING=utf-8 python build/cache/2ab-catalog-matrix.py   # matriz de catálogos 2A/2B vs KB
PYTHONIOENCODING=utf-8 python build/cache/2ab-collisions.py       # colisiones de id y de nombre
PYTHONIOENCODING=utf-8 python build/cache/2ab-t04-map.py          # mapa origen→destino (JSON)
python tools/knowledge/audit_staging_contract.py --tree 2A --tree 2B --json   # exit 0
```

Resultado de la matriz: KB 335 objetos / 335 entradas de mercado / 31 lores / 102
mercenarios; 2A 35 objetos y 35 entradas de mercado, con 0 colisiones de id en cualquier
familia.
