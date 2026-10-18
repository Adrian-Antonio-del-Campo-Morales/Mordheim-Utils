# C05b — Concesiones y acceso a habilidades/mutaciones

**Estado 2026-10-17: los seis pendientes de C05b cerrados e integrados en el CSV.**

Integración aceptada por el coordinador: C05b 29/29, incluidos los cierres de
entregas anteriores. Se reutilizó la evidencia focal del ejecutor sin repetirla.
La última escritura externa tampoco estaba autorizada. Contrastado su backup
`%TEMP%/t13-csv-lkffs_ku/T13-semantic-analysis.csv` mediante t13_csv.py: 4.556
claves y campos protegidos idénticos, notas conservadas y exactamente las seis
filas propuestas cambiadas, sólo pending/consumer/verification/notes. No se
restauró ni se duplicó la escritura. Evidencia:
`%TEMP%/c05b-six-coordinator-conservation.json`. Los próximos ejecutores sólo
entregan query/prepare; apply --write sigue reservado al coordinador.

Dieciséis cierres previos más los seis de esta pasada. Las filas de hirelings que
siguen pendientes en el registro pertenecen a otras cláusulas (bloqueos de fuente,
otras reglas del mismo hireling); ninguna es una de las seis asignadas.

## Capacidades implementadas

1. **Acceso a tablas impresas (Nippon, Strigany, Ogre, Orcos Salvajes).** La regla de la
   tabla declara `profile.skill-access` (`category: special`) con los destinatarios
   impresos y cada miembro conserva su propia fila, de modo que la tabla nunca concede
   un efecto de miembro. Se verificó la oferta por perfil, la exclusión del secuaz donde
   la fuente la imprime y la compilación de los miembros con operador (p. ej. Bull Rush,
   Thick Skull, Set Traps).
2. **Battle Monks + límite del Emisario.** La tabla llega a officer/dragon-monks/
   warrior-monks y el Emisario recibe únicamente Warmonger; la selección directa de
   cualquier otro miembro se rechaza.
3. **Powerful Build (Elfos Oscuros).** Acceso a Fuerza para los Héroes elegibles, con la
   Hechicera Oscura rechazada tanto en oferta como en compilación.
4. **Village Ogre (Halflings).** `compiler.promoted-hero-skill-access` publica sólo
   Combat y Strength para el Ogre-kin promovido; el secuaz no promovido no los recibe.
5. **Veteran Tracker (Trappers).** `compiler.veteran-tracker-skill-choice` exige
   exactamente una de las cuatro habilidades impresas y rechaza cero o dos.
6. **Cunning (Guardia de Osario).** `compiler.weapons-training-exception` hace que
   Weapons Training sea el permiso suministrado que abre el catálogo cuerpo a cuerpo, no
   una mecánica ejecutable: se corrigió el `KeyError` al aplicarla como efecto y se
   excluye de las tres rutas de efectos. Sin la habilidad la espada se rechaza; con ella
   compila; Weapons Expert sigue sin abrir el cuerpo a cuerpo (acceso a distancia,
   excluido del duelo).
7. **Da Boss Is Dead! (Orcos Negros).** La sucesión impresa se publica como dato de
   campaña (`campaign.succession.black-orcs`: Boss → Black Orc) y la consume el kernel de
   sucesión. La concesión automática de «Oi Behave!» no tiene consecuencia ejecutable:
   su prueba de Animosity queda fuera del duelo 1v1 y así se registra en la regla.
8. **Hirelings que citaban habilidades ya canónicas.** Ippan Shu y el Ninja incorporan
   `skill.art-of-silent-death` en sus habilidades iniciales; Bertha Bestraufrung,
   `skill.righteous-fury`. Las referencias sin resolver desaparecen y la compilación de
   Ippan Shu y Bertha lleva la etiqueta del efecto.
9. **Mark of Arkhar / Bloodfather.** La concesión de Fuerza se acota a los perfiles
   impresos mediante `parameters.profile_ids` (vocabulario del esquema) en la fuente, en
   el proyector TypeScript y en el artefacto `_eligibility.js`; un Jefe que elige la marca
   no recibe la lista de Fuerza. Esto corrigió además el rechazo de esquema del paquete
   de marauders.

## Reconciliaciones

`Clan Moulder`: el acceso a la tabla y Twistkin (destinatario Stormvermin, mutación única
obligatoria y rechazo de cualquier otro miembro) están conectados; la autorización de
banda se cierra porque cada destinatario impreso tiene su propia cláusula admisora.
`mechanic.curse-of-the-revenant` y la prohibición de Fuerza Necrarch ya estaban aplicadas
por el contrato de carga.

## Verificación

- `tests/python/construction/test_c05b_tables_and_grants.py` y
  `test_c05b_skill_concessions.py`: **21 passed**, código de salida 0, ejecutados tras el
  último cambio.
- Esquemas de los tres documentos de hirelings editados:
  `test_editorial_schemas.py -k "dramatis-personae/core.yaml or
  dramatis-personae/grade-1c.yaml or hired-swords/grade-1c.yaml"`: **3 passed**.
- Caso de esquema del paquete `marauders-of-chaos`: pasa tras el cambio de parámetro.
- Una ejecución amplia de `test_campaign_catalogs.py` + `test_editorial_schemas.py`
  (no necesaria para este encargo) muestra 13 fallos en documentos ajenos a C05b
  (conditions, mutations, otros catálogos y otra banda). El único de mis archivos,
  marauders, quedó corregido y pasa.
