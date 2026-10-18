# H02 — Kits y variantes individuales de personajes

**Estado: bloque terminado, 2026-10-17.** No se ejecutaron E2E, suites globales, parity ni
comparaciones con HEAD. Las 19 filas pendientes de la selección H02 quedan implementadas o
reconciliadas e integradas por el coordinador.

Integración: diecinueve cierres con snapshot completo, prepare/preview y control
concurrente; 4.556 claves, textos, huellas y notas conservados, verificación
anterior acumulada. Evidencia: `%TEMP%/h02-coordinator-07z9u8j6/`. Resultados
focales del ejecutor reutilizados, sin repetir pruebas. La expectativa antigua
de admisión de Drenok sigue señalada abajo y no se presenta como corregida.

## Capacidades (implementadas frente a reutilizadas)

- **Kits compartidos de Dark Elf Corsairs (nuevo).** `fixed_equipment` de Sorceress y Beastmaster
  declara las piezas impresas y el compilador las resuelve por la ruta del perfil de banda: la
  cualificación `material.dark-elf-blade` reviste sólo la hoja principal, la daga secundaria sigue
  siendo normal, la armadura ligera da 6+ y el beastlash ocupa la mano secundaria. La oferta expone
  exactamente esas piezas y operadores, sin `equipment_list` ni acceso genérico.
- **Elecciones impresas (nuevo).** `resolveHirelingKit` admite `choices` con repetición y
  `optional_items`; el compilador, ante arma omitida, toma la primera opción impresa en lugar de la
  daga libre. Gaoler (mayal o dos martillos/garrotes), Black Orc (dos hachas o arma a dos manos) y
  Centauro (espada o lanza) compilan cada alternativa como kit completo y rechazan mezclas.
- **Johann (nuevo).** Crimson Shade es `optional_items`: sin elección no existe; con
  `preparation_ids` se añade una vez y el Black Lotus automático sigue aplicado una sola vez.
- **Objetos particulares (nuevo/conexión).** Guadaña ceremonial con +1 F y dos manos; Beastlash con
  Fear sólo contra animales; recubrimiento de ajo contra Vampiros (fallo de herida a 6 natural sólo
  contra no-muerto vampírico); capa inicial del Bearman restringida a su perfil y sin efecto; Candle
  Tree resuelto al candelabro arcano propio de la Hermana de Sigmar.
- **Nicodemus (nuevo).** `weapon.wizards-staff` declara los dos modos impresos: a dos manos como
  clava con parada de broquel, o en la izquierda como clava normal sin parada. Mano secundaria activa
  rechazada; casting y espada de conjuro siguen excluidos.
- **Personas (conexión/reutilización).** Luthor queda como perfil separado normalizado con su kit
  propio; Ulli reutiliza la publicación de R13 sin código nuevo; Horseman permanece `out_of_scope`
  como entidad compuesta jinete-montura, sin perfil desmontado inventado.
- **Equipo fijo (nuevo).** Las dos reglas generales se compilan como
  `compiler.hireling-fixed-equipment`; el compilador rechaza un hireling sin la cláusula y el
  matcher rechaza propiedad ajena al kit impreso. No se implementó compraventa, transferencias ni
  campaña.
- **Ulli y Duelling Pistol (reutilizado).** El kit del Witch Hunter resuelve la pistola de duelo
  canónica y su alternativa ballesta-pistola como kits completos; no se implementó disparo.

## Disposición de las 19 filas

