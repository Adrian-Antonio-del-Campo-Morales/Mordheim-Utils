"""Shared UI string catalogue for both applications.

Single sanctioned translation layer of the interface strings: widgets call
:func:`tr` with a stable English key, and every UI string is a member of
``STRINGS``. The shared theme stays string-free; ``ui`` areas must not define
their own lookup tables. Keys are the current English literals, so an
untranslated key renders exactly as before — a missing translation degrades
to English instead of crashing.

Translate at display time: shared data (``POST_BATTLE_STEPS``,
``POST_BATTLE_GROUPS``, KB names) keeps its canonical English form and every
widget applies ``tr`` when rendering.

Locale selection: :func:`set_locale` (``None`` defers to the
``MORDHEIM_LOCALE`` environment variable). Application entry points call it
once before widgets are built, together with
``mordheim_knowledge.i18n.set_locale`` for the KB display names — this layer
stays independent of ``mordheim_knowledge`` on purpose.

``STRINGS`` is grouped by application area (the campaign UI extraction order)
so a translator can review it screen by screen; every entry must carry an
``es`` value (``tests/python/ui/test_ui_i18n.py`` enforces it).

Spanish glossary (keep consistent across entries): warband=banda,
rating=valoración, state=estado, stash=reserva, hoard=acopio,
henchmen=secuaces, hired swords=espadas a sueldo, shards=fragmentos,
draft=borrador, roster=plantilla, treasury=tesorería, upkeep=manutención,
advance=mejora, skill=habilidad, spell=conjuro, Out of Action=Fuera de
combate, XP=PX, gc=gc, Trading Post=Puesto Comercial, KB=base de
conocimiento, models=miniaturas, battle=b, timeline=línea temporal.
"""
from __future__ import annotations

import os

CANONICAL_LOCALE = "en"
SUPPORTED_LOCALES = frozenset({"en", "es"})

_active_locale = CANONICAL_LOCALE

