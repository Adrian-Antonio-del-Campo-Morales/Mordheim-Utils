# H01-Aenur — Ienh-Khain: Fuerza y críticos

## Estado

**H01-Aenur integrado por el coordinador, 2026-10-17: 4/4.** Cuatro filas
cerradas con snapshot completo, prepare/preview y control concurrente;
4.556 claves, textos, huellas y notas conservados. Consumidores y evidencia
anteriores acumulados. Integración: `%TEMP%/aenur-coordinator-1xh9o0dw/`.
Resultados del ejecutor reutilizados sin repetir pruebas. Reconciliación de
comportamiento existente, sin código nuevo de producción.

Cuatro cláusulas asignadas. **Ninguna necesitaba código nuevo**: el contrato
`weapon.ienh-khain` ya lleva `strength_bonus 1`, `critical_threshold 5` y
Parada; el equipo único de Aenur mapea a ese contrato y el kit canónico resuelve
la espada sin nombrarla. Faltaban discriminadores para el +1 aplicado una sola
vez y para el límite 4/5/6. Se añadieron dos pruebas en un archivo nuevo; no se
modificó fuente, dato ni consumidor.

Los dos archivos de prueba existentes con casos Aenur
(`test_t13_hireling_admission.py` y `test_t13_defence_parries_and_ward.py`)
tienen cambios en vuelo de otros agentes; no se editaron.

## Capacidades (antes → después)

**Reconciliadas (ya funcionaban; evidencia reejecutada):**

- **Kit y referencias** — el perfil compila sin `main_weapon_id`; el kit impreso
  resuelve `weapon.ienh-khain` y sus tres referencias apuntan al mismo contrato.
  No hay contribución extra por aparecer en el objeto y en la lista.
- **+1 Fuerza una sola vez** — el punto vive en el contrato de ataque de la
  espada (`trigger: attack`, `application: attack`), no en los efectos pasivos
  del portador. Compone una vez con Mighty Blow impreso: S4 → 6. Un duplicado
  daría 7 y el caso lo distingue.
- **Críticos 5–6** — `critical_threshold 5` llega a `prepare_wound_context` y
  `resolve_wound`. Límite ejecutado: herida 4 no es crítico, 5 y 6 sí. Se
  conservan la disponibilidad por turno y la excepción de "necesitar 6".
- **Propiedad del arma** — el crítico no se traslada al ataque de otra arma: el
  contrato es de ataque y los efectos globales del perfil mantienen crítico 6 y
  sin Parada. Aenur no tiene una segunda ruta legal de arma (el matcher del kit
  impreso rechaza cualquier otra), así que no se fabricó un build alternativo.

**Implementado:** sólo los dos discriminadores ausentes.

## Ruta canónica comprobada

1. `profiles[0].equipment.unique_equipment[0]` (Ienh-Khain) resuelve por
   `simulation-mappings` a `weapon.ienh-khain`.
2. `compile_fighter` sin arma explícita toma el kit impreso: A4, S4, la espada
   con +1 Fuerza, Parada y crítico 5; el perfil conserva su Mighty Blow.
3. `initialize_fighter` → `_attack_strength` (S6) → `prepare_wound_context`
   (umbral 5) → `resolve_wound` (4/5/6). Sin disparo, campaña ni monturas.

## Disposiciones CSV propuestas

Paquete preparado (sin `--write`):
`C:\Users\Pholtergate\AppData\Local\Temp\h02-aenur-prepared.json` — 4 cambios,
claves exactas, instantánea íntegra y hash del CSV coincidente con el estado
actual. `apply` en modo vista validó conservación; **no se escribió el CSV**.

| id (sufijo) | clause_id | cambios propuestos | evidencia ejecutada |
|---|---|---|---|
| `hireling.dramatis.aenur.item.ienh-khain.rule.strength/unclassified` | `whole` | `pending {}`, condiciones attack/attack/stack, `consumer` con rutas reales | `test_h01_aenur.py::test_the_kit_resolves_ienh_khain_and_applies_its_strength_once` + caso de admisión |
| `hireling.dramatis.aenur.item.ienh-khain.rule.critical/unclassified` | `whole` | `pending {}`, `consumer` con `resolve_wound` | `test_h01_aenur.py::test_the_sword_critical_starts_at_five_and_keeps_the_ordinary_limits` + caso de umbral fijo |
| `@/profiles/0/equipment/unique_equipment/0/rules/1/unclassified` | `whole` | `effect_id` real, `pending {}` | discriminador de Fuerza + caso de admisión |
| `@/profiles/0/equipment/unique_equipment/0/rules/2/unclassified` | `whole` | `effect_id` real, `pending {}` | discriminador 4/5/6 + caso de umbral fijo |

Se sustituyen los `effect_id` provisionales (`proposed.weapon.ienh-khain`) por
el operador real y se retira `source_blocked`/`requires`, que ya no aplican. Se
conserva toda la evidencia anterior y sólo se **añaden** notas.

## Archivos propios

- `tests/python/combat/modular/test_h01_aenur.py` — dos pruebas nuevas.
- `docs/knowledge/2a2b/deliveries/H01-Aenur-completed.md` — este documento.

Sin cambios en fuentes, bindings, consumidores ni CSV.

## Comprobación mínima

- `pytest tests/python/combat/modular/test_h01_aenur.py` → **2 passed**,
  exit 0 (`…\Temp\h02-aenur-run1.txt`).
- Casos existentes reutilizados (admisión del arma única y umbral fijo con
  ataque completo) → **2 passed**, exit 0
  (`…\Temp\h02-aenur-existing-run1.txt`).
- `t13_csv.py prepare` y `apply` (vista) → exit 0, 4 claves, instantánea
  coincidente (`…\Temp\h02-aenur-apply-preview.txt`).

Sin E2E, suites globales, parity, cobertura ni vectorial/nativo.

## Límites y bloqueos

- **CSV:** cuatro disposiciones integradas por el coordinador.
- **Concurrencia:** los casos Aenur existentes viven en archivos con cambios
  activos de otro agente; los discriminadores nuevos están en archivo separado.
- **Separación entre armas:** no existe una segunda arma legal para Aenur (el
  kit impreso la rechaza), así que se acredita por el contrato de ataque y por
  los efectos globales, no con un build inventado.
