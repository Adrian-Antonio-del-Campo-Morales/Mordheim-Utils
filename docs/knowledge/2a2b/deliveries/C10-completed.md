# C10 — Psicología, odio e identidad compartida

**Estado:** cláusula pendiente de C10 (Vengeful Hatred) cerrada. Instinctual Violence lo cerró el
coordinador. Sin commits, pushes, E2E ni documentos nuevos.

## Capacidad antes → después

| Capacidad | Antes | Después |
|---|---|---|
| Vengeful Hatred | `connection`: `individual.<band>.<profile>` cubría a todos los guerreros de un perfil, `band.<id>` a todas las bandas del listado y Leader bastaba para conceder | identidades de **instancia** suministradas: el guerrero y su banda llevan claves propias (`instance_id`, `warband_instance`) y el odiado es una sola de ellas. La rama de perfil desaparece; ninguna categoría se lee como individuo |

## Transporte (configuración → compilación → Odio)

- Configuración: `enmity_kind` + `enmity_target` en el portador; `instance_id` / `warband_instance`
  en cada guerrero, todo por el canal existente de hechos suministrados
  (`contracts.py::TRAIT_TYPES`, `runtime-scope.yaml`, esquema de perfiles).
- Compilación: `compile_fighter` valida (pareja incompleta, kind desconocido, identidad vacía, clave
  de instancia con espacios) y compila `instance.<clave>` / `warband-instance.<clave>`.
- Odio filtrado: `contexts.vengeful_enmity_target`, consumido por `_hit_reroll` como el resto de Odio:
  individuo = esa instancia; líder = el individuo seleccionado cuando ocurrió la herida, aunque
  pierda Líder (otro portador de Leader nunca entra); banda = la instancia de banda nombrada; tipo de banda = todas las
  bandas del tipo, la única rama por categoría. Sin destinatario no hay concesión.

## Comprobaciones

- `test_t13_c10_psychology_identity.py` → **22 passed** (salida guardada en `%TEMP%/c10-final-evidence.txt`
  conserva la evidencia del ejecutor). Tres casos exigidos: dos guerreros del mismo perfil con sólo
  el identificado odiado; dos bandas del mismo tipo con sólo la nombrada en la rama concreta y ambas en
  la de tipo; rama de líder referida al individuo determinado.
- Espejo de traits (`test_combat_traits_definition_matches_the_compiler_registry`,
  `test_supported_combat_traits_are_compiler_traits`) → 2 passed.
- YAML propio: las dos piezas tocadas no añaden desviaciones de formato (los avisos de
  `format_yaml --check` son de otros registros del mismo fichero).
- Ledger de consumidores: `mechanic.vengeful-hatred` reescrito con la instancia; sigue sin desajuste
  propio (quedan 11 `missing` + 5 `unknown` de otros paquetes, ajenos a esta cláusula).

## CSV (sólo `query` + `prepare`)

Integrada la única fila mediante propuesta nueva en `%TEMP%/c10-vengeful-integration-qf_cv55a`,
copia íntegra previa, validación de conservación y control concurrente; `pending {}`.
El coordinador corrigió la condición adicional de conservar Líder y adaptó el discriminador
existente a la duración permanente: 1 passed, `%TEMP%/c10-coordinator-permanent-leader.txt`.
Las demás comprobaciones del ejecutor se reutilizaron sin repetirlas. C10 cerrado.