#: Interface strings by canonical English key. An ``es`` entry marks the
#: string as translated; add new strings here with their English key first.
STRINGS: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------
    # Shell & navigation (shell.py, campaign_view.py, timeline.py,
    # campaign_statistics.py)
    # ------------------------------------------------------------------
    "A WARBAND THROUGH TIME": {"es": "UNA BANDA A TRAVÉS DEL TIEMPO"},
    "MORDHEIM CAMPAIGN MANAGER": {"es": "GESTOR DE CAMPAÑAS DE MORDHEIM"},
    "CAMPAIGN": {"es": "CAMPAÑA"},
    "TIMELINE": {"es": "LÍNEA TEMPORAL"},
    "STATISTICS": {"es": "ESTADÍSTICAS"},
    "RULES": {"es": "REGLAS"},
    "SETTINGS": {"es": "AJUSTES"},
    "Save": {"es": "Guardar"},
    "Load": {"es": "Cargar"},
    "Undo": {"es": "Deshacer"},
    "Post-battle action": {"es": "Acción de postbatalla"},
    "Injury roll": {"es": "Tirada de heridas"},
    "Advance roll": {"es": "Tirada de mejora"},
    "Resolve advance": {"es": "Resolver mejora"},
    "Apply advance": {"es": "Aplicar mejora"},
    "Choose Hero skill lists": {"es": "Elegir listas de habilidades del héroe"},
    "Exploration roll": {"es": "Tirada de exploración"},
    "Exploration re-roll": {"es": "Repetición de exploración"},
    "Exploration event roll": {"es": "Tirada de evento de exploración"},
    "Resolve Exploration event": {"es": "Resolver evento de exploración"},
    "Discard Exploration die": {"es": "Descartar dado de exploración"},
    "Keep Exploration roll": {"es": "Conservar tirada de exploración"},
    "Veteran experience roll": {"es": "Tirada de experiencia de veteranos"},
    "Rare item search roll": {"es": "Tirada de búsqueda de objeto raro"},
    "Dramatis search roll": {"es": "Tirada de búsqueda de Dramatis"},
    "Buy rare item": {"es": "Comprar objeto raro"},
    "Assign scenario spell reward": {"es": "Asignar recompensa de conjuro"},
    "Pre-battle injury check": {"es": "Chequeo de herida previo a la batalla"},
    "Record battle": {"es": "Registrar batalla"},
    "Hire warrior": {"es": "Contratar guerrero"},
    "Hire Hired Sword": {"es": "Contratar espada a sueldo"},
    "Dismiss warrior": {"es": "Despedir guerrero"},
    "Rename warrior": {"es": "Cambiar nombre del guerrero"},
    "Resize henchman group": {"es": "Cambiar tamaño del grupo de secuaces"},
    "Move equipment": {"es": "Mover equipo"},
    "Transfer equipment": {"es": "Transferir equipo"},
    "Change equipment": {"es": "Modificar equipo"},
    "Buy equipment": {"es": "Comprar equipo"},
    "Change stash": {"es": "Modificar reserva"},
    "Buy item": {"es": "Comprar objeto"},
    "Correct resources": {"es": "Corregir recursos"},
    "Correct inventory": {"es": "Corregir inventario"},
    "Correct skills": {"es": "Corregir habilidades"},
    "Change mercenary variant": {"es": "Cambiar variante mercenaria"},
    "Commit duplicate spell": {"es": "Confirmar conjuro repetido"},
    "Commit spell": {"es": "Confirmar conjuro"},
    "Commit skill": {"es": "Confirmar habilidad"},
    "Dice": {"es": "Dados"},
    "Dice: {}": {"es": "Dados: {}"},
    "No detailed injury rolls were recorded.": {"es": "No se registraron tiradas de heridas detalladas."},
    "No detailed exploration result was recorded.": {"es": "No se registró un resultado detallado de exploración."},
    "No veteran roll was recorded.": {"es": "No se registró una tirada de veteranos."},
    "No searches were recorded.": {"es": "No se registraron búsquedas."},
    "No recruitment changes were recorded.": {"es": "No se registraron cambios de reclutamiento."},
    "No equipment transactions were recorded.": {"es": "No se registraron operaciones de equipo."},
    "Export": {"es": "Exportar"},
    "New Campaign…": {"es": "Nueva campaña…"},
    "Manage Campaigns…": {"es": "Gestionar campañas…"},
    "Open campaign example": {"es": "Abrir ejemplo de campaña"},
    "Open creation example": {"es": "Abrir ejemplo de creación"},
    "CAMPAIGN TIMELINE": {"es": "LÍNEA TEMPORAL DE LA CAMPAÑA"},
    "CONFIRM": {"es": "CONFIRMAR"},
    "ADD BATTLE": {"es": "AÑADIR BATALLA"},
    "CONTINUE": {"es": "CONTINUAR"},
    "BATTLE #{}  ·  IN PROGRESS": {"es": "BATALLA #{}  ·  EN CURSO"},
    "Record the battle results to continue": {"es": "Registra el resultado de la batalla para continuar"},
    "RESULTS": {"es": "RESULTADOS"},
    "SCENARIO-SPECIFIC RESULTS": {"es": "RESULTADOS ESPECÍFICOS DEL ESCENARIO"},
    "Objectives, casualties caused and scenario rewards will appear here when their rules are available as structured data.": {
        "es": "Los objetivos, las bajas causadas y las recompensas del escenario aparecerán aquí cuando sus reglas estén disponibles como datos estructurados."
    },
    "EXPERIENCE ADJUSTMENT": {"es": "AJUSTE DE EXPERIENCIA"},
    "temporary manual value until scenario rewards are calculated automatically": {
        "es": "valor manual provisional hasta que las recompensas del escenario se calculen automáticamente"
    },
    "‹ BACK": {"es": "‹ ATRÁS"},
    "CONTINUE ›": {"es": "CONTINUAR ›"},
    "of {} models": {"es": "de {} miniaturas"},
    "Henchmen casualty {} of {} · D6 survival roll": {"es": "Baja de secuaz {} de {} · tirada de supervivencia D6"},
    "Rename…": {"es": "Cambiar nombre…"},
    "Rename": {"es": "Cambiar nombre"},
    "New name": {"es": "Nuevo nombre"},
    "Cannot rename": {"es": "No se puede cambiar el nombre"},
    "Name warrior or group": {"es": "Nombrar guerrero o grupo"},
    "Name": {"es": "Nombre"},
    "Incomplete step": {"es": "Paso incompleto"},
    "Resolve every injury roll before continuing.": {"es": "Resuelve todas las tiradas de heridas antes de continuar."},
    "Resolve the exploration roll before continuing.": {"es": "Resuelve la tirada de exploración antes de continuar."},
    "Resolve the veteran roll before continuing.": {"es": "Resuelve la tirada de veteranos antes de continuar."},
    "Cannot apply result": {"es": "No se puede aplicar el resultado"},
    "Resolve every assigned search before continuing.": {"es": "Resuelve todas las búsquedas asignadas antes de continuar."},
    "Assign each available Hero to one rare item or Dramatis search. A Hero can perform at most one search in this sequence. {}": {
        "es": "Asigna cada héroe disponible a la búsqueda de un objeto raro o Dramatis. Cada héroe puede realizar como máximo una búsqueda en esta secuencia. {}"
    },
    "HERO SEARCH ASSIGNMENTS": {"es": "ASIGNACIONES DE BÚSQUEDA DE HÉROES"},
    "No search": {"es": "No buscar"},
    "RARE ITEM": {"es": "OBJETO RARO"},
    "No Heroes are currently available to search.": {"es": "No hay héroes disponibles para realizar búsquedas."},
    "{} searches for a Rare {} item": {"es": "{} busca un objeto de rareza {}"},
    "{} searches for this Dramatis Persona": {"es": "{} busca a este Dramatis Personae"},
    "BATTLE #{} · RESULTS": {"es": "BATALLA #{} · RESULTADOS"},
    "Scenario": {"es": "Escenario"},
    "Results": {"es": "Resultados"},
    "Battle setup": {"es": "Preparación"},
    "Battle outcome": {"es": "Resultado"},
    "CAMPAIGN STATISTICS": {"es": "ESTADÍSTICAS DE LA CAMPAÑA"},
    "RATING PROGRESSION": {"es": "PROGRESIÓN DE LA VALORACIÓN"},
    "Battles": {"es": "Batallas"},
    "Victories": {"es": "Victorias"},
    "Current rating": {"es": "Valoración actual"},
    "Current models": {"es": "Miniaturas actuales"},
    "Campaign-first workspace: timeline at left, selected moment at right.": {
        "es": "Espacio de trabajo centrado en la campaña: línea temporal a la izquierda, momento seleccionado a la derecha."
    },
    "Aggregates live outside the sequence; the Timeline remains the default way to understand what happened and when.": {
        "es": "Los agregados viven fuera de la secuencia; la Línea Temporal sigue siendo la forma por defecto de entender qué pasó y cuándo."
    },
    "Campaign has not started yet": {"es": "La campaña aún no ha comenzado"},
    "Campaign {} error": {"es": "Error de campaña {}"},
    "MERCENARY VARIANT": {"es": "VARIANTE MERCENARIO"},
    "CURRENT  ·  Rating {}  ·  {}/{} models  ·  {} gc": {
        "es": "ACTUAL  ·  Valoración {}  ·  {}/{} miniaturas  ·  {} gc"
    },
    "DRAFT  ·  {} gc  ·  Rating {}  ·  {}/{} models": {
        "es": "BORRADOR  ·  {} gc  ·  Valoración {}  ·  {}/{} miniaturas"
    },
    "RESUME POST-BATTLE #{}": {"es": "REANUDAR POSTBATALLA #{}"},
    "+ NEW BATTLE": {"es": "+ NUEVA BATALLA"},
    "NEXT · RECORD BATTLE": {"es": "SIGUIENTE · REGISTRAR BATALLA"},
    "NEXT · START CAMPAIGN": {"es": "SIGUIENTE · INICIAR CAMPAÑA"},
    "{}  ·  {}  ·  started {}": {"es": "{}  ·  {}  ·  iniciada {}"},
    # ------------------------------------------------------------------
    # Timeline nodes & states (timeline.py, state_moment.py)
    # ------------------------------------------------------------------
    "INITIAL STATE": {"es": "ESTADO INICIAL"},
    "INITIAL WARBAND": {"es": "BANDA INICIAL"},
    "INITIAL WARBAND  ·  DRAFT": {"es": "BANDA INICIAL  ·  BORRADOR"},
    "DRAFT": {"es": "BORRADOR"},
    "Created when the draft is committed": {"es": "Se crea al confirmar el borrador"},
    "CURRENT WARBAND": {"es": "BANDA ACTUAL"},
    "BATTLE #": {"es": "BATALLA #"},
    "BATTLE #{}": {"es": "BATALLA #{}"},
    "BATTLE #{}  ·  {}": {"es": "BATALLA #{}  ·  {}"},
    "STATE #": {"es": "ESTADO #"},
    "STATE #{}": {"es": "ESTADO #{}"},
    "POST-BATTLE #": {"es": "POSTBATALLA #"},
    "POST-BATTLE #{}": {"es": "POSTBATALLA #{}"},
    "POST-BATTLE #{}  ·  COMPLETE": {"es": "POSTBATALLA #{}  ·  COMPLETADA"},
    "POST-BATTLE #{}  ·  IN PROGRESS": {"es": "POSTBATALLA #{}  ·  EN CURSO"},
    "  ·  Battle #{} resolving": {"es": "  ·  Batalla #{} en resolución"},
    "Rating {}  ·  {}/{} models": {"es": "Valoración {}  ·  {}/{} miniaturas"},
    "{}/{} models  ·  {} gc remaining": {"es": "{}/{} miniaturas  ·  {} gc restantes"},
    "Step {}/8  ·  {}": {"es": "Paso {}/8  ·  {}"},
    "Final Review": {"es": "Revisión Final"},
    "FINAL REVIEW  ›": {"es": "REVISIÓN FINAL  ›"},
    "Recovery · Exploration & Income · Searches · Warband": {
        "es": "Recuperación · Exploración e Ingresos · Búsquedas · Banda"
    },
    "Scenario · opponent · result · XP and casualties": {
        "es": "Escenario · rival · resultado · PX y bajas"
    },
    "{} completed battle states": {"es": "{} estados de batalla completados"},
    "NEXT STATE PENDING · finish Post-Battle #{}": {
        "es": "ESTADO SIGUIENTE PENDIENTE · termina la Postbatalla #{}"
    },
    "Dashed future node opening the Record Battle dialog.": {
        "es": "Nodo futuro discontinuo que abre el diálogo de Registrar Batalla."
    },
    "HISTORICAL · READ ONLY": {"es": "HISTÓRICO · SOLO LECTURA"},
    "CAMPAIGN POSITION": {"es": "POSICIÓN EN LA CAMPAÑA"},
    "Campaign starting point": {"es": "Punto de partida de la campaña"},
    "WARBAND AT THIS POINT": {"es": "BANDA EN ESTE PUNTO"},
    "WARBAND STATE #{}": {"es": "ESTADO DE BANDA #{}"},
    "THIS STATE IN THE TIMELINE": {"es": "ESTE ESTADO EN LA LÍNEA TEMPORAL"},
    "‹ PREVIOUS STATE": {"es": "‹ ESTADO ANTERIOR"},
    "‹ STATE #{}": {"es": "‹ ESTADO #{}"},
    "STATE #{} ›": {"es": "ESTADO #{} ›"},
    "NEXT STATE ›": {"es": "ESTADO SIGUIENTE ›"},
    "VIEW POST-BATTLE #{}": {"es": "VER POSTBATALLA #{}"},
    "No pending actions.": {"es": "No hay acciones pendientes."},
    "Post-battle is at step {}/8. State #{} does not exist yet.": {
        "es": "La posbatalla está en el paso {}/8. El Estado #{} aún no existe."
    },
    "Select the Post-Battle #8 node in the timeline, or use the Resume action above.": {
        "es": "Selecciona el nodo de Postbatalla #8 en la línea temporal, o usa la acción Reanudar de arriba."
    },
    "Read or edit one immutable/active warband state from the timeline.": {
        "es": "Lee o edita un estado de banda inmutable/activo desde la línea temporal."
    },
    "This is the immutable starting point from which the campaign begins.": {
        "es": "Este es el punto de partida inmutable desde el que comienza la campaña."
    },
    "This snapshot was created when Post-Battle #{} was committed. Open the adjacent transition nodes to see why the warband changed.": {
        "es": "Esta instantánea se creó cuando se confirmó la Postbatalla #{}. Abre los nodos de transición adyacentes para ver por qué cambió la banda."
    },
    "Total experience": {"es": "Experiencia total"},
    "Treasury": {"es": "Tesorería"},
    "Rating": {"es": "Valoración"},
    "Models": {"es": "Miniaturas"},
    "WARRIORS": {"es": "GUERREROS"},
    "Heroes": {"es": "Héroes"},
    "Henchmen": {"es": "Secuaces"},
    "INVENTORY": {"es": "INVENTARIO"},
    "OVERVIEW": {"es": "RESUMEN"},
    "Warband rating": {"es": "Valoración de la banda"},
    "Battle #{} is complete": {"es": "La batalla #{} está completa"},
    "After Battle #{} · {}": {"es": "Tras la batalla #{} · {}"},
    "{} · vs. {} · {}": {"es": "{} · contra {} · {}"},
    " models": {"es": " miniaturas"},
    " models  ·  ": {"es": " miniaturas  ·  "},
    # ------------------------------------------------------------------
    # Battle record (battle_moment.py, record_battle.py)
    # ------------------------------------------------------------------
    "Battle #": {"es": "Batalla #"},
    "WHAT HAPPENED ON THE TABLE": {"es": "QUÉ PASÓ EN LA MESA"},
    "One table battle: facts only, separated from post-battle consequences.": {
        "es": "Una batalla en la mesa: solo hechos, separados de las consecuencias de posbatalla."
    },
    "Battle records contain table facts only. Injury rolls, experience, exploration and trading belong to the Post-Battle node that follows this battle.": {
        "es": "Los registros de batalla contienen solo hechos de mesa. Las tiradas de heridas, la experiencia, la exploración y el comercio pertenecen al nodo de Postbatalla que sigue a esta batalla."
    },
    "Record Battle": {"es": "Registrar batalla"},
    "RECORD BATTLE": {"es": "REGISTRAR BATALLA"},
    "RECORD & RESOLVE": {"es": "REGISTRAR Y RESOLVER"},
    "Record the table facts of a played battle. The post-battle sequence that follows applies injuries, experience, exploration and trading.": {
        "es": "Registra los hechos de mesa de una batalla jugada. La secuencia de posbatalla que sigue aplica heridas, experiencia, exploración y comercio."
    },
    "PARTICIPANTS": {"es": "PARTICIPANTES"},
    "SCENARIO": {"es": "ESCENARIO"},
    "(no scenarios)": {"es": "(sin escenarios)"},
    "(optional)": {"es": "(opcional)"},
    "OPPONENT": {"es": "RIVAL"},
    "OPPONENT RATING": {"es": "VALORACIÓN DEL RIVAL"},
    "Opponent rating": {"es": "Valoración del rival"},
    "RESULT": {"es": "RESULTADO"},
    "Result": {"es": "Resultado"},
    "Victory": {"es": "Victoria"},
    "Defeat": {"es": "Derrota"},
    "Draw": {"es": "Empate"},
    "EXPERIENCE": {"es": "EXPERIENCIA"},
    "Casualties": {"es": "Bajas"},
    "Participated": {"es": "Participó"},
    "Models deployed": {"es": "Miniaturas desplegadas"},
    "OUT OF ACTION": {"es": "FUERA DE COMBATE"},
    "Out of Action / casualties recorded: {}": {
        "es": "Fuera de combate / bajas registradas: {}"
    },
    "{} models deployed · {} Out of Action. Which warriors went Out of Action is resolved in Recovery (post-battle step 1).": {
        "es": "{} miniaturas desplegadas · {} Fuera de combate. Qué guerreros quedaron Fuera de combate se resuelve en Recuperación (paso 1 de posbatalla)."
    },
    "BATTLE NOTES": {"es": "NOTAS DE BATALLA"},
    "NOTES": {"es": "NOTAS"},
    "No notes were recorded for this battle.": {
        "es": "No se registraron notas para esta batalla."
    },
    "Checklist of warriors recorded Out of Action (drives Recovery).": {
        "es": "Lista de guerreros registrados Fuera de combate (alimenta Recuperación)."
    },
    "Marked warriors roll on the serious-injury charts in Recovery (post-battle step 1). Henchman groups: ticking marks the whole group's survival roll.": {
        "es": "Los guerreros marcados tiran en las tablas de heridas graves en Recuperación (paso 1 de posbatalla). Grupos de secuaces: marcar la casilla representa la tirada de supervivencia de todo el grupo."
    },
    "total XP granted to each surviving warrior": {
        "es": "PX total concedido a cada guerrero superviviente"
    },
    "{} warrior(s) recorded Out of Action": {
        "es": "{} guerrero(s) registrado(s) Fuera de combate"
    },
    "Cannot record battle": {"es": "No se puede registrar la batalla"},
    "EXTRA REWARDS": {"es": "RECOMPENSAS EXTRA"},
    "Optional rewards granted by house rules or the campaign organiser.": {
        "es": "Recompensas opcionales concedidas por reglas de la casa o por el organizador de la campaña."
    },
    "GOLD CROWNS": {"es": "CORONAS DE ORO"},
    "WYRDSTONE": {"es": "PIEDRA BRUJA"},
    "ADD": {"es": "AÑADIR"},
    "REMOVE": {"es": "QUITAR"},
    # ------------------------------------------------------------------
    # Post-battle sequence chrome (post_battle_moment.py, post_battle_sequence.py)
    # ------------------------------------------------------------------
    "POST-BATTLE": {"es": "POSTBATALLA"},
    "Compact state marker used inside one post-battle chapter.": {
        "es": "Marcador de estado compacto usado dentro de un capítulo de posbatalla."
    },
    "THE TRANSITION": {"es": "LA TRANSICIÓN"},
    "Complete · transformed State #{} into State #{}": {
        "es": "Completa · transformó el Estado #{} en el Estado #{}"
    },
    " · APPLIED": {"es": " · APLICADO"},
    " · COMMITTED: {}": {"es": " · CONFIRMADO: {}"},
    " · Upkeep {}": {"es": " · Manutención {}"},
    " · rolled {}": {"es": " · tiró {}"},
    "RESOLVE ROLL": {"es": "RESOLVER TIRADA"},
    "Roll in app or enter physical dice": {"es": "Tirar en la app o introducir dados físicos"},
    "APPLY TO ROSTER": {"es": "APLICAR A LA PLANTILLA"},
    "SAVE & CLOSE": {"es": "GUARDAR Y CERRAR"},
    "COMMIT STATE #{}": {"es": "CONFIRMAR ESTADO #{}"},
    "All eight player actions are complete. This confirmation creates State #{}; warband rating is calculated automatically from the final roster. {}": {
        "es": "Las ocho acciones del jugador están completas. Esta confirmación crea el Estado #{}; la valoración de la banda se calcula automáticamente a partir de la plantilla final. {}"
    },
    "CONTINUE TO FINAL REVIEW  ›": {"es": "CONTINUAR A LA REVISIÓN FINAL  ›"},
    "Saves the campaign (with the pending post-battle) and returns to the current state.": {
        "es": "Guarda la campaña (con la posbatalla pendiente) y vuelve al estado actual."
    },
    "Rebuilds the current step in place, preserving scroll position.": {
        "es": "Reconstruye el paso actual en el sitio, conservando la posición de desplazamiento."
    },
    "Runs one engine action; reports and rebuilds on success.": {
        "es": "Ejecuta una acción del motor; informa y reconstruye si tiene éxito."
    },
    "KB provenance line (sequence step ids + resolved catalogue files).": {
        "es": "Línea de procedencia de la base de conocimiento (ids de los pasos de la secuencia + ficheros de catálogo resueltos)."
    },
    "KB source: {} — resolves {}": {
        "es": "Fuente de la base de conocimiento: {} — resuelve {}"
    },
    "OK": {"es": "Aceptar"},
    "Done": {"es": "Hecho"},
    "Removed": {"es": "Quitado"},
    "Pending pick": {"es": "Elección pendiente"},
    "once per sequence": {"es": "una vez por secuencia"},
    "choose below": {"es": "elegir abajo"},
    "None": {"es": "Ninguno"},
    "Not found": {"es": "No encontrado"},
    "XP {}": {"es": "PX {}"},
    " XP": {"es": " PX"},
    "+1 XP": {"es": "+1 PX"},
    "{} XP available": {"es": "{} PX disponibles"},
    "{} equipped": {"es": "{} equipado"},
    "{} · Rare {} · {}": {"es": "{} · Raro {} · {}"},
    "{} items": {"es": "{} objetos"},
    "{} shards": {"es": "{} fragmentos"},
    "{} remaining": {"es": "{} restantes"},
    "Prototype": {"es": "Prototipo"},
    "This control is visual-only in the interface prototype.": {
        "es": "Este control es solo visual en el prototipo de interfaz."
    },
    # ------------------------------------------------------------------
    # Step 01 · Recovery / injuries
    # ------------------------------------------------------------------
    "01 · Injuries": {"es": "01 · Heridas"},
    "{} warrior(s) were recorded Out of Action in the battle record": {
        "es": "{} guerrero(s) fueron registrados Fuera de combate en el registro de batalla"
    },
    "No warrior was recorded Out of Action: proceed to Experience.": {
        "es": "Ningún guerrero fue registrado Fuera de combate: pasa a Experiencia."
    },
    "{}. Resolve each against the KB serious-injury charts: each roll starts unresolved; resolving then applying it mutates the roster. {}": {
        "es": "{}. Resuelve cada una contra las tablas de heridas graves de la base de conocimiento: cada tirada empieza sin resolver; resolverla y aplicarla muta la plantilla. {}"
    },
    "No per-warrior record exists for this battle; every warrior is offered": {
        "es": "No existe registro por guerrero para esta batalla; se ofrece cada guerrero"
    },
    "Injuries applied": {"es": "Heridas aplicadas"},
    "Multiple Injuries": {"es": "Heridas múltiples"},
    "Dead": {"es": "Muerto"},
    "No lasting effect.": {"es": "Sin efecto permanente."},
    "Henchmen group · {} member{} · D6 survival roll": {
        "es": "Grupo de secuaces · {} miembro(s) · tirada de supervivencia D6"
    },
    "Henchmen group · {} member · D6 survival roll": {
        "es": "Grupo de secuaces · {} miembro · tirada de supervivencia D6"
    },
    "Hero · Out of Action · D66 serious injury roll": {
        "es": "Héroe · Fuera de combate · tirada de herida grave D66"
    },
    "Live KB resolution for an injury card's roll.": {
        "es": "Resolución en vivo de la base de conocimiento para la tirada de una carta de heridas."
    },
    " {} Champion": {"es": " {} Campeón"},
    " member": {"es": " miembro"},
    "+ 1 member": {"es": "+ 1 miembro"},
    "− 1 member": {"es": "− 1 miembro"},
    "{} · {} members": {"es": "{} · {} miembros"},
    "{} Champion": {"es": "{} Campeón"},
    # ------------------------------------------------------------------
    # Step 02 · Experience / advances
    # ------------------------------------------------------------------
    "02 · Experience": {"es": "02 · Experiencia"},
    "Allocate the experience Battle #{} granted (+{} XP). Crossed thresholds earn advance rolls resolved against the KB advancement tables; stat increases and skill/spell picks are committed here. {}": {
        "es": "Reparte la experiencia concedida por la Batalla #{} (+{} PX). Los umbrales cruzados dan tiradas de mejora que se resuelven contra las tablas de avance de la base de conocimiento; los aumentos de características y las elecciones de habilidad/conjuro se confirman aquí. {}"
    },
    "No warrior has crossed an experience threshold yet. Grant XP above; a threshold earns a 2D6 advance roll on the KB table (heroes: 20/40/65/90… · henchmen: 8/16/25/35…).": {
        "es": "Ningún guerrero ha cruzado aún un umbral de experiencia. Concede PX arriba; un umbral da una tirada de mejora de 2D6 en la tabla de la base de conocimiento (héroes: 20/40/65/90… · secuaces: 8/16/25/35…)."
    },
    "{} · crossed the {} XP threshold · 2D6 on the KB {} table": {
        "es": "{} · cruzó el umbral de {} PX · 2D6 en la tabla {} de la base de conocimiento"
    },
    "Advance roll": {"es": "Tirada de mejora"},
    "Advance resolved": {"es": "Mejora resuelta"},
    "Advance committed": {"es": "Mejora confirmada"},
    "Advances": {"es": "Mejoras"},
    "ADVANCE ROLLS EARNED THIS SEQUENCE": {
        "es": "TIRADAS DE MEJORA GANADAS EN ESTA SECUENCIA"
    },
    "The advance row {} needs a D6 sub-roll.": {
        "es": "La fila de mejora {} necesita una sub-tirada de D6."
    },
    "Resolved; choose the advance below.": {"es": "Resuelta; elige la mejora abajo."},
    "Choose the resulting advance.": {"es": "Elige la mejora resultante."},
    "Already known — pick a different entry.": {"es": "Ya conocida — elige otra entrada."},
    "VARIABLE PRICE": {"es": "PRECIO VARIABLE"},
    "COST ROLL": {"es": "TIRADA DE COSTE"},
    "Roll the declared cost dice; the total fixes the price.": {
        "es": "Tira los dados de coste declarados; el total fija el precio."
    },
    "Price resolved": {"es": "Precio resuelto"},
    "{} costs {} gc": {"es": "{} cuesta {} coronas"},
    "The buy uses the rolled total.": {"es": "La compra usa el total tirado."},
    "Cannot resolve": {"es": "No se puede resolver"},
    "The offer price could not be computed.": {"es": "No se pudo calcular el precio de la oferta."},
    "CLOSE": {"es": "CERRAR"},
    "UPGRADE PRICE": {"es": "PRECIO DE MEJORA"},
    "{}× the price of the base record it upgrades. Pick the record:": {
        "es": "{}× el precio del registro base que mejora. Elige el registro:"
    },
    "No owned records to upgrade. Buy the base item first.": {
        "es": "No hay registros propios que mejorar. Compra primero el objeto base."
    },
    "UPGRADE ({} gc)": {"es": "MEJORAR ({} coronas)"},
    "HIRING FEE ROLL": {"es": "TIRADA DE TARIFA DE CONTRATACIÓN"},
    "Hiring fee: {} + {}D{} gc": {"es": "Tarifa de contratación: {} + {}D{} coronas"},
    "FEE ROLL": {"es": "TIRADA DE TARIFA"},
    "Roll the fee dice; the engine adds the flat base.": {
        "es": "Tira los dados de la tarifa; el motor añade la base fija."
    },
    "Fee resolved": {"es": "Tarifa resuelta"},
    "The hire charges base + roll.": {"es": "La contratación cobra base + tirada."},
    "Total fee: {} gc": {"es": "Tarifa total: {} coronas"},
    "Already known — committing this pick records the duplicate: casting difficulty reduced by 1.": {
        "es": "Ya conocida — confirmar esta elección registra el duplicado: la dificultad de lanzamiento baja en 1."
    },
    "Already known — committing this pick records the duplicate: {}’s casting difficulty becomes {}.": {
        "es": "Ya conocida — confirmar esta elección registra el duplicado: la dificultad de lanzamiento de {} pasa a ser {}."
    },
    "This scenario declares no structured awards.": {
        "es": "Este escenario no declara premios estructurados."
    },
    "MANUAL ROW": {"es": "FILA MANUAL"},
    "XP": {"es": "PX"},
    "This result requires an effect or reroll outside the application. Reopen the advance and roll again once the roster is correct.": {
        "es": "Este resultado requiere un efecto o repesca fuera de la aplicación. Reabre la mejora y tira de nuevo cuando la lista esté correcta."
    },
    "REOPEN ADVANCE FOR REROLL": {"es": "REABRIR LA MEJORA PARA REPESCAR"},
    "Result resolved at the table; the advance reopens for a new roll.": {
        "es": "Resultado resuelto en la mesa; la mejora se reabre para una nueva tirada."
    },
    "Award rows are generated from the KB scenario plan (scenario_rewards); objectives that remain prose-only in the KB stay manual entries.": {
        "es": "Las filas de premio se generan del plan del escenario en la base de conocimiento; los objetivos que siguen en prosa se quedan como entradas manuales."
    },
    "Duplicated spell: {} (difficulty {})": {"es": "Hechizo duplicado: {} (dificultad {})"},
    "{} deepens {}: casting difficulty reduced by 1.": {
        "es": "{} profundiza {}: la dificultad de lanzamiento baja en 1."
    },
    "A group of one cannot split into a hero; reroll this advance instead.": {
        "es": "Un grupo de uno no puede dividirse en un héroe; vuelve a tirar esta mejora."
    },
    "THE LAD'S GOT TALENT…": {"es": "EL CHICO TIENE TALENTO…"},
    "The Lad's Got Talent": {"es": "El Chico Tiene Talento"},
    "Ask for the promoted member's name, then split the group (Lad's Got Talent).": {
        "es": "Pide el nombre del miembro promocionado y divide el grupo (El Chico Tiene Talento)."
    },
    "Name the member of {} who becomes a Hero.": {
        "es": "Nombra al miembro de {} que se convierte en Héroe."
    },
    "PROMOTE": {"es": "PROMOCIONAR"},
    "PROMOTION SKILL PICK": {"es": "ELECCIÓN DE HABILIDAD DE PROMOCIÓN"},
    "PICK PROMOTION SKILL ({} LEFT)…": {"es": "ELEGIR HABILIDAD DE PROMOCIÓN (QUEDAN {})…"},
    "Promotion Skill": {"es": "Habilidad de promoción"},
    "COMMIT A NEW SKILL": {"es": "CONFIRMAR UNA NUEVA HABILIDAD"},
    "COMMIT A NEW SPELL": {"es": "CONFIRMAR UN NUEVO CONJURO"},
    "CHOOSE SKILL…": {"es": "ELEGIR HABILIDAD…"},
    "GENERATE SPELL…": {"es": "GENERAR CONJURO…"},
    "  {}  ·  difficulty {}": {"es": "  {}  ·  dificultad {}"},
    "{} chooses one option of this advance. Known entries are listed but cannot be re-picked.": {
        "es": "{} elige una opción de esta mejora. Las entradas ya conocidas se listan pero no se pueden repetir."
    },
    "Experience total {} XP": {"es": "Experiencia total {} PX"},
    "Survived +1   ·   Scenario / objectives +1": {
        "es": "Supervivencia +1   ·   Escenario / objetivos +1"
    },
    # ------------------------------------------------------------------
    # Step 03 · Exploration & income / wyrdstone
    # ------------------------------------------------------------------
    "03 · Exploration": {"es": "03 · Exploración"},
    "Income": {"es": "Ingresos"},
    "Exploration Dice": {"es": "Dados de exploración"},
    "DIE {}": {"es": "DADO {}"},
    "Roll once for each eligible Hero, plus one die when the warband won. Shards come from the KB shard chart; matching dice open the KB special-result table. {}": {
        "es": "Tira una vez por cada Héroe apto, más un dado si la banda ganó. Los fragmentos salen de la tabla de fragmentos de la base de conocimiento; los dados coincidentes abren la tabla de resultados especiales de la base de conocimiento. {}"
    },
    "Resolve the roll to reveal the shard total.": {
        "es": "Resuelve la tirada para revelar el total de fragmentos."
    },
    "Exploration resolved · {} shard(s)": {"es": "Exploración resuelta · {} fragmento(s)"},
    "Exploration yielded {} wyrdstone shard(s) before income decisions.": {
        "es": "La exploración rindió {} fragmento(s) de Wyrdstone antes de las decisiones de ingresos."
    },
    "Wyrdstone shards": {"es": "Fragmentos de Wyrdstone"},
    "Shards found": {"es": "Fragmentos encontrados"},
    "Shards remaining": {"es": "Fragmentos restantes"},
    "Shards sold": {"es": "Fragmentos vendidos"},
    # ------------------------------------------------------------------
    # Step 04 · Sell Wyrdstone
    # ------------------------------------------------------------------
    "04 · Sell Wyrdstone": {"es": "04 · Vender Wyrdstone"},
    "Wyrdstone sale resolved once": {"es": "Venta de Wyrdstone resuelta una vez"},
    "Sale resolved": {"es": "Venta resuelta"},
    "Sell now": {"es": "Vender ahora"},
    "SELL": {"es": "VENDER"},
    "Buy and Sell": {"es": "Comprar y vender"},
    "BUY AND SELL": {"es": "COMPRAR Y VENDER"},
    " · free starting equipment": {"es": " · equipo inicial gratuito"},
    " · Hired Sword equipment": {"es": " · equipo de Espada de Alquiler"},
    "CLOSE COMBAT WEAPONS": {"es": "ARMAS DE COMBATE CUERPO A CUERPO"},
    "RANGED WEAPONS": {"es": "ARMAS A DISTANCIA"},
    "SHIELDS AND DEFENCES": {"es": "ESCUDOS Y DEFENSAS"},
    "MISCELLANEOUS EQUIPMENT": {"es": "EQUIPO DIVERSO"},
    "MATERIALS AND UPGRADES": {"es": "MATERIALES Y MEJORAS"},
    "TROLLHEIM EQUIPMENT": {"es": "EQUIPO DE TROLLHEIM"},
    "OTHER ITEMS": {"es": "OTROS OBJETOS"},
    "CALCULATE SALE": {"es": "CALCULAR VENTA"},
    "Choose quantity to sell": {"es": "Elige la cantidad a vender"},
    "Choose how many shards to sell. This action can only be performed once in the post-battle sequence; the sale value comes from the KB pricing table (warband size × shards sold). {}": {
        "es": "Elige cuántos fragmentos vender. Esta acción solo puede realizarse una vez en la secuencia de posbatalla; el valor de venta proviene de la tabla de precios de la base de conocimiento (tamaño de banda × fragmentos vendidos). {}"
    },
    "Selling zero shards is allowed: it closes the once-per-sequence action.": {
        "es": "Se permite vender cero fragmentos: cierra la acción única por secuencia."
    },
    "The table value is calculated from the current warband size and the fragments sold.": {
        "es": "El valor de tabla se calcula a partir del tamaño actual de la banda y los fragmentos vendidos."
    },
    "KB pricing table": {"es": "Tabla de precios de la base de conocimiento"},
    "ADD SHARDS TO HOARD": {"es": "AÑADIR FRAGMENTOS AL ACOPIO"},
    "In hoard": {"es": "En el acopio"},
    "Total {} → {} wyrdstone shard(s)": {"es": "Total {} → {} fragmento(s) de Wyrdstone"},
    "⚠ The rarity test failed; the item is not available to buy.": {
        "es": "⚠ La tirada de rareza falló; el objeto no está disponible para comprar."
    },
    "⚠ This successful search has already been used.": {
        "es": "⚠ Esta búsqueda exitosa ya ha sido utilizada."
    },
    "Consumed": {"es": "Usado"},
    "Available": {"es": "Disponible"},
    "{} ({}) — {}": {"es": "{} ({}) — {}"},  # locale-neutral: identical in Spanish
    "⚠ This item has no flat price; purchases are not supported yet.": {
        "es": "⚠ Este objeto no tiene precio fijo; las compras aún no están soportadas."
    },
    # ------------------------------------------------------------------
    # Step 05/06 · Searches: rare items & Dramatis Personae
    # ------------------------------------------------------------------
    "05 · Available Veterans": {"es": "05 · Veteranos disponibles"},
    "06 · Rare Items & Dramatis": {"es": "06 · Objetos raros y Dramatis"},
    "A · RARE ITEMS": {"es": "A · OBJETOS RAROS"},
    "B · DRAMATIS PERSONAE": {"es": "B · PERSONAJES ESPECIALES"},
    "Rare item search": {"es": "Búsqueda de objetos raros"},
    "Rare item availability search": {"es": "Búsqueda de disponibilidad de objetos raros"},
    "Dramatis search": {"es": "Búsqueda de Dramatis"},
    "Dramatis Personae search": {"es": "Búsqueda de Dramatis Personae"},
    "One UI phase contains the two consecutive searches: first rare items, then Dramatis Personae. Eligible Heroes are a limited search resource. Offers come from the KB Trading Post and hiring catalogue. {}": {
        "es": "Una fase de la interfaz contiene las dos búsquedas consecutivas: primero objetos raros, luego Dramatis Personae. Los héroes aptos son un recurso de búsqueda limitado. Las ofertas provienen del Puesto Comercial y del catálogo de contratación de la base de conocimiento. {}"
    },
    "A successful search reveals a contextual Buy action · resolves the 2D6 rarity test against the KB availability of the selected item": {
        "es": "Una búsqueda exitosa revela una acción contextual de Comprar · resuelve la tirada de rareza de 2D6 contra la disponibilidad en la base de conocimiento del objeto seleccionado"
    },
    "Live KB rarity-test resolution for a rare-item search.": {
        "es": "Resolución en vivo de la tirada de rareza de la base de conocimiento para una búsqueda de objetos raros."
    },
    "Live KB resolution of an exploration roll.": {
        "es": "Resolución en vivo de la base de conocimiento para una tirada de exploración."
    },
    "One D6 per searcher · a result under the Hero's Initiative locates the character": {
        "es": "Un D6 por buscador · un resultado por debajo de la Iniciativa del Héroe localiza al personaje"
    },
    "Eligible Heroes: {} · {}D6 from the KB allocation": {
        "es": "Héroes aptos: {} · {}D6 según la asignación de la base de conocimiento"
    },
    "Resolve the roll to locate the character. For conditional entries the acceptance roll reuses the same die.": {
        "es": "Resuelve la tirada para localizar al personaje. En las entradas condicionales, la tirada de aceptación reutiliza el mismo dado."
    },
    "Resolve the roll to test the selected item.": {
        "es": "Resuelve la tirada para probar el objeto seleccionado."
    },
    "Character found · hiring remains optional": {
        "es": "Personaje encontrado · contratarlo sigue siendo opcional"
    },
    "Located": {"es": "Encontrado"},
    "Choose a rare item": {"es": "Elige un objeto raro"},
    "Choose a special character": {"es": "Elige un personaje especial"},
    "{} rare Trading Post items are available to this warband. Assign an eligible Hero to search for one specific item; successful purchases go to the stash.": {
        "es": "{} objetos raros del Puesto Comercial están disponibles para esta banda. Asigna un Héroe apto para buscar un objeto concreto; las compras exitosas van a la reserva."
    },
    "{} rare entries in the KB trading post (showing {}).": {
        "es": "{} entradas raras en el Puesto Comercial de la base de conocimiento (mostrando {})."
    },
    "No rare items from the Trading Post are available to this warband.": {
        "es": "Ningún objeto raro del Puesto Comercial está disponible para esta banda."
    },
    "No Dramatis Personae are currently searchable by this warband.": {
        "es": "Esta banda no puede buscar actualmente ningún Dramatis Personae."
    },
    "No Hired Swords are available to this warband.": {
        "es": "No hay Espadas a Sueldo disponibles para esta banda."
    },
    "Heroes assigned to this search are not available to look for rare items in the same sequence. Entries marked * depend on roster/variant conditions evaluated by the application.": {
        "es": "Los héroes asignados a esta búsqueda no pueden buscar objetos raros en la misma secuencia. Las entradas marcadas con * dependen de condiciones de plantilla/variante evaluadas por la aplicación."
    },
    "Rare items and Dramatis searches resolved": {
        "es": "Búsquedas de objetos raros y Dramatis resueltas"
    },
    "  ·  Hire {}": {"es": "  ·  Contratar {}"},
    "BUY & ADD TO STASH": {"es": "COMPRAR Y AÑADIR A LA RESERVA"},
    "BUY EQUIPMENT": {"es": "COMPRAR EQUIPAMIENTO"},
    "COMMON ITEMS": {"es": "OBJETOS COMUNES"},
    "Common equipment can be purchased without a rarity search (KB Trading Post).": {
        "es": "El equipamiento común se puede comprar sin búsqueda de rareza (Puesto Comercial de la base de conocimiento)."
    },
    "Common items can be bought here. Rare finds from Searches have already been resolved and, if purchased, are waiting in the stash below.": {
        "es": "Aquí se pueden comprar objetos comunes. Los hallazgos raros de las Búsquedas ya están resueltos y, si se compraron, esperan en la reserva de abajo."
    },
    "Purchases are added to the stash": {"es": "Las compras se añaden a la reserva"},
    "HIRED SWORDS": {"es": "ESPADAS A SUELDO"},
    # ------------------------------------------------------------------
    # Step 05 · Veteran experience pool
    # ------------------------------------------------------------------
    "Determine the post-battle experience pool available for hiring experienced recruits. You are not committing to hire anyone yet. {}": {
        "es": "Determina la bolsa de experiencia de posbatalla disponible para contratar reclutas con experiencia. Aún no estás comprometiendo a contratar a nadie. {}"
    },
    "Veteran Experience Pool": {"es": "Bolsa de experiencia de veteranos"},
    "Veteran pool of {} XP": {"es": "Bolsa de veteranos de {} PX"},
    "Veteran pool: {} XP": {"es": "Bolsa de veteranos: {} PX"},
    "SET VETERAN POOL": {"es": "FIJAR BOLSA DE VETERANOS"},
    "Pool rolled": {"es": "Bolsa calculada"},
    "Availability check before recruitment · current pool {} XP": {
        "es": "Comprobación de disponibilidad antes del reclutamiento · bolsa actual {} PX"
    },
    "This pool is used later in Recruitment": {
        "es": "Esta bolsa se usa más adelante en Reclutamiento"
    },
    # ------------------------------------------------------------------
    # Step 07 · Recruitment
    # ------------------------------------------------------------------
    "07 · Recruitment": {"es": "07 · Reclutamiento"},
    "Hire new warriors or Hired Swords and buy common items. This is the warband-building stage; rare-item searches are already closed. {}": {
        "es": "Contrata guerreros o Espadas a Sueldo nuevos y compra objetos comunes. Esta es la fase de construcción de la banda; las búsquedas de objetos raros ya están cerradas. {}"
    },
    "Hire available mercenaries and account for upkeep where applicable. * = acceptance roll or Mercenary-variant condition.": {
        "es": "Contrata mercenarios disponibles y contabiliza la manutención donde corresponda. * = tirada de aceptación o condición de variante Mercenario."
    },
    "Recruit new members or add to the roster (KB profiles, model and treasury limits enforced).": {
        "es": "Recluta nuevos miembros o añade a la plantilla (perfiles de la base de conocimiento, con límites de miniaturas y tesorería aplicados)."
    },
    "RECRUIT": {"es": "RECLUTAR"},
    "RECRUITMENT": {"es": "RECLUTAMIENTO"},
    "Recruitment complete": {"es": "Reclutamiento completado"},
    "Recruitment and equipment reallocation produced the final warband.": {
        "es": "El reclutamiento y la reasignación de equipo produjeron la banda final."
    },
    "HENCHMEN  {}": {"es": "SECUACES  {}"},
    "HEROES  {}/{}": {"es": "HÉROES  {}/{}"},
    # ------------------------------------------------------------------
    # Step 08 · Equipment / inventory / stash
    # ------------------------------------------------------------------
    "08 · Equipment": {"es": "08 · Equipamiento"},
    "Buy common equipment, then manage the complete band inventory from the stash. Items found or purchased earlier appear here before the next warband state is committed. {}": {
        "es": "Compra equipamiento común y gestiona después el inventario completo de la banda desde la reserva. Los objetos encontrados o comprados antes aparecen aquí antes de confirmar el siguiente estado de banda. {}"
    },
    "BAND INVENTORY": {"es": "INVENTARIO DE LA BANDA"},
    "EQUIPMENT BY WARRIOR": {"es": "EQUIPAMIENTO POR GUERRERO"},
    "CURRENTLY EQUIPPED": {"es": "EQUIPADO ACTUALMENTE"},
    "Owned {}  ·  Equipped {}  ·  Available {}": {
        "es": "En propiedad {}  ·  Equipado {}  ·  Disponible {}"
    },
    "OWNED": {"es": "EN PROPIEDAD"},
    "EQUIPPED": {"es": "EQUIPADO"},
    "AVAILABLE ACTION": {"es": "ACCIÓN DISPONIBLE"},
    "CARRIED BY THE WARBAND": {"es": "PORTADO POR LA BANDA"},
    "(item_id, display name) pairs carried by the warrior.": {
        "es": "Pares (item_id, nombre visible) que porta el guerrero."
    },
    "STASH": {"es": "RESERVA"},
    "STASH (UNASSIGNED)": {"es": "RESERVA (SIN ASIGNAR)"},
    "In stash": {"es": "En la reserva"},
    "The stash is empty.": {"es": "La reserva está vacía."},
    "MANAGE RESOURCES": {"es": "GESTIONAR RECURSOS"},
    "+ ADD ITEM": {"es": "+ AÑADIR OBJETO"},
    "ASSIGN": {"es": "ASIGNAR"},
    "ASSIGN…": {"es": "ASIGNAR…"},
    "Assign to…": {"es": "Asignar a…"},
    "Assign to which warrior?": {"es": "¿Asignar a qué guerrero?"},
    "Pick the warrior receiving the stash item.": {
        "es": "Elige el guerrero que recibe el objeto de la reserva."
    },
    "This item is not in the inventory ledger; only ledger items can move.": {
        "es": "Este objeto no está en el libro de inventario; solo los objetos del libro pueden moverse."
    },
    "Assign moves an available copy from the stash to a warrior. Sell uses half the stored value.": {
        "es": "Asignar mueve una copia disponible de la reserva a un guerrero. Vender usa la mitad del valor almacenado."
    },
    "Equipment reallocated": {"es": "Equipamiento reasignado"},
    "Equipment Editor": {"es": "Editor de equipamiento"},
    "Rebuild lists in place (the dialog edits live campaign state).": {
        "es": "Reconstruye las listas en el sitio (el diálogo edita el estado vivo de la campaña)."
    },
    "Reassign equipment between the roster and the stash. Nothing is bought or sold here; the warband total stays the same.": {
        "es": "Reasigna equipamiento entre la plantilla y la reserva. Aquí no se compra ni se vende; el total de la banda no cambia."
    },
    "Reassign equipment between the roster and the stash with the EQUIPMENT action above.": {
        "es": "Reasigna equipamiento entre la plantilla y la reserva con la acción EQUIPAMIENTO de arriba."
    },
    "No equipment": {"es": "Sin equipamiento"},
    "No current assignments": {"es": "Sin asignaciones actuales"},
    "Inventory": {"es": "Inventario"},
    "Inventory item": {"es": "Objeto del inventario"},
    "Search inventory…": {"es": "Buscar en el inventario…"},
    "ALL": {"es": "TODOS"},
    "BY ITEM": {"es": "POR OBJETO"},
    "BY WARRIOR": {"es": "POR GUERRERO"},
    "TYPE": {"es": "TIPO"},
    "ITEM": {"es": "OBJETO"},
    "QTY": {"es": "CANT."},
    "WEAPONS": {"es": "ARMAS"},
    "ARMOUR": {"es": "ARMADURA"},
    "CONSUMABLES": {"es": "CONSUMIBLES"},
    "MISC": {"es": "VARIOS"},
    "Gold crowns": {"es": "Coronas de oro"},
    "Gold Crowns": {"es": "Coronas de oro"},
    "Gold": {"es": "Oro"},
    # ------------------------------------------------------------------
    # Initial warband draft (initial_warband_draft.py, add_warrior.py,
    # warrior_card.py)
    # ------------------------------------------------------------------
    "Build the warband that will become the campaign's immutable starting state.": {
        "es": "Construye la banda que se convertirá en el estado inicial inmutable de la campaña."
    },
    "Initial warband draft": {"es": "Borrador de la banda inicial"},
    "START CAMPAIGN": {"es": "INICIAR CAMPAÑA"},
    "EDIT": {"es": "EDITAR"},
    "TREASURY": {"es": "TESORERÍA"},
    "MODELS": {"es": "MINIATURAS"},
    "MODELS IN GROUP": {"es": "MINIATURAS EN EL GRUPO"},
    "CHARACTERISTICS": {"es": "CARACTERÍSTICAS"},
    "SKILL ACCESS": {"es": "ACCESO A HABILIDADES"},
    "SKILLS / RULES": {"es": "HABILIDADES / REGLAS"},
    "Leader / hero present": {"es": "Líder / héroe presente"},
    "Modifiers: none": {"es": "Modificadores: ninguno"},
    "Modifiers: ": {"es": "Modificadores: "},
    "Within starting treasury": {"es": "Dentro de la tesorería inicial"},
    "Cost {} gc per model  ·  Starting XP {}  ·  {}": {
        "es": "Coste {} gc por miniatura  ·  PX iniciales {}  ·  {}"
    },
    "{}  ·  {} gc  ·  XP {}": {"es": "{}  ·  {} gc  ·  PX {}"},
    "no roster limit": {"es": "sin límite de plantilla"},
    "at most {} models": {"es": "como máximo {} miniaturas"},
    "Maximum quantity for a new row according to the roster limits.": {
        "es": "Cantidad máxima para una fila nueva según los límites de plantilla."
    },
    "No heroes yet": {"es": "Aún no hay héroes"},
    "No henchman groups yet": {"es": "Aún no hay grupos de secuaces"},
    "Add Hero": {"es": "Añadir héroe"},
    "Add Henchmen Group": {"es": "Añadir grupo de secuaces"},
    "ADD HERO": {"es": "AÑADIR HÉROE"},
    "ADD HENCHMEN GROUP": {"es": "AÑADIR GRUPO DE SECUACES"},
    "HIRE SWORD": {"es": "CONTRATAR ESPADA A SUELDO"},
    "ADD FIRST HERO": {"es": "AÑADIR PRIMER HÉROE"},
    "ADD FIRST GROUP": {"es": "AÑADIR PRIMER GRUPO"},
    "+ ADD HERO": {"es": "+ AÑADIR HÉROE"},
    "+ ADD HENCHMAN GROUP": {"es": "+ AÑADIR GRUPO DE SECUACES"},
    "+ ADD FIRST HERO": {"es": "+ AÑADIR PRIMER HÉROE"},
    "+ ADD FIRST GROUP": {"es": "+ AÑADIR PRIMER GRUPO"},
    "ADD TO DRAFT": {"es": "AÑADIR AL BORRADOR"},
    "Remove from draft": {"es": "Quitar del borrador"},
    "Row context menu: group size and draft removal.": {
        "es": "Menú contextual de fila: tamaño del grupo y salida del borrador."
    },
    "Pick a canonical profile from the warband roster to begin.": {
        "es": "Elige un perfil canónico de la plantilla de la banda para empezar."
    },
    "Choose a canonical profile from the warband roster.": {
        "es": "Elige un perfil canónico de la plantilla de la banda."
    },
    "Choose a group profile; the whole group shares one profile card.": {
        "es": "Elige un perfil de grupo; todo el grupo comparte una ficha de perfil."
    },
    "(no profiles available)": {"es": "(sin perfiles disponibles)"},
    "Rules: ": {"es": "Reglas: "},
    "Skill access: ": {"es": "Acceso a habilidades: "},
    "CLOSE": {"es": "CERRAR"},
    "Cancel": {"es": "Cancelar"},
    "Cannot add warrior": {"es": "No se puede añadir el guerrero"},
    "Cannot remove warrior": {"es": "No se puede quitar el guerrero"},
    "Cannot resize group": {"es": "No se puede redimensionar el grupo"},
    "Minimum {} models reached": {"es": "Mínimo de {} miniaturas alcanzado"},
    "Per-warrior equipment and skill editing arrives with the campaign rules engine.": {
        "es": "La edición de equipamiento y habilidades por guerrero llegará con el motor de reglas de campaña."
    },
    "EXP  {} → {}": {"es": "EXP  {} → {} PX"},
    "Hero": {"es": "Héroe"},
    # ------------------------------------------------------------------
    # Dice resolution (dice_resolution.py)
    # ------------------------------------------------------------------
    "HOW DO YOU WANT TO RESOLVE THIS ROLL?": {
        "es": "¿CÓMO QUIERES RESOLVER ESTA TIRADA?"
    },
    "🎲  ROLL IN APP": {"es": "🎲  TIRAR EN LA APP"},
    "ROLL IN APP": {"es": "TIRAR EN LA APP"},
    "ENTER MANUALLY": {"es": "INTRODUCIR MANUALMENTE"},
    "ENTER {} RESULT": {"es": "INTRODUCIR RESULTADO {}"},
    "CHANGE METHOD": {"es": "CAMBIAR MÉTODO"},
    "CHOOSE THE RESULT": {"es": "ELEGIR EL RESULTADO"},
    "USE RESULT": {"es": "USAR RESULTADO"},
    "ROLL AGAIN / EDIT": {"es": "VOLVER A TIRAR / EDITAR"},
    "Rolled in app": {"es": "Tirado en la app"},
    "Entered manually": {"es": "Introducido manualmente"},
    "You can use physical dice at the table and enter exactly what you rolled.": {
        "es": "Puedes usar dados físicos en la mesa e introducir exactamente lo que sacaste."
    },
    "Dice total": {"es": "Total de los dados"},
    "Wyrdstone from roll": {"es": "Piedra bruja de la tirada"},
    "EXPLORATION EVENT": {"es": "EVENTO DE EXPLORACIÓN"},
    "No matching-dice event was obtained.": {"es": "No se obtuvo ningún evento por dados coincidentes."},
    "No special event.": {"es": "Sin evento especial."},
    "Possible effects and rewards": {"es": "Posibles efectos y recompensas"},
    "Event resolved.": {"es": "Evento resuelto."},
    "Choose a Hero": {"es": "Elige un héroe"},
    "Gold crowns": {"es": "Coronas de oro"},
    "Gold crowns roll": {"es": "Tirada de coronas de oro"},
    "Wyrdstone roll": {"es": "Tirada de piedra bruja"},
    "Wyrdstone shards": {"es": "Fragmentos de piedra bruja"},
    "Experience": {"es": "Experiencia"},
    "Event result roll": {"es": "Tirada de resultado del evento"},
    "Toughness test": {"es": "Chequeo de Resistencia"},
    "Leadership test": {"es": "Chequeo de Liderazgo"},
    "{} quantity roll": {"es": "Tirada de cantidad de {}"},
    "Result recorded": {"es": "Resultado registrado"},
    # ------------------------------------------------------------------
    # Dialogs: new campaign (new_campaign.py)
    # ------------------------------------------------------------------
    "New Mordheim Campaign": {"es": "Nueva campaña de Mordheim"},
    "Create Campaign": {"es": "Crear campaña"},
    "CREATE CAMPAIGN": {"es": "CREAR CAMPAÑA"},
    "CAMPAIGN NAME": {"es": "NOMBRE DE LA CAMPAÑA"},
    "Start with the minimum information. The initial warband is built next.": {
        "es": "Empieza con la información mínima. La banda inicial se construye a continuación."
    },
    "{}–{} models · {} gc starting{} · {}": {
        "es": "{}–{} miniaturas · {} gc iniciales{} · {}"
    },
    # ------------------------------------------------------------------
    # File actions (file_actions.py)
    # ------------------------------------------------------------------
    "Load Mordheim campaign": {"es": "Cargar campaña de Mordheim"},
    "Save Mordheim campaign": {"es": "Guardar campaña de Mordheim"},
    "Save a copy of the Mordheim campaign": {"es": "Guardar una copia de la campaña de Mordheim"},
    "Export campaign summary": {"es": "Exportar resumen de campaña"},
    "Loads a saved campaign and makes it the active state.": {
        "es": "Carga una campaña guardada y la convierte en el estado activo."
    },
    "Saves the active campaign; asks for a path only the first time.": {
        "es": "Guarda la campaña activa; pide una ruta solo la primera vez."
    },
    "Saves the campaign to a user-chosen path (Save As / Export).": {
        "es": "Guarda la campaña en una ruta elegida por el usuario (Guardar como / Exportar)."
    },
    "Exports a readable Markdown summary of the current state.": {
        "es": "Exporta un resumen Markdown legible del estado actual."
    },
    "Export PDF": {"es": "Exportar PDF"},
    "Export warband PDF": {"es": "Exportar PDF de la banda"},
    "Exports the warband at the selected timeline moment as PDF.": {
        "es": "Exporta la banda en el momento seleccionado de la línea temporal como PDF."
    },
    "PDF": {"es": "PDF files"},
    # PDF roster sheet labels (persistence/warband_pdf.py); the Spanish
    # values follow the printed warband sheets.
    "Warband": {"es": "Banda"},
    "Roster": {"es": "Plantilla"},
    "Profile": {"es": "Perfil"},
    "Type": {"es": "Tipo"},
    "Cost": {"es": "Coste"},
    "XP": {"es": "PX"},
    "Condition": {"es": "Estado"},
    "Equipment": {"es": "Equipo"},
    "Rules": {"es": "Reglas"},
    "SEARCH": {"es": "BUSCAR"},
    "SOURCES": {"es": "FUENTES"},
    "No entries match the search.": {"es": "Ninguna entrada coincide con la búsqueda."},
    "This category has no entries.": {"es": "Esta categoría no tiene entradas."},
    "Select an entry to read its rules.": {"es": "Selecciona una entrada para leer sus reglas."},
    "No effect text is recorded for this entry.": {"es": "No hay texto de efecto registrado para esta entrada."},
    "Conditions": {"es": "Estados"},
    "Core Rules": {"es": "Reglas Básicas"},
    "Spells": {"es": "Hechizos"},
    "Serious Injuries": {"es": "Heridas Graves"},
    "Value": {"es": "Valor"},
    "Number": {"es": "NÚMERO"},
    "Warband name:": {"es": "NOMBRE DE LA BANDA:"},
    "Warband type:": {"es": "TIPO DE BANDA:"},
    "Treasure": {"es": "TESORO"},
    "Gold Crowns:": {"es": "Coronas de Oro:"},
    "Wyrdstone:": {"es": "Piedra Bruja:"},
    "Warband value": {"es": "VALOR DE LA BANDA"},
    "Total experience:": {"es": "Experiencia Total:"},
    "Members ( {} ) x 5:": {"es": "Miembros ( {} ) x 5:"},
    "Rating:": {"es": "Valor:"},
    "Stored equipment": {"es": "EQUIPO ALMACENADO"},
    "Notes": {"es": "NOTAS"},
    "No warriors recorded.": {"es": "No hay guerreros registrados."},
    "All files": {"es": "Todos los archivos"},
    "JSON": {"es": "JSON files"},
    "Markdown": {"es": "Markdown files"},
    "Text": {"es": "Texto"},
    # ------------------------------------------------------------------
    # Settings & rules placeholders (settings_view.py)
    # ------------------------------------------------------------------
    "Settings": {"es": "Ajustes"},
    "Appearance": {"es": "Apariencia"},
    "Language": {"es": "Idioma"},
    "English": {"es": "Inglés"},
    "Dark": {"es": "Oscuro"},
    "Ruleset": {"es": "Reglamento"},
    "Core / Official": {"es": "Núcleo / Oficial"},
    "Enabled sources": {"es": "Fuentes activadas"},
    "Mordheim core + enabled sources": {"es": "Núcleo Mordheim + fuentes activadas"},
    "Campaign Rules": {"es": "Reglas de campaña"},
    "Campaign preferences, ruleset selection and presentation options.": {
        "es": "Preferencias de campaña, selección de reglamento y opciones de presentación."
    },
    "Search and browse the Mordheim knowledge base without campaign-management clutter.": {
        "es": "Busca y explora la base de conocimiento de Mordheim sin el ruido de la gestión de campaña."
    },
    "Search rules, skills, equipment, scenarios…": {
        "es": "Buscar reglas, habilidades, equipamiento, escenarios…"
    },
    "Warbands": {"es": "Bandas"},
    "Scenarios": {"es": "Escenarios"},
    "Skills": {"es": "Habilidades"},
    "Special Rules": {"es": "Reglas Especiales"},
    "BROWSE": {"es": "EXPLORAR"},
    # ------------------------------------------------------------------
    # Post-battle sequence navigator (existing seed, mordheim_campaign.ui)
    # ------------------------------------------------------------------
    "8 / 8 ACTIONS COMPLETE": {"es": "8 / 8 ACCIONES COMPLETADAS"},
    "COMPLETE": {"es": "COMPLETADO"},
    "CONTINUE TO {}  ›": {"es": "CONTINUAR A {}  ›"},
    "CURRENT": {"es": "ACTUAL"},
    "CURRENT PHASE  ·  {}": {"es": "FASE ACTUAL  ·  {}"},
    "DONE": {"es": "HECHO"},
    "EQUIPMENT": {"es": "EQUIPAMIENTO"},
    "EXPLORATION & INCOME": {"es": "EXPLORACIÓN E INGRESOS"},
    "Experience": {"es": "Experiencia"},
    "Exploration": {"es": "Exploración"},
    "FINAL ACTION": {"es": "ACCIÓN FINAL"},
    "FINAL REVIEW": {"es": "REVISIÓN FINAL"},
    "FINAL REVIEW  ·  ALL 8 ACTIONS COMPLETE": {
        "es": "REVISIÓN FINAL  ·  LAS 8 ACCIONES COMPLETADAS"
    },
    "FINAL REVIEW IS AN APP CONFIRMATION, NOT AN ADDITIONAL POST-BATTLE RULE STEP": {
        "es": "LA REVISIÓN FINAL ES UNA CONFIRMACIÓN DE LA APLICACIÓN, NO UN PASO ADICIONAL DE POST-BATALLA"
    },
    "IN PROGRESS": {"es": "EN CURSO"},
    "Injuries": {"es": "Heridas"},
    "LOCKED": {"es": "BLOQUEADO"},
    "NEXT": {"es": "SIGUIENTE"},
    "Next: Commit new warband state": {"es": "Siguiente: confirmar el nuevo estado de la banda"},
    "Next: Final Review": {"es": "Siguiente: Revisión Final"},
    "Next: {}": {"es": "Siguiente: {}"},
    "Rare Items & Dramatis": {"es": "Objetos raros y Dramatis"},
    "RECOVERY": {"es": "RECUPERACIÓN"},
    "Recruitment": {"es": "Reclutamiento"},
    "SEARCHES": {"es": "BÚSQUEDAS"},
    "SELL WYRDSTONE": {"es": "VENDER WYRDSTONE"},
    "Sell Wyrdstone": {"es": "Vender wyrdstone"},
    "SEQUENCE COMPLETE": {"es": "SECUENCIA COMPLETA"},
    "STEP {} OF {}": {"es": "PASO {} DE {}"},
    "Veterans": {"es": "Veteranos"},
    "WARBAND": {"es": "BANDA"},
    "{} ACTIONS REMAIN": {"es": "{} ACCIONES PENDIENTES"},
}


