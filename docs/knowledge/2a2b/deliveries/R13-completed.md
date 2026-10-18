# R13 — los cinco pendientes reales: armas mal atribuidas y referencias sin regla

**Estado integrado y cerrado: 13/13 filas de R13, 2026-10-16. La última conexión del Yari ya está aplicada al CSV.** Repo
`D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`. Base exacta previa a mis ediciones, conservada
fuera del árbol: `C:\Users\PHOLTE~1\AppData\Local\Temp\r13\base2\` (los archivos que toco, más la
instantánea íntegra del registro CSV: `sha256 366fccd34ebe0c2c789b5e52be2d2648`).

**Segunda pasada (2026-10-16, empuñaduras del Yari):** el parche, las copias de los archivos
modificados y la evidencia están en `C:\Users\PHOLTE~1\AppData\Local\Temp\r13g\evidence\`
(`yari-grips.patch`, `current/`, `current-md5.txt`). El lado eliminado de cada hunk del parche *es*
el contenido previo a mi edición; `loader.py`, `eligibility.py`, `index.ts` y `catalogue.py` ya
llevaban ediciones concurrentes de otro trabajo del mismo checkout antes de que yo los tocara, así
que no se reclama una base prístina para esos archivos: el parche y las copias son el registro
íntegro de lo que dejé, y en la sección 3 se cita el antes exacto de cada miembro nuevo.

Las ocho filas ya cerradas no se repiten. Se sustituyen las «pruebas de fuente» anteriores —que
construían el operador supuesto— por discriminadores de la ruta canónica (objeto → mapping →
consumidor) en `tests/python/construction/test_t13_weapon_variant_profiles.py`.

## 1. Belaying Pin: la definición impresa es sólo arrojadiza

**Antes:** `kind: close-combat-weapon` + `mechanic_id: weapon.mace`, con una Concussion que ninguna
palabra impresa sostenía. **Fuente decisiva** (la que el propio registro cita como `*id003`/`*id004`):
las listas de equipo Pirata y Swabbie del Town Cryer #9 — https://mordheimer.net/docs/warbands/grade-1b-warbands/pirates
— imprimen el Belaying Pin en **Missile Weapons** (3 gc), no en Hand-to-hand Combat Weapons; todo su
contenido impreso es el perfil arrojadizo `Range: 6" Strength: As user -1` con los modificadores de
arma arrojadiza incómoda, es decir el subsistema de disparo excluido. **Después:** `kind: ranged-weapon`,
`combat_status: out_of_scope`, sin `mechanic_id`, y mapping `out_of_scope` en
`sources/knowledge/catalog/mechanics/simulation-mappings.yaml`. No se inventa alcance, Fuerza,
Concussion ni +1 a la salvación enemiga. **Variantes conservadas:** el texto Town Cryer sigue siendo
el `effect` y la redacción Channel Rats (MiM p. 178, *Thrown weapon, +1 Enemy armour save*) entra como
`source_ref` propio, exactamente como pide `sources/2B/catalog/promotion-merge-notes.md`
(«extra source_ref + review note, not as replacement effect»). **Acceso por el objeto canónico:** el
ítem `belaying_pin` resuelve a *ningún* operador cuerpo a cuerpo y la Concussion queda sólo en la
Mace, su propio objeto.

## 2. Sunstaff: identidad de proyectil, sin mitad melee

