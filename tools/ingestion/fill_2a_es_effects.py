"""Fill the missing Spanish effect translations in the 2A staging catalog items.

Every item keeps its canonical English ``effect``; this script inserts an
``effect_i18n:`` block (folded ``es: >-`` scalar) after each effect — both the
item-level effect and every nested ``special_rules`` entry. Terminology follows
the names already established in the staging packages and the active KB
glossary (Fuera de Combate, tirada de heridas, salvación por armadura,
combate cuerpo a cuerpo, ...).

Usage::

    python tools/ingestion/fill_2a_es_effects.py           # dry run
    python tools/ingestion/fill_2a_es_effects.py --write   # apply
"""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[2] / "sources" / "2A" / "catalog" / "items"

# Keys are "<file>:<item_id>" for the item-level effect and
# "<file>:<item_id>:<rule_id>" for nested special_rules entries.
TRANSLATIONS: dict[str, str] = {
    # --- druchii-equipment.yaml ---
    "druchii-equipment.yaml:darksteel_blade": (
        "Las armas de Acero Oscuro se forjan en la ciudad de Hag Graef, el Risco "
        "Oscuro. Están forjadas con acero negro, una forma rara de acero que se "
        "encuentra en las profundidades de las montañas que rodean la ciudad, "
        "empleando una técnica ancestral conocida únicamente por los Elfos "
        "Oscuros. Las armas con hojas de Acero Oscuro tienen protuberancias "
        "afiladas y bordes dentados, que infligen graves daños al oponente. "
        "Cualquier héroe Druchii puede usar un arma de combate cuerpo a cuerpo "
        "con hoja de Acero Oscuro. Conseguirla, sin embargo, no es tarea fácil. "
        "Alcance: combate cuerpo a cuerpo. Fuerza: como el usuario. Reglas "
        "Especiales: Daño crítico, Filo cruel."
    ),
    "druchii-equipment.yaml:darksteel_blade:critical-damage": (
        "Las armas de Acero Oscuro infligen graves daños a sus oponentes. Al "
        "tirar en la tabla de impactos críticos, un arma de Acero Oscuro suma "
        "+1 al resultado."
    ),
    "druchii-equipment.yaml:darksteel_blade:wicked-edge": (
        "Las armas de Acero Oscuro están tachonadas de protuberancias afiladas "
        "y bordes dentados que infligen graves daños al oponente. Un resultado "
        "de 2-4 en la tabla de heridas es un resultado de aturdido."
    ),
    # --- grave-robbers-equipment.yaml ---
    "grave-robbers-equipment.yaml:hooded_lantern_rig": (
        "Permite al Saqueador de Tumbas realizar su trabajo en privado y con "
        "las manos libres, disponiendo al mismo tiempo de una fuente de luz."
    ),
    "grave-robbers-equipment.yaml:hooded_lantern_rig:concealed-light": (
        "Proporciona luz como un farol normal, pero impide que las miniaturas "
        "enemigas la vean."
    ),
    "grave-robbers-equipment.yaml:hooded_lantern_rig:free-hand": (
        "El arnés al que se sujeta el farol con capuchón deja al Saqueador las "
        "manos libres para ejercer su oficio."
    ),
    "grave-robbers-equipment.yaml:pry_bar": (
        "Aunque funciona como una maza en todos los sentidos, la palanqueta "
        "permite al Saqueador parar ataques. Alcance: combate cuerpo a cuerpo. "
        "Fuerza: como el usuario. Reglas Especiales: Parada."
    ),
    "grave-robbers-equipment.yaml:pry_bar:parry": (
        "Aunque funciona como una maza en todos los sentidos, la palanqueta "
        "permite al Saqueador parar ataques."
    ),
    "grave-robbers-equipment.yaml:surgeons_journal": (
        "Escrito por quienes han abierto a demasiados heridos, el Diario aporta "
        "al Médico un conocimiento más profundo."
    ),
    "grave-robbers-equipment.yaml:surgeons_journal:skilled-hand": (
        "Un Médico equipado con el Diario puede modificar en +1/-1 un único "
        "dado de la tirada de Herida Grave de un modelo amistoso, en lugar de "
        "usar su habilidad de Curandero."
    ),
    "grave-robbers-equipment.yaml:finger_pendant": (
        "Un sombrío trofeo que lucen los Saqueadores de Tumbas. (No se imprime "
        "texto descriptivo para este objeto más allá de su regla especial.)"
    ),
    "grave-robbers-equipment.yaml:finger_pendant:death-ward": (
        "Concede una salvación de un solo uso de 5+ contra la magia "
        "Necromántica o de Artes Oscuras."
    ),
    # --- masters-of-horror-equipment.yaml ---
    "masters-of-horror-equipment.yaml:chainsaw_sword": (
        "Una pesadilla mecánica fruto de la locura, este estruendoso artilugio "
        "desgarra la armadura con facilidad. Alcance: combate cuerpo a cuerpo. "
        "Fuerza: como el usuario. Reglas Especiales: Miedo, Trituradora."
    ),
    "masters-of-horror-equipment.yaml:chainsaw_sword:fear": (
        "Increíblemente ruidosa y escupiendo un humo verdoso enfermizo, esta "
        "arma hace temblar incluso a los soldados más curtidos. Una miniatura "
        "que lleve una Espada Motosierra causa Miedo."
    ),
    "masters-of-horror-equipment.yaml:chainsaw_sword:shredder": (
        "La Espada Motosierra desgarra y mastica la armadura como si fuera "
        "trapo. Todos los golpes de una Espada Motosierra reciben -2 a la "
        "salvación por armadura."
    ),
    "masters-of-horror-equipment.yaml:electric_trident": (
        "Nada tan estremecedor como un pinchazo de esta pequeña delicia. "
        "Alcance: combate cuerpo a cuerpo. Fuerza: como el usuario. Reglas "
        "Especiales: ¡Zzap!, Conmocionante, Clavo en la Bota."
    ),
    "masters-of-horror-equipment.yaml:electric_trident:zzap": (
        "El Tridente Eléctrico es tan aturdidor que una miniatura herida por "
        "él cuenta como Aturdida con un resultado de 2-4."
    ),
    "masters-of-horror-equipment.yaml:electric_trident:shocking": (
        "Con un 6 natural por impactar seguido de un 6 natural por herir, el "
        "Tridente Eléctrico descarga un campo de 2\" alrededor del objetivo. "
        "Todas las miniaturas (salvo el portador del arma) sufren un impacto "
        "de F3."
    ),
    "masters-of-horror-equipment.yaml:electric_trident:nail-in-boot": (
        "Si en la tirada por impactar con el Tridente sale un 1 en 1D6, el "
        "portador sufre un impacto de F3."
    ),
    "masters-of-horror-equipment.yaml:repeater_pistol_moh": (
        "Un arma peligrosa para quienes están en ambos extremos de la pistola. "
        "Siempre acaba con ¡un estampido! Alcance: 8\". Fuerza: 4. Reglas "
        "Especiales: -2 Salvación por Armadura, Demasiados Retoques, "
        "Repetición. Esta es la variante de los Maestros del Horror de la "
        "Pistola de Repetición del puesto comercial; tiene mayor alcance (8\" "
        "en lugar de 6\") y mecánicas únicas de retoques y repetición."
    ),
    "masters-of-horror-equipment.yaml:repeater_pistol_moh:save-modifier": (
        "Las pistolas perforan la armadura aún mejor de lo que sugiere su "
        "Fuerza de 4. Una miniatura que sufra una herida de una Pistola de "
        "Repetición debe hacer su salvación por armadura con -2."
    ),
    "masters-of-horror-equipment.yaml:repeater_pistol_moh:too-much-tinkering": (
        "La Pistola de Repetición es un arma fuertemente modificada. Para "
        "representar su mecánica inestable, cada vez que se aprieta el gatillo "
        "debes tirar 1D6: con un 4+ la pistola funciona bien; con un 2-3 la "
        "pistola no hace nada; con un 1, tira en la tabla de «Fallo de "
        "disparo»."
    ),
    "masters-of-horror-equipment.yaml:repeater_pistol_moh:repeater": (
        "La Pistola de Repetición puede disparar más de una vez durante la "
        "fase de Disparo. Por cada disparo adicional debes tirar 1D6 con -1 en "
        "la tabla anterior. Por ejemplo, para un disparo necesitas un 4+, y un "
        "1 obliga a tirar en la tabla de Fallo de Disparo; para un segundo "
        "disparo necesitas un 5+, y un 1-2 obliga a tirar en la tabla de fallo "
        "de disparo. Por supuesto, es imposible intentar más de 3 disparos por "
        "ronda."
    ),
    # --- necrarch-equipment.yaml ---
    "necrarch-equipment.yaml:staff_of_damnation": (
        "El arma predilecta de estos magos ancestrales, el Bastón de la "
        "Perdición les permite descargar magia letal contra sus enemigos. "
        "Alcance: combate cuerpo a cuerpo. Fuerza: como el usuario. Reglas "
        "Especiales: A Dos Manos, Pozo de magia."
    ),
    "necrarch-equipment.yaml:staff_of_damnation:two-handed": (
        "Como el Bastón de la Perdición requiere dos manos para empuñarlo, una "
        "miniatura equipada con él no puede usar escudo, broquel ni arma "
        "secundaria en combate cuerpo a cuerpo. Si la miniatura lleva escudo, "
        "sigue recibiendo el bonificador de +1 a su salvación por armadura "
        "contra disparos."
    ),
    "necrarch-equipment.yaml:staff_of_damnation:magic-well": (
        "Un Vampiro Necrarca puede lanzar un hechizo dentro del Bastón de la "
        "Perdición durante su fase de Magia en lugar de lanzarlo con "
        "normalidad. Si el lanzamiento tiene éxito, el hechizo queda "
        "almacenado en el bastón. El hechizo puede liberarse en una fase de "
        "Disparo posterior en lugar de lanzar otro hechizo."
    ),
    "necrarch-equipment.yaml:unholy_relic": (
        "Un artefacto blasfemo que portan los sirvientes de los Necrarcas. (La "
        "página de origen no imprime más texto de reglas para este objeto; "
        "solo aparece en la Lista de Equipo de Héroes por 15 coronas.)"
    ),
    "necrarch-equipment.yaml:damned_book": (
        "Escrito con la sangre de doncellas elfas y sobre la carne de "
        "vírgenes, el Libro Maldito pervierte el espacio a su alrededor. Aura "
        "Maldita: una miniatura que porte el Libro Maldito hace que todas las "
        "miniaturas enemigas a 2 pulgadas sufran una penalización de -1 por "
        "impactar en combate cuerpo a cuerpo."
    ),
    "necrarch-equipment.yaml:damned_book:cursed-aura": (
        "Una miniatura que porte el Libro Maldito hace que todas las "
        "miniaturas enemigas a 2 pulgadas sufran una penalización de -1 por "
        "impactar en combate cuerpo a cuerpo."
    ),
    # --- protectorate-equipment.yaml ---
    "protectorate-equipment.yaml:shield_of_sigmar": (
        "Transmitidos a través de la iglesia, estos escudos fueron portados "
        "por los hombres que lideró el propio Martillo de los Héroes. Un aura "
        "rodea estos escudos, otorgando a su portador una protección "
        "sobrenatural. Quien se proteja con un Escudo de Sigmar tiene una "
        "salvación especial de 6+ contra todos los ataques a distancia. "
        "Además, el peso del escudo parece disminuir: no se aplica la "
        "penalización de -1 por llevar escudo con Armadura Pesada. Salvación "
        "por Armadura: 6."
    ),
    "protectorate-equipment.yaml:shield_of_sigmar:shield-of-faith": (
        "Quien se proteja con un Escudo de Sigmar tiene una salvación especial "
        "de 6+ contra todos los ataques a distancia, y no se aplica la "
        "penalización de -1 por llevar escudo con Armadura Pesada."
    ),
    "protectorate-equipment.yaml:blessed_bolts": (
        "Bendecidas por el Sacerdote Guerrero y sus Acólitos, las Saetas "
        "Bendecidas pueden dispararse contra los enemigos de Sigmar. Cualquier "
        "ser Caótico, ya sea No Muerto, infundido por el Caos (mutantes o "
        "Endemoniados) o Retorcedor de la Magia, sufre enormemente con estos "
        "proyectiles: suma +1F al arma cuando se dispara contra ese tipo de "
        "objetivo. Alcance: como el arma. Fuerza: como el arma. Reglas "
        "Especiales: Sagrada."
    ),
    "protectorate-equipment.yaml:blessed_bolts:holy": (
        "Suma +1F al arma cuando se dispara contra cualquier ser Caótico (No "
        "Muertos, mutantes infundidos por el Caos o Endemoniados, o "
        "Retorcedores de la Magia)."
    ),
    # --- snotlings-equipment.yaml ---
    "snotlings-equipment.yaml:small_pebble": (
        "Alcance: 6\". Fuerza: como el usuario. Regla Especial: Arma "
        "arrojadiza, +1 Perforación de Armadura Enemiga, Fácil de Encontrar."
    ),
    "snotlings-equipment.yaml:small_pebble:thrown-weapon": (
        "Las miniaturas que usan piedrecitas no sufren penalizaciones por "
        "alcance ni por movimiento, ya que estas armas están perfectamente "
        "equilibradas para el lanzamiento. No pueden usarse en combate cuerpo "
        "a cuerpo."
    ),
    "snotlings-equipment.yaml:small_pebble:enemy-armour-piercing": (
        "Cualquier miniatura herida con una Piedrecita obtiene +1 a su "
        "salvación por armadura."
    ),
    "snotlings-equipment.yaml:small_pebble:easy-to-find": (
        "¡Encontrar una Piedrecita es fácil! Son gratis para los miembros de "
        "la banda Snotling. Si se pierde, puede encontrarse otra sin coste. "
        "Además, las Piedrecitas NO cuentan para el número máximo de armas de "
        "misil que un guerrero puede llevar."
    ),
    "snotlings-equipment.yaml:slingshot": (
        "Alcance máximo: 18\". Fuerza: 2. Regla Especial: Disparar dos veces a "
        "media distancia."
    ),
    "snotlings-equipment.yaml:slingshot:fire-twice-at-half-range": (
        "Un tirador con hondita puede disparar dos veces en la fase de "
        "Disparo si no se mueve en la fase de Movimiento. Pero no puede "
        "disparar a más de media distancia (9\") si dispara dos veces. Si la "
        "miniatura dispara dos veces, cada disparo recibe -1 por impactar."
    ),
    "snotlings-equipment.yaml:power_squig": (
        "El Squig de Poder funciona exactamente igual que un Familiar "
        "disponible para todas las bandas en la Lista de Equipo del Guerrero "
        "Sombra. ¡Solo que es más snotlinguesco!"
    ),
    # --- sorcerous-society-equipment.yaml ---
    "sorcerous-society-equipment.yaml:wizards_staff": (
        "A muchos Magos les resulta práctico el bastón tanto para sus largos "
        "viajes como para defenderse cuando el uso de sus artes mágicas podría "
        "levantar sospechas. Alcance: combate cuerpo a cuerpo. Fuerza: como el "
        "usuario. Reglas Especiales: Parada, A Dos Manos, Conmoción."
    ),
    "sorcerous-society-equipment.yaml:wizards_staff:parry": (
        "Un guerrero armado con un Bastón de Mago puede intentar Parar un "
        "golpe, igual que con una espada."
    ),
    "sorcerous-society-equipment.yaml:wizards_staff:two-handed": (
        "Una miniatura que use un Bastón de Mago no puede usar escudo, broquel "
        "ni arma adicional en combate cuerpo a cuerpo. Si la miniatura lleva "
        "escudo, recibe un bonificador de +1 a su salvación por armadura "
        "contra ataques de disparo."
    ),
    "sorcerous-society-equipment.yaml:wizards_staff:concussion": (
        "Al usar un Bastón de Mago, un resultado de 2-4 se considera aturdido "
        "al tirar en la tabla de heridas."
    ),
    "sorcerous-society-equipment.yaml:society_familiar": (
        "Los Familiares son animales que comparten una conexión especial con "
        "un Mago concreto. Cada Mago solo puede poseer un Familiar. Aunque los "
        "Familiares se consideran equipo, también son criaturas vivientes. Si "
        "uno queda Fuera de Combate durante una batalla, tira heridas como un "
        "Secuaz. Sin embargo, no cuentan para el tamaño máximo de la banda ni "
        "para las tiradas de Huida. Si el Familiar de un Mago muere o lo "
        "abandona, puede buscar un reemplazo usando las reglas de rareza. "
        "Perfiles — Perro: M6 HA4 F3 R3 H1 I4 A1 Ld5; Gato: M6 HA4 F2 R2 H1 I6 "
        "A1 Ld5; Cuervo: M2 HA2 F1 R1 H1 I4 A1 Ld5; Víbora: M3 HA4 F2/4* R1 H1 "
        "I5 A1 Ld5. Objetivo Pequeño: las miniaturas que disparan a un "
        "Familiar sufren -1 a su HP debido al pequeño tamaño del objetivo. "
        "(* Víbora: F2, o F4 contra objetivos susceptibles al veneno.)"
    ),
    "sorcerous-society-equipment.yaml:society_familiar:small-target": (
        "Las miniaturas que disparan a un Familiar sufren -1 a su HP debido al "
        "pequeño tamaño del objetivo."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:dog-loyal": (
        "Un Familiar Perro que permanezca a 6 pulgadas de su mago es inmune al "
        "miedo."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:dog-sniff": (
        "El Perro tiene un olfato muy fino y puede usarse para ayudar durante "
        "la exploración. La banda puede tirar un dado adicional y usar el "
        "resultado de este dado en lugar del de uno de los héroes "
        "supervivientes."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:cat-go-for-the-eyes": (
        "Si ambos ataques hieren con éxito en la misma ronda, la miniatura "
        "enemiga queda cegada y no puede devolver los golpes hasta su "
        "siguiente turno. Si solo uno de los ataques hiere, la miniatura "
        "afectada sufre -1 a HA y HP hasta el comienzo de su siguiente turno."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:raven-fly": (
        "Puede volar hasta 12 pulgadas a cualquier punto de la mesa."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:raven-i-see-you": (
        "Los hechizos pueden lanzarse sobre miniaturas que estén dentro del "
        "alcance del Mago o del Cuervo. Por tanto, un hechizo con alcance de "
        "12 pulgadas puede lanzarse sobre miniaturas a 12 pulgadas de "
        "cualquiera de los dos modelos."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:viper-poison": (
        "Si la Víbora saca un 6 por impactar, el ataque hiere automáticamente "
        "sin salvación por armadura. Cualquier otro impacto exitoso contra un "
        "objetivo susceptible al veneno inflige un impacto de F4. Si la "
        "criatura es inmune al veneno, considera el ataque como F2."
    ),
    "sorcerous-society-equipment.yaml:society_familiar:viper-coiled-and-ready": (
        "No es fácil pillarse a una Víbora desprevenida. Una Víbora tiene "
        "Reflejos Súbitos."
    ),
    # --- survivors-of-strigos-equipment.yaml ---
    "survivors-of-strigos-equipment.yaml:chest_talon": (
        "Diseñadas para el Domnu, estas armas a dos manos en forma de pico son "
        "ideales para rematar a los sedientos de sangre von Carstein. Alcance: "
        "combate cuerpo a cuerpo. Fuerza: como el usuario +1. Reglas "
        "Especiales: A Dos Manos, Perforacorazones."
    ),
    "survivors-of-strigos-equipment.yaml:chest_talon:two-handed": (
        "Como la Garra de Pecho requiere dos manos para empuñarla, una "
        "miniatura equipada con ella no puede usar escudo, broquel ni arma "
        "secundaria en combate cuerpo a cuerpo. Si la miniatura lleva escudo, "
        "sigue recibiendo el bonificador de +1 a su salvación por armadura "
        "contra disparos."
    ),
    "survivors-of-strigos-equipment.yaml:chest_talon:heart-pierce": (
        "Tal es el diseño destructivo del arma que suma +1 por herir contra un "
        "sediento de sangre."
    ),
    "survivors-of-strigos-equipment.yaml:black_gold_wristbands": (
        "Creados con la magia oscura de épocas pasadas, los brazaletes "
        "permiten a quien los lleva protegerse mejor del fuego de misiles. "
        "Acelerado: una miniatura que lleve Brazaletes de Oro Negro obtiene "
        "una salvación de 6+ contra todo fuego de misiles, incluido el "
        "mágico. Esta habilidad se acumula con la habilidad de Esquiva."
    ),
    "survivors-of-strigos-equipment.yaml:ring_of_strigos": (
        "Forjados con la sangre de los Necrarcas, estos anillos adornaron "
        "antaño los dedos de la nobleza de Strigos. Barrera Arcana: una "
        "miniatura que lleve un Anillo de Strigos obtiene una salvación de 6+ "
        "contra todos los hechizos de los que sea objetivo o se vea afectada."
    ),
    "survivors-of-strigos-equipment.yaml:cursed_book": (
        "Escrito por Videntes rencorosos, el Libro Maldito ofrece a su portador "
        "cierta protección contra quienes quieran dañarlo. Aura Maldita: una "
        "miniatura que porte el Libro Maldito hace que todas las miniaturas "
        "enemigas a 2\" sufran una penalización de -1 por impactar en combate "
        "cuerpo a cuerpo."
    ),
    # --- vampire-hunter-equipment.yaml ---
    "vampire-hunter-equipment.yaml:silver_tip_stake": (
        "Tal es el poder destructivo de la plata sobre la forma de un Vampiro "
        "que la estaca de punta de plata suma +1 a la tirada de heridas cuando "
        "causa una herida. Alcance: combate cuerpo a cuerpo. Fuerza: como el "
        "usuario. Reglas Especiales: Buscacorazones."
    ),
    "vampire-hunter-equipment.yaml:silver_tip_stake:heart-seeker": (
        "La estaca de punta de plata suma +1 a la tirada de heridas cuando "
        "causa una herida."
    ),
    "vampire-hunter-equipment.yaml:throat_guard": (
        "Como los vampiros de Sylvania dependen de desdichadas víctimas "
        "humanas para saciar su sed de sangre, es prudente proteger las zonas "
        "vulnerables. Así, el Protector de Garganta permite al Slayer tener la "
        "tranquilidad de saber que su sangre permanecerá en sus venas. Todas "
        "las tiradas de heridas causadas por un Vampiro tienen una salvación "
        "especial de 6+ mientras se lleve este equipo. Esta salvación no se ve "
        "modificada por la Fuerza, pero puede evitarse con críticos que "
        "ignoren la armadura. No añade ningún modificador a la salvación por "
        "armadura, y puede llevarse solo o combinado con armadura ligera o "
        "pesada."
    ),
    "vampire-hunter-equipment.yaml:throat_guard:life-saver": (
        "Todas las tiradas de heridas causadas por un Vampiro tienen una "
        "salvación especial de 6+ mientras se lleve este equipo. La salvación "
        "no se ve modificada por la Fuerza, pero puede evitarse con críticos "
        "que ignoren la armadura. No añade ningún modificador a la salvación "
        "por armadura."
    ),
}


