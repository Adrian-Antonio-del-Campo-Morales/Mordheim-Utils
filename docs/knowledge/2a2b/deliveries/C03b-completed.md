# C03b — Destinatarios de listas Trollheim

**Estado: completo**, 49 cláusulas de C03b cerradas. El coordinador implementó
las dos consecuencias rechazadas en la primera integración. Base inicial: rama `2A2B`, HEAD `a1f92653`,
árbol compartido con cambios heredados. Solo mis archivos llevan cambios propios.

## Capacidades antes → después

- **Implementación nueva.** El Pergamino del Familiar Rata se ofrecía a los
  cuatro héroes de Clan Pestilens. Ahora `profile.equipment-restrictions`
  publica `forbids: rat_familiar_scroll` para Plague Priest, Plague Monks y Monk
  Initiates, y el Pestilens Sorcerer conserva la línea: la excepción impresa
  sigue legal y los tres destinatarios ilegales quedan rechazados.
- **Reconciliación/evaluación:** 44 filas de acceso ya implementado o sin una
  restricción adicional en el destinatario actual; no son comportamientos nuevos.
- **Implementación posterior del coordinador:** los fragmentos de piedra bruja
  de niebla requieren poseer un Censer, sin obligar a atacarlo con él. La obligación
  se activa sólo llevando los fragmentos. El Witch Doctor, líder inicial obligatorio,
  debe incluir el tocado; el Big Boss no queda obligado. Se reutiliza la validación
  de equipo requerido, añadiendo su condición opcional `when_items`; no se simula
  sucesión de campaña ni se inventa un efecto del accesorio. «One use» sigue en C15.

## Comprobación

`pytest tests/python/construction/test_t13_construction_recipients.py -q` → 24
pasan, incluido el caso nuevo; `compile_fighter` rechaza poseer el pergamino a
los tres portadores nombrados y compila para el Sorcerer. Evidencia conservada
una sola vez fuera del repo: `%TEMP%\c03b-evidence-final.txt`.
Corrección del coordinador: dos casos en
`tests/python/construction/test_c03b_equipment_obligations.py` aprobados por
`compile_fighter` (ausencia/presencia, Censer poseído/activo, destinatario y control
sin fragmentos). Tipos estrictos del módulo de elegibilidad y bundle `--check`
aprobados. Cambios: `eligibility/index.ts`, bundle regenerado, bindings en
`special-rules.yaml` de Lustria Clan Pestilens y Savage Goblins. Base exacta y
salidas: `%TEMP%\c03b-obligations-no57qaqb`. Sin modificar compilador ni runtime.

## CSV e integración

Propuesta original: `%TEMP%\c03b-prepared-final.json`, 50 claves. El coordinador
integró 47 cierres (3 de implementación, 38 reconciliaciones y 6 evaluaciones)
y conservó pendientes los otros tres, mediante preparación nueva, preview y
`apply --write`, conservando 4.556 claves y controles concurrentes. Evidencia:
`%TEMP%\c03b-integrated-w21cesy8`. No se repitieron pruebas sin cambios de código.
Los dos cierres finales se integraron con snapshot nuevo y el mismo protocolo;
propuesta y salidas en `%TEMP%\c03b-obligations-no57qaqb`. La cláusula de un solo
uso conserva su pendiente de C15. Sin E2E, commits ni pushes.

Integración C09: declarados `when_items` y nombres traducidos omitidos por el
coordinador. Ambos contratos editoriales pasan; salida en
`D:/DEVEL/Mordheim/_c09-out/coordinator-c03b-schemas.txt`.
