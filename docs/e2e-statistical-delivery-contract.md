# Contrato de entrega por E2E · v1

## Alcance y reparto

Traducir las entradas de un E2E a un escenario de paridad **estadística**.
No ejecutar su cinta exacta ni certificar paridad. El coordinador asigna un
`audit_id::id` único por agente; sin asignación, solicitarla. No hay reserva
automática de casos.

El [coordinador](prompts/translate-e2e-statistical.md) reparte tandas de 10 casos
entre subagentes, respetando la capacidad real del entorno. Cada trabajador
recibe el [prompt individual](prompts/translate-e2e-statistical-worker.md) completo
y una asignación exclusiva.

Cada agente escribe exclusivamente:
`tests/engines/fixtures/e2e-statistical-deliveries/<sha256(case_key UTF-8)>.json`.
No modifica el catálogo consolidado, motores, ejecutores, otros casos ni el YAML.
El coordinador integra y comprueba la admisión por motor después.

## Archivo

Modelo completo: [ejemplo real](examples/e2e-statistical-parity.json).
Campos obligatorios; no añadir otros:

| Campo | Contenido |
|---|---|
| `schema` | `mordheim-e2e-statistical-delivery/v1` |
| `status` | `translated`, `blocked` o `not-applicable` |
| `source` | Objeto con `revision` (HEAD), `path` (YAML actual relativo), `sha256` (bytes del YAML) y `test_id` (`audit_id::id`). |
| `case_key` | `e2e/<audit_id>/<id>` |
| `case` | Resultado de `tools.verification.compiled_cases.encode_case`; `null` si no está traducido. |
| `decision_policy` | `{"kind":"engine-default"}` para una traducción sin decisiones explícitas; `null` en los demás estados. |
| `magnitudes` | `["winner"]`; ampliar observables es trabajo de integración separado. |
| `reason` | `null` si está traducido; motivo concreto y entrada afectada en otro caso. |

## Traducción

- Leer el YAML actual y conservar sus entradas: ambos combatientes compilados,
  contexto completo (incluidos participantes locales), participantes auxiliares,
  estados iniciales y límite de rondas. Conservar también etiquetas sintéticas
  cuando existan. No completar combatientes ausentes con perfiles inventados.
- Reutilizar una entrada congelada únicamente con evidencia de correspondencia
  con las entradas actuales. Si no puede demostrarse, compilar durante la
  preparación con el exportador existente; nunca durante el futuro test.
- En `case`: `origin.kind = "e2e"`, origen actual, `determinism.dice = []`,
  `determinism.decisions = []`, `expectations = null`, `benchmark = null` y
  `limits = {"maximum_rounds": N}`. Usar el valor E2E (1 si se omite).
  Recalcular huellas con `encode_case`; no copiar huellas de entradas alteradas.
- No fijar semillas, simulaciones, lotes o trabajadores en el escenario.
- Sin decisiones explícitas, usar la política predeterminada del motor; la
  integración comprobará que ambos motores la interpretan igual. Si hay
  decisiones explícitas, marcar `blocked` indicando qué política general falta:
  no borrar la cinta y asumir equivalencia, ni inventar decisiones.
- Rechazo de construcción esperado: `not-applicable`. Un rechazo esperado en
  ejecución requiere revisión: `blocked`. Una entrada que no pueda codificarse
  íntegramente también queda `blocked`; no se simplifica para hacerla admisible.

## Comprobación y entrega

Para `translated`, comprobar lectura JSON y round-trip exacto:
`encode_case(decode_case(entrega["case"])) == entrega["case"]`.
Comprobar además identidad, huella del YAML y conservación de entradas.
Para los otros estados, comprobar `case = null` y motivo verificable.
No hace falta ejecutar combate, una campaña estadística ni crear nuevos tests.

Informar: caso asignado, archivo, estado, comprobaciones realizadas y bloqueo.
`translated` significa datos preparados, no compatibilidad de motores ni paridad
aprobada. No hacer commit ni push salvo autorización expresa.