def wrap(text: str, indent: int) -> list[str]:
    pad = " " * indent
    return textwrap.fill(" ".join(text.split()), width=100,
                         initial_indent=pad, subsequent_indent=pad).splitlines()


def fill_file(path: Path, write: bool) -> list[str]:
    fn = path.name
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    filled: list[str] = []
    current_item: str | None = None
    current_rule: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        item_m = _match(line, 0)          # "- id: x" (item under items:)
        rule_m = _match(line, 2)          # "  - id: x" (nested special_rules)
        if item_m:
            current_item, current_rule = item_m, None
        elif rule_m:
            current_rule = rule_m
        eff_m = _effect_match(line)
        if eff_m:
            indent, kind = eff_m
            j = _effect_block_end(lines, i, indent)
            key = None
            if kind == "item" and current_item:
                key = f"{fn}:{current_item}"
            elif kind == "rule" and current_item and current_rule:
                key = f"{fn}:{current_item}:{current_rule}"
            block = lines[i:j]
            has_i18n = any("effect_i18n:" in l for l in block)
            text = TRANSLATIONS.get(key) if key else None
            if text and not has_i18n:
                out.extend(lines[i:j])
                out.append(f"{' ' * indent}effect_i18n:")
                out.append(f"{' ' * (indent + 2)}es: >-")
                out.extend(wrap(text, indent + 4))
                filled.append(key)
            else:
                out.extend(lines[i:j])
            i = j
            continue
        out.append(line)
        i += 1
    if filled and write:
        # newline="\n": the maintained YAML is LF-only (see .gitattributes).
        path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    return filled


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _match(line: str, pad: int) -> str | None:
    """Match '{pad}spaces- id: <id>' and return the id."""
    prefix = " " * pad + "- id: "
    if line.startswith(prefix):
        rest = line[len(prefix):].strip()
        if rest and " " not in rest and ":" not in rest:
            return rest
    return None


def _effect_match(line: str) -> tuple[int, str] | None:
    """Match an effect line at item (2) or rule (4) indent.

    Handles both folded scalars (``effect: >-``) and single-line scalars
    (``effect: Some text.``).
    """
    stripped = line.strip()
    if not stripped.startswith("effect:"):
        return None
    indent = _indent(line)
    if indent not in (2, 4):
        return None
    return indent, "item" if indent == 2 else "rule"


def _effect_block_end(lines: list[str], start: int, indent: int) -> int:
    """Return the line index just past the effect scalar starting at ``start``."""
    j = start + 1
    while j < len(lines):
        nxt = lines[j]
        if nxt.strip() == "" or _indent(nxt) > indent:
            j += 1
        else:
            break
    return j


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply (default: dry run)")
    args = parser.parse_args()
    total = 0
    for path in sorted(CATALOG.glob("*.yaml")):
        filled = fill_file(path, args.write)
        total += len(filled)
        if filled:
            print(f"{path.name}: {len(filled)}")
            for key in filled:
                print(f"  {key}")
    print(f"{'filled' if args.write else 'would fill'} {total} effect translation(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
