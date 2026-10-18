# H01-Veskit — garras, cuerpo metálico y estados individuales

## Estado

**H01-Veskit cerrado e integrado por el coordinador, 2026-10-17: 5/5.** Cinco
filas aplicadas con snapshot íntegro, prepare/preview y control concurrente;
4.556 claves, textos, huellas y notas conservados. Consumidores y evidencia
anteriores acumulados. Integración en `%TEMP%/veskit-coordinator-762l1ii5/`.
Resultados del ejecutor reutilizados, sin repetir pruebas. Reconciliación de
comportamiento existente; sin implementación nueva de producción.

Cinco cláusulas asignadas. **Ninguna necesitaba código de motor nuevo**: el
perfil ya se promueve al paquete de duelo (`hirelings.dramatis-personae.core`),
el kit impreso resuelve `weapon.veskit-claws`, y los operadores de armadura,
lesión y psicología ya estaban conectados en la KB. Faltaban discriminadores
ejecutados para la cara de armadura, el modificador total de las garras y la
prueba de psicología; se añadieron tres pruebas en un archivo nuevo. No se
modificó fuente, dato ni consumidor.

Base: los archivos compartidos relevantes (`core.yaml`, `execution.yaml`,
`close-combat.yaml`, `test_t13_defence_parries_and_ward.py`) tienen cambios en
vuelo de otros agentes; no se editaron. Las pruebas nuevas viven en un archivo
propio y reutilizan los casos Veskit ya existentes.

## Capacidades (antes → después)

**Reconciliadas (ya funcionaban; evidencia reejecutada):**

- **Garras / ataque no duplicado** — el perfil compila A4 con
  `attacks_bonus 0`: las pistolas integradas no suman un segundo ataque.
- **Garras / Fuerza y modificador** — `fixed_strength 5` y
  `armour_penetration 1`; Fuerza 5 aporta -2 y el punto propio de las garras
  completa el **-3 total**. Contra armadura pesada (5+) la tirada objetivo es 8
  y la salvación no existe. Sin perfil de disparo.
- **Cuerpo metálico** — `trait.natural-armour-save` con valor 3: ataque sin
  modificadores resuelve en 3+ (salva con 3, falla con 2). Sigue siendo
  armadura, no ward ni regeneración.
- **No Pain** — `mechanic.veskit-no-pain` colapsa todo resultado de lesión
  distinto de Out of Action a `STANDING`: Derribado (1) y Aturdido (3) no lo
  tumban; el 5 sigue eliminándolo. Implementado por el operador dedicado, no
  por `skill.ignore-pain`.
- **Unfeeling** — `mechanic.psychology-immunity` en el perfil: una prueba de
  psicología devuelve superada sin pedir tirada de Liderazgo.

**Implementado:** sólo los tres discriminadores ausentes. No se creó un segundo
sistema de armas, lesiones ni psicología.

## Ruta canónica comprobada

1. El catálogo expone `hireling.dramatis.veskit` y ofrece
   `weapon.veskit-claws` en la mano principal.
2. `compile_fighter` sin `main_weapon_id` resuelve el kit impreso
   (`weapon.veskit-claws`); el perfil compilado conserva M5/WS5/BS4/S4/T4/W2/I5/A4/Ld8.
3. `initialize_fighter` y las fases modulares consumen las consecuencias:
   `prepare_armour_context`/`armour_target` (3+ y -3 total), y
   `_resolve_wound_damage_body` (estados de lesión).
4. `resolve_local_leadership` corta la prueba de psicología antes de tirar.

## Disposiciones CSV propuestas

Paquete preparado (sin `--write`):
`C:\Users\Pholtergate\AppData\Local\Temp\h01-veskit-prepared.json` — 5 cambios,
claves exactas, instantánea íntegra y hash del CSV coincidente con el estado
actual. `apply` en modo vista validó conservación; **no se escribió el CSV**.

| clause_id | pending | relación propuesta | evidencia ejecutada |
|---|---|---|---|
| `extra-attack-already-in-profile` | `{}` | `equivalent` | caso existente A4 + prueba nueva |
| `claw-strength-and-save-modifier` | `{}` | `equivalent` | `test_h01_veskit.py::test_the_claws_keep_four_attacks_and_reach_a_total_minus_three_modifier` |
| `metallic-body-three-plus-save` | `{}` | `parameterized_variant` (sin cambio) | `test_h01_veskit.py::test_metallic_body_is_the_armour_save_on_three_or_better` |
| `ignores-knocked-down-and-stunned` | `{}` | `equivalent` | caso existente de lesiones (1/3/5) |
| `psychology-immunity` | `{}` | `equivalent` (sin cambio) | `test_h01_veskit.py::test_unfeeling_skips_the_psychology_test_instead_of_rolling_leadership` |

Las propuestas sustituyen los `effect_id` provisionales
(`proposed.rule.*`) por los operadores reales, rellenan `consumer` donde estaba
vacío y actualizan el contrato de las garras con los valores impresos. Se
conserva toda la evidencia anterior y sólo se **añaden** notas.

## Archivos propios

- `tests/python/combat/modular/test_h01_veskit.py` — tres pruebas nuevas.
- `docs/knowledge/2a2b/deliveries/H01-Veskit-completed.md` — este documento.

Sin cambios en fuentes, bindings, consumidores ni CSV.

## Comprobación mínima

- `pytest tests/python/combat/modular/test_h01_veskit.py` → **3 passed**,
  exit 0 (`…\Temp\h01-veskit-run1.txt`).
- Casos Veskit existentes (tres nodos, cinco casos) →
  **5 passed**, exit 0 (`…\Temp\h01-veskit-existing-run1.txt`).
- `t13_csv.py prepare` y `apply` (vista) → exit 0, 5 claves, instantánea
  coincidente (`…\Temp\h01-veskit-apply-preview.txt`).

Sin E2E, suites globales, parity, cobertura ni vectorial/nativo.

## Límites y bloqueos

- **CSV:** cinco disposiciones integradas por el coordinador.
- **Concurrencia:** el bloque Veskit ya existente vive en
  `test_t13_defence_parries_and_ward.py`, que tiene cambios activos de otro
  agente; por eso los discriminadores nuevos están en un archivo separado y no
  se tocó el archivo compartido.
- No se detectó ninguna contradicción de fuente que requiera web/PDF: la KB
  imprime Fuerza 5, modificador total -3, armadura 3+, No Pain y Unfeeling.
