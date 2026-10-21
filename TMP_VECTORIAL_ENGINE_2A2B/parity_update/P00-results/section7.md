## 7. Contrato P01 ↔ P02 (revisión 4)

> **Corrige la revisión 3.** Se mantienen la compilación única, el muestreo por
> `simulate_duel_observed`/`simulate_batch_observed`, la puerta seis sigma, los
> estados `PASS|DIVERGENCE|INCOMPATIBLE|NOT_ACTIVATED|NOT_RUN`, la ausencia de
> guiones por motor, de reintentos y de cuotas. Cambian cuatro cosas:
>
> 1. el testigo es **tipado** (contador, bandera, categoría, resultado directo o
>    hash) y cada variante declara su **predicado**; `> 0` no vale para una
>    categoría ni para un hash;
> 2. el contexto local se expresa con `DuelContext.nearby`/`distances` y
>    `LocalParticipant`, no con un campo `support`;
> 3. la cobertura se cuenta por **variante** (63), no por obligación ni por clave;
> 4. `behaviour-inventory.csv` se **transfiere** al catálogo de P01; no queda como
>    dependencia de ejecución ni como segundo registro que haya que sincronizar.

No se añade framework, lenguaje de escenarios, jerarquía de plugins ni dependencia
nueva. Se reutilizan `FighterBuild`, `CompiledFighter`, `DuelContext`,
`LocalParticipant` (`mordheim_core.models`), `compile_fighter`,
`ScriptedDecisions`, `simulate_duel_observed` y `simulate_batch_observed` sin
modificarlos.

### 7.1 Archivos y símbolos

| Módulo | Propietario | Símbolos públicos |
| --- | --- | --- |
| `verification/parity/_battery_cases.py` | P01 | `PROFILE_LEVELS`, `OUTCOMES`, `Witness`, `WITNESSES`, `OBSERVABLES`, `Variant`, `Obligation`, `OBLIGATIONS`, `battery_cases(level="complete")`, `validate_cases`, `validate_keys`, `validate_origins` |
| `verification/parity/_battery_runner.py` | P02 | `RESOURCES_OBSERVED`, `BatteryCaseResult`, `BatteryReport`, `run_battery(cases, *, profile=None, backend="numpy", rows=None, root=None)` |

`RESOURCES_OBSERVED` sigue siendo lo que el candidato publica hoy
(`lucky-charm`, `force-of-will`, `mark-of-the-old-ones`, `luck`); no es el
vocabulario completo. Lo no publicado se declara y sale `INCOMPATIBLE`, nunca se
reduce el caso.

### 7.2 Modelo de obligación, variante y testigo (P01)

`OBLIGATIONS` agrupa por bloque `Bxx`; la unidad ejecutable y contable es la
**variante** `Bxx.y` de §4.4. Una obligación con dos contratos distintos tiene dos
variantes con testigos distintos; una etiqueta o un consumidor compartido no las
funde.

```python
from dataclasses import dataclass
from typing import Literal, Mapping

WitnessKind = Literal["counter", "flag", "category", "direct-result", "hash"]
Predicate = Literal[
    "count>0", "count==0", "flag-true", "flag-false",
    "class-equals", "class-differs",
    "value-equals", "value-differs",
    "hash-changes", "hash-same",
]

@dataclass(frozen=True, slots=True)
class Witness:
    name: str
    kind: WitnessKind
    present: Predicate
    absent: Predicate

@dataclass(frozen=True, slots=True)
class Variant:
    id: str                          # "B14.1"
    title: str
    witness: Witness | None          # None = aún sin testigo admisible
    case_kind: Literal["duel", "structural", "unlocated"] = "duel"
    required: bool = True            # cuenta en el denominador de `complete`
    level: Literal["quick", "complete", "deep"] = "complete"
    owner: str = "G06"               # quién publica o implementa lo que falta
    evidence: str = ""               # comprobación exacta o hueco declarado
    secondary: tuple[str, ...] = ()  # variantes que la misma cláusula también toca

@dataclass(frozen=True, slots=True)
class Obligation:
    id: str                          # "B14"
    family: str                      # "F10-leadership"
    variants: tuple[Variant, ...]

OBLIGATIONS: Mapping[str, Obligation] = {...}
```

Reglas:

- `witness.name` pertenece a `WITNESSES` o es `None`; una cadena libre no es
  válida. El tipo y los predicados salen de la tabla de §7.6; P01 no los inventa
  por caso.
- `witness.kind="direct-result"` solo se admite en `B07.*` (la condición es el
  resultado directo de la tabla de lesión) y `B15.*` (la herida o la condición es
  el resultado directo de la recuperación o de la reacción). `condition` y
  `wounds` **no** son testigos de impacto, parada, armadura, save, recurso ni
  psicología.
- `required=True` es la variante material de §4.4 y cuenta en el denominador de
  `complete`. `required=False` documenta una variante dependiente de una entrada
  que aún no existe; no se omite del catálogo.
