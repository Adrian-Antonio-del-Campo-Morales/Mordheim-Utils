# Paquetes de trabajo pendientes del motor modular

Corte de asignación: **2026-10-15**, rama `2A2B`, HEAD `a1f92653`, árbol compartido con cambios locales. Documento de asignación solicitado por el usuario; no sustituye al CSV ni abre otro registro de estados.

Se han leído las descripciones y contratos de las **597 filas pendientes**: **579 YES**, **11 NO**, **6 UNCLASSIFIED**, **1 LATER**. Son cláusulas, no 597 capacidades ausentes. La agrupación es manual por consecuencia/consumidor; la compresión de selectores y la comprobación de cobertura son mecánicas. No se ha ejecutado una auditoría funcional de todas ellas ni se han cerrado filas.

Hay **31 paquetes de referencia**. Algunos son conjuntos de variantes del mismo mecanismo; los grupos H01/H03 y el residual C15 se señalan expresamente como no aptos para un encargo completo indiscriminado. El número de paquetes tampoco es una estimación de horas. Una etiqueta `assessment`, `data` o `connection` no determina si falta comportamiento: hay que seguir la ruta concreta y editar donde falte.

## Orden y asignación inmediata

1. **M00 integrado**: Misericordia del Conde está cerrada; véase [la entrega](deliveries/M00-completed.md). No reasignarla. Los conteos inferiores conservan el corte inicial.
2. **C09 integrado:** diez cláusulas cerradas. Alchemist se completó con la decisión humana de un intento al inicio de cada turno propio. No reasignar estas capacidades ni dedicar un encargo a Movement.
3. **C14a completo:** bendición, Honing y los tres resultados suministrados de Master Craftsman conectados al ejemplar físico. No reasignar el paquete.
4. **Frente de datos/construcción: C03a, C03b o C03c**, uno por encargo. Se pueden preparar bindings en fuentes disjuntas mientras trabaja un agente en el runtime; si necesitan cambiar elegibilidad compartida, se entregan para integración o se reserva ese consumidor.
5. Continuar C01/C02/C04/C05 por paquete, y C06/C08/C10/C11/C12/C13 según el consumidor disponible. Priorizar consecuencias no exclusivas de hirelings. Los H quedan después, salvo dependencia real compartida.
6. C07/C15 contienen trabajo ya implementado o límites de fuente/alcance: no convertirlos en otra campaña de revisiones. Reconciliar con evidencia existente y avanzar al hueco concreto. Las 18 filas fuera de YES no autorizan ampliar el duelo.

## Reglas del encargo que debe repetir cada prompt

**IMPLEMENTAR es la actividad principal.** Encargar un resultado utilizable de configuración → `compile_fighter` → `initialize_duel` → `resolve_round`, con las variantes seleccionadas. No pedir «audita todos los perfiles» ni entregar sólo estados/bindings. Si el comportamiento existe, reutilizarlo y resolver su conexión; no fabricar código ni pruebas. Una regla compuesta no se cierra por resolver sólo una parte.

- La selección inferior delimita qué filas leer. Consultar el CSV actual con `python -X utf8 tools/knowledge/t13_csv.py query`; leer manualmente las diferencias y referencias. Los selectores no deciden equivalencia ni alcance. No reauditar las 4.556 filas.
- Casos mínimos afectados: objetivo habitual 2–3 discriminadores nuevos por mecanismo, reutilizando los existentes; no una batería nueva por fila. Inicialmente como máximo tres archivos directamente afectados, sin esconder una batería amplia en parametrización. Ampliar sólo por fallo nuevo o riesgo concreto no cubierto. Conservar la primera salida fuera del repositorio; no relanzar para contar o recuperar resultados.
- **E2E completamente excluidos**, incluido cierre: no ejecutar, colectar, investigar, reparar ni editar harness/corpus/tests; cancelar una ejecución propia accidental. Sin suites amplias, inventarios o auditorías globales, parity, cobertura, vectorial/nativo ni T14. Sin implementación de campaña, grupos, terreno, disparo, casting, monturas ni escapes que dejan el duelo sin resolver.
- Una lectura de fuente o caso discriminante debe desbloquear la siguiente edición. No repetir búsquedas ya resueltas ni comparar baterías completas con HEAD. Un marcador pendiente o un test verde no bastan como interpretación.
- **Investigación primero en la KB:** usar los textos, referencias, contratos y decisiones existentes en el repositorio. No consultar web ni abrir PDF por rutina o para reconfirmar información suficiente. Recurrir a ellos únicamente si falta un dato imprescindible para la siguiente implementación o existe una contradicción concreta que la KB y los rulings no resuelven. Identificar ese dato antes de ampliar la búsqueda y consultar sólo el pasaje necesario. No inventar reglas para evitar consultar una fuente realmente necesaria. Cada prompt debe repetir este límite.
- Un escritor por archivo compartido. Revisar estado/propiedad antes de editar. En trabajo aislado preservar la base exacta inicial, incluidos cambios heredados, fuera del entregable. Ante bloqueo concurrente identificado una vez, continuar con lo independiente; no esperar mediante sondeos ni crear overlays para certificar una integración inexistente.
- Agentes externos: **CSV sólo `query` y `prepare`**, con propuesta fuera del repo. El coordinador integra mediante `apply` preview y `--write`: snapshot completo previo, 4.556 claves `(id, clause_id)`, textos/huellas/notas conservados, validación y rechazo de concurrencia. Nada de edición directa o scripts alternativos; ante daño, suspender escrituras y avisar, nunca restaurar desde HEAD.
- **Subagentes autorizados y recomendados si aceleran la implementación:** repartir capacidades concretas y archivos disjuntos; un escritor por archivo y un responsable de integración del paquete. Transmitir todos los límites. No duplicar investigación, revisiones o pruebas ya válidas de los delegados. Los subagentes devuelven cambios/evidencia al ejecutor principal, sin escribir el CSV ni crear informes separados. Los prompts deben incluir esta autorización.
- Sin commits, pushes ni cambios ajenos. La única documentación nueva del ejecutor principal es `deliveries/IDTAREA-completed.md`, según el contrato siguiente. Si ya existe una capacidad, distinguir reconciliación de implementación y no prolongar el encargo con auditorías.

## Despacho secuencial y entrega al coordinador

El coordinador proporciona los prompts en serie usando estos paquetes. Cada prompt
identifica un ID, las capacidades concretas, los archivos reservados y las exclusiones;
no autoriza al agente a abrir otro paquete. No reasignar un trabajo en curso. Antes
de entregar el siguiente prompt, usar el resultado anterior y comprobar sólo sus
puntos de integración necesarios, sin repetir la investigación o las pruebas válidas.

**Asignar bloques completos nuevos a los agentes externos.** El coordinador termina
los restos pequeños de integración o implementación de una entrega (incluido C03c).
Sólo devolver un bloque anterior al ejecutor si todavía exige implementación
sustancial; no consumir otro encargo externo en pequeños remates o verificaciones.

Cada agente crea **un único** documento
`docs/knowledge/2a2b/deliveries/IDTAREA-completed.md` (por ejemplo,
`C09-completed.md`). Objetivo: hasta 400 palabras, ampliables sólo para describir
un bloqueo o decisión imprescindible. No crear planes, diarios, inventarios,
certificados ni volcados adicionales. No copiar logs o textos del CSV al documento.

Contenido obligatorio:

1. **Estado:** completo, parcial o bloqueado; rama/base inicial y checkout de entrega.
2. **Capacidades:** antes → después; separar implementación nueva de conexión o
   reconciliación. Enumerar las partes asignadas todavía pendientes, si las hay.
3. **Cambios:** archivos propios y decisiones de fuente imprescindibles. Si se
   entrega parche, indicar ruta y base exacta; señalar cambios heredados/concurrentes.
4. **Comprobación:** comandos/selectores ejecutados y resultado; ruta de la salida
   conservada fuera del repo. No ejecutar pruebas adicionales para adornar el informe.
5. **CSV e integración:** claves `(id, clause_id)` resueltas o ruta de la propuesta
   preparada que las contiene, archivos compartidos pendientes de integrar y bloqueos
   concretos. Un informe llamado `completed` no convierte una entrega parcial en completa.

El agente no modifica este índice ni el plan para registrar su progreso. El
coordinador revisa la entrega acotada e integra código/propuesta cuando esté completa;
el estado de cláusulas permanece únicamente en el CSV.

## Propiedad y paralelismo

| Zona compartida | Regla de coordinación |
|---|---|
| `packages/typescript/domain/eligibility/index.ts` y `bridge.ts` | Un propietario para C01–C06 y cualquier H que los necesite. Los demás preparan datos en fuentes disjuntas o entregan parches aislados. |
| `packages/python/roster-construction/mordheim_construction/compiler.py`, `conditions.py`, `contracts.py` | Un propietario; C08/C09/C14 y proyecciones pueden coincidir. `equipment_preparations.py`/`runes.py` también requieren reserva si se modifican. |
| `modular/contexts.py`, `psychology.py`, `leadership.py`, `pools.py`, `rounds.py`, `aftermath.py`, `equipment.py`, `state.py` y `phases.py` | Reservar archivos reales, no sólo el nombre de familia. C08/C10/C11/C12/C13 y M00 pueden coincidir. |
| `sources/knowledge/catalog/mechanics/{close-combat,execution,simulation-mappings}.yaml` y catálogos items | Son archivos compartidos aunque las entradas sean distintas. Un integrador o parches aislados; no dos escritores simultáneos. |
| Fuentes de bandas distintas | Pueden editarse en paralelo si no coinciden archivos. Reservar también sus tests; un test compartido sigue teniendo un solo escritor. |
| CSV, este documento, plan, rulings y mapa de consumidores | Coordinador integra; no actualizarlos desde cada agente. El CSV sigue siendo la única cola de estado. |

Paralelismo práctico: **un consumidor compartido + un paquete de fuentes disjuntas**, o varios worktrees con entregas aisladas que el coordinador integra secuencialmente. Un worktree evita colisiones de escritura, pero no conflictos semánticos. No lanzar simultáneamente todos los paquetes C03 sobre el mismo archivo central de elegibilidad.

