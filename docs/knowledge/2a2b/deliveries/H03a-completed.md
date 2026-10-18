# H03a — Proyección y psicología de hirelings

**Estado: H03a cerrado; Gwen/leadership-distraction integrada por el coordinador,
además de los quince cierres previos y las cláusulas Solkan ya resueltas.**
El remate del coordinador está cerrado: el turno
perdido ya no sólo vacía el pool de ataques, también impide las acciones propias
opcionales de ese turno (Herb Lore, Rousing Sermon), conservando efectos pasivos,
pruebas obligatorias y respuestas del turno ajeno. Base compartida `2A2B`, HEAD
`a1f92653`, sin commits ni pushes.

Integración final 2026-10-17: una fila aplicada con snapshot completo,
prepare/preview, conservación de 4.556 claves/textos/huellas/notas y control
concurrente. Consumidores y evidencia anteriores acumulados; salida de ocho
casos del ejecutor reutilizada sin repetir pruebas. Evidencia de integración:
`%TEMP%/gwen-final-coordinator-hqzfe_bn/`.

Integración del coordinador, 2026-10-17: quince cierres aceptados con snapshot
completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente.
Se rechazó el cambio a scope NO de `leadership-distraction` mientras faltara el
texto completo; esta entrega recupera ese texto e implementa el resultado
suministrado. La penalización opcional de Liderazgo no se reabrió.

## Interpretación sustentada (Gwen / Massively Built)

Párrafo completo de la fuente referenciada —Fanatic Online 89, p. 2
(`https://broheim.net/downloads/fo/89RunnersUp.pdf`), recuperado del PDF y conservado
como texto extraído en `%TEMP%/fo89.txt`:

> «Massively Built. As any visitor can tell you, Gwen is a massive woman. During the
> shooting phase, if she is not in close combat, and hasn't run, she may "show her
> stuff" to any visible male target within 12". The target model must make a Ld check
> or lose his entire next turn as he stands dumbfounded by her impressive bulk.
> Naturally, females, skaven, orcs, and other non-human races are immune to this.
> While most undead are immune, Vampires, and Necromancers are not. Elves and Dwarves
> are affected, though not necessarily gaping in awe as much as disgust. (Optional)
> Any Slaaneshi cult members who fail their leadership check must take a further -1 Ld
> penalty for the remainder of the game.»

Lectura: el resultado impreso es **«lose his entire next turn»**, no una pérdida
limitada a movimiento o disparo. La fuente no restringe esa consecuencia ni la
identifica con Stunned: el objetivo queda «dumbfounded» y pierde el turno siguiente
completo. Por tanto el productor excluido (la prueba en fase de disparo, con alcance y
visibilidad) no excluye la consecuencia individual. Destinatarios impresos: varones
humanos, Elfos y Enanos afectados; mujeres, Skaven, Orcos y otras razas no humanas
inmunes; Vampiros y Nigromantes **no** inmunes pese a la inmunidad general de los
no-muertos. La penalización opcional de Liderazgo es una cláusula aparte, ya cerrada.

## Implementación

- **Estado suministrado.** `condition.massively-built-lost-turn` es una condición
  canónica nueva (`catalog/rules/conditions.yaml`, binding `mechanic`) cuyo efecto es
  la etiqueta homónima; se registra en `catalog/mechanics/execution.yaml` (effect-set
  pasivo sobre el portador) y en el catálogo `catalog/mechanics/close-combat.yaml`.
  La aporta el llamador sobre el objetivo afectado, igual que
  `condition.massively-built-leadership-penalty`; el duelo no produce la prueba.
- **Consumo único en el turno propio.** `FighterState.massively_built_lost_turn` se
  inicializa desde la etiqueta en `initialize_fighter`. `resolve_round` lee el hecho
  pendiente una vez al principio, eligiendo al participante activo con
  `state.first_player_turn`, y conserva esa lectura local durante todo el turno.
- **Acciones propias compuertas.** Esa misma lectura impide ofrecer o ejecutar las
  declaraciones voluntarias que el flujo resuelve antes del pool: Herb Lore, Rousing
  Sermon, la elección de poder del Djinn, la sea shanty del propio turno, el crude
  belch del Ogro y la evitación voluntaria de la carga Impetuosa. Durante el turno
  perdido no se pide decisión, tirada ni gasto de ninguna de ellas. La postura de arma
  y la danza de sombras siguen siendo selecciones de fase de ambos duelistas, no
  acciones del turno.
- **Gasto y contratos conservados.** El estado se gasta en el paso de ataque, cuando
  todos sus consumidores ya lo han leído: la contribución de ataque de esa fase se
  anula antes de capturar el remanente de Deathblow y la marca se limpia ahí mismo.
  Los contratos pasivos y obligatorios siguen resolviéndose (recuperación de
  Stunned/Knocked Down, pruebas de Miedo y Estupidez, recuperación del Renacido,
  alquimia, Hambre Negra). El turno del otro jugador no se toca: la represalia sigue
  intacta, el objetivo nunca pasa a Stunned ni a Knocked Down y no hay segundo disparo
  ni disparador automático repetido.
