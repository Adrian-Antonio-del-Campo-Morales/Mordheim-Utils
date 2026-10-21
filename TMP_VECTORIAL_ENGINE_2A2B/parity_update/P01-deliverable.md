# P01 — Catálogo de variantes, testigos y casos

## 1. Base recibida

- P00 revisión 4 aceptada como base de preparación, más las adendas **A8**,
  **A9** y **A10** de `COORDINATOR-progress-review.md`. No se reabre el contrato.
- Registro vivo: `sources/knowledge/verification/clause-contracts.csv`, sha256
  `2096df6eba24ed106b03a6033b1e438793dc1bc4bec40ac02b7423a8fc4056f3`
  (cambió por edición concurrente del propietario durante la revisión de P00).
- Inventario transferido: `P00-results/behaviour-inventory.csv`, sha256
  `58beba4428b676c88393605db7c6eb51bfe7f2b8a886bd4240ce29f7b09e4955`,
  1914 claves, 63 variantes. La copia de datos es
  `parity/_battery_keys.py` (generada una vez por el coordinador); P01 la importa
  y **no** lee `P00-results` en ejecución.
- Base de código conservada: el catálogo anterior (711 líneas) se corrigió y
  amplió; no se reconstruyó desde cero. No se ejecutaron motores ni campañas.

## 2. Archivos y símbolos

| Archivo | Cambio |
| --- | --- |
| `apps/combat-lab/mordheim_combat_lab/verification/parity/_battery_cases.py` | Reescritura del contrato y del catálogo: `Witness`, `WITNESSES`, `Variant`, `Obligation`, `VARIANTS`, `OBLIGATIONS`, `ProviderSpec`, `ContextSpec`, `BatteryCase`, `battery_cases`, `required_variants`, `resolve_context`, `validate_cases`, `validate_keys`, `validate_origins` |
| `tests/python/verification/test_parity_battery_cases.py` | Comprobante estructural mínimo (sin duelos) |
| `TMP_VECTORIAL_ENGINE_2A2B/parity_update/P01-deliverable.md` | Esta entrega |

No se editó `_battery_keys.py`, `_battery_runner.py`, `_specifications.py`,
`_replay.py`, `cli/commands.py`, el motor, la KB, el CSV canónico ni el corpus.

## 3. Contrato implementado

- **63 variantes** `Bxx.y`, ninguna «other»; **60 de duelo** y 3 estructurales/
  ambiguas (`B00.1`, `B09.1`, `B99.1`). Todas siguen `required=True` (A8): una
  entrada pendiente no reduce el denominador.
- **Testigo tipado por variante**: `Witness(name, kind, present, absent)` con
  `counter|flag|category|direct-result|hash`. `condition`/`wounds` son
  `direct-result` solo en B07/B15; `leadership-test-value` y `psychology-dice`
  son resultados medidos válidos en B11/B14 (A9). `acting-order` es categoría y
  `equipment` hash: no se evalúan con `>0`/«cero eventos».
- **Caso**: `id, level, variant, origin, first, second, rows, seed,
  maximum_rounds, context, decisions, decision_scope, observables, expect,
  positive_control, witness_value, also_covers, comparison, focused, requires,
  blocked_by, note`. Sin `keys`, `activation`, `family`, `support` ni
  `support_distance`.
- **Contexto**: `DuelContext` para hechos ya construidos; `ContextSpec` +
  `ProviderSpec` cuando hay aliados que compilar. `resolve_context(spec, root)`
  es el único puente perezoso (importa el compilador dentro de la función); P02
  compila los proveedores y conserva `LocalParticipant`/`distances`.
- **Dependencia externa explícita**: `blocked_by` con prefijo `state:`,
  `consume:`, `witness:` o `decision:`. El caso sigue presente y requerido; P02
  lo clasifica como `INCOMPATIBLE` con el propietario, nunca lo omite.
- **A10**: el positivo enfocado no lleva `positive_control`; el negativo usa
  `expect="absent"` y referencia al positivo con el mismo `focused`. Los pares
  reales de ausencia son B14.1 (6" vs 8"), B14.11 (primera vs segunda prueba) y
  B11.4 (condición cumplida vs no cumplida).

## 4. Cobertura preparada

- 80 casos: 10 `quick`, 23 `complete`, 6 `deep` y 41 casos base de variante.
- Perfil `quick`: 10 variantes (`B03.5`, `B04.1`, `B04.2`, `B06.1`, `B07.1`,
  `B07.2`, `B10.3`, `B11.1`, `B14.1`, `B15.1`), una por variante.
- `complete` representa las 60 variantes de duelo con al menos un caso; las 3
  estructurales/ambiguas se declaran aparte. Sin cuotas.
- `deep` añade composición y horizontes: miedo→parada, liderazgo→retest,
  horizonte de 12 rondas, recurso de un solo uso, espinas→varias heridas y
  transformación de equipo.

Casos reparados respecto a la revisión anterior:

| Caso | Corrección |
| --- | --- |
| `q04-natural-armour-six` | Piel natural de la banda del origen (`trait.natural-armour-save`), no armadura ligera |
| `q05-flammable-fire` | `weapon.brazier-iron` + `trait.flammable` materializados |
| `q11-black-hunger` | `skill_ids=("mechanic.black-hunger",)` |
| `q00-honorable` | `mechanic.honorable` + rival derribado; estado declarado como dependencia |
| `c04-parry-reroll` | Rodela en el defensor; el atacante no la lleva |
| `q10-leader-six` | `ContextSpec` con `ProviderSpec` y distancia 6"; sin tercer duelista |
| `q08-death-blow-optional` | Decisión de rechazo declarada |
| `c04-highest-injury` | Identidad `highest-injury-result-applies` |
| `off_weapon_id` | No se usa: solo `off_hand_id` |

## 5. Dependencias externas

| Dependencia | Propietario | Casos afectados |
| --- | --- | --- |
| Consumo de `DuelContext.nearby`/`distances` y fase de psicología/liderazgo en el candidato | G05 | B11.*, B12.1, B14.* |
| Publicación por fila de contadores, banderas, categorías y hash | G06 (con G02/G03) | B02–B08, B09.3, B10.1/3, B15.4–6 |
| Inyección de estado inicial | G00/G02 | B01.3, B01.5, B01.6, B15.3 |
| Decisiones por fila | P02/G02 | declarado en el contrato; ningún caso lo usa hoy |

Estas dependencias no bloquean aceptar P01 como preparación: el caso, la regla,
el contexto y el criterio están declarados; una futura ejecución sin esa
capacidad queda incompleta/incompatible.

## 6. Validación

Comprobante escrito (no ejecutado por P01; lo ejecuta el coordinador):

- 63 variantes, 60 de duelo, 3 estructurales/ambiguas; 1914 claves transferidas.
- `quick ⊆ complete ⊆ deep` por id y cobertura de las variantes requeridas.
- Tipos y predicados de testigo; `witness_value` obligatorio solo para
  categoría/resultado directo/hash; A9 respetado.
- Controles de ausencia de la misma variante; A10 en el positivo enfocado.
- Materialización de `requires` contra los campos reales del build y del
  contexto; orígenes `e2e:`/`new:` con forma válida.
- `off_hand_id`, rodela en el defensor, brazero, hambre negra y piel natural.

## 7. Pendientes propios de P01

- Ninguno bloqueante para la preparación. La ejecución de la comprobación y la
  verificación de las identidades E2E contra el corpus queda en manos del
  coordinador (P01 no tiene terminal).
- No se proponen cambios de CSV ni de `status.numpy`/`status.native`.