Los nombres de consumidores siguientes indican dónde buscar y reservar, no una orden de modificar todos esos archivos. La propiedad actual de otros agentes no se deduce del estado Git y debe acordarse al despachar.

## Paquetes y selección verificable

Los conteos son del corte, no se actualizan con cada entrega. Para reanudar, consultar sólo los pendientes que siguen presentes dentro de la selección del paquete. Una fila nueva o una modificación concurrente exige leerla; no hereda automáticamente una interpretación.

Selectores sobre la **columna `id`**, con `*` como comodín textual. Si se lista `clause_id`, sólo esas cláusulas; `*` en la segunda columna significa todas las pendientes de ese ID/prefijo en el corte. Se comprobaron las 597 claves: cada una pertenece exactamente a un paquete, sin omisiones ni duplicados. Esto prueba distribución del trabajo, no funcionamiento del motor.

Abreviaturas, expandidas antes de consultar:

- `B/` = `source/bands/mordheim/`
- `BT/` = `source/bands/trollheim/`
- `R/` = `rule/mordheim/`
- `RT/` = `rule/trollheim/`
- `S/` = `source/catalog/`

La herramienta no interpreta estos comodines: consultar con `--id` exacto y `--clause-id`, o por `--source` para obtener la fuente acotada y seleccionar los IDs indicados. No pasar un glob a `--id`. Ejemplo de consulta de familia: `python -X utf8 tools/knowledge/t13_csv.py query --pending --source dwarf-guildsmen-kaz --limit 30`; ampliar el límite sólo si la familia devuelve más filas, no para repetir el inventario global.


| Paquete | Filas | Resultado/familia |
|---|---:|---|
| C01a | 27 | Ataques naturales: reglas nativas Mordheim |
| C01b | 21 | Ataques naturales: declaraciones de perfiles Mordheim |
| C01c | 34 | Ataques naturales: variantes Trollheim |
| C02a | 20 | Restricciones de equipo: reglas Mordheim |
| C02b | 9 | Restricciones de equipo: reglas Trollheim |
| C02c | 43 | Restricciones de equipo: perfiles y estricturas |
| C03a | 44 | Destinatarios del catálogo de comercio |
| C03b | 49 | Destinatarios de listas Trollheim |
| C03c | 49 | Destinatarios de listas Mordheim |
| C03d | 5 | Destinatarios y combinaciones en objetos |
| C04a | 17 | Acceso a listas: Undead, Lahmia y orígenes |
| C04b | 23 | Acceso a listas: promoción, fase y excepciones |
| C05a | 6 | Habilidades enanas y Slayer |
| C05b | 29 | Concesiones y acceso a habilidades/mutaciones |
| C06 | 26 | Constructos Clockworkers |
| C07a | 11 | Variantes de armas y discrepancias de catálogo |
| C07b | 23 | Equivalencias de armas, armaduras y materiales |
| C08 | 8 | Mutaciones: brazos, ataques y contacto |
| C09 | 10 | Preparaciones y características compartidas |
| C10 | 25 | Psicología, odio e identidad compartida |
| C11 | 14 | Liderazgo y apoyo suministrado |
| C12 | 7 | Carga y acciones alternativas |
| C13 | 4 | Contagious y Rotten Body |
| C14a | 3 | Modificadores de ejemplar de arma |
| C14b | 6 | Kits físicos y defensas intrínsecas |
| C15 | 16 | Alcance y fuentes residuales: NO despachar como implementación masiva |
| H01 | 16 | Consecuencias reutilizables de Aenur, Veskit y Slayer |
| H02 | 23 | Kits y variantes individuales de personajes |
| H03a | 18 | Proyección y psicología de hirelings |
| H03b | 10 | Recursos y variantes de hirelings |
| R01 | 3 existentes | Remate de filas pendientes de C01b, C04b y C14b; no suma nuevas cláusulas |
| M00 | 1 | Misericordia del Conde — INTEGRADO |

### C01a — Ataques naturales: reglas nativas Mordheim

**C01a cerrado, integración final 2026-10-17: 27 cláusulas.** Kit impreso, daga del esclavo Skaven y prohibición de materiales/venenos/preparaciones conectados. Banshee completa la representación de Iniciativa ausente, Sweep sin aborto, inmunidad a drogas/venenos y Cold Steel. El garrote usa weapon.club conservando el comportamiento mace; la bendición canónica del ejemplar suministra attack.blessed sólo al arma elegida. Admitida sin la exclusión anterior; evidencia focal del ejecutor reutilizada, sin repetir baterías. Última fila aplicada con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente; retirado el problema resuelto.

**27 cláusulas (27 YES).** Conectar prohibiciones de equipo y ataques intrínsecos de animales, no muertos y otros perfiles de las reglas seleccionadas. Mantener las excepciones: garras espectrales, huesos como mazas, perfiles que sí pueden llevar armadura.

**Consumidores/propiedad:** eligibility/index.ts; compiler.py; reglas nativas de esta selección.

**Salida:** Una ruta legal sin equipo físico ficticio; Fuerza, número de ataques y penalizaciones según cada fuente.

