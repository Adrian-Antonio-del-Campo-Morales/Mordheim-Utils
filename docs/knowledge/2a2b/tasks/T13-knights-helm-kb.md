# T13-F063 — Knight's Helm data part (Karak Azgal p. 59)

Status: **KB data delivered 2026-10-03; F063 itself remains open.** This report
covers the data/source half only: what "Knight's Helm (Crusading Knights
warbands)" is, what can be represented from sources, what is still missing, and
the exact facts L07 needs. Construction, selection/compilation and the real
3-vs-4 Skull Busta attack are L07/L22 work and are not delivered here.

Entry revision: branch `2A2B`, HEAD `1b7f7cf`, working tree with concurrent L06
edits preserved. Evidence: `build/cache/t13-parallel/knights-helm-kb/`
(`sources/` includes the downloaded documents, `search-log.md`,
`sources/candidates/candidates.md`, `record-added.diff`, `published-row.json`,
`validation.txt`).

## 1. Sources and pages consulted

The only primary source found that names the object is the admitted one:

| Source | Page / section | What it says |
| --- | --- | --- |
| [Karak Azgal](https://broheim.net/downloads/campaigns/karakazgal/Karak%20Azgal.pdf) (broheim.net, Strike to Stun campaign, Donno Ranzato, 76 pp.; local `sources/karak-azgal.pdf`, sha256 `bbe4cb2e…0a55`) | **printed p. 59** (pdf page index 58; page footer "59", same page as the "Special Equipment" heading), section "Special Equipment / Skull Busta", Savage Orc warband | The Basha clause, verbatim: "Basha: Warriors wearing a helmet only save vs stunning on a roll of a 6 when hit by a Skull Busta. Knight's helms (Crusading Knights warbands) only save on a 4+." |

The whole Karak Azgal document contains exactly this one occurrence of "Knight"
(verified over the extracted text). It gives the helm no other rule: no ordinary
save, no price, no rarity, no recipients, no band data.

Corpus checked for the "Crusading Knights warbands" identity and for any other
knight helmet (**all negative**; details and links in `search-log.md`):

- Official-ish knight warbands: Town Cryer 8 Bretonnian Knights (Questing
  Knight / Knights Errant / Squires; Knights' list prices a generic
  "Helmet 10 gc"), Bretonnian Chapel Guard ("Helmet (Not Errant Knight) 10 gc";
  the Errant Knight may not wear a helmet — Vain), Bretonnian Grail Companions /
  Order of the Mare, Knights of the Bitter Moors, Bretonnian Knights-Errant.
- Strike to Stun family (Karak Azgal was made alongside Mousillon): Mousillon
  campaign and its ten warbands, the archived Strike to Stun index (only
  Iroquois, Shadow Avenger, Karak Azgal, Mousillon), Karak Azgal's own web
  expansions (the six `*-kaz` bands already in the KB).
- Crusades-setting material: Relics of the Crusades Pt 1/2 (warbands: Arabian
  Tribes, Clan Skryre, Slavers, The Fallen; only a "Dwarf Helm"), Sartosa
  additional rules, Khemri campaign ("Crusaders" is Tomb-Guardian backstory),
  Knight Panther / Knight of the White Wolf hired swords.
- Broheim's complete grade lists (warbands, hired swords, Dramatis Personae) and
  broad web searches in English, Italian, French and Spanish. "Crusading
  Knights of the Empire" (Scribd) is a Warhammer Fantasy Battle Empire article,
  not Mordheim.

## 2. Identity: found, and the reuse-or-create decision

**There is no equivalent in the KB to reuse.** `helmet` (and its variant
records) encodes the ordinary helmet reaction (4+ vs stun, not modified by
Strength). Under Basha the ordinary helmet is degraded to 6+, while the knight's
helm saves at 4+; reusing `defence.helmet` for the knight's helm would silently
declare the very equivalence the source's exception exists to break, and would
invent a base rule the source never prints. No alias, variant or band rule
carries this identity either: a case-insensitive `crusad` search over the whole
repository hits only the Basha text (KB plus its 2B staging mirror) and the F063
entry; a `helm` search over the catalogue finds only `helmet`,
`bone_helmet*`, `cooking_pot_helmet` and the shields.

**Decision: one new, reference-only item record**, not a mechanic, not an
equipment-list entry, not a band:

- [`sources/knowledge/catalog/items/shields-and-defences.yaml`](../../../sources/knowledge/catalog/items/shields-and-defences.yaml) —
  new `knights_helm` (`kind: shield-or-defence`), alphabetically between
  `kite_shield` and `sea_dragon_cloak`:
  - `name: Knight's Helm`, `name_i18n.es: Yelmo de Caballero`;
  - `effect` / `effect_i18n.es`: the verbatim Basha clause plus an explicit
    publication statement — "The cited source prints no other rule for the
    helm: its own save, price, rarity, recipients and access route remain
    unpublished, so this record is reference-only and grants no selectable
    equipment";
  - `source_refs`: Karak Azgal, `manual: broheim.net`, `printed_page: 59`,
    `section: Special Equipment / Skull Busta` (the citation that actually
    mentions it);
  - `combat_status: out_of_scope` and **no `mechanic_id`**. The loader maps such
    a row to `{"status": "out_of_scope"}` with no engine option, so no consumer
    can select or execute it;
  - no price, no rarity, no recipients, no access route, no tags — nothing that
    the source does not print.

**No staging mirror was added.** The staging trees are promotion inputs; the
2B KAZ file (`sources/2B/catalog/items/savage-orc-and-skryre-gear.yaml`) is
already behind the KB (its `skull_busta` is still `out_of_scope` while the KB
record is implemented by L06), so adding a KB reference row there would invent a
staging claim the promotion contract does not require. If the coordinator wants
the row mirrored, that is a staging/promotion decision, not a data requirement.

If the coordinator prefers not to carry a reference-only row until the primary
source appears, the change is a single block: `record-added.diff` is the exact
revert, and everything below still holds.

## 3. Rules and access that are actually source-backed

- **Under Basha only**: a warrior wearing a helmet hit by a Skull Busta saves
  vs stunning only on a 6; a Knight's Helm saves on a 4+. That is the sole
  documented datum of this object.
- **Nothing else is backed**: the helm's ordinary stun reaction, its price, its
  rarity, its recipients ("Crusading Knights warbands"), its access route and
  any armour bonus are not printed in any consulted source. The clause implies
  the knight's helm resists the Basha penalty (its reaction stays at 4+ while
  the ordinary helmet drops to 6+), but whether its ordinary reaction is 4+ or
  something else is undetermined. No equivalence with the ordinary helmet, the
  Cooking Pot helmet, or any fan helmet may be assumed.

