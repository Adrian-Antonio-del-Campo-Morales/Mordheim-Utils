# Veredictos sobre las discrepancias de fuente de la ingesta 2A

Formato y criterios heredados de `sources/2B/discrepancy-verdicts.md`: cada caso se
verifica contra el documento original citado por la fuente, no contra la transcripción
2A ni contra la KB activa.

## 1. Silver-tip Stake — LotD #5 "10 gc" (listas) vs "15 gc" (Special Equipment) → **FIEL A SU FUENTE; conflicto interno del original; resuelto por decisión editorial (2026-09-15)**

- Fuente primaria: página dedicada de mordheimer.net
  (`build/cache/2a-sources/pages/vampire-hunters-of-sylvania-lotd5.html`,
  texto en `build/cache/2a-sources/text/vampire-hunters-of-sylvania-lotd5.txt`).
  Los tres puntos de datos están verbatim:
  - Hero Equipment List: `Silver-tip Stake / 10 gc` (línea 69 del draft).
  - Pilgrim Equipment List: `Silver-tip Stake / 10 gc` (línea 108).
  - Special Equipment: `Silver-tip Stake / Cost: 15 gc / Availability: Common` (líneas 132–136).
- **PDF original de procedencia citado por la propia página:**
  `https://broheim.net/downloads/lod/LOD5.pdf#page=9` (By Tom Bell, PDF). Descargado a
  `build/cache/2a-sources/pdfs/LOD5.pdf` (19 páginas,
  sha256 `b302de59507bbea556b820e8ea84e47706328ea39f792060660764f109ce58d2`,
  no versionado en Git). El ancla de la página apunta a la página 9, pero las listas
  de equipo están en la **página 10 del PDF** (página impresa 9, índice 9).
- Verificación contra el PDF original (página 10, capa de texto nativa, sin OCR):
  el conflicto **se reproduce idéntico en el original**. La página imprime:
  - Hero list: `Silver-tip stake .................. 10 gc`
  - Pilgrim list: `Silver-tip stake .................. 10 gc`
  - Resumen de Special Equipment (columna de disponibilidad):
    `Silver-tip Stake  Common  15gc` — la extracción cuadruplica cada celda
    ("Silver Silver Silver Silver-- --tip Stake Common 15gc 15gc 15gc 15gc") y las
    cuatro repeticiones del precio leen **15gc** sin ambigüedad.