- `owner` es el propietario de la representación, del consumo o de la publicación
  que falta (`G00`, `G02`, `G03`, `G05`, `G06`, `P01`). No se usa para rebajar un
  estado.
- `secondary` no acredita nada por sí solo: exige que el caso declare el testigo
  de la variante secundaria en `also_covers` (§7.4).
- **Pertenencia**: `VARIANT_KEYS: Mapping[str, tuple[str, ...]]` se genera una
  sola vez importando `behaviour-inventory.csv` y se versiona con P01. A partir de
  ahí P01 es el propietario de la pertenencia; no hay lectura en tiempo de
  ejecución de `P00-results/` ni una segunda lista manual que mantener. P00
  conserva el CSV como foto de diseño y la reconciliación de §3.
- **Huecos**: una variante `required=True` con `witness=None` se declara igual y
  sus casos salen `INCOMPATIBLE:witness`; no se convierte en «cubierta por
  `winner`».

### 7.3 Modelo de caso (P01)

```python
from dataclasses import dataclass, field
from typing import Literal, Mapping
from mordheim_core.models import DuelContext, FighterBuild

PROFILE_LEVELS = ("quick", "complete", "deep")

@dataclass(frozen=True, slots=True)
class BatteryCase:
    id: str                                  # único y estable
    level: Literal["quick", "complete", "deep"]
    variant: str                             # "B14.1"; debe existir en OBLIGATIONS
    origin: str                              # "e2e:<audit_id>::<scenario>" | "spec:<fixture>#<case>"
    first: FighterBuild
    second: FighterBuild
    rows: int = 64
    seed: int = 2026
    maximum_rounds: int = 50
    context: DuelContext | None = None       # nearby/distances/contacts/charging
    decisions: Mapping[str, bool] = field(default_factory=dict)
    decision_scope: Literal["uniform", "per-row"] = "uniform"
    observables: tuple[str, ...] = ("winner", "rounds", "wounds", "condition")
    expect: Literal["present", "absent"] = "present"
    positive_control: str | None = None      # id de caso; obligatorio si expect="absent"
    witness_value: int | str | None = None   # categoría/resultado/hash esperado
    also_covers: tuple[str, ...] = ()        # variantes secundarias ejercidas
    comparison: Literal["witness", "focused"] = "witness"
    focused: str | None = None               # "winner:2" | "condition:out"; solo focused
    requires: tuple[str, ...] = ()           # ids de regla materializados en el build
    note: str = ""
```

Invariantes que P01 garantiza con `validate_cases`:

- `level in PROFILE_LEVELS`; `id` único; `variant` existe en `OBLIGATIONS`.
- `observables ⊆ OBSERVABLES`, contiene `"winner"` y contiene el nombre del
  testigo de la variante cuando no es `None`. Si el testigo es un resultado
  directo (`condition`/`wounds`), el nombre ya está en `OUTCOMES` y se admite sin
  duplicarlo en `WITNESSES`.
- `rows >= 1`, `seed >= 0`, `maximum_rounds >= 1`.
- `witness_value` es obligatorio si el testigo es `category`, `direct-result` o
  `hash`; prohibido si es `counter` o `flag`.
- `expect="absent"` exige `positive_control` no nulo, existente, de la **misma
  variante**, con `expect="present"` y declarado antes (sin ciclos). El caso
  negativo no exige activación positiva; exige el predicado `absent` del testigo
  y un control que cumpla `present`.
- `expect="present"` no admite `positive_control`.
- `comparison="focused"` exige `focused` con la forma `<outcome>:<valor>` y
  `positive_control`; `witness` debe ser `None` o no publicado (§7.6). Un caso
  `focused` no cuenta como testigo de una variante que sí tiene testigo.
- `also_covers` solo contiene variantes existentes y distintas; el nombre del
  testigo de cada una debe estar en `observables` y ser evaluable por P02. Una
  variante secundaria ya cubierta por otro caso no se duplica.
- `requires` se comprueba contra los campos reales de `FighterBuild`:
  `main_weapon_id`, **`off_hand_id`**, `armour_id`, `defence_ids`, `skill_ids`,
  `preparation_ids`, `special_rule_ids`, `condition_ids`, `main_material_id`,
  `off_material_id`, `variant_ids`, `trait_overrides` y `owned_item_ids`. Un id
  declarado que no aparece es un caso inválido, no un caso que «probablemente»
  active.
- Toda clave de `VARIANT_KEYS[variant]` existe y está admitida en el registro; se
  valida con `tools/knowledge/clause_registry.py`, sin escribir el CSV.
- **Anidamiento** por `id`: `quick ⊆ complete ⊆ deep`.
- **Origen**: `origin` resuelve a un `audit_id`/escenario E2E o a un fixture/caso
  semántico existente. P01 lo comprueba leyendo el corpus, sin importar helpers
  de `tests/` desde el módulo de producción.