# Additional UI literals introduced by campaign-library, manual-management,
# battle-check and post-battle follow-up screens.
STRINGS.update({
    "ACTIVE CAMPAIGN EFFECTS": {"es": "EFECTOS ACTIVOS DE CAMPAÑA"},
    "ADDITIONAL REWARDS": {"es": "RECOMPENSAS ADICIONALES"},
    "AVAILABLE ITEMS": {"es": "OBJETOS DISPONIBLES"},
    "AVAILABLE TO BUY": {"es": "DISPONIBLE PARA COMPRAR"},
    "Acceptance roll": {"es": "Tirada de aceptación"},
    "Add group member": {"es": "Añadir miembro al grupo"},
    "Add item": {"es": "Añadir objeto"},
    "Additional injuries": {"es": "Heridas adicionales"},
    "Advance applied": {"es": "Mejora aplicada"},
    "Advance needs attention": {"es": "La mejora requiere atención"},
    "Affected: {}.": {"es": "Afectado: {}."},
    "Already known — pick a different skill.": {"es": "Ya conocida; elige otra habilidad."},
    "Automatic": {"es": "Automático"},
    "BATTLE": {"es": "BATALLA"},
    "BATTLE #{} · PRE-BATTLE CHECKS": {"es": "BATALLA #{} · COMPROBACIONES PREVIAS"},
    "BROWSE…": {"es": "EXPLORAR…"},
    "BUY": {"es": "COMPRAR"},
    "CANCEL": {"es": "CANCELAR"},
    "CASUALTIES": {"es": "BAJAS"},
    "CATEGORY": {"es": "CATEGORÍA"},
    "CHOOSE FOLDER": {"es": "ELEGIR CARPETA"},
    "CONFIRM LISTS": {"es": "CONFIRMAR LISTAS"},
    "CURRENT ROSTER": {"es": "PLANTILLA ACTUAL"},
    "CURRENT STASH": {"es": "RESERVA ACTUAL"},
    "Campaign folder": {"es": "Carpeta de campaña"},
    "Campaign library": {"es": "Biblioteca de campañas"},
    "Campaign load error": {"es": "Error al cargar la campaña"},
    "Campaign points": {"es": "Puntos de campaña"},
    "Cannot add item": {"es": "No se puede añadir el objeto"},
    "Cannot apply correction": {"es": "No se puede aplicar la corrección"},
    "Cannot delete": {"es": "No se puede eliminar"},
    "Cannot edit skill": {"es": "No se puede editar la habilidad"},
    "Cannot hire Hired Sword": {"es": "No se puede contratar la espada a sueldo"},
    "Cannot move item": {"es": "No se puede mover el objeto"},
    "Cannot recruit": {"es": "No se puede reclutar"},
    "Check resolved": {"es": "Comprobación resuelta"},
    "Choose a skill": {"es": "Elegir una habilidad"},
    "Choose an outcome": {"es": "Elegir un resultado"},
    "Choose search target": {"es": "Elegir objetivo de búsqueda"},
    "Choose warriors": {"es": "Elegir guerreros"},
    "Confirm dismissal": {"es": "Confirmar expulsión"},
    "DELETE": {"es": "ELIMINAR"},
    "DESTROY": {"es": "DESTRUIR"},
    "DISCARD": {"es": "DESCARTAR"},
    "DISMISS": {"es": "EXPULSAR"},
    "Delete campaign": {"es": "Eliminar campaña"},
    "Dismiss 1 member": {"es": "Expulsar 1 miembro"},
    "Dismiss warrior / group": {"es": "Expulsar guerrero / grupo"},
    "Drag items between warriors and stash.": {"es": "Arrastra objetos entre guerreros y reserva."},
    "ENEMY OOA": {"es": "ENEMIGO FUERA DE COMBATE"},
    "EQUIPMENT OBLIGATIONS": {"es": "OBLIGACIONES DE EQUIPAMIENTO"},
    "EQUIPMENT PENDING": {"es": "EQUIPAMIENTO PENDIENTE"},
    "EVENT LOG": {"es": "REGISTRO DE EVENTOS"},
    "EXCHANGED": {"es": "INTERCAMBIADO"},
    "EXECUTED": {"es": "EJECUTADO"},
    "EXPLORATION": {"es": "EXPLORACIÓN"},
    "Edit skills": {"es": "Editar habilidades"},
    "Equipped": {"es": "Equipado"},
    "FINAL STATE": {"es": "ESTADO FINAL"},
    "Failed ({})": {"es": "Fallido ({})"},
    "Follow-up roll": {"es": "Tirada de seguimiento"},
    "HENCHMEN": {"es": "SECUACES"},
    "HEROES": {"es": "HÉROES"},
    "HIRE": {"es": "CONTRATAR"},
    "HIRE FEE": {"es": "TARIFA DE CONTRATACIÓN"},
    "HIRED SWORD": {"es": "ESPADA A SUELDO"},
    "Hiring fee": {"es": "Tarifa de contratación"},
    "INJURIES": {"es": "HERIDAS"},
    "Initial creation": {"es": "Creación inicial"},
    "Injury": {"es": "Herida"},
    "Invalid result": {"es": "Resultado no válido"},
    "KEEP ORIGINAL ROLL": {"es": "CONSERVAR TIRADA ORIGINAL"},
    "Manage resources": {"es": "Gestionar recursos"},
    "No Hired Swords yet": {"es": "Aún no hay espadas a sueldo"},
    "No matching campaigns.": {"es": "No hay campañas coincidentes."},
    "No recruits available": {"es": "No hay reclutas disponibles"},
    "OPEN": {"es": "ABRIR"},
    "Owned": {"es": "En propiedad"},
    "PAY UPKEEP": {"es": "PAGAR MANUTENCIÓN"},
    "PENDING FOLLOW-UPS": {"es": "SEGUIMIENTOS PENDIENTES"},
    "PURCHASED EQUIPMENT": {"es": "EQUIPAMIENTO COMPRADO"},
    "RESOLVE": {"es": "RESOLVER"},
    "RESOLVE ADVANCE": {"es": "RESOLVER MEJORA"},
    "RESOLVE…": {"es": "RESOLVER…"},
    "Roll again": {"es": "Volver a tirar"},
    "SCENARIO OBJECTIVES": {"es": "OBJETIVOS DEL ESCENARIO"},
    "SELECT": {"es": "SELECCIONAR"},
    "Serious injury roll": {"es": "Tirada de herida grave"},
    "Step completed": {"es": "Paso completado"},
    "UNAVAILABLE": {"es": "NO DISPONIBLE"},
    "UPKEEP": {"es": "MANUTENCIÓN"},
    "Unknown warrior": {"es": "Guerrero desconocido"},
    "Unresolved advance": {"es": "Mejora sin resolver"},
    "VETERAN EXPERIENCE": {"es": "EXPERIENCIA DE VETERANOS"},
    "WARBAND EQUIPMENT": {"es": "EQUIPAMIENTO DE LA BANDA"},
    "Wyrdstone": {"es": "Piedra bruja"},
    "battles": {"es": "batallas"},
    "from stash": {"es": "de la reserva"},
    "pending": {"es": "pendiente"},
    "roll": {"es": "tirada"},
})