- **Regla de Gwen.** El efecto de la cláusula en
  `catalog/hirelings/dramatis-personae/grade-2a.yaml` pasa a `leadership-distraction`
  (scope NO, sin binding) con la razón de que el resultado pertenece al objetivo
  suministrado, no al perfil de Gwen; la prueba, el alcance y la visibilidad siguen
  fuera del duelo. La penalización opcional queda como estaba.
- **Exclusiones impresas.** La elegibilidad (sexo, raza, excepciones Vampiro y
  Nigromante) permanece en el hecho suministrado: el motor no añade una inmunidad
  genérica que borre esa excepción, ni la re-deriva.

## Propuesta de la fila (sólo `prepare`, sin `--write`)

`source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/unclassified`
/ `leadership-distraction`:

- `clause_scope` YES (sin cambio), `relation` `equivalent`.
- `effect_id` `proposed.skip-next-own-turn` → `condition.massively-built-lost-turn`.
- `semantic_contract`: resultado = turno siguiente completo perdido; consumo único en
  el turno propio del objetivo; represalia del otro turno intacta; nunca Stunned;
  destinatarios y excepciones impresas.
- `pending`: `{}` (completo).
- `consumer`: `state.initialize_fighter`, `rounds.resolve_round`,
  `compiler.compile_fighter`, `conditions.resolve_supplied_conditions`.
- `verification`: `executed` + el archivo y el nodo de prueba + PDF/página de la
  fuente + condición + consumidores.

Paquete: `%TEMP%/h03a-gwen-proposal2.json`, snapshot
`sha256 3d2e8e349d051cb03b69800235c88639b372a3ffcfe4d6219c6939523f588333`
(la misma base que la copia previa preparada por el coordinador), **1 cambio**.
`apply` en seco validó snapshot y conservación con EXIT=0 y el CSV conservó la misma
huella (salida en `%TEMP%/h03a-gwen-apply2.txt`); **no se ejecutó `--write`** y la
fila sigue con su valor anterior en el CSV.

## Archivos propios

`packages/python/combat-engine/mordheim_combat/modular/state.py` y
`.../rounds.py` (estado y consumo),
`sources/knowledge/catalog/rules/conditions.yaml`,
`sources/knowledge/catalog/mechanics/execution.yaml`,
`sources/knowledge/catalog/mechanics/close-combat.yaml`,
`sources/knowledge/catalog/hirelings/dramatis-personae/grade-2a.yaml`,
`tests/python/combat/modular/test_h03a_hireling_psychology.py` y esta entrega.
No se editó el CSV ni el resto de filas integradas.

## Evidencia mínima

`python -m pytest tests/python/combat/modular/test_h03a_hireling_psychology.py -q`
→ **8 passed**, EXIT=0 (`%TEMP%/h03a-gwen-actions-final.txt`). El caso
`test_massively_built_supplied_loss_costs_the_recipients_own_turn_once` cubre
destinatario, momento, consumo, caducidad y acciones propias: el objetivo está herido
y lleva Herb Lore y Rousing Sermon, de modo que en su turno perdido las fuentes
estrictas fallarían ante cualquier decisión, tirada o gasto de esas acciones; sólo se
consumen la tirada de prioridad y el ataque del adversario (1 ataque), no queda gasto
de sermón y la condición sigue STANDING. En el turno ajeno previo el objetivo sigue
atacando (2 ataques, estado pendiente), en la fase siguiente vuelve el intercambio
normal (2 ataques) y en su siguiente turno propio Herb Lore y el Sermón se vuelven a
ofertar (decisión, tirada y gasto presentes), lo que demuestra que la compuerta es el
turno y no una retirada permanente de los operadores. El caso concurrente
`test_the_lost_turn_offers_no_optional_own_action` añade la prueba de decisiones
vacías en el turno perdido. Los otros seis casos H03a siguen pasando.

Comprobación de la KB: los cuatro YAML afectados cargan, la condición resuelve por
`condition_ids` y la regla de Gwen declara
`massively-built-shooting-producer` / `leadership-distraction` /
`massively-built-optional-leadership`.

## Límite concreto

`tests/python/knowledge/test_catalog.py` y `test_editorial_schemas.py` ya fallaban en
el árbol compartido por asuntos de otras familias (`banshee--cold-steel`, conteo
3108/2908, `norse-explorers-btb/wolves--animals`, `skills/114 kind`,
`skills/329 effect_i18n`, `weapons/100-101 rules_source_url`, `true_grit`); ninguna
de esas listas nombra las filas de Gwen ni la condición nueva. No se repararon por
estar fuera de alcance. Al ampliar el consumidor, el archivo de admisión mostró un
fallo de otra familia (Drenok, expectativa de bloqueo anterior a la implementación de
sus reglas); no se reparó por ser ajeno y las filas H03a no dependen de él.
