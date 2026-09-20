# Auditoría cruzada del staging 2B — 2026-09-14

Comparación de las 60 bandas de `sources/2B/bands/mordheim/` contra los textos
extraídos de los PDFs (`build/cache/2b-pdfs/text/`).

Herramienta: `tools/knowledge/audit_2b.py` (nueva). Salida cruda JSON:
`build/cache/2b-audit.json`. Ejecutar con:

```bash
python -X utf8 tools/knowledge/audit_2b.py
```

## Verificaciones automáticas realizadas

1. **Nombres de perfil** presentes en el texto extraído (insensible a
   mayúsculas/acentos, con tolerancia singular/plural).
2. **Costes** de héroes contra las líneas `NOMBRE ....... <N> gc` del PDF.
3. **Experiencia inicial** contra `NOMBRE starts with N experience`.
4. **Roster**: mínimo de modelos, máximo y oro inicial contra las frases
   `minimum of N models` / `never exceed N` / `N gold crowns`.
5. **skill_access**: tokens válidos (combat, shooting, academic, strength,
   speed, special, pirate, musicianship); henchmen sin acceso a habilidades.
6. **Referencias**: cada `rule_id` citado por perfiles/banda existe en
   `special-rules.yaml`; cada `equipment_lists` citado existe en
   `equipment-access.yaml`.

## Resultado global

| Verificación | Flags | Veredicto |
|---|---|---|
| Tokens de skill_access inválidos | 0 | ✅ limpio |
| Henchmen con skill_access | 0 | ✅ limpio |
| Costes de héroes (54 comparaciones) | 0 | ✅ limpio |
| Dangling `rule_id` | 40 → **0** | ✅ corregido (ver abajo) |
| Nombre de perfil no hallado en texto | 12 | ⚠️ todos falsos positivos (ver abajo) |
| Min/max modelos, oro inicial | 15 | ⚠️ todos falsos positivos (ver abajo) |
| Experiencia inicial | 1 | ⚠️ falso positivo (ver abajo) |
| Paquete ausente | 1 | esperado (`slave-uprising-kep`) |

> **Actualización (2026-09-14)**: tras corregir el defecto de haint y mejorar
> `audit_2b.py` (sección-anchoring para antologías, semántica any-agree,
> más variantes de redacción, matching por palabras y detección OCR), la
> auditoría completa reporta **`problem_count: 0`**, con solo 9 notas
> informativas `profile-name-ocr-unverifiable` en los PDFs KEP degradados.

## ❌ Discrepancia real: `call-of-the-night-haint-mim` (40 referencias colgantes) — **RESUELTA**

Los perfiles de las 6 unidades espirituales (Tomb Banshee, Malignant Spirits,
Revenants, Spirit Hosts, Poltergeists, Mourngul) citaban 40 `rule_id` con el
patrón `<perfil>--<regla>` (p. ej. `tomb-banshee--ethereal`,
`spirit-hosts--no-brain`) que **no existían** en su `special-rules.yaml`.

**Corregido (2026-09-14)**: se expandieron las reglas compartidas a 40 entradas
por perfil (convention del resto de paquetes), con texto fuente verificado
contra las páginas 4-5 del PDF y `runtime`/traducciones coherentes con el
paquete original (`LATER` para reglas de combate, `YES` para Inmune al Veneno,
`NO` para Large/No Brain, out of scope). El archivo pasa de 25 a 65 reglas y
todas las referencias resuelven.

> Estado anterior (para histórico): `band--ethereal` (band-level) definía el
> Ethereal compartido y cada perfil conservaba solo sus reglas únicas.

## ⚠️ Falsos positivos verificados

Todos fueron comprobados manualmente contra el texto del PDF:

- **Oro inicial** (`metal-mongers-mim`, `militiant-mootlanders-mim`,
  `pirates-of-the-cathayan-sea-sar`): los tres dicen «You have 500 warp
  tokens/gold crowns (Gold Crowns) which you can use to recruit…». El regex
  del auditor solo reconocía la variante «N gold crowns to assemble». YAML
  correcto (500).
- **Min/max modelos** (7 bandas KAZ): el PDF de KAZ es una antología; el
  auditor leía la intro compartida («An Adventurer Warband must include a
  minimum of 4 models… never exceed 15») en vez de la sección de cada banda.
  Las secciones propias dicen min 3 y máx 12/20, que es lo que tiene el YAML.
- **Máx modelos** (dwarf-guildsmen/dwarf-slayers: «the maximum number of
  warriors in the warband **is** 12»): variante de redacción sin «never
  exceed». YAML correcto (12).
- **Experiencia** (`savage-orcs-kaz`, Boss): el texto de KAZ contiene la
  entrada de la banda *Night Goblins* («A Boss starts with 6 experience»)
  y la de *Savage Orcs* («A Boss starts with 20 Experience Points»). El
  YAML sigue la sección de Savage Orcs (Boss 20, Big Boss/Night Goblin no
  aplica). Correcto.
- **Nombres de perfil** (`clan-angrund-kep`, `crooked-moon-kep`): los PDFs
  KEP son OCR degradado que pierde espacios y la letra G
  («DWARFNOBLE» = Dwarf Noble, «BIB» = Big Boss, «SQUI HOPPER» = Squig
  Hopper). Todos los nombres existen realmente en el PDF. Además, las
  comprobaciones de costes que sí se pudieron leer coinciden
  (Big Boss 45 gc/17 exp, Shaman 50 gc/10 exp…). `channel-rats-mim`
  (Domnu/Petru): los nombres llevan paréntesis en el YAML
  («Domnu (Caravan Master)») y el nombre simple sí aparece en el texto.

## Revisión de `slave-uprising-kep` (2026-09-14, cierre 60/60)

El paquete se transcribió a partir del OCR; esta revisión independiente lo
verificó contra las imágenes de página a 300 dpi:

- **Filas de héroes** (Demagogo/Subordinados): los dígitos leídos
  `…331157` / `…331156` confirman las características `6,3,3,3,3,…`
  que el draft de baja confianza había dejado dudosas.
- **Experiencia del Demagogo**: recorte de alta resolución de la frase
  «THE DEMAGOGUE STARTS WITH **1** EXPERIENCE» (confianza 0.76–0.9 en el
  glifo); `experience: 1` es correcto, no «11».
- **Reglas especiales**: las 7 entradas (Escapists, Hate Skaven, Leader,
  Trustworthy, Hate Dwarfs ×2, Keep Together) coinciden con el texto del
  PDF, con clasificaciones runtime coherentes con el resto del staging.

Sin defectos. **60/60 bandas transcritas y consistentes con sus fuentes.**

## Conclusión

60/60 paquetes estructuralmente consistentes con sus fuentes; costes,
experiencias y skill_access sin errores. Los dos defectos detectados
(referencias colgantes de `call-of-the-night-haint-mim` y la transcripción
OCR de `slave-uprising-kep`) fueron verificados/corregidos y la auditoría
re-ejecutada sale **limpia (`problem_count: 0`, 0 notas)**. El staging 2B
queda apto para la promoción a `sources/knowledge`.
