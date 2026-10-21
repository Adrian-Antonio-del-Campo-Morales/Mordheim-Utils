# Integración previa a G07 — entrega

## Base

- Repositorio `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`, árbol de trabajo compartido.
- Se conservaron todos los cambios locales previos (G00–G06 y los de otros propietarios).
- Archivos tocados: `vectorized/_types.py`, `vectorized/_state.py`, `vectorized/_attacks.py`,
  `vectorized/_driver.py`, `kernel.py`, `tests/python/combat/vectorized/test_runtime_regressions.py`,
  `sources/knowledge/verification/clause-contracts.csv` (solo vía `clause_registry.py`) y este
  documento. Sin commits ni pushes; sin campaña de paridad.

## 1. Fear: `psychology[i].fear_hit_sixes` → ataques → `hit_context`

- `CombatState.fear_hit_sixes` por simulación; el driver la limpia al inicio de cada ronda y
  copia `PsychologyResources.fear_hit_sixes` tras `resolve_fear`.
- `_prepare_weapon_attack(..., needs_sixes=...)` → `hit_context(needs_sixes=...)` →
  `hit_targets`; solo las filas marcadas exigen 6 natural, solo en melé, y el impacto
  automático contra WS 0 no se aplica con seis exigidos.
- `resolve_attacks` acepta la máscara y la escribe en el estado del atacante, de modo que
  arma principal, off-hand, extras, bonus, agarre y enredo leen la misma fila.
- **Evidencia**: sonda con carga declarada (`[0, 3]` de máscara, Ld 0); caso de regresión
  con objetivo 3 → 6.

## 2. Agarre completo y tentáculo por asignación

- `grappled`/`grappling` por simulación; declaración del Gaoler con sus exclusiones
  (Undead, Daemon, dead, pain-immunity, Large), ataque natural único sin daño, parada,
  prueba `S-2` con seis siempre falla y Blessed Sight, y liberación al inicio de **cada**
  fase de combate (o si el portador deja de estar Standing).
- **Tentáculo**: `_tentacle_forfeit` recorre la asignación completa que construye el
  modular: posiciones de mano (main/off), bonus de Whipcrack y contribuciones extra
  (`_pool_extra_weapons`, con las mismas exclusiones que `resolve_attacks`: mordisco/Eagles
  en su evento propio, vomit/wraith y Horned One sin carga). La decisión
  `round.{r}.{side}.grapple-lost-attack.{index}` nombra una posición de esa secuencia y cada
  fila quita la suya; si la fila no posee esa posición conserva el pool y no gasta. El
  mínimo 1 se aplica al pool completo, así que una mano + un extra sí puede perder la mano.
  Devuelve tres máscaras: posición de mano (`forfeits`), filas que pierden el Whipcrack (se
  limpia su evento) e índice original del extra perdido (`extra_forfeits`, que
  `resolve_attacks` salta en su bucle de extras). El gasto se marca por fila en
  `_RoundLedger.tentacle_used` solo cuando esa fila perdió un ataque.
- **Mim + tentáculo**: llega con `attacks=0` y sin Whipcrack, así que su pool es exactamente
  los extras restantes; con dos extras hay posición elegible y con uno se respeta el mínimo.
- **Evidencia**: 40 filas → 12 presas y 7/8 nuevas tras liberaciones; `[0,-1,0,0]` con la
  oferta por defecto y `[1,-1,1,1]` rechazando `.0`; mano + extra → pierde la mano;
  posición 1 del pool → `extra_forfeits` 0 y `resolve_attacks` pasa de 2 a 1 observación;
  látigo → `whip_forfeits` en la posición 1; Mim con 2 extras → extra 1, con 1 extra → sin
  pérdida; recurso gastado una vez y segunda ronda sin pérdida; agarre con máscaras
  simétricas; sonda Mim+2 extras contra defensor con tentáculo: 91 → 49 de daño.

## 3. Mim sin manos (`condition.mim-no-hand-attacks`)

