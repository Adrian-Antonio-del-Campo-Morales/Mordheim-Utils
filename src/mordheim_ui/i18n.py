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
``es`` value (``tests/ui/test_ui_i18n.py`` enforces it).

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
    "Export": {"es": "Exportar"},
    "New Campaign…": {"es": "Nueva campaña…"},
    "Manage Campaigns…": {"es": "Gestionar campañas…"},
    "Open campaign example": {"es": "Abrir ejemplo de campaña"},
    "Open creation example": {"es": "Abrir ejemplo de creación"},
    "CAMPAIGN TIMELINE": {"es": "LÍNEA TEMPORAL DE LA CAMPAÑA"},
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
    "Commit Skill": {"es": "Confirmar habilidad"},
    "Commit Spell": {"es": "Confirmar conjuro"},
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
    "Warband Rating": {"es": "Valoración de la banda"},
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
    "All files": {"es": "Todos los archivos"},
    "JSON": {"es": "JSON files"},
    "Markdown": {"es": "Markdown files"},
    "Text": {"es": "Texto"},
    # ------------------------------------------------------------------
    # Settings & rules placeholders (placeholder_view.py)
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