P01 construye los `FighterBuild` como el corpus E2E
(`tests/E2E/modular-engine/runner.py:49-58`): `characteristics` →
`Characteristics`, tuplas para las listas de ids. No importa código de pruebas.
Un escenario E2E con `initial_state` no se convierte hoy: se declara
`INCOMPATIBLE:state` (G00/G02) y no se ejecuta desde cero como si fuera
equivalente.

### 7.4 Selección y cobertura por variante

Un nivel es un conjunto de **variantes**, no un número de casos:

- **quick**: variantes con `level="quick"`; una representativa por variante, con
  testigo admisible o comparación enfocada. Es regresión, no certificado.
- **complete**: todas las variantes `required=True` con `case_kind="duel"` (60)
  con al menos un caso, incluidas las negativas pareadas de toda variante con
  disparador/ausencia materializable. Las tres estructurales/ambiguas (B00.1,
  B09.1, B99.1) se acreditan con su comprobación propia. No incluye composición.
- **deep**: `complete` + composición/sensibilidad `D01`–`D06` de §4.5. No reserva
  ninguna variante de comportamiento: si una interacción necesita una variante
  que no está en `complete`, se añade primero a `complete`.

`battery_cases(level)` devuelve los casos con nivel igual o anterior en
`PROFILE_LEVELS`. No hay alias con `--level deterministic|statistical|deep` ni con
`--pair-set`; P03 debe rechazar la mezcla.

Cobertura:

- Se calcula sobre `OBLIGATIONS[*].variants`, no sobre claves ni sobre número de
  casos. `MISSING:<variant-id>` por cada variante requerida con `case_kind="duel"`
  sin caso que la cubra; `missing_variants` vacío es condición de
  `accepted=True`.
- Una variante queda cubierta por un caso con `variant=id`, **o** por un caso que
  la declare en `also_covers` y cuyo testigo también se evalúe y pase. Un caso
  genérico de la obligación no cubre las demás variantes.
- Las claves se adjuntan a variantes (`VARIANT_KEYS`), no a casos sueltos: varias
  claves comparten variante y no se exige un duelo por clave.
- Variantes estructurales o sin duelo: `B00.1` (enrutado), `B09.1`
  (compilación) y `B99.1` (consumidor ambiguo) llevan `case_kind="structural"` o
  `"unlocated"`; se acreditan con su comprobación propia y salen `STRUCTURAL` o
  `UNLOCATED`, nunca `PASS` de batería ni cuentan como `MISSING` de duelo.
- Las 98 `shared-operator` se informan por el grupo de §4.6: 9 con evidencia
  exacta (y solo de una variante) y 89 pendientes. No se convierten en variantes
  de duelo ni se acreditan con un caso genérico.

### 7.5 Ejecución (P02)

```python
def run_battery(cases, *, profile=None, backend="numpy", rows=None, root=None) -> BatteryReport:
    ...
```

Por caso:

```python
first, second = compile_fighter(case.first, root), compile_fighter(case.second, root)
n = case.rows if rows is None else rows
decisions = ScriptedDecisions(case.decisions)

oracle = simulate_duel_observed(
    first, second, n, seed=case.seed, maximum_rounds=case.maximum_rounds,
    decisions=decisions, context=case.context)
candidate = _candidate_sample(
    backend, first, second, n, case.seed, case.maximum_rounds, decisions,
    context=case.context)
```

- **Compilación una vez** por caso y participante; el mismo `CompiledFighter`
  alimenta ambos motores. La compilación se mide aparte y no suma a
  `modular_seconds`.
- `root` es `knowledge_root()` cuando es `None`; P04 puede fijarlo.
- `backend="native"` usa `_combat_native.simulate_batch_observed` solo si
  `CONTEXT_VERSION == 1` y el símbolo existe; si no, `NOT_RUN:native-stale`.
- **Contexto local**: los aliados, el líder, el handler o el relay viajan en
  `case.context` (`DuelContext.nearby` + `distances`) y se compilan con la misma
  conversión que los duelistas. No hay `support` ni un tercer `CompiledFighter`
  aparte. Las variantes que solo necesitan el valor propio no exigen `nearby`.
- **Tres capas separadas** para B11/B14: representación (`DuelContext` existe y el
  corpus E2E ya la usa), consumo (`leadership.py` lee `nearby`/`distance`; el
  candidato no llama a esos resolutores en `_driver.py`) y publicación
  (`ObservedDuelResult`/`VectorBatchObservation` no exportan el valor ni el flag
  por fila). La falta de consumo es `INCOMPATIBLE:consumer:<variant>` `owner=G05`;
  la de publicación es `INCOMPATIBLE:witness:<name>` `owner=G06`. No se confunden
  con una ausencia del modelo de entrada.
- **Decisiones**: `ScriptedDecisions` responde por clave, uniformemente. Si el
  caso declara `decision_scope="per-row"`, P02 devuelve
  `INCOMPATIBLE:decision-scope owner=P02/G02` antes de compilar. Un `KeyError`
  durante la ejecución es `NOT_RUN:decision-script:<clave> owner=P01`.