- El pool de manos se vacía (`attacks` y `ordinary_attacks` a 0), Shifty y el agarre no se
  declaran, y el bonus de Whipcrack se descarta: en `pool_attack_weapons` ese bonus ocupa la
  posición `count - 1`, que el rango de forfeits de Mim siempre alcanza.
- Las contribuciones independientes (ataques naturales extra, Eagles, mordisco) siguen
  resolviendo, pero en el **mismo hueco de prioridad del pool ordinario** (evento 0/1), no
  como un pase previo: la fila Mim entra al evento con `attacks=0` cuando conserva extras y
  `resolve_attacks` sólo prepara esos extras. Con `remaining = max(1, count) if extra else 0`
  del modular, una fila sin extras no genera evento ni ataque.
- **Evidencia**: el pool de manos recibe `attacks=0`, el evento ordinario resuelve 1 ataque
  extra por fila, y el daño del portador de Mim queda entre 0 y el del mismo perfil sin la
  condición; sin contribución extra el daño es exactamente 0.

## 4. `mechanic.spawn-special-attacks`

- Se eliminó la tirada al inicio de ronda que contaminaba `state.attacks`. Ahora, dentro del
  grupo de equipo y tras el recuento (`attack_count`) y antes de Shifty y de los
  modificadores de ronda, un `D6+1` por guerrero y ronda **sustituye** el pool construido,
  igual que `resolve_spawn_attack_count`. La única excepción es el arma principal
  `weapon.vomit-attack`; `effect.wraith-touch` ya **no** exime de la tirada (el modular sólo
  comprueba vomit), corrección respecto de la nota anterior.
- **Evidencia**: con A=1 los valores resueltos quedan en 2..7 y varían entre filas.

## 5. Revisión de dependencias G00–G06

| Dependencia | Estado |
| --- | --- |
| `fear_hit_sixes` en ataques | Conectada |
| `grappled`/`grappling`, tentáculo | Conectado |
| Noble `count == loss == 1` | Conectado |
| `condition.mim-no-hand-attacks` | Conectado |
| `mechanic.spawn-special-attacks` | Conectado |
| `mechanic.nominated-strike-first`, `noblesse-stomp`, Shifty por prioridad | Ya conectados en G06 |
| `mechanic.denizens` | **Sin contrato ni comportamiento**: búsqueda en fuentes (`sources/`), catálogo, CSV, modular, native y `TODO.md`: cero apariciones; no hay cláusula que portar, no se inventa comportamiento y no se admite como implementado |
| Elección del tentáculo | Conectada sobre la asignación completa: manos, Whipcrack y extras, con la posición, el mínimo y el gasto por fila |

## 6. Puerta NumPy

`NUMPY_PENDING = _numpy_gate()`: resta de residuales y modificadores locales
`NUMPY_CONNECTED_TAGS` y de `behaviours` `NUMPY_CONNECTED_BEHAVIOURS`. Revisión de cada
behaviour admitido contra su ruta real:

| behaviour | ruta NumPy comprobada |
| --- | --- |
| `effect-values` | `_operators.wound_context` (umbral crítico), `_attacks` (salvación etérea) y `_operators.armour_targets` (armadura natural anulada por fuego) |
| `vomit` | `_driver._select_attack_replacement` elige el arma, `attack_count` la deja en 1 y `resolve_attacks` suprime el resto del pool |
| `spectral-touch` | `_attacks._resolve_weapon`: un 6 natural resuelve la herida extra sin nueva tirada ni crítico |
| `shifty` | `_driver`: ataque +1, arma nominada y evento propio en su prioridad; excluido con Mim y con el tope de manos vacías |
| `killing-blow` | `_attacks._parry_hits` (no parada) y `_resolve_weapon` (herida automática con 6 natural) |

No se añadieron entradas nuevas: `condition.mim-no-hand-attacks`, `mechanic.spawn-special-attacks`
y `rule.tentacle-grapple` nunca formaron parte de `_pending_snapshot()`, así que la puerta no
los rechazaba y su conexión no exige abrir nada. `NATIVE_PENDING` sigue siendo
`_pending_snapshot()` sin tocar, y las llamadas sin backend conservan el rechazo histórico.
Comprobado: `skill.shifty` se admite en NumPy y se rechaza en native y en la llamada legacy.
Las pruebas de Mim y de spawn llaman `simulate_batch(..., backend numpy)` sin sustituir la
puerta, así que la admisión se ejerce por la ruta pública; el tentáculo también se ejecutó
íntegro por esa misma ruta en sonda.