# Remaining literal keys used by campaign dialogs and post-battle result cards.
# Keep these keys here, rather than translating ad hoc in widgets, so Spanish
# remains complete and the English locale stays byte-identical.
STRINGS.update({k: {"es": v} for k, v in {
    "+ HIRE SWORD": "+ CONTRATAR ESPADA A SUELDO", "ADD ITEM": "AÑADIR OBJETO", "ADD ITEM FROM KB": "AÑADIR OBJETO DE LA BASE DE CONOCIMIENTO", "APPLY": "APLICAR", "AVAILABILITY": "DISPONIBILIDAD", "AVAILABLE TO": "DISPONIBLE PARA", "Additional serious injury · {} remaining": "Herida grave adicional · quedan {}", "BATTLE #{} · PRE-BATTLE CHECKS": "BATALLA #{} · COMPROBACIONES PREVIAS", "Battle #{}": "Batalla #{}", "Battle result award: +{} XP": "Recompensa de batalla: +{} PX", "Bitter Enmity": "Enemistad amarga", "CAMPAIGN LIBRARY": "BIBLIOTECA DE CAMPAÑAS", "CATACOMBS RE-ROLL": "REPETICIÓN DE CATACUMBAS", "CONFIRM TABLE-SIDE RESOLUTION": "CONFIRMAR RESOLUCIÓN DE MESA", "Cannot read campaign: {} ": "No se puede leer la campaña: {} ", "Captured warrior": "Guerrero capturado", "Choose a Hero and exactly two spells.": "Elige un Héroe y exactamente dos conjuros.", "Choose exactly two Hero skill lists. These define future skill advances; they do not grant skills now.": "Elige exactamente dos listas de habilidades de Héroe. Definen futuras mejoras; no conceden habilidades ahora.", "Choose exactly two skill lists available to Heroes in this warband.": "Elige exactamente dos listas de habilidades disponibles para los Héroes de esta banda.", "Choose one die to discard before resolving Exploration.": "Elige un dado que descartar antes de resolver la Exploración.", "Did not participate · {}": "No participó · {}", "Dismiss {}? Transferable equipment will return to the stash; restricted starting equipment leaves with the recruit.": "¿Expulsar a {}? El equipo transferible volverá a la reserva; el equipo inicial restringido se va con el recluta.", "EDIT SKILLS — {}": "EDITAR HABILIDADES — {}", "Edit skills…": "Editar habilidades…", "Enter a valid file name.": "Introduce un nombre de archivo válido.", "Enter the specific hated target required by this result ({}):": "Introduce el objetivo odiado concreto requerido por este resultado ({}):", "Equip every newly recruited Henchman with the required matching equipment before continuing.": "Equipa a cada Secuaz recién reclutado con el equipo coincidente requerido antes de continuar.", "Equipment required in the next step:": "Equipo necesario en el siguiente paso:", "Estimated equipment purchases: {} gc": "Compras de equipo estimadas: {} gc", "Experience cost: {} gc": "Coste de experiencia: {} gc", "Exploration follow-up resolved.": "Seguimiento de Exploración resuelto.", "Finish the pending Exploration decision before continuing.": "Termina la decisión de Exploración pendiente antes de continuar.", "Finish the pending Exploration discard or re-roll decision before continuing.": "Termina la decisión pendiente de descartar o repetir la tirada antes de continuar.", "GC AWARDED": "GC CONCEDIDAS", "Gold crowns paid to the captor:": "Coronas de oro pagadas al captor:", "HIRE HIRED SWORD": "CONTRATAR ESPADA A SUELDO", "Hero skill lists": "Listas de habilidades de Héroe", "Hire or dismiss warriors and Hired Swords. Equipment purchases and assignments are handled in the next step. {}": "Contrata o expulsa guerreros y Espadas a Sueldo. Las compras y asignaciones de equipo se gestionan en el siguiente paso. {}", "LEFT EYE": "OJO IZQUIERDO", "LOST": "PERDIDO", "Marked warriors roll on the serious-injury charts in Recovery (post-battle step 1). For Henchman groups, choose exactly how many members went Out of Action.": "Los guerreros marcados tiran en las tablas de heridas graves en Recuperación (paso 1). En grupos de Secuaces, elige exactamente cuántos miembros quedaron Fuera de combate.", "Members recruited this sequence still need this equipment.": "Los miembros reclutados en esta secuencia aún necesitan este equipo.", "Models: {} → {}": "Miniaturas: {} → {}", "Mordheim campaign": "Campaña de Mordheim", "Most battles": "Más batallas", "Most recent": "Más reciente", "Multiple Injuries: {} additional result(s)": "Heridas múltiples: {} resultado(s) adicional(es)", "Multiple advances earned · {}": "Mejoras múltiples obtenidas · {}", "NEW CAMPAIGN": "NUEVA CAMPAÑA", "New file name:": "Nuevo nombre de archivo:", "No additional reward was recorded.": "No se registró ninguna recompensa adicional.", "No advances were recorded in this sequence.": "No se registraron mejoras en esta secuencia.", "No eligible group or warrior has enough copies available.": "Ningún grupo o guerrero apto tiene suficientes copias disponibles.", "No purchased equipment": "No hay equipo comprado", "No recruits of this type are currently in the warband.": "No hay reclutas de este tipo en la banda.", "No wyrdstone sale was recorded.": "No se registró ninguna venta de piedra bruja.", "Not achieved": "No conseguido", "Not obtained": "No obtenido", "Not resolved": "Sin resolver", "OCCUPY": "OCUPAR", "OTHER PERMANENT LOSS": "OTRA PÉRDIDA PERMANENTE", "Obtained: {}": "Obtenido: {}", "Old Battle Wound": "Herida de batalla antigua", "On a roll of 1, this warrior must miss the battle.": "Con un resultado de 1, este guerrero debe perderse la batalla.", "Out of Action": "Fuera de combate", "PER-WARRIOR EXPERIENCE": "EXPERIENCIA POR GUERRERO", "Pending advance": "Mejora pendiente", "Permanently delete '{}'? ": "¿Eliminar '{}' permanentemente? ", "Post-battle pending": "Postbatalla pendiente", "Previous result: {}": "Resultado anterior: {}", "Purchases, sales and assignments produced the final inventory.": "Las compras, ventas y asignaciones produjeron el inventario final.", "Quantity · reason for correction": "Cantidad · motivo de corrección", "RAISED AS A ZOMBIE": "CONVERTIDO EN ZOMBI", "RANSOM…": "RESCATE…", "RARE ITEMS & DRAMATIS": "OBJETOS RAROS Y DRAMATIS", "RATING": "VALORACIÓN", "RECORDED CONSEQUENCES": "CONSECUENCIAS REGISTRADAS", "RENAME…": "CAMBIAR NOMBRE…", "RESOLVED AT THE TABLE": "RESUELTO EN LA MESA", "RIGHT EYE": "OJO DERECHO", "Ransom": "Rescate", "Rare": "Raro", "Rare finds": "Hallazgos raros", "Rating: {} → {}": "Valoración: {} → {}", "Re-roll all Exploration dice": "Repetir todos los dados de Exploración", "Ready for battle": "Listo para la batalla", "Reason for correction": "Motivo de corrección", "Recruit: {} gc": "Recluta: {} gc", "Rename campaign file": "Cambiar nombre del archivo de campaña", "Replacement die": "Dado de reemplazo", "Resolve and apply every earned advance before continuing to Exploration.": "Resuelve y aplica cada mejora obtenida antes de continuar a Exploración.", "Resolve every required effect before continuing.": "Resuelve cada efecto requerido antes de continuar.", "Resolve lasting injuries before recording the battle. Failed warriors will be excluded automatically.": "Resuelve las heridas permanentes antes de registrar la batalla. Los guerreros fallidos se excluirán automáticamente.", "Resolve or acknowledge every follow-up before continuing.": "Resuelve o confirma cada seguimiento antes de continuar.", "Result: {}": "Resultado: {}", "Roll number of additional injuries": "Tirar el número de heridas adicionales", "Roll required by this result": "Tirada requerida por este resultado", "Roll again": "Volver a tirar", "SCENARIO OBJECTIVES": "OBJETIVOS DEL ESCENARIO", "SCENARIO RE-ROLL": "REPETICIÓN DEL ESCENARIO", "SET TARGET…": "FIJAR OBJETIVO…", "SHARDS AWARDED": "FRAGMENTOS CONCEDIDOS", "SKILLS / INJURIES": "HABILIDADES / HERIDAS", "SOLD INTO SLAVERY": "VENDIDO COMO ESCLAVO", "Sale income is included in the final treasury change.": "Los ingresos de la venta están incluidos en el cambio final de tesorería.", "Scenario exploration rule applied.": "Regla de exploración del escenario aplicada.", "Searches assigned during this sequence were completed.": "Se completaron las búsquedas asignadas en esta secuencia.", "Select one of the skills available to this Hero.": "Selecciona una de las habilidades disponibles para este Héroe.", "Serious injury after losing in the pits": "Herida grave tras perder en los fosos", "Serious-injury rolls were completed before the new roster state was created.": "Las tiradas de heridas graves se completaron antes de crear el nuevo estado de la plantilla.", "Structured scenario answers recorded with this battle.": "Respuestas estructuradas del escenario registradas con esta batalla.", "The final roster contains {} models.": "La plantilla final contiene {} miniaturas.", "The individual warriors were not recorded for this battle.": "No se registraron los guerreros individuales de esta batalla.", "The opposing warband rating was {}.": "La valoración de la banda rival era {}.", "The recorded battle award was +{} XP.": "La recompensa registrada de batalla fue de +{} PX.", "The result will be applied automatically when possible.": "El resultado se aplicará automáticamente cuando sea posible.", "The scenario permits one complete Exploration re-roll.": "El escenario permite repetir completamente una tirada de Exploración.", "The sequence created State #{}.": "La secuencia creó el Estado #{}.", "These requirements will be purchased or assigned during the Equipment step.": "Estos requisitos se comprarán o asignarán durante el paso de Equipamiento.", "This result is excluded from Multiple Injuries.": "Este resultado se excluye de Heridas múltiples.", "This scenario declares no structured awards; grant experience manually below or in post-battle.": "Este escenario no declara premios estructurados; concede la experiencia manualmente abajo o en la postbatalla.", "Tome of Magic": "Tomo de magia", "Treasures": "Tesoros", "Upgrade weapon": "Mejorar arma", "VETERAN EXPERIENCE": "EXPERIENCIA DE VETERANOS", "WARBAND EQUIPMENT": "EQUIPAMIENTO DE LA BANDA", "WHAT HAPPENED TO THE CAPTURED WARRIOR?": "¿QUÉ PASÓ CON EL GUERRERO CAPTURADO?", "WON": "GANÓ", "Warrior no longer in the current roster": "El guerrero ya no está en la plantilla actual", "Wyrdstone: {} → {}": "Piedra bruja: {} → {}", "You may re-roll one Exploration die.": "Puedes repetir un dado de Exploración.", "maximum": "máximo", "not recorded": "no registrado", "one member of {}": "un miembro de {}", "manual per-warrior value for scenarios without a structured award plan": "valor manual por guerrero para escenarios sin plan de premios estructurado", "pending": "pendiente", "roll": "tirada", "{} experience award": "{} de recompensa de experiencia", "{} gc available": "{} gc disponibles", "{} gc awarded.": "{} gc concedidas.", "{} gc remaining": "{} gc restantes", "{} gc to buy": "{} gc para comprar", "{} models were deployed with a warband rating of {}.": "Se desplegaron {} miniaturas con una valoración de banda de {}.", "{} put {} enemy model(s) Out of Action.": "{} dejó Fuera de combate a {} miniatura(s) enemiga(s).", "{} received +{} XP for a scenario objective.": "{} recibió +{} PX por un objetivo del escenario.", "{} shard(s) were sold.": "Se vendieron {} fragmento(s).", "{} warrior result(s) were marked Out of Action.": "Se marcaron {} resultado(s) de guerreros Fuera de combate.", "{} wyrdstone shard(s) awarded.": "Se concedieron {} fragmento(s) de piedra bruja.", "{} wyrdstone shard(s) recorded": "Se registraron {} fragmento(s) de piedra bruja", "{} wyrdstone shard(s) were added by exploration.": "La exploración añadió {} fragmento(s) de piedra bruja", "{} × {} added to the stash.": "{} × {} añadido(s) a la reserva.",    "{}: {}": "{}: {} ({} )", "{}: {}× {}": "{}: {} por {}",
    " · the scenario allows one complete reroll": " · el escenario permite repetir completamente una tirada",
    "+{} exploration die · reroll all dice": "+{} dado de exploración · repetir todos los dados",
    "A campaign with that file name already exists.": "Ya existe una campaña con ese nombre de archivo.",
    "A stored injury result can no longer be resolved from the KB.": "Un resultado de herida guardado ya no puede resolverse desde la base de conocimiento.",
    "Automatic awards plus each warrior’s scenario actions.": "Premios automáticos más las acciones de escenario de cada guerrero.",
    "Buy and sell equipment, then drag items between the stash and warriors. Rare items found earlier remain available and are highlighted. {}": "Compra y vende equipo; después arrastra objetos entre la reserva y los guerreros. Los objetos raros encontrados siguen disponibles y destacados. {}",
    "CHOOSE 2 SKILL LISTS…": "ELEGIR 2 LISTAS DE HABILIDADES…", "CHOOSE HERO AND SPELLS…": "ELEGIR HÉROE Y CONJUROS…",
    "New Hero · The Lad's Got Talent · immediate 2D6 Hero advance": "Héroe nuevo · El Chico Tiene Talento · mejora inmediata de Héroe 2D6",
    "Resolve and apply every earned advance before continuing to Exploration. Pending: {}": "Resuelve y aplica cada mejora obtenida antes de continuar a Exploración. Pendientes: {}",
    "Resolve or acknowledge every follow-up before continuing: {}": "Resuelve o confirma cada seguimiento antes de continuar: {}",
    "Rolled {}: excluded result — roll again": "Resultado {}: resultado excluido; vuelve a tirar",
    "Rolled {}: {} — this result cannot be applied and must be rerolled.": "Resultado {}: {}; no se puede aplicar y debe repetirse la tirada.",
    "Roster size: {} → {} models": "Tamaño de plantilla: {} → {} miniaturas", "SACRIFICED": "SACRIFICADO", "STRAGGLER BONUS": "BONIFICACIÓN DEL REZAGADO",
    "Select a campaign to see its summary.": "Selecciona una campaña para ver su resumen.", "Select the Post-Battle node in the timeline to continue.": "Selecciona el nodo de Postbatalla en la línea temporal para continuar.",
    "The battle record handed the following totals to its Post-Battle sequence.": "El registro de batalla entregó los siguientes totales a su secuencia de Postbatalla.",
    "These are the facts recorded at the end of the battle; lasting consequences belong to Post-Battle.": "Estos son los hechos registrados al final de la batalla; las consecuencias permanentes pertenecen a la Postbatalla.",
    "This sequence was completed before the event log existed; aggregate totals above summarise it.": "Esta secuencia se completó antes de existir el registro de eventos; los totales anteriores la resumen.",
    "This subtable result could not be resolved from the KB.": "Este resultado de subtabla no pudo resolverse desde la base de conocimiento.",
    "Treasury: {} → {} gc": "Tesorería: {} → {} gc", "Veteran Experience: {} XP": "Experiencia de veteranos: {} PX", "Warband rating: {} → {}": "Valoración de banda: {} → {}",
    "{} D66 roll(s) required.": "Se requieren {} tirada(s) de D66.", "{} Heroes available · {} rare items · {} Dramatis Personae": "{} Héroes disponibles · {} objetos raros · {} Dramatis Personae",
    "{} Out of Action result(s) were recorded.": "Se registraron {} resultado(s) Fuera de combate.", "{} Veteran XP remained after recruitment.": "Quedaron {} PX de veteranos tras el reclutamiento.", "{} advance(s) recorded": "Se registraron {} mejora(s)",
    "{} faced {} in {} and recorded a {}.": "{} se enfrentó a {} en {} y registró un {}.",    "{} · did not participate · {} · {} battle(s) remaining before this battle": "{} · no participó · {} · quedan {} batalla(s) antes de esta batalla",
    "CREATE": "CREAR", "COMMIT": "CONFIRMAR", "RETURN": "DEVOLVER",
    "Injury: {} · {} {}": "Herida: {} · {} {}", "Injury: {}": "Herida: {}",
    "Lasting Injury": "Herida permanente", "Recovery": "Recuperación",
    "Injury: {} · misses {} more battle(s)": "Herida: {} · se pierde {} batalla(s) más",
    "Injury: Bitter Enmity · Hatred: {}": "Herida: Enemistad amarga · Odio: {}",
    "Injury: Old Battle Wound · roll D6 before each battle; misses it on 1": "Herida: Herida de batalla antigua · tira un D6 antes de cada batalla; con 1 se la pierde",
    "Injury: Blinded In One Eye · lost {} eye": "Herida: Cegado de un ojo · perdió el ojo {}",
    "Leg Wound": "Herida en la pierna", "Chest Wound": "Herida en el pecho",
    "Blinded In One Eye": "Cegado de un ojo", "Nervous Condition": "Afección nerviosa", "Hand Injury": "Herida en la mano",
    "left": "izquierdo", "right": "derecho", "both": "ambos",
}.items()})