- Ningún caso ejecuta `replay_duel` ni transporta guiones de tiradas. Las
  reproducciones exactas existentes quedan en `test_duel_replay.py` como evidencia
  separada; P03 las cita sin fusionarlas con `PASS`.
- Un fallo de compilación es `NOT_RUN:compile:<tipo>: <mensaje>` (caso/base
  inválido, P01). Un rechazo de `require_optimized_support` es
  `INCOMPATIBLE:construction`.

### 7.6 Observables, testigos tipados y conversión del contexto

`OBSERVABLES = OUTCOMES + WITNESSES`. Un **resultado** describe cómo terminó el
duelo; un **testigo** cuenta o clasifica el evento concreto que debía activarse.

```python
OUTCOMES = ("winner", "rounds", "wounds", "condition")

WITNESSES = (
    # recursos (nombre exacto del recurso gastado)
    "lucky-charm", "force-of-will", "mark-of-the-old-ones", "luck",
    # banderas de estado
    "frenzy", "devoted-frenzy", "on-fire", "entangled", "force-of-will-active",
    "broken-hands", "hampered", "disability", "netted", "grappled", "entranced",
    # psicología y liderazgo
    "fear-hit-sixes", "fear-test-skipped", "psychology-test-skipped",
    "psychology-dice", "stupidity-failed", "animosity-failed",
    "feral-instinct-failed", "leadership-first-failed", "leadership-auto-pass",
    "leadership-test-value", "poetry-first-leadership",
    # eventos de combate
    "hit-modified", "wound-modified", "strength-modified",
    "armour-save-rolled", "special-save-rolled", "parried",
    "attack-count", "acting-order", "reroll-used", "equipment",
)
```

Tabla de tipos y predicados (contrato, no sugerencia):

| Testigo | Tipo | `present` | `absent` | `witness_value` |
| --- | --- | --- | --- | --- |
| recursos (`lucky-charm`…), `hit-modified`, `wound-modified`, `strength-modified`, `armour-save-rolled`, `special-save-rolled`, `parried`, `attack-count`, `reroll-used`, `fear-hit-sixes` | `counter` | `count>0` | `count==0` | — |
| `frenzy`, `devoted-frenzy`, `on-fire`, `entangled`, `force-of-will-active`, `broken-hands`, `hampered`, `disability`, `netted`, `grappled`, `entranced`, `fear-test-skipped`, `psychology-test-skipped`, `stupidity-failed`, `animosity-failed`, `feral-instinct-failed`, `leadership-first-failed`, `leadership-auto-pass` | `flag` | `flag-true` | `flag-false` | — |
| `acting-order` | `category` | `class-equals` | `class-differs` | `0` o `1` |
| `leadership-test-value`, `psychology-dice` | `direct-result` (valor medido) | `value-equals` | `value-differs` | valor declarado |
| `condition`, `wounds` (solo B07/B15) | `direct-result` | `value-equals` | `value-differs` | código/valor declarado |
| `equipment` | `hash` | `hash-changes` | `hash-same` | hash base |
| `poetry-first-leadership` | `flag` | `flag-true` | `flag-false` | — |

Consecuencias:

- `acting-order` **nunca** se evalúa con `> 0` ni con «cero eventos»: es una
  categoría 0/1 y el caso declara cuál satisface `present` en `witness_value`.
- `equipment` **nunca** se evalúa por conteo: es un hash; `present` significa
  distinto del hash base declarado (o del control negativo), `absent` igual.
- `condition`/`wounds` solo son testigo con `kind="direct-result"` en `B07.*` y
  `B15.*`. Para impacto, parada, armadura, save, recurso o psicología no se
  deducen de una herida o condición terminal.
- Un testigo no publicado por ambos lados es `INCOMPATIBLE:witness:<nombre>` con
  `owner`. No se reduce a `winner`, no se descarta el observable y no se declara
  `PASS`.
- `RESOURCES_OBSERVED` documenta lo que el candidato ya publica; no autoriza a
  compararlo contra un oráculo que no lo devuelve.
- Las claves de una regla no se «cubren» por estar en `VARIANT_KEYS`: la cobertura
  exige testigo (o comparación enfocada) y comparación.

#### 7.6.1 Conversión E2E → `DuelContext`

El corpus ya expresa el contexto local con los campos de `DuelContext`; P01
reutiliza la conversión de `tests/E2E/modular-engine/runner.py:100-112`:

```yaml
duel_context:
  first_id: first
  second_id: second
  nearby:
    - participant_id: leader
      side_id: second
      condition: standing
      fighter: {collection: mordheim, band_id: amazons-lustria, profile_id: serpent-priestess}
  distances: [[second, leader, 6]]
  charging: [first]
  active_participant: first
```