## 4. Modified files and validation performed

Modified (this delivery):

- `sources/knowledge/catalog/items/shields-and-defences.yaml` (one new record;
  file was clean before the edit).
- Published artefact regenerated with the maintained generator:
  `outputs/web-public/knowledge/{knowledge-web.json, knowledge-catalogue.json,
  rules-prose.json, display-text.json}` (gitignored; deferred item count
  449 → 450).

Validation (exact commands and outputs in `validation.txt`):

- `format_yaml.py --check sources/knowledge` → 0 failures; the edited file alone
  is formatter-clean (the 3 drifting files are pre-existing and unrelated).
- `tools/mordheim-utils.py verify --structural` → green (1050 profiles).
- `pytest tests/python/knowledge/test_editorial_schemas.py test_kb_i18n.py
  test_equipment_source_absence.py` → 317 passed.
- `pytest tests/python/knowledge/test_catalog.py` → 47 passed.
- `audit_kb_conformance.py` → exit 0 (its 6 deviations are pre-existing band
  clauses, none item-related); `audit_schema_strictness.py` → exit 0 (39
  justified findings).
- `generate_knowledge_web.py` → wrote 4 outputs, 450 deferred items;
  `--check` → "check ok … is up to date".
- Web presentation, equipment surface
  (`presentation-completeness-equipment.test.tsx`): 9 of 10 tests pass,
  including every per-entry assertion over all 450 entries — `knights_helm`
  resolves a real name and effect in both locales. The one failure is the pinned
  "24 rows without description" count (now 22) and is **not caused by this
  record**: the four `carronade*` entries now resolve prose through concurrent
  uncommitted work in `packages/typescript/application/rules/{catalogue-text,
  rules-catalogue}.ts`. The pin was left untouched (foreign owner).
- `pytest tests/python/web/test_knowledge_artefact.py
  test_presentation_contract.py` → 32 passed.
- `pytest tests/python/web/test_kb_artefact_performance.py` → 1 failed / 5
  passed: its reference-stat pin (`items 388`, `campaign_sections 16`) was
  already stale before this delivery (449 items / 17 sections in the published
  artefact); this change adds exactly one item. Not refreshed, as instructed.

