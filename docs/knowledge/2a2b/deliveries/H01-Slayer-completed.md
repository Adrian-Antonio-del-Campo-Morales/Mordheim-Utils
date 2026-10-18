# H01 — Seis cláusulas del Dwarf Troll Slayer

**Integración final del coordinador, 2026-10-17: 6/6 cerradas.** Seis filas
aplicadas con snapshot completo, prepare/preview y control concurrente;
4.556 claves, textos, huellas y notas conservados, verificación previa acumulada.
Evidencia de integración: `%TEMP%/h01-coordinator-7an2wsuw/`.

Remate mínimo de composición: Ferocious Charge tampoco solicita su declaración
voluntaria durante un turno propio perdido por Gwen. Guarda añadida en el mismo
consumidor y discriminador incorporado al caso existente; los dos casos afectados
(Ferocious Charge y turno perdido) pasan, salida en
`%TEMP%/h01-coordinator-composition.txt`. Base anterior conservada en
`%TEMP%/h01-coordinator-base-dcuwvqn_/`. Los otros resultados del ejecutor se
reutilizaron sin repetir baterías. Sin E2E, commit ni push.

**Estado: las seis filas resueltas, paquete CSV preparado para el coordinador,
2026-10-17.** Base compartida `2A2B`, HEAD `a1f92653`, sin commits ni pushes.
Veskit, Aenur y Ogre Bodyguard no se reabrieron; el remate de C15 sobre
consumibles es ajeno a esta entrega.

## Implementación nueva frente a reutilización

- **Nueva (una sola capacidad):** el `may` impreso de Ferocious Charge no tenía
  consumidor. `rounds.resolve_round` pide
  `round.N.side.ferocious-charge` en la ronda de carga y, si se declina, retira
  la etiqueta sólo de la copia de ataque de esa ronda: ni se dobla el pool ni se
  paga el −1. Al aceptar, `build_attacks` dobla antes del ataque de segunda
  arma y `prepare_hit_context` resta uno. La decisión no se repite en rondas
  posteriores y el perfil compilado conserva la habilidad para otra carga.
- **Reutilizado sin cambios:** `trait.concussion-immune` y `skill.hard-to-kill`
  en `_injury_context`/`injury_condition`; `skill.monster-slayer` en
  `prepare_wound_context` (tope 4, máximo y no sustitución); `skill.berserker`
  en `prepare_hit_context`; `mechanic.psychology-immunity` en `resolve_fear`.
  Los bindings y `runtime` de las seis reglas ya existían en
  `catalog/hirelings/hired-swords/core.yaml`, y la admisión de grado core ya
  estaba abierta en `combat_packages`. No se duplicó ningún bono ni operador.
- **Selección:** las tres habilidades son `grant: selectable`; no se conceden
  por compilar el perfil. Se preservan las restricciones de selección específicas
  de cada origen; no se trasladan excepciones de otra banda al perfil contratado.

## Las seis disposiciones

| `clause_id` | `effect_id` | Resultado observable |
|---|---|---|
| `hard-head-ignores-mace-and-club-rules` | `trait.concussion-immune` | maza con total 2 → Derribado; un 6 sigue Fuera de Combate |
| `hard-to-kill-injury-chart` | `skill.hard-to-kill` | 5 → Aturdido; sólo 6 Fuera de Combate |
| `monster-slayer-wounds-on-four` | `skill.monster-slayer` | S3 vs R4 pasa de 5+ a 4+; S5 por arma a dos manos conserva 3+ |
| `whole` (Berserker) | `skill.berserker` | +1 a impactar sólo en el turno de carga |
| `whole` (Ferocious Charge) | `skill.ferocious-charge` | elección: doblar Ataques con −1 a impactar; declinar deja pool y tirada normales; caduca con la carga |
| `psychology-immunity` | `mechanic.psychology-immunity` | el portador no tira Liderazgo contra un Ogro que causa Miedo; un cargador ordinario sí |

## Paquete preparado (sólo `prepare`, sin `--write`)

`%TEMP%/h01-prepared2.json`, huella del CSV
`c8d2ceeb66f653e0b692c79606eed52e131e2de1063d3552c29521c9977cbffa`,
**6 cambios** por `(id, clause_id)`, todos con `pending: {}`, `verification`
ampliada con `executed` + nodo de prueba y nota `[H01 2026-10-17]` que conserva
las notas previas. `apply` en seco validó snapshot y conservación con EXIT=0
(`%TEMP%/h01-dryrun.txt`). **No se ejecutó `--write`** y el CSV conservó su
huella.

## Archivos propios

- `packages/python/combat-engine/mordheim_combat/modular/rounds.py` (un solo
  bloque: la compuerta de Ferocious Charge antes del pool de ataques).
- `tests/python/combat/modular/test_h01_dwarf_troll_slayer.py` (nuevo).
- Esta entrega.

No se editaron el CSV, el catálogo de hirelings ni archivos de otros agentes.

## Evidencia mínima

`python -m pytest tests/python/combat/modular/test_h01_dwarf_troll_slayer.py -q`
→ **6 passed**, EXIT=0 (`%TEMP%/h01-final-run.txt`; primera salida equivalente en
`%TEMP%/h01-first-run.txt`). Cubre compilación canónica
con las intrínsecas una vez y las habilidades sólo al elegirlas; conmoción de
maza frente a lesión genérica; banda 5 Aturdido / 6 Fuera de Combate; tope de
herida con control de Fuerza mejor; +1 de Berserker sólo al cargar; Ferocious
Charge aceptado (3 ataques, impactos a 4+), declinado (2 ataques, 3+ sin
penalización) y sin decisión ni penalización en la ronda siguiente; Deathwish
sin tirada de Miedo frente al Ogro y control negativo con un cargador normal.

Vecinos ejecutados una vez: `test_h03a_hireling_psychology.py` y
`test_t13_residual_lifecycle.py` → **85 passed, 2 failed**
(`%TEMP%/h01-neighbours.txt`). Los dos fallos ocurren al compilar
`shallows-beasts-mim/buccaneer` por disponibilidad de `weapon.mace`
(`restrictions.py`/`eligibility.py`), antes de resolver ninguna ronda y fuera de
este diff; origen no atribuido y no reparados por estar fuera de alcance.

## Bloqueos exactos

Ninguno propio. El artefacto web no se regeneró porque no se tocó ningún YAML.
Quedan fuera, sin reabrir: el `all-alone` de Deathwish (subsistema de grupo ya
excluido), el productor de disparo/alcance del perfil y cualquier port
vectorial/nativo. No se ejecutaron E2E, suites globales, parity ni cobertura.