- `nearby` se compila con la misma función `_fighter` que los duelistas y se
  envuelve en `LocalParticipant(participant_id, side_id, fighter, condition)`.
- `distances` son pulgadas de borde a borde entre ids de participantes;
  `DuelContext` rechaza duplicados, ids desconocidos y distancias negativas.
- **Control sin líder**: se omite la entrada de `nearby` (o se deja vacía). No se
  usa `support=None` porque no hay tal campo; la variante B14.4 (liderazgo propio)
  puede incluir un líder en `nearby` y comprobar que no se adopta su valor.
- **Control fuera de radio**: el mismo proveedor con `distances` 8" para un radio
  de 6", o 13" para 12"; el corpus ya tiene ese caso
  (`...barbarian--dim-witted...::outside-the-printed-six-inches...`).
- La distancia se declara siempre que el contrato la lea; no se inventa un
  `support_distance` que el motor no consume.
- `mob-leadership` no usa `nearby`: el recuento de aliados a 3" viaja en
  `CompiledFighter.mob_allies`, suministrado por el llamador.

### 7.7 Comparación, activación y NOT_ACTIVATED

Cada observable declarado se compara por categorías sobre la muestra:

- `winner` aporta 3 categorías (0, 1, 2); `condition` 5 por participante;
  `wounds` y `rounds` una por valor entero observado en cualquiera de los dos
  motores (unión de valores, sin recortar). Los testigos de tipo contador usan la
  unión de conteos; los categóricos y los hashes, sus valores.
- Para cada categoría `c`: `p = oracle_count[c] / n`, `q = candidate_count[c] / n`.
- **Puerta existente** (`_statistical.py:19-24`):
  `|p - q| <= max(0.0025, 6·sqrt(p(1-p)/n + q(1-q)/n))`. P02 copia la expresión
  literal citando esa línea; P03 la unifica. No se inventa ni se relaja.
- `PASS` exige que todas las categorías de todos los observables declarados pasen
  y que se cumpla el criterio de testigo (o el enfocado).

Evaluación del testigo (por variante):

- `counter`: `present` = alguna fila con `count>0`; `absent` = todas con `count==0`.
- `flag`: `present` = alguna fila con la bandera; `absent` = ninguna.
- `category`: `present` = alguna fila con `value == witness_value`; `absent` =
  ninguna fila con ese valor. `acting-order` se evalúa así, no por magnitud.
- `direct-result`: `present` = el valor medido coincide con `witness_value`;
  `absent` = no coincide (p. ej. la condición no es la declarada).
- `hash`: `present` = el hash difiere de `witness_value`; `absent` = coincide.
  `equipment` no se interpreta como cero/no cero.

Estados:

- `expect="present"` y el oráculo no muestra el predicado `present`:
  `NOT_ACTIVATED:<witness>`. No se atribuye a divergencia entre motores: no hay
  activación observada.
- `expect="absent"` sin control: `NOT_ACTIVATED:no-positive-control`. Con control
  declarado pero sin activación en el control:
  `NOT_ACTIVATED:positive-control:<id>`; **no** `DIVERGENCE`.
- Contraste: el par positivo/negativo debe diferir en el oráculo (positivo cumple
  `present`, negativo cumple `absent`). Si ambos cumplen `present`, el criterio no
  discrimina: `NOT_RUN:criterion-insensitive:<variant>` `owner=P01` (defecto de
  caso), no una divergencia de motores.
- Ambos motores ejecutaron y sus distribuciones difieren: `DIVERGENCE:distribution`.
  Es el único camino que atribuye una diferencia entre motores.

**Comparación enfocada** (`comparison="focused"`): cuando el testigo no está
publicado, un par de casos puede declarar un único resultado discriminante
(`focused`, p. ej. `condition:out` o `winner:2`) y su dirección esperada. El
criterio es: el oráculo difiere entre positivo y negativo en ese resultado y el
candidato reproduce la misma diferencia. Se informa `coupling="focused"` y no
acredita activación por evento. Se admite para no exigir instrumentación nueva
automáticamente; no sustituye a un testigo ya declarado ni convierte una
diferencia de distribución en activación.

**Límite**: ni el testigo ni el contraste demuestran independencia fila a fila ni
localizan la causa de una diferencia. La independencia exige observación por
evento (G06) y se informa `coupling="unverified"`. La evidencia exacta sigue
siendo `_specifications.py` y `test_duel_replay.py`; la batería aporta amplitud y
sensibilidad, no exactitud por sí sola.

**Sin reintentos**: no se cambia la semilla ni se amplía `rows` tras un fallo. La
sensibilidad se mide antes de fijar presupuestos, con la escalera
`(case.rows, 4·case.rows)`.

### 7.8 Comprobación de lote

Por cada caso con `rows > 1`:

1. **Determinismo**: dos ejecuciones con el mismo caso, semilla y ancho producen
   arrays idénticos (`repeat_is_deterministic=True`, `contract_probe.py`). Un
   fallo es `DIVERGENCE:batch-nondeterministic`.
