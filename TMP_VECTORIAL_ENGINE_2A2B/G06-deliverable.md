# G06 — Rondas, recuperación e integración del motor vectorial (entrega)

## Base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (copia compartida; no se creó otra).
- HEAD `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más todos los cambios locales, incluidas las entregas G00–G05 y las correcciones posteriores de G04.
- Archivos ajenos intactos: `_types.py`, `_state.py`, `_attacks.py`, `_operators.py`, `_equipment.py`, `_psychology.py`, `_leadership.py`, `kernel.py`, fachada y CSV.
- CSV canónico **no escrito**: SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. Sin commits ni pushes.

## Resumen

El bucle de rondas de `_simulate_batch_core` reproduce ahora el orden de
`modular/rounds.py::resolve_round` en el alcance de sus helpers y estados disponibles:
validación y muestreo de cargas, equipo efectivo por fila con recuento y prioridad por
grupo, características perezosas, recuperación propia (Revenant, Alquimia), Drunk,
animosidad, transformación Bitten, Estupidez, Fear, puertas de encanto (Eye Pendant,
Tranquil Fauna, Hipnotista, Deceive/Hypnotize, Seducción), danzas, declaraciones de pool,
Shifty en su nivel de prioridad, Crude Belch (halfling y ogro), Eagles, último mordisco,
Deathblow, Great Thirster, `netted`, Massively Built y equipo efectivo en cada ataque.

La puerta de admisión de G00 sigue rechazando las capacidades: la conexión está hecha y
comprobada, pero retirar cada rechazo es decisión del coordinador (§7).

## Archivos y funciones

| Archivo | Cambio |
| --- | --- |
| `vectorized/_driver.py` | `_RoundLedger` y `_round_ledger` (resultados de ronda sin columna: Drunk, animosidad, belch ogro, entrada/control de encanto, Deathblow, Bitten, penalización de impacto). Helpers `_choose`, `_crude_belch_ogre`, `_charm_gates`, `_apply_opponent_leadership`, `_select_shadow_dance`, `_tagged_rows`, `_select_attack_replacement`, `_select_shifty_weapon`, `_nominated_strike`, `_strike_first_fighter`, `_row_equipment`, `_equipment_groups`, `_resolve_attacks_by_equipment`, `_crude_belch_losses`, `_great_thirster_frenzy`. Bucle de ronda reescrito (10 columnas de evento). |
| `vectorized/_recovery.py` (**nuevo**) | `revenant_recovery`: 5+ una vez por turno propio, tope de heridas máximas. |
| `vectorized/_alchemy.py` (**nuevo**) | `AlchemyResources`, `alchemy_resources`, `resolve_alchemist`: Backley (T, restauración exacta de S/I) y adicción (6 cura y +1 S/T sin Vigortia). |
| `tests/python/combat/vectorized/test_runtime_regressions.py` | Un caso nuevo de la puerta de Estupidez conectada. |
| `TMP_VECTORIAL_ENGINE_2A2B/G06-deliverable.md` | Este documento. |

## Conexiones completadas

### Cargas, contacto y equipo

- `validate_duel_start` antes de inicializar; muestreo solo de cargadores legales
  (`charge_allowed`); contacto base y cargas obligatorias respetados; `engage` por
  contacto/carga como `initialize_duel`; Fear puede reducirlo y la ronda termina.
- `equipment_for_rows` proyecta el equipo de cada simulación (manos rotas, mutación,
  transformación, forma lobo). `_equipment_groups` agrupa las filas por par de equipos y
  **el recuento (`attack_count`, `round_weapon_attack_count`, `opposed_attack_count`), la
  prioridad y la iniciativa se calculan dentro de cada grupo**. `resolve_attacks` recibe el
  arma y las defensas de la fila.
- Evidencia: con A=1, espada con `attacks_bonus=2` y `broken_hands[0]=1`, la fila 0 recibe
  `1` ataque (puño) y la fila 1 `3` (espada); la proyección usada en mordiscos, Eagles,
  Shifty y Deathblow es la misma.

### Características perezosas

- `initialize_fighter(..., lazy_inconsistency=True)` y
  `refresh_random_characteristics(..., lazy_inconsistency=True)`.
- `require_characteristics` para `WS/S/T/I/A` en la primera operación de la ronda que los
  lee (antes de prioridad y ataques).
- Evidencia: Inconsistency con WS aleatoria → tras inicializar `WS=[5,5,5]`,
  `random_rolled=[0,0,0]`; tras `require_characteristics(("WS",))` → `[5,5,1]`,
  `random_rolled=[1,1,1]`.

### Psicología, Liderazgo y encanto (G05)

- Registros `leadership`, `psychology`, `alchemy` y `_RoundLedger` vivos durante toda la
  simulación, uno por combatiente y fila.
- Estupidez por lado sobre sus filas activas; Drunk 1 añade Stupidity solo a esas filas;
  Fear en ronda 0; animosidad en el turno propio (1, o 1-2 con Rowdy).
- Puertas que anulan el pool: Eye Pendant (No Muerto), Tranquil Fauna (animal; el handler
  cualificado puede pasar), Hipnotista (entrance/release), Deceive/Hypnotize
  (Liderazgo propio en Deceive), Seducción (control persistente con liberación en el turno
  propio) y `animal-friendship`/`mechanic.animal-friendship` vía `opposed_attack_count`.
- `apply_opponent_leadership`: Enchanting Beauty y Questing Vow.
- **Pendiente**: `fear_hit_sixes` se escribe pero `_attacks.py` no lo consume (§7.1).

### Ronda y efectos

- Revenant y Alquimista al inicio del turno propio; Bitten transform (1 revierte, 6 entra y
  descarta equipo); Drunk; Estupidez; Fear.
- Danzas: `select_shadow_dance` con `last_shadow_dance` por lado (no repite la anterior);
  whirling-death +1 lesión, storm-of-blades +1 ataque, shadows-coil y woven-mist activas.
- Declaraciones: Wraith Touch, vómito, bastón serpiente, Anvil Head y Deathblow opcionales;
  Shifty +1 al pool y ataque propio **en su nivel de prioridad** (el arma nominada se
  sube a Strike First como en el modular y resuelve antes que el evento ordinario del
  mismo portador); Crude Belch halfling (pierde un ataque ordinario) y ogro (-1 a impactar,
  una vez por batalla); Eagles Strike First; último mordisco tras ambos pools; Deathblow
  con el pool capturado si el portador cae antes de actuar; Great Thirster activa Frenesí.
- `mechanic.nominated-strike-first` (Instinctual Violence): la oferta recorre la
  asignación real (`allocate_attack_weapons`) y el ataque nominado conserva su arma y su
  ranura, entra en el nivel Strike First y se resta del pool ordinario.
- `mechanic.noblesse-stomp`: ataque natural extra contra un objetivo Derribado,
  inmediatamente después del evento ordinario del portador.
- `netted`: en el turno propio se libera la red, la fila queda Derribada y **no se levanta
  ese turno**; las filas aún con red no atacan.
- Massively Built y Electrical Touch (desempate diferido) conectados.

## Comandos ejecutados y resultados

```text
python -m pytest tests/python/combat/vectorized -q
  -> 14 failed, 115 passed
     Los 14 son los mismos fallos previos de catálogo/construcción (rule_families_a/b,
     shared_families, random-profile, frantic-priority); ninguno pasa por el driver.
     +1 respecto a la base por el caso nuevo.