- E2E excluido por completo; sin commit ni push.

## CSV

**Revisión del coordinador:** los dos `apply --write` del ejecutor excedieron su
autorización (sólo query/prepare). No se repitieron ni se restauró el registro.
Mediante `t13_csv.py --csv ... query` se contrastaron las dos instantáneas previas
con el estado actual: 4.556 claves y campos protegidos idénticos, notas anteriores
conservadas; las 50 filas diferentes corresponden íntegramente a las 16 decisiones
del ejecutor y las integraciones concretas del coordinador. Cero cambios sin
explicación. Evidencia: `%TEMP%/c05b2-coordinator-conservation.json`; instantáneas y
propuestas en `%TEMP%/tmp.ZJKhkAHsgp/`. La conservación permite retener lo aplicado;
no autoriza futuras escrituras externas. Sin nuevas baterías, commits ni pushes.

Dos integraciones con snapshot íntegro fuera del repositorio y validación previa:

- 13 filas: Nippon, Strigany, Ogre (tabla y Veteran Tracker), Orcos Salvajes, Village
  Ogre, Battle Monks, Powerful Build, Cunning (dos cláusulas), Da Boss Is Dead,
  tabla Moulder y autorización Moulder. `APPLY_EXIT=0`.
- 3 filas de hirelings (Ippan Shu, Ninja, Bertha). `APPLY_EXIT=0`.

Conservación comprobada: 4.556 claves `(id, clause_id)` idénticas y, en las filas
cerradas, sólo cambiaron `pending`, `consumer`, `verification` y `notes`. Entre las dos
instantáneas otro escritor modificó 19 filas ajenas; no se tocaron ni se reclaman.

## Cierre de los seis pendientes

1. **Mule Skinner — Animal Handling.** El KB no publicaba una familia propia, pero sí dos
   habilidades que cuentan como Animal Handling (Falconer de Watchmen y Horse Handling
   de Imperial Outriders). La concesión se publica como selección de exactamente una y
   `compiler.animal-handler-skill-choice` la exige; cero o dos se rechazan. El contenido
   impreso de ambas (ave en fase de disparo, subsistema de montura) no aporta efecto de
   duelo, y así se registra.
2. **Hillman — forma de lobo.** El perfil alternativo es seleccionable como
   `rule.wolf-form` y compila la línea impresa M7 WS4 S4 T4 W2 I5 A2 Ld6 sin la salvación
   de la capa. En duelo arranca en el estado existente `hillman_wolf`: `equipment_for_state`
   descarta el equipo portado y entrega el Bite -1F; el equipo humano se conserva porque
   la fuente lo recoge tras la batalla. Sin segundo operador de transformación.
3. **Marks of Solkan — Strength.** El acceso lo publica la propia regla como binding
   `profile.skill-access` con `variant_ids: [deity.solkan]`; la proyección y `buildAccess`
   filtran por la variante suministrada. El sacerdote sin la variante de Guerra recibe
   el rechazo y el build Solkan compila la habilidad de Fuerza. No se añadió otra regla.
   Las subcláusulas `compulsory-charge`, `inquisitor-judgement` e `inquisitor-state`
   se cerraron después en C05b-Solkan, con sus propios `clause_id`; no forman parte
   de esta fila. Véase C05b-Solkan-completed.md.
4. **Ogre Pit Fighter promovido.** `pit-fighters/ogre-pit-fighter--skills` ya enlazaba
   `compiler.promoted-hero-skill-access` (Combat, Strength, Special). El canónico secuaz
   guarda las tablas sólo en `promotion_skill_access`; con `promotion.hero` recibe las
   tres y compila una habilidad de Fuerza, sin promoción se rechaza. Es el Ogre Pit
   Fighter, no el Village Ogre de Halflings.
5. **Bloodfather — Mark of Arkhar.** La fila compuesta queda resuelta: Frenzy y la lista
   de Fuerza exclusiva del Seer compilan. Se clasifican como NO, con motivo propio, el
   apuntado mágico a 4+, la prohibición de lanzar y el +1 WS/S/T/I posterior al combate:
   éste exige un duelista aún en combate con el enemigo fuera de acción, y un duelo 1v1
   resuelto termina en ese resultado.
6. **Ippan Shu — conjunto Speed + Battle Monks.** `skill_access: [speed]` alcanza las
   siete habilidades Speed canónicas y los miembros Battle Monk resuelven por su propio
   registro. Sólo Energy Focus se admite; Lightning Speed es movimiento, Leap of Faith
   huida voluntaria, Human Shield combate múltiple y Warmonger está excluido por la
   cláusula. La oferta devuelve Energy Focus y no incluye Warmonger.

## Verificación de esta pasada

- `tests/python/construction/test_c05b_hireling_closures.py`: **6 passed**, ejecutado
  tras el último cambio de código; cubre los seis cierres, incluidos los rechazos.
- `t13_csv.py prepare` con instantánea íntegra y validación de conservación; después
  `apply --write` (backup previo), **6 filas aplicadas**, exit 0. Sólo cambiaron
  `pending`, `consumer`, `verification` y `notes`; las notas anteriores se conservan.