2. **Forma**: cada array mide `rows` (`shape_mismatch=none`). Si no,
   `DIVERGENCE:batch-shape`.
3. **Contraste**: el de §7.7, evaluado entre el caso y su `positive_control`, con
   el predicado tipado de la variante o el resultado enfocado. Es la única
   comprobación de lote que atribuye una diferencia al disparador.
4. **Alcance de decisión**: `decision_scope="per-row"` se rechaza antes de
   ejecutar; un `KeyError` es `NOT_RUN:decision-script`, no una decisión tomada
   por defecto.

**Multiplicidad retirada** (revisión 2 §7.7.3): no se exige que una categoría con
`0 < count < rows` en el oráculo aparezca también en el candidato. Los motores no
comparten tiradas fila a fila y una categoría rara puede faltar en una muestra
independiente aunque las distribuciones coincidan. Reproducción del defecto:
oráculo con 63 ceros y un uno, candidato con 64 ceros; la puerta seis sigma
acepta (`p=1/64`, `q=0`, `tol≈0.093 > 0.0156`) y la regla declaraba
`batch-mask`. Por eso los cuatro `DIVERGENCE` históricos por `batch-mask` no se
cuentan como defectos de reglas del motor: esa evidencia no localiza ni acredita
tales defectos.

**Lo que el contrato no afirma** (medido): la fila 0 de un lote no coincide con una
ejecución individual de la misma semilla. Con `seed=11`, `rows=16` frente a
`rows=1` difieren `rounds` (3 vs 2), `first_wounds` (-1 vs 0) y `second_wounds`
(0 vs 1); ver `contract-probe.txt`. Por tanto no se exige correspondencia fila a
fila con el oráculo, repetir una sola fila no es evidencia de lote y detectar qué
fila gastó qué recurso exige observación por evento (G06). `first_wounds` puede
ser negativo; se trata como una categoría más, sin recortar.

### 7.9 Resultado, estados y alcance

```python
@dataclass(frozen=True, slots=True)
class BatteryCaseResult:
    case: str
    level: str
    variant: str
    obligation: str
    backend: str                  # "numpy" | "native"
    status: str                   # PASS | DIVERGENCE | INCOMPATIBLE | NOT_ACTIVATED | NOT_RUN
    keys: tuple[str, ...]         # derivadas de VARIANT_KEYS
    observables: tuple[str, ...]
    rows: int
    witness: str | None = None
    witness_kind: str | None = None
    witness_rate: float | None = None
    expect: str = "present"
    expect_value: int | str | None = None
    comparison: str = "witness"   # "witness" | "focused"
    coupling: str = "unverified"  # "contrast" | "focused" | "unverified"
    detail: str = ""
    modular_seconds: float = 0.0
    candidate_seconds: float = 0.0

@dataclass(frozen=True, slots=True)
class BatteryReport:
    complete: bool
    accepted: bool                # complete, scope == "profile" and variants covered
    scope: str                    # "profile" | "provided"
    profile: str | None
    results: tuple[BatteryCaseResult, ...]
    passed: tuple[str, ...]
    divergences: tuple[str, ...]
    incompatible: tuple[str, ...]
    not_activated: tuple[str, ...]
    not_run: tuple[str, ...]
    missing_variants: tuple[str, ...]
```

| Estado | Significado | ¿Aceptable? |
| --- | --- | --- |
| `PASS` | Ambos ejecutaron, el testigo o el contraste enfocado cumple y todas las categorías pasan | Sí |
| `DIVERGENCE` | Ambos ejecutaron y sus distribuciones difieren; o falla determinismo/forma | No |
| `INCOMPATIBLE` | Construcción rechazada, observable/testigo no publicado, consumo ausente, decisión per-row o backend sin capacidad | No |
| `NOT_ACTIVATED` | El testigo esperado no apareció en el oráculo, o el control positivo de una ausencia no activó | No |
| `NOT_RUN` | No se ejecutó: backend ausente/obsoleto, compilación inválida, guion de decisión ausente, caso o criterio mal definido | No |

`accepted=True` exige `scope="profile"`, `missing_variants` vacío y ausencia de
`DIVERGENCE`, `INCOMPATIBLE`, `NOT_ACTIVATED` y `NOT_RUN`. `scope="provided"`
puede ser `complete=True` en el sentido interno del subconjunto, pero nunca
`accepted=True`: es diagnóstico, no acreditación del perfil. P03 traduce
`--require-complete` sobre `accepted`.

Clasificación de excepciones, sin silenciar ninguna:

- `ValueError` de `require_optimized_support` o del runtime uno-contra-uno →
  `INCOMPATIBLE:construction`.
- `KeyError` de `ScriptedDecisions` → `NOT_RUN:decision-script:<clave> owner=P01`.
- `AttributeError`/`TypeError` al leer un observable o testigo no publicado →
  `INCOMPATIBLE:witness:<nombre>` (G02/G03/G05/G06), nunca `PASS`.
