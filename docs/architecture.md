# Arquitectura

## Paquetes del monorepo y dependencias permitidas

```text
mordheim_core
  ↑
mordheim_knowledge → mordheim_construction → mordheim_combat
                  ↑          ↑
                  └ mordheim_combat_lab.application ← mordheim_combat_lab.persistence
                         ↑
                         mordheim_combat_lab.ui
                         mordheim_campaign (reutiliza mordheim_ui)

mordheim_combat_lab.verification → mordheim_knowledge + mordheim_construction
                                   + mordheim_combat + tests/specs
```

`mordheim_core` no conoce YAML, UI ni verificadores. `mordheim_combat` recibe
`CompiledFighter` y no carga la KB. `mordheim_combat_lab.application` ejecuta
casos de uso sin Tkinter. Las dos aplicaciones presentan resultados con la capa
compartida `mordheim_ui` y coordinan sus propios hilos. `verification` está
fuera del runtime y utiliza el motor real como sistema bajo prueba.

`mordheim_campaign` es *interface-first*: los widgets dependen de view-models y de la
capa UI compartida; las bandas y perfiles canónicos entran por
`mordheim_campaign.application.knowledge_port` (sobre `mordheim_knowledge`) y la
persistencia de campaña vive en `mordheim_campaign/persistence`. La legalidad de
post-batalla y el uso de `mordheim_construction` son fases posteriores.

## Recursos compartidos

La KB vive una sola vez en `sources/knowledge/`. La resolución de rutas
pertenece a `mordheim_knowledge.paths` (`knowledge_root()`), con override por
variable de entorno (`MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH`) y soporte de EXE
congelado para ambas aplicaciones. El corpus de verificación vive en
`tests/specs/` (`specifications_root()`), es material de test y no se distribuye.

## Recorrido de una regla

1. La regla editorial y su binding están en `sources/knowledge/`.
2. `mordheim_knowledge` valida y carga documentos por IDs estables.
3. `mordheim_construction` valida accesos y compila el binding en `CompiledFighter`.
4. El motor consume el efecto en una fase o handler con estado.
5. Un escenario de `tests/specs/` comprueba concesión, compilación y resultado observable.

El motor modular divide estado, preparación de contextos, ataques, pools, efectos
posteriores, rondas y duelo. El vectorizado es el runtime de análisis de la UI,
pero no el oráculo de corrección del modular.

## Backend nativo (Cython)

`mordheim_combat._combat_native` es un segundo runtime optimizado, compilado a
C con Cython, que porta la semántica del motor vectorizado (nunca la del
modular directamente: el modular sigue siendo el único oráculo de corrección).
Vive en tres piezas:

- `_combat_compile.py` reutiliza exactamente los helpers Python certificados
  del vectorizado para plegar en escalares, una vez por duelo, cada decisión
  de etiquetas que el motor tomaría dentro de sus bucles (fuentes, reacciones,
  paradas, heridas automáticas, anvil-head, etc.).
- `_combat_native.pyx` consume ese plan compilado con structs planos
  (`FighterC`, `SourceC`, `DuelC`, `StateC`) y resuelve cada ronda sobre filas
  activas en C: paradas, defensas de impacto, heridas y reacciones usan el
  mismo orden de fases y tablas que el vectorizado.
- `_combat_native.pxd` declara la frontera C entre las funciones mutuamente
  recursivas del motor.

El driver de Python (`simulate_duel` en `vectorized.py`) expone el backend con
`backend="native"` o `"auto"`; `available_backends()` lo reporta solo cuando la
extensión está compilada, de modo que un entorno sin compilador C conserva el
comportamiento NumPy sin cambios. El motor usa un PCG32 por lote derivado de la
semilla de la petición, por lo que una misma petición es reproducible (replay
determinista por semilla). El plan se compila una vez por petición (~0,5 ms);
la compilación del `.pyx` a `.pyd` ocurre una sola vez en la instalación y
queda fuera de cualquier medición de rendimiento.

### Verificación y rendimiento

El nativo se certifica contra el oráculo modular con la misma puerta
estadística de seis sigmas que NumPy (`compare_statistical_parity(...,
backend="native")` comparte la muestra modular con NumPy), y la puerta de
rendimiento exige mejorar al menos un escenario un 10 % sin regresiones
mayores del 5 % frente a NumPy (`benchmark --backend native`).
`test-report --statistical` y `parity --statistical` incluyen el backend nativo
automáticamente cuando está disponible; en el CSV semántico los casos por
operador no le aplican (`NOT_APPLICABLE`): el nativo es un motor de duelo
completo sin operadores independientes, verificado en las filas de duelo
(estadísticas) y con la semántica de operador cubierta por el adaptador NumPy.
Mientras la extensión no está compilada, esas filas se marcan `NOT_AVAILABLE`
y el reporte permanece `PENDING`, señal del trabajo pendiente real.
Los cambios del núcleo C se pasan por AddressSanitizer antes de integrarse
(sobrescrituras de structs sin inicializar, dimensionado de arrays y
acumulación por lotes ya detectados y corregidos así).

La legalidad pertenece a `mordheim_construction`; la composición a
`mordheim_core.effects`; las fases a `mordheim_combat.phases`; workbooks y
preferencias a `mordheim_combat_lab.persistence`. Los tests de
`tests/architecture/` hacen ejecutables estos límites.
