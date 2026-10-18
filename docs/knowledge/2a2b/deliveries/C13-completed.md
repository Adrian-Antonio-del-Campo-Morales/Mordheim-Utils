# C13 — Contagious y Rotten Body

**Estado:** integrado, cuatro cláusulas cerradas, 2026-10-15. Rama `2A2B`, HEAD `a1f92653`, checkout
`D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, con trabajo concurrente ajeno.
Base inicial: `bands/mordheim/skaven-clan-pestilens/special-rules.yaml` limpio en
HEAD (sin hunks de otro propietario); el fichero de prueba es nuevo.

**Capacidad:** antes, la regla nativa `Contagious` del Clan Pestilens de Mordheim
seguía `scope: LATER` / `implemented: NO` / `binding: null` y su predecesora
`Rotten Body` sólo aportaba `trait.poison-immune`: la pareja legal no compilaba
(`special rule is outside the executable duel runtime`). Ahora la misma pareja
canónica —`rotten-body` + `contagious`— compila con los traits `poison_immune` y
`contagious`, y la reacción se ejecuta en duelo modular real: herida de cuerpo a
cuerpo que deja al portador Fuera de combate → el atacante hace un chequeo de
Resistencia, un 6 natural siempre falla y cuesta una Herida automática, y Undead y
Possessed quedan exentos. Sin Rotten Body la selección se rechaza.

**Implementación nueva:** binding `trait.contagious` en la regla de
`skaven-clan-pestilens` (id de efecto renombrado desde el marcador
`unimplemented.*`), 9 líneas. **Reutilización sin cambios:** el operador
`aftermath._react_to_wound` y su rama Contagious, el helper de chequeo de
característica, el trait compartido de `lustria-clan-pestilens`, la compilación
`compile_fighter` y la puerta de prerrequisito de
`eligibility/index.ts::loadoutRestriction` (no modificada). El coordinador corrigió
un hueco concreto: la reacción ahora exige `outcome.melee_attack` y daño nuevo
positivo antes de considerar el estado OUT definitivo. Rescate y test se reutilizan.

**Comprobación:** `tests/python/combat/modular/test_t13_contagious_and_rotten_body.py`,
9 casos aprobados: acceso y prerrequisito en ambas rutas, destinatarios impresos
(rat-ogre rechazado), disparador definitivo frente a Derribado, rescate previo,
una sola reacción por herida resuelta, paso/fallo del chequeo y 6 natural, y
exención con un Tomb Guardian canónico. Se ejecuta por
`compile_fighter → initialize_duel → resolve_round` con `StrictDice`. Afectados
reejecutados: `test_stateful_rules.py -k spines_acid_blood` (1 aprobado) y casos de
esquema editorial de bandas; estas baterías adicionales no se repitieron.
El coordinador comprobó dos casos existentes de OUT/rescate con el consumidor
corregido y añadió un único negativo (daño no cuerpo a cuerpo o sin daño nuevo),
aprobado. La primera ejecución del negativo falló por faltar contexto de carga
en su fixture; se corrigió y sólo se repitió ese caso. Salidas:
`%TEMP%/c13-integration-trigger.txt` y `c13-integration-trigger-negative.txt`.
E2E no ejecutado ni tocado.

**CSV:** cuatro propuestas integradas mediante nueva preparación, preview y
`apply --write`, conservando las 4.556 claves, textos, huellas y notas y verificando
concurrencia. Snapshot/propuesta/salidas:
`%TEMP%/c13-integrated-4d4k_5ar`. La clave histórica `unimplemented.…` se conserva;
`effect_id` ya señala `trait.contagious`. No se necesita regenerar un inventario
para cerrar esta implementación. Sin pendientes de C13, commits ni pushes.