- Consumo de `nearby` no implementado en el candidato →
  `INCOMPATIBLE:consumer:<variant> owner=G05`.
- `decision_scope="per-row"` → `INCOMPATIBLE:decision-scope owner=P02/G02`.
- Testigo no registrado o caso sin variante → `NOT_RUN:case-definition:<detalle>
  owner=P01`.
- Cualquier otra excepción → `DIVERGENCE:exception:<tipo>: <mensaje>`.

### 7.10 Evaluación solo-lectura de P01 y P02

P00 no ha modificado `_battery_cases.py` ni `_battery_runner.py`. Esta evaluación
fija qué conservar y qué corregir; la corrección es de P01/P02.

#### P01 — `_battery_cases.py`

**Conservar**:

- Módulo de datos sin importar el runner; separación catálogo/ejecución.
- `PROFILE_LEVELS`, `OBSERVABLES`, `BatteryCase`, `battery_cases`,
  `validate_cases`, `validate_keys`.
- Selección acumulativa por `id` y comprobación de claves admitidas contra el
  registro.
- `_fighter` como conversión explícita a `FighterBuild` (sin importar helpers de
  `tests/`).
- `OUTCOME_OBSERVABLES` como semilla de la separación resultado/testigo.

**Corregir**:

| # | Hallazgo | Corrección exigida |
| --- | --- | --- |
| 1 | `BatteryCase` no tiene `variant`, `expect`, `positive_control`, `witness_value`, `also_covers`, `decision_scope`, `comparison`, `requires` | Añadirlos con los invariantes de §7.3. `activation` se retira. |
| 2 | `_fighter` solo acepta `weapon`, `armour`, `collection`, `band`, `profile` y características | Exponer `skill_ids`, `preparation_ids`, `special_rule_ids`, `condition_ids`, `defence_ids`, materiales y `trait_overrides`, ya soportados por `FighterBuild`. |
| 3 | `q04-natural-armour-six` usa armadura ligera en un combatiente genérico; no lleva `band--beastmen-special-skills-shaggy-hide` | Materializar piel natural con el perfil/regla del origen y declarar `requires`; si falta entrada, `INCOMPATIBLE:input`, no sustituir por armadura. |
| 4 | `q05-flammable-fire` usa maza contra espada; faltan `weapon.brazier-iron` y `flammable` | Materializar fuego e inflamabilidad; el testigo es `on-fire`/`wound-modified`, no la herida terminal. |
| 5 | `q11-black-hunger` no lleva `skill_ids=("mechanic.black-hunger",)` | Añadir la regla al build; `requires=("mechanic.black-hunger",)`. |
| 6 | `q00-honorable` no lleva `mechanic.honorable` ni el rival derribado | Materializar regla y estado inicial; si el estado no se puede inyectar, `INCOMPATIBLE:state`. |
| 7 | `c04-parry-reroll` no declara la rodela en el defensor | Poner la rodela en el defensor y declarar B06.2; el atacante no lleva el arma de parada. |
| 8 | `q10-leader-six` no declara proveedor ni 6"; el líder es duelista | Construir `DuelContext(nearby=(LocalParticipant(...),), distances=((second, leader, 6),))`; el líder no sustituye al segundo combatiente. Sin líder: omitir `nearby`; fuera de radio: la misma entrada a 8". |
| 9 | `q08-death-blow-optional` no declara la decisión del origen | Declarar `decisions` y `decision_scope="uniform"`; sin guion, `NOT_RUN:decision-script`. |
| 10 | `c04-highest-injury` cita `e2e:core/combat-injury-states::the-highest-of-several-injury-results-applies`, que no existe | Usar `highest-injury-result-applies`; la identidad correcta está en el YAML actual. |
| 11 | Hay una clave de ejecución declarada solo en `deep` | Trasladar su variante base a `complete`; `deep` añade composición/sensibilidad, no reserva comportamientos. |
| 12 | Varios casos solo declaran observables terminales y pueden aprobar sin la regla | Declarar el testigo tipado de la variante; si no está publicado, `INCOMPATIBLE:witness` o comparación enfocada declarada, nunca `PASS` por actividad genérica. |
| 13 | No hay variantes negativas pareadas | Añadir `expect="absent"` + `positive_control` para toda variante con disparador/ausencia materializable, con el predicado `absent` de su tipo. |
| 14 | `validate_cases` no comprueba materialización ni `origin` | Validar `requires` contra el build (con **`off_hand_id`**) y resolver `origin` en la prueba de catálogo. |
| 15 | La cobertura se calcula por obligación | Contarla por variante, con `also_covers` y `MISSING:<variant-id>`; importar `VARIANT_KEYS` una vez y no leer `P00-results` en ejecución. |

#### P02 — `_battery_runner.py`

**Conservar**:

- Compilación única por caso y participante; el mismo `CompiledFighter` para
  ambos motores.
