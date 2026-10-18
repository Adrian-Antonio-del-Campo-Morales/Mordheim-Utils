# C06 — Constructos Clockworkers

**Estado: completo e integrado**, 26 pendientes reconciliados y dos notas de alcance.

**Implementación nueva:** ninguna en código de producción. El bloque ya estaba
conectado en la KB y en los consumidores compartidos; lo que faltaba era el
discriminador (la banda no tenía ninguno) y el dictamen del marcador
`work: assessment`. Lo demás es reconciliación con evidencia vigente, no una
fase de evaluación: cada capacidad se comprobó a través de su consumidor real.

**Capacidades, antes → después**

- *Ranuras, costes y armadura*: los dos perfiles publican
  `profile.equipment-restrictions` (equipment_slots 2/4, armour_slots 1,
  slot_costs por pieza); el guardián ponderado ya aplica la capacidad al
  conjunto completo contando copias físicas distintas (declaradas u poseídas) y
  exime al constructo del máximo normal de armas. Sin cambios.
- *Destinatarios*: `clockwork_rifle` y `heavy_armour` alcanzan solo a
  master-of-clocks y dwarf-engineer, en la oferta **y** en la selección directa.
- *No Pain*: el `skill.ignore-pain` compilado llega a
  `phases.injury_condition`, que convierte el aturdido en derribado.
- *Venenos y drogas*: el transporte de veneno elimina la contribución contra el
  constructo y el compilador descarta su propia preparación de droga.
- *Psicología*: `resolve_fear` no exige tirada al constructo cargado por quien
  causa miedo.
- *Equipo incorporado* (dictamen del marcador): la mitad ejecutable es la
  capacidad de ranuras, implementada; la prohibición de retirar equipo
  incorporado es contabilidad de plantilla — el contrato no distingue retirar
  de abandonar y la fuente usa abandonar para liberar ranuras —, así que no se
  inventa consumidor. No concede inmunidad en el duelo: el látigo sigue
  desarmando al constructo.

**Archivos/base:** dos tests nuevos; base `a1f92653` con los cambios locales
heredados intactos (`%TEMP%/c06/base-heredado.diff`, `base-status.txt`). Diff
propio en `%TEMP%/c06/c06-incremental.diff` (213 líneas, sólo tests). No toqué
`eligibility/index.ts`, `_eligibility.js` ni `compiler.py` (en vuelo).

**Comprobaciones:** `pytest tests/python/construction/test_c06_clockworker_constructs.py
tests/python/combat/modular/test_c06_clockworker_construct_duel.py` → 12 passed,
exit 0 (`%TEMP%/c06/pytest-c06-final.txt`); sondas directas en
`%TEMP%/c06/probe*.py`.

**CSV integrado:** las 28 filas contrastadas con el estado actual; preparación nueva,
preview y escritura en `%TEMP%/c06-integrated-90nhwpza`. Snapshot íntegro previo,
4.556 claves/textos/huellas/notas conservados y control concurrente. Son 26 cierres
y dos notas, sin nuevas capacidades de producción. Evidencia del ejecutor reutilizada.

**Pendientes del paquete:** ninguno. `constructs-never-leaves-combat` conserva scope NO con la
división anotada; `band--constructs` sigue descriptivo y sin binding para no
duplicar la concesión a los dos constructos.

Sin E2E, commits ni pushes.
