# C05b-Solkan — carga obligatoria, juicio y estado del Inquisidor

**Estado 2026-10-17: tres cláusulas cerradas e integradas por el coordinador.**
Las consecuencias admitidas ya estaban conectadas y consumidas: esta entrega
reconcilia su estado y añade discriminadores, sin nueva implementación de producción.
El acceso a Strength por
`deity.solkan` se conservó sin cambios.

## Capacidades antes → después

1. **Carga obligatoria (`compulsory-charge`).** Antes: el mecánico
   `mechanic.solkan-witch-finder` existía, pero la obligación no tenía condición
   suministrable ni discriminador de activación. Después: la ruta canónica es
   `deity.solkan` + `skill.witch-finder` + `condition.witch-finder-charge`;
   `compile_fighter` rechaza la condición si falta la marca o la habilidad elegida y
   `initialize_duel` la rechaza si el enemigo no pertenece a las identidades impresas
   (Caos, warlock, nigromante, hechicero, warp-tainted) o si no hay carga real. Solo se
   resuelve la carga suministrada: visibilidad, mapa, movimiento y elección de objetivo
   siguen excluidos, como ya declaraba la regla.
2. **Juicio del Inquisidor (`inquisitor-judgement`).** Antes: `_inquisitor_brands`
   consumía la tabla, pero no había prueba de que la capacidad perteneciera únicamente
   a la marca elegida. Después: al inicio de cada nueva ronda de combate, cada
   Inquisidor tira un D6 contra el enemigo; un 6 tira D66 sobre las 36 filas canónicas y
   aplica esa fila como marca persistente mediante `apply_brand`. Se omiten No Muertos,
   seguidores del Caos y grupos de banda caóticos. La ronda siguiente vuelve a tirar el
   juicio y conserva la marca ya aplicada. Sin la habilidad Inquisitor no se tira ni se
   prepara la tabla.
3. **Estado del Inquisidor (`inquisitor-state`).** Antes: el effect-set publicaba
   `mechanic.psychology-immunity`, pero faltaba evidencia canónica de su consumo.
   Después: el Inquisidor inmune no realiza pruebas de Psicología (Fear incluido) por
   los consumidores existentes, mientras un Priest con la variante pero sin la marca
   elegida las conserva. `never leaves combat` queda clasificado **NO** por la decisión
   vigente de que escape voluntario, retirada y ruptura de contacto están fuera del duelo
   1v1; no existe productor de salida que conectar y el duelo termina por lesión.

## Archivos propios

- `tests/python/construction/test_c05b_hireling_closures.py`:
  `test_the_supplied_compulsory_charge_belongs_to_the_marked_witch_finder_alone`.
- `tests/python/combat/modular/test_t13_residual_lifecycle.py`:
  `test_the_inquisitor_judgement_belongs_to_the_chosen_mark_alone`.
- Este documento.

No se modificó código de producción ni la KB: los tres consumidores ya existían
(`compile_fighter`, `initialize_duel`, `_inquisitor_brands`/`apply_brand`, psicología y
liderazgo); lo que faltaba era el discriminador de activación por variante/marca y la
evidencia de cierre. No se duplicó ningún binding ni operador.

## Comprobación mínima

Ejecutados los casos seleccionados de los dos archivos afectados (más los existentes
reutilizados del mismo bloque):

```
pytest ... test_the_supplied_compulsory_charge_belongs_to_the_marked_witch_finder_alone
        ... test_the_inquisitor_judgement_belongs_to_the_chosen_mark_alone
        ... test_canonical_witch_finder_supplied_attempt_requires_named_enemy_and_mark
        ... test_inquisitor_brand_is_dynamic_once_per_success_and_rechecks_every_combat_phase
        ... test_inquisitor_does_not_roll_or_brand_excluded_enemy (3 exclusiones)
        ... test_canonical_inquisitor_prepared_chart_reaches_live_combat_consumer
        ... test_canonical_inquisitor_psychology_immunity_reuses_normal_fear_consumer
9 passed, exit 0
```

Salida guardada en `%TEMP%/c05b-solkan-tests.txt`. Sin E2E, sin suites globales, sin
comparaciones con HEAD, sin commit ni push.

## Propuestas CSV (sin `apply --write`)

Integración del coordinador completada: snapshot íntegro nuevo, prepare y preview
correctos, apply --write de tres filas con conservación de 4.556 claves/campos
protegidos/notas y control concurrente. Consumidores y verificaciones anteriores
acumulados, sin sustituirlos. Evidencia en
`%TEMP%/solkan-coordinator-e6s36o2q/`. Se reutilizó la salida de nueve casos del
ejecutor, sin repetir pruebas. El ejecutor no escribió el CSV.

Paquete: `%TEMP%/c05b-solkan-prepare.json`; `prepare` exit 0 y snapshot aún vigente
(sha256 del CSV idéntico al preparado). Tres filas, sólo `pending`, `consumer`,
`verification` y `notes`; notas anteriores conservadas por append.

| `clause_id` | `pending` | consumidores | verificación |
|---|---|---|---|
| `witch-finder--scope--compulsory-charge` | `{"work":"assessment"}` → `{}` | `compile_fighter`, `state.py::initialize_duel` | 1 nuevo + 1 existente |
| `witch-finder--scope--inquisitor-judgement` | `{"work":"assessment"}` → `{}` | `_prepared_mutation_options`, `_inquisitor_brands`, `resolve_round`, `apply_brand` | 1 nuevo + 3 existentes |
| `witch-finder--scope--inquisitor-state` | `{"work":"assessment"}` → `{}` | `resolve_local_leadership`, `resolve_fear`, `initialize_fighter` | 2 existentes de otro archivo admitido |

`clause_scope`, `semantic_contract`, `relation` y `effect_id` no se tocan: la
equivalencia con un único operador no está demostrada para un texto compuesto.

## Bloqueos exactos

- `never leaves combat` (parte de `inquisitor-state`): excluido por
  `docs/decisions/design-rulings.md#voluntary-escape-does-not-belong-to-combat-lab--2026-10-04`;
  no se simuló ningún escape.
- Visibilidad, mapa, movimiento y selección de objetivo de Witch-finder: fuera del
  duelo 1v1; la carga real se recibe como hecho suministrado.
- No quedan consecuencias admitidas pendientes en estas tres cláusulas.
