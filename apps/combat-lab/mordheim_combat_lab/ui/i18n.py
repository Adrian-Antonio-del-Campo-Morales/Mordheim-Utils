"""Combat Lab interface translations; English keys are the canonical fallback."""
from __future__ import annotations

import os

CANONICAL_LOCALE = "en"
SUPPORTED_LOCALES = frozenset({"en", "es"})
_active_locale = CANONICAL_LOCALE

STRINGS: dict[str, dict[str, str]] = {'Causes Fear (already active)': {'es': 'Causa Miedo (efecto ya activo)'},
 'Stupidity — supplied individual conditions': {'es': 'Estupidez — condiciones individuales indicadas'},
 'Supplied individual facts': {'es': 'Hechos individuales aportados'},
 'Snorri: pre-battle drinking result (2-6; 1 = absent)': {'es': 'Snorri: bebida antes de la batalla (2-6; 1 '
                                                                '= ausente)'},
 '2: WS and S -1': {'es': '2: HA y F -1'},
 '3: No effect': {'es': '3: Sin efecto'},
 '4: All combatants -1 to hit': {'es': '4: Todos los combatientes -1 por impactar'},
 '5: Strength +1': {'es': '5: Fuerza +1'},
 '6: Frenzy': {'es': '6: Frenesí'},
 'Animal qualification for Tranquil Fauna': {'es': 'Categoría animal para Fauna Tranquila'},
 'Animal Handler controlled': {'es': 'Controlado por Adiestrador de Animales'},
 'Large predatory beast': {'es': 'Gran bestia depredadora'},
 'Qualified Animal Handler Leadership': {'es': 'Liderazgo del Adiestrador de Animales cualificado'},
 'Vampire bloodline': {'es': 'Estirpe vampírica'},
 'Opponent is the nominated Guiding Dream Hero': {'es': 'El adversario es el Héroe designado por Sueño Guía'},
 'Eagle companions (blank = one with Eagle Friend)': {'es': 'Compañeras águilas (vacío = una con Amiga de '
                                                            'las Águilas)'},
 'House Guard house': {'es': 'Casa de la Guardia'},
 'Fighter role': {'es': 'Tipo de guerrero'},
 'Mercenary origin': {'es': 'Origen mercenario'},
 'Other mercenary origin': {'es': 'Otro origen mercenario'},
 'Creature nature': {'es': 'Naturaleza de la criatura'},
 'Species': {'es': 'Especie'},
 'Active Command': {'es': 'Orden activa'},
 'Legal Wheelo fitting': {'es': 'Accesorio legal del Wheelo'},
 'Follower of Onogal': {'es': 'Seguidor de Onogal'},
 'Carrying an open flame': {'es': 'Porta una llama encendida'},
 'Ordinary animal': {'es': 'Animal normal'},
 'Lizardman': {'es': 'Hombre Lagarto'},
 'Vampire': {'es': 'Vampiro'},
 'Righteous Charge already qualified': {'es': 'Carga Justiciera ya habilitada'},
 'Follow Me': {'es': 'Seguidme'},
 'Ready to Die': {'es': 'Listo para morir'},
 'Living': {'es': 'Vivo'},
 'Daemon': {'es': 'Demonio'},
 'Possessed': {'es': 'Poseído'},
 'Sex (for source conditions)': {'es': 'Sexo (condiciones de la regla)'},
 'Male': {'es': 'Masculino'},
 'Female': {'es': 'Femenino'},
 'Elf identity': {'es': 'Identidad élfica'},
 'Use profile identity': {'es': 'Usar identidad del perfil'},
 'High Elf': {'es': 'Alto Elfo'},
 'Dark Elf': {'es': 'Elfo Oscuro'},
 'Neither High nor Dark Elf': {'es': 'Ni Alto Elfo ni Elfo Oscuro'},
 'Acquired Stupidity': {'es': 'Estupidez adquirida'},
 'Stupidity exemption already active': {'es': 'Exención de Estupidez ya activa'},
 'Previous Stupidity test failed': {'es': 'Chequeo anterior de Estupidez fallido'},
 'Eligible handler\'s own Leadership within 6"': {'es': 'Liderazgo propio del adiestrador válido a 6"'},
 'Brood Mentality bonus already active': {'es': 'Bonificación de Mentalidad de Prole ya activa'},
 'Leadership (blank = unknown)': {'es': 'Liderazgo (vacío = desconocido)'},
 'Save': {'es': 'Guardar'},
 'Load': {'es': 'Cargar'},
 'Scenario': {'es': 'Escenario'},
 'None': {'es': 'Ninguno'},
 'Cancel': {'es': 'Cancelar'},
 'Hero': {'es': 'Héroe'},
 'Cost': {'es': 'Coste'},
 'Equipment': {'es': 'Equipamiento'},
 'Language': {'es': 'Idioma'},
 'English': {'es': 'Inglés'},
 'EQUIPMENT': {'es': 'EQUIPAMIENTO'},
 'pending': {'es': 'pendiente'},
 'roll': {'es': 'tirada'},
 'left': {'es': 'izquierdo'},
 'right': {'es': 'derecho'},
 'both': {'es': 'ambos'},
 'Mordheim Combat Lab': {'es': 'Laboratorio de Combate Mordheim'},
 'Simulation Workbook': {'es': 'Libro de simulación'},
 'Collections ▾': {'es': 'Colecciones ▾'},
 'Mordheim Core': {'es': 'Núcleo de Mordheim'},
 'Import ▾': {'es': 'Importar ▾'},
 'Load candidate': {'es': 'Cargar candidato'},
 'Load enemy': {'es': 'Cargar rival'},
 'Candidate': {'es': 'Candidato'},
 'Enemy': {'es': 'Rival'},
 'Improvements': {'es': 'Mejoras'},
 'Weapons': {'es': 'Armas'},
 'House Rules': {'es': 'Reglas de la casa'},
 'Active runtime': {'es': 'Motor activo'},
 'Mordheim close combat · KB-backed legal equipment · deterministic seed support': {'es': 'Combate cuerpo a '
                                                                                          'cuerpo de '
                                                                                          'Mordheim · equipo '
                                                                                          'legal respaldado '
                                                                                          'por la base de '
                                                                                          'conocimiento · '
                                                                                          'soporte de '
                                                                                          'semilla '
                                                                                          'determinista'},
 'Configure the candidate and enemy, then use an analysis tab.': {'es': 'Configura el candidato y el rival y '
                                                                        'usa una pestaña de análisis.'},
 'Ready for an analysis with the selected fighters.': {'es': 'Listo para un análisis con los luchadores '
                                                             'seleccionados.'},
 'Configuration error: {}': {'es': 'Error de configuración: {}'},
 'Save Mordheim Combat Lab workbook': {'es': 'Guardar libro de Mordheim Combat Lab'},
 'Load Mordheim Combat Lab workbook': {'es': 'Cargar libro de Mordheim Combat Lab'},
 'Workbook save error: {}': {'es': 'Error al guardar el libro: {}'},
 'Saved workbook: {}': {'es': 'Libro guardado: {}'},
 'Workbook load error: {}': {'es': 'Error al cargar el libro: {}'},
 'Loaded {} : {}': {'es': 'Cargado {}: {}'},
 'Choose a warrior and their legal combat configuration.': {'es': 'Elige un guerrero y su configuración de '
                                                                  'combate legal.'},
 'Configure the opposing warrior used by every simulation and analysis.': {'es': 'Configura el guerrero '
                                                                                 'rival usado por cada '
                                                                                 'simulación y análisis.'},
 'The executable rules are selected by the knowledge base. This version deliberately does not restore the legacy checkboxes: they altered the retired engine and could silently produce a duel that the new runtime cannot represent.': {'es': 'Las '
                                                                                                                                                                                                                                               'reglas '
                                                                                                                                                                                                                                               'ejecutables '
                                                                                                                                                                                                                                               'las '
                                                                                                                                                                                                                                               'selecciona '
                                                                                                                                                                                                                                               'la '
                                                                                                                                                                                                                                               'base '
                                                                                                                                                                                                                                               'de '
                                                                                                                                                                                                                                               'conocimiento. '
                                                                                                                                                                                                                                               'Esta '
                                                                                                                                                                                                                                               'versión '
                                                                                                                                                                                                                                               'no '
                                                                                                                                                                                                                                               'restaura '
                                                                                                                                                                                                                                               'deliberadamente '
                                                                                                                                                                                                                                               'las '
                                                                                                                                                                                                                                               'casillas '
                                                                                                                                                                                                                                               'heredadas: '
                                                                                                                                                                                                                                               'alteraban '
                                                                                                                                                                                                                                               'el '
                                                                                                                                                                                                                                               'motor '
                                                                                                                                                                                                                                               'retirado '
                                                                                                                                                                                                                                               'y '
                                                                                                                                                                                                                                               'podían '
                                                                                                                                                                                                                                               'producir '
                                                                                                                                                                                                                                               'en '
                                                                                                                                                                                                                                               'silencio '
                                                                                                                                                                                                                                               'un '
                                                                                                                                                                                                                                               'duelo '
                                                                                                                                                                                                                                               'que '
                                                                                                                                                                                                                                               'el '
                                                                                                                                                                                                                                               'nuevo '
                                                                                                                                                                                                                                               'motor '
                                                                                                                                                                                                                                               'no '
                                                                                                                                                                                                                                               'puede '
                                                                                                                                                                                                                                               'representar.'},
 'Identity and Source': {'es': 'Identidad y origen'},
 'Name:': {'es': 'Nombre:'},
 'Warband:': {'es': 'Banda:'},
 'Warrior:': {'es': 'Guerrero:'},
 'BASIC ATTRIBUTES': {'es': 'ATRIBUTOS BÁSICOS'},
 'Main Hand': {'es': 'Mano principal'},
 'Free hand': {'es': 'Mano libre'},
 'No armour': {'es': 'Sin armadura'},
 'No poison': {'es': 'Sin veneno'},
 'No helmet': {'es': 'Sin yelmo'},
 'No preparation': {'es': 'Sin preparación'},
 'Off Hand': {'es': 'Mano secundaria'},
 'Armour': {'es': 'Armadura'},
 'SKILLS': {'es': 'HABILIDADES'},
 'Weapon': {'es': 'Arma'},
 'Weapon analysis': {'es': 'Análisis de armas'},
 'Compare weapons': {'es': 'Comparar armas'},
 'No selectable skills are available for this profile.': {'es': 'No hay habilidades seleccionables '
                                                                'disponibles para este perfil.'},
 'Material': {'es': 'Material (equipo)'},
 'Poison': {'es': 'Veneno'},
 'Free selection loaded · all implemented duel skills are available.': {'es': 'Selección libre cargada · '
                                                                              'todas las habilidades de '
                                                                              'duelo implementadas están '
                                                                              'disponibles.'},
 'Equipment analysis': {'es': 'Análisis de equipamiento'},
 'The selected main weapon and skills remain fixed while legal equipment configurations are simulated.': {'es': 'El '
                                                                                                                'arma '
                                                                                                                'principal '
                                                                                                                'y '
                                                                                                                'las '
                                                                                                                'habilidades '
                                                                                                                'elegidas '
                                                                                                                'permanecen '
                                                                                                                'fijas '
                                                                                                                'mientras '
                                                                                                                'se '
                                                                                                                'simulan '
                                                                                                                'configuraciones '
                                                                                                                'de '
                                                                                                                'equipo '
                                                                                                                'legales.'},
 'Simulations': {'es': 'Simulaciones'},
 'Battery workers (-1 = automatic, 0 = sequential)': {'es': 'Workers de batería (-1 = automático, 0 = '
                                                            'secuencial)'},
 'Compare equipment': {'es': 'Comparar equipamiento'},
 'Maximum changed slots': {'es': 'Máximo de ranuras modificadas'},
 "Compare the candidate's legal off-hand and armour configurations.": {'es': 'Compara las configuraciones '
                                                                             'legales de mano secundaria y '
                                                                             'armadura del candidato.'},
 'Item {}': {'es': 'Objeto {}'},
 'Best Result': {'es': 'Mejor resultado'},
 'MOTTA Score': {'es': 'Puntuación MOTTA'},
 'Equipment Used': {'es': 'Equipamiento usado'},
 'Off hand': {'es': 'Mano secundaria'},
 'Helmet': {'es': 'Yelmo'},
 'Preparation': {'es': 'Preparación'},
 'Main material': {'es': 'Material principal'},
 'Main poison': {'es': 'Veneno principal'},
 'Off-hand material': {'es': 'Material de la mano secundaria'},
 'Off-hand poison': {'es': 'Veneno de la mano secundaria'},
 'Current configuration': {'es': 'Configuración actual'},
 'Comparing {} equipment configurations…': {'es': 'Comparando {} configuraciones de equipamiento…'},
 'Compared {} configurations across {} duels.': {'es': 'Se compararon {} configuraciones en {} duelos.'},
 ' Skipped {} invalid configurations.': {'es': ' Se omitieron {} configuraciones no válidas.'},
 'Complete': {'es': 'Completo'},
 'Error': {'es': 'Error del análisis'},
 'Cancelled': {'es': 'Cancelado'},
 'Equipment analysis error: {}': {'es': 'Error del análisis de equipamiento: {}'},
 'Equipment analysis cancelled.': {'es': 'Análisis de equipamiento cancelado.'},
 'Improvement analysis': {'es': 'Análisis de mejoras'},
 'Compare improvements': {'es': 'Comparar mejoras'},
 'Compare each legal additional skill against the candidate baseline.': {'es': 'Compara cada habilidad '
                                                                               'adicional legal contra la '
                                                                               'línea base del candidato.'},
 'Improvement {}': {'es': 'Mejora {}'},
 'Number of improvements:': {'es': 'Número de mejoras:'},
 'Skills ({} / {})': {'es': 'Habilidades ({} / {})'},
 'Select all': {'es': 'Seleccionar todas'},
 'Select none': {'es': 'Deseleccionar todas'},
 'Select at least one improvement to compare.': {'es': 'Selecciona al menos una mejora para comparar.'},
 'Not enough selected skills for {} improvements.': {'es': 'No hay suficientes habilidades seleccionadas '
                                                           'para {} mejoras.'},
 'Each row applies the selected profile-legal skills to the candidate configuration.': {'es': 'Cada fila '
                                                                                              'aplica al '
                                                                                              'candidato las '
                                                                                              'habilidades '
                                                                                              'legales del '
                                                                                              'perfil '
                                                                                              'seleccionadas.'},
 'Baseline: {}% candidate win rate. Compared {} combinations across {} duels.': {'es': 'Línea base: {}% de '
                                                                                       'victorias del '
                                                                                       'candidato. Se '
                                                                                       'compararon {} '
                                                                                       'combinaciones en {} '
                                                                                       'duelos.'},
 'Comparing {} improvement combinations…': {'es': 'Comparando {} combinaciones de mejoras…'},
 'Weapons ({} / {})': {'es': 'Armas ({} / {})'},
 'Select at least one weapon to compare.': {'es': 'Selecciona al menos un arma para comparar.'},
 'Comparing {} weapons with {} duels each…': {'es': 'Comparando {} armas con {} duelos cada una…'},
 'Compared {} weapons across {} duels.': {'es': 'Se compararon {} armas en {} duelos.'},
 'Each selected main weapon is simulated against the current enemy configuration.': {'es': 'Cada arma '
                                                                                           'principal '
                                                                                           'seleccionada se '
                                                                                           'simula contra la '
                                                                                           'configuración '
                                                                                           'enemiga actual.'},
 'Weapon analysis error: {}': {'es': 'Error del análisis de armas: {}'},
 'Weapon analysis cancelled.': {'es': 'Análisis de armas cancelado.'},
 "Configure the duel, then compare the candidate's legal weapons.": {'es': 'Configura el duelo y compara las '
                                                                           'armas legales del candidato.'},
 'Improvement analysis error: {}': {'es': 'Error del análisis de mejoras: {}'},
 'Improvement analysis cancelled.': {'es': 'Análisis de mejoras cancelado.'}}


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

