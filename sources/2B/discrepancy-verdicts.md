# Veredictos sobre las discrepancias de fuente señaladas en la revisión de equivalencia

Fecha: 2026-09-14. Cada caso se verificó contra el PDF original (cacheado en
`build/cache/2b-pdfs/`), no contra la transcripción 2B ni contra la KB.

## 1. Vomit Attack — KEP "S8" vs KB "S5" → **ERROR DE TRANSCRIPCIÓN; corregido a S5**

- Fuente: `crooked-moon-kep.pdf`, página impresa 7 (índice 6), bloque del Troll.
- El PDF de KEP es un escaneo sin capa de texto; el texto cacheado provenía del OCR
  antiguo, que devolvía `WITHASTRENTHF ANDIKNREARMURAVES` (el dígito se perdía) o
  `WITHASTRENTHFSAND...` (el dígito se leía como "S").
- Verificación a 300 dpi con re-OCR + recorte ampliado ×4 con Otsu sobre la línea:
  `THAT AUTOMATKALLY HIT> WITH A STRENTH F 5 AN IKNRE> ARMUR >AVE>` — el dígito es
  inequívocamente **5** (conf. 0.92–0.98 en tres pasadas independientes).
- Corresponde además al sentido del juego: la KB (`shared-rule.vomit-attack`) y el KAZ
  (`night-goblins-kaz.txt` línea 1907, "Strength of 5") imprimen 5.
- **Acción aplicada:** `crooked-moon-kep/special-rules.yaml` corregido (effect e
  effect_i18n: "Strength of 5" / "Fuerza de 5"). El `rule_ref: shared-rule.vomit-attack`
  queda sin discrepancia.

## 2. Always Hungry — KAZ "15 gc + sacrificio" vs KB "20 gc / contar como 2" → **FIEL A SU FUENTE; sin cambio**

- Fuente: `night-goblins-kaz.txt` líneas 1899–1904 (Karak Azgal, página del Troll):
  "The warband must pay **15 gc** after every game… the Big Boss has the option of
  **sacrificing three Snotlings or two Cave Squigs** to the Troll in lieu of buying food…
  If this fee is not paid… the Troll gets hungry and wanders off."
- La KB (`shared-rule.always-hungry`) modela la variante del Mordheim rulebook/Mordheimer:
  20 gc, o "count as 2 members / 5 crowns".
- Son **dos impresiones distintas de la misma regla** (KAZ reimprime la regla con coste y
  opciones propias). La transcripción 2B refleja fielmente su fuente; el vínculo
  `rule_ref: shared-rule.always-hungry` declara equivalencia semántica (upkeep por
  manutención, con alternativa si no se paga) y la diferencia de coste vive en el efecto
  de banda, que es la fuente de verdad de esta banda.
- **Acción:** ninguna. Discrepancia documentada (ya estaba en la tabla de la revisión).

## 3. Regeneration KEP (omite la cláusula Flaming) → **FIEL A SU FUENTE; sin cambio**

- Fuente: `crooked-moon-kep.txt` líneas 233–236 (página impresa del Troll): "REGENERATIN:
  TRLL HAVE A UNIUE PHYSILY… ROLL A D6, ON A RESULT OF 4 OR MORE THE WOUND IS IGNORED…
  TROLLS MAY NOT REGENERATE WOUNDS CAUSED BY FIRE OR FIRE-BASED MAGIC. TROLLS NEVER ROLL
  FOR INJURY AFTER A BATTLE."