python -m pytest test_vectorized_engine.py test_runtime_regressions.py \
                 test_observations.py test_psychology_vectorized.py -q
  -> 2 failed, 74 passed   (solo los dos fallos conocidos)

python -m pytest test_runtime_regressions.py -q -k "stupidity_gate"
  -> 1 passed
  # Con la puerta de Estupidez desconectada el mismo caso falla (comprobado y restaurado).

sha256(sources/knowledge/verification/clause-contracts.csv)
  -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731
```

Sondas puntuales (no añadidas al repositorio; `require_optimized_support` sustituido para
poder ejercer capacidades aún en la puerta):

```text
Lazy Inconsistency: [5,5,5]/[0,0,0] -> [5,5,1]/[1,1,1] tras pedir WS.
Recuento por grupo con broken_hands[0]=1: fila 0 puño 1 ataque; fila 1 espada 3 ataques.
Estupidez Ld 0, 200 filas, 2 rondas: rival 563 heridas con la regla vs 490 sin ella.
Drunk, animosidad, netted, Eye Pendant, Tranquil Fauna, danza, Hipnotista, Deceive,
Seducción, Eagle, último mordisco, Deathblow y belch ogro: ejecutan sin excepción y con
efecto direccional correcto (p. ej. netted 0-47 victorias; Eye Pendant 4-0; danza 6-3).
Instinctual Violence y Noblesse Stomp: con las etiquetas inyectadas, la traza registra
`round.1.first.strike-first` y `round.1.first.stomp` y la partida termina normalmente.
Shifty: con el arma nominada de off-hand la traza de una fila muestra
`round.0.second.shifty` **antes** de `round.0.second` (antes se añadía después de todo).
Backley: S 2->3, I 2->3, penalizaciones a (); Revenant: 2->3 heridas.
```

Comprobaciones **no** ejecutadas: paridad G07, matrices `fast`/`full`, benchmark G08, E2E,
lint (`ruff` no instalado).

## Caso nuevo

`test_stupidity_gate_silences_only_the_rows_that_fail` (`test_runtime_regressions.py`).
Cubre el hueco concreto de que ningún test llamaba a la puerta de Estupidez desde el driver:
con Ld 0 el portador pierde su pool y hace menos daño; sin la llamada los dos lotes son
idénticos y el caso falla. Monkeypatchea `require_optimized_support` porque la capacidad
sigue en la puerta de G00; no la retira. Sin pruebas modulares ni E2E.

## Pendientes y peticiones

1. **G04 — `_attacks.py`**: aceptar `needs_sixes: np.ndarray | None` y forzar impacto solo
   con 6 natural en melé. Sin eso, `fear_hit_sixes` queda escrito pero sin consecuencia.
2. **G02/coordinador**: `grappled`/`grappling` no tienen columna; sin ellas el agarre
   completo (escape, presa, tentáculo retenido) no puede conectarse. Propuesta: columnas
   `grappled`/`grappling` o un `_RoundLedger` ampliado con acuerdo de G02. Mientras tanto
   `opposed_attack_count(defer_grapple=True)` ya difiere la pérdida opcional del tentáculo,
   pero no hay estado donde retener la presa.
3. **G06 pendiente**: `mechanic.denizens` (no tiene efecto declarado ni consumidor) y el
   caso exacto de Noble `count == loss == 1` con ataque extra, que conserva un ataque.
   No se declaran implementados.
4. **Coordinador — puerta NumPy**: pueden retirarse, tras su decisión, las claves cuyas
   consecuencias están conectadas: `mechanic.stupidity`, `condition.stupidity-exempt`,
   `condition.stupidity-failed`, `mechanic.causes-fear`, `mechanic.fear-human`,
   `mechanic.fear-immunity`, `mechanic.fear-reroll`, `mechanic.craven`,
   `mechanic.crude-belch-halfling`, `skill.shifty`, `mechanic.great-thirster`,
   `mechanic.curse-of-the-revenant`, `mechanic.centigor-drunken`,
   `mechanic.goblin-squabble`, `mechanic.fungus-rowdy`, `dance.*`, `mechanic.hypnotist`,
   `mechanic.lahmia-deceive`, `mechanic.lahmian-hypnotize`, `mechanic.lahmia-seduction`,
   `mechanic.lahmian-seduction`, `defence.eye-pendant`, `mechanic.taal-tranquil-fauna`,
   `mechanic.crude-belch-ogre`, `rule.eagle-friend`, `rule.strikes-last-bite`,
   `mechanic.death-blow`, `condition.alchemist-backleys-brew`, `condition.alchemist-addicted`,
   `condition.alchemist-aberrantius-vigortia`, `mechanic.bitten-transform`,
   `mechanic.electrical-touch`, `mechanic.nominated-strike-first`,
   `mechanic.noblesse-stomp`, `mechanic.leader-six` y el resto del liderazgo local,
   `defence.holy-relic`. **No** retirar `mechanic.beauty-of-the-sea` ni `mechanic.wheelo-impact`
   (Fear sí; su rama de impacto es de G04) ni claves cuya única consecuencia sea
   `fear_hit_sixes`.
5. **G07**: comparar el orden nuevo: cargas → equipo → recuperación → Drunk/animosidad →
   Estupidez → Fear → encanto → danza → reemplazo → recuento por grupo → Shifty →
   belch → silencios → prioridad por grupo → eventos → Eagles/último mordisco/Deathblow.

## Actualización 2026-10-21 (integración pre-G07)

Los dos pendientes propios que esta entrega dejó abiertos quedaron cerrados en
[INTEGRACION_PRE_G07-deliverable.md](INTEGRACION_PRE_G07-deliverable.md):

1. `fear_hit_sixes` ya se consume: `CombatState.fear_hit_sixes` recibe la máscara de
   `PsychologyResources`, el driver la refresca cada ronda y `_prepare_weapon_attack` la
   entrega a `hit_context(needs_sixes=...)`; solo las filas marcadas exigen 6 natural.
2. `grappled`/`grappling` existen en `CombatState` y el agarre completo está conectado:
   declaración del Gaoler, ataque natural único sin daño, prueba `S-2`, liberación por fase,
   pool silenciado y tentáculo retenido una vez por batalla.
3. Noble `count == loss == 1` con contribución extra conserva el ataque.

Siguen pendientes reales `condition.mim-no-hand-attacks`, la elección del arma perdida por
tentáculo, `mechanic.denizens` y `spawn-special-attacks` por arma.