def set_locale(locale: str | None = None) -> str:
    """Select the UI locale (``"en"`` / ``"es"``); returns the effective one.

    ``None`` defers to ``MORDHEIM_LOCALE``. Unsupported locales keep the
    current selection, so a typo can never blank the interface.
    """
    global _active_locale
    candidate = str(locale or os.environ.get("MORDHEIM_LOCALE") or CANONICAL_LOCALE).strip().lower().split("-", 1)[0]
    if candidate in SUPPORTED_LOCALES:
        _active_locale = candidate
    return _active_locale


def current_locale() -> str:
    """The active UI locale (canonical English unless changed)."""
    return _active_locale


def tr(key: str) -> str:
    """Translate one UI string in the active locale.

    Untranslated or unknown keys return the key itself (the English literal),
    keeping the current interface byte-identical under ``en``.
    """
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_active_locale) or key


#: Application-layer result messages shown verbatim by the widgets. The
#: application layer stays Tkinter-free, so it cannot call ``tr`` itself;
#: instead the widgets pass the returned message through this catalogue. A
#: message without an entry renders in English, never crashing.
MESSAGES: dict[str, str] = {
    "Rarity {}: a 2D6 roll of {} (modifiers {}) finds the item.": "Rareza {}: una tirada de 2D6 de {} (modificadores {}) encuentra el objeto.",
    "Rarity {}: a 2D6 roll of {} (modifiers {}) does not find the item.": "Rareza {}: una tirada de 2D6 de {} (modificadores {}) no encuentra el objeto.",
    "Rarity {}: a 2D6 roll of {} finds the item.": "Rareza {}: una tirada de 2D6 de {} encuentra el objeto.",
    "Rarity {}: a 2D6 roll of {} does not find the item.": "Rareza {}: una tirada de 2D6 de {} no encuentra el objeto.",
    "No Trading Post availability declared for this item.": "Este objeto no tiene disponibilidad declarada en el Puesto Comercial.",
    "Roll again on the same chart (D66).": "Vuelve a tirar en la misma tabla (D66).",
    "Follow-up D6 subtable required.": "Se requiere una subtabla D6 de seguimiento.",
    "{} dice rolled {}: {}.": "{} dados con resultado {}: {}.",
    "The selected base weapon is not available in the stash.": "El arma base elegida no está disponible en la reserva.",
    "This weapon upgrade is not available during warband creation.": "Esta mejora de arma no está disponible durante la creación de la banda.",
    "Only weapons can receive this upgrade.": "Solo las armas pueden recibir esta mejora.",
    "There is nothing to undo.": "No hay nada que deshacer.",
    "This warrior cannot use that item during creation.": "Este guerrero no puede usar ese objeto durante la creación.",
    "Source and destination are the same warrior.": "Origen y destino son el mismo guerrero.",
    "Unknown source or destination warrior.": "Guerrero de origen o destino desconocido.",
    "This item cannot be transferred.": "Este objeto no se puede transferir.",
    "The destination warrior cannot use that item during creation.": "El guerrero de destino no puede usar ese objeto durante la creación.",
    "Commit the initial warband before recording battles.": "Confirma la banda inicial antes de registrar batallas.",
    "Result must be Victory, Defeat or Draw.": "El resultado debe ser Victoria, Derrota o Empate.",
    "Resolve every pre-battle injury check before recording the battle.": "Resuelve todas las comprobaciones de herida previas a la batalla antes de registrarla.",
    "Unknown pre-battle injury check.": "Comprobación de herida previa desconocida.",
    "Enter a reason for the correction.": "Introduce un motivo para la corrección.",
    "Only gold crowns are available during creation.": "Solo hay coronas de oro disponibles durante la creación.",
    "Resources can be corrected only during creation or post-battle.": "Los recursos solo pueden corregirse durante la creación o la postbatalla.",
    "Items can be corrected only during creation or post-battle.": "Los objetos solo pueden corregirse durante la creación o la postbatalla.",
    "Enter a reason for adding the item.": "Introduce un motivo para añadir el objeto.",
    "Select an item from the KB catalogue.": "Selecciona un objeto del catálogo de la base de conocimiento.",
    "Enter a reason for the skill correction.": "Introduce un motivo para la corrección de habilidad.",
    "Skills can be edited only during creation or post-battle.": "Las habilidades solo pueden editarse durante la creación o la postbatalla.",
    "Unknown warrior or skill.": "Guerrero o habilidad desconocidos.",
    "An inherent or starting skill cannot be removed.": "No se puede eliminar una habilidad inherente o inicial.",
    "Only the initial warband draft can be edited.": "Solo se puede editar el borrador de la banda inicial.",
    "Heroes are individuals; add or remove them instead.": "Los héroes son individuales; añádelos o quítalos en su lugar.",
    "Profile is no longer available in the knowledge base.": "El perfil ya no está disponible en la base de conocimiento.",
    "A henchman group keeps at least one member.": "Un grupo de secuaces conserva al menos un miembro.",
    "Not enough gold for the added members.": "No hay oro suficiente para los miembros añadidos.",
    "Warrior not found in the draft.": "Guerrero no encontrado en el borrador.",
    "Only draft warriors and groups can be renamed here.": "Solo se pueden renombrar aquí guerreros y grupos del borrador.",
    "Name cannot be empty.": "El nombre no puede estar vacío.",
    "Another warrior or group already uses that name.": "Otro guerrero o grupo ya usa ese nombre.",
    "Only draft warriors can buy creation equipment.": "Solo los guerreros del borrador pueden comprar equipo de creación.",
    "This warrior cannot buy that item.": "Este guerrero no puede comprar ese objeto.",
    "This item has no supported creation price.": "Este objeto no tiene precio de creación soportado.",
    "Purchased item not found on this draft warrior.": "El objeto comprado no se encuentra en este guerrero del borrador.",
    "Hired Swords can be added here only during warband creation.": "Las Espadas a Sueldo solo pueden añadirse aquí durante la creación de la banda.",
    "This Hired Sword is not available to the warband.": "Esta Espada a Sueldo no está disponible para la banda.",
    "Select the warband's Mercenary variant first.": "Selecciona primero la variante Mercenario de la banda.",
    "Items can be bought for the draft stash only during creation.": "Los objetos solo pueden comprarse para la reserva del borrador durante la creación.",
    "This warband cannot buy that item.": "Esta banda no puede comprar ese objeto.",
    "That quantity is not available in the draft stash.": "Esa cantidad no está disponible en la reserva del borrador.",
    "No pending post-battle.": "No hay postbatalla pendiente.",
    "Post-Battle #{} is still pending; commit it before recording the next battle.": "La Postbatalla #{} sigue pendiente; confírmala antes de registrar la siguiente batalla.",
    "Unknown scenario: {}": "Escenario desconocido: {}",
    "Unavailable warriors cannot receive battle results: {}.": "Los guerreros no disponibles no pueden recibir resultados de batalla: {}.",
    "The destination needs {} copies; only {} are available.": "El destino necesita {} copias; solo hay {} disponibles.",
    "{} transferred from {} to {}.": "{} transferido de {} a {}.",
}