- **Veredicto:** el conflicto es un **erratum interno del propio documento original**
  (LotD #5 imprime dos precios para el mismo objeto en la misma página), no un error
  de extracción ni de transcripción. La transcripción 2A es fiel: ambos valores están
  registrados verbatim con notas SOURCE CONFLICT en
  `bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml` y en
  `catalog/items/vampire-hunter-equipment.yaml`.
- **Acción aplicada:** ninguna en los datos de transcripción (ambos valores se conservan
  registrados como impresos). **Decisión editorial aplicada (2026-09-15):** el coste
  operativo del objeto es **10 gc** (las listas de contratación, fuente de los perfiles
  que pueden comprarlo); la cifra **15 gc** del bloque Special Equipment se marca como
  **erratum** del original. Documentado en las notas de
  `equipment-access.yaml` y `catalog/items/vampire-hunter-equipment.yaml`.
- **Recomendación, hoy aplicada:** las **listas de contratación (10 gc)** son la cifra
  operativa — son las que usan los perfiles que pueden comprar el objeto (héroe y
  peregrino) — mientras que el bloque "Special Equipment" es un resumen descriptivo; el
  patrón coercitivo de las demás entradas del mismo bloque apoya la lectura de erratum
  (Scythe 10 gc y Throat Guard 10 gc coinciden con sus listas). Decisión tomada
  explícitamente por el usuario (2026-09-15): **10 gc operativo, 15 gc erratum**.

## 2. Re-verificación de precios contra las fuentes (2026-09-16) → **8 precios corregidos; 5 listas que nunca se habían cotejado entran en cobertura**

Aplicación a las 19 bandas de la misma re-verificación que se hizo para 2B
(`sources/2B/discrepancy-verdicts.md` §7), con dos extracciones por fuente,
consciencia de divisa, fórmulas y precios relativos, y cotejo de las listas de
equipo en las dos direcciones. Herramienta: `tools/ingestion/audit_2a_sources.py`
(sección 4 reescrita y sección 4b nueva).

### 2.1 Correcciones aplicadas (8 filas, 4 paquetes)

Todos los importes se leyeron de la tabla de la página (extracción 1) y de la
extracción plana `build/cache/2a-sources/text/` (extracción 2), y coinciden.

| Banda | Lista | Ítem | Antes | Ahora | Lo que imprime la fuente |
|---|---|---|---|---|---|
| `masters-of-horror-sylv` | `hero-equipment-list` | `chainsaw_sword` | `null` + nota | **`15+D6`** | lista: `Chainsaw Sword 15 + D6 gc` |
| `masters-of-horror-sylv` | `hero-equipment-list` | `electric_trident` | `null` + nota | **`15+D6`** | lista: `Electric Trident 15 + D6 gc` |
| `masters-of-horror-sylv` | `hero-equipment-list` | `repeater_pistol` | `null` + nota | **`25+3D6`** | lista: `Repeater Pistol 25 + 3D6 gc` |
| `necrarchs-the-soul-stealers-lotd1` | `necrarch-hero-equipment-list` | `damned_book` | `null` + nota | **`45+3D6`** | lista: `Damned Book 45 + 3D6 gc` |
| `sorcerous-society-lotd4` | `sorcerous-society-equipment-list` | `society_familiar` | `null` + nota | **`20`** | lista: `Familiar 20 gc`; bloque Special Equipment: `Cost: 20 + 2D6 gold crowns` |
| `survivors-of-strigos-sylv` | `hero-equipment-list` | `black_gold_wristbands` | `null` + nota | **`35`** | lista: `Black Gold Wristbands 35 gc`; bloque: `Cost: 35 + 2D6 gc` |
| `survivors-of-strigos-sylv` | `hero-equipment-list` | `ring_of_strigos` | `null` + nota | **`20`** | lista: `Ring of Strigos 20 gc`; bloque: `Cost: 20 + D6 gc` |
| `survivors-of-strigos-sylv` | `hero-equipment-list` | `cursed_book` | `null` + nota | **`50`** | lista: `Cursed Book 50 gc`; bloque: `Cost: 50 + 3D6 gc` |

**Criterio aplicado** (el que ya usa la KB, no uno nuevo):

* si **la propia lista imprime** una tirada, el precio se guarda como la expresión de
dados que el contrato editorial prescribe (`cost: 25+1D6`; precedente KB
`trollheim/lustria-pirates`: `pirate_flag cost: 40+2D6`);
* si la lista imprime una **cifra fija** y solo el bloque Special Equipment añade los
dados, manda la **cifra de la lista** (es la que se paga al crear la banda) y la
fórmula queda documentada en `notes`; el base del bloque coincide con la lista en los
tres casos, así que no hay conflicto, solo abreviatura. Es el patrón KB
`khemri-mages` (`familiar cost: 20`, nota «the detailed entry is Rare 8 and costs
20+1D6 gc»), `lustria-dark-elves` (`sea_dragon_cloak cost: 50`) y `lustria-high-elves`
(`elven_wine cost: 30`).
* un precio **relativo** («3x cost», «3 x price», «2 x price») sigue guardándose como
`null` con su redacción en `notes`: es la forma KB de `gromril_weapon`,
`ithilmar_weapon` y `dark_steel_weapon`.

Ninguna cifra se inventó: cada valor nuevo sale de la fila del listado de la página, y
cada nota de la fila quedó reescrita para decir de dónde sale (lista o bloque).

### 2.2 Listas que el auditor no cotejaba (5 listas, 73 filas)

El auditor solo miraba encabezados `h3` terminados en «equipment list». Siete páginas
publican alguna lista bajo un **`h2`** (Ogre Hunting Party, Outlaws, Sorcerous Society,
Protectorate of Sigmar; y los contenedores `h2` de Masters of Horror, Survivors of
Strigos, Clan Moulder, Vampire Hunters y Necrarchs, cuyos hijos `h3` sí se cotejaban).
Las cinco listas `h2` **nunca se habían verificado**:

| Banda | Lista | Filas en la página |
|---|---|---|
| `ogre-hunting-party-web` | `ogre-equipment-list` | 8 |
| `ogre-hunting-party-web` | `gnoblar-equipment-list` | 14 |
| `outlaws-of-stirwood-forest-redux-fbg` | `outlaws-equipment-list` | 15 |
| `sorcerous-society-lotd4` | `sorcerous-society-equipment-list` | 17 |
| `protectorate-of-sigmar-lotd3` | `protectorate-equipment-list` | 19 |

Las 73 filas se cotejaron contra la tabla de la página: **todas coinciden** (ninguna
corrección). El auditor ahora es *dirigido por la lista*: cada lista del paquete debe
tener su encabezado en la página, y una lista sin sección en la fuente se reporta
(`list-without-source`) en vez de omitirse en silencio. Un encabezado que solo abre
listas hijas (contenedor) no aporta filas propias; uno que tiene filas propias **y**
contiene una sublista (caso de Protectorate of Sigmar con Huntsman) sigue siendo lista.

### 2.3 Lo que tampoco se comparaba: divisa, fórmulas y precios relativos

* **Divisa.** Clan Moulder (Skaven) tarifa sus listas en **warp tokens** (`Dagger 1st
free/2 wt`, `Warplock Pistol 35 wt (70 for a brace)`). El antiguo `parse_cost` solo
entendía `N gc` y devolvía `None` para esas celdas, así que sus **23 filas nunca se
compararon**: ahora se comparan (coinciden todas) y el auditor conoce `gc`, `crowns` y
`wt`. La lista guarda la cifra impresa, sin convertir divisa.
* **Filas gratuitas.** Tres filas que la fuente imprime como `Free!` y el paquete guarda
como `cost: 0` se daban por no comparables; ahora se leen como importe 0.
* **Precios relativos.** `gromril_weapon` (×3 coste, 3 listas de `dwarf-slayer-cult-web`),
`ithilmar_weapon` (2 x precio, 2 listas de `wood-elves-of-athel-loren-web`) y
`darksteel_blade` (3 x base, `druchii-mic`) se aceptan como `null` **solo** cuando la
celda de la fuente dice un múltiplo; un `null` ante una cifra impresa se reporta.
* **Listas delegadas al reglamento: no hay ninguna en 2A.** Se buscaron las frases con
las que una página reenvía su lista al manual («use the equipment lists from the
rulebook», «as per the Mordheim rulebook») en las 19 páginas: ninguna lo hace. El hueco
equivalente en 2A era el de las listas `h2` de §2.2.

### 2.4 Precios del bloque Special Equipment (35 ítems, 34 cotejados)

Los precios de los objetos propios de cada banda viven en el catálogo provisional como
prosa (`availability_note`) y **ningún auditor los comparaba con la página**. Se añadió
la sección 4b: para cada ítem se lee el precio que imprime su sección y se compara con el
registrado; un precio que la lista de la banda lleva (y que ya se coteja en §2.2) cuenta
como verificado, y un ítem sin sección ni precio en lista se reporta.

Resultado: **34 de 35 coinciden**; el único caso que no es un error de dato es el
Silver-tip Stake (verdicto 1). `unholy_relic` no tiene sección propia en la página de los
Necrarchs y su precio (15 gc) lo lleva la Necrarch Henchmen Equipment List.

### 2.5 Convenciones de nombre adjudicadas (explícitas, nunca inferidas)

El cotejo fila↔ítem se hace por nombre del catálogo; cuando la página imprime otro
nombre, el par se declara en el registro compartido de palabras impresas
(`tools/ingestion/printed_wordings.py`, §9) y la fila se compara como cualquier otra
(nombre **y** precio del texto, sin sustituir la evidencia):

| Banda | Fila impresa | Ítem | Comprobación |
|---|---|---|---|
| `protectorate-of-sigmar-lotd3` | `Sigmarite Warhammer 15 gc*` | `sigmarite_hammer` | precio 15 ✓ |
| `protectorate-of-sigmar-lotd3` | `Holy Water 5 gc*` | `blessed_water` | precio 5 ✓ |
| `vampire-hunters-of-sylvania-lotd5` | `Holy Water 10 gc` | `blessed_water` | precio 10 ✓ (verdicto 1) |
| `outlaws-of-stirwood-forest-redux-fbg` | `Long Bow Heroes only 15 gc` | `long_bow` | precio 15 ✓ |

### 2.6 Cobertura y prueba negativa

Salida del auditor (2026-09-16):

```
sources/2A vs cached pages: 0 open finding(s), 13 adjudicated
equipment coverage: 47 list(s) matched (5 published under an h2); 558 printed row(s)
  compared (558 matching, 0 without a price cell); 0 list entr(y/ies) absent from the
  tables (0 of them confirmed by the flat-text extraction)
special-equipment coverage: 35 catalogue item(s) of the 19 bands, 34 with a price on
  the page compared against the recorded one; 3 profile row(s) printed inside those
  sections compared with the item text
```

La cobertura se imprime a propósito: «0 hallazgos» sin filas comparadas no es
evidencia. Y el auditor **falla de verdad**: `tests/knowledge/test_2a_source_audit.py`
(12 pruebas) inyecta un precio equivocado, una fila que el paquete pierde, un precio de
tirada aplanado a `null`, una lista renombrada sin encabezado en la página, un precio
de Special Equipment contradicho y un perfil de ítem borrado, y exige el hallazgo en
cada caso (más pruebas unitarias de `cost_cell_value`/`price_shape` y del reparto
contenedor/listas hijas).

## 3. Re-verificación de completitud (2026-09-16) → **1 dato ausente completado a mano; el resto confirmado contra las páginas**

Objetivo: no basta con que lo ingerido coincida con la fuente, hay que comprobar que **no
falte nada** de ella. Se revisó cada campo vacío del paquete 2A y cada dimensión que
ningún auditor cubría, contra las páginas cacheadas:

| Dimensión | Comprobación | Resultado |
|---|---|---|
| Cupos del roster (las 91 filas de las 19 bandas) | prosa de «Choice of Warriors» ↔ `roster.members[].minimum/maximum` | 19/19 coinciden; las 19 filas sin máximo son «any number of …» en la fuente (verificado una a una) |
| Tamaño de banda y oro inicial | «minimum of N models» / «maximum … never exceed N» / «you have 500 …» ↔ `roster.*` | 19/19 coinciden |
| Experiencia inicial de héroe | sección «Starting Experience» ↔ `profiles[].experience` | 19/19 coinciden (`halflings-mic` la imprime en línea, dentro de Choice of Warriors); ya lo cubría `audit_2a.py` |
| Rareza de los 35 ítems | «Rare N» de cada sección ↔ `rarity` | coinciden; `null` sólo donde la página no imprime número («Grave Robbers only», «Special», «Clan Moulder only») |
| Precios relativos | filas con `cost: null` | 6 filas (`3x cost`, `2 x price`, `3 x base weapon price`), todas relativas **en la fuente**: es la forma KB, no un hueco |
| Prosa de los 35 ítems | texto de cada sección ↔ `effect` + `special_rules` | 1 hueco real (§3.1); el resto, falsos positivos de un cotejo por palabras (la línea `Cost:`/`Availability:` y el pie de página de la web contaminaban la comparación) |
| Cifras guardadas | cada número del ítem ↔ su sección | sin cifras inventadas; el único aviso es la nota editorial del Silver-tip Stake (fechas y nº de caso, no datos de fuente) |

### 3.1 Hueco real: el perfil de la montura Pigback

La sección *Special Equipment / Pigback Mount* imprime su fila de atributos
(`M 5 WS 2 BS - S 2 T - W 1 I 3 A 1 Ld 5`, verificada en la tabla HTML, no sólo en el
texto plano) y el ítem se había ingerido con su prosa pero **sin la fila**. Era
invisible para todos los cotejos: `audit_2a.py` lee los bloques `div.fighter` de la
página (perfiles de guerrero) y las secciones de Special Equipment son prosa, y los
cotejos de contenido comparan prosa, no dígitos.

Completado a mano (EN + ES), con la misma forma que usa el ítem hermano de 2B
(`wolf_rat_mount`) y el Familiar de la Society of Sorcery:

```yaml
effect: >-
  A gnoblar hero may ride a luckless gnoblar, who is forced to carry them piggyback.
  Profile: M5 WS2 BS- S2 T- W1 I3 A1 Ld5.
```

Los otros dos ítems con fila de perfil en su sección (`wolf_rat_mount`, `society_familiar`
con sus cuatro animales) ya la tenían completa.

### 3.2 Huecos reales: tres aclaraciones condensadas en la prosa de reglas

La KB conserva las aclaraciones entre paréntesis de la prosa de reglas
(`(i.e. …)`, `(thus, …)`, `(no save allowed)`) y descarta los ejemplos resueltos
(`(Example: …)`, `(ex. …)`, `(e.g. …)`: **ningún** fichero de la KB, 2A o 2B lleva
uno). Tres aclaraciones se habían condensado fuera del paquete, y ninguna comprobación
lo veía porque de las reglas sólo se cotejaba el **nombre** contra la página:

| Banda / regla | Texto que faltaba |
|---|---|
| `snotlings-web` / `bullied-goblin--stampede` | «(do not count additional hand attacks)», «(i.e. you may have multiple Snotlings each forfeit their attack, each adding +1 S for each attack)» y «(thus, if you have two Stampeding Heroes, you cannot have one Snotling runt forfeit his attack TWICE…)» |
| `dwarf-slayer-cult-web` / `rememberer--record-of-valor` | «(as they are saved from the jaws of death)» y la aclaración del `i.e.` de Back-up Records («1 Slayer taken OOA gives you a max of 1 exploration die, even if both the Rememberer and the Bard witness it») |
| `dwarf-slayer-cult-web` / `band--slayer-skills` | el matiz impreso de Monster Slayer («after all modifiers due to weapon bonuses, etc» → se había escrito «after all weapon modifiers») |

Restauradas en EN y ES con la redacción impresa (el ejemplo resuelto de Stampede sigue
fuera, por la convención anterior). Barrido completo: se compararon **todas** las
aclaraciones entre paréntesis de las secciones de reglas de las 19 páginas; las demás
(o son ejemplos, o son restricciones de encabezado como `(Leaders only)`, o su prosa
vive en los hechizos de `catalog/magic-2a.yaml`, o son la sección-contenedora
`Commands` de Mazzalupo, cuyas siete órdenes se ingieren como siete reglas propias).

### 3.3 Guardas nuevas (§4c y §4d del auditor)

`check_item_profiles` compara cualquier fila de perfil impresa dentro de una sección de
Special Equipment con el texto del ítem, como **subsecuencia ordenada de sus números**
(la redacción alrededor queda libre). Acepta cualquiera de los ítems candidatos del
catálogo, porque los nombres de display colisionan entre catálogos (el `familiar` de
Trollheim de la KB frente al `society_familiar` de 2A). Salida: 3 filas comparadas, 0
hallazgos, y la prueba negativa (borrar `I3` del perfil del Pigback en una copia
descartable) sí lo reporta.

`check_rule_clarifications` cubre la clase §3.2: para cada regla, toma la sección que
su `source.section` nombra y exige que cada aclaración entre paréntesis de esa prosa
aparezca en el paquete (se comparan las reglas de la banda en conjunto, porque una
sección puede alimentar varias reglas, y las cifras se normalizan a palabras: la página
escribe «1 snotling runt», la transcripción «one Snotling runt»). Los ejemplos se
excluyen por la convención. Salida: 20 aclaraciones comparadas, 0 hallazgos; la prueba
negativa (borrar la aclaración de restricciones de mano de Stampede) sí lo reporta.

## 4. Revisión a mano de las aclaraciones fuera de la guarda (2026-09-16) → **4 completadas a mano; 11 cubiertas por otra vía; 16 fuera de alcance por convención; 4 divergencias de ítem compartido**

La guarda `clarification-absent` (§3.3) sólo mira las secciones de reglas y hechizos
(`special rules` / `special skills` / `magic`), porque es donde vive la prosa que se
ingiere como regla. Fuera quedaban las entradas de héroe/henchmen, la prosa de los
objetos y los encabezados de lista. Un barrido total de las 19 páginas —cualquier nivel
de encabezado, tablas descartadas (las listas ya se auditan fila a fila por precio)—
revisó **459** aclaraciones entre paréntesis y dejó 32 sin coincidencia literal en el
paquete. Herramienta: `build/cache/2a-sources/probe_clarifications_all.py` (con
`--global` el cotejo se hace contra toda la 2A y el catálogo de la KB, lo que separa el
hueco real del falso positivo del emparejamiento objeto↔banda: los objetos
`out-of-scope` no llevan `source_refs` con el slug de la banda que los usa). Cada
ausencia se adjudicó a mano contra su sección.

### 4.1 Completadas a mano (4)

| Banda | Dónde | Qué faltaba | Acción |
|---|---|---|---|
| `ogre-hunting-party-web` | `band--ogre-hunting-skills`, cláusula Set Traps | Las dos aclaraciones impresas —«(he may not set traps if he's just recovered from being Knocked Down)» y «(note that the Trapper won't trigger his own traps)»— y el resto del procedimiento que la condensación se había llevado («Trappers are experts at dropping snares», «friend or foe», «roll a D6», el caso de varias heridas / Derribado o Aturdido, «Regardless whether the trap was triggered or not») | Restaurado con la redacción impresa (EN + ES). Precedente KB: la misma regla en `averlanders/bergjaeger--set-traps` conserva el texto íntegro, aclaraciones incluidas. En la misma pasada se restauró la frase perdida del Redador («if not used during the game, they assumed to be stashed away or fallen apart») |
| `dwarf-slayer-cult-web` | filas de lista del `throwing_axe` | La disponibilidad que imprime su sección: «Slayers-common, (non-slayers, rare 5)» | Nota añadida en las dos listas que imprimen la fila; la convención del propio fichero ya anotaba las disponibilidades («Dwarf only», «Rare 9 (Slayers only)») |
| `dwarf-slayer-cult-web` | notas del `gromril_weapon` (3 listas) | «(or the campaign setting)» tras «later purchases use the Mordheim price chart» | Nota completada |
| `protectorate-of-sigmar-lotd3` | nuevo `band--huntsman-hero-slot` | «0 – 1 Huntsman (takes place of one templar)»: restricción de cupo que ni el roster ni ninguna regla recogían | Regla de banda nueva con la forma exacta del precedente KB (`outlaws-of-stirwood-forest/band--cleric-hero-slot`: `applies_to: {band: true}`, `runtime` `NO`/`NO` con `reason`), EN + ES, registrada en `band.yaml:rule_ids` |

### 4.2 Cubiertas por otra vía, sin cambio (11)

| Banda(s) | Aclaración | Dónde vive ya |
|---|---|---|
| `necrarchs-the-soul-stealers-lotd1` (×2) | «(such as fear)», «(but may charge normally)» | Reglas con `rule_ref` sin prosa local, según la decisión de `retired-rule-restatements.md`: la regla compartida imprime literalmente «may not run, but may charge normally», y la redacción de la fuente (con ambas aclaraciones, EN + ES) está archivada allí |
| `snotlings-web` (×4) | «(see “small hands” below for rules)», «(in regards to the rule “weakness in numbers”)», «(dodgy, small target, small hands, not so tough)», «(Warband size: 3-30)» | Las cuatro reglas existen (`band--small-hands`, `band--weakness-in-numbers`, `band--dodgy/small-target/small-hands/not-so-tough-gits` con `applies_to: {band: true}` y la exención del Mob en su propia regla); las restricciones de Runts están en `profile.equipment_restrictions`; el tamaño de banda es `roster.minimum_models: 3` / `maximum_models: 30` |
| `grave-robbers-sylv`, `outlaws-of-stirwood-forest-redux-fbg`, `wood-elves-of-athel-loren-web` (×3) | «(bought in groups of 1-5)» | `roster.members[].group_size: {minimum: 1, maximum: 5}` (también en `nipponese-expedition-web`: `ashigaru`) |
| `outlaws-of-stirwood-forest-redux-fbg` | «(in addition to all other modifiers)» | El texto del `forest_cloak` lo lleva; el barrido no lo veía porque ese ítem vive en `out-of-scope.yaml`, sin `source_refs` que lo asocien a la banda |
| `dreamwalkers-cult-of-morr-fbg` | «(check at special rules section)» | `dreamer--choosen-of-morr` dice «See the special rules section for more information.» |

### 4.3 Fuera de alcance por convención KB (16)

Ningún fichero de la KB, 2A o 2B ingiere descripciones de héroe, lore de trasfondo,
ensayos de táctica ni ejemplos resueltos: los `profiles` no tienen campo de descripción,
los `effect` de ítem llevan reglas (no prosa de marketing) y los ejemplos se descartan por
la convención de §3.2.

| Banda(s) | Caso | Conteo |
|---|---|---|
| `halflings-mic` | «(especially eat!)» y «(the list goes on and on!)» (lore), «(by halfling standards, anyways)» (lema de la entrada de henchmen) | 3 |
| `ogre-hunting-party-web` | «(before running like hell)» (lema del Sabre-Baiter) | 1 |
| `snotlings-web` | «(For example: you have 15 members, with a total of 42 experience…)» (ejemplo resuelto), «(as orcs tend to do)» y «(their first mind you!)» (prosa de las entradas) | 3 |
| `outlaws-of-stirwood-forest-redux-fbg` | Las tres del relato del autor («A little background»: las miniaturas proxy, «just the pictures, layout, and correcting typos», «i thought he'd sold the lot») | 3 |
| `dwarf-slayer-cult-web` | «(but stronger)» (prosa del ítem de la KB), «(from charging)» (dentro del ejemplo resuelto de Whirlwind of Death), y el ensayo de táctica del autor: «(thick skull, step aside, etc.)», «(although, i've never personally used one…)», «(that may be nothing to an elf warband…)», «(though constant stuns…)» | 6 |

### 4.4 Divergencias con ítems compartidos de la KB — **decisión pendiente (4)**

Estas cuatro no son texto perdido: son la página imprimiendo **su propia versión** de un
ítem que ya vive en la KB, cuyo texto es canónico y que la 2A referencia por `item_id`.

**`druchii-mic` — Sea Dragon Cloak (3 aclaraciones).** El ítem KB `sea_dragon_cloak`
(fuente: mordheimer *grade-1b dark-elves*) imprime la ambigüedad de combinación y su
mecánica dice «Grants a 5+ save in close combat and 4+ against shooting; **cannot combine
with other armour**». La página 2A imprime su regla *Scales*:

> …receives a +2 bonus to his save against shooting (or in the event where he has none, a 5+ save)
> and a +1 bonus to his save in close combat (or, if he has none, a 6+ save). A Sea Dragon Cloak
> may be combined with other pieces of armour (shield, light armour) with no penalty.

Los dos originales **se contradicen** en lo esencial (¿se combina o no?) y en las cifras
(bono frente a salvación fija). El paquete referencia el `item_id` de la KB y no reimprime
la versión de la página: hay que decidir en la promoción entre (a) mantener el texto de la
KB como canónico y añadir el `source_ref` de la página con la variante documentada
(precedente 2B `dragon_cloak` → `sea_dragon_cloak`) o (b) tratar la impresión de la página
como un ítem variante propio. **No se ha tocado nada**.

**`dwarf-slayer-cult-web` — Parry del Dwarf Axe (1 aclaración).** La página imprime la
regla de parada completa, incluido «a model armed with two dwarf axes (or a dwarf axe and
a sword, etc) does not get to parry two attacks but may instead re-roll a failed parry».
La KB modela el ítem con `mechanic weapon.dwarf-axe` (`parry: true`,
`armour_penetration: 1`) y `rules/resolution.yaml` fija
`reroll: {sword_and_buckler: one_reroll_of_failed_parry, two_swords: no_reroll}`: **la
repetición con dos hachas no está implementada** y el paquete no puede añadirla a un ítem
compartido. Registrado para la promoción (ampliar la mecánica del ítem o dejar constancia
del hueco de motor).

### 4.5 Sin hogar en el esquema actual (1)

«You have 500 warp tokens (equivalent to gold crowns)» (`skaven-of-clan-moulder-web`). El
esquema de banda no tiene campo de divisa —las claves de `band.yaml` de la KB son
`id`/`name`/…/`roster`/`rule_ids`/`variants`, y los miembros de roster sólo
`profile_id`/`minimum`/`maximum`/`group_size`— y la propia revisión de conformidad de 2B
ya dejó marcados como pendientes sus `currency: dinars` / `currency: warp tokens` y el
`currency_note` de Pestilens. Este paquete **tuvo** las claves
`starting_gold_currency`/`starting_gold_note` y se retiraron en la pasada de conformidad
por no ser forma KB (patrón derivado de `sources/knowledge`); las listas de Moulder sí imprimen la
divisa fila a fila («1st free/2 wt»), de modo que el dato es visible, pero el enunciado
de equivalencia no tiene dónde ir. Pendiente de decisión (¿campo documentado en el
esquema de banda, aplicado a la vez a 2A y 2B, o nota?), sin efecto hoy en la vista: el
generador web no publica `starting_gold`.

### 4.6 Cobertura del barrido

```
459 aclaraciones revisadas en las 19 páginas (todas las secciones, cualquier nivel)
 32 ausentes distintas tras el cotejo literal
   4 completadas a mano (§4.1)
  11 cubiertas por otra vía (§4.2)
  16 fuera de alcance por convención (§4.3)
   4 divergencias con la KB (§4.4) + 1 sin hogar en el esquema (§4.5)
  0 pendientes de comprobación
```

Reproducible con `python build/cache/2a-sources/probe_clarifications_all.py` (y
`--global` para el cotejo contra toda la 2A y el catálogo KB).

## 5. Pasada de fidelidad del staging (2026-09-21)

La re-verificación cruzada de los paquetes contra los textos extraídos
(`tools/ingestion/audit_2ab_fidelity.py`) encontró una divergencia más de ítem
compartido, del mismo tipo que las de §4.4:

**`druchii-mic` — Swift del Draich (1 aclaración).** La página imprime el arma y su regla
propia:

> Range: Close combat · Strength: As user +2 · Special Rules: Two-handed, **Swift**.
> Swift: A Draich, unlike other double-handed weapons, does not Strike last.

La KB modela el `item_id` `draich` desde Trollheim (`mechanic weapon.draich`, «strikes
last») y el paquete 2A lo referencia por id, así que la regla impresa **no se refleja** en
ninguna parte: la página describe un Draich que **no** golpea el último y la KB uno que sí.
Decisión de promoción pendiente, con las mismas dos salidas que el Cloak (documentar la
variante en el `source_ref` o modelar el ítem de la página aparte). **No se ha tocado
nada.**

## 6. Cotejo de los Dramatis Personae contra su fuente (2026-09-23)

Los 30 perfiles de `sources/knowledge/catalog/hirelings/dramatis-personae/` (grados 1a, 1b,
1c y 2a) tienen su cotejo en `tools/ingestion/check_2a_dramatis.py`, que es el **mismo**
lector de entradas impresas que el de los hirelings de 2B: la geometría con la que se lee
cada entrada, la comparación de divisa y la cobertura por chequeo son compartidas, y cada
driver sólo resuelve qué página imprime a cada personaje y qué adjudica su árbol.

### 6.1 El cotejo anterior no leía la página por entradas

Cotejaba el texto aplanado de la página y localizaba los bloques por el nombre del
personaje, y eso produjo cuatro perfiles sin localizar (Aksho, el Dark Jester, Sigmund y
William) y **dos tarifas atribuidas al vecino**:

| Perfil | Tarifa que el cotejo anterior leía | Tarifa que la página imprime | De quién era |
|---|---|---|---|
| “Busty” Gwen | 75 gc + 30 gc | ninguna (cobra por el escenario) | del Dark Jester, entrada contigua |
| The Foole | 70 gc + 35 gc | 40 gc | de Sigmund, entrada contigua |

La página de mordheimer.net trae sus entradas escritas —un `div` con clase propia por
personaje y una celda por columna en la tabla de perfiles—, así que la lectura por geometría
es aquí la estructura del documento: la tarifa, la fila y el rating de una entrada no pueden
mezclarse con los de la contigua. El texto plano queda como respaldo, declarado como tal.

### 6.2 Resultado

| Chequeo | Cobertura (grado 2a) | Hallazgos |
|---|---|---|
| Entrada impresa localizada | 7/7 | — |
| Tarifa (importe **y** divisa) | 6/7 | 0 |
| Fila de stats | 6/7 | 0 |
| Rating | 7/7 | 0 |
| Reglas presentes (una por una) | 7/7 | 0 |

Los grados 1a, 1b y 1c quedan **sin comparar** porque su página no está cacheada en este
checkout, y el informe lo dice agrupado en vez de contarlos como verdes. Dos adjudicaciones
se declaran con su evidencia en lugar de silenciarse:

- **The Headless Horseman** (`out_of_scope`: entidad compuesta de jinete y montura): imprime
tarifa (100 gc) y dos filas, y el catálogo no modela ni su tabla ni su tarifa, así que su
tarifa y su fila quedan como nota y se coteja lo que sí declara (rating +80 y las nueve
reglas).
- **`Conditional Acceptance — Good-Aligned Employers`** (William): la página imprime la
elegibilidad como el párrafo «May Be Hired: … any good-aligned warband may hire William on
a roll of 4+», y el catálogo la modela como regla del perfil; la etiqueta se declara en
`EDITORIAL` con esa evidencia y queda como nota.

```bash
python -X utf8 tools/ingestion/check_2a_dramatis.py
python -X utf8 -m pytest tests/knowledge/test_2a_dramatis_cotejo.py
```

La batería fija la lectura buena con la página real (Gwen sin tarifa y el Dark Jester con
75/30; la fila de Aksho con su Ld de dos cifras completa) y añade dos **pruebas negativas**:
una tarifa cambiada en el contrato y una fila cambiada en el catálogo tienen que producir el
hallazgo correspondiente.

## 7. Las listas y tablas de 2A se leen con el lector compartido (2026-09-23)

`audit_2a_sources.py` coteja las listas, los precios y las tablas de las 19 páginas, y
ahora las lee con el **mismo lector de entradas impresas** que el cotejo de catálogo
(`tools/ingestion/printed_entries.py`): encabezados con su tramo, texto de la sección y
filas de tabla con sus celdas en el orden de las columnas. Antes las leía con expresiones
regulares sobre el HTML, que pierden una celda con etiquetas dentro o con entidades
escapadas y no distinguen el tramo de una sección de la tabla que le sigue.

La corrida completa da **los mismos números** que la lectura anterior —0 hallazgos
abiertos, 14 adjudicados, 47 listas y 558 filas comparadas— y ahora declara la cobertura
**por chequeo**, como los cotejos de hirelings y de Dramatis Personae:

```
sources/2A vs cached pages: 0 open finding(s), 14 adjudicated
cobertura por chequeo: skills 44/44 etiquetas en 12 bandas, special-equipment 34/34 secciones en 14 bandas, lists 558/558 filas en 47 listas [bajo un h2: 5], special-price 33/34 precios en 35 ítems (1 sin comparar), item-profiles 3/3 filas en 3 secciones, rules 362/365 nombres en 19 bandas, clarifications 22/22 aclaraciones en 19 bandas, magic 69/69 conjuros en 12 secciones
```

Los dos deltas son los hallazgos ya adjudicados: 1 precio (el erratum del silver-tip
stake, §2.1) y 3 nombres de regla que la página no imprime como etiqueta (§3). El
`1 sin comparar` de `special-price` es el ítem cuya tarifa la página no imprime y sí su
lista: se declara en vez de contarse como verde. Las cifras sustituyen a las tres líneas
en prosa que el auditor imprimía antes (§2.6), que quedan como el registro de aquella
corrida.

Los pins: `tests/knowledge/test_2a_source_audit.py` fija las cifras de la corrida
completa y añade la lectura por estructura (una celda con `<strong>` y una tabla que
pertenece a la sección siguiente), y `tests/knowledge/test_printed_entries.py` cubre el
lector —encabezados con su tramo, filas con sus celdas y su tabla— y el libro de
cobertura.

## 8. El auditor de fidelidad lee las filas de la tabla impresa (2026-09-23)

`audit_2ab_fidelity.py` coteja los 79 paquetes de staging —los 19 de 2A incluidos— contra
los textos de sus fuentes, y leía el documento de cada paquete con `pdftotext -layout`.
Ahora lo lee con el **lector compartido** (`printed_entries.PdfCorpus`), que da cada columna
entera y en su orden, y las filas de características de la tabla impresa con la **línea
física y sus celdas** (`printed_row`). Tres reglas son las que cambian lo que el auditor ve:

- **el nombre de la fila es el de la celda que lleva sus cifras**, no la cola de la prosa
  que la columna vecina deja a la misma altura: la línea «… their ascension. They» |
  «Spirit 5 5 0 4 3 4 5 3 9» da la fila «Spirit» (antes, «their ascension. They»), y el
  «Boss» del KAZ se llama «Boss» y no «stwi ald boss»;
- **las nueve cifras de una fila pueden repartirse entre celdas, pero cada celda las imprime
  en un solo tramo**: la tabla de tesoros que imprimen las páginas de «Warrior Training
  Ground» («D3 Gems worth 10 gc each 4+») y el paréntesis que la sigue daban nueve cifras
  plausibles de un perfil llamado «D» que ningún paquete modela, y se reportaba en los ocho
  paquetes del KAZ;
- **una fila cuyo nombre coincide con un perfil del KB sólo cuenta como modelada si el KB
  también lleva sus características**: el KB tiene un «Boss» de `4 3 4 3 3 1 4 1 7` y las
  páginas del KAZ imprimen un «Boss» de `4 4 3 4 4 1 3 1 8`, así que darlo por cubierto por
  el nombre ocultaba la fila.

Medido contra la misma corrida con la lectura anterior (los mismos 80 paquetes y el mismo
KB), no hay ningún hallazgo nuevo y sí uno menos en cada clase que crece la cobertura:
`rule-effect-condensed` 97 → 64 (los efectos que la geometría lee enteros pasan de
«condensados» a verbatim o casi verbatim: 988 → 1037), `item-in-supplement` 15 → 14,
`item-name-missing` 28 → 27, y las filas que el auditor reconoce por su nombre impreso pasan
de 1 a 20 (las que coteja por sus características, 620 → 600: son las mismas filas, mejor
atribuidas). Los nombres de las 208 filas «modeladas en otro documento» mejoran en 71 casos
(el resto es de las fuentes sin geometría cacheada, que conservan su lectura).

Dos casos entran en `ADJUDICATED` con su razón y ninguno es un defecto:

| Etiqueta | Veredicto |
|---|---|
| `araby-smugglers-sar`: «Fine Craftsmanship» (`rule-name-editorial`) | La misma errata de la fuente («Fine Craftmenship») que ya estaba adjudicada; con el efecto leído casi verbatim, el caso se clasifica por su nombre |
| `snotlings-web`: fila `4 4 4 3 3 2 9 4 6` («snotling») | Es la tabla de máximos que la página encabeza «Profile» («Snotling maximums: M 4, WS 4, BS 4, S 3, T 3, W 2, I 9, A 4, Ld 6»): el paquete la lleva dentro de su regla «Characteristic Increase», no como perfil, y el auditor la lee ahí. Antes quedaba silenciada por el nombre («Snotlings» es un perfil del KB, con otras características) |

Los pins: `tests/knowledge/test_2ab_fidelity_rows.py` fija las tres reglas con fixtures
—el nombre de la celda que lleva las cifras, las cifras partidas entre celdas, la tabla de
tesoros que no es una fila, el perfil del KB que no cubre la fila— y, si están cacheados
los PDFs, los nombres de las filas de la tabla del KAZ.

## 9. Los objetos del paquete se cotejan contra las listas impresas (2026-09-23)

El auditor cotejaba los objetos de `equipment-access.yaml` buscando su nombre en el
**texto** del documento: una traza de nombre, que cualquier prosa satisface —el objeto
quedaba por bueno porque su nombre apareciera en la descripción de una regla, en la lista
del vecino o en la del capítulo de un anual—. Ahora los coteja contra la **fila de la
lista**: lo que la fuente imprime con su tarifa, leído por geometría en las listas de
precios de 2B (`price_rows`) y por la estructura de la página web en 2A (`list_rows`: una
celda por columna y la fila que tasa). El nombre se coteja por **palabras**, no por su
puntuación, porque la fila la imprime la fuente a su manera: «Blunderbuss*» (el asterisco
de disponibilidad), «Mace/Hammer» y «Dagger/Pointy Stick» (dos objetos en una celda),
«Cat O’ Nine Tails» (el apóstrofo), «Double Handed Weapon» (sin guion) y «Hammer/Mace»
(el catálogo lo llama «Mace Hammer»). La clase del hallazgo dice de dónde sale el nombre:

| Clase | Qué declara |
|---|---|
| `item-in-list` | Una fila de la lista del propio documento imprime el nombre |
| `item-in-supplement` | Sólo lo imprime la lista de un capítulo que el árbol comparte (anuales, especialistas) |
| `item-outside-list` | Ninguna fila lo imprime: el nombre sólo está en la prosa del documento, que el informe nombra entre paréntesis |
| `item-name-missing` | No está ni en una fila ni en la prosa |

Los objetos de las 19 páginas, sobre las mismas 47 listas y 558 filas que ya cotejaba
`audit_2a_sources.py`: **556 de 559 se leen ya en la fila de su lista**, ninguno cae en
`item-in-supplement` y los 3 restantes son el mismo objeto en las tres listas de
Snotlings (`item-outside-list`):

| Objeto | Fila impresa (verbatim) | Paquete | Veredicto |
|---|---|---|---|
| `small_pebble` ×3 (Snotling, Shoota y Snotling Mob Equipment List) | p. de Snotlings: la lista imprime `Pebble … Free!` y la sección de reglas imprime el mismo objeto como `Small Pebble` | `item_id: small_pebble`, `cost: 0`, `notes: Free!` | **fiel a su fuente**: el objeto está impreso en la lista (y el paquete copia su tarifa y su nota); la página le da dos nombres —`Pebble` en la lista y `Small Pebble` en su regla— y el catálogo toma el de la regla. El hallazgo se declara, no se corrige |

Los 3 `item-name-missing` que quedaban (`blessed_water` ×2 y `sigmarite_hammer`) no eran
huecos sino **divergencias de palabra**: la página sí imprime el objeto, con otro nombre
—`Holy Water` en las dos listas y `Sigmarite Warhammer` en la del Protectorate— y con la
tarifa que el paquete declara, y el cotejo no conocía esa palabra. El veredicto es
**quedar como nota**: no se renombra la fila del paquete (su `item_id` es el del KB, que
manda en el vocabulario) ni se promociona una entrada nueva (el objeto ya está en el
catálogo), sino que la palabra impresa se registra donde el cotejo la lee:

| Objeto (KB) | Palabra impresa (verbatim) | Tarifa | Dónde queda registrada |
|---|---|---|---|
| `blessed_water` | `Holy Water` (Protectorate) y `Holy Water` (Vampire Hunters) | 5 gc* / 10 gc* ✓ | `printed_wordings.py`, el registro único de los tres cotejos: la fila se lee con `words_at('2A', banda, lista, objeto)` y el objeto con `words_for_item(objeto, '2A')` |
| `sigmarite_hammer` | `Sigmarite Warhammer` (Protectorate) | 15 gc* ✓ | ídem |

Con la palabra registrada los tres objetos pasan de `item-name-missing` a **`item-in-list`**
—la lista sí imprime su fila, con la palabra de la fuente— y `item-name-missing` queda en
**0** para las 19 páginas: 556 objetos en la fila de su lista y los 3 del nombre corto de
la lista de Snotlings declarados. El nombre canónico del KB **no se toca**: el de `blessed_water` («Blessed Water»)
es a su vez la palabra con que imprime el objeto el capítulo de *Miracle Workers* de 2B, y
el de `sigmarite_hammer` («Sigmarite Hammer») una contracción de «Sigmarite Warhammer» que
el contrato, el motor y las pruebas de paridad ya usan (`weapon.sigmarite-hammer`);
renombrarlo es un cambio de la KB entera —schema, interfaz y vectores—, no un arreglo de
staging, y la convención de este árbol es registrar la variante, no renombrar el nombre.
Al promover, las dos páginas se suman a los `source_refs` de ambos objetos.

Hasta el 2026-09-24 cada auditor llevaba **su** tabla de palabras —`SOURCE_WORDING` en
`audit_2a_sources.py` y en `audit_2b.py`, `ITEM_ALIASES` en el cotejo de fidelidad— y una
pareja adjudicada en una se quedaba sin ver en las otras: el de fidelidad declaraba
huecos que los otros dos ya tenían adjudicados. Ahora hay **un solo registro**
(`tools/ingestion/printed_wordings.py`), con el sitio donde se leyó cada palabra, y lo
leen los tres. Las dos de 2A de la tabla de arriba se resuelven igual que antes —el
informe de `audit_2a_sources.py` es idéntico byte a byte, 0 abiertos y 14 adjudicados—, y
las que sólo tenía 2B pasan a servir también al cotejo de fidelidad (dos objetos que
estaban en la clase `item-in-supplement` se leen ya en la fila de su propio documento,
§15.5 de los verdictos de 2B).

```bash
python -X utf8 tools/ingestion/audit_2ab_fidelity.py --tree 2A --json > build/cache/fidelity-2a.json
python -X utf8 -m pytest tests/knowledge/test_2ab_fidelity_rows.py tests/knowledge/test_printed_entries.py
```

Los pins: `tests/knowledge/test_2ab_fidelity_rows.py` fija el cotejo del objeto contra la
fila (el asterisco de disponibilidad, la celda que imprime dos objetos, el apóstrofo, el
guion contra el espacio, la entrada combinada que la lista imprime en el otro orden, el
nombre que el catálogo compone con un guion largo y cada palabra impresa de las dos
adjudicadas arriba, contra la fila verbatim de la que se leyó), y
`tests/knowledge/test_printed_entries.py` la lectura que lo hace posible (una fila por
celda que tasa, la fila cuya tarifa es un multiplicador del precio de otro objeto y la
tabla de la página web que tasa con él).

## Resumen

| Caso | Veredicto | Acción |
|---|---|---|
| Silver-tip Stake LotD #5: 10 gc (listas) vs 15 gc (Special Equipment) | Fiel a su fuente (erratum interno del PDF original, verificado en `LOD5.pdf` p.10) | Resuelto por decisión editorial: 10 gc operativo; 15 gc marcado como erratum (2026-09-15) |
| 8 precios de tirada/lista guardados como `null` (Masters of Horror ×3, Necrarchs, Sorcerous Society, Survivors of Strigos ×3) | La fuente imprime cifra y/o dados; `null` perdía el precio | Corregido con el criterio KB (§2.1): expresión de dados si la lista la imprime, cifra de lista si la lista es fija |
| 5 listas publicadas bajo `h2` (Ogre ×2, Outlaws, Sorcerous Society, Protectorate) | Nunca cotejadas por el auditor | Cubiertas: 73 filas comparadas, todas coinciden; el auditor ahora es dirigido por la lista |
| 23 filas de Clan Moulder en warp tokens | La divisa impedía compararlas | Cubiertas (coinciden); el auditor conoce `gc`/`crowns`/`wt` |
| Precios del bloque Special Equipment (35 ítems) | Sin cotejar contra la página | 34 cotejados; sin errores (el único desacuerdo es el erratum del verdicto 1) |
| Perfil de la montura Pigback (`ogre-hunting-party-web`) | Fila de atributos impresa en su sección, no ingerida | Completada a mano (EN + ES); guarda `item-profile-absent` añadida al auditor (§3.3) |
| Aclaraciones entre paréntesis en 3 reglas (Stampede, Record of Valor, Monster Slayer) | Prosa de regla condensada: se caían `(i.e. …)`, `(thus, …)` y matices impresos | Restauradas en EN y ES; barrido completo de las 19 páginas y guarda `clarification-absent` (§3.3) |
| Cupos, tamaño de banda, oro, experiencia, rareza, precios relativos y prosa de los 35 ítems | Cotejados como parte de la re-verificación (§3) | Sin errores: 19/19 bandas y 35/35 ítems coinciden con las páginas |
| 32 aclaraciones entre paréntesis de entradas de héroe/henchmen, prosa de ítem y encabezados de lista (fuera de la guarda, que sólo cubre secciones de reglas) | Barrido total de las 19 páginas, adjudicación a mano (§4) | 4 completadas a mano; 11 cubiertas por otra vía; 16 fuera de alcance por convención; 4 divergencias de ítem compartido |
| Set Traps del `ogre-hunting-party-web`: dos aclaraciones impresas más el procedimiento de la trampa | Prosa de regla condensada (la KB-Averlanders conserva la misma regla íntegra) | Restaurado EN + ES; Redador recupera su frase perdida (§4.1) |
| «0 – 1 Huntsman (takes place of one templar)» (`protectorate-of-sigmar-lotd3`) | Restricción de cupo sin reflejo en roster ni reglas | Regla de banda `band--huntsman-hero-slot` con el patrón KB `band--cleric-hero-slot` (§4.1) |
| Sea Dragon Cloak (`druchii-mic`) y Parry del Dwarf Axe (`dwarf-slayer-cult-web`) | La página imprime su versión de un ítem compartido que la KB define con texto canónico (la del Cloak **contradice** la de la KB; la repetición de parada con dos hachas no está en el motor) | Registrado para la promoción; **nada tocado** en la KB compartida (§4.4) |
| Divisa de Clan Moulder («500 warp tokens (equivalent to gold crowns)») | El esquema de banda no tiene campo de divisa (las claves `starting_gold_currency`/`starting_gold_note` de este paquete se retiraron por no ser forma KB; 2B tiene el mismo pendiente para `dinars`/`warp tokens`) | Pendiente de decisión de esquema (§4.5); la divisa sí es visible en las notas de lista («1st free/2 wt») y el generador web no publica `starting_gold` |
| Draich (`druchii-mic`): regla *Swift* impresa | La página imprime su versión de un ítem que la KB define con texto canónico (KB: «strikes last»; página: «does not Strike last») | Registrado para la promoción; **nada tocado** en la KB compartida (§5) |
| Dramatis Personae de grado 2a: cuatro bloques sin localizar y dos tarifas del vecino (Gwen con los 75 gc del Dark Jester; el Foole con los 70 gc de Sigmund) | El cotejo leía el texto aplanado y no la página por entradas | Cotejo rehecho sobre el lector de entradas compartido con 2B: 7/7 localizados, 0 hallazgos (§6) |
| Listas y tablas de las 19 páginas de banda: leídas con expresiones regulares sobre el HTML | Una celda con etiquetas dentro o con entidades se perdía, y una tabla podía atribuirse al tramo equivocado | Leídas por la estructura del documento con el lector compartido, y con cobertura por chequeo (8 chequeos); mismos números: 0 abiertos, 14 adjudicados, 47 listas y 558 filas (§7) |
| Filas de características del auditor de fidelidad: leídas con `pdftotext -layout` | Atribuía a la fila la cola de la prosa vecina y leía como fila la tabla de tesoros del KAZ («D3 Gems worth…», ocho paquetes) | Leídas con la línea física y las celdas del lector compartido (`printed_row`), con el nombre de la celda que lleva las cifras y un solo tramo de cifras por celda; 0 hallazgos nuevos, `rule-effect-condensed` 97 → 64 y 71 nombres de fila mejorados (§8) |
| Objetos de `equipment-access.yaml` cotejados contra el **texto** del documento (traza de nombre) | Cualquier prosa daba el objeto por impreso, y el nombre de una fila de lista se perdía por su puntuación (asterisco de disponibilidad, dos objetos en una celda, apóstrofo, guion) | Cotejados contra la **fila de la lista impresa**: 2107 de 2131 objetos en `item-in-list`, 17 en `item-in-supplement`, 5 en `item-outside-list` y `item-name-missing` 27 → **0** (2 adjudicados: la lista que el KAZ delega al reglamento); en 2A, 556/559 en su lista y el único caso divergente es el nombre corto de la lista de Snotlings (`Pebble` por `Small Pebble`, §9) |
