# M00 — Misericordia del Conde de Ventimiglia

**Estado:** integrado, 2026-10-15. Rama `2A2B`, HEAD `a1f92653`, checkout
`D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, con cambios concurrentes.
Resumen del coordinador a partir de la entrega recibida.

**Capacidad:** antes sólo existía el registro de campaña. Ahora el objeto físico
`count_of_ventimiglias_misericordia` se selecciona y compila con el operador propio
`weapon.count-of-ventimiglias-misericordia`: espada con parada, tabla de heridas
1–3 aturdido / 4–6 fuera de combate. Sin Dolor convierte el aturdimiento en
derribado para el No Muerto probado. No se implementa adquisición/exploración.
La Misericordia de Cursed Cavalcade conserva su identidad y reglas distintas.

**Cambios:** nueva identidad en los catálogos de armas, mecánicas, ejecución y
mapeos; `item_id` en `campaign/exploration-and-income.yaml`. Nuevo borde inferior
`InjuryContext.stun_threshold` en `phases.py`, aplicado desde
`modular/contexts.py`; guarda de soporte optimizado en `kernel.py`. El coordinador
añadió la entrada concreta al mapa `verification/consumers.py`.
Se reutilizan compilación, posesión física, parada y resolución de heridas.

**Comprobación:** el agente declara 8 casos aprobados en
`tests/python/combat/modular/test_t13_ventimiglia_misericordia.py`: extremos y límite
3/4, No Muerto canónico y acceso/conservación de la otra arma. El coordinador leyó
los cambios y las expectativas; no repitió esas pruebas. La salida focal guardada
no fue identificada de forma inequívoca en la entrega. Las comprobaciones más
amplias mencionadas por el agente no acreditan el estado integrado general ni se
reprodujeron. Comprobación de integración: prepare, preview y escritura CSV
aprobados; validación estática del registro y formato de los cambios del coordinador.

**CSV:** integrada la clave
`source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/unclassified`,
cláusula `misericordia-injury`, con `pending: {}`. Preparación nueva sobre el CSV
actual, conservación de 4.556 claves y controles concurrentes mediante la
herramienta mantenida. Propuesta, snapshot y salidas en
`C:/Users/Pholtergate/AppData/Local/Temp/m00-misericordia-integrated-aerkv5dq`.

Sin pendientes propios de M00. Sin E2E, commits ni pushes del coordinador.
