# Prompt de coordinador: traducción paralela de E2E

Coordina agentes para traducir los E2E actuales a escenarios precompilados de
paridad estadística. Ejecuta el trabajo; no te limites a proponer un plan.

## Entorno y alcance

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils`.
- Rama: `precompile-all`.
- No accedas ni modifiques `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`.
- Alcance predeterminado: todos los E2E pendientes, en tandas de 10 casos.
  Si el usuario limita casos, cantidad o tiempo, respeta ese límite.
- Estás autorizado a lanzar subagentes para este trabajo. No crees chats nuevos
  del usuario, no hagas commit ni push y no integres todavía las entregas en el
  ejecutor estadístico.

## Preparación única

1. Verifica carpeta, rama y estado de Git; conserva cambios ajenos. Si la rama no
   coincide, informa sin cambiarla automáticamente.
2. Lee `AGENTS.md`, `docs/e2e-statistical-parity.md`,
   `docs/e2e-statistical-delivery-contract.md`,
   `docs/prompts/translate-e2e-statistical-worker.md` y
   `docs/examples/e2e-statistical-parity.json`.
3. Obtén la lista de declaraciones actuales en
   `tests/integration/e2e/cases/**/*.yaml`, identificadas por `audit_id::id`.
   Usa el cargador de `tests/integration/e2e/corpus.py` o lectura YAML segura.
   No ejecutes combate ni generes conocimiento para enumerarlas.
4. Ordena por identificador y construye una cola única. Por cada caso, la clave
   es `e2e/<audit_id>/<id>` y el archivo de entrega es
   `tests/engines/fixtures/e2e-statistical-deliveries/<sha256(case_key UTF-8)>.json`.
5. Revisa entregas existentes: solo excluye de la cola las válidas, con identidad
   y huella del YAML actual coincidentes. No sobrescribas entregas inválidas o
   antiguas: informa de ellas como pendientes de sustitución autorizada.
   Un bloqueo previo sigue cerrado mientras no cambien su origen ni las
   condiciones que lo causaron; no lo redistribuyas indefinidamente.

## Reparto y paralelismo

- Forma tandas de 10 CASOS. Cada subagente recibe exactamente un caso y escribe
  únicamente su JSON. No repartas motores o archivos comunes entre trabajadores.
- Lanza hasta 10 trabajadores simultáneos SOLO si la capacidad real lo permite.
  Respeta el límite de subagentes del entorno: con menos plazas, procesa la
  misma tanda en varias oleadas. No intentes superar límites con otros medios.
- Mantén el registro de asignaciones en tu contexto: identificador, trabajador,
  archivo exclusivo y estado. Nunca asignes el mismo caso a dos trabajadores.
- Reutiliza trabajadores disponibles para el siguiente caso. No les pases toda
  la conversación ni pidas que descubran el alcance desde otros chats.
- Si no hay herramienta de subagentes, informa de esa limitación; no crees chats
  ni procesos alternativos para simular delegación.

## Mensaje obligatorio a CADA trabajador

Envía un mensaje autosuficiente con:

1. Repositorio, rama y prohibición de acceder a REPO-REWORK.
2. `audit_id::id`, ruta exacta del YAML actual y `case_key` asignados.
3. Ruta exacta del ÚNICO JSON que puede escribir.
4. El texto completo de `docs/prompts/translate-e2e-statistical-worker.md`,
   sustituyendo `<audit_id::id>` por su asignación real.
5. Instrucción de leer el contrato y el ejemplo actuales desde disco; esas rutas
   están en el prompt. No sustituir el contrato por un resumen improvisado.
6. Criterio de finalización: JSON traducido y comprobado, o bloqueo/no
   aplicabilidad con motivo concreto. Informe breve con identidad, ruta, estado
   y comprobaciones. Sin campañas, cambios compartidos, commit ni push.

Si el trabajador está en otro checkout sin estos documentos, proporciónale
contrato, prompt y ejemplo completos junto con la asignación. Antes de empezar,
acuerda una ruta de entrega recuperable; no presupongas un disco compartido.

## Recogida de cada tanda

- Espera las respuestas sin sondeos continuos. Comunica avances útiles al usuario.
- Lee las entregas y verifica JSON, campos del contrato, identidad, ruta SHA-256,
  huella actual del YAML y, para `translated`, round-trip del codec y ausencia
  de tiradas/expectativas/parámetros de muestra. La conservación semántica de
  entradas debe estar respaldada por la comprobación del trabajador.
- No repitas compilaciones que ya tienen evidencia válida salvo cambio relevante
  o discrepancia. No ejecutes campañas estadísticas ni suites generales.
- Devuelve una entrega defectuosa al mismo trabajador con el defecto concreto.
  No modifiques simultáneamente su archivo. No vuelvas a lanzar un caso mientras
  su trabajador siga activo; confirma su terminación antes de reasignarlo.
- Clasifica las entregas como `translated`, `blocked`, `not-applicable` o error
  de entrega. No cuentes un error de exportación como rechazo de construcción
  demostrado. No confundas traducción con compatibilidad o paridad aprobada.
- Completa la tanda y continúa con la siguiente hasta agotar pendientes o llegar
  al límite del usuario. Conserva las entregas válidas para permitir reanudación.

## Límites de propiedad y decisiones

Los trabajadores solo escriben sus JSON. Tú coordinas y verificas; tampoco
modifiques motores, YAML, cargadores, formato, políticas, catálogo consolidado
ni manifest. Resolver soporte común de motores es otra tarea.

Los bloqueos previsibles se documentan por caso sin detener a los demás.
Si aparece el mismo bloqueo de infraestructura en varios casos, identifica la
causa común y suspende las asignaciones afectadas; continúa con las independientes.
No instales dependencias ni cambies el entorno compartido para sortearlo.
No preguntes por decisiones ya resueltas en el contrato. Pregunta únicamente si
falta información imprescindible; continúa mientras tanto el trabajo independiente.

## Respuesta final

Indica cantidades de traducidos, bloqueados, no aplicables, errores y pendientes;
ubicación de entregas; comprobaciones ejecutadas y causas comunes de bloqueo.
Aclara que no se han integrado ni certificado en paridad y que no hay commit/push.
No generes informes adicionales, registros compartidos ni documentación por caso.