| Fila (clave original) | Disposición |
|---|---|
| `dark-elf.../profiles/4` kit | Cerrada: kit de la hechicera por ruta de perfil |
| `dark-elf.../profiles/5` kit | Cerrada: armadura, hoja y beastlash |
| `trading-post.../items/132` nota | Cerrada: restricción por perfil del Bearman |
| Johann `crimson-shade` | Cerrada: opción de kit, no efecto permanente |
| Johann `poisoned-weapons` | Cerrada: un único Black Lotus en el arma impresa |
| Marianna `garlic` | Cerrada: recubrimiento sólo contra Vampiros |
| Ulli `named-consequences` | Reconciliada: R13 ya publicado; sin código nuevo |
| Nicodemus `staff-modes` | Cerrada: dos modos, mano ocupada y parada |
| Luthor `personas` | Cerrada: perfil separado normalizado |
| Horseman `profile` | Resuelta por alcance: entidad compuesta excluida, sin invención |
| Witch Hunter `Duelling Pistol` | Cerrada: elección canónica del kit |
| Gaoler `equipment_choice` | Cerrada: mayal o dos contundentes |
| Black Orc `equipment_choice` | Cerrada: dos hachas o a dos manos |
| Centauro `equipment_choice` | Cerrada: espada o lanza |
| Priest of Morr `ceremonial scythe` | Cerrada: +1 F y dos manos |
| Bog Hunter `beastlash-beastbane` | Cerrada: Fear contra animales |
| Sister of Sigmar Candle Tree | Cerrada: candelabro arcano propio |
| Hired Sword `fixed-equipment` | Cerrada: admisión y rechazo de propiedad extra |
| Dramatis Personae `fixed-equipment` | Cerrada: mismo consumidor y matcher |

## Paquete CSV preparado (sin aplicar)

`%TEMP%/h02-prepared.json`: 19 cambios `(id, clause_id)`, sólo `pending`, `verification` y notas
añadidas; huella `df1622b5…` idéntica al CSV actual en el momento de preparar. `apply` sin
`--write` validó el paquete con EXIT=0 y el CSV conservó esa misma huella; no se ejecutó
`apply --write` ni se editó el CSV. La integración corresponde al coordinador.

## Archivos propios

- `sources/knowledge/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml`
- `sources/knowledge/catalog/hirelings/dramatis-personae/{core,grade-1a,grade-1c,rules}.yaml`
- `sources/knowledge/catalog/hirelings/hired-swords/{grade-1b,grade-2b,rules}.yaml`
- `sources/knowledge/catalog/campaign/trading-post.yaml`
- `sources/knowledge/catalog/items/weapons-close-combat.yaml`
- `sources/knowledge/catalog/mechanics/{close-combat,execution}.yaml`
- `packages/python/roster-construction/mordheim_construction/{compiler,contracts,combat_packages}.py` y
  `_eligibility.js` regenerado
- `packages/typescript/domain/eligibility/index.ts`
- `packages/python/combat-engine/mordheim_combat/{phases.py,modular/contexts.py,modular/attacks.py}`
- `tests/python/construction/test_h02_kits_and_variants.py` (nuevo)

## Evidencia mínima

```
python -m pytest tests/python/construction/test_h02_kits_and_variants.py tests/python/construction/test_t13_hireling_admission.py::test_ulli_compiles_with_his_printed_kit_and_only_his_admitted_skills tests/python/construction/test_t13_hireling_admission.py::test_the_pair_keeps_its_joint_identity_and_ulli_gains_no_campaign_hire -q
20 passed
``` Cubre oferta canónica, kit completo, alternativas legales, mezclas
prohibidas, destinatario del objeto, consumo único del veneno y propiedad del equipo fijo.

## Bloqueos

Ninguno funcional dentro de H02. Durante la sesión otro frente mantuvo temporalmente inválido
`catalog/mechanics/close-combat.yaml`; se releyó una vez tras su escritura y la comprobación final
pasó sobre el estado íntegro. No se persiguieron bloqueos ajenos ni se tocaron sus fragmentos.

Fallo externo observado al ampliar el consumidor del compilador: en
`test_t13_hireling_admission.py` (35 passed, 1 failed) el caso
`test_a_blocked_equivalence_names_its_own_blocker` sigue esperando el bloqueo
`intrinsic duel clauses are pending` para Drenok, pero el árbol compartido ya contiene la
implementación de sus reglas (`weapon.icefang-axe`, `mechanic.drenok-berserker`,
`defence.sabertooth-hide`) en `grade-1b.yaml`, fuera de H02. Ahora la negativa correcta es la del
matcher de kit al pedir un arma a dos manos que no es su hacha única. No se editó ni la prueba ni el
dato ajenos; queda para el frente que posee Drenok.
