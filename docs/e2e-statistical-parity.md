# E2E como escenario precompilado de paridad estadística

Trabajo individual para agentes: [contrato](e2e-statistical-delivery-contract.md),
[ejemplo](examples/e2e-statistical-parity.json) y
[prompt de coordinador](prompts/translate-e2e-statistical.md) y
[prompt individual](prompts/translate-e2e-statistical-worker.md).

## Objetivo

Reutilizar la configuración de combate de un E2E para comparar distribuciones
entre Modular (referencia) y un motor candidato; no reproducir el E2E exacto.

## Trabajo necesario

1. **Congelar entradas:** combatientes compilados, contexto, participantes
   auxiliares, estado inicial y límite de rondas; conservar identidad y huella
   del E2E de origen para detectar datos desactualizados.
2. **Separar ejecución:** las tiradas prescritas y expectativas exactas del E2E
   no forman parte de la comparación estadística. Declarar una política de
   decisiones aplicable a todas las simulaciones; no reutilizar ciegamente
   decisiones preparadas para una trayectoria concreta.
3. **Adaptar consumidores:** cargar el escenario sin recompilar y aplicar las
   mismas entradas y política de decisiones en ambos motores. Configurar por
   separado semillas, tamaño de muestra, lote y trabajadores.
4. **Comprobar admisión:** declarar incompatibilidad si un motor no puede
   representar alguna entrada. Los rechazos de construcción esperados pertenecen
   a las pruebas del compilador. No omitir entradas ni recurrir a otro motor.
5. **Comparar muestras:** ejecutar muestras aleatorias independientes y comparar
   las magnitudes declaradas con el criterio estadístico existente; informar
   aprobación, divergencia, incompatibilidad o fallo por escenario y candidato.

## Criterio de aceptación

Un E2E es utilizable cuando su configuración está congelada y vigente, ambos
motores la ejecutan íntegramente sin compilación durante el test, y sus muestras
producen una comparación estadística válida. Ser utilizable no implica aprobar
la paridad ni sustituye la validación de expectativas del E2E original.

## Conexión común desde el comando de paridad

Las entregas individuales se ejecutan con el comando de paridad existente.
`--level e2e` o `--catalog e2e` sin identificadores selecciona todas las entregas,
incluidas las bloqueadas y no aplicables, que se contabilizan sin ejecutarlas.
Los casos incompatibles se informan con su motivo. Ejemplo en PowerShell:

```powershell
python tools/mordheim-utils.py check parity --level e2e --simulations 1000 --workers 2 --backend numpy --magnitudes winner,wounds,condition --output outputs/e2e-parity/all.json
```

Para ejecutar solo una selección, usar `--e2e` o `--e2e-selection-file`:

```bash
mordheim-combat-lab parity --catalog e2e \
  --e2e <case_key|audit_id::id> [--e2e ...] \
  --simulations 100 --seed 2026 --workers 2 \
  --magnitudes winner,wounds,condition \
  --output outputs/e2e-parity/selection.json
```

- `--e2e-selection-file` admite un identificador por línea (`#` comentarios).
- `--output outputs/e2e-parity/all.json` guarda únicamente el JSON.
- `--output-md outputs/e2e-parity/all.md` guarda únicamente el resumen Markdown.
  Pueden usarse juntas para guardar ambos formatos de la misma ejecución,
  sin repetir simulaciones. Las rutas deben ser distintas. El Markdown muestra
  configuración, totales, divergencias, errores y motivos de incompatibilidad
  o bloqueo. Esta opción está disponible para el catálogo E2E.
- `--backend` elige `numpy` (predeterminado), `native` o `all`; `modular` solo
  no se admite porque no hay candidato que comparar.
- Las entregas declaran `magnitudes: ["winner"]`. `--magnitudes` amplía la
  campaña —`winner` es obligatorio; `wounds`, `condition` y `rounds` son las
  magnitudes que el ejecutor ya compara— sin reescribir entregas ni cambiar el
  contrato.
- Una entrega no se ejecuta si está `blocked`, es `not-applicable`, está
  desactualizada (`stale-delivery`), incumple el formato (`invalid-delivery`) o
  pide entradas que el ejecutor no expresa (`incompatible`).
- Los resultados separan `approved`, `divergence`, `reference-failure`,
  `candidate-failure`, `execution-failure`, `incompatible` y los dos estados no
  ejecutables. Una excepción del candidato se informa como `candidate-failure`,
  nunca como divergencia medida.
- Una muestra aprobada no certifica paridad estadística ni compatibilidad de
  motores.

### Límites conocidos

- El ejecutor compartido no expresa `initial_state` ni
  `auxiliary_participants`; esos casos quedan `incompatible` con el campo
  concreto.
- La política `engine-default` se comprueba sondeando los valores
  predeterminados de ambos motores; si no corresponden, los casos quedan
  `incompatible`. No se inventan decisiones ni se borran cintas prescritas.
- Los escenarios E2E son mayoritariamente de una ronda, así que la comparación
  de heridas y condiciones finales suele tener poco recorrido; el ganador sigue
  siendo la magnitud principal.