#: Application-layer result messages shown verbatim by the widgets. The
#: application layer stays Tkinter-free, so it cannot call ``tr`` itself;
#: instead the widgets pass the returned message through this catalogue. A
#: message without an entry renders in English, never crashing.
MESSAGES.update({
    '+1 {} is not offered by this advance.': '+1 {} no lo ofrece esta mejora.',
    'A die roll is required.': 'Se requiere una tirada de dado.',
    'A valid D66 result is required after losing in the pits.': 'Se requiere un resultado D66 válido tras perder en los fosos.',
    'Acceptance roll failed; {}+ was required.': 'La tirada de aceptación falló; se requería {}+.',
    'Acceptance roll {} failed (needed {}+); the hire is declined.': 'La tirada de aceptación {} falló (se necesitaba {}+); la contratación se rechaza.',
    'An acceptance roll of {}+ is required before hiring.': 'Se requiere una tirada de aceptación de {}+ antes de contratar.',
    'An acceptance roll of {}+ is required.': 'Se requiere una tirada de aceptación de {}+.',
    'Battle #{} recorded · {} vs. {} ({}).': 'Batalla #{} registrada · {} contra {} ({}).',
    'Battle experience already applied.': 'Experiencia de batalla ya aplicada.',
    'Cannot exceed {} heroes.': 'No se pueden superar {} héroes.',
    'Cannot exceed {} warband members.': 'No se pueden superar {} miembros de banda.',
    'Cannot sell a negative quantity.': 'No se puede vender una cantidad negativa.',
    'Choose a Hero.': 'Elige un Héroe.',
    'Choose a skill to commit.': 'Elige una habilidad que confirmar.',
    'Choose a spell to commit.': 'Elige un conjuro que confirmar.',
    'Choose at most {} eligible warriors.': 'Elige como máximo {} guerreros aptos.',
    'Choose exactly two different Hero skill lists.': 'Elige exactamente dos listas de habilidades de Héroe distintas.',
    'Choose exactly two different spells.': 'Elige exactamente dos conjuros distintos.',
    'Choose one of the available options.': 'Elige una de las opciones disponibles.',
    'Choose ransom, exchange, or permanent loss.': 'Elige rescate, intercambio o pérdida permanente.',
    'Choose the duplicated spell.': 'Elige el conjuro duplicado.',
    "Choose the warrior's remaining eye.": 'Elige el ojo restante del guerrero.',
    "Choose two Hero skill lists before rolling the promoted Hero's advance.": 'Elige dos listas de habilidades de Héroe antes de tirar la mejora del Héroe promocionado.',
    'Choose what happened to the captured warrior.': 'Elige qué pasó con el guerrero capturado.',
    'Choose whether to destroy or occupy the camp.': 'Elige destruir u ocupar el campamento.',
    'Enter a result from 1 to {}.': 'Introduce un resultado de 1 a {}.',
    'Enter the warrior, warband, or warband type hated.': 'Introduce el guerrero, banda o tipo de banda odiado.',
    'Every member of {} already carries {}.': 'Cada miembro de {} ya porta {}.',
    'Every selected list must be available to Heroes in this warband.': 'Cada lista seleccionada debe estar disponible para los Héroes de esta banda.',
    'Fee roll must be between {} and {}.': 'La tirada de tarifa debe estar entre {} y {}.',
    'Fee roll {} is below the minimum {} of {}D{}.': 'La tirada de tarifa {} está por debajo del mínimo {} de {}D{}.',
    'Follow-up resolved: {} (the warrior is no longer on the roster).': 'Seguimiento resuelto: {} (el guerrero ya no está en la plantilla).',
    'Groups of {} hold at most {} models.': 'Los grupos de {} tienen como máximo {} miniaturas.',
    'Hero maximum reached ({}); reroll this advance.': 'Máximo de héroes alcanzado ({}); vuelve a tirar esta mejora.',
    'Hireling profile not found in the KB: {}': 'Perfil de contratado no encontrado en la base de conocimiento: {}',
    'Invalid upgrade price: expected {} gc.': 'Precio de mejora no válido: se esperaban {} gc.',
    'No exploration follow-up pending.': 'No hay seguimiento de exploración pendiente.',
    'No pending advance for: {}': 'No hay mejora pendiente para: {}',
    'No pending promotion for this warrior.': 'No hay promoción pendiente para este guerrero.',
    'No unassigned {} in the stash.': 'No hay {} sin asignar en la reserva.',
    'No unresolved advance can be rerolled.': 'No hay mejora sin resolver que se pueda repetir.',
    'Not enough gold: {} costs {} gc, treasury is {} gc.': 'Oro insuficiente: {} cuesta {} gc, la tesorería es {} gc.',
    'Not enough gold: {} gc needed (recruit + experience cost), {} gc available.': 'Oro insuficiente: se necesitan {} gc (recluta + coste de experiencia), hay {} gc.',
    'Not enough gold: {} gc needed, {} gc available.': 'Oro insuficiente: se necesitan {} gc, hay {} gc.',
    'Not enough gold: {} gc needed.': 'Oro insuficiente: se necesitan {} gc.',
    'Not enough {}: {} needed, {} available.': '{} insuficiente: se necesitan {}, hay {}.',
    'One member joined {} for {} gc; equipment remains pending.': 'Un miembro se unió a {} por {} gc; el equipo queda pendiente.',
    'One selected spell is not available to this Hero.': 'Uno de los conjuros elegidos no está disponible para este Héroe.',
    'Only an existing henchman group can receive a member.': 'Solo un grupo de secuaces existente puede recibir un miembro.',
    'Only one {} may be employed by the warband.': 'La banda solo puede contratar un {}.',
    'Only {} of {} actions completed.': 'Solo {} de {} acciones completadas.',
    'Only {} shard(s) available to sell.': 'Solo hay {} fragmento(s) disponibles para vender.',
    'Only {} unassigned copy/copies in the stash.': 'Solo hay {} copia(s) sin asignar en la reserva.',
    'Per-warrior scenario awards applied (see the battle record).': 'Premios de escenario por guerrero aplicados (ver el registro de batalla).',
    'Promote the group member before choosing skill lists.': 'Promociona al miembro del grupo antes de elegir listas de habilidades.',
    'Renamed to {}.': 'Renombrado a {}.',
    'Required matching Henchmen equipment is still pending.': 'El equipo coincidente requerido de los Secuaces sigue pendiente.',
    'Resolve the advance roll first.': 'Resuelve primero la tirada de mejora.',
    'Resolved price must be between {} and {} gc.': 'El precio resuelto debe estar entre {} y {} gc.',
    'Roll the hiring fee ({}D{} + {} gc).': 'Tira la tarifa de contratación ({}D{} + {} gc).',
    'Roll {} lands on an excluded result; roll again.': 'La tirada {} da un resultado excluido; vuelve a tirar.',
    "Roll {}'s hiring fee ({}D{} + {} gc) before hiring.": 'Tira la tarifa de contratación de {} ({}D{} + {} gc) antes de contratar.',
    'Roster limit for {} reached ({} remaining).': 'Límite de plantilla de {} alcanzado (quedan {}).',
    'Roster limit for {} reached ({}/{}).': 'Límite de plantilla de {} alcanzado ({}/{}).',
    'Roster limit for {} reached.': 'Límite de plantilla de {} alcanzado.',
    "Spell {} is not in {}'s lore ({}).": 'El conjuro {} no está en la lista de {} ({}).',
    'The Hired Sword already left the warband.': 'La Espada a Sueldo ya dejó la banda.',
    "The Lad's Got Talent promotes a henchman group member.": 'El Chico Tiene Talento promociona a un miembro del grupo de secuaces.',
    'The advance roll is not resolved yet.': 'La tirada de mejora aún no está resuelta.',
    'The captured warrior is no longer on the roster.': 'El guerrero capturado ya no está en la plantilla.',
    'The correction would leave a negative balance ({}).': 'La corrección dejaría un saldo negativo ({}).',
    'The remaining Henchmen must reroll results 10-12. Roll again.': 'Los Secuaces restantes deben repetir los resultados 10-12. Tira de nuevo.',
    'The stash needs {} more {} for the whole group.': 'La reserva necesita {} {} más para todo el grupo.',
    'The warband cannot pay a ransom of {} gc.': 'La banda no puede pagar un rescate de {} gc.',
    'The warrior is no longer on the roster.': 'El guerrero ya no está en la plantilla.',
    'This advance does not increase a characteristic.': 'Esta mejora no aumenta una característica.',
    'This advance is already committed.': 'Esta mejora ya está confirmada.',
    'This advance offers several characteristics; choose one.': 'Esta mejora ofrece varias características; elige una.',
    'This advance requires a table-side resolution; it has been recorded as resolved.': 'Esta mejora requiere resolución en la mesa; se ha registrado como resuelta.',
    "This hire needs the warband's Mercenary variant, which is not selected yet.": 'Esta contratación necesita la variante Mercenario de la banda, aún sin seleccionar.',
    'This hire requires an acceptance roll that is not declared.': 'Esta contratación requiere una tirada de aceptación no declarada.',
    'This item has no flat price; purchases are not supported yet.': 'Este objeto no tiene precio fijo; las compras aún no están soportadas.',
    'This post-battle is already committed.': 'Esta postbatalla ya está confirmada.',
    'This weapon upgrade is not available to the warband in this phase.': 'Esta mejora de arma no está disponible para la banda en esta fase.',
    'Undone: {}.': 'Deshecho: {}.',
    'Unknown Bitter Enmity follow-up.': 'Seguimiento de Enemistad amarga desconocido.',
    'Unknown Hired Sword upkeep.': 'Manutención de Espada a Sueldo desconocida.',
    'Unknown Sold to the Pits encounter.': 'Encuentro de Vendido a los fosos desconocido.',
    'Unknown Tome of Magic reward or Hero.': 'Recompensa del Tomo de magia o Héroe desconocidos.',
    'Unknown advance option in the KB: {}': 'Opción de mejora desconocida en la base de conocimiento: {}',
    'Unknown captured-warrior follow-up.': 'Seguimiento de guerrero capturado desconocido.',
    'Unknown characteristic: {}': 'Característica desconocida: {}',
    'Unknown eye-injury follow-up.': 'Seguimiento de herida ocular desconocido.',
    'Unknown follow-up.': 'Seguimiento desconocido.',
    'Unknown item.': 'Objeto desconocido.',
    'Unknown profile: {}': 'Perfil desconocido: {}',
    'Unknown resource: {}': 'Recurso desconocido: {}',
    'Unknown skill: {}': 'Habilidad desconocida: {}',
    'Unknown warrior or item.': 'Guerrero u objeto desconocido.',
    'Unknown warrior: {}': 'Guerrero desconocido: {}',
    'Warband limit reached: at most {} of this item (own {}).': 'Límite de banda alcanzado: como máximo {} de este objeto (en propiedad {}).',
    'Wyrdstone can only be sold once per post-battle sequence.': 'La piedra bruja solo puede venderse una vez por secuencia de posbatalla.',
    '{} XP applied to each surviving warrior.': '{} PX aplicados a cada guerrero superviviente.',
    '{} already has the {} upgrade.': '{} ya tiene la mejora {}.',
    '{} already knows {} (rolled twice: lower its difficulty by 1).': '{} ya conoce {} (salió dos veces: baja su dificultad en 1).',
    '{} already knows {}.': '{} ya conoce {}.',
    '{} already knows {}; choose another spell.': '{} ya conoce {}; elige otro conjuro.',
    '{} bought for {} gc.': '{} comprado por {} gc.',
    '{} corrected by {}.': '{} corregido en {}.',
    '{} declares both a flat and a variable fee; the KB entry is inconsistent.': '{} declara tarifa fija y variable a la vez; la entrada de la base de conocimiento es incoherente.',
    '{} declares no hiring fee the application can charge.': '{} no declara ninguna tarifa de contratación que la aplicación pueda cobrar.',
    '{} deepens {}: casting difficulty reduced by 1.': '{} profundiza {}: la dificultad de lanzamiento baja en 1.',
    '{} does not carry {}.': '{} no porta {}.',
    '{} does not know {}; pick it as a new spell instead.': '{} no conoce {}; elígelo como conjuro nuevo en su lugar.',
    '{} gains +{} {} (now {}).': '{} gana +{} {} (ahora {}).',
    '{} has no payable hiring fee.': '{} no tiene tarifa de contratación pagable.',
    '{} hired for {}.': '{} contratado por {}.',
    '{} holds at most {} models.': '{} tiene como máximo {} miniaturas.',
    '{} is forbidden for this profile.': '{} está prohibido para este perfil.',
    '{} is forbidden for {}: the profile may never acquire {} skills.': '{} está prohibido para {}: el perfil nunca puede adquirir habilidades de {}.',
    '{} is not a wizard in the KB lore assignments.': '{} no es un hechicero en las asignaciones de listas de la base de conocimiento.',
    "{} is not in {}'s skill access.": '{} no está en el acceso a habilidades de {}.',
    "{} is not on {}'s skill tables ({}).": '{} no está en las tablas de habilidades de {} ({}).',
    '{} learns the spell {}.': '{} aprende el conjuro {}.',
    '{} learns {}.': '{} aprende {}.',
    '{} may only be assigned to heroes.': '{} solo puede asignarse a héroes.',
    '{} may use {} and {}; roll one Hero advance now.': '{} puede usar {} y {}; tira ahora una mejora de Héroe.',
    '{} needs {} Veteran XP; only {} available.': '{} necesita {} PX de veteranos; solo hay {} disponibles.',
    '{} needs {}× {}; only {} in stash.': '{} necesita {}× {}; solo {} en la reserva.',
    '{} now has {} member{}.': '{} ahora tiene {} miembro{}.',
    '{} now knows {}.': '{} ahora conoce {}.',
    '{} removed from the draft.': '{} quitado del borrador.',
    '{} sold; {} gc refunded.': '{} vendido; {} gc devueltas.',
    '{} upgraded to {} for {} gc.': '{} mejorado a {} por {} gc.',
    '{} {} is already at the {} racial maximum ({}).': '{} {} ya está en el máximo racial de {} ({}).',
    '{}: no lasting effect on the roster.': '{}: sin efecto permanente en la plantilla.',
    '{}× {} added to stash.': '{}× {} añadido(s) a la reserva.',
    '{}× {} bought for {} gc (stash).': '{}× {} comprado(s) por {} gc (reserva).',
    '{}× {} sold; {} gc refunded.': '{}× {} vendido(s); {} gc devueltas.',
})


