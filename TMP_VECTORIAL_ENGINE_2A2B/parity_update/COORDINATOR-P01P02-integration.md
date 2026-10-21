# Integración del coordinador — P01/P02 (primera tanda)

> **Separación vigente de planes:** P01/P02 continúan con P00 revisión 4 +
> A8–A10. P03 cierra el rework con los tests de los tres niveles definidos y
> conectados, sin esperar a G07 ni resultados del candidato. P04/P05 son una
> campaña posterior con la batería renovada; P04 no completa autoría faltante
> y P05 no es G07. Rige la sección inicial de
> [COORDINATOR-progress-review.md](COORDINATOR-progress-review.md).

> **Nota histórica; alcance corregido el 2026-10-21:** solo preparamos tests
> mientras se implementa el vectorial. Las ejecuciones descritas abajo ya
> ocurrieron; sus resultados no condicionan la entrega de preparación ni
> acreditan defectos de reglas del candidato. Rigen la
> [revisión vigente](COORDINATOR-progress-review.md) y los prompts actualizados.
> Las dependencias del motor no bloquean la conexión de P03.

Fecha: 2026-10-21. Base: copia de trabajo actual (HEAD `c91c2a7c`, cambios
locales del motor incluidos). No hay commits. CSV intacto
(`b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`).

## Entregado

| Encargo | Archivo | Estado |
| --- | --- | --- |
| P00 | `P00-deliverable.md` + `P00-results/` | Reconciliación reutilizable; completar inventario y contrato según revisión vigente |
| P01 | `parity/_battery_cases.py` | Primera tanda parcial: 11/34/40 casos (quick/complete/deep) |
| P01 | `tests/python/verification/test_parity_battery_cases.py` | 2 comprobantes; pasan |
| P02 | `parity/_battery_runner.py` | Adaptador inicial; corregir multiplicidad y contrato de testigos sin exigir resultados del candidato |
| Coordinación | `COORDINATOR-P00-review.md` | Veredicto, contrato congelado y cesiones |

## P00 — revisión

Se reprodujeron los números del inventario: 4556 filas, 3457 admitidas, 0
huérfanas, 0 claves de anexo no admitidas, 189 `unlocated`, 1914 de ejecución.
También se reprodujeron `contract_probe.py` (`row0_equals_solo=False`,
determinista, sin desajuste de forma) y las 50 divergencias base
(35 `initialize`, 5 `pool`, 4 `replacement_pool`, 3 `attack`, 2 `recovery`,
1 `acting_order`).

Correcciones registradas en `COORDINATOR-P00-review.md`:

- **A1**: `knowledge_root` se importa de `mordheim_knowledge.loader`.
- **A2**: una decisión ausente del caso es `NOT_RUN:decision-script` (P01), no
  `INCOMPATIBLE`; solo la necesidad de respuestas por fila es
  `INCOMPATIBLE:decision-scope`.
- **A3**: la línea base de `_vectorized` pasó de 143 a **296** verificadas tras
  el port G03, porque la marca es textual. No es cobertura; P03/P05 deben
  recalcularla.
- **A4**: `deep_test_scenarios` está en `cli/scenarios.py` (42/30/10), y el
  adaptador `round` existe pero es restringido, no ausente.
- **A5**: conservar obligaciones F09/F10 y declarar sus dependencias sin reducir
  casos a `winner`. Su disponibilidad no bloquea la preparación de `quick`.
- **A6 corregida**: especificar testigos propios de la regla. No deducir `hits`
  de heridas/condiciones terminales ni usar actividad genérica como prueba de una
  regla. Si falta publicación, preparar su contrato y asignar la dependencia.
- **A7**: completar las obligaciones de diseño y sus referencias, sin cuotas de
  casos. P03 separa huecos de autoría, dependencias del motor y futura ejecución;
  su `complete` de campaña no es el cierre de la preparación.

## P02 — runner

`run_battery(cases, backend="numpy", rows=None, root=None)` compila una vez por
caso, muestrea oráculo y candidato con la misma semilla/horizonte/decisiones y
devuelve `BatteryReport`. Incluye:

- comparación por categorías con la puerta seis sigma existente
  (`_statistical.py:19-24`, citada);
- comprobaciones de forma, determinismo y multiplicidad del lote;
- `INCOMPATIBLE:observable` con propietario; `NOT_RUN:decision-script` con
  `owner=P01`; `INCOMPATIBLE:decision-scope` separado;
- backend nativo con `NOT_RUN:native-stale` si falta versión/símbolo/plan;
- sin fallback al modular y sin importar `_battery_cases` en runtime.

## Ejecución de comprobación

```text
pytest tests/python/verification/test_parity_battery_cases.py -q
  -> 2 passed

run_battery(battery_cases("quick"), rows=16)
  -> complete=False
     PASS         q04-injury-chart, q04-natural-armour-six, q03-netted-initial,
                  q06-intrinsic-save, q00-honorable
     DIVERGENCE   q04-parry-attempt, q05-flammable-fire,
                  q08-death-blow-optional, q11-black-hunger
     INCOMPATIBLE q09-fear-charged, q10-leader-six (observables G05/G06)
```

Se retira la atribución inicial de estas salidas a defectos reales G04/G06.
La revisión posterior reprodujo las cuatro salidas con 16 filas como `batch-mask`:
el criterio de presencia de categorías es inválido para muestras independientes.
Las cifras históricas de 64 filas tampoco se reprodujeron en la copia posterior.
Estos resultados no se usan para aceptar la preparación ni abrir correcciones
del motor. No se reejecutan ahora.

Hallazgo adicional: el candidato produce heridas negativas (`-1`, `-2`) en
algunas filas; se conservan como categoría (no se recortan), como exige P00.

## Continuación de la preparación

1. **P00/P01:** completar obligaciones y variantes justificadas, sin cuotas de
   casos. Corregir entradas que omiten la regla, referencias y preparación;
   declarar contrato y propietario de capacidades externas pendientes. Crear
   P01-deliverable.md.
2. **P02:** corregir multiplicidad, especificar testigos y comprobar infraestructura
   sin ejecutar el candidato. No derivar impactos de estados terminales. Crear
   P02-deliverable.md con dependencias explícitas.
3. **P03:** conectar catálogo, ejecutor e informes cuando sus interfaces y trabajo
   propio estén preparados; puede avanzar en partes independientes. No espera a
   observables implementados ni casos NumPy aprobados. Separar preparación,
   huecos de autoría y ejecución futura, sin reducir el denominador ni heredar
   marcas textuales como `PASS`.

No se modificó el motor, el CSV, `_replay.py` ni `cli/commands.py` en esta
integración. P01/P02 escribieron archivos disjuntos.
