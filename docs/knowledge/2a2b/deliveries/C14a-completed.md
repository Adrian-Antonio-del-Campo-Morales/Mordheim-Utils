# C14a — Modificadores de ejemplar de arma

**Estado:** completo, tres cláusulas cerradas, 2026-10-15. Rama `2A2B`,
checkout `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, compartido. Base inicial
en `D:/tmp/c14a/base`. Sin cambios propios en `compiler.py` ni `equipment_preparations.py`.

**Antes → después.** Bendición, Honing y coating carecían de conexión al ejemplar. Ahora:

1. **Bendición de exploración:** se suministra sobre un ejemplar legal de Sisters of Sigmar o Witch
   Hunters; ese arma hiere Undead y Possessed en 2+ (`prepare_wound_context` limita el objetivo de
   herida a 2 contra `undead_or_possessed`). Impacto, salvaciones y secuencia de heridas intactos: un 3
   sigue fallando el impacto y un 1 sigue sin herir. Un mercenario es rechazado.
2. **Honing:** hasta tres hojas nombradas, Dragon Swords incluidas, ganan Cutting Edge
   (`armour_penetration: 1`, tag `rule.cutting-edge`) sólo en esas hojas; una maza se rechaza y la otra
   mano conserva su salvación. Duración suministrada (la batalla); sin el hecho, nada se aplica y no se
   pide tirada: el servicio entre batallas sigue sin simularse.
3. **Master Craftsman:** los tres resultados suministrados llegan al arma elegida: +1 Fuerza,
   +1 Iniciativa al portador o coating (+1 Fuerza y +1 a la tirada de Heridas). La tabla ya existía
   en `build/audit/m5-coord/printed/the-foole.txt`; coincide con Fanatic Online 89, página 3.
   Iniciativa cambia el orden del asalto, también desde una mano adicional; perder el arma retira
   su bono. El coating conserva la contrapartida limpia contra inmunidad al veneno.

**Implementación:** modificadores físicos en `runes.py`, herida en `contexts.py`, condiciones,
esquemas y hechos de slot; pruebas en `test_supplied_weapon_modifiers.py`.

Cierre: dos condiciones y hechos de slot adicionales, tabla nativa, Iniciativa de mano extra en
`phases.py` y retirada en `equipment.py`. Tres discriminadores nuevos; sólo se repitió el caso
de orden tras corregir su contexto de turno. Salidas `master-craftsman-*.txt` en `D:/tmp/c14a/out/`.

**Integración:** el coordinador eliminó la exclusividad inventada de un modificador por objeto.
Bendición, Honing y una runa se componen sobre la misma arma; una segunda runa sigue rechazada.
Un discriminador demuestra el fallo anterior y la corrección (`coordinator-composition-before.txt`
y `coordinator-composition-after.txt` en `D:/tmp/c14a/out/`).

**Comprobación:** reutilizados los nueve casos iniciales y 32 de runas/preparaciones.
Esquemas actuales de condiciones y perfil nativo válidos; sin nueva batería editorial general.

**CSV integrado:** propuesta contrastada con las tres filas actuales y preparada de nuevo en
`%TEMP%/c14a-integrated-_02a89zi`; snapshot completo, preview y escritura con conservación de
4.556 claves/campos protegidos/notas y control concurrente. Cierre de la última fila en
`%TEMP%/c14a-complete-mjn4x1a9`, con nueva preparación y conservación. Diferencias iniciales en
`D:/tmp/c14a/out/`.

**Pendientes del paquete:** ninguno. Productores post-batalla, encuentro especial y contabilidad
de dos batallas excluidos; los resultados actuales se suministran sin simular campaña. E2E,
vectorial/nativo fuera del encargo. Sin commits ni pushes.