STRINGS.update({k: {"es": v} for k, v in {
    'All warbands of that type': 'Todas las bandas de ese tipo',
    'Arm Wound': 'Herida en el brazo',
    'Bitter Enmity': 'Enemistad amarga',
    'Captured': 'Capturado',
    'Dead': 'Muerto',
    'Deep Wound': 'Herida profunda',
    'Frenzy': 'Frenesí',
    'Full Recovery': 'Recuperación completa',
    'Hardened': 'Endurecido',
    'Horrible Scars': 'Cicatrices horribles',
    'Light wound': 'Herida leve',
    'Madness': 'Locura',
    'Robbed': 'Desvalijado',
    'Severe arm wound': 'Herida grave en el brazo',
    'Smashed Leg': 'Pierna destrozada',
    'Sold To The Pits': 'Vendido a los fosos',
    'Stupidity': 'Estupidez',
    'Survives Against The Odds': 'Sobrevive contra todo pronóstico',
    'The entire warband of the warrior responsible for the injury': 'Toda la banda del guerrero responsable de la herida',
    'The individual who caused the injury (the enemy leader if it was a Henchman)': 'El individuo que causó la herida (el líder enemigo si era un Secuaz)',
    'The leader of the warband that caused the injury': 'El líder de la banda que causó la herida',
    'Removed': 'Retirado',
    'removes the warrior from the roster': 'quita al guerrero de la plantilla',
    'permanent characteristic modifier': 'modificador permanente de característica',
    'battle-start characteristic check': 'chequeo de característica al inicio de batalla',
    'misses games': 'se pierde partidas',
    'gains a lasting condition': 'gana una condición permanente',
    'equipment is lost or sold': 'el equipo se pierde o se vende',
    'warrior is captured': 'el guerrero es capturado',
    'triggers a special encounter': 'desencadena un encuentro especial',
    'gains a reward': 'gana una recompensa',
    'Permanent {} modifier: {:+d}.': 'Modificador permanente de {}: {:+d}.',
    'May use no more than {} one-handed weapon at a time.': 'No puede usar más de {} arma a una mano a la vez.',
    'Gains a permanent equipment restriction.': 'Gana una restricción permanente de equipo.',
    'Misses the next {} game{}.': 'Se pierde la(s) próxima(s) {} partida(s).',
    'Misses {}D{} games; roll to determine the duration.': 'Se pierde {}D{} partidas; tira para determinar la duración.',
    'Gains {}.': 'Gana {}.',
    'Before each battle roll {}D{}; on {}, the warrior misses that game.': 'Antes de cada batalla tira {}D{}; con {}, el guerrero se pierde esa partida.',
    'All equipment carried by the warrior is lost.': 'Todo el equipo que porta el guerrero se pierde.',
    'The warrior is permanently removed from the roster.': 'El guerrero se retira permanentemente de la plantilla.',
    'The warrior is captured; their equipment remains with them until captivity is resolved.': 'El guerrero es capturado; su equipo permanece con él hasta resolver el cautiverio.',
    'Permanently hates {}.': 'Odia permanentemente a {}.',
    'Triggers the special Sold to the Pits encounter; resolve it before continuing.': 'Desencadena el encuentro especial Vendido a los fosos; resuélvelo antes de continuar.',
    'The warrior gains {} Experience.': 'El guerrero gana {} de experiencia.',
    'The warrior gains the listed reward.': 'El guerrero gana la recompensa indicada.',
    'Matching dice': 'Dados coincidentes',
}.items()})


