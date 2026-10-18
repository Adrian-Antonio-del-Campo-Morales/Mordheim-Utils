# C05a — Habilidades enanas y Slayer

**Estado: integrado y cerrado, 2026-10-16.** Rama `2A2B`, HEAD `a1f92653` más
cambios locales preservados. Segunda entrega desde `D:/DEVEL/Mordheim/C05a-iso2`;
integración por fragmentos sobre el checkout principal, sin restaurar archivos desde HEAD.

## Capacidades completadas

- Las tablas Dwarf y Slayer llegan a sus destinatarios por selección canónica;
  Rememberer humano conserva Speed y no recibe la columna Dwarf. Born Marksmen
  conserva su acceso suministrado de promoción; esos cierres previos no se reabrieron.
- Master of Blades publica una sola habilidad, Unbeatable Warrior, sin conceder
  el distinto Sword Master vampírico. True Grit declara y consume 1-3 derribado,
  4-5 aturdido, 6 fuera de combate.
- Slayer Cult ofrece los ocho miembros admitidos, incluidos Deathwish,
  Deathblow y Axe Mastery. Deathwish reutiliza inmunidad a psicología; Axe Mastery
  reutiliza Axe Expert, conservando su contrato de armas/carga y la exclusión impresa.
- Deathblow permite los ataques restantes tras quedar fuera de combate. El
  coordinador corrigió tres huecos de la entrega: propagación hasta herida/lesión,
  resto del pool después de un ataque anticipado y elección opcional de declinarlo.
  No duplica un pool ya completado y conserva su efecto desde derribado.
- Extra Tough, Resource Hunter y Relentless tienen disposiciones explícitas de
  campaña/movimiento. Las declaraciones T09 se alinearon con los miembros completos.

## Integración y comprobación

Fuentes de las tres bandas, catálogo de habilidades, contratos mecánicos,
EffectSet, runtime modular y dos archivos focales integrados; mapa de consumidores actualizado.
La base inicial exacta se declara preservada en la entrega aislada, pero su ruta
no fue aportada: el coordinador examinó el incremento disponible y preservó además
los archivos actuales antes de aplicar fragmentos en `%TEMP%/c05a-integration-wy5yp25m`.

Tras los remates, sólo construcción C05a y combate Deathblow: **15 passed**,
`%TEMP%/c05a-coordinator-final.txt`. Los 144 casos del ejecutor se reutilizaron;
no se repitió su batería de paradas/guardas ni auditorías generales.

Tres filas CSV restantes integradas con snapshot íntegro, conservación de las
4.556 claves/textos/huellas/notas y control concurrente:
`%TEMP%/c05a-final-csv-integration-7p5of9w0`. Sin pendientes propios; sin E2E,
vectorial/nativo, commits ni pushes.