## 7. CSV

Actualizado solo con `clause_registry.py prepare` + `apply --write`, con `status.native`
intacto (`pending`) y sin `verified`:

| clave exacta | fila |
| --- | --- |
| `mechanic.causes-fear` | `mechanic/mechanic.causes-fear` / `cause-fear` |
| `mechanic.gaoler-grapple` | `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.torturer-s-grapple/unclassified` |
| `mechanic.spawn-special-attacks` | `mechanic/mechanic.spawn-special-attacks` / `whole` |
| Tentacle (mutación) | `source/catalog/campaign/mutations.yaml/campaign.mutation.tentacle/unclassified` |
| Origen de banda de Spawn | `rule/mordheim/marauders-of-chaos/spawn-of-chaos--special-attacks/mechanic.spawn-special-attacks` |

Las dos últimas pasaron de `numpy: pending` a `numpy: implemented`; `native` sigue
`pending` en todas y ninguna tiene `verified`. La fila canónica de spawn recibió una nota
de corrección (solo vomit exime de la tirada) y la de Tentacle una nota de alcance completo
(manos + Whipcrack + extras, Mim incluido). SHA-256 del CSV:
`155f727cc95461649820dcdb0eb786db767a59e43d31224ce1b85b3e12d78a94`.

## Comprobaciones ejecutadas

```text
python -m pytest tests/python/combat/vectorized -q
  -> 14 failed, 120 passed (exit 1)
     Mismos 14 fallos previos: catálogo/construcción, Frantic, random-profile y familias.

python -m pytest tests/python/combat/vectorized/test_runtime_regressions.py -q
  -> 1 failed, 42 passed   (solo el fallo previo de Frantic)

python -m pytest tests/python/combat/test_kernel_plan.py \
                 tests/python/verification/test_structural.py \
                 tests/python/knowledge/test_clause_registry.py -q
  -> 21 passed (exit 0)

python -m ruff check <archivos tocados>
  -> no ejecutado: el modulo ruff no esta instalado en este entorno.
```

Casos de regresión añadidos a `test_runtime_regressions.py` (mismo número de tests; se
ampliaron los tres existentes):

```text
Mim: sin extras el daño del portador es exactamente 0; con un ataque natural extra el evento
     ordinario resuelve sólo ese ataque y el daño queda entre 0 y el del perfil sin Mim.
Tentáculo: [0,-1,0,0] con la oferta por defecto y [1,-1,1,1] al rechazar .0; mano + extra
     pierde la mano; posición 1 → extra_forfeits 0 y resolve_attacks 2→1 observaciones; látigo
     en la posición 1 → whip_forfeits; Mim 2 extras → extra 1 y Mim 1 extra → sin pérdida;
     gasto único y segunda ronda sin pérdida.
Spawn: valores observados 2..7 con A=1 y más de un resultado distinto por lote.
```

Sondas puntuales (no añadidas al repositorio, `require_optimized_support` sustituido):

```text
Mim: attacks=0 en manos; evento 0/1 conserva el extra y no se adelanta a la prioridad.
Gasto: el recurso del tentáculo sólo se marca cuando la fila perdió una posición.
Puerta: skill.shifty -> numpy admitido; native y legacy rechazados.
```

## Pendientes reales

1. `mechanic.denizens`: sin contrato, fuente, catálogo, CSV ni consumidor modular/native. La
   disposición queda documentada y no se inventa comportamiento; no se admite como
   implementado.
2. `behaviours` restantes fuera de la puerta: ninguno; la paridad de G07 decidirá si alguna
   ruta nueva debe volver a cerrarse.

La elección del tentáculo queda cerrada como implementación: manos, Whipcrack y extras son
posiciones reales, incluido el cruce Mim con extras, y no se traslada a G07 como trabajo
pendiente. G07 sólo debe verificarla contra el modular.
