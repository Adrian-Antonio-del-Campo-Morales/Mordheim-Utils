# Baseline de integración del port web

Fecha: 2026-09-10 (Europe/Madrid)

Estado de F0: **completada**. Los resultados siguientes describen el punto de partida; no son requisitos que deban estar verdes en esta fase.

## Punto de partida

- Rama: `main`.
- Commit base: `2fa070af898c26009acba15705cc02e94e360006` (`feat(web): preserve desktop equipment cost ledgers`).
- Upstream: `origin/main`, divergencia `0 behind / 0 ahead`.
- Los demás trabajos/agentes estaban detenidos al tomar esta foto.
- Árbol sin consolidar: 59 modificados, 11 eliminados y 14 no versionados antes de añadir esta baseline.

Este es un checkpoint de diagnóstico, no un checkpoint limpio. No se ha atribuido cada cambio ni se han establecido propietarios permanentes. Si comienza trabajo simultáneo sobre un archivo central, la coordinación será puntual para ese archivo.

Que el árbol no compile o tenga tests fallidos no bloquea F0: esos problemas quedan documentados aquí para clasificarlos y resolverlos en las fases posteriores.

## Manifest de paridad

- Fichero: `tests/web/parity/campaign-test-manifest.json`.
- Filas: 1.209.
- Estado: 1.209 `pending`; ningún otro estado presente.

El manifest todavía no sirve como prueba de cierre.

## Gates ejecutados

| Gate | Resultado | Evidencia principal |
|---|---|---|
| Tests Python de `tests/web` | No disponible | Python global 3.10.6 y pytest 7.1.2; colección detenida por ausencia de `jsonschema` en cuatro módulos. La `.venv310` referencia un Python 3.14 inexistente. |
| Tests del núcleo TypeScript | Fallo | 27 ficheros pasaron y 19 fallaron; 308 tests pasaron y 34 fallaron. Hay errores de sintaxis y divergencias funcionales. |
| Typecheck del núcleo TypeScript | Fallo | Errores de sintaxis en `scenario-awards.ts`, `injuries-workflow.ts` y `service.ts`. |
| Tests de la aplicación web | Fallo | 2 ficheros pasaron y 14 fallaron; 15 tests pasaron y 2 fallaron. Trece suites no pudieron cargarse, principalmente por errores de sintaxis compartidos y un import ausente. |
| Typecheck de la aplicación web | Fallo | Errores de sintaxis compartidos en `injuries-workflow.ts` y `service.ts`. |
| Build web | Fallo | Vite se detiene al transformar `service.ts:293`. |

Versiones usadas: Node `v24.19.0`, Vitest `3.2.7`, Vite `7.3.6` y TypeScript `5.8.3`. Los binarios locales se ejecutaron directamente porque `npm` no estaba disponible en `PATH`; no se instalaron dependencias.

## Fallos base que deben distinguirse de regresiones posteriores

1. Errores de sintaxis en tres fuentes TypeScript impiden typecheck, build y parte de la colección de tests.
2. Falta el módulo importado `@app/features/battle/scenario-awards` desde `BattlePanel.tsx`.
3. Las suites que sí cargan muestran divergencias en avances, injuries, exploración, equipo, economía, draft, bajas, post-battle, rareza y límites/rechazos.
4. Los guardas de arquitectura detectan una referencia a Python en el adapter y la cadena `tkinter` en el bundle existente.
5. El entorno Python del checkout no permite ejecutar `tests/web` de forma reproducible hasta reparar o recrear su entorno de dependencias.

## Uso posterior

Conservar estos resultados para diferenciar los problemas presentes al inicio de los introducidos posteriormente. Cuando el bloque actual se consolide, podrán compararse los nuevos resultados con esta foto; no es necesario repetir F0 ni exigir que esta baseline quede verde.

## Actualización posterior a F0 (2026-09-10)

- Vitest TypeScript completo: 51 ficheros, 430 tests, todos verdes.
- Typecheck TypeScript completo: verde, incluidas las fixtures/tests actualizadas al contrato V4.
- Aplicación web: typecheck y build de Vite verdes. Su Vitest sigue con 29 fallos en 7 suites (59 pruebas verdes), concentrados en fixtures/expectativas de UI que aún montan el antiguo `CampaignSlice`; no se han tratado como regresiones del núcleo.
- Esta actualización no cambia la foto F0 ni certifica build o tests Python.