- `simulate_duel_observed`/`simulate_batch_observed`, normalización de ganador y
  comparación por categorías.
- Puerta seis sigma copiada literalmente de `_statistical.py:19-24`.
- Determinismo (`_same_sample`), forma (`_shape_mismatch`), timings separados,
  import perezoso del nativo, `knowledge_root()`, `backend` validado.
- `KeyError` → `NOT_RUN:decision-script`.
- `BatteryCaseResult`/`BatteryReport` y los cinco estados.

**Corregir**:

| # | Hallazgo | Corrección exigida |
| --- | --- | --- |
| 1 | `_multiplicity_failure` y su llamada aplican la regla retirada | Eliminarla. Sustituirla por el contraste de §7.7/§7.8. |
| 2 | `_activation` exige `name in _SUPPORTED` y `name in _BOOLEAN`; la intersección es vacía | Leer el testigo tipado de `OBLIGATIONS[variant]`; aplicar el predicado de su tipo, `expect` y `positive_control`. |
| 3 | `_SUPPORTED` solo contiene los 4 terminales | Ampliarlo con los testigos publicados; lo no publicado sale `INCOMPATIBLE:witness:<nombre>` con `owner`. |
| 4 | `_BOOLEAN` mezcla recursos y banderas y no decide nada válido | Retirarlo o limitarlo a la comparación; no decide activación. |
| 5 | No se evalúa `DuelContext.nearby` para B11/B14 | Consumir el contexto en el camino candidato cuando exista; si no, `INCOMPATIBLE:consumer:<variant> owner=G05`. No introducir `support`. |
| 6 | `INCOMPATIBLE:decision-scope` no tiene camino | Rechazar `case.decision_scope="per-row"` antes de compilar; documentar el adaptador P02/G02. |
| 7 | `run_battery` calcula `complete` sobre los casos recibidos | Añadir `profile`, `missing_variants`, `scope`, `accepted`; sin `profile`, `accepted=False`. |
| 8 | No hay criterio de ausencia ni control positivo | Evaluar `expect="absent"` con el predicado tipado y `positive_control`; si el control no activa, `NOT_ACTIVATED`. |
| 9 | `activation=None` se interpreta como «sin comprobación» y permite `PASS` | Un caso sin testigo admisible ni comparación enfocada es `INCOMPATIBLE:witness`, no `PASS`. |
| 10 | El informe no expone variante, testigo, tipo, expectativa ni cobertura | Añadir `variant`, `witness`, `witness_kind`, `witness_rate`, `expect`, `expect_value`, `comparison`, `coupling`, `missing_variants`. |
| 11 | No hay contraste entre caso positivo y negativo | Implementar la comprobación cruzada en `run_battery` (post-proceso del conjunto), no dentro de un único caso. |
| 12 | No hay comparación enfocada | Aceptar `comparison="focused"` con un único outcome y su dirección declarada; informar `coupling="focused"`. |

#### Entregas

`P01-deliverable.md` y `P02-deliverable.md` no existen en esta copia. Son
obligatorios incluso si la fase queda parcial. P00 no los crea: pertenecen a sus
propietarios y deben declarar alcance, archivos, evidencia y dependencias
externas.

### 7.11 Invariantes que P03 puede comprobar sin reejecutar

- `battery_cases("quick") ⊆ battery_cases("complete") ⊆ battery_cases("deep")` por
  `id`.
- Toda variante `required=True` con `case_kind="duel"` tiene al menos un caso en
  `complete`, propio o vía `also_covers` con su testigo; `missing_variants` vacío
  para `accepted=True`; las estructurales/ambiguas informan `STRUCTURAL` o
  `UNLOCATED`.
- Cada caso declara una variante registrada y un testigo evaluable por su tipo, o
  una comparación enfocada declarada; si no, `INCOMPATIBLE:witness`/
  `NOT_RUN:case-definition`.
- Cada `expect="absent"` tiene un `positive_control` de la misma variante y ambos
  aparecen en el informe.
- Un control positivo que no activa produce `NOT_ACTIVATED`, nunca `DIVERGENCE`.
- `run_battery(..., profile=...)` informa `scope="profile"`; un subconjunto informa
  `scope="provided"` y `accepted=False`.
- `VARIANT_KEYS` suma 1914 claves y 63 variantes; no hay una lista de claves a
  mano ni lectura de `P00-results` en ejecución.
- Las 1256 `shared` se informan `STRUCTURAL`; las 189 `unlocated`, `UNLOCATED`;
  las 98 `shared-operator`, por el grupo de §4.6 (9 exactas/89 pendientes), nunca
  como `PASS` genérico.
- El informe separa declarado (clave), ejecutado (caso), activado (testigo),
  observado (comparación) y pendiente/incompatible/divergente. Las 143
  «verificadas» estructurales de `_vectorized` no se mezclan con `PASS`.
- `levels` del payload es un recuento medido de casos por perfil, no una cuota.