No engine, `compiler.py`, shared eligibility file or bundle was touched; L06's
in-progress files (`weapons-close-combat.yaml`, `combat-equipment.yaml`,
`materials-and-upgrades.yaml`) were not modified, and the delivered Skull Busta
behaviour and its tests are untouched. No semantic spec pins, budgets or foreign
manifests were refreshed. No staging document was edited.

## 5. Exact facts L07 needs

1. **The Basha interaction is the only documented rule**: on a Skull Busta hit,
   ordinary-helmet stun saves succeed only on a 6; a Knight's Helm's on a 4+.
   L06 already implements the ordinary-helmet 6+ and preserves No Pain
   (converts the injury before the helmet step) and Thick Skull (keeps its
   replacement reaction and helmet improvement); the knight's-helm 4+ is the
   admitted counterpart still missing from selection/compilation.
2. **The canonical identity now exists** as `knights_helm`, reference-only
   (`combat_status: out_of_scope`, no mechanic, no access). L07 can bind a
   mechanic to it once the base rules exist, but must not map it to
   `defence.helmet`, must not give it a price/rarity, and must not invent a
   recipient.
3. **To pass F063's close criterion** (a real Skull Busta attack distinguishing
   a failed 3 from a successful 4), L07 still needs: the helm's base reaction
   definition, at least one real recipient profile, and a real access route. All
   three remain unsourced. Until then the 4+ must not be activated through a
   fabricated ordinary-helmet fixture.
4. The same clause also remains inside `skull_busta`'s own `effect` in
   `weapons-close-combat.yaml` (unchanged); the new record adds the identity and
   the explicit publication limits, it does not move the weapon rule.

## 6. Remaining contradictions and absences

- **"Crusading Knights warbands" is unidentified.** Not in Broheim's warband
  grades, not in Strike to Stun/Mousillon, not in the KB, not in any searched
  fan archive. The phrasing suggests a family of knight warbands (possibly an
  unreleased companion to the Karak Azgal/Mousillon pair); the KAZ clause is the
  only surviving reference found.
- **Candidate leads, deliberately not adopted** (full text in
  `sources/candidates/candidates.md`): the French fan band "Bande Bretonniens"
  `Heaume / Coiffe` (20 Co, knights and Damsel only; 4+ stun save converting
  Stunned to Knocked Down, not modified by Strength; +1 armour save; −1
  Initiative) and the Italian "Mordheim Tomo 1" `Elmo da Cavaliere` (18 co,
  Raro 9, Bretonnia only — full rules not obtainable: Scribd blocks fetches and
  the community Drive copy is 404). Both are non-primary, differently named fan
  publications with no demonstrated link to the KAZ reference; treating either
  as the same object would be an invented equivalence.
- **Access limitations** for future searches: Wayback CDX timed out; the STS
  `Mordheim v1.5` PDF and `order-of-the-mare.pdf` downloads failed; Scribd
  truncates/blocks. A user-side browser session or a different archive may still
  find the original "Crusading Knights" supplement.
- **Pre-existing repository drift noticed** (not touched): the
  `test_kb_artefact_performance.py` reference-stat pin and the equipment
  "24 absent rows" pin, both already stale from concurrent catalogue/
  presentation work before this delivery.

## 7. Proposed F063 update text (coordinator; README/plan/register are read-only)

To be inserted in
[T13-execution-follow-ups.md](T13-execution-follow-ups.md#t13-f063--skull-busta-knights-helm-counterpart-is-absent-from-the-kb)
under the existing entry, keeping **Status: open**:

> - **Data part prepared — 2026-10-03:** [Knight's Helm KB report](T13-knights-helm-kb.md).
>   The Crusading Knights primary equipment source was not found in the official,
>   Broheim, Strike to Stun/Mousillon, Relics of the Crusades, Town Cryer or fan
>   corpora consulted; Karak Azgal printed p. 59 remains the only primary
>   mention. `shields-and-defences.yaml` now carries `knights_helm` as a
>   reference-only record (`combat_status: out_of_scope`, no mechanic, no
>   price/rarity/recipients/access), holding the verbatim Basha clause and
>   stating that the helm's own rules are unpublished; the ordinary helmet is
>   not a substitute and no equivalence may be adopted from the non-primary fan
>   leads (Italian `Elmo da Cavaliere`, French `Heaume`, full texts in the
>   evidence). **Resume:** L07 decides whether to adopt a documented lead or
>   continue the source hunt; a real 3-vs-4 attack still requires the base
>   reaction, a real recipient profile and a real access route. **Close when:**
>   unchanged. The item is not claimed implemented or mapped.