**Antes:** `kind: close-combat-weapon` + `mechanic_id: weapon.brazier-iron` (dos manos, F+1,
ignición). **Fuente decisiva:** la Heroines Equipment List de las Amazons, Town Cryer #23
(`*id009` → https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons), lista el Sunstaff en
**Missile Weapons** (50 gc), y su texto impreso es el perfil de proyectil `Range: 24" Strength: 4
Accurate`. Ninguna frase impresa dice dos manos, F+1 ni ignición. **Después:** `kind: ranged-weapon`,
`combat_status: out_of_scope`, sin `mechanic_id`, mapping `out_of_scope`. **No se extiende** a
`sunstaff_lustria` (Town Cryer #15, 35 gc): conserva registro y operador, y su propia fuente sí
documenta una mitad melee distinta. **Residuo anotado sin tocar el registro** (transcripción no
verificada visualmente): el perfil impreso llevaría además una regla especial *No save* que el
`effect` congelado no recoge; al quedar el objeto fuera del duelo no tiene consecuencia ejecutable.

## 3. Yari: las dos empuñaduras impresas, desde el mismo objeto canónico

**Integración final del coordinador:** ambas empuñaduras canónicas aceptadas;
nota obsoleta de la lista alineada sin alterar el clause_text protegido del CSV.
Corregido el caso de ausencia del Peto de Bronce ya conectado por C07b.
Seis casos afectados correctos (`%TEMP%\yari-coordinator-final.txt`). Una fila
aplicada con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas
y control concurrente en
`C:\Users\PHOLTE~1\AppData\Local\Temp\yari-coordinator-final-wsoyb8zx`.
R13 y C07b quedan cerrados; sin E2E, commit ni push.

**Corrección del coordinador (conservada como antecedente):** el cierre anterior no se aceptó porque
la oferta canónica no incluía la empuñadura a dos manos y elegir ese operador desde un build custom no
completaba la ruta de la lista. Esa traba queda resuelta en la capa responsable: la declaración vive en
el registro del objeto, no en un segundo objeto ni en una línea nueva.

**Antes (paso 1, ya integrado):** `out_of_scope` sin binding; la nota de la lista decía «internal item
mechanics are intentionally not modelled here». Comprobado una vez en el momento de esa pasada: no existía
entrega C07b en `deliveries/`, y el ítem seguía sin configurar, así que se completa el objeto en vez de
sobrescribir nada ajeno. **Reconciliación con C07b (posterior, sin cambio de código):** la entrega
`C07b-completed.md` apareció después, de forma concurrente, y su parte pertinente remite expresamente a
este encargo — «**Pendiente exacto:** la elección canónica de ambas empuñaduras del Yari se completa en
R13; no se cerró esa fila aquí» — con su rama (`D:\DEVEL\Mordheim\C07b-work`) todavía en `out_of_scope`
para el ítem y sin ninguna solución de empuñaduras que reutilizar. No hubo por tanto solución existente
que duplicar, y ninguna de las dos entregas sobrescribe la nota de la línea (que sigue siendo el
`clause_text` congelado de la fila). **Paso 1:** `sources/knowledge/catalog/items/trollheim.yaml` / `yari` pasa a
`combat_status: implemented` con `mechanic_id: weapon.yari-one-handed`, la misma forma que sus tres
hermanos de la misma entrada (kusara_kama, death_knife, witch_sword, anclados al mismo `*id008` de
`chaos-in-the-streets` impreso 161).

**Paso 2, la conexión que faltaba (esta pasada).** El puente objeto→mechanic del registro de mappings
es 1:1, y ahí estaba el hueco real: una sola línea de lista sólo podía ofrecer un operador. La
solución es una extensión mínima en la capa de identidad del objeto, reutilizando los dos operadores ya
existentes y sin inventar ninguna arma nueva:

- `contracts/knowledge-editorial-v1/catalog-items.yaml.schema.json`: nuevo miembro opcional
  `alternate_mechanic_ids` (array de ids únicos) con su descripción de contrato; sólo un objeto
  `implemented` puede declararlo (si aparece, exige `combat_status: implemented` **y** `mechanic_id`).
- `sources/knowledge/catalog/items/trollheim.yaml` / `yari`: gana
  `alternate_mechanic_ids: [weapon.yari-two-handed]` junto a su `mechanic_id` de una mano.
- `packages/python/knowledge/mordheim_knowledge/loader.py::load_simulation_mappings`: la fila generada
  del objeto publica `alternate_mechanic_ids` y **falla** si una empuñadura declarada no resuelve a un
  mechanic ejecutable (nada se descarta en silencio).
- `packages/python/roster-construction/mordheim_construction/eligibility.py::_catalogue`: la proyección
  de `items` viaja con `alternate_mechanic_ids` hacia el módulo compartido.
- `packages/typescript/domain/eligibility/index.ts` (y su bundle `_eligibility.js`, regenerado con
  `npm run build:eligibility`): `ItemFacts` declara el miembro; `carriedItemFacts`/`catalogueItemFacts`
  resuelven **también** la grafía del operador alterno; y un único helper `itemMechanics(catalogue,
  itemId)` devuelve las empuñaduras del objeto y es el que usan las tres rutas de oferta
  (`profileEquipment`, `buildAccess.addLists`, `catalogueEquipment`/`contractEquipment`).
- `apps/combat-lab/mordheim_combat_lab/application/catalogue.py`: la misma línea de lista precio ambas
  empuñaduras (`_costs_for_packages` recorre el operador por defecto **y** los alternos declarados).

**Resultado medido por la ruta canónica** (evidencia `probes.txt`): `CombatCatalogue().weapons` del
Silent Hunter devuelve `weapon.yari-one-handed` **y** `weapon.yari-two-handed`; las dos al mismo coste
`15.0` de esa única línea; y `validate_configuration(possession=('yari',), slots={'main_weapon_id':
<empuñadura>})` no informa problema con **ninguna** de las dos. **Transporte y consumo modular:**
`compile_fighter` con `band_id`/`profile_id` (no un build libre) compila las dos; una mano conserva
`parry` y la mano secundaria legal (`equipment_decisions(slot='off', main_weapon_id=
'weapon.yari-one-handed')` → daga permitida); dos manos conserva `parry`, `two_handed` y golpea primero
(`phases.resolve_priority(PriorityContext(fighter, foe, first_round=True)).priority == 1`), y rechaza
el equipo incompatible tanto en la decisión de selección como al compilar («occupies both hands»).
**Una sola identidad física:** sigue habiendo un `item_id` (`yari`), una entrada de la lista del Silent
Hunter y una fila del registro de mappings; cambiar de empuñadura no añade un segundo objeto, no exige
una segunda posesión (`possession=('yari',)` basta) y no elude al destinatario: otro perfil de la misma
banda (`shadow-blade`) no recibe ninguna de las dos y sigue viendo la posesión de `yari` rechazada.

## 4–5. Stickfire y Vermin Pot: pasaje recuperado y cierre sin comportamiento

**Fuente decisiva (original leído, no la nota del catálogo):** la publicación completa
`Relics of the Crusades Pt 2` (https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf,
página 16 del PDF = impresa 42) imprime cada nombre **una sola vez**, en la frase de equipo del
perfil de Armen Abbas: *«Equipment: Armen Abbas carries the Angel Wings, a sword and enough stickfire
and vermin pots to last for the entire battle.»* El suplemento no imprime perfil, entrada de tabla ni
regla especial para ninguno de los dos en ningún punto (verificado sobre el texto extraído completo
de las 962 líneas). No es una búsqueda infructuosa: es un objeto nombrado sin regla, así que **no se
inventa efecto ni consecuencia de duelo** y ambos registros permanecen `out_of_scope` e inertes (sin
`mechanic_id`, sin consumidor), con su dependencia de fuente resuelta por el pasaje. Se cierran por
separado, por ser dos objetos distintos.

## Archivos modificados

- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/sources/knowledge/catalog/items/weapons-close-combat.yaml`
  (`belaying_pin`, `sunstaff`: `kind`, `combat_status`, `source_refs`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/sources/knowledge/catalog/mechanics/simulation-mappings.yaml`
  (mismas dos filas: `out_of_scope`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/sources/knowledge/catalog/items/trollheim.yaml`
  (`yari`: `implemented` + `mechanic_id`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/tests/python/construction/test_t13_weapon_variant_profiles.py`
  (discriminadores canónicos de los tres ítems; se retiran los antiguos que construían Mace y Brazier Iron).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/tests/python/knowledge/test_equipment_source_absence.py` (`yari` sale del conjunto de ausencia:
  la fila dejó de ser `out_of_scope` al conectarse a su operador, el mismo estado que sus hermanos
  Deathbringer. El propio módulo pedía revisar la decisión cuando eso ocurriera; se documenta ahí).

Archivos propios de esta segunda pasada (rutas absolutas):

- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/contracts/knowledge-editorial-v1/catalog-items.yaml.schema.json`
  (`alternate_mechanic_ids` + su condicional; md5 `368aa89c14ffeabe830f41098a81eb29`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/sources/knowledge/catalog/items/trollheim.yaml`
  (`yari`: `alternate_mechanic_ids`; md5 `6ec8b513f301deb2c91fe5099b571398`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/packages/python/knowledge/mordheim_knowledge/loader.py`
  (fila de mappings con los alternos + guarda de empuñadura no ejecutable; md5 `373a5429ef8ebb9e42dda6719ec0700e`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/packages/python/roster-construction/mordheim_construction/eligibility.py`
  (proyección `items` con los alternos; md5 `1f74aa540d5f5e999951976770705084`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/packages/typescript/domain/eligibility/index.ts`
  (`ItemFacts`, alias/resolución de grafías y helper `itemMechanics`; md5 `4c1b6388f8a098e672aab55dd78f6988`)
  y el bundle regenerado
  `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/packages/python/roster-construction/mordheim_construction/_eligibility.js`
  (`npm run build:eligibility`; md5 `3b52ea6096471441bd5eca098b9af665`; `check:eligibility` → *current*).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/apps/combat-lab/mordheim_combat_lab/application/catalogue.py`
  (precio de ambas empuñaduras por la misma línea + `load_items` importado; md5 `3626cc3682ea40b46f8564f37d353ea4`).
- `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK/tests/python/construction/test_t13_weapon_variant_profiles.py`
  (cinco casos nuevos de la ruta canónica; md5 `5b99d030504f689d9f0ab1d51ffb016c`).

Nota de colocación, deliberada: los dos registros corregidos permanecen en su archivo registrado
(`catalog/items/weapons-close-combat.yaml`) porque el `source_file` del CSV es un campo protegido y no
puede reescribirse; su `kind` ya declara lo que imprime su fuente. Sólo son destinos de promoción para
registros *staged*, que no es el caso.

## CSV: propuesta preparada y validada, no escrita

**Integración del coordinador:** cinco filas actualizadas, cuatro pendientes
cerrados y Yari conservado como conexión pendiente. Snapshot íntegro, propuesta
corregida, validación, preview y escritura con conservación de 4.556 claves,
textos, huellas y notas y rechazo de concurrencia en
`C:\Users\PHOLTE~1\AppData\Local\Temp\r13-v2-coordinator-2dkydtgb`.
Evidencia focal del ejecutor reutilizada; sin nueva batería, E2E, commit ni push.

**Propuesta de esta segunda pasada** (fila `yari-definition`, única clave):
`C:\Users\Pholtergate\AppData\Local\Temp\r13g\r13-yari-grips.json`; paquete validado:
`C:\Users\Pholtergate\AppData\Local\Temp\r13g\r13-yari-grips-prepared.json`. `prepare` →
`PREPARE_EXIT=0` (sólo `pending: {}` y `verification`, más `append_notes` con la justificación
concreta); `apply` **sin** `--write` → `APPLY_EXIT=0` sobre la instantánea real (4.556 claves,
campos protegidos intactos, comentarios previos preservados). El registro **no** se escribió:
`md5 cb33527b3e3b471ee420e3efda0f0a4c` idéntico antes y después, sin `.csv.lock`, sin tocar plan,
índice ni registros compartidos, sin commit ni push. Preview conservado:
`…\Temp\r13g\apply-preview.txt`; md5 previo: `…\Temp\r13g\csv-before.txt`.

Propuesta de la primera pasada: `C:\Users\Pholtergate\AppData\Local\Temp\r13\r13-changes-v2.json`;
paquete validado: `C:\Users\Pholtergate\AppData\Local\Temp\r13\r13-prepared-v2.json`.
Cinco claves `(id, clause_id)`: Belaying Pin `melee-profile--scope--melee-profile`; Sunstaff `whole`;
Yari `yari-definition`; Stickfire y Vermin Pot `item`. `prepare` y `apply` (sin `--write`):
`PREPARE_EXIT=0`, `APPLY_EXIT=0`, 4.556 claves, campos protegidos intactos, notas sólo añadidas. Las
justificaciones concretas van dentro de `append_notes` de cada fila (no sólo anunciadas). El CSV
compartido **no** se escribió: no hay `.csv.lock`, no se tocó el plan, el índice ni ningún registro
compartido, y no hay commit ni push.

## Resultados exactos

### Segunda pasada: empuñaduras del Yari (2026-10-16)

- `tests/python/construction/test_t13_weapon_variant_profiles.py` +
  `tests/python/construction/test_shared_eligibility.py` (un solo mando) → **45 passed**, EXIT=0; la
  segunda incluye la comprobación de que el bundle regenerado coincide con la huella de sus fuentes TS.
  Los cinco casos nuevos comprueban, en la interfaz del usuario y no en un build libre: declaración del
  objeto, oferta y elección de ambas empuñaduras al mismo precio, aceptación de cada una con una única
  posesión, transporte al `compile_fighter` del destinatario, propiedades modulares (parry, dos manos,
  golpea primero vía `phases.resolve_priority`), rechazo de la mano secundaria incompatible y ausencia
  de acceso para otro perfil de la banda.
- `tests/python/ui/test_catalogue.py` (consumidor directo de la capa de oferta y de `cost`) → **15
  passed, 1 failed**, EXIT=1. El único fallo es un texto de razón de habilidad
  (`'Two or more enemies and All Alone tests are outside resolved 1v1 duels.'` frente al esperado
  `'Its effect requires two or more opponents; …'`) en datos de skills de otro trabajo del mismo
  checkout: **no** toca ningún id de Yari, ni la oferta, ni el coste.
- `tests/python/knowledge/test_equipment_source_absence.py` → **1 failed, 1 passed**, EXIT=1. El fallo
  es `bronze_breastplate is no longer out_of_scope` y **sí** está atribuido: es un cambio integrado de
  la entrega C07b («Peto de bronce (Khemri): `out_of_scope` → `armour.light-armour`»), la misma clase
  de fila que sale del conjunto de ausencia que esta entrega documentó para `yari`. No es un fallo de
  esta conexión: `yari` ya había salido de ese conjunto en la pasada anterior y ningún otro caso del
  archivo toca las empuñaduras.
- `npm run check:eligibility` → *Shared eligibility bundle is current*, EXIT=0; `npx tsc --noEmit`
  (`packages/typescript`) → EXIT=0 sin salida.
- Contrato editorial: `editorial_schemas.problems_of('catalog-items.yaml.schema.json', …)` sobre el
  registro real de `yari` → **sin problemas**; con `implemented` + empuñadura → sin problemas; con
  `out_of_scope` + empuñadura → rechazado (`mechanic_id` requerido y `combat_status` *implemented*
  esperado); con un miembro inventado → rechazado por `additionalProperties`.
- Guarda de datos: un objeto `implemented` con `alternate_mechanic_ids: [weapon.ghost]` en un KB
  sintético hace fallar `load_simulation_mappings` con «item probe declares an unexecutable grip».
- `generate_knowledge_web._build_items('mordheim')` (462 filas) publica la fila `yari` con
  `alternate_mechanic_ids` sin excepción: el artefacto web conserva la declaración.
- Salidas conservadas: `…\Temp\r13g\evidence\pytest-construction.txt`, `pytest-ui-catalogue.txt`,
  `probes.txt`, `npm-and-tsc.txt`.

### Primera pasada (sin cambios en esos archivos)

- `tests/python/construction/test_t13_weapon_variant_profiles.py` → **15 passed**, EXIT=0.
- `tests/python/knowledge/test_equipment_source_absence.py` + el archivo anterior → **17 passed**, EXIT=0.
- `tests/python/combat/modular/test_local_modifier_variants.py -k armen` → **1 passed, 362 deselected**,
  EXIT=0 (el kit canónico de Armen Abbas con stickfire/vermin pot sigue sin bloquear el duelo ni
  aportar comportamiento).
- `tests/python/knowledge/test_catalog.py` + `test_editorial_schemas.py` → 334 passed, **19 failed**,
  EXIT=1. Ningún fallo nombra un archivo de esta entrega: son colecciones de hireling sin fila en
  mappings, una defensa que no compila y validaciones editoriales de `mechanics/close-combat.yaml`,
  `execution.yaml` y del registro de manuales, en un checkout compartido con ediciones en curso.
  **Origen no determinado**; no se abrió auditoría ni comparación contra HEAD.
- Prueba de ruta (salida conservada): `C:\Users\PHOLTE~1\AppData\Local\Temp\r13\out\probe-r1.txt`
  (`belaying_pin` y `sunstaff` sin mapping; `sunstaff_lustria` intacto; `yari` →
  `weapon.yari-one-handed` + «Yari (one-handed)»). Texto original recuperado:
  `...\Temp\r13b\rel2.txt`. Salidas de pruebas: `...\Temp\r13\out\tests-variant2.txt`,
  `tests-absence2.txt`, `tests-armen.txt`, `tests-catalog.txt`.

## Límites y disposiciones que no cambian

- E2E no se ejecutó, colectó, investigó ni editó; tampoco comandos que los incluyan.
- Suites TS/Vitest no ejecutadas (fuera del presupuesto de la tarea): el cambio del módulo compartido se
  verificó por su consumidor real en Python (el bundle) y por `tsc --noEmit`; un golden test de Vitest
  que liste el equipo del Silent Hunter no se comprobó aquí.
- El bundle `_eligibility.js` es un artefacto generado: al regenerarlo recoge el estado **actual** de
  `index.ts`/`bridge.ts`, que incluye ediciones concurrentes de otro trabajo del mismo checkout. La
  huella `Source SHA256` coincide con esas fuentes (por eso `check:eligibility` informa *current*), que
  es el estado coherente del módulo compartido, no sólo mi cambio.
- `test_knowledge_artefact.py` → 21 failed, EXIT=1, con el primer fallo dentro de
  `_build_rules_prose`/`load_rules_catalog` (catálogo de reglas compartido, ajeno a los ítems): la
  suite no llega siquiera a construir la sección de items, así que su estado no es atribuible a esta
  entrega. La ruta de items se comprobó directamente con `_build_items` (arriba).
- El fallo heredado `warband-groups` (25 vs 24) de `test_campaign_loaders.py` no se reejecutó (no hay
  causa nueva); sigue como estaba, no atribuido a R13.
- Rows 1/3 (perfiles a distancia), 9 (crossbow pistol), 12/13 (inscripción/aprendizaje de runas):
  exclusiones por contenido ya justificadas en la entrega anterior, sin cambio.
- `sunstaff_lustria` se deja como está por instrucción expresa de no extender la decisión a variantes
  de otra fuente; su fuente sí documenta una mitad melee, ajena a esta fila.