- La variante KEP **reproduce la regla completa excepto la última cláusula** de la KB
  ("…unless they were taken Out of Action by a Flaming weapon or spell. Then the Troll
  rolls for injury as normal"). La omisión es del PDF de KEP, no de la transcripción.
- La cláusula que ambas versiones comparten es la mecánica operativa (D6 4+ ignora la
  herida, no regenera fuego); el `rule_ref: shared-rule.regeneration` es correcto.
- **Acción:** ninguna en los datos. Anotar en revisión que la banda KEP usa el texto de
  su fuente (la excepción Flaming post-batalla no aplica según KEP).

## 4. Turnkeys "Immune to Poison" vinculado a `shared-rule.immune-to-poison-3` → **VÍNCULO DÉBIL; revertido**

- Fuente: `watchmen-mim.txt` líneas 492–496: "Immune to Poison: Jailers have the
  constitution of an ox allowing them to shrug off the effects of almost any poison. After
  developing a resistance during years of contraband substance abuse, **Turnkeys are not
  affected by any poison**."
- La regla 2B es una **inmunidad por constitución/resistencia**, no la regla no-muerto.
  La variante de la KB `shared-rule.immune-to-poison-3` dice literalmente "Warriors with
  the **Undead** special rule are unaffected by poison" — su fundamento no aplica a los
  Turnkeys (vivos). Vincularla atribuiría a la banda una condición que no cumple.
- La variante genérica `shared-rule.immune-to-poison` ("This warrior is immune to
  Poison") sí coincide semánticamente con la frase operativa de la fuente.
- **Acción aplicada:** `rule_ref` de `turnkeys--immune-to-poison` cambiado de
  `shared-rule.immune-to-poison-3` a `shared-rule.immune-to-poison`, con el vínculo
  justificado por la frase operativa ("not affected by any poison").

## Resumen

| Caso | Veredicto | Acción |
|---|---|---|
| Vomit Attack KEP S8 vs S5 | Error de transcripción (OCR) | Corregido a S5 (EN/ES) |
| Always Hungry KAZ 15 gc vs KB 20 gc | Fiel a su fuente (KAZ reimprime con coste propio) | Sin cambio; documentado |
| Regeneration KEP sin cláusula Flaming | Fiel a su fuente (omisión del PDF KEP) | Sin cambio; documentado |
| Turnkeys immune-to-poison | Vínculo incorrecto (variante Undead) | Re-vinculado a `shared-rule.immune-to-poison` |

## 5. Auditoría de dígitos de `crooked-moon-kep` (barrido anti-OCR completo)

Fecha: 2026-09-14. Motivación: el caso 1 demostró que el OCR original del PDF KEP
(escaneo sin capa de texto) inventaba y perdía dígitos. Se realizó un barrido de todos
los números del paquete (roster, perfiles, XP, costes, precios de equipo) regenerando
las 8 páginas a 300 dpi (`build/cache/2b-pdfs/cmk300-*.png`, OCR en
`cmk300-ocr.txt`) y verificando cada valor.

### Resultados verificados sin cambios (coinciden con el paquete)

- Roster: mínimo 3, máximo 12, 500 gc; Big Boss 1, Shaman 0-1, Bosses 0-2,
  Squig Hoppers 0-2, Night Goblins ilimitados (grupos 1-5), Fanatics 0-2,
  Cave Squigs 0-5, Troll 0-1, Snotling Mob 0-1.
- Perfiles: Big Boss 45 gc / 17 XP; Bosses 25 gc / 6 XP; Night Goblins 15 gc;
  Fanatics 20 gc; Cave Squigs 15 gc; Troll 200 gc; Snotling Mob 50 gc
  (10 gc por Snotling de reposición).
- Líneas de características: Big Boss 4/3/3/3/3/1/2/1/7; Shaman 4/2/3/3/3/1/3/1/6;
  Bosses 4/3/3/3/3/1/2/1/6; Squig Hopper 2D6/4/3/3/1/4/1/6; Night Goblins
  4/2/3/3/3/1/3/1/5; Fanatics 4/2/3/3/3/1/3/1/5; Cave Squigs 2D6/4/0/4/3/1/4/1/5
  (el BS=0 del OCR antiguo se recuperó contra KAZ); Troll 6/3/1/5/4/3/1/3/4;
  Snotlings 4/2/2/2/2/1/3/1/4.
- Shaman 50 gc / 10 XP: el OCR a 300 dpi leía "1" (dígito comido), pero la fuente
  lo resuelve: el propio PDF KEP declara ser "a version of the Night Goblin warband
  from the Karak Azgal supplement", y el texto KAZ (líneas 1746 y 1758 de
  `night-goblins-kaz.txt`) imprime "A Shaman starts with 10 experience" y
  "0-1 Shaman / 50 gold crowns to hire". El paquete (50 gc / 10 XP) es correcto.
- Reglas: Vomit Attack Fuerza 5 (caso 1), Always Hungry 15 gc + sacrificio
  (caso 2), Regeneration sin cláusula Flaming (caso 3).
- Lista de equipo: Dagger 1st free/2, Sword 10, Spear 10, Club 3, Short Bow 5,
  Light Armour 20, Shield 5, Helmet 10, Poison Daggers 25, Two-handed 15,
  Ball & Chain 15, Madcap Mushrooms 25 — todo coincide línea a línea.

### Error encontrado y corregido: coste del Squig Hopper

- El paquete tenía `cost: null` con la nota "The printed profile has no separate
  hire cost in the source" — ambos heredados del OCR antiguo, que leía la línea de
  contratación como `2UHPPERL<RWNTHIRE` (sin dígitos).
- Verificación: la línea de contratación a 300 dpi ("0-2 SQUIG HOPPERS … GOLD
  CROWNS TO HIRE") tiene **dos** glifos de coste. El análisis de componentes conexos
  del token de coste muestra: primer dígito sin agujeros (forma escalonada del "3"),
  segundo dígito w=20 px con **un contador cerrado y simétrico** — un "0"
  inequívoco (ni "6" con barra superior ni "9" con cola). La línea imprime
  **"SQUIG HOPPERS 30 GOLD CROWNS TO HIRE"**.
- Cohere con la XP del Hopper: el OCR antiguo no capturó coste ni XP; la XP "6" ya
  estaba confirmada por recorte ("A SQUIG HOPPER STARTS WITH 6 EXPERIENCE").
- **Acción aplicada:** `squig-hopper.cost: null → 30` y nota de restricción
  reescrita con el texto real de la fuente ("A Squig Hopper can't be equipped with
  any weapon but can pick armour from the Night Goblins list"), sustituyendo la
  nota de flag derivada del OCR defectuoso.

## 6. Auditoría de dígitos de `clan-angrund-kep` y `slave-uprising-kep` (barrido anti-OCR)

Fecha: 2026-09-14. Mismo método que el caso 5: render a 300 dpi
(`cak300-*.png`, `suk300-*.png`; OCR completo en `cak300-ocr.txt`), lectura
quirúrgica por recortes, análisis de glifos por componentes conexos y
comparación con plantillas confirmadas por contexto.

### clan-angrund-kep (PDF KEP escaneado, 7 páginas)

Valores verificados sin cambios (coinciden con el paquete):
- Roster: mínimo 3, máximo 12, 500 gc; Noble 1, Engineer 0-1, Troll Slayer 0-1,
  Ironbreaker 0-1, Clansmen ilimitados, Thunderers 0-5, Beardlings ilimitados.
- XP: Noble 20 (token de dos glifos "2"+"0"; el OCR lee "2"), Engineer 10
  (glifos verificados "1"+"0"), Troll Slayers 8 (glifo con dos bucles cerrados;
  el OCR de 200 dpi lo leía "&"≈8; el paquete ya tenía 8).
- Costes: Noble 85 (leído limpio a 600 dpi), Engineer 50 ("S"=5 + 0, coincide
  con Expert Craftsman de KAZ), Troll Slayer 50, Clansmen 40, Beardlings 25,
  Ironbreaker 110 (doble "1" + 0).
- Perfiles: Noble 3/5/4/3/4/1/2/1/9; Engineer 3/4/3/3/4/1/2/1/9 (el "743..." del
  OCR a 200 dpi era mala lectura); Troll Slayer 3/4/3/3/4/1/2/1/9 (leído
  "343341219" con zoom); Ironbreaker 3/4/3/3/3/1/1/2/9; Clansmen 3/4/3/3/4/1/2/1/9;
  Thunderers 3/4/3/3/4/1/2/1/9; Beardlings 3/3/2/3/4/1/2/1/8.
- Listas de equipo (dos columnas; el OCR mezclaba columnas): Warrior y Thunderer
  verificadas línea a línea contra el paquete.

**Errores encontrados y corregidos:**

1. **Dwarf Thunderers: coste 60 → 40.** El primer dígito del coste es
   inequívocamente "4" (diagonal + travesaño, idéntico al "4" confirmado de
   Clansmen y Beardlings' "2"-ref), no "6": el OCR lee "4KL>" y "4L>" en dos
   pasadas. Cohere con la impresión de KAZ para Dwarf Thunderers
   (`night-goblins-kaz.txt` ~línea 1481: "0-5 Dwarf Thunderers / 40 gold crowns
   to hire"); el precio de 60 gc del paquete provenía del rulebook base, no del
   PDF fuente.
2. **Lista Thunderer: faltaba CROSSBOW 25 gc.** El OCR de página completa
   intercalaba las dos columnas y el "25" (de la ballesta, columna Thunderer)
   se atribuyó a SWORD, ocultando el ítem. Con separación por columnas se lee
   "<ROSSBOW. . 25". Añadido `crossbow` (id existente en la KB) cost 25 a
   `dwarf-thunderer-equipment-list`. El SWORD 10 del paquete coincide con KAZ.

### slave-uprising-kep (PDF KEP escaneado, 3 páginas)

Valores verificados sin cambios (coinciden con el paquete):
- Lista de equipo completa: Dagger 1st free/2nd 2, Mace 3, Hammer 3, Axe 5,
  Sword 10, Spear 10, Halberd 10, **Sling 2** (fragmento "LIN2<" a y2511),
  Short Bow 5, Buckler 5, Helmet 10.
- Roster: 1 Demagogue, hasta 3 Underlings, 1 Goblin Leader, 1 Human Leader,
  Rabble ilimitados, hasta 5 Human Slaves, hasta 5 Goblin Slaves.
- XP: Demagogue 1 (dos lecturas independientes "STARTWITH1EXPERIEN<E"),
  Underlings/Leaders 4.
- Henchmen: Rabble 15 gc 5/2/2/3/3/1/4/1/4; Goblin Slaves 15 gc 4/2/2/3/3/1/3/1/5;
  Human Slaves 15 gc 4/2/2/3/3/1/3/1/7 — todo idéntico al paquete.
- Costes: Underlings 25, Goblin Leader 25, Human Leader 25 (patrón de glifos
  idéntico al "25" verificado).
- Perfiles de héroes: Demagogue 6/3/3/3/3/1/5/1/7 — el OCR "633331157" coincide
  exactamente con el paquete (la sospecha de intercambio I/A era infundada aquí).
  Goblin Leader 4/3/3/3/3/1/3/1/6 y Human Leader 4/3/3/3/3/1/3/1/7: el OCR a
  200 dpi leyó "...136"/"...137" (par apretado "31" transpuesto); el paquete
  (I=3, A=1) coincide con el perfil canónico de héroe humano de Mordheim y con
  la estructura de las filas confirmadas; se acepta el paquete con nota.

**Error encontrado y corregido:**

3. **Demagogue: coste 30 → 50.** Los glifos del coste son "5" (idéntico al "5"
   del "25" verificado: barra superior + asta izquierda + cuenco) + "0" (óvalo
   con contador cerrado y muescas internas, idéntico al "0" de "10"/"110"). La
   nota original del modelador ("source shows 3[0]") leyó el "5" en cursiva como
   "3". Corregido `demagogue.cost: 30 → 50`.

## Auditoría de dígitos 300/600 dpi — reglas de texto, KEP restantes (2026-09-14)

Extensión de la auditoría a los **textos de reglas** de `clan-angrund-kep` y `slave-uprising-kep`
(las cifras de perfiles, costes y equipo ya estaban verificadas). Método: OCR a 600 dpi con
recortes quirúrgicos y lectura de glifos por arte ASCII para los tokens ambiguos.

### clan-angrund-kep (special-rules.yaml) — todo confirmado, sin cambios

| Regla | Token verificado | Resultado |
|---|---|---|
| Hard to Kill | "roll of 6 instead of 5", "1-2 knocked down, 3-5 stunned" | ✓ (página 16, OCR 300 dpi) |
| True Grit | "1-3 knocked down, 4-5 stunned" | ✓ ("1-3" leído a 600 dpi binarizado, conf 0.90; el paquete es correcto) |
| Thick Skull | "2+ instead of 4+" | ✓ |
| Leader | "within 6\"" | ✓ |
| Resource Hunter | "+1/-1" | ✓ |
| Expert Weaponsmith | "3\" pistols / 6\" crossbows and handguns" | sin cifra legible en el PDF escaneo (línea degradada); texto coincide con la impresión de KAZ Guildsmen — aceptado con nota |
| Ferocious Charge | "-1 to hit penalty" | ✓ (recorte a 600 dpi, conf 0.92) |
| Monster Slayer / Berserker | "4+" / "+1" | ✓ |
| Incomparable Miners | "+1 treasure" | ✓ |

### slave-uprising-kep (special-rules.yaml) — 1 corrección aplicada

- **Escapists — cláusula de captura truncada.** El OCR a 600 dpi reveló una frase que faltaba
  en el borrador y en el paquete: *"They can never be captured, and any injury result like
  Sold to the Pits or Captured by Skaven are treated as full recovery."* El paquete tenía solo
  "Skaven are treated as full recovery" (artefacto del corte de línea del primer OCR). **Corregido
  en EN y ES.** Nota: el "Sold to the Pits" es la lectura más consistente del fragmento
  degradado (todos los pases OCR leen "SLD/LIKE SOLD T THE PIT"); la mecánica coincide con la
  tabla de heridas estándar de Mordheim.
- **Escapists — distancia de huida "1/2\"" ✓.** El OCR lee "12\"" pero el arte ASCII del glifo
  muestra una barra diagonal ancha ("/") entre el 1 y el 2; el OCR la fusiona con el "1"
  (confusión /→1 documentada en la cabecera del borrador). El paquete ya tenía 1/2\" — correcto.

Los tres PDFs escaneados del manifiesto (KEP) han pasado ahora la auditoría completa:
perfiles, costes, equipo y textos de reglas.

## 7. Re-verificación completa contra fuentes de los 60 paquetes (2026-09-15)

Pasada de verificación de **todos** los datos ingeridos contra los PDFs de origen, con
`tools/knowledge/audit_2b.py` reescrito para extraer más evidencia y producir menos ruido:

- **Doble extracción por banda.** Cada comprobación se evalúa sobre el texto cacheado *y*
  sobre un `pdftotext -layout` (cacheado en `build/cache/2b-pdfs/layout/`). El extractor plano
  es completo pero colapsa las tablas a columnas; el de layout conserva el orden visual pero
  pierde líneas por entrelazado. Una fila se considera verificada si **cualquiera** de las dos
  formas la confirma; solo se marca si ninguna puede.
- **Nombres tokenizados.** Los apóstrofes tipográficos, las barras y los nombres partidos por
  línea ya no impiden la búsqueda (`Bramstetter’s` = `Bramstetter's`, `Scimitar (Sword)` =
  `Scimitar/Sword`, `Toughened leat hers` = `Toughened leather`).
- **Divisas y líderes de puntos.** Se reconocen `gc/GCs/wt/tc/dinars`, y las series de puntos
  (`Dagger .. .. .. 1st free/2 gc`) se colapsan para que el precio entre en la ventana.
- **Precios con fórmula y listas delegadas.** Las filas con precio impreso como fórmula se
  verifican por su figura base (`75+5D6` → 75); las listas que el documento remite al
  reglamento se contrastan contra la transcripción de esa misma lista en la KB.
- **Redacción impresa adjudicada.** Una tabla explícita en la herramienta registra las
  palabras que la fuente imprime distintas del nombre canónico; el precio se sigue leyendo
  del propio texto, de modo que la adjudicación no sustituye a la evidencia.

### Cobertura

| Resultado | Filas |
|---|---|
| Filas de equipo con coste | **1620** |
| Verificadas contra el texto del PDF | **1553** |
| Verificadas contra la lista del reglamento (KB, mismo `list_id`) | **11** |
| Adjudicadas a mano (ventana de extracción) | **2** |
| En PDFs escaneados (OCR): verificadas a mano en la §6 | **54** |
| **Problemas** | **0** |

Perfiles, costes de contratación, experiencia inicial, composición de roster, oro inicial,
listas de equipo, `rule_ids` y referencias: sin discrepancias. Las 54 filas OCR pertenecen a
`clan-angrund-kep` (29), `crooked-moon-kep` (19) y `slave-uprising-kep` (15), los tres PDFs
sin capa de texto, cuyo barrido de 300/600 dpi está documentado en la §6.

### Correcciones aplicadas (1 referencia errónea + 1 precio)

| Banda / fila | Antes | Después | Evidencia |
|---|---|---|---|
| `night-goblins-kaz` · fanáticos | `hobgoblin_poisoned_daggers` 25 gc | **`poison_daggers`** 25 gc | La fuente imprime “Poison daggers. 25 gc Common (Fanatics only)”. El id anterior apuntaba al objeto de los Hobgoblins (KB `sons-of-hashut`, 15 gc): item distinto. Las bandas KB de goblins nocturnos usan `poison_daggers` 25 en su lista de fanáticos. |
| `militiant-mootlanders-mim` · héroes | `magic_acorn` 250 gc | **100 gc** | La lista de héroes imprime `Magic Acorn ... 100 gc`; el bloque de equipo especial imprime `250 gold crowns` para el mismo objeto. Se aplica la regla editorial de 2A (Silver-tip Stake): **el precio de lista es el operativo**; la cifra del bloque especial queda como erratum documentado en las notas de la fila. |

`plague_censer` se revisó en los dos paquetes de Clan Pestilens y **no se cambió**: ambos
imprimen la fila de lista (`Plague Censor 100 gc*` en LUS — con errata tipográfica de la
fuente — y `Plague Censor 100 wt` en MOU), y el bloque de equipo especial imprime
`75+5D6 gc` como precio de compra posterior. Verificado primero como 75 por no encontrar la
fila de lista tipografiada; se revirtió al aparecer. Las notas de ambas filas recogen ahora
las dos cifras y la regla aplicada.

### Adjudicaciones sin cambio (datos correctos)

| Caso | Evidencia |
|---|---|
| `gromril_armour` 75 en `dwarf-guildsmen-kaz` y `dwarf-slayers-kaz` | La lista de enanos de KAZ no imprime precio para la armadura Gromril (solo “Gromril Weapon 3x the cost”); la lista es la del reglamento, y sus copias en la KB (`dwarf-rangers`, `dwarf-treasure-hunters`, mismo `dwarf-warrior-equipment-list`) la tasan en 75 gc. El candidato de 100 gc procede de la frase siguiente (“training manual … sell for 100 gc”). Registrado como fila adjudicada con su veredicto. |
| Listas skaven de KAZ (`skaven-of-clan-mors-kaz`, `skaven-of-clan-skryre-kaz`) | La fuente declara “All of the equipment lists from the rulebook apply”: no imprime listas. Las filas coinciden con la transcripción KB de esa lista (`skaven-clan-eshin` · `skaven-hero-equipment-list`: weeping blades 50, throwing stars 15, blowpipe 25, warp pistol 35). El jezzail (175 GC) sí se imprime en el bloque `SKAVEN CLAN SKRYRE SPECIAL EQUIPMENT`. |
| Lista de Thunderers de KAZ (`dwarf-guildsmen-kaz`) | La fuente remite por nombre a la “Dwarf Thunderers equipment list” pero no imprime el precio del handgun; lo aporta la lista del reglamento (KB `dwarf-treasure-hunters` · `thunderer-equipment-list`, mismo id, 35 gc). |
| Palabras impresas distintas del nombre canónico | `Halbard` (errata) = `halberd` 10 · `Wardog` = `warhound` 30 · `Horsemens Hammer` = `horsemans_hammer` 30 · `Double-handed weapon` / `Double Handed Weapon` = `great_weapon` 15 y `two_handed_weapon` 15 · `Toughened leather` = `toughened_leathers` 5 · `Rope and Hook` = `rope_hook` 5 · `Superiour Black Powder` = `superior_blackpowder` 20 · `Ball and Chain` = `ball_chain` 15 · `Scimitar (Sword)` = `sword_scimitar` 10 · `Swivel Gun Ammo: Ball/Chain/Grape Shot` = 5/2/2 · `Jezzail` = `jezzail` 175. Todas con precio coincidente en la fuente. |

### Reproducir la verificación

```bash
python tools/knowledge/audit_2b.py                  # informe JSON a stdout
python tools/knowledge/ingest_2b.py validate        # forma del staging
python -m pytest tests/knowledge -q                 # 351 pruebas
python tools/format_yaml.py --check sources/2B
```

Los veredictos que la herramienta usa están en `tools/knowledge/audit_2b.py`
(`SOURCE_WORDING`, `KNOWN_EQUIPMENT`, `RULEBOOK_DELEGATED`), cada uno con su motivo. Las
filas siguen siendo información, no problemas: `problem_count` es 0.

## 8. Re-verificación de costes de héroe y experiencia inicial (2026-09-16)

La pasada de la §7 verificó el equipo; esta cierra las dos magnitudes que quedaban fuera:
el **coste de contratación** y la **experiencia inicial** de cada héroe. Al medir la
cobertura apareció lo importante: **los dos chequeos llevaban semanas muertos**. Construían el
patrón desde el nombre en minúsculas (`norm()`) y lo buscaban contra el texto capitalizado
del PDF sin `re.I`, así que **0 de 207 héroes** se comparaban y `cost-mismatch` y
`experience-mismatch` no podían disparar nunca.

### Defectos del cotejo corregidos

| Defecto | Efecto | Corrección |
|---|---|---|
| Patrón insensible a mayúsculas invertido: nombre en minúsculas contra texto capitalizado, sin `re.I` | `cost-mismatch` y `experience-mismatch` inertes | `hero_name_patterns()` (nombre y su otro número, para `Apprentices`/`Apprentice`) + búsqueda `re.I` |
| Un solo idioma de imprenta (puntos guía del reglamento) | Ningún documento 2B imprime así los héroes | Idiomas reales: `<n> NOMBRE <coste> gold crowns to hire` y `<Nombre> .... <coste>`; se descarta `<Nombre> <coste>` a secas porque la extracción a dos columnas pega la tabla de skills con el coste de la columna vecina |
| Divisa única (gc) | Los MIM skaven imprimen **warp tokens** y la REL **dinares**: 12 bandas ilegibles | Divisa explícita: `gc`, `gold crowns`, `warp tokens`, `dinars`, `coronas` |
| Ventana de búsqueda normalizada con `presence()` | El idioma de puntos guía era inerte (esa normalización borra los puntos) | Anclaje sobre texto real (`section_anchor_pattern`), con el encabezado del perfil como ancla |
| Sin alcance por banda | En KAZ (8 bandas por PDF) `Apprentices` se tasaba con el `20` de Clan Skryre | Búsqueda acotada a la sección del propio perfil; en documento compartido sin encabezado localizable se deja sin verificar en vez de adivinar |
| Fórmula detectada en cualquier punto de la ventana | Una fila de precio normal con un `D6` cerca se degradaba a `equipment-price-formula` (informativa) y un **precio erróneo pasaba inadvertido** | La fórmula solo cuenta si está en la posición de precio de la propia fila (30 caracteres tras el nombre) |

### Figuras delegadas a otra banda (nuevo `DELEGATED_PROFILES`)

El suplemento de Sartosa no tasa sus héroes: imprime **«Same as Da Mob»** y remite a la lista
del Orc Mob. Ahora esas cinco figuras se contrastan contra la transcripción de la KB
(`orc-mob`), que coincide en todas (Orc Boss 80, Orc Shaman 40, Orc Big ‘Uns 40 y los mismo
henchmen 25/15/15/200); se reportan como `cost-delegated` con el cotejo hecho, no como
ilegibles.

### Cobertura tras la corrección

| Resultado | Héroes |
|---|---|
| Costes verificados por idioma impreso | **125** |
| Costes verificados por delegación (KB `orc-mob`) | **5** |
| Experiencias verificadas por idioma impreso | **152** |
| Experiencias verificadas por delegación | **5** |
| `cost-unverifiable` (informativos, con su motivo) | **72** |
| **Problemas** | **0** |

### Verificación a mano de los 72 no fijados por idioma

Se releyeron las páginas **por geometría** (página → columna → línea, que es el orden que ve
un lector) acotando a la ventana de páginas que el manifest registra para cada banda cuando
el PDF es compartido: **21 bandas confirmadas en las que toda figura impresa existe en el
paquete** (KAZ ×2, MIM ×9, LUS, SAR ×3, REL ×6). Falsos positivos que produjo ese barrido,
comprobados y descartados: `Rookies` 15 (el `25 gold crowns Availability: Rare 12` era el
halcón de caza de la columna vecina) y `Young Nobles` 30 (el `55` era el de Shearls).

Lecturas directas de página, cuando la extracción no basta:

| Banda | Impreso | Veredicto |
|---|---|---|
| `call-of-the-night-haint-mim` | 110 / 60 **cold crowns**, 25 / 30 gold crowns | coincide con el paquete |
| `skaven-of-clan-pestilens-mou` | `1 PLAGUE PRIEST .... 65 wt`, `0-2 PLAGUE CHAMPIONS .... 45 wt`, `0-3 MONK INITIATES .... 20 wt`, Plague Monks 25, Plague Rats 25 «each», Slaves 15 | coincide |
| `pirates-of-the-cathayan-sea-sar` | 60 / 35 / 55 / 15 héroes; 25 / 25 / 35 henchmen; Floordogs 0 («Never Gain Experience») | coincide |
| `clan-angrund-kep` (escaneado) | 85, 50, 50, 110; henchmen 40, 40, 25 | coincide (dígitos recuperados por recorte + binarizado invertido) |
| `crooked-moon-kep` (escaneado) | Big Boss 45, Bosses 25, Night Goblins 15 | coincide |
| `slave-uprising-kep` (escaneado) | 25 / 25 / 25 héroes; 15 / 15 / 15 henchmen | coincide |

**Residuo declarado:** en los tres PDFs escaneados la tipografía decorativa hace que el OCR
pierda algunos dígitos sueltos (el Shaman y los Squig Hoppers de `crooked-moon-kep`, el
Demagogue de `slave-uprising-kep` y varios henchmen). Donde el dígito se recupera coincide con
el paquete, y ningún dato legible lo contradice; quedan listados como `cost-unverifiable` para
una lectura humana de la imagen, sin inventar la cifra. **Ese residuo se cierra en la §9**, por
lectura de las páginas escaneadas y por las dos rutas de lectura nuevas del auditor.

### Datos

**Ninguna corrección de datos en esta pasada.** Todos los hallazgos eran defectos del cotejo
o artefactos de la extracción a dos columnas; los valores de los 60 paquetes se mantienen tal
cual. La batería negativa que lo demuestra (10 casos, uno por chequeo, cada uno rompe el dato
y exige el hallazgo) está en `tools/knowledge/audit_2b_negative_tests.py` y pasa 10/10:

```bash
python -X utf8 tools/knowledge/audit_2b_negative_tests.py
```
## 9. Cierre de los `cost-unverifiable`: lectura por geometría, tipografía decorativa y páginas escaneadas (2026-09-16)

Fecha: 2026-09-16. La §8 dejó **72 héroes con `cost-unverifiable`**: el cotejo de costes sólo
sabía leer las figuras que la fuente imprime *junto al nombre* (lista con puntos guía, «1 Big
Boss 45 gold crowns to hire»). Quedaban fuera tres formas de impresión reales. Se han cubierto
las tres y el residuo es **0**.

### 9.1 Figura en una línea propia → lectura por geometría de página

Se lee del XML de `pdftohtml -xml` de la página (que da la posición de cada palabra) y se ha
añadido al auditor:

- **Separación por columnas**: en una misma altura conviven la línea de la columna izquierda y
  la de la derecha (MIM y MOU). Las palabras sólo se agrupan si siguen unas a otras (hueco
  < 45 pt), de modo que cada figura queda con su columna.
- **Anclaje al encabezado**: la figura toma como encabezado la primera línea corta que no sea
  prosa situada por encima, en el **mismo margen izquierdo** (±30 pt) y dentro de 240 pt; se
  conservan las 4 líneas superiores como candidatas, porque la fuente intercala avisos
  («0-1\* Sea Singer», «\*(Replaces Skeleton or Ghost Mate)», «40 gold crowns»).
- **Puertas contra falsos positivos**, cada una comprobada con un caso real: se descarta un
  encabezado cuyos términos extra sean números (la fila de perfil «Black Skaven 6 4 3 4 3 1 5 1
  6» *contiene* el nombre) y se deja de mirar hacia arriba en cuanto la línea inmediata nombra
  a **otro** personaje del paquete (el «Cannon Fodder» que tapa al Capitán sólo promocionable).
- **Alcance por banda**: un PDF de campaña lleva varias bandas (KAZ, 8); cada fila del manifest
  aporta su `pdf_start_page` y la ventana se corta en el inicio de la siguiente.
- **Divisas**: se añaden *gold coins* (KAZ) y *cold crowns* (errata de `call-of-the-night`).

**55 figuras** quedaron verificadas por esta ruta: MIM 29 (en 8 bandas), REL 18 (6 bandas),
KAZ 5 (2 bandas), LUS 2 y SAR 1.

### 9.2 Encabezados en tipografía decorativa → descifrado

Los suplementos skaven imprimen los encabezados de perfil en una fuente decorativa cuyos
códigos son las letras desplazadas: «Engineer Adept» se extrae como `'KDFKBBO>ABMQ` y «Black
Skaven» como `$I>@H5H>SBK`, así que ningún cotejo por nombre podía reconocerlos. El
desplazamiento se dedujo de los pares que el propio documento imprime dos veces (el título
«Skyre Warp Engineers», los perfiles junto a su fila de características y los precios de la KB):
los códigos `0x3E-0x57` son la letra menos 3 y `0x24-0x3C` la misma letra menos `0x1E`, y ambas
franjas descifran a una letra. La rutina sólo se aplica a líneas sin minúsculas que contienen
códigos que ninguna fuente de texto imprime (`$ > @ *`), y el resultado se ofrece **además** de
la lectura literal: un encabezado que descifre a algo no reconocible simplemente no casa con
ningún perfil, nunca acredita una cifra.

**5 figuras** cerradas así: `metal-mongers-mim` (Engineer Adept 55, Black Skaven 40, Forge-Rats
20), `guild-of-disgraced-engineers-mim` (Apprentice Engineers 40, cuyo encabezado queda 129 pt
por encima de la cifra) y `ghost-pirates-sar` (Sea Singer 40, tras el aviso entre paréntesis).

### 9.3 Páginas escaneadas → lecturas registradas en el propio auditor

Los tres PDF KEP no tienen capa de texto: sus figuras están impresas en una tipografía que el
OCR pierde («2UHPPERL<RWNTHIRE» es «0-2 SQUIG HOPPERS 30 GOLD CROWNS TO HIRE») o confunde (el
«5» en cursiva se lee «S», y así «50» llega como «S»). Se incorpora al auditor la tabla
`READ_OFF_PAGE` con **las 12 figuras de héroe leídas de la imagen**, cada una con la página de
la que se leyeron, y el motivo de conjunto remite a §5 y §6 de este documento (recortes a
300/600 dpi, análisis de glifos por componentes conexos y corroboración cuando la misma figura
se imprime en otro documento: el Shaman 50 por el texto KAZ de los Night Goblins, del que el
propio PDF KEP declara ser versión). El auditor compara la lectura con el paquete: coincidir
**verifica** la cifra («cost-read-off-page»), y discrepar produce un `cost-mismatch` real, no
un «no verificable».

| Banda | Figuras de héroe leídas de la imagen | Páginas |
|---|---|---|
| `clan-angrund-kep` | Noble 85, Engineer 50, Troll Slayers 50, Ironbreaker 110 | 3, 4, 4, 5 |
| `crooked-moon-kep` | Big Boss 45, Shaman 50, Bosses 25, Squig Hopper 30 | 4, 5, 5, 5 |
| `slave-uprising-kep` | Demagogue 50, Underlings 25, Goblin Leader 25, Human Leader 25 | 2, 2, 2, 2 |

La lectura es reproducible con la herramienta nueva `tools/knowledge/read_scanned_costs.py`
(renderiza a 400 dpi, localiza cada línea de contratación con RapidOCR, recorta la franja
anterior y la imprime en varias preprocesos y en arte ASCII para lectura humana). El auditor
**no** depende de ella (RapidOCR es una instalación de usuario, no una dependencia del
proyecto): sólo consume lo que quedó leído y registrado.

### Resultado

| Métrica | §8 | ahora |
|---|---|---|
| Costes de héroe verificados contra la página | 125 | **185** |
| Costes de héroe leídos de la imagen del escaneo | 0 | **12** |
| Costes verificados por delegación (KB «Da Mob») | 5 | **5** |
| `cost-unverifiable` | **72** | **0** |
| Experiencias verificadas | 152 | **152** |
| Problemas | 0 | **0** |

**Ninguna corrección de datos en esta pasada**: las 72 figuras que el cotejo no alcanzaba
coinciden todas con el paquete (las dos que estaban mal — Squig Hopper `null` y Demagogue
30 — ya se corrigieron en §5 y §6). Lo que estaba incompleto era la herramienta de lectura, no
los datos. La batería negativa se amplía a **15/15** (los 12 casos de dato más 3 de maquinaria:
al desactivar el descifrado decorativo, la lectura por geometría o las lecturas registradas,
las cifras que cada ruta sostiene vuelven a `cost-unverifiable`), y pasa completa:

```bash
python -X utf8 tools/knowledge/audit_2b_negative_tests.py
```

## 11. Cotejo de perfiles y stats de las tres bandas KEP (imagen)

Las filas de estadísticas de clan-angrund-kep, crooked-moon-kep y slave-uprising-kep,
no verificables por extracción de texto (escaneos), se contrastaron contra la imagen:

- **Método**: render a 400 dpi (`pdftoppm`), componentes conexos por glifo en la franja
  de dígitos y **clasificación por plantillas** — cada glifo se compara contra los glifos
  de filas de la misma página ya leídos sin ambigüedad (misma fuente decorativa).
  Distancias de decisión 0.03-0.08 frente a 0.30-0.37 entre dígitos distintos.
- **Orden de columnas KEP**: M WS BS S T W **A I** Ld (el encabezado impreso lo
  confirma); el paquete usa el orden KB (I antes de A) — la comparación tiene en cuenta
  el intercambio.
- **Corrección de datos (1)**: `slave-uprising-kep` Underlings I **3→5** (fila impresa
  `633331(1)(5)6`; el OCR crudo «633331156» ya lo insinuaba y el cruce por plantillas
  lo confirma: A=1, I=5, Ld=6).
- **Confirmadas 21 filas** (16 exactas + 2 por intercambio A/I + 3 con «3» decorativo
  leído como «7» por el OCR crudo, resuelto por plantillas: Troll Slayers, Ironbreaker,
  Clansmen). Squig Hopper y Cave Squigs empiezan su fila con «2D6», no verificables
  glifo a glifo; sus columnas fijas coinciden con lo extraído.
- Herramienta reproducible: `tools/knowledge/read_2b_kep_stats.py` (semillas
  y coordenadas documentadas en el propio fichero).

## 12. Cotejo de hirelings y Dramatis Personae contra fuentes

Los 28 hirelings de `sources/2B/catalog/hirelings/` (grade-2b, MiM Specialists,
Miracle Workers priests y Relics) se contrastaron por primera vez contra sus PDFs
(`tools/knowledge/check_2b_hirelings.py`; bloques impresos en
`hireling-blocks/` para lectura manual):

- **Tarifa, fila de stats, rating y presencia de reglas**, con adjudicación por
  página a dos columnas (la tarifa del vecino no cuenta) y fusiones de frases
  partidas entre líneas.
- **1 corrección de datos**: Fire-Eater hire **70 → 75** gcs (+30 upkeep), leído
  de la cabecera impresa de su bloque (MiM Specialists p4, texto real del PDF).
- **Verificados a mano los residuales**: Snorri (fila 353442228 y +20 con la p62
  compartida con el Black Orc; Drunk/Lucky en la continuación p63), Aldred
  (+60 fijo; Righteous Fury impreso en la línea de Skills), Bog Hunter y
  Midshipman (filas 433331316 / 433331417, mezcladas por columna en el extractor),
  Halfling Pimp (+10; el +15 era del Fence), Albino Stormvermin (75 **warp
  tokens**), Norse Bearman (Drunken impreso en la cabecera de página),
  Priest of Verena (Strictures en la página compartida con Solkan),
  Armen Abbas (+65 fijo, `kind: fixed` correcto).
- **Strigani Seer Necromancer y Snerik siguen siendo name-only legítimos**: el
  PDF de Karak Azgal sólo los *menciona* en las listas de contratación (p51 y
  p45/56); no imprime bloque de perfil. El estatus `normalization_status:
  name-only` del paquete es fiel a la fuente.

Resultado: **27/28 con datos verificados contra el bloque impreso** (25 exactos
+ 1 corregido + Strigani/Snerik name-only conformes) y la batería en verde:
validate 60/0, conformidad 0, audit_2b 0 problemas.