<details>
<summary>Selección de claves de C01a</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/halflings-mic/piggies--equipment-restrictions/*` | * |
| `R/horned-hunters/*` | * |
| `R/lustrian-reavers/*` | * |
| `R/maneaters/*` | * |
| `R/marauders-of-chaos/*` | * |
| `R/mazzalupo-web/*` | * |
| `R/necrarchs-mou/*` | * |
| `R/necrarchs-the-soul-stealers-lotd1/*` | * |
| `R/night-goblins-mic/*` | * |
| `R/norse-explorers-btb/*` | * |
| `R/protectorate-of-sigmar-lotd3/*` | * |
| `R/skaven-of-clan-skryre-rel/*` | * |
| `R/slavers-rel/*` | * |
| `R/strigoi-kaz/bats--equipment-restrictions/*` | * |
| `R/strigoi-kaz/charnel-guard--equipment-restrictions/*` | * |
| `R/strigoi-kaz/fell-bats--equipment-restrictions/*` | * |
| `R/strigoi-kaz/ghouls--equipment-restrictions/*` | * |
| `R/strigoi-kaz/vampire--equipment-restrictions/*` | * |
| `R/tomb-guardians/tomb-scorpions--equipment-restrictions/*` | * |
| `R/witch-hunters/*` | * |
| `R/wood-elves-of-arden-mou/*` | * |

</details>

### C01b — Ataques naturales: declaraciones de perfiles Mordheim

**Remate R01 integrado:** undead/profiles/5, cláusula no-unarmed-penalty, ya está cerrada. Ataque natural y ausencia de penalizaciones comprobados mediante evidencia focal reutilizada, sin repetir las demás entregas.

**Cerrado 2026-10-17: 21/21.** Conservadas las restricciones de once bandas, Unarmed Fighting corporal, tirada única de Spawn y las reglas del Dragon Monk. Integrado el remate del Tomb Scorpion en ambos orígenes: el veneno intrínseco permanece en el ataque y ya no concede equipo seleccionable. Consumidor regenerado; tres casos y sonda de ambas variantes del ejecutor reutilizados. Tres filas finales de C01b/C01c integradas con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Sin repetir baterías.

**21 cláusulas (21 YES).** Resolver las declaraciones de perfiles y sus dependencias de ataques naturales. Incluye Wulfen, Strigoi, perros, Treekin y casos especiales: Dragon Monk, Spawn y Sabretusk. No generalizar el waiver del puño a todos los perfiles.

**Consumidores/propiedad:** Mismos consumidores que C01a; perfiles Mordheim.

**Salida:** El equipo prohibido se rechaza y el ataque intrínseco correcto llega al duelo; excepciones conservadas.

<details>
<summary>Selección de claves de C01b</summary>

| id (abreviado) | clause_id |
|---|---|
| `B/call-of-the-night-haint-mim/profiles.yaml/*` | * |
| `B/druchii-mic/profiles.yaml/@/profiles/7/*` | * |
| `B/fen-guard-mim/profiles.yaml/*` | * |
| `B/marauders-of-chaos/profiles.yaml/@/profiles/4/*` | * |
| `B/marauders-of-chaos/profiles.yaml/@/profiles/6/*` | * |
| `B/masters-of-horror-sylv/*` | * |
| `B/norse-explorers-btb/*` | * |
| `B/norse-explorers-lustria/*` | * |
| `B/ogre-hunting-party-web/*` | * |
| `B/order-of-the-mare-web/profiles.yaml/*` | * |
| `B/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/*` | * |
| `B/restless-dead/profiles.yaml/@/profiles/3/*` | * |
| `B/restless-dead/profiles.yaml/@/profiles/6/*` | * |
| `B/survivors-of-strigos-sylv/*` | * |
| `B/tomb-guardians/*` | * |
| `B/undead/profiles.yaml/@/profiles/3/*` | * |
| `B/undead/profiles.yaml/@/profiles/5/*` | * |
| `B/underworld-alliance-mim/*` | * |

</details>

### C01c — Ataques naturales: variantes Trollheim

**Cerrado 2026-10-17: 34/34.** Trece perfiles publican sus ataques naturales y restricciones; compile_fighter consume profile.natural-attacks conservando profile.fist y el rechazo de armas explícitas. Las dos filas finales del Tomb Scorpion se cerraron con el consumidor compartido de C01b y la declaración específica khemri, sin duplicar comportamiento. Evidencia focal del ejecutor reutilizada; CSV integrado con snapshot, conservación de 4.556 claves/textos/huellas/notas y control concurrente. El defecto separado de preparaciones oferta/compilación quedó resuelto mediante preparationIssue compartido; ocho casos focales correctos y registro de problemas actualizado, sin nuevos cierres CSV.

**34 cláusulas (34 YES).** Conectar animales, esqueletos y variantes de No Muertos de los perfiles/reglas seleccionados. Distinguir ausencia de penalización, ausencia de equipo y arma improvisada.

**Consumidores/propiedad:** Mismos consumidores que C01a; fuentes Trollheim.

**Salida:** Variantes accesibles sin duplicar ataques o regalar inmunidades.

<details>
<summary>Selección de claves de C01c</summary>

| id (abreviado) | clause_id |
|---|---|
| `RT/chaos-streets-greenskins/*` | * |
| `RT/khemri-cursed-of-karak-zorn/*` | * |
| `RT/khemri-tomb-guardians/tomb-scorpions--equipment-restrictions/*` | * |
| `RT/trollheim-undead/*` | * |
| `BT/chaos-streets-greenskins/*` | * |
| `BT/chaos-streets-mordheim-inhabitants/profiles.yaml/@/profiles/6/*` | * |
| `BT/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/6/*` | * |
| `BT/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/4/*` | * |
| `BT/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/6/*` | * |
| `BT/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/8/*` | * |
| `BT/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/9/*` | * |
| `BT/khemri-cursed-of-karak-zorn/*` | * |
| `BT/khemri-hobgoblin-raiders/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/7/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/9/*` | * |
| `BT/khemri-mages/profiles.yaml/*` | * |
| `BT/khemri-necromancers/*` | * |
| `BT/khemri-tomb-guardians/profiles.yaml/*` | * |
| `BT/lustria-amazons/profiles.yaml/@/profiles/5/*` | * |
| `BT/lustria-clan-pestilens/profiles.yaml/@/profiles/6/*` | * |
| `BT/lustria-dark-elves/profiles.yaml/@/profiles/6/*` | * |
| `BT/lustria-norse/profiles.yaml/*` | * |
| `BT/trollheim-skaven-clan-eshin/profiles.yaml/*` | * |
| `BT/trollheim-undead/*` | * |
| `BT/trollheim-witch-hunters/*` | * |
| `S/rules/special-rules.yaml/shared-rule.natural-weapons/*` | * |

</details>

### C02a — Restricciones de equipo: reglas Mordheim

**C02a cerrado, integración final 2026-10-17.** A las catorce propuestas anteriores se añaden las seis del remate: prohibición de monturas de Black Orcs, acceso al Amuleto para Slayers, materiales Ogre, carga y equipo Nuttaz y prohibición completa Vim-To. Nuevo permiso canónico del Amuleto y rechazo de estado mounted; demás consumidores reutilizados. Evidencia final del ejecutor aceptada sin repetir baterías. Seis filas integradas con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. La admisión post-batalla observada es un consumidor de campaña fuera del cierre modular, no corregido ni certificado aquí. Detalle en C02a-completed.md.

**20 cláusulas (20 YES).** Aplicar restricciones de armadura, armas, categorías e inventario a los perfiles seleccionados; incluye Nuttaz, Flayerkin, Daemon-Fimm y Vim-To Mage. Las prohibiciones de disparo sólo afectan construcción, no autorizan resolver disparos.

**Consumidores/propiedad:** eligibility/index.ts y bindings nativos; compiler.py sólo si falta proyección.

**Salida:** Configuración permitida aceptada y configuración prohibida rechazada, sin convertir controles en permisos globales.

<details>
<summary>Selección de claves de C02a</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/black-orcs/band--let-the-goons-do-the-work/*` | * |
| `R/black-orcs/orc-nuttaz--savage/*` | * |
| `R/disciples-of-maldred-mou/*` | * |
| `R/druchii-mic/band--disdain/*` | * |
| `R/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen` | `non-thrown-missile-prohibition` |
| `R/dwarf-slayer-cult-web/band--slayer-rules/*` | * |
| `R/halflings-mic/band--too-big/*` | * |
| `R/high-elves-lus/*` | * |
| `R/khorne-raiders-sar/*` | * |
| `R/lords-of-the-marsh-mim/*` | * |
| `R/nipponese-expedition-web/vim-to-mage--tenants-of-the-order/*` | * |
| `R/ogre-hunting-party-web/band--huuuuge/*` | * |
| `R/savage-orcs-kaz/gobbo-boyz--equipment-restrictions/*` | * |
| `R/savage-orcs-kaz/nuttaz--equipment-restrictions/*` | * |
| `R/silent-brotherhood-sc/*` | * |
| `R/snotlings-web/band--small-hands/*` | * |
| `R/strigoi-kaz/skeletons--equipment-restrictions/*` | * |

</details>

### C02b — Restricciones de equipo: reglas Trollheim

**C02b cerrado, integración final 2026-10-16: nueve cláusulas.** Red Teeth accede a Feather Headdress cuando porta condition.current-warband-leader, con el contrato compartido de C11; oferta, veredicto y compilación coinciden y conservan las otras prohibiciones. Completada también la resolución de objetos conocidos en band_forbids, manteniendo el rechazo del objeto prohibido y el diagnóstico de tokens desconocidos. El coordinador corrigió el límite de lookup null, reconstruyó eligibility y ejecutó cinco casos afectados, correctos. Tres filas integradas (un cierre y dos actualizaciones de evidencia) con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Retirado el problema resuelto del registro.

**9 cláusulas (9 YES).** Conectar restricciones Lahmia/Necrarch, Corsairs, High Elves, Skinks y Red Teeth. Preservar diferencias de material, tipo de arma y destinatario.

**Consumidores/propiedad:** Mismos consumidores que C02a; fuentes Trollheim.

**Salida:** Todas las restricciones compuestas del paquete se aplican completas.

<details>
<summary>Selección de claves de C02b</summary>

| id (abreviado) | clause_id |
|---|---|
| `RT/chaos-streets-undead-bloodlines/lahmia-vampire--equipment-restrictions/*` | * |
| `RT/chaos-streets-undead-bloodlines/necrarch-vampire--equipment-restrictions/*` | * |
| `RT/khemri-tomb-guardians/mortuary-acolytes--equipment-restrictions/*` | * |
| `RT/lustria-dark-elves/*` | * |
| `RT/lustria-high-elves/*` | * |
| `RT/lustria-lizardmen/skink-braves--equipment-restrictions/*` | * |
| `RT/lustria-savage-goblins/*` | * |

</details>

### C02c — Restricciones de equipo: perfiles y estricturas

**C02c cerrado, integración 2026-10-17.** Cuarenta y una disposiciones finales integradas; se respetaron las filas ya cerradas por C02a. Permisos y prohibiciones coinciden entre oferta y compilación, con excepciones del kit, Ulric/Verena/Taal, materiales enanos y destinatarios de listas. Young'uns conserva equipo legal y exclusiones; Khorne reutiliza C02a; aclaración Taal tratada como construcción y Ostlanders como Ruffians. Snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente correctos. Evidencia del ejecutor reutilizada sin repetir baterías; detalle en C02c-completed.md.

**43 cláusulas (43 YES).** Resolver las restricciones declaradas en perfiles: armadura, materiales enanos, armas permitidas y estricturas Ulric/Verena/Taal. Varias rutas Ulric ya fueron trabajadas: reutilizar evidencia y pasar a las que falten.

**Consumidores/propiedad:** eligibility/index.ts; proyección de perfiles; fuentes de perfiles y estricturas.

**Salida:** No quedan bypass entre inventario, equipo activo y selección canónica de los casos asignados.

<details>
<summary>Selección de claves de C02c</summary>

| id (abreviado) | clause_id |
|---|---|
| `item/wolf_pelt_cloak` | * |
| `mechanic/defence.wolf-pelt-cloak` | * |
| `B/black-orcs/*` | * |
| `B/horned-hunters/*` | * |
| `B/khorne-raiders-sar/*` | * |
| `B/kislevites/*` | * |
| `B/knights-of-the-bitter-moors-mim/*` | * |
| `B/marauders-of-chaos/profiles.yaml/@/profiles/1/*` | * |
| `B/necrarchs-mou/*` | * |
| `B/nipponese-expedition-web/*` | * |
| `B/ostlanders/*` | * |
| `B/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/2/equipment_restrictions/2/*` | * |
| `B/savage-orcs-kaz/profiles.yaml/*` | * |
| `B/savage-orcs-sar/*` | * |
| `B/vampire-hunters-of-sylvania-lotd5/*` | * |
| `BT/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/2/*` | * |
| `BT/lustria-high-elves/profiles.yaml/*` | * |
| `S/campaign/magic.yaml/@/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/@/profiles/29/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/@/profiles/20/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/*` | * |
| `S/rules/special-rules.yaml/shared-rule.strictures/*` | * |

</details>

### C03a — Destinatarios del catálogo de comercio

Integración corregida 2026-10-15: **parcial**. Integradas 37 disposiciones de C03a
(22 conexiones y 15 restricciones de adquisición), más el cierre de la regresión
de Runestones en C03c: 38 filas con conservación y control concurrente. Runestones
respeta creación y fase posterior; Chosen ya no concede acceso por defecto.
**Cierre final 2026-10-15:** Chosen ya se selecciona y compila; las cláusulas 162
y 367 quedan resueltas, sin simular monturas ni avances de campaña. El coordinador
corrigió 187 contra la fuente: Knights-only era un error de extracción, no una
restricción impresa. Se conserva el acceso de las listas de Peregrinos/Arqueros;
el caso afectado pasa. Tres filas finales integradas con conservación/concurrencia.
C03a cerrado. Remate de Shortsword integrado: operador propio con Parry y +1 a
la salvación enemiga (6+ sin armadura), mappings corregidos y fila item/shortsword
reconciliada. Dos discriminadores de ataque real pasan frente a controles con
espada ordinaria; retirado el problema resuelto del registro.

**44 cláusulas (44 YES).** Transportar las restricciones de destinatario de trading-post a la construcción individual: banda, especie, héroe, perfil o habilidad. No implementar compras, disponibilidad comercial ni límites de toda una banda. Las entradas exclusivas de hirelings se dejan para después de las compartidas.

**Consumidores/propiedad:** trading-post.yaml; profileFactsProjection y entryAvailable del dominio de elegibilidad.

**Salida:** Un objeto no se ofrece ni se acepta al destinatario incorrecto; el destinatario legal lo puede compilar.

<details>
<summary>Selección de claves de C03a</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/campaign/trading-post.yaml/@/items/1/*` | * |
| `S/campaign/trading-post.yaml/@/items/10/*` | * |
| `S/campaign/trading-post.yaml/@/items/130/*` | * |
| `S/campaign/trading-post.yaml/@/items/133/*` | * |
| `S/campaign/trading-post.yaml/@/items/137/*` | * |
| `S/campaign/trading-post.yaml/@/items/138/*` | * |
| `S/campaign/trading-post.yaml/@/items/144/*` | * |
| `S/campaign/trading-post.yaml/@/items/15/*` | * |
| `S/campaign/trading-post.yaml/@/items/162/*` | * |
| `S/campaign/trading-post.yaml/@/items/17/*` | * |
| `S/campaign/trading-post.yaml/@/items/18/*` | * |
| `S/campaign/trading-post.yaml/@/items/186/*` | * |
| `S/campaign/trading-post.yaml/@/items/187/*` | * |
| `S/campaign/trading-post.yaml/@/items/21/*` | * |
| `S/campaign/trading-post.yaml/@/items/213/*` | * |
| `S/campaign/trading-post.yaml/@/items/22/*` | * |
| `S/campaign/trading-post.yaml/@/items/237/*` | * |
| `S/campaign/trading-post.yaml/@/items/24/*` | * |
| `S/campaign/trading-post.yaml/@/items/249/*` | * |
| `S/campaign/trading-post.yaml/@/items/25/*` | * |
| `S/campaign/trading-post.yaml/@/items/258/*` | * |
| `S/campaign/trading-post.yaml/@/items/26/*` | * |
| `S/campaign/trading-post.yaml/@/items/264/*` | * |
| `S/campaign/trading-post.yaml/@/items/27/*` | * |
| `S/campaign/trading-post.yaml/@/items/272/*` | * |
| `S/campaign/trading-post.yaml/@/items/277/*` | * |
| `S/campaign/trading-post.yaml/@/items/29/*` | * |
| `S/campaign/trading-post.yaml/@/items/3/*` | * |
| `S/campaign/trading-post.yaml/@/items/31/*` | * |
| `S/campaign/trading-post.yaml/@/items/32/*` | * |
| `S/campaign/trading-post.yaml/@/items/320/*` | * |
| `S/campaign/trading-post.yaml/@/items/327/*` | * |
| `S/campaign/trading-post.yaml/@/items/34/*` | * |
| `S/campaign/trading-post.yaml/@/items/35/*` | * |
| `S/campaign/trading-post.yaml/@/items/367/*` | * |
| `S/campaign/trading-post.yaml/@/items/37/*` | * |
| `S/campaign/trading-post.yaml/@/items/374/*` | * |
| `S/campaign/trading-post.yaml/@/items/4/*` | * |
| `S/campaign/trading-post.yaml/@/items/434/*` | * |
| `S/campaign/trading-post.yaml/@/items/441/*` | * |
| `S/campaign/trading-post.yaml/@/items/47/*` | * |
| `S/campaign/trading-post.yaml/@/items/49/*` | * |
| `S/campaign/trading-post.yaml/@/items/5/*` | * |
| `S/campaign/trading-post.yaml/@/items/9/*` | * |

</details>

### C03b — Destinatarios de listas Trollheim

Integración 2026-10-15: **C03b cerrado, 49 cláusulas**. Tras los 47 cierres
iniciales, se implementaron el prerrequisito Censer y el tocado obligatorio del
líder inicial. «One use» sigue pendiente en C15, fuera de este paquete.
Véase [la entrega revisada](deliveries/C03b-completed.md).
Los conteos y selectores siguientes conservan el corte inicial.

**49 cláusulas (1 NO, 48 YES).** Conectar las líneas de listas de equipo Trollheim con sus destinatarios reales: héroes, líder, Beastmaster, Loremaster, Witch Doctor y otras variantes. Separar de este paquete la ejecución del efecto del objeto, asignada a su consumidor.

**Consumidores/propiedad:** equipment-access.yaml Trollheim; entryAvailable/profileEquipment en eligibility/index.ts.

**Salida:** Oferta y validación coinciden para las variantes y excepciones del paquete.

<details>
<summary>Selección de claves de C03b</summary>

| id (abreviado) | clause_id |
|---|---|
| `BT/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/15/*` | * |
| `BT/chaos-streets-sigmar-protectorate/equipment-access.yaml/*` | * |
| `BT/khemri-lahmian-brotherhood/equipment-access.yaml/*` | * |
| `BT/khemri-mages/equipment-access.yaml/*` | * |
| `BT/lustria-amazons/equipment-access.yaml/*` | * |
| `BT/lustria-clan-pestilens/equipment-access.yaml/*` | * |
| `BT/lustria-clan-pestilens/profiles.yaml/@/profiles/0/*` | * |
| `BT/lustria-clan-pestilens/profiles.yaml/@/profiles/2/*` | * |
| `BT/lustria-clan-pestilens/profiles.yaml/@/profiles/3/*` | * |
| `BT/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/14/*` | * |
| `BT/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/16/*` | * |
| `BT/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/5/*` | * |
| `BT/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/1/*` | * |
| `BT/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--high-elves-only` |
| `BT/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/16/*` | * |
| `BT/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/6/*` | * |
| `BT/lustria-norse/equipment-access.yaml/*` | * |
| `BT/lustria-pirates/*` | * |
| `BT/lustria-pygmies/*` | * |
| `BT/lustria-savage-goblins/equipment-access.yaml/*` | * |
| `BT/lustria-savage-goblins/profiles.yaml/@/profiles/1/*` | * |
| `BT/trollheim-skaven-clan-eshin/equipment-access.yaml/*` | * |

</details>

### C03c — Destinatarios de listas Mordheim

Integración completa 2026-10-15: 49 cláusulas cerradas. El coordinador terminó
acceso High Elven, combinación Kumfy Gear, requisito Falconer y destinatario de
Runas Élficas después de crear la banda; reutilizó las siete dependencias ya
implementadas. Véase [la entrega integrada](deliveries/C03c-completed.md).
No reasignar este paquete; los conteos inferiores son del corte inicial.

**49 cláusulas (49 YES).** Conectar las líneas de listas Mordheim: oficio, héroe, especie, banda, exclusiones y habilidades requeridas. Incluye compatibilidad Skull Busta/Warpaint, Poison Daggers y excepciones de listas.

**Consumidores/propiedad:** equipment-access.yaml Mordheim; entryAvailable/profileEquipment y restricciones compartidas.

**Salida:** Los permisos de línea no se amplían a toda la lista ni a otra variante.

<details>
<summary>Selección de claves de C03c</summary>

| id (abreviado) | clause_id |
|---|---|
| `B/call-of-the-night-haint-mim/equipment-access.yaml/*` | * |
| `B/crooked-moon-kep/equipment-access.yaml/*` | * |
| `B/druchii-mic/equipment-access.yaml/*` | * |
| `B/dwarf-slayer-cult-web/*` | * |
| `B/fen-guard-mim/equipment-access.yaml/*` | * |
| `B/halflings-mic/*` | * |
| `B/high-elves-lus/*` | * |
| `B/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/*` | * |
| `B/house-guard-sc/equipment-access.yaml/@/equipment_lists/2/items/1/*` | * |
| `B/low-kings-mim/*` | * |
| `B/mazzalupo-web/*` | * |
| `B/mercenaries/*` | * |
| `B/metal-mongers-mim/equipment-access.yaml/*` | * |
| `B/night-goblins-kaz/equipment-access.yaml/*` | * |
| `B/orc-pirates-sar/*` | * |
| `B/order-of-the-mare-web/equipment-access.yaml/*` | * |
| `B/outlaws-of-stirwood-forest-redux-fbg/*` | * |
| `B/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/*` | * |
| `B/pit-fighters/*` | * |
| `B/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/12/*` | * |
| `B/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/14/*` | * |
| `B/shadow-warriors/*` | * |
| `B/shallows-beasts-mim/*` | * |
| `B/silent-brotherhood-sc/*` | * |
| `B/skaven-of-clan-moulder-web/*` | * |
| `B/skaven-of-clan-skryre-rel/*` | * |
| `B/slavers-rel/*` | * |
| `B/sorcerous-society-lotd4/*` | * |
| `B/watchmen-mim/*` | * |
| `B/wood-elves-of-athel-loren-web/*` | * |

</details>

### C03d — Destinatarios y combinaciones en objetos

**C03d cerrado, integración 2026-10-16.** Cinco filas integradas con snapshot íntegro, conservación de las 4.556 claves y control concurrente. Tres conexiones declarativas completadas: Skull Busta para sus destinatarios Orco, dosis Maibd sólo para Witch Elves sin cerrar el mercado general y Huge Jaws para Saurus Héroes, incluidos los promovidos. Combinaciones de Skull Busta y kit del Priest of Manann reutilizan consumidores existentes. Evidencia focal del ejecutor: cuatro casos correctos; fuentes entregadas idénticas al estado integrado, sin repetir baterías. Sin pendientes dentro del paquete.

**5 cláusulas (5 YES).** Resolver las restricciones publicadas en item/rule que complementan las líneas de lista: Skull Busta, veneno Maibd, Huge Jaws y equivalentes de esta selección.

**Consumidores/propiedad:** Catálogos de objetos; selección de reglas y restricciones compartidas.

**Salida:** Destinatario y combinación legal se conservan junto con el efecto ya existente.

<details>
<summary>Selección de claves de C03d</summary>

| id (abreviado) | clause_id |
|---|---|
| `item/skull_busta` | * |
| `R/druchii-mic/witch-elves--maibd-poison/*` | * |
| `RT/lustria-lizardmen/band--sacred-mark-huge-jaws/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/*` | * |

</details>

### C04a — Acceso a listas: Undead, Lahmia y orígenes

**C04a cerrado, integración 2026-10-15.** Diecisiete filas reconciliadas con snapshot completo, conservación y control concurrente. Lahmia selecciona Foreign/Native sin unir listas ni ampliar destinatarios fijos; Estalian conserva la armadura pesada añadida por su variante. Undead, Halfling y restricciones Sartosan reutilizan conexiones existentes. Los artefactos temporales del ejecutor no estaban accesibles en este host: integración preparada desde las claves actuales y dos discriminadores de los consumidores modificados ejecutados, ambos correctos (`%TEMP%/c04a-coordinator-focused.txt`). Sin repetir baterías generales.

**17 cláusulas (17 YES).** Resolver listas Foreign/Native Lahmia, acceso Undead, Halfling y variantes Estalian/Wasteland. El origen elegido determina la lista; no unir listas incompatibles.

**Consumidores/propiedad:** profileEquipment/catalogueEquipment en eligibility/index.ts; datos de variantes.

**Salida:** Cada variante compila con su lista correcta y rechaza las otras.

<details>
<summary>Selección de claves de C04a</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/mootlanders/*` | * |
| `R/sartosan-pirates-sar/*` | * |
| `B/estalian-corsairs-sar/*` | * |
| `B/mootlanders/*` | * |
| `B/sartosan-pirates-sar/*` | * |
| `B/undead/profiles.yaml/@/profiles/1/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/0/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/1/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/3/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/4/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/5/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/6/*` | * |
| `BT/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/8/*` | * |

</details>

### C04b — Acceso a listas: promoción, fase y excepciones

**Remate R01 integrado:** disciples-of-maldred-mou/profiles/3, cláusula whole, ya está cerrada. Oferta y selección directa respetan la fase suministrada; implementación existente reutilizada sin reabrir el resto del paquete.

**C04b cerrado, integración 2026-10-16: 23 cláusulas.** Ghoul promovido y fase inicial Mercenary de Maldred implementados; herencias de equipo reconciliadas. Clan Mors y Clan Skryre ya seleccionan y compilan Black Hunger y Tail Fighting, excluyen Art of Silent Death y disponen movimiento/despliegue por contenido. El coordinador extendió el selector de Héroe a Clanrats/Skavenslaves promovidos manteniendo el rechazo sin promoción; dos discriminadores pasan. Dos filas finales integradas con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Evidencia restante reutilizada, sin repetir baterías generales.

**23 cláusulas (23 YES).** Resolver Ghoul promovido, mercenarios Maldred, Ruffians/Outlaws, Swabbies, permisos de armadura y listas heredadas seleccionadas. Usar hechos suministrados admitidos; no simular promoción ni campaña.

**Consumidores/propiedad:** profileEquipment, bandEquipmentLimits, profileFactsProjection; fuentes del paquete.

**Salida:** La configuración recibe permisos según el estado explícito sin suprimir prohibiciones específicas.

<details>
<summary>Selección de claves de C04b</summary>

| id (abreviado) | clause_id |
|---|---|
| `item/lance_not_questing_knight` | * |
| `R/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-equipment-lists` |
| `R/skaven-of-clan-mors-kaz/*` | * |
| `R/skaven-of-clan-skryre-kaz/*` | * |
| `RT/khemri-thieves-guild/*` | * |
| `RT/lustria-pirates/*` | * |
| `B/disciples-of-maldred-mou/*` | * |
| `B/druchii-mic/profiles.yaml/@/profiles/4/*` | * |
| `B/fallen-the-rel/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/0/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/1/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/2/equipment_restrictions/0/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/3/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/4/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/5/*` | * |
| `B/pirates/*` | * |
| `B/restless-dead/profiles.yaml/@/profiles/0/*` | * |
| `BT/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/0/*` | * |
| `BT/lustria-amazons/profiles.yaml/@/profiles/0/*` | * |

</details>

### C05a — Habilidades enanas y Slayer

**C05a cerrado, integración 2026-10-16.** Tres filas restantes cerradas conservando las 4.556 claves/textos/huellas/notas. Master of Blades concede sólo Unbeatable Warrior; True Grit declara su tabla completa y Slayer Cult ofrece Deathwish, Deathblow y Axe Mastery. Miembros de campaña/movimiento excluidos por contenido. Incremento aislado incorporado por fragmentos; el coordinador corrigió Deathblow para resolver heridas, conservar ataques restantes tras una nominación anticipada y permitir declinarlo. Quince casos afectados pasan (`%TEMP%/c05a-coordinator-final.txt`); evidencia amplia del ejecutor reutilizada sin repetirla. Libro mayor T09 alineado con las tablas completas.

**6 cláusulas (6 YES).** Conectar listas especiales/heredadas y restricciones de Rememberer. Las destrezas individuales conservan sus propios operadores; no implementarlas otra vez por conectar la tabla.

**Consumidores/propiedad:** profileSkillLists, profileFactsProjection, buildAccess; fuentes Dwarf/Slayer.

**Salida:** Un perfil elige las habilidades permitidas y conserva las exclusiones impresas.

<details>
<summary>Selección de claves de C05a</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-special-skill-access` |
| `R/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen` | `promotion-shooting-skill-choice--scope--skill-list-access` |
| `R/dwarf-slayer-cult-web/band--slayer-special-skills/*` | * |
| `R/dwarf-slayer-cult-web/rememberer--not-a-slayer/*` | * |
| `R/dwarf-slayers-kaz/band--slayer-special-skills/*` | * |
| `R/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-special-skill-access` |

</details>

### C05b — Concesiones y acceso a habilidades/mutaciones

**C05b cerrado, integración 2026-10-17: 29/29.** A los cierres anteriores se añaden los seis pendientes: elección Animal Handling, forma de lobo suministrada, acceso Solkan condicionado por variante, promoción del Ogre Pit Fighter, disposición completa de Bloodfather y habilidades de Ippan Shu. Evidencia focal del ejecutor reutilizada (seis casos); no se repitieron pruebas. El coordinador contrastó el backup íntegro de la última escritura con el CSV: 4.556 claves y campos protegidos idénticos, notas conservadas y exactamente seis filas cambiadas, sin diferencias ajenas. Se retienen los cambios, aunque la escritura externa excedió su autorización; no autoriza nuevas escrituras. Las tres subcláusulas adicionales de Solkan se cerraron después en C05b-Solkan: consumidores existentes y nueve casos del ejecutor reutilizados, tres filas integradas con snapshot, conservación y control concurrente; sin nueva implementación de producción. Detalle en las entregas C05b y C05b-Solkan.

**29 cláusulas (2 UNCLASSIFIED, 27 YES).** Resolver Big Bully/Tiny, prerrequisitos, tablas Moulder/Nippon/Strigany/Ogre y concesiones seleccionables. Incluye Rat Ogre con mutación inicial y cambio de rol Bloodfather. Resolver cada variante impresa; no conceder toda una tabla por un nombre pendiente. Rune Use requiere contrato recuperado, no inventado.

**Consumidores/propiedad:** Selección/eligibility/index.ts; grants; fuentes seleccionadas; compiler sólo si falta transporte.

**Salida:** Cada concesión tiene destinatario, cantidad, opciones y prerrequisitos correctos; efectos se reutilizan.

<details>
<summary>Selección de claves de C05b</summary>

| id (abreviado) | clause_id |
|---|---|
| `mechanic/mechanic.curse-of-the-revenant` | * |
| `mechanic/mechanic.frustratingly-tiny` | * |
| `mechanic/mechanic.mark-of-arkhar` | * |
| `R/battle-monks-of-cathay/band--battle-monks-special-skills/*` | * |
| `R/black-orcs/band--da-boss-is-dead/*` | * |
| `R/channel-rats-mim/*` | * |
| `R/dark-elves/*` | * |
| `R/halflings-mic/village-ogre--skills/*` | * |
| `R/nipponese-expedition-web/band--nippon-special-skills/*` | * |
| `R/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `ogre-skill-list-rest` |
| `R/ogre-hunting-party-web/trappers--veteran-tracker/*` | * |
| `R/savage-orcs-kaz/band--orc-special-skills/*` | * |
| `R/skaven-of-clan-moulder-web/*` | * |
| `R/snotlings-web/bigsnotz--big-bully/*` | * |
| `R/strigoi-kaz/charnel-guard--cunning/*` | * |
| `BT/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/3/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/@/profiles/1/*` | * |
| `S/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/1/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/@/profiles/21/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.mule-skinner.rule.animal-handler/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.runesmith-journeyman.rule.runesmith/*` | * |
| `S/hirelings/hired-swords/grade-1c.yaml/@/profiles/6/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/@/profiles/17/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--skill-access` |
| `S/rules/special-rules.yaml/shared-rule.skills/*` | * |

</details>

### C06 — Constructos Clockworkers

Integrado 2026-10-15: **26 pendientes reconciliados y dos notas de disposición**.
Las capacidades de ranuras, destinatarios e inmunidades ya estaban implementadas;
la entrega aporta discriminadores de construcción y consumidores reales, no código
de producción nuevo. Equipo incorporado conserva su capacidad actual sin inventar
transferencias de plantilla ni inmunidad al desarme. Véase
[la entrega integrada](deliveries/C06-completed.md). No reasignar el paquete.

**26 cláusulas (26 YES).** Cerrar conjuntamente ranuras, costes, capacidad de armadura, equipo incorporado y sus inmunidades/No Pain. Ya existen proyección de ranuras y bindings de los dos perfiles: comprobar la conexión faltante sin rediseñar el sistema. No confundir prohibición de retirar equipo en construcción con inmunidad universal a romper o desarmar: decidir desde la fuente.

**Consumidores/propiedad:** Clockworkers profiles/equipment-access/special-rules; equipo/eligibility/index.ts; compile_fighter; consumo de estados si falta.

**Salida:** Soldier y Fiend legales, límites aplicados e inmunidades consumidas; productores de mapa/campaña excluidos por separado.

<details>
<summary>Selección de claves de C06</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/clockworkers-sc/*` | * |
| `B/clockworkers-sc/*` | * |

</details>

### C07a — Variantes de armas y discrepancias de catálogo

**C07a cerrado, integración 2026-10-17: 11/11.** Seis filas finales reconciliadas: Cathayan sin penetración adicional, Starsword conserva ward como excepción Dodge y Sun Gauntlet mantiene su variante secundaria F4 sin armadura. Ya funcionaban; sin código nuevo de producción. Evidencia focal y ruta canónica del ejecutor reutilizadas sin repetir pruebas. CSV con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Prosa editorial Cathayan obsoleta señalada en la entrega y pendiente de su propietario; no bloquea el contrato ejecutable vigente.

**11 cláusulas (4 NO, 1 UNCLASSIFIED, 6 YES).** Cathayan Longsword, Starsword, Sun Gauntlet y Belaying Pin: conservar perfiles/variantes y separar disparo de cuerpo a cuerpo. Starsword ya tiene ruling sobre Dodge; consultarlo. No volver a implementar su ignorar armadura si funciona.

**Consumidores/propiedad:** Catálogos items/mechanics; construcción y consumidor de armas correspondiente.

**Salida:** Variantes admitidas seleccionables y correctas; fuentes realmente ausentes identificadas sin completar reglas inventadas.

<details>
<summary>Selección de claves de C07a</summary>

| id (abreviado) | clause_id |
|---|---|
| `item/belaying_pin` | * |
| `item/cathayan_longsword` | * |
| `item/starsword` | * |
| `item/sun_gauntlet` | * |
| `item/sunstaff` | * |
| `mechanic/weapon.cathayan-longsword` | * |
| `mechanic/weapon.starsword` | * |
| `mechanic/weapon.sun-gauntlet` | * |

</details>

### C07b — Equivalencias de armas, armaduras y materiales

**C07b cerrado, integración final 2026-10-16: 23 cláusulas.** Integrados palo puntiagudo y kits, pala, peto de bronce, bastón de viaje y armas Pristekk; Pointy Stick enlaza weapon.dagger con grant:none, sin bono pasivo duplicado. R13 completa ambas empuñaduras del mismo Yari mediante alternate_mechanic_ids: oferta, precio, selección y compilación canónicos con sus restricciones. Dieciséis casos del paquete y seis casos finales de Yari/ausencia correctos; evidencia restante reutilizada, sin baterías globales. Retirado el Peto de Bronce del conjunto obsoleto de objetos sin binding y alineada la nota del Yari. CSV integrado con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente. R13 también queda cerrado (13 filas).

**23 cláusulas (1 NO, 22 YES).** Pointy Stick/daga, Wall of Steel, látigos y Shock Rod Pristekk, pica, Dwarf Axe, halberd, Travel Staff y equivalencias de armadura. Varias ya tienen operador: la tarea es conectar la variante pendiente, no copiar el comportamiento.

**Consumidores/propiedad:** Fuentes de equipo; mappings y construcción; phases/pools sólo ante ausencia concreta.

**Salida:** Identidad canónica y material/posición correctos llegan al ataque o defensa sin doble bono.

<details>
<summary>Selección de claves de C07b</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-dwarf-axe` |
| `R/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-dwarf-axe` |
| `R/nipponese-expedition-web/ashigaru--wall-of-steel/*` | * |
| `R/snotlings-web/band--pointy-stick/*` | * |
| `B/bretonnian-knights-errant-mou/*` | * |
| `B/clan-angrund-kep/*` | * |
| `B/crooked-moon-kep/profiles.yaml/*` | * |
| `B/grave-robbers-sylv/*` | * |
| `B/night-goblins-kaz/profiles.yaml/*` | * |
| `B/skaven-of-clan-pristekk-sc/*` | * |
| `BT/chaos-streets-arcane-society/*` | * |
| `BT/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/6/*` | * |
| `BT/khemri-tomb-guardians/equipment-access.yaml/*` | * |
| `BT/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/7/*` | * |

</details>

### C08 — Mutaciones: brazos, ataques y contacto

Integración completa 2026-10-15: ocho cláusulas cerradas. El coordinador corrigió
Great Claw + Extra Arm: capacidad de armas según brazos restantes, sin borrar
la prohibición de la garra. Evidencia del ejecutor reutilizada y discriminador
de composición correcto. Véase [la entrega integrada](deliveries/C08-completed.md).
No reasignar el paquete; conteos inferiores del corte inicial.

**8 cláusulas (8 YES).** Extra Arm, Scorpion Tail, Great Claw, Blackblood, Spines y Tentacle. Resolver asignación física, prohibición del brazo, ataque adicional e inmunidad al veneno, contacto, disparador y elección de ataque reducido. Trabajo de mutaciones anterior existe: integrar sus fragmentos correctos y completar sólo huecos.

**Consumidores/propiedad:** compiler.py; modular/equipment.py, pools.py, aftermath.py según consumidor.

**Salida:** Los efectos de cada mutación se componen con equipo y estado real; no duplican ataques ni disparadores.

<details>
<summary>Selección de claves de C08</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/campaign/mutations.yaml/*` | * |

</details>

### C09 — Preparaciones y características compartidas

Integración 2026-10-15: **diez cláusulas cerradas**. El coordinador corrigió
Brewers y completó Backley/adicción tras la decisión humana: un intento al inicio
de cada turno propio, con liberación persistente y sin duplicar Vigortia. Véase
[la entrega integrada](deliveries/C09-completed.md). Conteos inferiores: corte inicial.

**10 cláusulas (10 YES).** Brewers (incluido +1 WS/+1 S, tope 10), Remas/Remasen +1 Ld, Paladin of Horror +1 Ld, mayoría/minoría suministrada, Human Rememberer y características fijadas de Condemned. Alchemist ya tiene condiciones canónicas: reutilizarlas; separar adicción de campaña y Movement sin efecto en duelo.

**Consumidores/propiedad:** conditions.yaml/conditions.py; bonuses en compile_fighter; fuentes de cada destinatario.

**Salida:** Bonos aplicados exactamente una vez, con topes, destinatario y duración; configuraciones incompatibles rechazadas.

<details>
<summary>Selección de claves de C09</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/dwarf-guildsmen-kaz/band--brewers/*` | * |
| `R/masters-of-horror-sylv/*` | * |
| `R/tileans/*` | * |
| `R/underworld-alliance-mim/*` | * |
| `RT/khemri-necromancers/*` | * |
| `RT/lustria-tileans/*` | * |
| `B/dwarf-slayers-kaz/*` | * |
| `B/marauders-of-chaos/profiles.yaml/@/profiles/5/*` | * |
| `S/rules/special-rules.yaml/shared-rule.middenheim-physical-prowess/*` | * |

</details>

### C10 — Psicología, odio e identidad compartida

Integración parcial 2026-10-15: a los seis cierres previos se añaden 18
cierres/disposiciones aceptados. Slavers ya tiene ruta nativa y suministrada;
Fear of Fire, Bear Tamer y Lunatics reutilizan consumidores existentes. Pit Fighter
se dispone por su bono condicionado al terreno, no por los kits iniciales.
Instinctual Violence integrado: una asignación efectiva compartida, conservada
también al declinar toda nominación. Mayoría secundaria y Whipcrack corregidos.
**C10 cerrado, integración 2026-10-15:** Vengeful Hatred transporta identidades
de instancia del guerrero y de su banda, conservando la categoría sólo para
tipo de banda. El coordinador retiró la condición de conservar Líder: el odio
permanente sigue al individuo seleccionado, sin transferirse a un sucesor.
Reutilizada evidencia del ejecutor y ejecutado sólo ese discriminador adicional;
última fila integrada con conservación/concurrencia. Véase
[la entrega](deliveries/C10-completed.md).

**25 cláusulas (4 NO, 21 YES).** Holy Relic de Battle Pilgrims, odio a slavers, Vengeful Hatred, Instinctual Violence, Wild Lunatics, identidad Gnoblar/Stone Golem/Tomb Scorpion y Fear of Fire. Pit Fighter y Cloud of Flies requieren separar entorno/disparo de consecuencias admitidas. No fabricar alcance para cerrar las partes excluidas.

**Consumidores/propiedad:** contexts.py, psychology.py, rounds.py y facts/conditions; fuentes compartidas.

**Salida:** Prerrequisitos y destinatario controlan los estados; duración, primera ronda, Frenzy e inmunidades respetadas.

<details>
<summary>Selección de claves de C10</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/bretonnian-chapel-guard/*` | * |
| `R/carnival-of-chaos/band--blessings-of-nurgle-cloud-of-flies/*` | * |
| `R/carnival-of-chaos/nurglings--cloud-of-flies/*` | * |
| `R/carnival-of-chaos/plague-bearers--cloud-of-flies/*` | * |
| `R/fen-guard-mim/*` | * |
| `R/grave-robbers-sylv/*` | * |
| `R/kislevites/bear-tamer--bear-handler/*` | * |
| `R/night-goblins-web/*` | * |
| `R/ogre-hunting-party-web/band--greenskins/*` | * |
| `R/pit-fighters/*` | * |
| `R/tomb-guardians/tomb-scorpions--living/*` | * |
| `R/watchmen-mim/*` | * |
| `RT/chaos-streets-pit-fighters/*` | * |
| `RT/khemri-tomb-guardians/stone-golem--animated/*` | * |
| `RT/khemri-tomb-guardians/tomb-scorpions--living/*` | * |
| `RT/lustria-pygmies/*` | * |
| `S/campaign/serious-injuries.yaml/*` | * |
| `S/rules/special-rules.yaml/shared-rule.free-the-slaves/*` | * |

</details>

### C11 — Liderazgo y apoyo suministrado

**C11 cerrado, integración final 2026-10-16: 14 cláusulas.** Mob, Dim-Witted, Dark Majesty, Songster, Poetry y exención suministrada de Stupidity conectados; Rememberer e Inspiring Presence reconciliados; Plague Cart dispuesto por su contenido de Instabilidad/post-retirada. Battle Tongue Norse admite al Jarl nativo y a otro Héroe suministrado como líder actual mediante condition.current-warband-leader; selección, compilación y préstamo a diez pulgadas conectados, sin conceder Leader desde la habilidad. El contrato suministrado puede reutilizarse en C02b. Evidencia focal del ejecutor reutilizada, sin repetir baterías. Última fila integrada con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente.

**14 cláusulas (14 YES).** Bear Tamer/Rat Ogre, Songster, Rememberer, Poetry, Mob, líder ampliado y Plague Cart. Aplicar sólo los hechos de apoyo expresamente admitidos por los rulings; no crear terceros combatientes, mapas, recuentos de grupo ni distancias simuladas.

**Consumidores/propiedad:** conditions/facts; modular/leadership.py y psychology.py; reglas seleccionadas.

**Salida:** Beneficiario correcto y condición de apoyo precisa, incluidas excepciones de entrenador caído; sin duplicar liderazgo o bonos.

<details>
<summary>Selección de claves de C11</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/adventurers-kaz/*` | * |
| `R/battle-monks-of-cathay/raging-peasants--mob/*` | * |
| `R/carnival-of-chaos/plague-cart--plague-cart/*` | * |
| `R/dreamwalkers-cult-of-morr-fbg/*` | * |
| `R/dwarf-slayer-cult-web/band--rememberer-skills/*` | * |
| `R/dwarf-slayers-kaz/rememberer--rememberer/*` | * |
| `R/ghutani-rel/*` | * |
| `R/kislevites/trained-bear--trained/*` | * |
| `R/muzil-rel/*` | * |
| `R/turjuk-rel/*` | * |
| `RT/chaos-streets-undead-bloodlines/band--von-carstein-power-dark-majesty/*` | * |
| `RT/lustria-norse/*` | * |
| `S/rules/special-rules.yaml/shared-rule.stupidity/*` | * |

</details>

### C12 — Carga y acciones alternativas

**C12 cerrado, integración final 2026-10-16.** A los cuatro cierres previos se añaden las tres disposiciones Netter. Kaz y Crooked Moon reutilizan condition.netted como estado suministrado de la víctima, con ataque y recuperación existentes; no conceden el lanzamiento ni invocan el helper sin conexión. Ogre conserva cantidad/procedencia/destinatarios de sus tres redes como hechos impresos: suministro/reposición/transferencia y lanzamiento son externos, sin conceder una técnica Night Goblin. El coordinador corrigió la justificación de exclusión para basarla en contenido, no en ausencia de binding/lista. Tres filas finales integradas con conservación de 4.556 claves y control concurrente; reutilizada evidencia focal del ejecutor (16 passed), sin repetir baterías.

**7 cláusulas (7 YES).** Berserk Charge, Dire Wolf charge, Animal Fury, Bull Charge y variantes Netter. Bull Charge y el consumidor _netter ya existen: no reescribirlos por la etiqueta pendiente. Netter combina lanzamiento y carga: respetar la exclusión de disparo y no inventar una resolución admitida; resolver lo permitido y registrar exactamente la parte externa.

**Consumidores/propiedad:** pools.py/rounds.py/aftermath.py; grants y fuentes de carga.

**Salida:** Acceso y sustitución/bonos de carga correctos, sin acumular el pool normal con una acción sustitutiva ni simular disparo.

<details>
<summary>Selección de claves de C12</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/crooked-moon-kep/*` | * |
| `R/night-goblins-kaz/*` | * |
| `R/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `bull-charge`; `netter` |
| `RT/lustria-amazons/*` | * |
| `S/rules/special-rules.yaml/shared-rule.berserk-charge/*` | * |
| `S/rules/special-rules.yaml/shared-rule.charge/*` | * |

</details>

### C13 — Contagious y Rotten Body

Integrado 2026-10-15: las cuatro cláusulas están cerradas. Binding nativo conectado;
el coordinador añadió la condición de daño nuevo de cuerpo a cuerpo al consumidor.
Véase [la entrega integrada](deliveries/C13-completed.md). No reasignar.

**4 cláusulas (4 YES).** Conectar ambas variantes Pestilens y su prerrequisito. _react_to_wound ya contiene Contagious; reutilizarlo y corregir sólo la conexión o composición ausente. No abrir auditoría general de reacciones.

**Consumidores/propiedad:** Pestilens special-rules; requisitos en elegibilidad; modular/aftermath.py.

**Salida:** Reacción sólo tras Out of Action definitivo en cuerpo a cuerpo; test, 6 natural y exclusiones Undead/Possessed; prerrequisito válido.

<details>
<summary>Selección de claves de C13</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/skaven-clan-pestilens/*` | * |
| `RT/lustria-clan-pestilens/*` | * |

</details>

### C14a — Modificadores de ejemplar de arma

Integración 2026-10-15: **tres cláusulas cerradas**. Bendición y
Honing se aplican al ejemplar elegido; los tres resultados de Master Craftsman
(+1 Fuerza, +1 Iniciativa y coating Giggle Juice) también funcionan.
Corregida por el coordinador su composición: varios modificadores distintos
pueden coexistir; se conserva una sola runa por objeto. La tabla ya recuperada
se incorporó a la KB y los bonos se retiran al perder el arma. Véase
[la entrega integrada](deliveries/C14a-completed.md).

**3 cláusulas (3 YES).** Arma bendecida de exploración (hiere Undead/Possessed en 2+), Honing de Swordsmith y modificaciones de Master Craftsman. Proyectar resultado suministrado sobre el ejemplar concreto; no implementar su adquisición ni servicio de campaña.

**Consumidores/propiedad:** equipment_preparations.py/runes.py o mecanismo de ejemplares existente; compiler.py; equipo modular.

**Salida:** Bono sólo en el arma elegida, sin contaminar otra copia ni sobrevivir a su retirada; duración según cada contrato.

<details>
<summary>Selección de claves de C14a</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/campaign/exploration-and-income.yaml/@/*` | * |
| `S/hirelings/dramatis-personae/grade-2a.yaml/@/profiles/4/*` | * |
| `S/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.swordsmith.rule.honing/*` | * |

</details>

### C14b — Kits físicos y defensas intrínsecas

**Remate R01 integrado:** gibbets--iron-cage, cláusula intrinsic-save, ya está cerrada. Salvación intrínseca 5+ desde mechanic.iron-cage, sin pieza comprada ni duplicación; evidencia existente reutilizada.

**C14b cerrado, integración 2026-10-15.** A las siete filas reconciliadas se añade el cierre de `weapons-and-save`: el kit fijo de Witch Elf arma ambas manos con hojas élficas oscuras y Dark Venom, manteniendo Frenesí y defensa intrínseca. El coordinador conectó también la selección explícita de la espada al mismo kit; ambos casos focales pasan. Mano del Flautista y coraza 4+ conectadas; Att'la, Gibbets y retirada de equipo reutilizan consumidores existentes. CSV integrado con copia completa, conservación y control concurrente; evidencia restante reutilizada.

**6 cláusulas (6 YES).** Attla, Iron Cage de Gibbets, 4+ de House Guard, kit compuesto Dark Elf Corsairs, mano ocupada por instrumento y equipo perdido tras transformación. Separar armadura intrínseca de objeto portado; no cerrar weapons-and-save al resolver sólo el 5+.

**Consumidores/propiedad:** Datos de equipo; compilación/slots; modular/equipment.py y recomposición de rounds.py si procede.

**Salida:** Kit legal completo, manos correctas y defensas/bonos retirados o conservados según su procedencia real.

<details>
<summary>Selección de claves de C14b</summary>

| id (abreviado) | clause_id |
|---|---|
| `R/ghost-pirates-sar/*` | * |
| `B/cursed-cavalcade/*` | * |
| `B/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/*` | * |
| `B/house-guard-sc/equipment-access.yaml/@/equipment_lists/2/items/0/*` | * |
| `BT/lustria-savage-goblins/profiles.yaml/@/profiles/7/*` | * |
| `S/campaign/exploration-and-income.yaml/campaign.magical-artefact.attlas-plate-mail/*` | * |

</details>

### C15 — Alcance y fuentes residuales: NO despachar como implementación masiva

**C15 cerrado, integración final 2026-10-17: 16/16.** A las dos herencias enanas y once cierres residuales se añaden las tres filas de Warpaint y Elven Wine. Preparaciones individuales con destinatarios canónicos: Warpaint da ward 6+ y Elven Wine inmunidad sólo a Fear; aplicación previa a batalla y duración de batalla, sin consumo por tirada ni productor grupal. Operadores existentes reutilizados, nuevas conexiones de catálogo/configuración y efecto. Evidencia del ejecutor reutilizada sin repetir pruebas. Tres filas finales integradas con snapshot, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Bloqueos editoriales/web ajenos siguen señalados sin presentarlos como corregidos; detalle en C15-remaining-completed.md.

**Subfamilia C15-Dwarf-inheritance cerrada, integración 2026-10-17: 2/2.** Herencia automática para los destinatarios enanos de Guildsmen y Slayers, excluyendo al Recordador Humano suministrado y evitando la compra o duplicación de las reglas raciales. Consumidores de combate reutilizados; corregida concesión band en vez de selectable. Dos filas integradas con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente; evidencia focal del ejecutor reutilizada. Artefacto web bloqueado por conflicto de traducciones registrado, sin nuevas ejecuciones del generador. No implica cierre del resto de C15.

**16 cláusulas (16 YES).** Ropas sin texto, Wheelo, comandos suministrados, Sermons, Snotling count-as-one, customización Machine-Ogre y herencias pendientes. Mantener las referencias de fuente ya recuperadas. Distinguir construcción de productores excluidos. Este paquete es de disposición/resolución técnica residual, no avance de motor acreditado.

**Consumidores/propiedad:** Fuente y consumidores explícitos de cada contrato; sin cambios globales.

**Salida:** Cada parte tiene disposición concreta; no convertir falta de fuente en una regla inventada ni marcar capacidad nueva por reconciliación.

<details>
<summary>Selección de claves de C15</summary>

| id (abreviado) | clause_id |
|---|---|
| `item/eshin_assassin_clothes` | * |
| `item/mage_robes` | * |
| `item/wizard_robe` | * |
| `R/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-combat-rules` |
| `R/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-combat-rules` |
| `R/snotlings-web/shoota-teams--teamwork/*` | * |
| `R/snotlings-web/snotling-mobs--teamwork/*` | * |
| `B/metal-mongers-mim/profiles.yaml/*` | * |
| `B/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/2/equipment_restrictions/1/*` | * |
| `B/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/13/*` | * |
| `B/snotlings-web/*` | * |
| `BT/chaos-streets-mordheim-inhabitants/profiles.yaml/@/profiles/0/*` | * |
| `BT/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--single-use` |
| `S/campaign/magic.yaml/spell.commands.art-thou-ready-to-die-fighting/*` | * |
| `S/campaign/magic.yaml/spell.commands.follow-me-mine-pugnacious-ones/*` | * |

</details>

### H01 — Consecuencias reutilizables de Aenur, Veskit y Slayer

**H01 cerrado, integración final 2026-10-17.** Seis filas Slayer finales integradas, además de Aenur/Veskit y Ogre Bodyguard ya reconciliados. Nueva decisión opcional de Ferocious Charge, con ambas mitades del efecto y caducidad; cinco consumidores existentes reutilizados. El coordinador añadió la compuerta de turno perdido y comprobó los dos casos de composición afectados, correctos; no repitió el resto. Snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Fallos de compilación de Buccaneer señalados en H01-Slayer-completed.md para la integración final, sin atribución inventada ni cierre ficticio.

**Subfamilia H01-Aenur cerrada, integración 2026-10-17: 4/4.** Referencias de Ienh-Khain resueltas al operador real, +1 Fuerza aplicado una vez y críticos desde 5 conservando sus límites ordinarios. Comportamiento existente reconciliado, sin código nuevo de producción. Evidencia del ejecutor reutilizada sin repetir pruebas. Cuatro filas integradas con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. No implica cierre de todo H01.

**Subfamilia H01-Veskit cerrada, integración 2026-10-17: 5/5.** Garras A4 sin duplicación, F5 y modificador total -3, cuerpo metálico 3+, No Pain e inmunidad a psicología ya funcionaban; cinco filas reconciliadas sin código nuevo de producción. Evidencia del ejecutor reutilizada, sin repetir pruebas. CSV integrado con snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente. No reasignar Veskit ni interpretar este cierre como cierre de todo H01.

**16 cláusulas (16 YES).** Ienh-Khain +1 S y críticos 5–6; Veskit garras/cuerpo/No Pain; Slayer Hard Head/Hard to Kill/Monster Slayer/Berserker/Ferocious Charge. Prioridad posterior a compartidas; antes de asignar dividir por operador real, sin encargar revisar los tres perfiles enteros.

**Consumidores/propiedad:** Catálogo hirelings; operadores de armas, heridas y carga existentes; compiler.

**Salida:** Consecuencias individuales conectadas sin duplicar estadísticas ya impresas ni reutilizar la identidad de otra arma.

<details>
<summary>Selección de claves de H01</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/hirelings/dramatis-personae/core.yaml/@/profiles/0/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.item.ienh-khain.rule.critical/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.item.ienh-khain.rule.strength/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.integrated-warplock-pistols/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.metallic-body/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.no-pain/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.unfeeling/*` | * |
| `S/hirelings/hired-swords/core.yaml/*` | * |

</details>

### H02 — Kits y variantes individuales de personajes

**H02 cerrado, integración 2026-10-17: diecinueve filas finales.** Kits canónicos Corsairs, alternativas completas Gaoler/Black Orc/Centauro, Johann, objetos particulares, modos del bastón de Nicodemus, personas y equipo fijo conectados; Ulli y exclusión Horseman reutilizados. Evidencia focal del ejecutor aceptada sin repetir baterías. CSV integrado con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. La expectativa antigua de admisión de Drenok sigue señalada en la entrega, fuera de este cierre.

**23 cláusulas (1 LATER, 1 NO, 2 UNCLASSIFIED, 19 YES).** Ulli individual (no pareja), elección de armas, ceremonial scythe, Beastlash, Johann, Nicodemus, personas y kit personal. La agrupación comparte construcción de kits, no autoriza implementar todas las reglas de todos estos perfiles. Elementos stickfire/vermin pots/candle tree requieren fuente y alcance antes de actuar.

**Consumidores/propiedad:** resolveHirelingKit; fuentes hirelings; mappings de equipo.

**Salida:** Sólo los kits y variantes asignados quedan seleccionables; control de inventario fijo preservado, fuentes ausentes explícitas.

<details>
<summary>Selección de claves de H02</summary>

| id (abreviado) | clause_id |
|---|---|
| `B/dark-elf-corsairs-mou/profiles.yaml/@/profiles/4/*` | * |
| `B/dark-elf-corsairs-mou/profiles.yaml/@/profiles/5/*` | * |
| `S/campaign/trading-post.yaml/@/items/132/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.johann-the-knife.rule.crimson-shade/*` | * |
| `S/hirelings/dramatis-personae/core.yaml/hireling.dramatis.johann-the-knife.rule.poisoned-weapons/*` | * |
| `S/hirelings/dramatis-personae/grade-1a.yaml/*` | * |
| `S/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/3/*` | * |
| `S/hirelings/dramatis-personae/grade-2a.yaml/@/profiles/3/*` | * |
| `S/hirelings/dramatis-personae/grade-2b.yaml/@/*` | * |
| `S/hirelings/dramatis-personae/rules.yaml/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/@/profiles/11/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/@/profiles/2/*` | * |
| `S/hirelings/hired-swords/grade-1b.yaml/@/profiles/28/*` | * |
| `S/hirelings/hired-swords/grade-1c.yaml/@/profiles/2/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/@/profiles/1/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/@/profiles/10/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/@/profiles/13/*` | * |
| `S/hirelings/hired-swords/rules.yaml/*` | * |

</details>

### H03a — Proyección y psicología de hirelings

**H03a cerrado, integración final 2026-10-17.** A los quince cierres previos (incluido Ogre Bodyguard) se añade Gwen/leadership-distraction; Solkan ya estaba cerrado. El texto completo confirma la pérdida del turno propio entero. Nueva condición suministrada bloquea ataques y acciones propias voluntarias, consume el estado una vez y conserva contratos pasivos/obligatorios y respuestas del turno ajeno. Ocho casos del ejecutor reutilizados sin repetir pruebas. Una fila final integrada con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente. Detalle en H03a-completed.md.

**18 cláusulas (18 YES).** Miedo de traits/profiles, Dark Mage, Fallen Sister, Busty Gwen y Solkan. Las marcas, juicio y cargas son consecuencias distintas; no cerrar Solkan por conectar inmunidad. Separar en encargo de proyección existente y encargo de juicio si éste falta.

**Consumidores/propiedad:** Facts/compile_fighter; psicología y liderazgo; rounds para juicio.

**Salida:** Identidad/rasgo llega al consumidor real; consecuencias compuestas completas dentro del subalcance asignado.

<details>
<summary>Selección de claves de H03a</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dark-mage.rule.despise-despoilers/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dark-mage.rule.self-assured/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.the-fallen-sister.rule.ashamed-and-afraid/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--compulsory-charge`; `witch-finder--scope--inquisitor-judgement`; `witch-finder--scope--inquisitor-state` |
| `S/hirelings/traits.yaml/*` | * |

</details>

### H03b — Recursos y variantes de hirelings

**H03b cerrado, integración 2026-10-18: nueve filas finales.** Innominatus recibe su arma única y reglas intrínsecas; Oracle, Snorri, Belandysh y ramas del Emisario reconciliados mediante consumidores existentes. Evidencia focal del ejecutor reutilizada sin repetir pruebas. Snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control concurrente correctos. Consulta final del registro: cero filas pendientes. Esto cierra la cola de cláusulas, no la validación integrada del motor ni los fallos conocidos del bloque 4.

**10 cláusulas (1 UNCLASSIFIED, 9 YES).** Foole, Myrmidia Oracle, Snorri, Belandysh y Emissary patron. Patrones de dados/recursos y variantes son diferentes: asignar recursos o patron/profile por separado, no todo el grupo de una vez. Snorri ya tiene resultados compilados; no repetir implementación.

**Consumidores/propiedad:** OwnedRollDice; condiciones/compilador; datos de variantes de hirelings.

**Salida:** Elección de variante y recursos consumidos/caducados según fuente; sin doble aplicación ni productor externo simulado.

<details>
<summary>Selección de claves de H03b</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/0/*` | * |
| `S/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/2/*` | * |
| `S/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.poison-ring/*` | * |
| `S/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.snorri-nosebiter.rule.drunk/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/@/profiles/5/*` | * |
| `S/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/*` | * |
| `S/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.marks-of-myrmidia/*` | * |

</details>

### R01 — Remate de tres filas pendientes de bandas

**R01 cerrado, integración 2026-10-17: 3/3.** Tres cláusulas reconciliadas mediante capacidades existentes de C01b/C04b/C14b, con discriminador añadido de selección por fase. Snapshot íntegro, conservación de 4.556 claves/textos/huellas/notas y control concurrente correctos; evidencia focal del ejecutor reutilizada sin repetir pruebas. La expectativa antigua de veneno de Zombies queda señalada en R01-completed.md para el cierre integrado, no se ha corregido ni usado para invalidar la consecuencia distinta de ataque natural.

**Encargo registrado 2026-10-17.** Agrupa tres claves existentes que aún constan
pendientes pese a las entregas anteriores de sus paquetes. No añade cláusulas,
no altera el corte inicial de 597 y no vuelve a auditar los paquetes completos.

| Paquete original | id | clause_id |
|---|---|---|
| C04b | `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` |
| C14b | `rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/profile.equipment-restrictions` | `intrinsic-save` |
| C01b | `source/bands/mordheim/undead/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` |

**Salida:** listas Maldred según fase suministrada, salvación de armadura
intrínseca 5+ de Gibbets y ataque propio sin penalizaciones del perfil Undead
conectados y accesibles. Reutilizar evidencia de los paquetes originales;
implementar sólo huecos reales y preparar los tres cierres CSV, sin escribirlos.
Entrega única: `deliveries/R01-completed.md`. Aplican íntegramente los límites
del plan: casos mínimos, E2E excluidos, un escritor por archivo, sin nuevos
subsistemas de campaña ni restauraciones completas, commits o pushes.

### M00 — Misericordia del Conde — INTEGRADO


**1 cláusulas (1 YES).** No reasignar. Arma física distinta de la Misericordia de Cursed Cavalcade; espada y tabla de heridas 1–3/4–6 con excepción de No Muertos.

**Consumidores/propiedad:** Catálogos de armas, execution, mappings; consumidor de heridas.

**Salida:** Entrega ya encargada; integración por el coordinador.

<details>
<summary>Selección de claves de M00</summary>

| id (abreviado) | clause_id |
|---|---|
| `S/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/*` | * |

</details>

## Límites de este análisis

No se han ejecutado tests, modificado código/datos ni escrito el CSV. Se ha contrastado la ruta compartida de elegibilidad/compilación y algunos consumidores representativos; el resto conserva la incertidumbre funcional que declara el CSV. No interpretar el tamaño de un paquete como número de funciones nuevas. Antes de despachar, seleccionar las variantes concretas del paquete y reservar los archivos que realmente necesita. No volver a hacer este análisis completo para preparar cada prompt.