STRINGS.update({k: {"es": v} for k, v in {
    'Mordheim Combat Lab': 'Laboratorio de Combate Mordheim',
    'Simulation Workbook': 'Libro de simulación',
    'Collections ▾': 'Colecciones ▾',
    'Mordheim Core': 'Núcleo de Mordheim',
    'Import ▾': 'Importar ▾',
    'Load candidate': 'Cargar candidato',
    'Load enemy': 'Cargar rival',
    'Load': 'Cargar',
    'Save': 'Guardar',
    'Candidate': 'Candidato',
    'Enemy': 'Rival',
    'Improvements': 'Mejoras',
    'Weapons': 'Armas',
    'Equipment': 'Equipamiento',
    'House Rules': 'Reglas de la casa',
    'Active runtime': 'Motor activo',
    'Mordheim close combat · KB-backed legal equipment · deterministic seed support': 'Combate cuerpo a cuerpo de Mordheim · equipo legal respaldado por la base de conocimiento · soporte de semilla determinista',
    'Configure the candidate and enemy, then use an analysis tab.': 'Configura el candidato y el rival y usa una pestaña de análisis.',
    'Ready for an analysis with the selected fighters.': 'Listo para un análisis con los luchadores seleccionados.',
    'Configuration error: {}': 'Error de configuración: {}',
    'Save Mordheim Combat Lab workbook': 'Guardar libro de Mordheim Combat Lab',
    'Load Mordheim Combat Lab workbook': 'Cargar libro de Mordheim Combat Lab',
    'Workbook save error: {}': 'Error al guardar el libro: {}',
    'Saved workbook: {}': 'Libro guardado: {}',
    'Workbook load error: {}': 'Error al cargar el libro: {}',
    'Loaded {} : {}': 'Cargado {}: {}',
    'Loaded workbook: {}': 'Libro cargado: {}',
    'Choose a warrior and their legal combat configuration.': 'Elige un guerrero y su configuración de combate legal.',
    'Configure the opposing warrior used by every simulation and analysis.': 'Configura el guerrero rival usado por cada simulación y análisis.',
    'The executable rules are selected by the knowledge base. This version deliberately does not restore the legacy checkboxes: they altered the retired engine and could silently produce a duel that the new runtime cannot represent.': 'Las reglas ejecutables las selecciona la base de conocimiento. Esta versión no restaura deliberadamente las casillas heredadas: alteraban el motor retirado y podían producir en silencio un duelo que el nuevo motor no puede representar.',
    'Identity and Source': 'Identidad y origen',
    'Name:': 'Nombre:',
    'Warband:': 'Banda:',
    'Warrior:': 'Guerrero:',
    'BASIC ATTRIBUTES': 'ATRIBUTOS BÁSICOS',
    'EQUIPMENT': 'EQUIPAMIENTO',
    'Main Hand': 'Mano principal',
    'Free hand': 'Mano libre',
    'No armour': 'Sin armadura',
    'No poison': 'Sin veneno',
    'No helmet': 'Sin yelmo',
    'No preparation': 'Sin preparación',
    'None': 'Ninguno',
    'Off Hand': 'Mano secundaria',
    'Armour': 'Armadura',
    'Skills': 'Habilidades',
    'SKILLS': 'HABILIDADES',
    'Weapon': 'Arma',
    'Weapon analysis': 'Análisis de armas',
    'Each legal main weapon is simulated against the current enemy configuration.': 'Cada arma principal legal se simula contra la configuración actual del rival.',
    'Compare weapons': 'Comparar armas',
    'No selectable skills are available for this profile.': 'No hay habilidades seleccionables disponibles para este perfil.',
    'Material': 'Material (equipo)',
    'Poison': 'Veneno',
    'Free selection loaded · all implemented duel skills are available.': 'Selección libre cargada · todas las habilidades de duelo implementadas están disponibles.',
    'Equipment analysis': 'Análisis de equipamiento',
    'The selected main weapon and skills remain fixed while legal equipment configurations are simulated.': 'El arma principal y las habilidades elegidas permanecen fijas mientras se simulan configuraciones de equipo legales.',
    'Simulations': 'Simulaciones',
    'Battery workers': 'Workers de batería',
    'Battery workers (-1 = automatic, 0 = sequential)': 'Workers de batería (-1 = automático, 0 = secuencial)',
    'Compare equipment': 'Comparar equipamiento',
    'Maximum changed slots': 'Máximo de ranuras modificadas',
    "Compare the candidate's legal off-hand and armour configurations.": 'Compara las configuraciones legales de mano secundaria y armadura del candidato.',
    'Item {}': 'Objeto {}',
    'Best Result': 'Mejor resultado',
    'MOTTA Score': 'Puntuación MOTTA',
    'Cost': 'Coste',
    'Equipment Used': 'Equipamiento usado',
    'Off hand': 'Mano secundaria',
    'Helmet': 'Yelmo',
    'Preparation': 'Preparación',
    'Main material': 'Material principal',
    'Main poison': 'Veneno principal',
    'Off-hand material': 'Material de la mano secundaria',
    'Off-hand poison': 'Veneno de la mano secundaria',
    'Current configuration': 'Configuración actual',
    'Comparing {} equipment configurations…': 'Comparando {} configuraciones de equipamiento…',
    'Compared {} configurations across {} duels.': 'Se compararon {} configuraciones en {} duelos.',
    ' Skipped {} invalid configurations.': ' Se omitieron {} configuraciones no válidas.',
    'Complete': 'Completo',
    'Error': 'Error del análisis',
    'Cancelled': 'Cancelado',
    'Equipment analysis error: {}': 'Error del análisis de equipamiento: {}',
    'Equipment analysis cancelled.': 'Análisis de equipamiento cancelado.',
    'Improvement analysis': 'Análisis de mejoras',
    'Each result adds one currently unselected, profile-legal skill to the candidate configuration.': 'Cada resultado añade una habilidad legal del perfil aún sin elegir a la configuración del candidato.',
    'Compare improvements': 'Comparar mejoras',
    'Compare each legal additional skill against the candidate baseline.': 'Compara cada habilidad adicional legal contra la línea base del candidato.',
    'Improvement {}': 'Mejora {}',
    'Comparing {} additional skills…': 'Comparando {} habilidades adicionales…',
    'Baseline: {}% candidate win rate. Compared {} skills across {} duels.': 'Línea base: {}% de victorias del candidato. Se compararon {} habilidades en {} duelos.',
    'Number of improvements:': 'Número de mejoras:',
    'Skills ({} / {})': 'Habilidades ({} / {})',
    'Select all': 'Seleccionar todas',
    'Select none': 'Deseleccionar todas',
    'Select at least one improvement to compare.': 'Selecciona al menos una mejora para comparar.',
    'Not enough selected skills for {} improvements.': 'No hay suficientes habilidades seleccionadas para {} mejoras.',
    'Each row applies the selected profile-legal skills to the candidate configuration.': 'Cada fila aplica al candidato las habilidades legales del perfil seleccionadas.',
    'Baseline: {}% candidate win rate. Compared {} combinations across {} duels.': 'Línea base: {}% de victorias del candidato. Se compararon {} combinaciones en {} duelos.',
    'Comparing {} improvement combinations…': 'Comparando {} combinaciones de mejoras…',
    'Weapons ({} / {})': 'Armas ({} / {})',
    'Select at least one weapon to compare.': 'Selecciona al menos un arma para comparar.',
    'Comparing {} weapons with {} duels each…': 'Comparando {} armas con {} duelos cada una…',
    'Compared {} weapons across {} duels.': 'Se compararon {} armas en {} duelos.',
    'Each selected main weapon is simulated against the current enemy configuration.': 'Cada arma principal seleccionada se simula contra la configuración enemiga actual.',
    'Weapon analysis error: {}': 'Error del análisis de armas: {}',
    'Weapon analysis cancelled.': 'Análisis de armas cancelado.',
    'Configure the duel, then compare the candidate\'s legal weapons.': 'Configura el duelo y compara las armas legales del candidato.',
    'Improvement analysis error: {}': 'Error del análisis de mejoras: {}',
    'Improvement analysis cancelled.': 'Análisis de mejoras cancelado.',
}.items()})


def tr_message(message: str) -> str:
    """Translate one application-layer result message.

    ``MESSAGES`` keys are the English templates with ``{}`` placeholders.
    A concrete message ("Post-Battle #3 is still…") is matched against the
    templates by replacing each ``{}`` with a number/word wildcard, so the
    arguments are recovered and re-inserted into the Spanish template.
    Unknown messages render unchanged — never crash.
    """
    import re

    if not message or _active_locale == CANONICAL_LOCALE:
        return message
    direct = MESSAGES.get(message)
    if direct is not None:
        return direct
    for template, translated in MESSAGES.items():
        if "{}" not in template:
            continue
        pattern = "^" + "(.+?)".join(re.escape(part) for part in template.split("{}")) + "$"
        match = re.match(pattern, message, re.DOTALL)
        if match and "{}" in translated:
            try:
                return translated.format(*match.groups())
            except (IndexError, ValueError):
                continue
    return message
