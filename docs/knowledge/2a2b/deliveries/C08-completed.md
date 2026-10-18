# C08 — Mutaciones: brazos, ataques y contacto

**Estado: completo e integrado**, ocho cláusulas cerradas; rama `2A2B`, HEAD `a1f92653`.

**Capacidades antes → después**

- **Extra Arm**: conserva ataque del arma o ataque natural con escudo/rodela, incluso para Poseídos;
  rechaza armas a dos manos/emparejadas. Acceso impreso también en mano extra: Poseídos sin armas.
- **Great Claw**: ataque +1 F existente conectado; prohibición de armas según brazos restantes.
  El coordinador corrigió la combinación con Extra Arm: dos armas y un escudo son legales con
  tres brazos; tres armas no. Sin Extra Arm siguen rechazados dos armas o un arma a dos manos.
- **Blackblood**: reacción S3 sin críticos existente, ahora con procedencia explícita de cuerpo a cuerpo.
  La infección hereda la del ataque padre; impactos sintéticos independientes conservan su
  tratamiento no melee. Contacto y ausencia de críticos conservados.
- **Scorpion Tail, Spines, Tentacle**: los `requires` quedan resueltos y comprobados (F5 y F2 contra inmunidad; S1 automática al inicio de fase sin críticos; grapa con nominación y mínimo 1).

**Archivos/base**: `compiler.py`, `modular/attacks.py`, `modular/aftermath.py`,
`test_source_corrections.py` y `test_special_bindings.py`. Checkout compartido sucio;
diff reconstruido en `%TEMP%/c08/c08-incremental.diff`. Elegibilidad compartida dejada a su propietario.

**Comprobaciones** (salida en `%TEMP%\c08\`): `test_special_bindings.py` 9 pasan (incluye el discriminador nuevo legal/ilegal), `test_source_corrections.py` 120 pasan (Blackblood y Scorpion Tail nuevos), `test_t13_tentacle_nomination.py` 10 pasan, `test_stateful_rules.py` 19 pasan; `npm run check:eligibility` al día. Comprobación directa de las seis mutaciones: `verify_c08.py`/`verify_c08b.py`.

**CSV integrado**: propuesta original contrastada con las ocho filas actuales y preparada de nuevo
en `%TEMP%/c08-integrated-_jg628tc`. Snapshot completo previo, preview, conservación de 4.556 claves,
textos, huellas y notas, y control concurrente. Discriminador de composición del coordinador correcto:
`%TEMP%/c08/coordinator-arm-composition.txt`. Sin repetir las baterías del ejecutor.

**Límites**: capacidad por brazos restantes, sin nominación anatómica del brazo mutado. La base
reconstruida no acredita aislamiento inicial; el coordinador integró los cambios presentes, sin
restaurar archivos. La entrega registró cuatro fallos de elegibilidad y uno de Condemned; su causa
y antigüedad no quedan demostradas por `.pytest_cache`. No se declara una batería global verde.
Sin E2E, commits ni pushes.
