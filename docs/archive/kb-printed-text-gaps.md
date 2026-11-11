# Worklist: printed-text gaps between the clause register and the knowledge base

Generated 2026-11-10 from `sources/knowledge/verification/clause-contracts.csv` matched against every YAML file under `sources/knowledge/`. Regenerate by re-running the text-match analysis; this file is a review artifact, not a registry.

## Purpose

The clause register quotes printed rule text (`clause_text`); the knowledge base stores the same text in `effect`/`effect_i18n` fields. For 4,260 of 4,556 register rows the two agree verbatim (or up to punctuation). The 296 items below are the remainder: places where the register asserts printed text that the KB does not contain. Each one is either a lossy paraphrase (the register condensed text the KB already has), a genuine KB extraction gap (printed text never reached the KB), or structured-data equivalence (the fact exists in the KB as a field, not prose). Until each item is dispositioned, the KB cannot be treated as the single source of printed text, and the register cannot be slimmed to a reference-only join table.

## Applied corrections and adopted decisions — 2026-11-10

This worklist preserves the original 296-item review snapshot and its dispositions (**267 D1, 27 D3, 2 D4; no D2**). The original `register text`, KB excerpts and review-stage verification paragraphs below are historical evidence, not the current CSV contents. Per-entry `resolution` lines record the applied follow-up and supersede the review-stage statements that corrections were still pending.

The user authorised retiring false/editorial rows, retaining both Bone Helmets as ordinary Helmets, and granting a Possessed with Extra Arm its additional natural attack even with an empty extra hand. The user also chose to correct Sunstaff Lustria's catalogue while leaving motor support pending. These decisions are recorded in `docs/decisions/design-rulings.md`.

The reviewed direct CSV edit (outside the protected-field apply tool) retired **18 rows**: ten cross-item copies, five obsolete missing-text annotations (two Bone Helmets and three recovered robe entries), two inherited-rule scope comments and the spurious Instinctual Violence All Alone/reroll clause. It corrected **17 retained rows**, including the campaign Extra Arm contract outside this 296-item snapshot. The register now contains **4,538 rows**, down from 4,556; retained identities, ordering and source fingerprints are unchanged, and untouched physical records were preserved. The ordinary apply tool still protects source columns and conserves rows; its unrelated fixed total was removed so it can operate on the corrected register.

All 27 D3 follow-ups are applied: fifteen D3 rows retired and twelve corrected. Three additional D1 extraction placeholders were retired because their recovered own-binding clauses remain. Four other retained snapshot rows were clarified (Watchmen, the two Bone Helmet aliases and the recovered Eshin clause); the campaign companion makes up the seventeenth corrected row. The original disposition counts remain a review inventory, not counts of newly added rules. No rule paragraphs were fabricated to preserve a row count.

Extra Arm's construction bug and its existing regression check were corrected. Sunstaff Lustria now carries the previously verified Town Cryer #15 profile and no longer executes as Brazier Iron. Its dedicated melee implementation is the **only remaining follow-up from this worklist**, explicitly deferred by the user and tracked in `TODO.md`; the catalogue's nonexecuting status is not a ruling excluding its printed melee capability. No further PDF investigation was performed during this correction batch.

### Correction-batch verification

- `python3 tools/setup_worktree.py --check`: checkout-local environment validated before Python checks.
- `.venv/bin/python -u -m pytest tests/knowledge/test_clause_registry.py -n 2 --dist=load -q --durations=10 --tb=short`: **12 tests / 12 subtests passed** after removing the fixed total. Duplicate, baseline-loss, protected-column and concurrent-change safeguards remain covered.
- `.venv/bin/python -u -m pytest tests/construction/test_special_bindings.py::test_extra_arm_and_great_claw_enforce_their_printed_arm_rules tests/construction/test_special_bindings.py::test_mutant_grants_and_mutation_handlers_have_distinct_observables -n 2 --dist=load -q --durations=10 --tb=short`: **2 passed**. Repeated once because the user then clarified the Possessed empty-hand case; final run **2 passed**, including exactly-one-attack checks for empty hand, shield and buckler.
- `.venv/bin/python -u -m pytest tests/construction/test_weapon_variant_profiles.py::test_the_sunstaff_is_the_missile_weapon_its_source_lists -n 2 --dist=load -q --durations=10 --tb=short`: **1 passed**, proving the false executable mapping is absent.
- Focused item/simulation schema checks and real loader assertions passed for the two Sunstaff YAML files. Targeted inline Python checks passed for the live CSV schema, declared retirement/correction selection, preservation of retained identities/fingerprints and byte-for-byte conservation of all untouched records. The variable-count register query succeeds on the corrected CSV; `git diff --check` passed.

Evidence applies to revision `386c093d` plus this working-tree correction batch and the user decisions above. Earlier review evidence was reused; no full component suites, engine simulations, broad certification or register slimming were performed. Text recovery for Sunstaff is checked against the previously verified profile; no former D2 exists to re-match.

## Methodology

Work file by file (items are grouped by KB source file). For each item, compare the register clause text with the KB node cited, consulting the printed source reference where given, and record one disposition:

- **D1 — KB already covers it.** The KB effect text or structured fields express the same fact in different words. No KB edit. Mark the register clause as derived wording.
- **D2 — KB text gap.** The printed text is genuinely absent from the KB. Backfill the KB node's `effect` (and `effect_i18n` if the Spanish source is available) from the printed source cited. Never write rule text from memory or inference — only from the cited source.
- **D3 — Register-side defect.** The clause misquotes, duplicates, or does not correspond to any printed text. Record it for a reviewed register correction (`clause_text` is a protected column; corrections go through a reviewed register edit, not the apply tool).
- **D4 — Structured equivalence.** The fact lives in the KB as data (rarity, price, save value). No prose backfill; note the field.

### Quick pass (mechanical pre-triage, 2026-11-10)

A conservative automatic pass pre-filled candidates on 147 of the 296 items; at that stage 149 remained fully pending. Rules used:

- **candidate D1 (auto)**: at least 85% of the clause's content words, and every number in the clause, appear in the KB node's effect text (minimum 5 content words). These look like condensed quotes of text the KB already has. Each still needs a human confirmation that the *semantics* match — coverage of words is not coverage of meaning; tick the checkbox and replace "candidate" with the final disposition.
- **candidate D1/D2-resolved (auto)** (section A only): the KB node has gained effect text since the placeholder was authored. Confirm the new text covers the recovered binding, then record D1; if it does not, the item is still a D2.
- An initial D4 heuristic matched 3 items on node metadata rather than structured data fields and was discarded; no D4 was pre-filled.
- No item was auto-closed: at the time of this automatic pass every checkbox was open and every disposition remained a candidate until reviewed.

## Expected results

- Every item carries exactly one disposition, recorded in this file next to the item.
- All D2 items produce KB edits sourced from the cited material; after the batch, re-running the text-match analysis should classify every former D2 as a verbatim or normalised match.
- D1/D4 items justify dropping `clause_text` as stored content in the planned register slimming: the KB (plus structured fields) is then the single home of printed text, and the register keeps only its clause segmentation, contracts, consumers and evidence.
- D3 items form the reviewed register-correction batch.
- End state: the register ↔ KB text relationship is total and mechanical, with no unexplained residue.

## A. Register-acknowledged missing text (21 items)

The register itself records that the KB entry carried no printed text when the clause was authored. The clause_text is a placeholder annotation, not rulebook text.

### Section A review — 2026-11-10

The source-based easy pass adjudicated all 21 entries against current KB nodes and existing CSV contracts at revision `386c093d`: **5 D1, 14 D3, 0 D2, 2 D4**. The Watchmen consequence and robe paragraphs are already present. Ten cross-item attributions are explicitly recognised as provenance errors in the register's semantic contracts; two robe clauses retain stale generic targets, and two bone-helmet clauses are extraction-status annotations rather than printed rules. The fourteen D3 entries require reviewed correction of the register text, not new runtime grants.

The two D4 entries establish only the explicitly stored `mechanic_id: defence.helmet` alias. The cited Lizardmen equipment lists name and price the bone helmets but do not independently print their equivalence to an ordinary Helmet. That source limitation remains explicit; this pass neither invents a bone-specific effect nor certifies independent printed provenance for the alias. Canonical Helmet prose already exists in the KB.

Checked boxes record completed dispositions, not applied register corrections. No KB or protected CSV columns were changed, and no source-backed D2 backfill was needed. Verification: `git diff --check` and targeted `.venv/bin/python -` assertions passed for exactly 21 dispositions, their 5/14/0/2 counts, preserved entry identities/quotations/source references, and byte-for-byte unchanged sections B and C. No functional suites were run; there are no D2 text edits to re-match.

### `bands/mordheim/watchmen-mim/special-rules.yaml`

- [x] **rule/mordheim/watchmen-mim/band--fanatical/unimplemented.watchmen-mim.band.fanatical** · clause `fanatical-advance--scope--automatic-leadership` · scope YES
  - register text: “(auto-pass Leadership”
  - KB node: `band--fanatical` (has effect text)
  - KB effect: “Knights of Purity are vigilante crusaders hell-bent on the destruction of Chaos. Any Hero of the Watch with 30 experience points becomes a crusader of Law; Knights of Purity automatically pass all Leadership-based tests they are required to take.”
  - printed source: broheim.net / Special rules / Fanatical / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Watchmen.pdf
  - disposition: **D1** — Derived wording — Resolved derived fragment: the full band--fanatical effect and effect_i18n explicitly grant automatic success on all Leadership-based tests to Knights of Purity. The current compiler.knight-of-purity binding and CSV recipient contract restrict this to the promoted Hero; the historical fragment is not an independent quotation or a missing KB paragraph.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

### `catalog/items/shields-and-defences.yaml`

- [x] **item/bone_helmet** · clause `printed-text-missing` · scope YES
  - register text: “(no printed text supplied: the extracted entry carries an empty effect text; the rule was recovered from the binding recorded on the entry)”
  - KB node: `bone_helmet` (**no effect text**)
  - printed source: mordheimer.net / Saurus equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Register clause_text is an extraction-status annotation, not printed rule text. Cited Lizardmen Saurus equipment list lists Bone Helmet for 10 gc and supplies no unique effect paragraph. Reviewed correction: retain the absence observation as provenance, not a printed clause; no D2 text can be copied from this source.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/bone_helmet** · clause `behaves-as-a-helmet` · scope YES
  - register text: “(printed text absent; recovered from the binding to defence.helmet: the entry behaves as a helmet)”
  - KB node: `bone_helmet` (**no effect text**)
  - printed source: mordheimer.net / Saurus equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D4** — Item bone_helmet explicitly stores mechanic_id: defence.helmet. Existing catalog/items/shields-and-defences.yaml helmet.effect contains the unmodified 4+ Stunned-to-Knocked-Down save; catalog/mechanics/close-combat.yaml defence.helmet.effect also states the conversion. This closes the binding-derived fact as structured equivalence only: cited equipment list names/costs the item, without independently asserting ordinary-helmet equivalence. No invented per-item rule paragraph.
  - resolution (2026-11-10): **decision applied** — User retained the ordinary Helmet mapping. The register now stores no fabricated bone-specific quote (empty clause_text), while the explicit mechanic binding remains. See the adopted Bone Helmet ruling in docs/decisions/design-rulings.md.

- [x] **item/bone_helmet** · clause `behaves-as-eshin-assassin-robes` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.eshin-assassin-robes)”
  - KB node: `bone_helmet` (**no effect text**)
  - printed source: mordheimer.net / Saurus equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Cross-item provenance error: actual bone_helmet has only mechanic_id: defence.helmet and no armour.eshin-assassin-robes binding. CSV semantic_contract already identifies this copied clause as a provenance error and grants no armour. Cited Lizardmen equipment list supplies only the bone-helmet entry, no robe behaviour. Reviewed correction: remove/rehome this false printed clause in the register batch; preserve explanatory provenance, do not add armour to KB.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/bone_helmet** · clause `behaves-as-a-wizards-robe` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.wizard-s-robe)”
  - KB node: `bone_helmet` (**no effect text**)
  - printed source: mordheimer.net / Saurus equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Cross-item provenance error: actual bone_helmet has only mechanic_id: defence.helmet and no armour.wizard-s-robe binding. CSV semantic_contract already identifies this copied clause as a provenance error and grants no armour. Cited Lizardmen equipment list supplies only the bone-helmet entry, no robe behaviour. Reviewed correction: remove/rehome this false printed clause in the register batch; preserve explanatory provenance, do not add armour to KB.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/bone_helmet_skink_priest_only** · clause `printed-text-missing` · scope YES
  - register text: “(no printed text supplied: the extracted entry carries an empty effect text; the rule was recovered from the binding recorded on the entry)”
  - KB node: `bone_helmet_skink_priest_only` (**no effect text**)
  - printed source: mordheimer.net / Skinks equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Register clause_text is an extraction-status annotation, not printed rule text. Cited Lizardmen Skinks equipment list lists Bone Helmet (Skink Priest only) for 10 gc and supplies no unique effect paragraph. Reviewed correction: retain the absence observation as provenance, not a printed clause; no D2 text can be copied from this source.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/bone_helmet_skink_priest_only** · clause `behaves-as-a-helmet` · scope YES
  - register text: “(printed text absent; recovered from the binding to defence.helmet: the entry behaves as a helmet)”
  - KB node: `bone_helmet_skink_priest_only` (**no effect text**)
  - printed source: mordheimer.net / Skinks equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D4** — Item bone_helmet_skink_priest_only explicitly stores mechanic_id: defence.helmet. Existing catalog/items/shields-and-defences.yaml helmet.effect contains the unmodified 4+ Stunned-to-Knocked-Down save; catalog/mechanics/close-combat.yaml defence.helmet.effect also states the conversion. This closes the binding-derived fact as structured equivalence only: cited equipment list names/costs the item, without independently asserting ordinary-helmet equivalence. No invented per-item rule paragraph.
  - resolution (2026-11-10): **decision applied** — User retained the ordinary Helmet mapping. The register now stores no fabricated bone-specific quote (empty clause_text), while the explicit mechanic binding remains. See the adopted Bone Helmet ruling in docs/decisions/design-rulings.md.

- [x] **item/bone_helmet_skink_priest_only** · clause `behaves-as-eshin-assassin-robes` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.eshin-assassin-robes)”
  - KB node: `bone_helmet_skink_priest_only` (**no effect text**)
  - printed source: mordheimer.net / Skinks equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Cross-item provenance error: actual bone_helmet_skink_priest_only has only mechanic_id: defence.helmet and no armour.eshin-assassin-robes binding. CSV semantic_contract already identifies this copied clause as a provenance error and grants no armour. Cited Lizardmen equipment list supplies only the bone-helmet entry, no robe behaviour. Reviewed correction: remove/rehome this false printed clause in the register batch; preserve explanatory provenance, do not add armour to KB.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/bone_helmet_skink_priest_only** · clause `behaves-as-a-wizards-robe` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.wizard-s-robe)”
  - KB node: `bone_helmet_skink_priest_only` (**no effect text**)
  - printed source: mordheimer.net / Skinks equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D3** — Cross-item provenance error: actual bone_helmet_skink_priest_only has only mechanic_id: defence.helmet and no armour.wizard-s-robe binding. CSV semantic_contract already identifies this copied clause as a provenance error and grants no armour. Cited Lizardmen equipment list supplies only the bone-helmet entry, no robe behaviour. Reviewed correction: remove/rehome this false printed clause in the register batch; preserve explanatory provenance, do not add armour to KB.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

### `catalog/items/trollheim.yaml`

- [x] **item/eshin_assassin_clothes** · clause `printed-text-missing` · scope YES
  - register text: “(no printed text supplied: the extracted entry carries an empty effect text; the rule was recovered from the binding recorded on the entry)”
  - KB node: `eshin_assassin_clothes` (has effect text)
  - KB effect: “15 gc. Availability: Common (Silent Hunter only). These special garments are made of a noise-damping cloth. Save: the Eshin Assassin Clothes act exactly like Light Armour, granting a 6+ save, and cannot be combined with any other armour except a helmet. The Assassin's Luck: the Eshin assassin robes ”
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D1** — Derived wording — Resolved extraction placeholder: eshin_assassin_clothes now carries full effect/effect_i18n, including 6+ save, helmet-only combination exception, failed-save re-rolls and Silent Hunter availability; its mechanic_id is armour.eshin-assassin-robes. CSV semantic_contract already records recovered source chaos-in-the-streets 159/161.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired obsolete extraction-status annotation: full source paragraph is now present; actual own-binding clause remains. Original identity and annotation remain above as the retirement record.

- [x] **item/eshin_assassin_clothes** · clause `behaves-as-a-helmet` · scope YES
  - register text: “(printed text absent; recovered from the binding to defence.helmet: the entry behaves as a helmet)”
  - KB node: `eshin_assassin_clothes` (has effect text)
  - KB effect: “15 gc. Availability: Common (Silent Hunter only). These special garments are made of a noise-damping cloth. Save: the Eshin Assassin Clothes act exactly like Light Armour, granting a 6+ save, and cannot be combined with any other armour except a helmet. The Assassin's Luck: the Eshin assassin robes ”
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: the clothes bind armour.eshin-assassin-robes, not defence.helmet; their effect permits wearing a helmet but does not grant its 4+ Stunned-to-Knocked-Down roll. Withdraw/correct this attribution in reviewed register edit.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/eshin_assassin_clothes** · clause `behaves-as-eshin-assassin-robes` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.eshin-assassin-robes)”
  - KB node: `eshin_assassin_clothes` (has effect text)
  - KB effect: “15 gc. Availability: Common (Silent Hunter only). These special garments are made of a noise-damping cloth. Save: the Eshin Assassin Clothes act exactly like Light Armour, granting a 6+ save, and cannot be combined with any other armour except a helmet. The Assassin's Luck: the Eshin assassin robes ”
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D1** — Derived wording — Resolved own-binding placeholder: item effect and armour.eshin-assassin-robes both state 6+ Light Armour save, no armour combination except helmet, and re-rolls of failed saves; full source paragraph is already present in English/Spanish.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **item/eshin_assassin_clothes** · clause `behaves-as-a-wizards-robe` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.wizard-s-robe)”
  - KB node: `eshin_assassin_clothes` (has effect text)
  - KB effect: “15 gc. Availability: Common (Silent Hunter only). These special garments are made of a noise-damping cloth. Save: the Eshin Assassin Clothes act exactly like Light Armour, granting a 6+ save, and cannot be combined with any other armour except a helmet. The Assassin's Luck: the Eshin assassin robes ”
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: clothes bind armour.eshin-assassin-robes, not armour.wizard-s-robe, and their effect grants no spellcasting permission. Withdraw/correct the reviewed register attribution.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/mage_robes** · clause `printed-text-missing` · scope YES
  - register text: “(no printed text supplied: the extracted entry carries an empty effect text; the rule was recovered from the binding recorded on the entry)”
  - KB node: `mage_robes` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe grants its bearer a 6+ armour save and cannot combine its effects with any other piece of armour. Spellcasting: because they are made with magic, the robes do not prevent the caster fr”
  - printed source: khemri / Mage Equipment List / 
  - disposition: **D1** — Derived wording — Resolved extraction placeholder: mage_robes now contains full English/Spanish source text, 6+ armour save, no combination with any other armour and spellcasting permission; mechanic_id armour.mage-robes matches it. CSV records recovered Khemri paragraph at p.61, equipment list p.59.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired obsolete extraction-status annotation: full source paragraph is now present; actual own-binding clause remains. Original identity and annotation remain above as the retirement record.

- [x] **item/mage_robes** · clause `behaves-as-a-helmet` · scope YES
  - register text: “(printed text absent; recovered from the binding to defence.helmet: the entry behaves as a helmet)”
  - KB node: `mage_robes` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe grants its bearer a 6+ armour save and cannot combine its effects with any other piece of armour. Spellcasting: because they are made with magic, the robes do not prevent the caster fr”
  - printed source: khemri / Mage Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: mage_robes binds armour.mage-robes and grants no helmet stun-reaction roll; no armour may combine with it, helmet included. Withdraw/correct this attribution in reviewed register edit.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/mage_robes** · clause `behaves-as-eshin-assassin-robes` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.eshin-assassin-robes)”
  - KB node: `mage_robes` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe grants its bearer a 6+ armour save and cannot combine its effects with any other piece of armour. Spellcasting: because they are made with magic, the robes do not prevent the caster fr”
  - printed source: khemri / Mage Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: mage_robes binds armour.mage-robes, not Eshin armour; its effect has no failed-save re-roll and excludes every armour combination. Withdraw/correct the reviewed register attribution.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/mage_robes** · clause `behaves-as-a-wizards-robe` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.wizard-s-robe)”
  - KB node: `mage_robes` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe grants its bearer a 6+ armour save and cannot combine its effects with any other piece of armour. Spellcasting: because they are made with magic, the robes do not prevent the caster fr”
  - printed source: khemri / Mage Equipment List / 
  - disposition: **D3** — Stale protected clause_text cites armour.wizard-s-robe, whose helmet exception contradicts the actual item. Item mechanic_id and CSV effect_id/semantic_contract correctly use armour.mage-robes, granting 6+ armour, no combination including helmets, and spellcasting permission; reviewed correction must change the historical generic target to this own variant. No KB extraction gap remains.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **item/wizard_robe** · clause `printed-text-missing` · scope YES
  - register text: “(no printed text supplied: the extracted entry carries an empty effect text; the rule was recovered from the binding recorded on the entry)”
  - KB node: `wizard_robe` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe acts exactly like Light Armour, granting a 6+ save, but it cannot combine its effects with any other armour. Spellcasting: because they are made with magic, the robes do not prevent th”
  - printed source: chaos-in-the-streets / Arcane Society Equipment List / 
  - disposition: **D1** — Derived wording — Resolved extraction placeholder: wizard_robe now contains full English/Spanish source text, 6+ Light Armour save, no combination with any other armour and spellcasting permission; mechanic_id armour.wizard-robe matches it. CSV records recovered chaos-in-the-streets paragraph p.68 and equipment list p.167.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired obsolete extraction-status annotation: full source paragraph is now present; actual own-binding clause remains. Original identity and annotation remain above as the retirement record.

- [x] **item/wizard_robe** · clause `behaves-as-a-helmet` · scope YES
  - register text: “(printed text absent; recovered from the binding to defence.helmet: the entry behaves as a helmet)”
  - KB node: `wizard_robe` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe acts exactly like Light Armour, granting a 6+ save, but it cannot combine its effects with any other armour. Spellcasting: because they are made with magic, the robes do not prevent th”
  - printed source: chaos-in-the-streets / Arcane Society Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: wizard_robe binds armour.wizard-robe and grants no helmet stun-reaction roll; its effect excludes all other armour. Withdraw/correct this attribution in reviewed register edit.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/wizard_robe** · clause `behaves-as-eshin-assassin-robes` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.eshin-assassin-robes)”
  - KB node: `wizard_robe` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe acts exactly like Light Armour, granting a 6+ save, but it cannot combine its effects with any other armour. Spellcasting: because they are made with magic, the robes do not prevent th”
  - printed source: chaos-in-the-streets / Arcane Society Equipment List / 
  - disposition: **D3** — Cross-copied provenance error, already identified by CSV semantic_contract: wizard_robe binds armour.wizard-robe, not Eshin armour; no failed-save re-roll or helmet combination is granted. Withdraw/correct the reviewed register attribution.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

- [x] **item/wizard_robe** · clause `behaves-as-a-wizards-robe` · scope YES
  - register text: “(printed text absent; recovered from the binding to armour.wizard-s-robe)”
  - KB node: `wizard_robe` (has effect text)
  - KB effect: “The mages, after suffering many wounds in combat, have woven these magic robes for their protection. Save: the robe acts exactly like Light Armour, granting a 6+ save, but it cannot combine its effects with any other armour. Spellcasting: because they are made with magic, the robes do not prevent th”
  - printed source: chaos-in-the-streets / Arcane Society Equipment List / 
  - disposition: **D3** — Stale protected clause_text cites armour.wizard-s-robe, whose helmet exception contradicts this actual item. Item mechanic_id and CSV effect_id/semantic_contract correctly use armour.wizard-robe, granting 6+ armour, no combination including helmets, and spellcasting permission; reviewed correction must change the historical generic target to this own variant. No KB extraction gap remains.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

## B. Clause text absent from the KB (209 items)

The clause text does not appear in any KB file, verbatim or after punctuation/unicode normalisation. Either the register author paraphrased printed text the KB already encodes differently, or the KB is missing the text.

### Section B review — 2026-11-10

All 209 entries have been adjudicated against the full current KB nodes at revision `386c093d`: **200 D1, 9 D3, 0 D2, 0 D4**. D1 wording is derived rather than a verbatim printed quotation. A checked box records a completed disposition; D3 register corrections remain a reviewed follow-up, not an applied correction. No protected CSV columns or KB text were changed. Sections A and C are outside this batch.

The apparent missing effects include incorrect matches to nested runtime-effect IDs and catalogue items whose `mechanic_id` already points to canonical prose. Evidence below identifies those owning nodes or references. Disputed printed wording was checked against the cited sources; no inferred rule text was backfilled.

Verification for this documentation-only batch: `git diff --check` passed. A targeted `.venv/bin/python -` assertion check compared the edited document with its pre-edit contents at `386c093d`: exactly 209 checked entries and dispositions (200 D1 / 9 D3), no pending/candidate dispositions in B, unchanged entry identities, register quotations, KB snapshots and source references, and byte-for-byte unchanged A and C. No functional suites were run. No D2 edits exist to re-match; this review does not certify the full register or complete its future slimming.

### `bands/mordheim/adventurers-kaz/special-rules.yaml`

- [x] **rule/mordheim/adventurers-kaz/band--no-fixed-leader/unimplemented.adventurers-kaz.band.no-fixed-leader** · clause `no-fixed-leader` · scope NO
  - register text: “pre-battle D6 leader election with inter-hero rivalry restrictions”
  - KB node: `band--no-fixed-leader` (has effect text)
  - KB effect: “The Adventurers warband has no fixed leader. The adventurers argue and squabble all the time with each other about all kinds of minor things like food and gold, let alone that they can decide on their leader. When creating a warband mark each Hero (except the Imperial Captain) on the roster sheet wi”
  - printed source: broheim.net / Leader / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect specifies the pre-battle D6, numbered Heroes and Dwarf/Elf/Wizard/Barbarian Leadership rivalry restrictions.

- [x] **rule/mordheim/adventurers-kaz/barbarian--dim-witted/unimplemented.adventurers-kaz.barbarian.dim-witted** · clause `dim-witted--scope--leader-leadership-supply` · scope YES
  - register text: “effective Leadership 7 for warband members within 6"”
  - KB node: `barbarian--dim-witted` (has effect text)
  - KB effect: “If the Barbarian is the warband's leader then he has an effective Leadership of 7 for warband members within 6\" and Rout tests.”
  - printed source: broheim.net / heroes / 0-1 Barbarian / Special Rules / Dim-witted / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect expressly sets leader Barbarian Leadership to 7 for members within 6 inches and Rout tests.

### `bands/mordheim/averlanders/special-rules.yaml`

- [x] **rule/mordheim/averlanders/halflings-scouts--promotion/compiler.promoted-hero-no-strength-access** · clause `whole` · scope YES
  - register text: “A Halfling that is promoted to hero may not choose Strength skills as one of his two skill lists.”
  - KB node: `halflings-scouts--promotion` (has effect text)
  - KB effect: “A Halfling that is promoted to hero through the “The lad’s got talent” advance may not choose Strength skills as one of his two skill lists. Halflings are not known for their great strength!”
  - printed source: mordheimer.net / henchmen / 0 – 3 Halflings Scouts / Special Rules / Promotion / https://mordheimer.net/docs/warbands/grade-1a-warbands/averlander
  - disposition: **D1** — Derived wording — Effect prohibits choosing Strength among the two skill lists after The lad’s got talent promotion.

### `bands/mordheim/battle-monks-of-cathay/special-rules.yaml`

- [x] **rule/mordheim/battle-monks-of-cathay/band--battle-monks-special-skills-warmonger/unimplemented.battle-monks-of-cathay.band.battle-monks-special-skills-warmonger** · clause `warmonger` · scope NO
  - register text: “pre-battle Ld test adds D3+1 Raging Peasants; each is subject to Hatred”
  - KB node: `band--battle-monks-special-skills-warmonger` (has effect text)
  - KB effect: “The Emissary may make an Ld test before the battle. If the test is successful, D3+1 Raging Peasants join the warband for the next game (this may exceed the maximum number of warriors). Each Raging Peasant in the warband is subject to Hatred for the duration of the battle.”
  - printed source: mordheimer.net / Battle Monks Special Skills / Warmonger / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay
  - disposition: **D1** — Derived wording — Effect contains the Emissary’s successful pre-battle Ld test, D3+1 Peasants and battle-long Hatred.

- [x] **rule/mordheim/battle-monks-of-cathay/emissary--decree/unimplemented.battle-monks-of-cathay.emissary.decree** · clause `decree` · scope NO
  - register text: “leader-death replacement and purchase restriction until a new Emissary is hired”
  - KB node: `emissary--decree` (has effect text)
  - KB effect: “When the Emissary dies, a new one must be hired as soon as possible. Until you have done so, no other warriors and/or equipment may be bought. The new Emissary will then reclaim Leadership of the warband.”
  - printed source: mordheimer.net / Heroes / 1 Emissary / Special Rules / Decree / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay
  - disposition: **D1** — Derived wording — Effect requires replacement of a dead Emissary, forbids other purchases until then and restores Leadership.

### `bands/mordheim/black-dwarfs/special-rules.yaml`

- [x] **rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-tyrant/unimplemented.black-dwarfs.band.chaos-dwarf-special-skills-tyrant** · clause `tyrant` · scope NO
  - register text: “leader may re-roll a failed Rout test while not knocked down or stunned”
  - KB node: `band--chaos-dwarf-special-skills-tyrant` (has effect text)
  - KB effect: “This skill is for the Chaos Dwarf leader only. This Priest of Hashut is renowned for his tyranny. His word is absolute so his own warband fears his cruelty more then the enemy. When making a Rout test, and if led by a leader with this skill, the leader may inspire his warband to stick around. This s”
  - printed source: mordheimer.net / Chaos Dwarf special skills / tyrant / https://mordheimer.net/docs/warbands/grade-1c-warbands/black-dwarfs
  - disposition: **D1** — Derived wording — Effect explicitly permits failed Rout re-rolls only while the leader is neither knocked down nor stunned.

### `bands/mordheim/black-orcs/special-rules.yaml`

- [x] **rule/mordheim/black-orcs/band--da-boss-is-dead/unimplemented.black-orcs.band.da-boss-is-dead** · clause `da-boss-is-dead--scope--leader-succession` · scope NO
  - register text: “on Boss death a Black Orc takes over leadership”
  - KB node: `band--da-boss-is-dead` (has effect text)
  - KB effect: “If the Boss is killed, a Black Orc takes over leadership before any other warrior regardless of relative experience, and the replacement automatically gains "Oi Behave!".”
  - printed source: mordheimer.net / Special Rules / Da Boss is Dead! / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D1** — Derived wording — Effect explicitly makes a Black Orc the successor when the Boss is killed.

- [x] **rule/mordheim/black-orcs/band--da-boss-is-dead/unimplemented.black-orcs.band.da-boss-is-dead** · clause `da-boss-is-dead--scope--rule-grant` · scope YES
  - register text: “and gains Oi Behave!”
  - KB node: `band--da-boss-is-dead` (has effect text)
  - KB effect: “If the Boss is killed, a Black Orc takes over leadership before any other warrior regardless of relative experience, and the replacement automatically gains "Oi Behave!".”
  - printed source: mordheimer.net / Special Rules / Da Boss is Dead! / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D1** — Derived wording — Effect explicitly grants Oi Behave! to that successor.

- [x] **rule/mordheim/black-orcs/black-orc-boss--oi-behave/unimplemented.black-orcs.black-orc-boss.oi-behave** · clause `oi-behave` · scope NO
  - register text: “the Boss punishes a misbehaving Henchman within 6" and the Henchman adds the slap Strength to its Animosity roll”
  - KB node: `black-orc-boss--oi-behave` (has effect text)
  - KB effect: “If any Henchman fails his Animosity test within 6” of the Boss, the player may opt to have the boss stamp his authority (and clenched fist) on the situation. The misbehaving Henchman will receive an automatic hit at the strength of the Orc player’s choosing. If the Henchman is still on his feet afte”
  - printed source: mordheimer.net / heroes / 1 Black Orc Boss / Special Rules / Oi Behave! / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D1** — Derived wording — Effect contains the 6-inch failed-Animosity punishment and Strength modifier, conditional on remaining standing.

- [x] **rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions** · clause `no-leader` · scope NO
  - register text: “Orc Nuttaz can never have the Leader ability.”
  - KB node: `orc-nuttaz--savage` (has effect text)
  - KB effect: “Nuttaz must always run or charge their maximum distance towards the nearest opponent they can see. Friendly models do not block line of sight. Additionally they fight with an extra attack whilst in combat. This does not appear on their profile nor does it count towards the racial maximum. If no enem”
  - printed source: mordheimer.net / henchmen / 0 – 4 Orc Nuttaz / Special Rules / Savage / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D1** — Derived wording — Effect expressly forbids the Leader ability.

- [x] **rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions** · clause `no-rout-leadership` · scope NO
  - register text: “Orc Nuttaz cannot lend their Leadership for Rout tests.”
  - KB node: `orc-nuttaz--savage` (has effect text)
  - KB effect: “Nuttaz must always run or charge their maximum distance towards the nearest opponent they can see. Friendly models do not block line of sight. Additionally they fight with an extra attack whilst in combat. This does not appear on their profile nor does it count towards the racial maximum. If no enem”
  - printed source: mordheimer.net / henchmen / 0 – 4 Orc Nuttaz / Special Rules / Savage / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D3** — Register prohibition omits the printed exception when Nuttaz are the only models left on the board. Reviewed correction: include that exception; KB already contains it. Confirmed against cited mordheimer.net Black Orcs, Savage.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`, `conditions`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

### `bands/mordheim/bretonnian-buccaneers-sar/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-buccaneers-sar/swabbies--blimey-they-got-away/unimplemented.bretonnian-buccaneers-sar.swabbies.blimey-they-got-away** · clause `whole` · scope NO
  - register text: “If the Pirate Warband itself Routs, Swabbies who have left the table are removed from the roster.”
  - KB node: `swabbies--blimey-they-got-away` (has effect text)
  - KB effect: “If the Pirate Warband itself Routs, any Swabbies who have already left the table in previous turns are presumed to have made a successful escape, and are never seen from again. Remove them from your warband roster as if they had been killed.”
  - printed source: broheim.net / Henchmen / 0-5 Swabbies / Special Rules / Blimey they got away / https://broheim.net/downloads/warbands/supplement/sartosa/Human%20Pirates.pdf
  - disposition: **D1** — Derived wording — Effect removes escaped Swabbies from the roster if the Pirate warband routs.

### `bands/mordheim/bretonnian-chapel-guard/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--low-caste/unimplemented.bretonnian-chapel-guard.battle-pilgrims.low-caste** · clause `low-caste` · scope NO
  - register text: “Low Caste henchmen reroll The Lad's Got Talent and may never become heroes”
  - KB node: `battle-pilgrims--low-caste` (has effect text)
  - KB effect: “Battle Pilgrims are peasants, and while they are not stupid, there is a glass ceiling to what they can attain in Bretonnian society. Low Caste henchmen learn experience and advance as normal, but reroll any results of “The Lad's Got Talent”, and may never become heroes.”
  - printed source: mordheimer.net / henchmen / 0 – 5 Battle pilgrims / Special Rules / Low Caste / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect requires rerolling The Lad’s Got Talent and prohibits becoming heroes.

- [x] **rule/mordheim/bretonnian-chapel-guard/bowmen--low-caste/unimplemented.bretonnian-chapel-guard.bowmen.low-caste** · clause `low-caste` · scope NO
  - register text: “Low Caste henchmen reroll The Lad's Got Talent and may never become heroes”
  - KB node: `bowmen--low-caste` (has effect text)
  - KB effect: “Bowmen are peasants, and while they are not stupid, there is a glass ceiling to what they can attain in Bretonnian society. Low Caste henchmen learn experience and advance as normal, but reroll any results of “The Lad's Got Talent”, and may never become heroes.”
  - printed source: mordheimer.net / henchmen / 0 – 7 Bowmen / Special Rules / Low Caste / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect requires rerolling The Lad’s Got Talent and prohibits becoming heroes.

- [x] **rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--holy-relics/unimplemented.bretonnian-chapel-guard.battle-pilgrims.holy-relics** · clause `holy-relic-group-split` · scope NO
  - register text: “a Pilgrim with a relic breaks off and forms its own individual henchman group”
  - KB node: `battle-pilgrims--holy-relics` (has effect text)
  - KB effect: “Battle Pilgrims may be given a Holy Relic, regardless of the fact that henchman are not normally allowed to take Miscellaneous items. If a Battle Pilgrim owns a Holy Relic, he gains the ability Frenzy (Reminder: when frenzied, he is immune to Hatred.) It is possible to give a Holy Relic to Battle Pi”
  - printed source: mordheimer.net / henchmen / 0 – 5 Battle pilgrims / Special Rules / Holy Relics / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect ends with the relic-bearing Pilgrim splitting into an individual henchman group if there are insufficient relics for all.

- [x] **rule/mordheim/bretonnian-chapel-guard/band--virtue-of-purity/unimplemented.bretonnian-chapel-guard.band.virtue-of-purity** · clause `no-panic-and-all-alone--scope--no-panic` · scope NO
  - register text: “never panics or breaks from combat”
  - KB node: `band--virtue-of-purity` (has effect text)
  - KB effect: “A Knight may never voluntarily break from combat unless knocked down. The Knight is immune to All Alone and other mundane effects that would cause him to leave combat; magical effects that cause fleeing work normally.”
  - printed source: mordheimer.net / special rules / Virtue of Purity / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D3** — Register turns a qualified rule into an absolute prohibition. Reviewed correction: retain the knocked-down exception to voluntary breaking and the normal operation of magical fleeing. KB already has both; confirmed at cited mordheimer.net Chapel Guard, Virtue of Purity.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **rule/mordheim/bretonnian-chapel-guard/band--virtue-of-purity/unimplemented.bretonnian-chapel-guard.band.virtue-of-purity** · clause `no-panic-and-all-alone--scope--all-alone` · scope NO
  - register text: “never needs Leadership tests for fighting alone”
  - KB node: `band--virtue-of-purity` (has effect text)
  - KB effect: “A Knight may never voluntarily break from combat unless knocked down. The Knight is immune to All Alone and other mundane effects that would cause him to leave combat; magical effects that cause fleeing work normally.”
  - printed source: mordheimer.net / special rules / Virtue of Purity / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect expressly grants immunity to All Alone; clause is derived wording for that immunity.

### `bands/mordheim/bretonnian-knights-errant-mou/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-knights-errant-mou/knights-errant--brettonian-leader/unimplemented.bretonnian-knights-errant-mou.knights-errant.brettonian-leader** · clause `whole` · scope NO
  - register text: “The Knights Errant warband has no normal leader; each Knight Errant starts with D6+7 experience and the knight with the highest experience becomes the leader and follows the leader rules from then on.”
  - KB node: `knights-errant--brettonian-leader` (has effect text)
  - KB effect: “The Knights Errant warband doesn't have a leader like a normal warband has; the Knights Errant are brothers in arms and the Squires will happily follow any of the mighty knights. However as rules and scenarios confer special bonuses or rules to leaders the warband must have one. Each of the Knights ”
  - printed source: broheim.net / heroes / 1- 4 Knights Errant / Special Rules / Brettonian Leader / https://broheim.net/downloads/warbands/supplement/mousillon/Bretonnian Knights Errant.pdf
  - disposition: **D1** — Derived wording — Full effect gives D6+7 initial experience, highest roll selecting the leader and subsequent normal leader rules.

### `bands/mordheim/bretonnian-knights/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-knights/knights-errant--knights-virtue/unimplemented.bretonnian-knights.knights-errant.knights-virtue** · clause `no-panic-and-all-alone--scope--no-panic` · scope NO
  - register text: “never panics or breaks from combat”
  - KB node: `knights-errant--knights-virtue` (has effect text)
  - KB effect: “A Knight Errant is a chivalrous warrior who is superior to ordinary warriors. He will never panic and break from combat and so does not have to pass a Leadership test for being all alone.”
  - printed source: mordheimer.net / heroes / 0 – 2 Knights Errant / Special Rules / Knights Virtue / https://mordheimer.net/docs/warbands/grade-1b-warbands/bretonnian
  - disposition: **D1** — Derived wording — Effect expressly says the Knight Errant never panics and breaks from combat.

- [x] **rule/mordheim/bretonnian-knights/knights-errant--knights-virtue/unimplemented.bretonnian-knights.knights-errant.knights-virtue** · clause `no-panic-and-all-alone--scope--all-alone` · scope NO
  - register text: “never needs Leadership tests for fighting alone”
  - KB node: `knights-errant--knights-virtue` (has effect text)
  - KB effect: “A Knight Errant is a chivalrous warrior who is superior to ordinary warriors. He will never panic and break from combat and so does not have to pass a Leadership test for being all alone.”
  - printed source: mordheimer.net / heroes / 0 – 2 Knights Errant / Special Rules / Knights Virtue / https://mordheimer.net/docs/warbands/grade-1b-warbands/bretonnian
  - disposition: **D1** — Derived wording — Effect expressly removes the Leadership test for being all alone.

- [x] **rule/mordheim/bretonnian-knights/questing-knight--knights-virtue/unimplemented.bretonnian-knights.questing-knight.knights-virtue** · clause `no-panic-and-all-alone--scope--no-panic` · scope NO
  - register text: “never panics or breaks from combat”
  - KB node: `questing-knight--knights-virtue` (has effect text)
  - KB effect: “A Questing Knight is a chivalrous warrior who is superior to ordinary warriors. He will never panic and break from combat and so does not have to pass a Leadership test for being all alone.”
  - printed source: mordheimer.net / heroes / 1 Questing Knight / Special Rules / Knights Virtue / https://mordheimer.net/docs/warbands/grade-1b-warbands/bretonnian
  - disposition: **D1** — Derived wording — Effect expressly says the Questing Knight never panics and breaks from combat.

- [x] **rule/mordheim/bretonnian-knights/questing-knight--knights-virtue/unimplemented.bretonnian-knights.questing-knight.knights-virtue** · clause `no-panic-and-all-alone--scope--all-alone` · scope NO
  - register text: “never needs Leadership tests for fighting alone”
  - KB node: `questing-knight--knights-virtue` (has effect text)
  - KB effect: “A Questing Knight is a chivalrous warrior who is superior to ordinary warriors. He will never panic and break from combat and so does not have to pass a Leadership test for being all alone.”
  - printed source: mordheimer.net / heroes / 1 Questing Knight / Special Rules / Knights Virtue / https://mordheimer.net/docs/warbands/grade-1b-warbands/bretonnian
  - disposition: **D1** — Derived wording — Effect expressly removes the Leadership test for being all alone.

### `bands/mordheim/brood-of-ghurash-the-sc/special-rules.yaml`

- [x] **rule/mordheim/brood-of-ghurash-the-sc/newborns--nestlings/unimplemented.brood-of-ghurash-the-sc.newborns.nestlings** · clause `nestlings` · scope NO
  - register text: “Brood heroes with line of sight to a slain Newborn hate the killer; heroes must intercept charges at Newborns”
  - KB node: `newborns--nestlings` (has effect text)
  - KB effect: “If a Newborn is taken out of action by an enemy warrior in close combat, every Brood hero with line of sight to the poor Newborn hates the causing model until the end of the game. Heroes must always try to intercept charges at Newborns.”
  - printed source: broheim.net / 0-2 Newborns / Special Rules / Nestlings / https://broheim.net/downloads/warbands/supplement/sealedcity/Brood Of Ghurash.pdf
  - disposition: **D1** — Derived wording — Effect contains hatred of the close-combat killer for witnessing Brood Heroes and mandatory attempted interception.

### `bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml`

- [x] **rule/mordheim/call-of-the-night-haint-mim/band--requilary/unimplemented.call-of-the-night-haint-mim.band.requilary** · clause `requilary` · scope NO
  - register text: “Ethereal members deploy from the Requilary by Ld test; on destruction the warband routs”
  - KB node: `band--requilary` (has effect text)
  - KB effect: “All Ethereal members start the battle inside the Requilary. At the beginning of each turn make a Ld test using the highest Leadership available; for each point you pass by you may deploy that many members within 6 inches of the Mortis Engine. In missions where the Mortis Engine cannot be brought, th”
  - printed source: broheim.net / Special rules / Requilary / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call Of The Night Haint.pdf
  - disposition: **D1** — Derived wording — Effect contains initial Requilary occupation, turn-start Ld-based deployment and immediate rout on destruction.

### `bands/mordheim/carnival-of-chaos/special-rules.yaml`

- [x] **rule/mordheim/carnival-of-chaos/plague-cart--plague-cart/unimplemented.carnival-of-chaos.plague-cart.plague-cart** · clause `plague-cart--scope--warband-size` · scope NO
  - register text: “warband size +2”
  - KB node: `plague-cart--plague-cart` (has effect text)
  - KB effect: “While the Plague Cart is in the warband, the maximum number of warriors is increased by 2. Plague Bearers and Nurglings may re-roll Leadership tests for Daemonic Instability and add +1 to their Injury tests if taken out of action.”
  - printed source: mordheimer.net / henchmen / 0 – 1 Plague Cart / Special Rules / Plague Cart / https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos
  - disposition: **D1** — Derived wording — Effect expressly increases maximum warband size by 2 while the cart remains.

- [x] **rule/mordheim/carnival-of-chaos/plague-cart--plague-cart/unimplemented.carnival-of-chaos.plague-cart.plague-cart** · clause `plague-cart--scope--individual-effects` · scope NO
  - register text: “Plague Bearers/Nurglings re-roll Daemonic Instability Ld tests and add +1 to injuries”
  - KB node: `plague-cart--plague-cart` (has effect text)
  - KB effect: “While the Plague Cart is in the warband, the maximum number of warriors is increased by 2. Plague Bearers and Nurglings may re-roll Leadership tests for Daemonic Instability and add +1 to their Injury tests if taken out of action.”
  - printed source: mordheimer.net / henchmen / 0 – 1 Plague Cart / Special Rules / Plague Cart / https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos
  - disposition: **D1** — Derived wording — Effect expressly gives Plague Bearers and Nurglings Daemonic Instability Leadership rerolls and +1 Injury tests when out of action.

- [x] **rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle/mechanic.blessings-of-nurgle** · clause `whole--scope--blessing-price` · scope NO
  - register text: “and second and subsequent Blessings cost double.”
  - KB node: `band--blessings-of-nurgle` (has effect text)
  - KB effect: “Those that worship at the fetid altar of the Lord of Decay suffer from terrible diseases and decay, which are known as Blessings of Nurgle. Blessings of Nurgle may be bought for Tainted Ones only when they are recruited; you may not buy new Blessings for a model after recruitment. Any Tainted may ha”
  - printed source: mordheimer.net / Blessings of Nurgle / https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos
  - disposition: **D1** — Derived wording — Effect ends with the first Blessing at normal price and second/subsequent Blessings at double price.

### `bands/mordheim/channel-rats-mim/special-rules.yaml`

- [x] **rule/mordheim/channel-rats-mim/band--shadowy-traditions/unimplemented.channel-rats-mim.band.shadowy-traditions** · clause `shadowy-traditions` · scope NO
  - register text: “post-battle audience with an Old Father and permanent hero profile changes”
  - KB node: `band--shadowy-traditions` (has effect text)
  - KB effect: “The Petru is an enchanter able to summon one of the Old Fathers. Instead of searching for a rare item during the post battle sequence, the Petru can request for one of his family to be granted an audience with the Old Father. On a successful Leadership test one of the other Heroes in the warband mus”
  - printed source: broheim.net / Special Rules / Shadowy Traditions, Father-in-Darkness chart, Red Thirst / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Channel Rats.pdf
  - disposition: **D1** — Derived wording — Full effect contains the post-battle Old Father audience and permanent Father-in-Darkness profile changes.

- [x] **rule/mordheim/channel-rats-mim/band--strigany-special-skills-list/unimplemented.channel-rats-mim.band.strigany-special-skills-list** · clause `strigany-skills` · scope YES
  - register text: “Strigany skill list: Knowledge of Myths (exploration), Bull Rush, Songster, etc.”
  - KB node: `band--strigany-special-skills-list` (has effect text)
  - KB effect: “River Strigany may choose to use the following skill list instead of the standard skill lists. Knowledge of Myths and Legends: during the Exploration phase, if the Hero was not taken out of action, you may re-roll one dice, keeping the second result even if it is worse. Bull Rush: when he charges, t”
  - printed source: broheim.net / Strigany Special Skills / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Channel Rats.pdf
  - disposition: **D1** — Derived wording — Full effect lists Knowledge of Myths and Legends, Bull Rush, Songster, Prize-fighter, Animal Charmer and Infiltration.

### `bands/mordheim/clockworkers-sc/special-rules.yaml`

- [x] **rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs** · clause `need-orders` · scope NO
  - register text: “start-of-turn D6 without a friendly hero within 6 inches; 1-2 cannot move or shoot”
  - KB node: `band--constructs` (has effect text)
  - KB effect: “Clockwork constructs differ massively from living beings and follow a number of special rules: Need Orders (roll a D6 at the start of your turn for each construct without a friendly hero within 6 inches unless it is in close combat; on 1-2 the model may neither move nor shoot this turn); Immune to P”
  - printed source: broheim.net / Special skills / Constructs / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Need Orders in the full effect supplies the turn-start D6, absent friendly Hero within 6 inches and 1–2 movement/shooting restriction (excluding close combat).

- [x] **rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs** · clause `brainless` · scope NO
  - register text: “gains no experience, only physical enhancement”
  - KB node: `band--constructs` (has effect text)
  - KB effect: “Clockwork constructs differ massively from living beings and follow a number of special rules: Need Orders (roll a D6 at the start of your turn for each construct without a friendly hero within 6 inches unless it is in close combat; on 1-2 the model may neither move nor shoot this turn); Immune to P”
  - printed source: broheim.net / Special skills / Constructs / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Brainless in the effect explicitly prohibits experience and permits physical enhancement only.

- [x] **rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs** · clause `in-built-equipment` · scope YES
  - register text: “given equipment may not be removed; constructs use equipment slots”
  - KB node: `band--constructs` (has effect text)
  - KB effect: “Clockwork constructs differ massively from living beings and follow a number of special rules: Need Orders (roll a D6 at the start of your turn for each construct without a friendly hero within 6 inches unless it is in close combat; on 1-2 the model may neither move nor shoot this turn); Immune to P”
  - printed source: broheim.net / Special skills / Constructs / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — In-built Equipment in the effect explicitly prohibits removal and defines equipment slots.

- [x] **rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct** · clause `construct-psychology-immunity` · scope YES
  - register text: “Constructs are immune to Psychology.”
  - KB node: `clockwork-fiend--construct` (has effect text)
  - KB effect: “Clockwork fiends are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-1 Clockwork fiend / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / Immune to Psychology supplies the text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct** · clause `construct-poison-immunity` · scope YES
  - register text: “Constructs are unaffected by poison.”
  - KB node: `clockwork-fiend--construct` (has effect text)
  - KB effect: “Clockwork fiends are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-1 Clockwork fiend / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / Immune to Poison supplies the text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct** · clause `construct-excluded-producers--scope--in-built-equipment` · scope YES
  - register text: “the prohibition on removing already fitted equipment”
  - KB node: `clockwork-fiend--construct` (has effect text)
  - KB effect: “Clockwork fiends are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-1 Clockwork fiend / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / In-built Equipment supplies the no-removal text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct** · clause `construct-equipment-slot-capacity` · scope YES
  - register text: “The clockwork-fiend has 4 equipment slots and one armour slot; two-handed or missile weapons occupy two slots, other weapons one.”
  - KB node: `clockwork-fiend--construct` (has effect text)
  - KB effect: “Clockwork fiends are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-1 Clockwork fiend / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Composite derived wording: profiles.yaml clockwork-fiend equipment_restrictions supplies four equipment slots/one armour slot; dwarf-engineer--smithery effect supplies the two-handed/missile 2-slot and other-weapon 1-slot rule. Both are already KB prose; confirmed in Clockworkers PDF pp. 3 and 5.

- [x] **rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct** · clause `construct-psychology-immunity` · scope YES
  - register text: “Constructs are immune to Psychology.”
  - KB node: `clockwork-soldiers--construct` (has effect text)
  - KB effect: “Clockwork soldiers are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-5 Clockwork soldiers / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / Immune to Psychology supplies the text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct** · clause `construct-poison-immunity` · scope YES
  - register text: “Constructs are unaffected by poison.”
  - KB node: `clockwork-soldiers--construct` (has effect text)
  - KB effect: “Clockwork soldiers are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-5 Clockwork soldiers / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / Immune to Poison supplies the text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct** · clause `construct-excluded-producers--scope--in-built-equipment` · scope YES
  - register text: “the prohibition on removing already fitted equipment”
  - KB node: `clockwork-soldiers--construct` (has effect text)
  - KB effect: “Clockwork soldiers are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-5 Clockwork soldiers / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Construct effect explicitly incorporates band special rules; band--constructs / In-built Equipment supplies the no-removal text.

- [x] **rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct** · clause `construct-equipment-slot-capacity` · scope YES
  - register text: “The clockwork-soldiers has 2 equipment slots and one armour slot; two-handed or missile weapons occupy two slots, other weapons one.”
  - KB node: `clockwork-soldiers--construct` (has effect text)
  - KB effect: “Clockwork soldiers are constructs as described in the band special rules.”
  - printed source: broheim.net / 0-5 Clockwork soldiers / Special Rules / Construct / https://broheim.net/downloads/warbands/supplement/sealedcity/Clockworkers.pdf
  - disposition: **D1** — Derived wording — Composite derived wording: profiles.yaml clockwork-soldiers equipment_restrictions supplies two equipment slots/one armour slot; dwarf-engineer--smithery effect supplies the weapon slot-cost rule. Both are already KB prose; confirmed in Clockworkers PDF pp. 3 and 5.

### `bands/mordheim/crooked-moon-kep/special-rules.yaml`

- [x] **rule/mordheim/crooked-moon-kep/troll--always-hungry/unimplemented.crooked-moon-kep.troll.always-hungry** · clause `whole` · scope NO
  - register text: “A Troll requires an upkeep cost of 20 gold crowns after every game, with the option to count as two members instead.”
  - KB node: `troll--always-hungry` (**no effect text**)
  - printed source: broheim.net / Henchmen / 0-1 Troll / Special Rules / Always Hungry / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Crooked Moon Night Goblins.pdf
  - disposition: **D1** — Derived wording — Node rule_ref resolves to catalog/rules/special-rules.yaml shared-rule.always-hungry: full text contains 20 gc upkeep and the insufficient-gold alternative of two members/5 gc with reduced warband capacity. No local effect backfill.

### `bands/mordheim/cult-of-the-possessed/special-rules.yaml`

- [x] **rule/mordheim/cult-of-the-possessed/band--mutations/compiler.mutation-purchase-at-recruitment** · clause `whole--scope--mutation-price` · scope NO
  - register text: “and second and subsequent mutations cost double.”
  - KB node: `band--mutations` (has effect text)
  - KB effect: “Those who dwell in Mordheim soon develop horrible mutations, and the Cult of the Possessed seem to be especially susceptible. In addition, Mordheim attracts mutants from all over the Empire, who are always quick to join the Chaos covens. Most mutations are simply inconvenient or hideous, but some ma”
  - printed source: mordheimer.net / Mutations / https://mordheimer.net/docs/warbands/grade-1a-warbands/cult-of-the-possessed
  - disposition: **D1** — Derived wording — Effect ends with second and subsequent mutations bought for the same model costing double.

### `bands/mordheim/dreamwalkers-cult-of-morr-fbg/special-rules.yaml`

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--choosen-of-morr/unimplemented.dreamwalkers-cult-of-morr-fbg.band.choosen-of-morr** · clause `choosen-of-morr` · scope NO
  - register text: “warband-creation D6 ritual that may reject a dreamer and hand leadership to the Priest”
  - KB node: `band--choosen-of-morr` (has effect text)
  - KB effect: “A Priest of Morr must ALWAYS certify that each dreamer is genuine, not a heretic...or worse! which means that he must prove through a ritual that the dreamer's dreams truly come from Morr and are not the product of necromantic magic or the corruption of chaos. When creating a band of dreamwalkers, t”
  - printed source: mordheim-facebook-group / Special Rules / Choosen Of Morr / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D1** — Derived wording — Full effect gives the creation-time D6 certification ritual, rejection and Priest succession, later attempts and genuine Dreamer leadership.

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--special-skill-inured-to-horror/unimplemented.dreamwalkers-cult-of-morr-fbg.special-skill.inured-to-horror** · clause `all-alone-and-reroll` · scope NO
  - register text: “All Alone test / reroll clause carried by the same sentence”
  - KB node: `band--special-skill-inured-to-horror` (has effect text)
  - KB effect: “Only the true faithful followers of Morr know and accept death and become inured to horror. The model is immune to Fear, and need never take All Alone tests.”
  - printed source: mordheim-facebook-group / Special Skills / Inured to Horror / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D3** — Editorial annotation, not printed text: effect grants All Alone immunity and contains no reroll. Reviewed correction: replace annotation with the actual All Alone sentence and remove unsupported reroll wording.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/andanti--andanti-knowledge/mechanic.andanti-knowledge** · clause `whole` · scope YES
  - register text: “Their secret knowledge makes them skilled fighters against vampires: when fighting a vampire they get +1 to hit in close combat.”
  - KB node: `andanti--andanti-knowledge` (has effect text)
  - KB effect: “Their secret knowledge passed from member to member makes them skilled fighters against vampires. When fighting a vampire they get +1 to hit in close combat.”
  - printed source: mordheim-facebook-group / Heroes / 0-1 The Andanti / Special Rules / Andanti Knowledge / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D1** — Derived wording — Effect explicitly gives +1 to hit in close combat against a vampire; clause is condensed prose.

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--special-skill-inspiring-presence/unimplemented.dreamwalkers-cult-of-morr-fbg.special-skill.inspiring-presence** · clause `inspiring-presence-borrow` · scope YES
  - register text: “Morr Worshippers may borrow the Dreamer's Leadership within 12 inches instead of the normal 6; only the Dreamer may take this skill.”
  - KB node: `band--special-skill-inspiring-presence` (has effect text)
  - KB effect: “When a Dreamer proves to be a brave leader and truly chosen of Morr, his followers will follow their dreamer to death with unwavering courage. To represent this, Morr Worshwishpers can use the dreamer's lead if they are 12" away instead of the usual 6". (Only for Dreamer).”
  - printed source: mordheim-facebook-group / Special Skills / Inspiring Presence / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D1** — Derived wording — Effect gives the Dreamer Leadership benefit at 12 inches instead of 6 and restricts the skill to the Dreamer.

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/dreamer--guiding-dream/mechanic.guiding-dream** · clause `whole--scope--campaign-narrative` · scope NO
  - register text: “, plus the campaign assignment narrative.”
  - KB node: `dreamer--guiding-dream` (has effect text)
  - KB effect: “At the beginning of each battle, the Dreamer must roll D6 and consult the Guiding Dream table to discover what kind of vision Morr is sending him. 1 - Disturbing Vision: The vision of the previous night is clear, but incomplete. That worries the dreamer too much and he feels very tired the next day.”
  - printed source: mordheim-facebook-group / Guiding Dream / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D1** — Derived wording — Full effect includes the closing narrative about a specific action/place/time assigned by Morr and uncertain survival; clause is an editorial summary of existing narrative.

### `bands/mordheim/druchii-mic/special-rules.yaml`

- [x] **rule/mordheim/druchii-mic/noble--will-to-survive/unimplemented.druchii-mic.special.will-to-survive** · clause `will-to-survive` · scope NO
  - register text: “Ld test against a death Serious Injury result; survives but misses D3 battles”
  - KB node: `noble--will-to-survive` (has effect text)
  - KB effect: “Naggaroth is a harsh land with harsh inhabitants and weaklings are shown no mercy. This elf is able to survive by pure strength of will. If the model gets out of action and result of the Serious Injuries roll is death, make a Leadership test against unmodified Ld of the model (no holy relics etc.). ”
  - printed source: mordheim-index-catalog / Special Skills / Will to Survive / https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii
  - disposition: **D1** — Derived wording — Effect contains unmodified Ld test on a Death injury result, survival on success and D3 missed battles.

- [x] **rule/mordheim/druchii-mic/band--fey-acuity/unimplemented.druchii-mic.band.fey-acuity** · clause `whole` · scope NO
  - register text: “During the Exploration phase add +1 to the number of artifacts or wyrdstone pieces found by a Dark Elf warband, as long as at least one hero was searching.”
  - KB node: `band--fey-acuity` (has effect text)
  - KB effect: “During the Exploration phase when checking for artifacts or wyrdstone at the end of the game, add +1 to the number of pieces found by a Dark Elf warband, as long as at least one hero was searching.”
  - printed source: mordheim-index-catalog / Special Rules / Fey Acuity / https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii
  - disposition: **D1** — Derived wording — Effect explicitly adds one artifact/wyrdstone piece when at least one Hero searched.

- [x] **rule/mordheim/druchii-mic/band--slavers/unimplemented.druchii-mic.band.slavers** · clause `whole` · scope NO
  - register text: “In case of finding prisoners during the Exploration phase, Druchii may follow the rules for Skaven.”
  - KB node: `band--slavers` (has effect text)
  - KB effect: “In case of finding prisoners (roll of "333" during Exploration phase) Druchii may follow the rules for Skaven.”
  - printed source: mordheim-index-catalog / Special Rules / Slavers / https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii
  - disposition: **D1** — Derived wording — Effect explicitly allows Skaven prisoner rules after Exploration result 333; clause omits the parenthetical roll.

### `bands/mordheim/dwarf-guildsmen-kaz/special-rules.yaml`

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers** · clause `brew-fear-immunity` · scope YES
  - register text: “1-2: the warrior is immune to fear for the duration of the battle.”
  - KB node: `band--brewers` (has effect text)
  - KB effect: “A Dwarf Brewer is always able to produce a barrel of his finest brew prior to each battle. The leader will allow D3 of his heroes to drink before a battle. Nominate the models to drink and then roll a D6 to determine what type of beer he is offering. 1-2: XXXXXX A strong brew which endows the Dwarf ”
  - printed source: broheim.net / Special Rules / Brewers / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Brewers effect explicitly maps 1–2 to battle-long Fear immunity.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers** · clause `brew-frenzy` · scope YES
  - register text: “3-4 Troll Brew: for the duration of the battle the warrior is subject to frenzy.”
  - KB node: `band--brewers` (has effect text)
  - KB effect: “A Dwarf Brewer is always able to produce a barrel of his finest brew prior to each battle. The leader will allow D3 of his heroes to drink before a battle. Nominate the models to drink and then roll a D6 to determine what type of beer he is offering. 1-2: XXXXXX A strong brew which endows the Dwarf ”
  - printed source: broheim.net / Special Rules / Brewers / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Brewers effect explicitly maps 3–4 Troll Brew to battle-long Frenzy.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers** · clause `brew-characteristic` · scope YES
  - register text: “5-6 Special Brew: the warrior's Weapon Skill and Strength are both increased by +1 for the duration of the battle, never greater than 10.”
  - KB node: `band--brewers` (has effect text)
  - KB effect: “A Dwarf Brewer is always able to produce a barrel of his finest brew prior to each battle. The leader will allow D3 of his heroes to drink before a battle. Nominate the models to drink and then roll a D6 to determine what type of beer he is offering. 1-2: XXXXXX A strong brew which endows the Dwarf ”
  - printed source: broheim.net / Special Rules / Brewers / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Brewers effect explicitly maps 5–6 Special Brew to +1 WS/+1 S, duration one battle, ceiling 10.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance** · clause `inherited-combat-rules` · scope YES
  - register text: “The band inherits the Town Crier/Best of Town Crier Dwarf rules except Incomparable Miners.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules and equipment lists from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarf Guildsmen may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills listed in Town Crier 6 (or Best”
  - printed source: broheim.net / Special Rules / Dwarf Equipment Lists / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect expressly inherits Town Crier 6 / Best of Town Crier special rules except Incomparable Miners.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance** · clause `inherited-dwarf-axe` · scope YES
  - register text: “Dwarfs may use the Dwarf Axe described by the referenced Dwarf rules.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules and equipment lists from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarf Guildsmen may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills listed in Town Crier 6 (or Best”
  - printed source: broheim.net / Special Rules / Dwarf Equipment Lists / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect expressly permits Dwarf Guildsmen to use the referenced Dwarf Axe.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance** · clause `inherited-special-skill-access` · scope YES
  - register text: “Dwarf Heroes may use the referenced Dwarf Special Skills.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules and equipment lists from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarf Guildsmen may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills listed in Town Crier 6 (or Best”
  - printed source: broheim.net / Special Rules / Dwarf Equipment Lists / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect expressly permits Dwarf Heroes to use the referenced Dwarf Special Skills.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance** · clause `inherited-equipment-lists` · scope YES
  - register text: “Dwarf Guildsmen use the equipment lists from the cited compilation.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules and equipment lists from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarf Guildsmen may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills listed in Town Crier 6 (or Best”
  - printed source: broheim.net / Special Rules / Dwarf Equipment Lists / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect expressly inherits Town Crier 6 / Best of Town Crier equipment lists.

- [x] **rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance** · clause `inherited-exclusions` · scope NO
  - register text: “Movement penalties, hiring/progression bookkeeping and the expressly excluded Incomparable Miners rule do not resolve a duel.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules and equipment lists from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarf Guildsmen may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills listed in Town Crier 6 (or Best”
  - printed source: broheim.net / Special Rules / Dwarf Equipment Lists / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D3** — Engine-scope commentary about what resolves a duel is not printed rule text. Reviewed correction: move that commentary to scope rationale; the printed Incomparable Miners exclusion is already in the effect and inherited-combat-rules clause.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

### `bands/mordheim/dwarf-rangers/special-rules.yaml`

- [x] **rule/mordheim/dwarf-rangers/band--dont-trust-em/unimplemented.dwarf-rangers.band.dont-trust-em** · clause `dont-trust-em` · scope NO
  - register text: “allied Dwarf warbands are not friendly models; do not prevent All Alone tests”
  - KB node: `band--dont-trust-em` (has effect text)
  - KB effect: “In multiplayer games, Dwarf Rangers may ally with other Dwarf warbands, but models from the two warbands are never considered friendly models to each other. They can prevent each other from marching and do not prevent each other from taking All Alone tests, although they are not enemies.”
  - printed source: mordheimer.net / Special Rules / Don’t Trust ‘Em / https://mordheimer.net/docs/warbands/grade-1b-warbands/dwarf-rangers
  - disposition: **D1** — Derived wording — Effect explicitly makes allied Dwarf bands mutually non-friendly and unable to prevent each other’s All Alone tests.

### `bands/mordheim/dwarf-slayer-cult-web/special-rules.yaml`

- [x] **rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--skittish/unimplemented.dwarf-slayer-cult-web.axe-hurlers.skittish** · clause `skittish` · scope NO
  - register text: “on That Lad's Got Talent the Hurler must learn Death Wish instead of advancing”
  - KB node: `axe-hurlers--skittish` (has effect text)
  - KB effect: “As newly crowned Slayers, Hurlers do not have the skill 'Death Wish,' and suffer psychology like normal. When a Hurler gains 'That Lad's Got Talent', instead of making an immediate roll on the Hero Advance Table, he MUST learn the skill 'Death Wish.'”
  - printed source: mordheimer.net / 0-5 Axe Hurlers / Special Rules / Skittish / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect replaces the immediate Hero Advance roll after That Lad’s Got Talent with mandatory Death Wish.

- [x] **rule/mordheim/dwarf-slayer-cult-web/band--rememberer-skills/unimplemented.dwarf-slayer-cult-web.special.rememberer-skills** · clause `rememberer-skills--scope--leadership-reroll-aura` · scope YES
  - register text: “Songster Ld-reroll aura within 6"”
  - KB node: `band--rememberer-skills` (has effect text)
  - KB effect: “Songster — a Bard's rousing war songs steel the hearts of all those around him. Any friendly model within 6" of a Bard may re-roll any failed Leadership test with a +1 to Leadership, to a max of 10. This includes rout tests. Rememberer only. Song of Honor — in the postgame, if one or more Slayers in”
  - printed source: mordheimer.net / Special Skills / Songster, Song of Honor / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Songster in the effect gives friendly models within 6 inches Leadership rerolls with +1 Ld (maximum 10).

- [x] **rule/mordheim/dwarf-slayer-cult-web/band--rememberer-skills/unimplemented.dwarf-slayer-cult-web.special.rememberer-skills** · clause `rememberer-skills--scope--rout-and-experience` · scope NO
  - register text: “including Rout, and post-game experience”
  - KB node: `band--rememberer-skills` (has effect text)
  - KB effect: “Songster — a Bard's rousing war songs steel the hearts of all those around him. Any friendly model within 6" of a Bard may re-roll any failed Leadership test with a +1 to Leadership, to a max of 10. This includes rout tests. Rememberer only. Song of Honor — in the postgame, if one or more Slayers in”
  - printed source: mordheimer.net / Special Skills / Songster, Song of Honor / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Full effect explicitly includes Rout in Songster and post-game +1 Experience for heroes/henchmen in Song of Honor after a Slayer death.

- [x] **rule/mordheim/dwarf-slayer-cult-web/band--slayer-special-skills/unimplemented.dwarf-slayer-cult-web.special.slayer-special-skills** · clause `slayer-skills` · scope YES
  - register text: “Slayer hero skill list (Deathwish, Ferocious Charge, Monster Slayer, Thick Skull, ...)”
  - KB node: `band--slayer-special-skills` (has effect text)
  - KB effect: “The Slayer hero skill list (Slayers Only): Deathwish — the hero is completely immune to all psychology and never needs to test if fighting alone. Ferocious Charge — the Slayer may double his attacks on the turn in which he charges, with a -1 to-hit penalty that turn. Monster Slayer — in close combat”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Full effect contains the Slayer hero skill list including all four named examples.

- [x] **rule/mordheim/dwarf-slayer-cult-web/stubbles--skittish/unimplemented.dwarf-slayer-cult-web.stubbles.skittish** · clause `skittish` · scope NO
  - register text: “on That Lad's Got Talent the Stubble must learn Death Wish instead of advancing”
  - KB node: `stubbles--skittish` (has effect text)
  - KB effect: “As newly crowned Slayers, Stubbles do not have the skill 'Death Wish', and suffer psychology like normal. When a Stubble gains 'That Lad's Got Talent', instead of making an immediate roll on the Hero Advance Table, he MUST learn the skill 'Death Wish.'”
  - printed source: mordheimer.net / Stubbles / Special Rules / Skittish / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect replaces the immediate Hero Advance roll after That Lad’s Got Talent with mandatory Death Wish.

- [x] **rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen** · clause `promotion-shooting-skill-choice--scope--promotion-event` · scope NO
  - register text: “If an Axe Hurler rolls That Lad's Got Talent”
  - KB node: `axe-hurlers--born-marksmen` (has effect text)
  - KB effect: “If an Axe Hurler rolls a "That Lad's Got Talent" as an advancement, he may always choose Shooting skills as one of his two skill list choices. He may do this even if there are no heroes with Shooting Skills in the warband. Reminder: Even with Weapon Mastery, he may not use any missile weapons that a”
  - printed source: mordheimer.net / 0-5 Axe Hurlers / Special Rules / Born Marksmen / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect starts with the specified Axe Hurler promotion event.

- [x] **rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen** · clause `non-thrown-missile-prohibition` · scope YES
  - register text: “Even with Weapon Mastery, an Axe Hurler may not use any missile weapons that aren't thrown.”
  - KB node: `axe-hurlers--born-marksmen` (has effect text)
  - KB effect: “If an Axe Hurler rolls a "That Lad's Got Talent" as an advancement, he may always choose Shooting skills as one of his two skill list choices. He may do this even if there are no heroes with Shooting Skills in the warband. Reminder: Even with Weapon Mastery, he may not use any missile weapons that a”
  - printed source: mordheimer.net / 0-5 Axe Hurlers / Special Rules / Born Marksmen / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect ends with the exact prohibition on non-thrown missile weapons even with Weapon Mastery.

- [x] **rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/profile.equipment-restrictions** · clause `postgame` · scope NO
  - register text: “Damnable Luck: after rolling for all injuries you may reroll one result of Death for a single slayer hero or henchman, accepting the second result. Only in Victory: Slayer heroes do not gain exploration dice if they were defeated or routed.”
  - KB node: `band--slayer-rules` (has effect text)
  - KB effect: “Deathwish: Slayers seek an honorable death in combat. Unless stated otherwise, all members of this are completely immune to all psychology and never need to test if fighting alone. This includes Hatred, Frenzy & Stupidity. Damnable Luck: While Slayers SEEK death, it often eerily avoids them. In the ”
  - printed source: mordheimer.net / Special Rules / Slayer Special Rules / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Full effect contains both Damnable Luck’s single Death reroll and Only in Victory’s exploration exclusions.

- [x] **rule/mordheim/dwarf-slayer-cult-web/rememberer--not-a-slayer/unimplemented.dwarf-slayer-cult-web.rememberer.not-a-slayer** · clause `not-a-slayer` · scope YES
  - register text: “The Rememberer is not a Slayer and the Slayer rules do not apply.”
  - KB node: `rememberer--not-a-slayer` (has effect text)
  - KB effect: “A Rememberer is not a Slayer, and the slayer rules don't apply. Also, they may not learn "Slayer Only" skills, and may never be warband leader.”
  - printed source: mordheimer.net / 0-1 Rememberer / Special Rules / Not a Slayer / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect expressly states the Rememberer is not a Slayer and Slayer rules do not apply.

- [x] **rule/mordheim/dwarf-slayer-cult-web/rememberer--not-a-slayer/unimplemented.dwarf-slayer-cult-web.rememberer.not-a-slayer** · clause `no-slayer-skill-access` · scope YES
  - register text: “A Rememberer may not learn Slayer-only skills.”
  - KB node: `rememberer--not-a-slayer` (has effect text)
  - KB effect: “A Rememberer is not a Slayer, and the slayer rules don't apply. Also, they may not learn "Slayer Only" skills, and may never be warband leader.”
  - printed source: mordheimer.net / 0-1 Rememberer / Special Rules / Not a Slayer / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect expressly prohibits learning Slayer Only skills.

- [x] **rule/mordheim/dwarf-slayer-cult-web/rememberer--not-a-slayer/unimplemented.dwarf-slayer-cult-web.rememberer.not-a-slayer** · clause `no-leader` · scope NO
  - register text: “A Rememberer may never be the warband Leader.”
  - KB node: `rememberer--not-a-slayer` (has effect text)
  - KB effect: “A Rememberer is not a Slayer, and the slayer rules don't apply. Also, they may not learn "Slayer Only" skills, and may never be warband leader.”
  - printed source: mordheimer.net / 0-1 Rememberer / Special Rules / Not a Slayer / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect expressly prohibits becoming warband leader.

### `bands/mordheim/dwarf-slayers-kaz/special-rules.yaml`

- [x] **rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance** · clause `inherited-combat-rules` · scope YES
  - register text: “The band inherits the Town Crier/Best of Town Crier Dwarf rules except Incomparable Miners.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarfs may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills and Slayer heroes may also use the Slayer Special Skills, al”
  - printed source: broheim.net / Special Rules / Special Weapons / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect applies all Town Crier 6/Best of Town Crier special rules except Incomparable Miners.

- [x] **rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance** · clause `inherited-dwarf-axe` · scope YES
  - register text: “Dwarfs may use the Dwarf Axe described by the referenced Dwarf rules.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarfs may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills and Slayer heroes may also use the Slayer Special Skills, al”
  - printed source: broheim.net / Special Rules / Special Weapons / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect expressly permits the Dwarf Axe detailed in Town Crier 6/Best of Town Crier.

- [x] **rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance** · clause `inherited-special-skill-access` · scope YES
  - register text: “Dwarf Heroes may use the referenced Dwarf Special Skills; Slayer Heroes may also use the Slayer Special Skills.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarfs may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills and Slayer heroes may also use the Slayer Special Skills, al”
  - printed source: broheim.net / Special Rules / Special Weapons / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect expressly grants Dwarf Heroes Dwarf Special Skills and Slayer heroes the additional Slayer Special Skills.

- [x] **rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance** · clause `inherited-exclusions` · scope NO
  - register text: “Movement penalties, hiring/progression bookkeeping and the expressly excluded Incomparable Miners rule do not resolve a duel.”
  - KB node: `band--town-crier-6-inheritance` (has effect text)
  - KB effect: “All of the special rules from Town Crier 6 (or Best of Town Crier) apply apart from Incomparable Miners. Dwarfs may use the Dwarf Axe as detailed in Town Crier 6 (or Best of Town Crier). Dwarf Heroes may use any of the Dwarf Special Skills and Slayer heroes may also use the Slayer Special Skills, al”
  - printed source: broheim.net / Special Rules / Special Weapons / Dwarf Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D3** — This is author-written duel-scope commentary, not printed rules: the effect only excludes Incomparable Miners from inherited rules. Keep the scope reasoning in notes; remove this unsupported printed-text clause through reviewed register correction.
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

### `bands/mordheim/forest-goblins-lus/special-rules.yaml`

- [x] **rule/mordheim/forest-goblins-lus/gigantic-spider--may-ride/unimplemented.forest-goblins-lus.gigantic-spider.may-ride** · clause `mount` · scope NO
  - register text: “The Chieftain may ride the Gigantic Spider.”
  - KB node: `gigantic-spider--may-ride` (has effect text)
  - KB effect: “The Forest Goblin Chieftain may ride the Gigantic Spider using the optional mounts rules. He gains +1 armour save and moves at the spider's rate of 6. Shooting attacks hit the Chieftain on a roll of 1-2 and the spider on 3-6; in close combat the opponent may choose which to hit. The spider no longer”
  - printed source: broheim.net / 0-1 Gigantic Spider / Special Rules / May Ride / https://broheim.net/downloads/warbands/supplement/lustria/Forest Goblins.pdf
  - disposition: **D1** — Derived wording — The effect expressly lets the Forest Goblin Chieftain ride the Gigantic Spider using optional mount rules.

### `bands/mordheim/forest-goblins/special-rules.yaml`

- [x] **rule/mordheim/forest-goblins/braves--remove-animosity/unimplemented.forest-goblins.braves.remove-animosity** · clause `remove-animosity` · scope NO
  - register text: “may remove the Animosity rule instead of choosing a skill on advance”
  - KB node: `braves--remove-animosity` (has effect text)
  - KB effect: “When a Brave earns a skill advance, he may choose to remove his Animosity rule instead of choosing a skill.”
  - printed source: mordheimer.net / Forest Goblin Skill Table / Note / https://mordheimer.net/docs/warbands/grade-1b-warbands/forest-goblins
  - disposition: **D1** — Derived wording — The effect offers removal of Animosity instead of a skill when a Brave earns a skill advance.

- [x] **rule/mordheim/forest-goblins/gigantic-spider--may-ride/unimplemented.forest-goblins.gigantic-spider.may-ride** · clause `mount` · scope NO
  - register text: “The Chieftain may ride the Gigantic Spider.”
  - KB node: `gigantic-spider--may-ride` (has effect text)
  - KB effect: “The Forest Goblin Chieftain, may ride the Gigantic Spider. He gains +1 armour save, and shall move at the Gigantic Spider's rate of 6. Shooting attacks hit the Chieftain on a die roll of 1-2, and the Gigantic Spider on a 3-6. In close combat, the opponent may choose which to hit. The Gigantic Spider”
  - printed source: mordheimer.net / henchmen / 0 – 1 Gigantic Spider / Special Rules / May Ride / https://mordheimer.net/docs/warbands/grade-1b-warbands/forest-goblins
  - disposition: **D1** — Derived wording — The effect expressly permits the Forest Goblin Chieftain to ride the Gigantic Spider.

### `bands/mordheim/ghutani-rel/special-rules.yaml`

- [x] **rule/mordheim/ghutani-rel/scholar--field-of-scholarship/unimplemented.ghutani-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--exploration` · scope NO
  - register text: “Cartography exploration bonus”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Cartography in the full effect permits adding or deducting 1 from a D6 when exploring.

- [x] **rule/mordheim/ghutani-rel/scholar--field-of-scholarship/unimplemented.ghutani-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--injury-reroll` · scope NO
  - register text: “Physiology injury reroll”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Physiology in the full effect permits choosing a hero to reroll his result after all serious injuries are resolved.

- [x] **rule/mordheim/ghutani-rel/scholar--field-of-scholarship/unimplemented.ghutani-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--leader-leadership` · scope YES
  - register text: “Poetry leader Leadership”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Poetry in the full effect gives the leader +1 Leadership on his first scenario Leadership test if the warband won its previous battle.

### `bands/mordheim/grave-robbers-sylv/special-rules.yaml`

- [x] **rule/mordheim/grave-robbers-sylv/band--special-skill-instinctual-violence/unimplemented.grave-robbers-sylv.special-skill.instinctual-violence** · clause `all-alone-and-reroll` · scope NO
  - register text: “All Alone test / reroll clause carried by the same sentence”
  - KB node: `band--special-skill-instinctual-violence` (has effect text)
  - KB effect: “Having experienced countless encounters with the Undead, this warrior is hardened to terror. When charged by any Undead models, he does not have to take a Fear test. Additionally, he may nominate one of his attacks to Strike First.”
  - printed source: sylvania-supplement / Special Skills / Instinctual Violence / https://mordheimer.net/docs/warbands/grade-2a-warbands/grave-robbers
  - disposition: **D3** — The cited Instinctual Violence source and effect cover Fear immunity when charged by Undead and nominating one attack to Strike First; neither contains an All Alone test or reroll. Darkstalker is a separate rule which ignores All Alone tests, not a reroll. Delete this spurious clause via reviewed register correction. Source verified 2026-11-10: https://mordheimer.net/docs/warbands/grade-2a-warbands/grave-robbers#instinctual-violence
  - resolution (2026-11-10): **retired** — Removed from the live CSV by the user-authorised reviewed edit. Retired non-rule extraction annotation, cross-item provenance error or editorial scope commentary; rationale retained in worklist. Original identity and annotation remain above as the retirement record.

### `bands/mordheim/guild-of-disgraced-engineers-mim/special-rules.yaml`

- [x] **rule/mordheim/guild-of-disgraced-engineers-mim/expelled-engineer--inventor/unimplemented.guild-of-disgraced-engineers-mim.expelled-engineer.inventor** · clause `whole` · scope NO
  - register text: “In the Trading phase the Engineer may instead attempt to create a new invention from the Book of Bad Ideas, needing the book and the listed ingredients and passing the printed difficulty test.”
  - KB node: `expelled-engineer--inventor` (has effect text)
  - KB effect: “In the Trading phase, instead of searching for rare items or visiting a location, the Engineer may instead attempt to create a new invention from the book of bad ideas. The Engineer needs the book and the listed ingredients to do this, and must pass the difficulty test stated on the invention.”
  - printed source: broheim.net / Heroes / 1 Expelled Engineer / Special Rules / Inventor / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Guild Of Disgraced Engineers.pdf
  - disposition: **D1** — Derived wording — The effect covers Trading-phase invention creation instead of rare-item search/location visits, requiring the Book of Bad Ideas, listed ingredients and invention difficulty test.

### `bands/mordheim/lizardmen-lus/special-rules.yaml`

- [x] **rule/mordheim/lizardmen-lus/skink-priest--leader/mechanic.leader-six** · clause `leader-six` · scope YES
  - register text: “The Skink Priest is the warband leader and any Lizardmen within 6 inches may use his Leadership for any Leadership test”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “The Skink Priest is the leader of the warband; any Lizardmen within 6 inches may use his Leadership for any Leadership test. If he is killed, a new Skink Priest may be recruited, but the warband must play at least one game without a leader first.”
  - printed source: broheim.net / 1 Skink Priest / Special Rules / Leader / https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf
  - disposition: **D1** — Derived wording — The effect names the Skink Priest as leader and grants Lizardmen within 6 inches his Leadership for Leadership tests.

- [x] **rule/mordheim/lizardmen-lus/skink-priest--leader/mechanic.leader-six** · clause `leader-replacement` · scope NO
  - register text: “If the Skink Priest is killed a new Skink Priest may be recruited only after the warband has played one battle without a leader”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “The Skink Priest is the leader of the warband; any Lizardmen within 6 inches may use his Leadership for any Leadership test. If he is killed, a new Skink Priest may be recruited, but the warband must play at least one game without a leader first.”
  - printed source: broheim.net / 1 Skink Priest / Special Rules / Leader / https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf
  - disposition: **D1** — Derived wording — The effect requires at least one game without a leader before recruiting a replacement for a killed Skink Priest.

- [x] **rule/mordheim/lizardmen-lus/band--bite-attack/compiler.bite-attack** · clause `whole` · scope YES
  - register text: “The Saurus have a powerful bite attack... The bite attack always strikes last, regardless of who charged.”
  - KB node: `band--bite-attack` (has effect text)
  - KB effect: “The Saurus have a powerful bite attack, this bite attack uses the Saurus' own strength to wound and receives no penalty for not using a weapon. The bite attack always strikes last, regardless of who charged or which weapon is used, even after double-handed weapons.”
  - printed source: broheim.net / Special Rules / Bite Attack / https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf
  - disposition: **D1** — Derived wording — The full effect includes Saurus bite attacks and always striking last regardless of charge or weapon, even after double-handed weapons.

### `bands/mordheim/lizardmen/special-rules.yaml`

- [x] **rule/mordheim/lizardmen/skink-priest--leader/mechanic.leader-six** · clause `leader-six` · scope YES
  - register text: “The Skink Priest is the warband leader and any Lizardmen within 6 inches may use his Leadership for any Leadership test”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “The Skink Priest is the leader of the Warband and any Lizardmen within 6" may use his Leadership characteristic for any Leadership tests. If the Skink Priest is killed you may recruit a new Skink Priest but you must play at least one game without the leader to give him time to join up.”
  - printed source: mordheimer.net / heroes / 1 Skink Priest / Special Rules / Leader / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D1** — Derived wording — The effect names the Skink Priest as leader and grants Lizardmen within 6 inches his Leadership for Leadership tests.

- [x] **rule/mordheim/lizardmen/skink-priest--leader/mechanic.leader-six** · clause `leader-replacement` · scope NO
  - register text: “If the Skink Priest is killed a new Skink Priest may be recruited only after the warband has played one battle without a leader”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “The Skink Priest is the leader of the Warband and any Lizardmen within 6" may use his Leadership characteristic for any Leadership tests. If the Skink Priest is killed you may recruit a new Skink Priest but you must play at least one game without the leader to give him time to join up.”
  - printed source: mordheimer.net / heroes / 1 Skink Priest / Special Rules / Leader / https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
  - disposition: **D1** — Derived wording — The effect requires at least one game without the leader before a replacement Skink Priest joins.

### `bands/mordheim/low-kings-mim/special-rules.yaml`

- [x] **rule/mordheim/low-kings-mim/guttersnipes--tea-leaf/unimplemented.low-kings-mim.guttersnipes.tea-leaf** · clause `tea-leaf` · scope NO
  - register text: “may steal one item during the post-battle sequence”
  - KB node: `guttersnipes--tea-leaf` (has effect text)
  - KB effect: “Naturally thieves are most adept at picking pockets! A Guttersnipe may attempt to steal one item during the post battle sequence. Choose any item; if it is a common item the Guttersnipe successfully steals it on a 2+ on a D6. Rare items are successfully stolen by rolling higher than the availability”
  - printed source: broheim.net / Heroes / 0-2 Guttersnipes / Special Rules / Tea-Leaf! / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Low Kings.pdf
  - disposition: **D1** — Derived wording — The effect expressly permits a Guttersnipe to attempt stealing one item in the post-battle sequence and retains the success/capture conditions.

### `bands/mordheim/lustrian-reavers/special-rules.yaml`

- [x] **rule/mordheim/lustrian-reavers/reaver-beastmaster--war-beasts/unimplemented.lustrian-reavers.reaver-beastmaster.war-beasts** · clause `war-beasts-hiring` · scope NO
  - register text: “War Beasts count towards maximum size and must initially be bought with the Beastmaster”
  - KB node: `reaver-beastmaster--war-beasts` (has effect text)
  - KB effect: “If the warband includes a Reaver Beastmaster, it may include up to 2 War Beasts in total. They count towards the warband's maximum size, must initially be bought with the Beastmaster, may be replaced if killed, and may use the Beastmaster's Leadership while within 6 inches.”
  - printed source: mordheimer.net / Heroes / 0 – 1 Reaver Beastmaster / Special Rules / War Beasts / https://mordheimer.net/docs/warbands/grade-1c-warbands/lustrian-reavers
  - disposition: **D1** — Derived wording — The effect counts War Beasts toward maximum warband size and requires initially buying them with the Beastmaster.

### `bands/mordheim/marauders-of-chaos/special-rules.yaml`

- [x] **rule/mordheim/marauders-of-chaos/band--mark-of-onogal/trait.mark-of-onogal-the-crow** · clause `mark-admitted-effects` · scope YES
  - register text: “A marked leader gains +1 Toughness and is immune to poison. A Seer with this mark is immune to poison.”
  - KB node: `band--mark-of-onogal` (has effect text)
  - KB effect: “A marked leader gains +1 Toughness, may re-roll once on the Serious Injuries table, and is immune to poison. A Seer with this mark is immune to poison. Ritual details are intentionally not modelled here.”
  - printed source: mordheimer.net / Mark of the Dark Gods / Mark of Onogal the Crow / https://mordheimer.net/docs/warbands/grade-1c-warbands/marauders-of-chaos
  - disposition: **D1** — Derived wording — The effect gives a marked leader +1 Toughness and poison immunity, and a marked Seer poison immunity.

- [x] **rule/mordheim/marauders-of-chaos/band--mark-of-onogal/trait.mark-of-onogal-the-crow** · clause `serious-injuries-reroll` · scope NO
  - register text: “A marked leader may re-roll once on the Serious Injuries table.”
  - KB node: `band--mark-of-onogal` (has effect text)
  - KB effect: “A marked leader gains +1 Toughness, may re-roll once on the Serious Injuries table, and is immune to poison. A Seer with this mark is immune to poison. Ritual details are intentionally not modelled here.”
  - printed source: mordheimer.net / Mark of the Dark Gods / Mark of Onogal the Crow / https://mordheimer.net/docs/warbands/grade-1c-warbands/marauders-of-chaos
  - disposition: **D1** — Derived wording — The effect expressly allows the marked leader one Serious Injuries table reroll.

### `bands/mordheim/masters-of-horror-sylv/special-rules.yaml`

- [x] **rule/mordheim/masters-of-horror-sylv/flesh-construct--a-bit-unhinged/unimplemented.masters-of-horror-sylv.flesh-construct.a-bit-unhinged** · clause `a-bit-unhinged` · scope NO
  - register text: “must pass a Ld test to gain the experience for surviving the game”
  - KB node: `flesh-construct--a-bit-unhinged` (has effect text)
  - KB effect: “Flesh Constructs do not gain experience normally. They must make a successful Leadership test in order to gain the experience for surviving the game; dead brains can only be expected to learn so much, after all.”
  - printed source: sylvania-supplement / 0-1 Flesh Construct / Special Rules / A Bit Unhinged / https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror
  - disposition: **D1** — Derived wording — The effect requires a successful Leadership test for surviving-game experience.

- [x] **rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform** · clause `transformed-unarmed-penalties` · scope YES
  - register text: “Once transformed, the Bitten ... suffer no penalties for fighting unarmed.”
  - KB node: `the-bitten--transform` (has effect text)
  - KB effect: “Roll a D6 each turn and consult the following. Once transformed, the Bitten cast off all equipment (save for a dagger) and suffer no penalties for fighting unarmed. 1: Madness: your Bitten suffers from Stupidity this turn. If Transformed, they revert to human form. 2 to 5: Act as normal 6: Transform”
  - printed source: sylvania-supplement / 0-3 The Bitten / Special Rules / Transform / https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror
  - disposition: **D1** — Derived wording — The effect expressly removes unarmed-fighting penalties once the Bitten transforms.

- [x] **rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform** · clause `transformation-sprint` · scope NO
  - register text: “Transformed: your Bitten gains ... Sprint.”
  - KB node: `the-bitten--transform` (has effect text)
  - KB effect: “Roll a D6 each turn and consult the following. Once transformed, the Bitten cast off all equipment (save for a dagger) and suffer no penalties for fighting unarmed. 1: Madness: your Bitten suffers from Stupidity this turn. If Transformed, they revert to human form. 2 to 5: Act as normal 6: Transform”
  - printed source: sylvania-supplement / 0-3 The Bitten / Special Rules / Transform / https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror
  - disposition: **D1** — Derived wording — The effect grants Sprint alongside Frenzy on the Transformed result.

### `bands/mordheim/mazzalupo-web/special-rules.yaml`

- [x] **rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption** · clause `corruption--scope--attack-reroll` · scope YES
  - register text: “make a hitting enemy reroll one successful attack”
  - KB node: `master-of-finances--corruption` (has effect text)
  - KB effect: “Masters of finances are not good fighters but they are certainly skilled at convincing the enemy to leave them alone. When hit in close combat but before rolling to wound, the player controlling the Mazzalupo warband can give 5 gold crowns to the opponent for each model that hit the Master of financ”
  - printed source: mordheimer.net / 0-1 Master of Finances / Special Rules / Corruption / https://mordheimer.net/docs/warbands/grade-2a-warbands/mazzalupo
  - disposition: **D1** — Derived wording — The effect permits bribing each attacker for 5 crowns to reroll one successful attack roll, before rolling to wound.

- [x] **rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption** · clause `corruption--scope--psychology-immunity-limit` · scope YES
  - register text: “Psychology-immune models cannot be corrupted”
  - KB node: `master-of-finances--corruption` (has effect text)
  - KB effect: “Masters of finances are not good fighters but they are certainly skilled at convincing the enemy to leave them alone. When hit in close combat but before rolling to wound, the player controlling the Mazzalupo warband can give 5 gold crowns to the opponent for each model that hit the Master of financ”
  - printed source: mordheimer.net / 0-1 Master of Finances / Special Rules / Corruption / https://mordheimer.net/docs/warbands/grade-2a-warbands/mazzalupo
  - disposition: **D1** — Derived wording — The effect expressly prohibits corrupting models immune to Psychology.

### `bands/mordheim/merchant-caravans/special-rules.yaml`

- [x] **rule/mordheim/merchant-caravans/merchant--merchant/unimplemented.merchant-caravans.merchant.merchant** · clause `merchant` · scope NO
  - register text: “the Merchant is always the warband leader; succession and Merchant-specific effects”
  - KB node: `merchant--merchant` (has effect text)
  - KB effect: “The Merchant is always the warband's leader. Leadership succession and Merchant-specific effects are defined by the warband's Merchant rule.”
  - printed source: mordheimer.net / Heroes / 1 Merchant / Special Rules / Merchant / https://mordheimer.net/docs/warbands/grade-1c-warbands/merchant-caravans
  - disposition: **D1** — Derived wording — The effect states that the Merchant is always leader and refers succession/Merchant consequences to the Merchant rule.

- [x] **rule/mordheim/merchant-caravans/band--merchant-leadership/unimplemented.merchant-caravans.band.merchant-leadership** · clause `merchant-succession` · scope NO
  - register text: “leader replacement, Merchant special rule and Apprentice purchase”
  - KB node: `band--merchant-leadership` (has effect text)
  - KB effect: “The Merchant is the warband leader and warriors within 6" may use his Leadership for Leadership tests. If the Merchant permanently leaves the warband, determine a new leader normally. The new leader gains the Merchant special rule, counts as a Merchant for all purposes, and may choose Merchant Speci”
  - printed source: mordheimer.net / Special rules / Merchant / https://mordheimer.net/docs/warbands/grade-1c-warbands/merchant-caravans
  - disposition: **D1** — Derived wording — The full effect covers replacement after permanent departure, Merchant rule/status/special skills for the new leader and compulsory Apprentice purchase if no model qualifies.

### `bands/mordheim/muzil-rel/special-rules.yaml`

- [x] **rule/mordheim/muzil-rel/scholar--field-of-scholarship/unimplemented.muzil-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--exploration` · scope NO
  - register text: “Cartography exploration bonus”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Cartography in the full effect permits adding or deducting 1 from a D6 when exploring.

- [x] **rule/mordheim/muzil-rel/scholar--field-of-scholarship/unimplemented.muzil-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--injury-reroll` · scope NO
  - register text: “Physiology injury reroll”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Physiology in the full effect permits choosing a hero to reroll his result after serious injuries resolve.

- [x] **rule/mordheim/muzil-rel/scholar--field-of-scholarship/unimplemented.muzil-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--leader-leadership` · scope YES
  - register text: “Poetry leader Leadership”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Poetry in the full effect gives the leader +1 Leadership on the first scenario Leadership test after winning the previous battle.

### `bands/mordheim/necrarchs-mou/special-rules.yaml`

- [x] **rule/mordheim/necrarchs-mou/skeleton--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “Skeletons may only ever use one weapon at a time.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — The worklist resolver selected runtime effect ID profile.equipment-restrictions rather than owning rule skeleton--equipment-restrictions. Its existing effect says skeletons may only use one weapon at a time; runtime also has max_active_one_handed_weapons: 1. Correct the worklist node reference, no KB backfill.

### `bands/mordheim/night-goblins-web/special-rules.yaml`

- [x] **rule/mordheim/night-goblins-web/snotlings--insignificant/unimplemented.night-goblins-web.snotlings.insignificant** · clause `insignificant` · scope NO
  - register text: “count as 1 model for Rout and maintenance, half an experience point, ignored for shooting priority”
  - KB node: `snotlings--insignificant` (has effect text)
  - KB effect: “Nobody cares about the Snotlings. All Snotlings in the warband count as 1 model for rout tests purposes and warband maintenance costs. Each Snotling is worth half an experience point, rounded down at the end of the battle. Snotlings may be ignored for shooting priority purposes. Snotlings never gain”
  - printed source: mordheimer.net / Henchmen / 0 – 5 Snotlings / Special Rules / Insignificant / https://mordheimer.net/docs/warbands/grade-1c-warbands/night-goblins-web
  - disposition: **D1** — Derived wording — The effect retains counting all Snotlings as one for Rout/maintenance, half an experience point each rounded down post-battle, and exemption from shooting priority.

- [x] **rule/mordheim/night-goblins-web/squig-herder--master-herder/unimplemented.night-goblins-web.squig-herder.master-herder** · clause `master-herder` · scope NO
  - register text: “recovery-phase Ld test to regain control of out-of-control Squigs within range”
  - KB node: `squig-herder--master-herder` (has effect text)
  - KB effect: “During the recovery phase, any out of control Cave Squigs or Great Squigs in the herder's control range (6", or 12" with a Squig Prodder) will stop running amok, and may be controlled normally, if the Herder can pass a Leadership test.”
  - printed source: mordheimer.net / Heroes / 0 – 1 Squig Herder / Special Rules / Master Herder / https://mordheimer.net/docs/warbands/grade-1c-warbands/night-goblins-web
  - disposition: **D1** — Derived wording — The effect describes a recovery-phase Leadership test to regain control of out-of-control Cave/Great Squigs within 6 inches (12 with a Squig Prodder).

- [x] **rule/mordheim/night-goblins-web/boss--da-biggest-boss/profile.skill-access** · clause `whole` · scope YES
  - register text: “The Boss... may choose Strength skills. No other member of the warband except the current leader may ever use Strength skills.”
  - KB node: `boss--da-biggest-boss` (has effect text)
  - KB effect: “The Boss is so big, compared to other Night Goblins that is, that they may choose Strength skills. If the Boss dies, the promoted leader will gain this rule. No other member of the warband except the current leader may ever use Strength skills.”
  - printed source: mordheimer.net / Heroes / 1 Boss / Special Rules / Da Biggest Boss / https://mordheimer.net/docs/warbands/grade-1c-warbands/night-goblins-web
  - disposition: **D1** — Derived wording — The effect expressly reserves Strength skill access for the Boss/current leader and transfers the rule on succession.

### `bands/mordheim/nipponese-expedition-web/special-rules.yaml`

- [x] **rule/mordheim/nipponese-expedition-web/band--nippon-special-skills/unimplemented.nipponese-expedition-web.special.nippon-special-skills** · clause `nippon-skills` · scope YES
  - register text: “Nippon skill list including Death before Dishonor and Iaijutsu”
  - KB node: `band--nippon-special-skills` (has effect text)
  - KB effect: “Nippon Warband members may choose to use the following skill list instead of the standard skill lists. Death before Dishonor: once per grim engagement, when fate decrees their demise in the swirling melee, they unleash a final barrage of strikes before the void claims them. If this model would be re”
  - printed source: mordheimer.net / Nippon Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/nipponese-expedition
  - disposition: **D1** — Derived wording — The full Nippon Special Skills effect includes both Death before Dishonor and Iaijutsu, with their rules.

### `bands/mordheim/ogre-hunting-party-web/special-rules.yaml`

- [x] **rule/mordheim/ogre-hunting-party-web/band--ideas-above-their-station/unimplemented.ogre-hunting-party-web.band.ideas-above-their-station** · clause `ideas-above-their-station` · scope NO
  - register text: “on Hunter death the highest-Ld Gnoblar takes over; a replacement may be bought”
  - KB node: `band--ideas-above-their-station` (has effect text)
  - KB effect: “If the Ogre Hunter is killed, the Gnoblar with the highest leadership takes over as leader (or, if tied, the Gnoblar with the highest experience takes over). A replacement Ogre Hunter may be purchased, in which case he becomes the new leader.”
  - printed source: mordheimer.net / Special Rules / Ideas Above Their Station / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — The effect names the highest-Leadership Gnoblar as successor (experience breaks ties) and permits a replacement Ogre Hunter to take leadership.

- [x] **rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills** · clause `ogre-skill-list-rest` · scope YES
  - register text: “Scent Hound, Maneater, Bellowing Roar, Set Traps and Infiltration”
  - KB node: `band--ogre-hunting-skills` (has effect text)
  - KB effect: “Crude Belch: Ogres and Gnoblars eat almost anything. A Hero with this 'condition' may unleash his noxious fumes on all enemies engaged in close combat. Those that do not pass a Ld test suffer a -1 'to hit' modifier for the turn. The Hero must wait until a new enemy engages him in combat before he re”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — The full skill-list effect contains Scent Hound, Maneater, Bellowing Roar, Set Traps and Infiltration and their rules.

- [x] **rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills** · clause `crude-belch` · scope YES
  - register text: “Crude Belch: A Hero with this condition may unleash his noxious fumes on all enemies engaged in close combat; those failing a Ld test suffer -1 to hit for the turn.”
  - KB node: `band--ogre-hunting-skills` (has effect text)
  - KB effect: “Crude Belch: Ogres and Gnoblars eat almost anything. A Hero with this 'condition' may unleash his noxious fumes on all enemies engaged in close combat. Those that do not pass a Ld test suffer a -1 'to hit' modifier for the turn. The Hero must wait until a new enemy engages him in combat before he re”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — Crude Belch in the effect targets enemies engaged in close combat and gives those failing Leadership -1 to hit for the turn.

- [x] **rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills** · clause `bull-charge` · scope YES
  - register text: “Bull Charge: when charging, an Ogre with this skill may attempt a single attack with +1 to hit rather than his normal attacks; if successful the enemy is automatically knocked down.”
  - KB node: `band--ogre-hunting-skills` (has effect text)
  - KB effect: “Crude Belch: Ogres and Gnoblars eat almost anything. A Hero with this 'condition' may unleash his noxious fumes on all enemies engaged in close combat. Those that do not pass a Ld test suffer a -1 'to hit' modifier for the turn. The Hero must wait until a new enemy engages him in combat before he re”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — Bull Charge in the effect replaces normal attacks with one charging attack at +1 to hit and automatic knockdown on success.

- [x] **rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills** · clause `netter` · scope NO
  - register text: “Netter: each game the Gnoblar hero starts with 3 Nets, which may not be sold or traded and are restored each game.”
  - KB node: `band--ogre-hunting-skills` (has effect text)
  - KB effect: “Crude Belch: Ogres and Gnoblars eat almost anything. A Hero with this 'condition' may unleash his noxious fumes on all enemies engaged in close combat. Those that do not pass a Ld test suffer a -1 'to hit' modifier for the turn. The Hero must wait until a new enemy engages him in combat before he re”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — Netter in the effect grants three nets each game to Gnoblar heroes, forbids sale/trade/giving them away and restores them for the next game.

- [x] **rule/mordheim/ogre-hunting-party-web/band--greenskins/unimplemented.ogre-hunting-party-web.band.greenskins** · clause `greenskin-classification` · scope YES
  - register text: “Gnoblars count as 'Greenskins'”
  - KB node: `band--greenskins` (has effect text)
  - KB effect: “Unlike Goblins, Gnoblars do not tend to work closely with Orcs. However, for all intents and purposes, they count as 'Greenskins'. They do not suffer Animosity, but suffer the rule known as 'Bicker' (see below).”
  - printed source: mordheimer.net / Special Rules / Greenskins / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — The effect expressly counts Gnoblars as Greenskins for all intents and purposes.

- [x] **rule/mordheim/ogre-hunting-party-web/band--huuuuge/profile.equipment-restrictions** · clause `all-alone-and-rating` · scope NO
  - register text: “Ogres also ignore all alone tests... All ogres have a warband rating of 20 plus experience.”
  - KB node: `band--huuuuge` (has effect text)
  - KB effect: “Ogres are big, massive and frightening creatures. All ogre models cause fear. All ogres are Large targets. Ogres also ignore all alone tests. An ogre can never have Ithilmar or Gromril or heavy armour — they don't make it in such sizes! All ogres have a warband rating of 20 plus experience (instead ”
  - printed source: mordheimer.net / 1 Ogre Hunter / Special Rules / Huuuuge / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — The effect explicitly has Ogres ignore All Alone tests and use a warband rating of 20 plus experience instead of 5.

- [x] **rule/mordheim/ogre-hunting-party-web/ogre-hunter--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “Ogres don't have free daggers... Ogres never fight with daggers in close combat.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — The worklist resolver selected runtime effect ID profile.equipment-restrictions rather than owning rule ogre-hunter--equipment-restrictions. Its existing effect states Ogres have no free daggers and never fight with daggers in close combat. Correct the worklist node reference, no KB backfill.

- [x] **rule/mordheim/ogre-hunting-party-web/trappers--veteran-tracker/unimplemented.ogre-hunting-party-web.trappers.veteran-tracker** · clause `infiltration-warband-limit` · scope NO
  - register text: “At most one Trapper may start with Infiltration.”
  - KB node: `trappers--veteran-tracker` (has effect text)
  - KB effect: “A trapper starts with ONE of the following Special Skills: Infiltration (max 1), Set Traps, Netter, or Scent Hound. You must choose this skill upon the hero's purchase. See the Special Skills rules for details.”
  - printed source: mordheimer.net / 0-3 Trappers / Special Rules / Veteran Tracker / https://mordheimer.net/docs/warbands/grade-2a-warbands/ogre-hunting-party
  - disposition: **D1** — Derived wording — The Trapper effect offers Infiltration with an explicit max 1 restriction among its starting skill options.

### `bands/mordheim/order-of-the-mare-web/special-rules.yaml`

- [x] **rule/mordheim/order-of-the-mare-web/band--blazing-saddles/unimplemented.order-of-the-mare-web.band.blazing-saddles** · clause `whole` · scope NO
  - register text: “If the Blazing Saddles supplement is in play, the Paragon, Gallant, Esquiresses and Redeemed Knights should all automatically have the Ride skill.”
  - KB node: `band--blazing-saddles` (has effect text)
  - KB effect: “If the Blazing Saddles supplement (Town Cryer #14) is in play, the Paragon, Gallant, Esquiresses and Redeemed Knights should all automatically have the Ride skill. In addition, the Order of the Mare warbands should be allowed to ignore the normal warband limitation of two mounts in areas of dense te”
  - printed source: mordheimer.net / A Word from the Author / Blazing Saddles / https://mordheimer.net/docs/warbands/grade-2a-warbands/order-of-the-mare
  - disposition: **D1** — Derived wording — The effect expressly grants Ride to Paragon, Gallant, Esquiresses and Redeemed Knights when Blazing Saddles is used.

- [x] **rule/mordheim/order-of-the-mare-web/pilgrims--peasants/unimplemented.order-of-the-mare-web.pilgrims.peasants** · clause `whole` · scope NO
  - register text: “Pilgrims may never become heroes. Reroll any The Lad's Got Talent results.”
  - KB node: `pilgrims--peasants` (has effect text)
  - KB effect: “While devout and loyal, pilgrims are simple peasants with no ambition other than following their chosen saint, as such may never become heroes. Reroll any The Lad's Got Talent results.”
  - printed source: mordheimer.net / Pilgrims / Special Rules / Peasants / https://mordheimer.net/docs/warbands/grade-2a-warbands/order-of-the-mare
  - disposition: **D1** — Derived wording — The effect expressly forbids Pilgrims becoming heroes and rerolls The Lad's Got Talent.

### `bands/mordheim/ostlanders/special-rules.yaml`

- [x] **rule/mordheim/ostlanders/band--ostlander-special-skills-taunt/unimplemented.ostlanders.band.ostlander-special-skills-taunt** · clause `taunt--scope--shooting-phase-producer` · scope NO
  - register text: “during the Shooting phase, taunt one enemy (LoS rules) instead of shooting”
  - KB node: `band--ostlander-special-skills-taunt` (has effect text)
  - KB effect: “After years of baiting opponents into drunken brawls, this Ostlander has learned some of most vile insults in the Empire. During the Shooting phase, the warrior may choose to taunt one enemy instead of shooting with a missile weapon or casting a spell. The warrior must be able to see the enemy and t”
  - printed source: mordheimer.net / Ostlander Special Skills / Taunt / https://mordheimer.net/docs/warbands/grade-1a-warbands/ostlander
  - disposition: **D1** — Derived wording — The full Taunt effect gives Shooting-phase taunt instead of a missile shot/spell, requires sight and applies shooting LOS/nearest-target rules.

- [x] **rule/mordheim/ostlanders/band--ostlander-special-skills-taunt/unimplemented.ostlanders.band.ostlander-special-skills-taunt** · clause `taunt--scope--leadership-test` · scope NO
  - register text: “the enemy takes a Ld test”
  - KB node: `band--ostlander-special-skills-taunt` (has effect text)
  - KB effect: “After years of baiting opponents into drunken brawls, this Ostlander has learned some of most vile insults in the Empire. During the Shooting phase, the warrior may choose to taunt one enemy instead of shooting with a missile weapon or casting a spell. The warrior must be able to see the enemy and t”
  - printed source: mordheimer.net / Ostlander Special Skills / Taunt / https://mordheimer.net/docs/warbands/grade-1a-warbands/ostlander
  - disposition: **D1** — Derived wording — The full Taunt effect explicitly makes the enemy take a Leadership test and preserves the pass/fail consequences.

### `bands/mordheim/outlaws-of-stirwood-forest-redux-fbg/special-rules.yaml`

- [x] **rule/mordheim/outlaws-of-stirwood-forest-redux-fbg/band--bow-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “Every warrior must carry a type of bow, but not crossbows, as part of their equipment.”
  - KB node: `band--bow-restrictions` (has effect text)
  - KB effect: “All warriors in an Outlaws warband may be equipped with only one missile weapon at any time. All warriors must carry a type of bow, but not crossbows, as part of their equipment. So, even if an Outlaw acquires skills that allow him to use additional ballistic weaponry, he cannot do so. The only exce”
  - printed source: mordheim-facebook-group / Special Rules / https://mordheimer.net/docs/warbands/grade-2a-warbands/outlaws-of-stirwood-forest-redux
  - disposition: **D1** — Derived wording — The effect contains the bow requirement and excludes crossbows; it also expressly exempts the Cleric. Treat the register text as a derived general-rule excerpt, retaining the Cleric exception from the owning effect.

### `bands/mordheim/pirates/special-rules.yaml`

- [x] **rule/mordheim/pirates/band--pirate-special-skills-booming-voice/unimplemented.pirates.band.pirate-special-skills-booming-voice** · clause `booming-voice` · scope NO
  - register text: “once per turn the Captain makes a pirate within 8" that failed its run-away test reroll it”
  - KB node: `swabbies--not-true-pirates` (has effect text)
  - KB effect: “Swabbies who are fleeing or Out of Action do not count when determining whether the Pirate warband must take a Rout test.”
  - printed source: mordheimer.net / Henchmen / Swabbies / Don't mind them mates / https://mordheimer.net/docs/warbands/grade-1b-warbands/pirates
  - disposition: **D1** — Derived wording — The worklist resolver points at unrelated swabbies--not-true-pirates. The actual owning node band--pirate-special-skills-booming-voice already contains the once-per-turn Captain reroll for a pirate within 8 inches who failed fleeing/rallying, plus Captain posture/combat restrictions. Correct the worklist node/source reference, no KB backfill.

### `bands/mordheim/restless-dead/special-rules.yaml`

- [x] **rule/mordheim/restless-dead/grave-guards--may-not-run/unimplemented.restless-dead.grave-guards.may-not-run** · clause `may-not-run` · scope NO
  - register text: “Grave Guards may not run but can charge normally.”
  - KB node: `grave-guards--may-not-run` (has effect text)
  - KB effect: “Grave Guards are slow undead creatures and may not run (but can charge normally).”
  - printed source: mordheimer.net / heroes / 0 - 3 Grave Guards / Special Rules / May not Run / https://mordheimer.net/docs/warbands/grade-1c-warbands/restless-dead
  - disposition: **D1** — Derived wording — The effect forbids Grave Guards running but permits normal charges.

- [x] **rule/mordheim/restless-dead/skeletons--may-not-run/unimplemented.restless-dead.skeletons.may-not-run** · clause `may-not-run` · scope NO
  - register text: “Skeletons may not run but can charge normally.”
  - KB node: `skeletons--may-not-run` (has effect text)
  - KB effect: “Skeletons are slow undead creatures and may not run (but may charge normally).”
  - printed source: mordheimer.net / henchmen / 0 - 8 Skeletons / Special Rules / May not run / https://mordheimer.net/docs/warbands/grade-1c-warbands/restless-dead
  - disposition: **D1** — Derived wording — The effect forbids Skeletons running but permits normal charges.

- [x] **rule/mordheim/restless-dead/wights--may-not-run/unimplemented.restless-dead.wights.may-not-run** · clause `may-not-run` · scope NO
  - register text: “Wights may not run but can charge normally.”
  - KB node: `wights--may-not-run` (has effect text)
  - KB effect: “Wights are slow undead creatures and may not run (but may charge normally).”
  - printed source: mordheimer.net / henchmen / 0 - 3 Wights / Special Rules / May not run / https://mordheimer.net/docs/warbands/grade-1c-warbands/restless-dead
  - disposition: **D1** — Derived wording — The effect forbids Wights running but permits normal charges.

- [x] **rule/mordheim/restless-dead/necromancer--apprentices/unimplemented.restless-dead.necromancer.apprentices** · clause `apprentices` · scope NO
  - register text: “Spell knowledge restriction for Necromancers.”
  - KB node: `necromancer--apprentices` (has effect text)
  - KB effect: “Necromancers may only ever know spells known by their Liche masters. Even if they did know spells the Liche didn't, they wouldn't dare use them for fear of their master's response for their arrogance! If the Liche is ever killed, the Necromancer can continue to learn magic spells as a normal wizard,”
  - printed source: mordheimer.net / heroes / 0 - 1 Necromancer / Special Rules / Apprentices / https://mordheimer.net/docs/warbands/grade-1c-warbands/restless-dead
  - disposition: **D1** — Derived wording — The full effect limits Necromancers to spells their Liche master knows, lifting the restriction when the Liche dies.

- [x] **rule/mordheim/restless-dead/scarecrows--animated-construct/unimplemented.restless-dead.scarecrows.animated-construct** · clause `animated-construct` · scope NO
  - register text: “Each Scarecrow must be assigned to a controller.”
  - KB node: `scarecrows--animated-construct` (has effect text)
  - KB effect: “Each Scarecrow must be assigned to either the Liche or the Necromancer as its controller, and each controller may control only one Scarecrow. Therefore two Scarecrows may only be fielded if both a Liche and a Necromancer are present. If a controller cannot participate in a battle, its Scarecrow cann”
  - printed source: mordheimer.net / henchmen / 0 - 2 Scarecrows / Special Rules / Animated Construct / https://mordheimer.net/docs/warbands/grade-1c-warbands/restless-dead
  - disposition: **D1** — Derived wording — The full effect requires each Scarecrow be assigned to the Liche or Necromancer as controller and retains controller limits and consequences.

### `bands/mordheim/sartosan-pirates-sar/special-rules.yaml`

- [x] **rule/mordheim/sartosan-pirates-sar/swabbies--blimey-they-got-away/unimplemented.sartosan-pirates-sar.swabbies.blimey-they-got-away** · clause `whole` · scope NO
  - register text: “If the Pirate Warband itself Routs, Swabbies who have left the table are removed from the roster.”
  - KB node: `swabbies--blimey-they-got-away` (has effect text)
  - KB effect: “If the Pirate Warband itself Routs, any Swabbies who have already left the table in previous turns are presumed to have made a successful escape, and are never seen from again. Remove them from your warband roster as if they had been killed.”
  - printed source: broheim.net / Henchmen / 0-5 Swabbies / Special Rules / Blimey they got away / https://broheim.net/downloads/warbands/supplement/sartosa/Human%20Pirates.pdf
  - disposition: **D1** — Derived wording — The effect removes previously escaped Swabbies from the roster as killed if the Pirate Warband itself Routs.

### `bands/mordheim/sea-ghosts-mim/special-rules.yaml`

- [x] **rule/mordheim/sea-ghosts-mim/minstrels--songster/unimplemented.sea-ghosts-mim.minstrels.songster** · clause `songster-group-emission` · scope NO
  - register text: “all friendly models within 6" of the warrior are affected”
  - KB node: `minstrels--songster` (has effect text)
  - KB effect: “Invigorating deep-sea shanties and reflective Elven lays boost the morale of all those around. Any friendly model within 6" of the warrior may re-roll any failed Leadership test with a +1 to Leadership. This includes rout tests.”
  - printed source: broheim.net / Henchmen / 0-3 Minstrels / Special Rules / Songster / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Sea%20Ghosts.pdf
  - disposition: **D1** — Derived wording — The effect gives any friendly model within 6 inches a failed Leadership test reroll with +1 Leadership, including Rout tests.

### `bands/mordheim/skaven-of-clan-moulder-web/special-rules.yaml`

- [x] **rule/mordheim/skaven-of-clan-moulder-web/band--packmasters-and-goading/unimplemented.skaven-of-clan-moulder-web.band.packmasters-and-goading** · clause `packmasters-and-goading` · scope NO
  - register text: “pre-turn Goading difficulty check and results chart against beast groups within 6"”
  - KB node: `band--packmasters-and-goading` (has effect text)
  - KB effect: “Clan Moulder Packmasters and Apprentices have access to a unique system known as "Goading," allowing them to whip their beasts into a frenzy with special effects based on success. Goading attempts are made at the very beginning of the Moulder turn, before any movement takes place, against a single m”
  - printed source: mordheimer.net / Special Rules / Packmasters and Goading; Goading / https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder
  - disposition: **D1** — Derived wording — The full effect contains pre-movement Goading against one beast/group within 6 inches, difficulty values 6/8/10 and the complete result chart.

- [x] **rule/mordheim/skaven-of-clan-moulder-web/band--clan-moulder-special-skills/unimplemented.skaven-of-clan-moulder-web.special.clan-moulder-special-skills** · clause `clan-moulder-skill-list-rest` · scope NO
  - register text: “Beastkin range doubling, Subjugator post-battle capture and Twistkin mutation purchase”
  - KB node: `band--clan-moulder-special-skills` (has effect text)
  - KB effect: “Clan Moulder heroes may choose to use the following Skill list instead of any of the standard Skill tables available to them. Black Hunger: the Hero may declare at the beginning of his turn that he is using this skill; he may add +1 attack and +D3" to the total move on his profile for the duration o”
  - printed source: mordheimer.net / Special Skills / https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder
  - disposition: **D1** — Derived wording — The full skill-list effect includes doubled Beast/Animal Handling range to 12 inches, Subjugator capture and Twistkin half-price mutation purchase.

- [x] **rule/mordheim/skaven-of-clan-moulder-web/packmaster--master-handler/unimplemented.skaven-of-clan-moulder-web.packmaster.master-handler** · clause `whole` · scope NO
  - register text: “Packmasters have access to the Goading system, plus begin with the Ride Wolf Rat skill and one additional Beast Handling skill.”
  - KB node: `packmaster--master-handler` (has effect text)
  - KB effect: “Packmasters are experts at handling all manner of twisted creatures. They have access to the Goading system detailed below, plus begin any one-off game or campaign with the Ride Wolf Rat skill and one additional Beast Handling skill (choose either Giant Rats or Wolf Rats).”
  - printed source: mordheimer.net / 1 Packmaster / Special Rules / Master Handler / https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder
  - disposition: **D1** — Derived wording — The effect grants Packmasters access to Goading, Ride Wolf Rat and an additional Beast Handling skill (Giant Rats or Wolf Rats).

- [x] **rule/mordheim/skaven-of-clan-moulder-web/rat-ogres--its-alive/unimplemented.skaven-of-clan-moulder-web.rat-ogres.its-alive** · clause `mutation-payment` · scope NO
  - register text: “The required mutation is purchased when the Rat Ogre is hired.”
  - KB node: `rat-ogres--its-alive` (has effect text)
  - KB effect: “Moulder Rat Ogres are twisted creatures ever subject to the cruel curiosity of their masters. When hired each Rat Ogre must purchase a single Mutation from the list in the Mordheim Rulebook at the listed price (see Possessed Warband section).”
  - printed source: mordheimer.net / 0-2 Rat Ogres / Special Rules / It's Alive! / https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder
  - disposition: **D1** — Derived wording — The effect expressly requires each Rat Ogre to purchase a single Mutation at the listed price when hired.

### `bands/mordheim/slavers-rel/special-rules.yaml`

- [x] **rule/mordheim/slavers-rel/band--slaves-talent-advance/unimplemented.slavers-rel.band.slaves-talent-advance** · clause `slaves-talent-advance` · scope NO
  - register text: “on Lad's Got Talent a slave takes a Ld test and may be freed and become a caravan guard”
  - KB node: `band--slaves-talent-advance` (has effect text)
  - KB effect: “Slaves will generally be ill-treated by a slave merchant. If any slave achieves the 'Lad's got the Talent' advance, then the slave must make a leadership test. If it is passed then the slave merchant sees some potential and loyalty in the slave and frees him. The slave retains his statistic line tho”
  - printed source: broheim.net / Slavers / Special rules / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — The full effect requires Leadership on Lad's Got Talent, freeing a successful slave and changing his type to caravan guard; failure becomes a eunuch.

### `bands/mordheim/snotlings-web/special-rules.yaml`

- [x] **rule/mordheim/snotlings-web/band--that-gits-got-talent/unimplemented.snotlings-web.band.that-gits-got-talent** · clause `that-gits-got-talent` · scope NO
  - register text: “on That Lad's Got Talent a Snotling learns Mob Rule and The Rigors of Leadership”
  - KB node: `band--that-gits-got-talent` (has effect text)
  - KB effect: “When a Snotling henchman gets the 'That Lad's Got Talent!' advance, they automatically learn the skills Mob Rule and The Rigors of Leadership. See Warband list for details of these skills.”
  - printed source: mordheimer.net / Special Rules / That (Git)'s Got Talent! / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The effect expressly grants Mob Rule and The Rigors of Leadership on a Snotling henchman's Lad's Got Talent advance.

- [x] **rule/mordheim/snotlings-web/bullied-goblin--mob-master/unimplemented.snotlings-web.special.mob-master** · clause `mob-master` · scope NO
  - register text: “the Hero and a Snotling Mob within 2" become Immune to Psychology; combo with Stampede”
  - KB node: `bullied-goblin--mob-master` (has effect text)
  - KB effect: “The Hero is a Master at controlling and leading the Snotlings around him as a Mob. So long as your Hero is within 2" of a Snotling Mob, both he and the Snotling Mob become Immune to Psychology exactly as if the Hero counted as a second Snotling Mob. When this skill is combined with the "Stampede" sk”
  - printed source: mordheimer.net / Snotling Special Skills / Mob Master / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The full effect grants Hero and Mob Psychology immunity within 2 inches and explains the Stampede +1-to-hit/+1-Strength combination.

- [x] **rule/mordheim/snotlings-web/bullied-goblin--mob-rule/unimplemented.snotlings-web.shared.mob-rule** · clause `mob-rule` · scope NO
  - register text: “+1 Leadership per two Snotlings within 6", to a maximum of 10”
  - KB node: `bullied-goblin--mob-rule` (has effect text)
  - KB effect: “The Hero is easily goaded on by his fellow Snotlings, and swells with courage in large groups. For every 2 Snotlings within 6" of the Hero, the Hero gains +1 Leadership, to a maximum of 10. (Note: These bonuses will stack onto the Leader's base Leadership for the purposes of the Leader skill).”
  - printed source: mordheimer.net / 1 Bullied Goblin / Special Rules / Mob Rule / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The effect explicitly gives +1 Leadership per two Snotlings within 6 inches, maximum 10.

- [x] **rule/mordheim/snotlings-web/snotling-mobs--mob-mentality/unimplemented.snotlings-web.snotling-mobs.mob-mentality** · clause `mob-mentality` · scope NO
  - register text: “two Snotling Mobs within 2" are both Immune to Psychology for the rest of the turn”
  - KB node: `snotling-mobs--mob-mentality` (has effect text)
  - KB effect: “Snotlings are infamous for becoming totally immune to being afraid of everything when they gang up into one big mass. When Snotling Mobs starts a turn within 2" of another Snotling Mob, they both become Immune to Psychology for the rest of the turn (this applies to an opponent's turn as well.)”
  - printed source: mordheimer.net / 0-3 Snotling Mobs / Special Rules / Mob Mentality / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The effect grants both Mobs Psychology immunity for the rest of the turn when they start within 2 inches, including opponent turns; the register wording is a shortened excerpt with that trigger retained in the owning effect.

### `bands/mordheim/strigoi-kaz/special-rules.yaml`

- [x] **rule/mordheim/strigoi-kaz/charnel-guard--cunning/unimplemented.strigoi-kaz.charnel-guard.cunning** · clause `weapons-training-permission` · scope YES
  - register text: “A Charnel Guard may learn Weapons Training and thereby use weapons outside its ordinary allowance.”
  - KB node: `charnel-guard--cunning` (has effect text)
  - KB effect: “Unlike ordinary ghouls a Charnel Guard can take the Weapons Training or Weapons Expert skills and learn to use any weapon.”
  - printed source: broheim.net / heroes / 0-2 Charnel Guard / Special Rules / Cunning / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect permits Charnel Guards to take Weapons Training and learn to use any weapon.

- [x] **rule/mordheim/strigoi-kaz/charnel-guard--cunning/unimplemented.strigoi-kaz.charnel-guard.cunning** · clause `weapons-expert-missile-access` · scope NO
  - register text: “A Charnel Guard may learn Weapons Expert to use additional missile weapons.”
  - KB node: `charnel-guard--cunning` (has effect text)
  - KB effect: “Unlike ordinary ghouls a Charnel Guard can take the Weapons Training or Weapons Expert skills and learn to use any weapon.”
  - printed source: broheim.net / heroes / 0-2 Charnel Guard / Special Rules / Cunning / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect permits Weapons Expert and learning any weapon; the referenced skill supplies the missile-weapon interpretation, also explained by the owning runtime exclusion reason.

### `bands/mordheim/turjuk-rel/special-rules.yaml`

- [x] **rule/mordheim/turjuk-rel/scholar--field-of-scholarship/unimplemented.turjuk-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--exploration` · scope NO
  - register text: “Cartography exploration bonus”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Cartography in the full effect permits adding or deducting 1 from a D6 when exploring.

- [x] **rule/mordheim/turjuk-rel/scholar--field-of-scholarship/unimplemented.turjuk-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--injury-reroll` · scope NO
  - register text: “Physiology injury reroll”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Derived shorthand; Physiology explicitly allows selecting a hero to re-roll his serious-injury result after all serious injuries resolve.

- [x] **rule/mordheim/turjuk-rel/scholar--field-of-scholarship/unimplemented.turjuk-rel.scholar.field-of-scholarship** · clause `field-of-scholarship--scope--leader-leadership` · scope YES
  - register text: “Poetry leader Leadership”
  - KB node: `scholar--field-of-scholarship` (has effect text)
  - KB effect: “When joining a warband, the scholar must choose the area of knowledge he specialises in. Choose one of the following. Cartography: the Scholar keeps a detailed map of where you have been; you may add or deduct 1 from a D6 when exploring. Physiology: after all serious injuries have been resolved you ”
  - printed source: broheim.net / Heroes / 0-1 Scholar / Special Rules / Field of Scholarship / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Derived shorthand; Poetry explicitly adds +1 Leadership to the leader for the first Leadership test of a scenario after winning the last battle.

- [x] **rule/mordheim/turjuk-rel/band--turjuk-leader-mount/unimplemented.turjuk-rel.band.turjuk-leader-mount** · clause `mount` · scope NO
  - register text: “Turjuk leaders are expected to own a mount.”
  - KB node: `band--turjuk-leader-mount` (has effect text)
  - KB effect: “As horses are viewed with such pride by the Turjuks, any leader of a Turjuk warband that does not own a Riding Horse or Arabian Steed will have his leadership reduced by 1.”
  - printed source: broheim.net / Arabian Tribes / Turjuk / Special Rules / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Derived shorthand; the effect penalises a Turjuk leader without a Riding Horse or Arabian Steed by -1 Leadership.

### `bands/mordheim/underworld-alliance-mim/special-rules.yaml`

- [x] **rule/mordheim/underworld-alliance-mim/band--alliance-of-inconvenience/unimplemented.underworld-alliance-mim.band.alliance-of-inconvenience** · clause `alliance-of-inconvenience` · scope NO
  - register text: “two leaders with faction-scoped Ld bonuses and two Rout tests”
  - KB node: `band--alliance-of-inconvenience` (has effect text)
  - KB effect: “The Underworld has two leaders: only skaven can use the Slave King's Leadership bonus and only goblins the Bully's. When taking rout tests (25% of the warband out of action as normal) the warband takes two rout tests, one for each leader; if one leader fails, all warband members of his type rout wit”
  - printed source: broheim.net / Special Rules / An Alliance of Inconvenience / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Underworld Alliance.pdf
  - disposition: **D1** — Derived wording — Derived summary: effect explicitly states two leaders, faction-exclusive Leadership sharing, and one Rout test per leader.

- [x] **rule/mordheim/underworld-alliance-mim/band--power-grab/unimplemented.underworld-alliance-mim.band.power-grab** · clause `composition-producer` · scope NO
  - register text: “Determine which race has more warriors in the warband at the start of the match.”
  - KB node: `band--power-grab` (has effect text)
  - KB effect: “If there is more of one type of race than the other at the start of a match, the race with more warriors gains +1 Ld and the race with less gains -1 Ld.”
  - printed source: broheim.net / Special Rules / Power Grab / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Underworld Alliance.pdf
  - disposition: **D1** — Derived wording — Derived producer wording: effect compares race counts at the start of a match before assigning Leadership modifiers.

- [x] **rule/mordheim/underworld-alliance-mim/band--power-grab/unimplemented.underworld-alliance-mim.band.power-grab** · clause `supplied-leadership-adjustment` · scope YES
  - register text: “At match start the majority race gains +1 Leadership and the minority race loses 1 Leadership.”
  - KB node: `band--power-grab` (has effect text)
  - KB effect: “If there is more of one type of race than the other at the start of a match, the race with more warriors gains +1 Ld and the race with less gains -1 Ld.”
  - printed source: broheim.net / Special Rules / Power Grab / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Underworld Alliance.pdf
  - disposition: **D1** — Derived wording — Derived wording: effect gives majority race +1 Ld and minority race -1 Ld at match start.

### `bands/mordheim/watchmen-mim/special-rules.yaml`

- [x] **rule/mordheim/watchmen-mim/band--fanatical/unimplemented.watchmen-mim.band.fanatical** · clause `fanatical-advance--scope--campaign-trigger` · scope NO
  - register text: “with 30 experience a Hero becomes a crusader of Law”
  - KB node: `band--fanatical` (has effect text)
  - KB effect: “Knights of Purity are vigilante crusaders hell-bent on the destruction of Chaos. Any Hero of the Watch with 30 experience points becomes a crusader of Law; Knights of Purity automatically pass all Leadership-based tests they are required to take.”
  - printed source: broheim.net / Special rules / Fanatical / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Watchmen.pdf
  - disposition: **D1** — Derived wording — Derived wording: effect explicitly promotes any Watch Hero at 30 experience points to crusader of Law.

### `bands/mordheim/woodsmen-de-artois-mou/special-rules.yaml`

- [x] **rule/mordheim/woodsmen-de-artois-mou/band--quarterstaff/compiler.woodsmen-quarterstaff** · clause `whole` · scope YES
  - register text: “It is a hefty length of wood... give a +1 S bonus but can also be used to parry. The quarterstaff is used two handed.”
  - KB node: `band--quarterstaff` (has effect text)
  - KB effect: “Cost 15 gc, Common. Some Woodsmen favour the quarterstaff. It is a hefty length of wood about the height of the warrior. In skilled hands it is a versatile weapon and not only will give a +1 S bonus but can also be used to parry. The quarterstaff is used two handed and cannot be used with an additio”
  - printed source: broheim.net / Woodsmen Special Equipment / Quarterstaff / https://broheim.net/downloads/warbands/supplement/mousillon/Woodsmen%20de%20Artois.pdf
  - disposition: **D1** — Derived wording — Elliptical quote: complete Quarterstaff effect includes the wood description, +1 S, Parry and two-handed use.

### `bands/trollheim/chaos-streets-arcane-society/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-arcane-society/arcane-bodyguard--not-leader/unimplemented.chaos-streets-arcane-society.arcane-bodyguard.not-leader** · clause `not-a-leader` · scope NO
  - register text: “may never become the warband leader; no model may use the Bodyguard's Leadership”
  - KB node: `arcane-bodyguard--not-leader` (has effect text)
  - KB effect: “An Arcane Bodyguard may never become the warband leader, and no other model may use the Bodyguard's Leadership.”
  - printed source: chaos-in-the-streets / Heroes / 0-2 Arcane Bodyguards / Not a Leader / 
  - disposition: **D1** — Derived wording — Derived wording: effect forbids both becoming leader and sharing the Bodyguard Leadership.

### `bands/trollheim/chaos-streets-bretonnian-knights/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-bretonnian-knights/knights-errant--knights-virtue/unimplemented.chaos-streets-bretonnian-knights.knights-errant.knights-virtue** · clause `no-panic-and-all-alone--scope--no-panic` · scope NO
  - register text: “never panics or breaks from combat”
  - KB node: `knights-errant--knights-virtue` (has effect text)
  - KB effect: “A Knight Errant never panics or flees from combat and never needs to take a Leadership test for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 0-2 Knights Errant / Special Rules / Knight's Virtue / 
  - disposition: **D1** — Derived wording — Derived wording: Knight Errant effect says never panics or flees combat.

- [x] **rule/trollheim/chaos-streets-bretonnian-knights/knights-errant--knights-virtue/unimplemented.chaos-streets-bretonnian-knights.knights-errant.knights-virtue** · clause `no-panic-and-all-alone--scope--all-alone` · scope NO
  - register text: “never needs Leadership tests for fighting alone”
  - KB node: `knights-errant--knights-virtue` (has effect text)
  - KB effect: “A Knight Errant never panics or flees from combat and never needs to take a Leadership test for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 0-2 Knights Errant / Special Rules / Knight's Virtue / 
  - disposition: **D1** — Derived wording — Derived wording: Knight Errant effect exempts Leadership tests for fighting alone.

- [x] **rule/trollheim/chaos-streets-bretonnian-knights/questing-knight--knights-virtue/unimplemented.chaos-streets-bretonnian-knights.questing-knight.knights-virtue** · clause `no-panic-and-all-alone--scope--no-panic` · scope NO
  - register text: “never panics or breaks from combat”
  - KB node: `questing-knight--knights-virtue` (has effect text)
  - KB effect: “The Questing Knight never panics or flees from combat and never needs to take a Leadership test for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 1 Questing Knight / Special Rules / Knight's Virtue / 
  - disposition: **D1** — Derived wording — Derived wording: Questing Knight effect says never panics or flees combat.

- [x] **rule/trollheim/chaos-streets-bretonnian-knights/questing-knight--knights-virtue/unimplemented.chaos-streets-bretonnian-knights.questing-knight.knights-virtue** · clause `no-panic-and-all-alone--scope--all-alone` · scope NO
  - register text: “never needs Leadership tests for fighting alone”
  - KB node: `questing-knight--knights-virtue` (has effect text)
  - KB effect: “The Questing Knight never panics or flees from combat and never needs to take a Leadership test for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 1 Questing Knight / Special Rules / Knight's Virtue / 
  - disposition: **D1** — Derived wording — Derived wording: Questing Knight effect exempts Leadership tests for fighting alone.

### `bands/trollheim/chaos-streets-dwarf-treasure-hunters/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--death-oath/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-troll-slayers.death-oath** · clause `psychology-immunity` · scope YES
  - register text: “The Dwarf Troll Slayers is completely immune to Psychology.”
  - KB node: `dwarf-troll-slayers--death-oath` (has effect text)
  - KB effect: “Dwarf Troll Slayers are completely immune to all Psychology and do not need to take tests for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 0-2 Dwarf Troll Slayers / Special Rules / Death Oath / 
  - disposition: **D1** — Derived wording — Derived wording: Death Oath effect states complete immunity to all Psychology.

- [x] **rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--death-oath/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-troll-slayers.death-oath** · clause `death-oath-all-alone` · scope NO
  - register text: “never needs to test for fighting alone”
  - KB node: `dwarf-troll-slayers--death-oath` (has effect text)
  - KB effect: “Dwarf Troll Slayers are completely immune to all Psychology and do not need to take tests for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 0-2 Dwarf Troll Slayers / Special Rules / Death Oath / 
  - disposition: **D1** — Derived wording — Derived wording: Death Oath effect explicitly exempts fighting-alone tests.

### `bands/trollheim/chaos-streets-mordheim-inhabitants/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-mordheim-inhabitants/band--revival-sermons/unimplemented.chaos-streets-mordheim-inhabitants.band.revival-sermons** · clause `revival-sermons` · scope NO
  - register text: “sermon subsystem delivered like spells and affecting only the warband”
  - KB node: `band--revival-sermons` (has effect text)
  - KB effect: “Revival Sermons are not magical and affect only members of the Mordheim Inhabitants warband; they never affect enemy or allied warbands, and Hired Swords in the Prophet's employ do not benefit from them. When the Prophet gains a new skill, he may instead learn a random new Revival Sermon or reduce t”
  - printed source: chaos-in-the-streets / Special Rules / Revival Sermons / 
  - disposition: **D1** — Derived wording — Derived summary: complete Revival Sermons effect limits recipients to the warband and explicitly uses the normal spell casting procedure unless stated otherwise.

### `bands/trollheim/chaos-streets-pit-fighters/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--death-oath/unimplemented.chaos-streets-pit-fighters.dwarf-troll-slayer.death-oath** · clause `death-oath-all-alone` · scope NO
  - register text: “never needs to test for fighting alone”
  - KB node: `dwarf-troll-slayer--death-oath` (has effect text)
  - KB effect: “The Dwarf Troll Slayer is completely immune to Psychology and does not need to take tests for fighting alone.”
  - printed source: chaos-in-the-streets / Heroes / 0-1 Dwarf Troll Slayer / Special Rules / Death Oath / 
  - disposition: **D1** — Derived wording — Derived wording: Death Oath explicitly exempts tests for fighting alone.

### `bands/trollheim/chaos-streets-sigmar-protectorate/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-sigmar-protectorate/band--protectorate-special-skills-absolute-faith/unimplemented.chaos-streets-sigmar-protectorate.band.protectorate-special-skills-absolute-faith** · clause `all-alone-and-reroll` · scope NO
  - register text: “All Alone test / reroll clause carried by the same sentence”
  - KB node: `band--protectorate-special-skills-absolute-faith` (has effect text)
  - KB effect: “The Hero may re-roll failed Fear tests and does not need to take a test for being engaged by multiple opponents.”
  - printed source: chaos-in-the-streets / Sigmar's Protectorate Special Skills / Absolute Faith / 
  - disposition: **D1** — Derived wording — Derived annotation, not printed text: full effect permits re-rolling failed Fear tests and exempts tests for engagement by multiple opponents (All Alone).

### `bands/trollheim/khemri-cursed-of-karak-zorn/special-rules.yaml`

- [x] **rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--death-oath/unimplemented.khemri-cursed-of-karak-zorn.troll-slayer.death-oath** · clause `death-oath-all-alone` · scope NO
  - register text: “never needs to test for fighting alone”
  - KB node: `troll-slayer--death-oath` (has effect text)
  - KB effect: “The Troll Slayer is completely immune to Psychology and does not need to take tests for fighting alone.”
  - printed source: khemri / Heroes / 0-1 Troll Slayer / Death Oath / 
  - disposition: **D1** — Derived wording — Derived wording: Death Oath explicitly exempts tests for fighting alone.

### `bands/trollheim/khemri-hobgoblin-raiders/special-rules.yaml`

- [x] **rule/trollheim/khemri-hobgoblin-raiders/band--hobgoblin-special-skills-wolf-tamer/unimplemented.khemri-hobgoblin-raiders.band.hobgoblin-special-skills-wolf-tamer** · clause `wolf-tamer` · scope NO
  - register text: “control and ride a Giant Wolf; reroll Riding tests; dismount without a Ld test”
  - KB node: `band--hobgoblin-special-skills-wolf-tamer` (has effect text)
  - KB effect: “The Hero may direct one purchased Giant Wolf in battle without riding it; that wolf still counts toward the warband's normal 0-5 Giant Wolf limit. If the Hero rides a Giant Wolf, it may re-roll failed Riding tests but must accept the second result. The Hero may also voluntarily dismount whenever des”
  - printed source: khemri / Hobgoblin Special Skills / Wolf Tamer / 
  - disposition: **D1** — Derived wording — Derived summary: full Wolf Tamer effect covers directing an unmounted wolf, Riding-test re-rolls, and voluntary dismount without the normal wolf Leadership test.

- [x] **rule/trollheim/khemri-hobgoblin-raiders/giant-wolves--mount/unimplemented.khemri-hobgoblin-raiders.giant-wolves.mount** · clause `mount` · scope NO
  - register text: “Giant Wolves must normally be ridden.”
  - KB node: `giant-wolves--mount` (has effect text)
  - KB effect: “Every Giant Wolf that participates in a battle must normally be ridden by a member of the warband. The rider may not voluntarily dismount. If the rider is taken Out of Action, the Giant Wolf must pass a Leadership test; if it fails, the wolf immediately leaves the table and counts as Out of Action. ”
  - printed source: khemri / Henchmen / 0-5 Giant Wolves / Mounts / 
  - disposition: **D1** — Derived wording — Derived wording: Mount effect explicitly requires each participating Giant Wolf normally to be ridden.

### `bands/trollheim/khemri-lahmian-brotherhood/special-rules.yaml`

- [x] **rule/trollheim/khemri-lahmian-brotherhood/lackeys--favoured/unimplemented.khemri-lahmian-brotherhood.lackeys.favoured** · clause `favoured` · scope NO
  - register text: “on the Beloved's death a Lackey may be given the Blood Kiss, becoming a Beloved with Ld 8”
  - KB node: `lackeys--favoured` (has effect text)
  - KB effect: “If the Beloved dies, the Lahmian Vampire may give the Blood Kiss to one Lackey. That warrior becomes a Beloved for roster purposes, increases Leadership to 8, and the warband may recruit another Lackey. Granting the Blood Kiss counts as one advance roll.”
  - printed source: khemri / Heroes / 0-2 Lackeys / Favoured / 
  - disposition: **D1** — Derived wording — Derived summary: Favoured effect permits a Lackey to receive Blood Kiss after Beloved death and become a Beloved with Leadership 8.

### `bands/trollheim/lustria-amazons/special-rules.yaml`

- [x] **rule/trollheim/lustria-amazons/band--amazon-special-skills-animal-fury/unimplemented.lustria-amazons.band.amazon-special-skills-animal-fury** · clause `all-alone-and-reroll` · scope NO
  - register text: “All Alone test / reroll clause carried by the same sentence”
  - KB node: `band--amazon-special-skills-animal-fury` (has effect text)
  - KB effect: “The Hero is immune to Fear and All Alone tests and gains +1 Attack during a turn in which she charges.”
  - printed source: lustria / Amazon Special Skills / Animal Fury / 
  - disposition: **D3** — Register-side unsupported reroll annotation: Animal Fury effect grants Fear/All Alone immunity and +1 Attack on a charging turn, with no re-roll. Reviewed correction should replace generic "All Alone test / reroll clause carried by the same sentence" with the actual All Alone immunity clause. Do not alter protected clause_text via apply tool.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

### `bands/trollheim/lustria-high-elves/special-rules.yaml`

- [x] **rule/trollheim/lustria-high-elves/band--determination/unimplemented.lustria-high-elves.band.determination** · clause `determination` · scope NO
  - register text: “against Dark Elves count as Ld 10 for Rout tests and never voluntarily Rout”
  - KB node: `band--determination` (has effect text)
  - KB effect: “When fighting a Dark Elf warband, High Elves count as Leadership 10 when taking Rout tests and may never voluntarily Rout.”
  - printed source: lustria / High Elf Special Rules / Determination / 
  - disposition: **D1** — Derived wording — Derived wording: Determination explicitly gives Leadership 10 for Rout tests and forbids voluntary Rout against Dark Elves.

- [x] **rule/trollheim/lustria-high-elves/explorers--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May never use blackpowder weapons, drugs or poisons, or Dwarf-made equipment. May not select the Mage Staff or Elven Runestones.”
  - KB node: `explorers--equipment-restrictions` (has effect text)
  - KB effect: “May never use blackpowder weapons. May never use drugs or poisons. May never use Dwarf-made equipment, including Gromril and Obsidian equipment. May not select the Mage Staff or Elven Runestones; those entries are Loremaster only.”
  - printed source: lustria / 0-2 Explorers / 
  - disposition: **D1** — Derived wording — Derived consolidated wording: Explorers effect separately lists every prohibition in the clause.

- [x] **rule/trollheim/lustria-high-elves/sea-guard--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May never use blackpowder weapons, drugs or poisons, or Dwarf-made equipment. May not select the Mage Staff or Elven Runestones.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — False missing-node match: inspect the owning sea-guard--equipment-restrictions node, not nested runtime effect profile.equipment-restrictions. Its full effect covers every listed prohibition.

- [x] **rule/trollheim/lustria-high-elves/sword-guardians--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May never use blackpowder weapons, drugs or poisons, Dwarf-made equipment or missile weapons. May not select the Mage Staff or Elven Runestones.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — False missing-node match: inspect the owning sword-guardians--equipment-restrictions node, not nested runtime effect profile.equipment-restrictions. Its full effect covers every listed prohibition.

### `bands/trollheim/lustria-lizardmen/special-rules.yaml`

- [x] **rule/trollheim/lustria-lizardmen/skink-priest--leader/mechanic.leader-six** · clause `leader-six` · scope YES
  - register text: “The Skink Priest is the warband leader and any Lizardmen within 6 inches may use his Leadership for any Leadership test”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “Any warband model within 6" of the Skink Priest may use his Leadership instead of its own. If the Skink Priest is destroyed, a new Skink Priest may be recruited only after the warband has played one battle without one.”
  - printed source: lustria / Heroes / 1 Skink Priest / Leader / 
  - disposition: **D1** — Derived wording — Derived wording; owning rule is named Leader, applies to Skink Priest, and explicitly permits any warband model within 6 inches to use his Leadership; profiles.yaml binds skink-priest to this rule.

- [x] **rule/trollheim/lustria-lizardmen/skink-priest--leader/mechanic.leader-six** · clause `leader-replacement` · scope NO
  - register text: “If the Skink Priest is killed a new Skink Priest may be recruited only after the warband has played one battle without a leader”
  - KB node: `skink-priest--leader` (has effect text)
  - KB effect: “Any warband model within 6" of the Skink Priest may use his Leadership instead of its own. If the Skink Priest is destroyed, a new Skink Priest may be recruited only after the warband has played one battle without one.”
  - printed source: lustria / Heroes / 1 Skink Priest / Leader / 
  - disposition: **D1** — Derived wording — Derived wording: Leader effect delays replacement recruitment until one battle has been played without the slain Skink Priest.

- [x] **rule/trollheim/lustria-lizardmen/band--cold-blooded/unimplemented.lustria-lizardmen.band.cold-blooded** · clause `cold-blooded-rout` · scope NO
  - register text: “when taking a Rout test, roll 3D6 keep the two lowest; and the warband may never use a Saurus or Kroxigor Leadership for a Rout test”
  - KB node: `band--cold-blooded` (has effect text)
  - KB effect: “When taking a Rout test or any other Psychology test, roll 3D6 and keep the two lowest results. The warband may never use the Leadership of a Saurus or Kroxigor when taking a Rout test.”
  - printed source: lustria / Lizardmen Special Rules / Cold-Blooded / 
  - disposition: **D1** — Derived wording — Derived wording: Cold-Blooded effect explicitly gives 3D6 keep lowest two and forbids Saurus/Kroxigor Leadership for Rout tests.

- [x] **rule/trollheim/lustria-lizardmen/band--scaly-skin/compiler.lizardmen-scaly-skin** · clause `whole` · scope YES
  - register text: “Lizardmen have natural Scaly Skin saves... an Injury-table result that denies armour saves also denies that 6+ Scaly Skin save.”
  - KB node: `band--scaly-skin` (has effect text)
  - KB effect: “Lizardmen have natural Scaly Skin saves. Strength modifiers may not reduce a Scaly Skin save beyond 6+, although an Injury-table result that denies armour saves also denies that 6+ Scaly Skin save. Scaly Skin may be combined with other armour, except Hardened Leather provides no additional bonus.”
  - printed source: lustria / Lizardmen Special Rules / Scaly Skin / 
  - disposition: **D1** — Derived wording — Elliptical quote: full Scaly Skin effect explicitly includes natural saves and the Injury-table exception to the 6+ floor.

### `bands/trollheim/lustria-pirates/special-rules.yaml`

- [x] **rule/trollheim/lustria-pirates/band--pirate-special-skills-swashbuckler/unimplemented.lustria-pirates.band.pirate-special-skills-swashbuckler** · clause `swashbuckler` · scope NO
  - register text: “end-of-phase Ld test to disengage from base contact without free attacks”
  - KB node: `band--pirate-special-skills-swashbuckler` (has effect text)
  - KB effect: “At the end of any close-combat phase, whether the Hero's or the opponent's, if the Hero is in base contact with an enemy model the Hero may take a Leadership test. If passed, the Hero may immediately make one normal move, but may not run or charge, and the enemy does not receive free attacks for the”
  - printed source: lustria / Pirate Special Skills / Swashbuckler / 
  - disposition: **D1** — Derived wording — Derived summary: complete Swashbuckler effect permits an end-of-combat-phase Leadership test to disengage without free attacks.

### `bands/trollheim/lustria-tileans/special-rules.yaml`

- [x] **rule/trollheim/lustria-tileans/band--remas-officer-leadership/unimplemented.lustria-tileans.band.remas-officer-leadership** · clause `leadership-characteristic-bonus` · scope YES
  - register text: “The Mercenary Captain, Champions and Recruits have +1 Leadership at all times, regardless of the opposing warband”
  - KB node: `band--remas-officer-leadership` (has effect text)
  - KB effect: “The Mercenary Captain, Champions and Recruits in a Remas warband have +1 Leadership at all times, regardless of the opposing warband.”
  - printed source: lustria / Remas / Special Rules / 
  - disposition: **D1** — Derived wording — Derived wording: effect explicitly gives Remas Captain, Champions and Recruits +1 Leadership at all times.

### `catalog/items/trollheim.yaml`

- [x] **item/ankus** · clause `whole` · scope YES
  - register text: “Strike-first melee weapon whose Injury 2-4 is Stunned.”
  - KB node: `ankus` (**no effect text**)
  - printed source: khemri / Native Warbands / Beloved Equipment List / ; khemri / Necromancer Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.ankus` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/bagh_nakh** · clause `whole` · scope YES
  - register text: “Paired weapon granting +1 Attack, +1 Strength and an extra -1 armour save.”
  - KB node: `bagh_nakh` (**no effect text**)
  - printed source: khemri / Thief Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.bagh-nakh` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/chained_squig** · clause `whole` · scope YES
  - register text: “Strength 3 strike-first attack that cannot be parried and entangles on a hit.”
  - KB node: `chained_squig` (**no effect text**)
  - printed source: chaos-in-the-streets / Orc Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.chained-squig` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/choppa** · clause `whole` · scope YES
  - register text: “Choppa grants +1 Strength in the first round and an extra -1 armour save and may be used with a shield.”
  - KB node: `choppa` (**no effect text**)
  - printed source: chaos-in-the-streets / Orc Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.choppa` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/dark_steel_weapon** · clause `whole` · scope YES
  - register text: “Dark steel weapon re-rolls failed wound rolls.”
  - KB node: `dark_steel_weapon` (**no effect text**)
  - printed source: lustria / Dark Elf Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `material.dark-steel` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/devil_toxin** · clause `whole` · scope YES
  - register text: “Devil's Toxin re-rolls failed wound rolls and the re-roll cannot cause a critical hit.”
  - KB node: `devil_toxin` (**no effect text**)
  - printed source: lustria / Pygmy Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `poison.devil-s-toxin` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/draich** · clause `whole` · scope YES
  - register text: “Two-handed Strength +2 weapon that strikes last, may parry, has Concussion and adds +1 on the critical hit table.”
  - KB node: `draich` (**no effect text**)
  - printed source: lustria / Dark Elf Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.draich` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/elven_greatsword** · clause `whole` · scope YES
  - register text: “Two-handed Strength +2 greatsword that strikes last and may parry.”
  - KB node: `elven_greatsword` (**no effect text**)
  - printed source: lustria / High Elf Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.elven-greatsword` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/great_scimitar** · clause `whole` · scope YES
  - register text: “Two-handed Strength +2 scimitar that strikes last with an extra -1 armour save.”
  - KB node: `great_scimitar` (**no effect text**)
  - printed source: khemri / Native Warbands / Beloved Equipment List / ; khemri / Undead Warrior Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.great-scimitar` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/hammer_or_mace** · clause `whole` · scope YES
  - register text: “Bludgeon whose Injury 2-4 is Stunned.”
  - KB node: `hammer_or_mace` (**no effect text**)
  - printed source: lustria / Pirate Equipment List / ; lustria / Swabbie Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.mace` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/kusara_kama** · clause `whole` · scope YES
  - register text: “Two-handed weapon with an extra -1 armour save whose 5+ hit hampers the enemy weapon and removes one attack.”
  - KB node: `kusara_kama` (**no effect text**)
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.kusara-kama` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/long_boathook** · clause `whole` · scope YES
  - register text: “Two-handed hook at Strength -1 that strikes first in the first round of any close combat.”
  - KB node: `long_boathook` (**no effect text**)
  - printed source: lustria / Pirate Equipment List / ; lustria / Swabbie Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.long-boat-hook` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/manbane** · clause `whole` · scope YES
  - register text: “+1 to wound rolls and a natural 1 always fails.”
  - KB node: `manbane` (**no effect text**)
  - printed source: lustria / Pygmy Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `poison.manbane` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/nightshade** · clause `whole` · scope YES
  - register text: “Each unsaved wound reduces the opponent Initiative by 1 to a minimum of 1.”
  - KB node: `nightshade` (**no effect text**)
  - printed source: lustria / Pygmy Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `poison.nightshade` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/pistol_brace** · clause `whole` · scope YES
  - register text: “Close-combat pistol profile: one Strength 4 first-round attack with the pistol armour-penetration bonus.”
  - KB node: `pistol_brace` (**no effect text**)
  - printed source: chaos-in-the-streets / Arcane Society Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.pistol` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/scythe** · clause `whole` · scope YES
  - register text: “Two-handed weapon with an extra -1 armour save.”
  - KB node: `scythe` (**no effect text**)
  - printed source: khemri / Necromancer Equipment List / ; khemri / Undead Warrior Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.scythe` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/spider_spit** · clause `whole` · scope YES
  - register text: “An undefended hit forces a Toughness test and failure paralyses the target until it passes a test in its own Recovery phase.”
  - KB node: `spider_spit` (**no effect text**)
  - printed source: lustria / Pygmy Equipment List / ; lustria / Savage Goblin Hero Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `poison.spider-spittle` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/stone_axe** · clause `whole` · scope YES
  - register text: “Stone axe uses club rules: normal Strength and Injury 2-4 treated as Stunned.”
  - KB node: `stone_axe` (**no effect text**)
  - printed source: lustria / Amazon Heroine Equipment List / ; lustria / Amazon Warrior Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.stone-axe` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/two_handed_club** · clause `whole` · scope YES
  - register text: “Two-handed club with +2 Strength that strikes last unless Strongman applies.”
  - KB node: `two_handed_club` (**no effect text**)
  - printed source: lustria / Bruiser Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.double-handed-weapon` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/witch_sword** · clause `whole` · scope YES
  - register text: “Witch sword adds +1 Strength in the first round and may parry.”
  - KB node: `witch_sword` (**no effect text**)
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `weapon.witch-sword` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

- [x] **item/wolfsbane** · clause `whole` · scope YES
  - register text: “Wolfsbane causes critical hits on a wound roll of 5-6 unless a natural 6 is required to wound.”
  - KB node: `wolfsbane` (**no effect text**)
  - printed source: lustria / Pygmy Equipment List / 
  - disposition: **D1** — Derived wording — Derived wording; item mechanic_id `poison.wolfsbane` resolves to its canonical effect in `catalog/mechanics/close-combat.yaml`, which covers the entire clause (no duplicated item prose needed).

### `catalog/items/weapons-close-combat.yaml`

- [x] **item/cathayan_longsword** · clause `armour-penetration-discrepancy` · scope YES
  - register text: “Attacks made with a Cathayan longsword give the bearer +1 Initiative and +1 Weapon Skill.”
  - KB node: `cathayan_longsword` (has effect text)
  - KB effect: “A close combat weapon using the wielder's Strength, with Parry, Cutting Edge (an additional -1 armour save modifier), and Mastercrafted (+1 Weapon Skill and +1 Initiative for attacks with this sword). this sword).”
  - printed source: mordheimer.net / Soldier Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay; mordheimer.net / Ogre Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/maneaters
  - disposition: **D1** — Derived wording — Derived wording: Cathayan Longsword effect explicitly grants +1 WS and +1 Initiative to attacks using the sword.

- [x] **item/mace_hammer** · clause `whole` · scope YES
  - register text: “Range: Close Combat Strength: As user Concussion : a roll of 2-4 is treated as stunned when rolling to see the extent of a model's injuries.”
  - KB node: `hammer` (has effect text)
  - KB effect: “Range: Close Combat Strength: As user Concussion : Hammers and other bludgeoning weapons are excellent to use for striking your enemy senseless. When using a hammer, club or mace, a roll of 2-4 is treated as stunned when rolling to see the extent of a model's injuries.”
  - printed source: mordheimer.net / Scout Equipment List / https://mordheimer.net/docs/warbands/grade-1a-warbands/averlander; mordheimer.net / Marksman equipment list / https://mordheimer.net/docs/warbands/grade-1a-warbands/averlander
  - disposition: **D1** — Derived wording — Condensed quote: hammer effect states As User Strength and injury rolls 2–4 treated as stunned.

- [x] **item/starsword** · clause `whole` · scope YES
  - register text: “Range: Close Combat Strength: As user +1 Parry : Can parry enemy blows”
  - KB node: `starsword` (has effect text)
  - KB effect: “A close combat weapon giving +1 Strength and Parry. Its attacks ignore armour saves; ward and Dodge saves are expressly retained.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria; lustria / Amazons / Starsword / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons-lustria
  - disposition: **D1** — Derived wording — Derived wording: Starsword effect explicitly gives +1 Strength and Parry.

- [x] **item/sun_gauntlet** · clause `whole` · scope YES
  - register text: “Range: 12" Strength: 4 Accurate : The Sun Gauntlet does not suffer the usual -1 modifier to hit for long range.”
  - KB node: `sun_gauntlet` (has effect text)
  - KB effect: “A ranged Strength 4 weapon with range 12 inches and no long-range hit penalty. In close combat it may be combined with another weapon for one additional Strength 4 attack each turn; no armour save is permitted.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons; amazons / Sun Gauntlet / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons
  - disposition: **D1** — Derived wording — Derived wording: Sun Gauntlet effect explicitly gives range 12 inches, Strength 4 and no long-range hit penalty.

- [x] **item/sunstaff_lustria** · clause `whole` · scope YES
  - register text: “Two-handed, Strength +1, with an ignition threshold of 5 against flammable targets.”
  - KB node: `sunstaff_lustria` (**no effect text**)
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria; mordheimer.net / Henchwomen equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria
  - disposition: **D3** — Register-side invented melee profile: cited source links Town Cryer #15, printed p.19 (PDF p.21), Sunstaff (35 gc, Rare 10): Range 12 inches/Close Combat, Strength as user, Special Sunbolt; Sunbolt is a 12-inch Strength 4 shooting attack ignoring armour except ward/Dodge and long-range penalties. No +1 Strength, two-handed rule or ignition threshold appears. Reviewed correction must withdraw the brazier-derived clause and use the printed profile; binding discrepancy remains a concrete TODO. Source: https://broheim.net/downloads/towncryer/TownCryer15.pdf (linked by https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria).
  - resolution (2026-11-10): **catalogue corrected; execution deferred by user** — Printed profile and Sunbolt are now in the item; the false Brazier Iron item/simulation mappings, CSV effect and ignition parameters were removed. The register explicitly records the dedicated melee profile as pending. See TODO.md; Sunbolt shooting remains outside the duel.

### `catalog/mechanics/close-combat.yaml`

- [x] **mechanic/skill.tough-as-steel** · clause `out-of-action-only-on-six` · scope YES
  - register text: “Only goes Out of Action on a 6 on the Injury table.”
  - KB node: `skill.tough-as-steel` (has effect text)
  - KB effect: “When rolling on the Injury table for this Hero, a roll of 1-3 is treated as knocked down, 4-5 as stunned, and 6 as out of action.”
  - disposition: **D1** — Derived wording — Derived wording: Tough as Steel injury table explicitly assigns Out of Action only to 6.

- [x] **mechanic/weapon.cathayan-longsword** · clause `armour-penetration-discrepancy` · scope YES
  - register text: “Attacks made with a Cathayan longsword give the bearer +1 Initiative and +1 Weapon Skill.”
  - KB node: `weapon.cathayan-longsword` (has effect text)
  - KB effect: “A close combat weapon using the wielder's Strength, with Parry, Cutting Edge (an additional -1 armour save modifier), and Mastercrafted (+1 Weapon Skill and +1 Initiative for attacks with this sword).”
  - printed source: mordheimer.net / Soldier Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay; mordheimer.net / Ogre Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/maneaters
  - disposition: **D1** — Derived wording — Derived wording: Cathayan Longsword effect explicitly grants +1 WS and +1 Initiative to attacks using the sword.

- [x] **mechanic/weapon.starsword** · clause `dodge-exception` · scope YES
  - register text: “A Starsword ignores all armour saves except for ward and Dodge saves.”
  - KB node: `weapon.starsword` (has effect text)
  - KB effect: “A close combat weapon giving +1 Strength and Parry. Its attacks ignore armour saves; ward and Dodge saves are expressly retained.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria; lustria / Amazons / Starsword / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons-lustria
  - disposition: **D1** — Derived wording — Derived wording: Starsword effect ignores armour while expressly retaining ward and Dodge saves.

- [x] **mechanic/weapon.sun-gauntlet** · clause `whole` · scope YES
  - register text: “Off-hand-only Strength 4 attack that ignores armour saves.”
  - KB node: `weapon.sun-gauntlet` (has effect text)
  - KB effect: “A ranged Strength 4 weapon with range 12 inches and no long-range hit penalty. In close combat it may be combined with another weapon for one additional Strength 4 attack each turn; no armour save is permitted.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons; amazons / Sun Gauntlet / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons
  - disposition: **D1** — Derived wording — Derived wording and structured restriction: weapon.sun-gauntlet effect gives an additional Strength 4 attack with another weapon and no armour save; fields main_hand:false/off_hand:true express off-hand-only.

- [x] **mechanic/weapon.sun-gauntlet** · clause `ranged-profile` · scope NO
  - register text: “Range: 12" Strength: 4 Accurate : The Sun Gauntlet does not suffer the usual -1 modifier to hit for long range.”
  - KB node: `weapon.sun-gauntlet` (has effect text)
  - KB effect: “A ranged Strength 4 weapon with range 12 inches and no long-range hit penalty. In close combat it may be combined with another weapon for one additional Strength 4 attack each turn; no armour save is permitted.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons; amazons / Sun Gauntlet / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons
  - disposition: **D1** — Derived wording — Derived wording: Sun Gauntlet effect explicitly gives range 12 inches, Strength 4 and no long-range hit penalty.

- [x] **mechanic/mechanic.beauty-of-the-sea** · clause `whole` · scope YES
  - register text: “A male, non-animal enemy must pass a Leadership test to charge a Sea Singer... The Sea Singer causes Fear in female models.”
  - KB node: `mechanic.beauty-of-the-sea` (has effect text)
  - KB effect: “In order for a male, non-animal enemy to charge a Sea Singer, he must pass a Leadership test, or else be dazzled at her beauty and remain in place. If charged by a Sea Singer, the model may not attack back in combat until he passes a Leadership Test in the beginning of the Combat Phase. Once a test ”
  - printed source: broheim.net / Heroes / 0-1 Sea Singer / Special Rules / https://broheim.net/downloads/warbands/supplement/sartosa/Ghost%20Pirates.pdf
  - disposition: **D1** — Derived wording — Elliptical quote: complete Beauty of the Sea effect includes the male non-animal Leadership charge gate and Fear in female models.

- [x] **mechanic/mechanic.magical-void** · clause `whole` · scope YES
  - register text: “The Corpse Master gains a 4+ save against enemy spells and magic weapons.”
  - KB node: `mechanic.magical-void` (has effect text)
  - KB effect: “The Corpse Master is a space void of magic and thus gains a 4+ save against enemy spells and magic weapons.”
  - printed source: broheim.net / 1 Corpse Master / Special Rules / Magical Void / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call Of The Night Haint.pdf
  - disposition: **D1** — Derived wording — Condensed quote: Magical Void explicitly grants Corpse Master a 4+ save against enemy spells and magic weapons.

- [x] **mechanic/mechanic.shallya-tranquil-aura** · clause `whole--scope--weapon-skill-penalty` · scope YES
  - register text: “All models within 2 inches suffer -1 Weapon Skill”
  - KB node: `mechanic.shallya-tranquil-aura` (has effect text)
  - KB effect: “All models within 2" suffer -1 Weapon Skill and -1 Ballistic Skill, except Daemons and Undead.”
  - printed source: liber-malefic / Priests for Every Occasion / Priestess of Shallya / https://www.scribd.com/document/241727651/Miracle-workers-in-Mordheim
  - disposition: **D3** — Register wording overstates coverage: KB effect explicitly excludes Daemons and Undead from the -1 Weapon Skill/-1 Ballistic Skill aura. Reviewed correction: "All models within 2 inches, except Daemons and Undead, suffer -1 Weapon Skill." Retain the exception; no KB edit.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`, `conditions`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **mechanic/mechanic.wizened-halfling** · clause `whole` · scope YES
  - register text: “All halflings may re-roll any failed leadership test when within 6 inches of the leader as well as using his leadership for both tests.”
  - KB node: `mechanic.wizened-halfling` (has effect text)
  - KB effect: “This old halfling is greatly respected by the other members of the warband and they never question his word. All halflings may also re-roll any failed leadership test when within 6" of the leader as well as using his leadership for both tests.”
  - printed source: mordheim-index-catalog / Halfling Special Skills / Wizened Halfling / https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings
  - disposition: **D1** — Derived wording — Derived wording: Wizened Halfling explicitly gives failed Leadership-test re-rolls within 6 inches of the leader and his Leadership for both tests.

### `catalog/skills/warband.yaml`

- [x] **rule/catalog/warband/skill.tough-as-steel/skill.tough-as-steel** · clause `out-of-action-only-on-six` · scope YES
  - register text: “Only goes Out of Action on a 6 on the Injury table.”
  - KB node: `skill.tough-as-steel` (has effect text)
  - KB effect: “When rolling on the Injury table for this Hero, a roll of 1-3 is treated as knocked down, 4-5 as stunned, and 6 as out of action.”
  - disposition: **D1** — Derived wording — Derived wording: Tough as Steel injury table explicitly assigns Out of Action only to 6.

## C. Partial matches (66 items)

The first words of the clause match a KB text but the remainder diverges — usually a printed stat-line or special-rules block whose tail the KB effect text condenses.

### Section C review — 2026-11-10

All 66 entries have been adjudicated against the full current KB nodes at revision `386c093d`: **62 D1, 4 D3, 0 D2, 0 D4**. D1 wording is derived or excerpted, with the cited owning rules, canonical references and companion clauses preserving its meaning. Checked boxes record completed dispositions; the four D3 corrections remain a reviewed register follow-up. No protected CSV columns or KB text were changed. Sections A and B are unchanged by this batch.

The four D3 entries concern Extra Arm's Mutant/Possessed subjects, Beauty of the Sea's charge direction, Looter's requirement that the Hero was not taken Out of Action, and Mark of Shornaal's close-combat limit. Each has a correction proposal below, checked against the cited source. Apparent missing effects were resolved through owning rule nodes or existing canonical mechanic references.

Verification for this documentation-only batch: `git diff --check` and targeted `.venv/bin/python -` assertions passed: exactly 66 checked entries and dispositions (62 D1 / 4 D3), no pending/candidate dispositions in C, unchanged entry identities, quotations, KB snapshots and source references, and byte-for-byte unchanged content before C. No functional suites were run; no D2 edits require text re-matching. This is adjudication of C, not certification of the full register or execution of its correction batch.

### `bands/mordheim/battle-monks-of-cathay/special-rules.yaml`

- [x] **rule/mordheim/battle-monks-of-cathay/raging-peasants--mob/unimplemented.battle-monks-of-cathay.raging-peasants.mob** · clause `ally-count-producer` · scope NO
  - register text: “A Peasant gets +1 Ld for each other allied Peasant model within 3 inches.”
  - KB node: `raging-peasants--mob` (has effect text)
  - KB effect: “Peasants become threatening in large numbers. A Peasant gets +1 Ld for each other allied Peasant model within 3". Due to their rage, they do not benefit from the leader rule.”
  - printed source: mordheimer.net / henchmen / 0 – 5 Raging Peasants / Special Rules / Mob / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay
  - disposition: **D1** — Derived wording — Effect explicitly gives +1 Ld per other allied Peasant within 3 inches; inches replaces the printed inch symbol only.

- [x] **rule/mordheim/battle-monks-of-cathay/raging-peasants--mob/unimplemented.battle-monks-of-cathay.raging-peasants.mob** · clause `individual-leadership-bonus` · scope YES
  - register text: “A Peasant gets +1 Ld for each other allied Peasant model within 3 inches.”
  - KB node: `raging-peasants--mob` (has effect text)
  - KB effect: “Peasants become threatening in large numbers. A Peasant gets +1 Ld for each other allied Peasant model within 3". Due to their rage, they do not benefit from the leader rule.”
  - printed source: mordheimer.net / henchmen / 0 – 5 Raging Peasants / Special Rules / Mob / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay
  - disposition: **D1** — Derived wording — Effect explicitly gives +1 Ld per other allied Peasant within 3 inches; same printed clause is shared by distinct register consumers, not a missing text extraction.

### `bands/mordheim/black-dwarfs/special-rules.yaml`

- [x] **rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-chaos-engineer/mechanic.chaos-engineer** · clause `search-and-rarity` · scope NO
  - register text: “Whenever a Hero with this skill searches for Chaos armour or Obsidian Weapons, he gets +3 on the roll.”
  - KB node: `band--chaos-dwarf-special-skills-chaos-engineer` (has effect text)
  - KB effect: “The Hero has great technical skill and can use this to craft wicked armours and weapons. Whenever a Hero with this skill searches for Chaos armour (including Mechanical Suits) or Obsidian Weapons, he gets +3 on the roll. This represents the Engineer’s ability to craft these items himself. The Hero i”
  - printed source: mordheimer.net / Chaos Dwarf special skills / chaos engineer / https://mordheimer.net/docs/warbands/grade-1c-warbands/black-dwarfs
  - disposition: **D1** — Derived wording — Effect contains the +3 search modifier for Chaos armour (including Mechanical Suits) or Obsidian Weapons.

### `bands/mordheim/black-orcs/special-rules.yaml`

- [x] **rule/mordheim/black-orcs/band--black-orc-special-skills-proven-warrior/compiler.proven-warrior** · clause `whole` · scope YES
  - register text: “Once he gains this skill, the model is now considered a full Black Orc Warrior and uses their equipment list and skill lists.”
  - KB node: `band--black-orc-special-skills-proven-warrior` (has effect text)
  - KB effect: “This young warrior has proven himself worthy of his Black Orc heritage. This skill may only be taken by a Young’un with the Black Orc blood ability and 25 experience. Once he gains this skill, the model is now considered a full Black Orc Warrior (yet still retains the title of Young’un). He follows ”
  - printed source: mordheimer.net / Black Orc Special Skills / proven warrior / https://mordheimer.net/docs/warbands/grade-1b-warbands/black-orcs
  - disposition: **D1** — Derived wording — Effect grants full Black Orc status and its equipment/skill lists, retaining the Young’un title; clause is condensed wording.

### `bands/mordheim/bretonnian-chapel-guard/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--holy-relics/unimplemented.bretonnian-chapel-guard.battle-pilgrims.holy-relics** · clause `holy-relic-frenzy` · scope YES
  - register text: “If a Battle Pilgrim owns a Holy Relic, he gains the ability Frenzy (when frenzied, he is immune to Hatred).”
  - KB node: `battle-pilgrims--holy-relics` (has effect text)
  - KB effect: “Battle Pilgrims may be given a Holy Relic, regardless of the fact that henchman are not normally allowed to take Miscellaneous items. If a Battle Pilgrim owns a Holy Relic, he gains the ability Frenzy (Reminder: when frenzied, he is immune to Hatred.) It is possible to give a Holy Relic to Battle Pi”
  - printed source: mordheimer.net / henchmen / 0 – 5 Battle pilgrims / Special Rules / Holy Relics / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect expressly grants Frenzy for owning a Holy Relic and states the Hatred-immunity reminder.

- [x] **rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood** · clause `whole--scope--squire-construction` · scope YES
  - register text: “If you choose to keep him a Squire, he may choose two skill lists from Combat, Academic, Strength, or Speed and retains his normal Squire equipment tables.”
  - KB node: `squires--knighthood` (has effect text)
  - KB effect: “When a Squire rolls “The Lad's Got Talent”, you may choose one of two options when promoting him to a hero: to have him remain a Squire, or to have him become a Knight Errant. (Note: in this manner, you may have more than three Knights Errant in your Warband). If you choose to keep him a Squire, he ”
  - printed source: mordheimer.net / henchmen / 0 – 5 Squires / Special Rules / Knighthood / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect gives remaining Squires two choices from Combat/Academic/Strength/Speed and retention of Squire equipment tables.

- [x] **rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood** · clause `whole--scope--knight-errant-construction` · scope YES
  - register text: “If you choose to make him a Knight Errant, he immediately gains the Knight, Vain and Impetuous rules instead of receiving an immediate advancement, may learn Special Skills in addition to two other skill sets, but must switch his equipment to the Knight Equipment list, and may never use missile weapons.”
  - KB node: `squires--knighthood` (has effect text)
  - KB effect: “When a Squire rolls “The Lad's Got Talent”, you may choose one of two options when promoting him to a hero: to have him remain a Squire, or to have him become a Knight Errant. (Note: in this manner, you may have more than three Knights Errant in your Warband). If you choose to keep him a Squire, he ”
  - printed source: mordheimer.net / henchmen / 0 – 5 Squires / Special Rules / Knighthood / https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
  - disposition: **D1** — Derived wording — Effect contains all listed Knight Errant promotion consequences: Knight/Vain/Impetuous, replacement immediate advance, extra Special access, equipment switch and missile prohibition.

### `bands/mordheim/bretonnian-knights-errant-mou/special-rules.yaml`

- [x] **rule/mordheim/bretonnian-knights-errant-mou/band--knights-feats/profile.skill-access** · clause `whole` · scope YES
  - register text: “Knights Errant may choose to use the following skill list instead of the standard skill lists: Combat charge, Lancer, Sword master, Armour specialist.”
  - KB node: `band--knights-feats` (has effect text)
  - KB effect: “Knights Errant may choose to use the following skill list instead of the standard skill lists: 1 - Combat charge: the character gains +1 attack and +1 WS when he charges. 2 - Lancer: the character can use this skill only on horseback; may not be combined with Combat charge. If the character's first ”
  - printed source: broheim.net / Knights Feats / https://broheim.net/downloads/warbands/supplement/mousillon/Bretonnian Knights Errant.pdf
  - disposition: **D1** — Derived wording — Full effect enumerates Combat charge, Lancer, Sword master and Armour specialist after the stated alternative skill-list permission.

### `bands/mordheim/carnival-of-chaos/special-rules.yaml`

- [x] **rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-mark-of-nurgle/special-rule.band--blessings-of-nurgle-mark-of-nurgle** · clause `whole` · scope YES
  - register text: “The Tainted One is burned with the great mark of Nurgle. It gains +1 Wound and is immune to all poisons.”
  - KB node: `band--blessings-of-nurgle-mark-of-nurgle` (has effect text)
  - KB effect: “Cost: 35 Gold Crowns The Tainted One is burned with the great mark of Nurgle, the three spheres, that weep foul pus constantly. It gains +1 Wound and is immune to all poisons.”
  - printed source: mordheimer.net / Blessings of Nurgle / Mark of Nurgle / https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos
  - disposition: **D1** — Derived wording — Effect contains both +1 Wound and poison immunity; register only omits descriptive three-sphere/pus wording.

- [x] **rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle/mechanic.blessings-of-nurgle** · clause `whole--scope--blessing-construction` · scope YES
  - register text: “Blessings of Nurgle may be bought for Tainted Ones only when they are recruited; any Tainted may have one or more Blessings”
  - KB node: `band--blessings-of-nurgle` (has effect text)
  - KB effect: “Those that worship at the fetid altar of the Lord of Decay suffer from terrible diseases and decay, which are known as Blessings of Nurgle. Blessings of Nurgle may be bought for Tainted Ones only when they are recruited; you may not buy new Blessings for a model after recruitment. Any Tainted may ha”
  - printed source: mordheimer.net / Blessings of Nurgle / https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos
  - disposition: **D1** — Derived wording — Effect contains recruitment-only Blessing purchase permission and one-or-more Blessings for each Tainted.

### `bands/mordheim/channel-rats-mim/special-rules.yaml`

- [x] **rule/mordheim/channel-rats-mim/band--water-caravan/unimplemented.channel-rats-mim.band.water-caravan** · clause `whole` · scope NO
  - register text: “Each Strigany warband must include one Riverboat or River Barge, replaced by a Wagon and two horses if the campaign has no rivers.”
  - KB node: `band--water-caravan` (has effect text)
  - KB effect: “Each Strigany warband must include one Riverboat or River Barge. If there are no rivers in your campaign then you should replace the River Boat with a Wagon and two horses. If you do this then replace 'Rigger' skill with 'Handyman' to allow your Tinker to repair the wagon.”
  - printed source: broheim.net / Choice of Warriors / Water Caravan / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Channel Rats.pdf
  - disposition: **D1** — Derived wording — Effect contains mandatory Riverboat/River Barge and the no-rivers Wagon/two-horse substitution.

### `bands/mordheim/clan-angrund-kep/special-rules.yaml`

- [x] **rule/mordheim/clan-angrund-kep/ironbreaker--watch-out/unimplemented.clan-angrund-kep.ironbreaker.watch-out** · clause `whole` · scope NO
  - register text: “An Ironbreaker knows all about the Underdeep and so he or any Dwarf 6 inches away may reroll the result on the Encounter table that affects them.”
  - KB node: `ironbreaker--watch-out` (has effect text)
  - KB effect: “An Ironbreaker knows all about the Underdeep and its perils and so he or any Dwarf 6" away may decide to reroll the result on the Encounter table that affects them.”
  - printed source: broheim.net / Heroes / 0-1 Ironbreaker / Special Rules / Watch Out! / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — Effect explicitly supplies Ironbreaker/Dwarf within 6 inches Encounter-table reroll; differences are prose condensation and inch notation.

### `bands/mordheim/cult-of-the-possessed/special-rules.yaml`

- [x] **rule/mordheim/cult-of-the-possessed/band--mutations-extra-arm/special-rule.band--mutations-extra-arm** · clause `whole` · scope YES
  - register text: “The mutant may use any single-handed weapon in the extra arm, giving him +1 attack in hand-to-hand combat. Alternatively he may carry a shield or buckler in the extra arm, gaining an extra attack but still not carrying a weapon.”
  - KB node: `band--mutations-extra-arm` (has effect text)
  - KB effect: “The mutant may use any single-handed weapon in the extra arm, giving him +1 attack when fighting in hand-to-hand combat. Alternatively, he may carry a shield or a buckler in the extra arm. If a Possessed chooses to do this, he gains an extra attack but still cannot carry a weapon. Cost: 40 gold crow”
  - printed source: mordheimer.net / Mutations / extra arm / https://mordheimer.net/docs/warbands/grade-1a-warbands/cult-of-the-possessed
  - disposition: **D3** — Register merges different subjects: source and KB allow the mutant a single-handed weapon (+1 attack) OR shield/buckler, then separately say a Possessed gains an extra attack but cannot carry a weapon. Reviewed correction: preserve that Possessed-only subject; do not apply its extra-attack/no-weapon sentence to a shield-bearing Mutant. Correct clause_text, semantic_contract and recipient conditions together in the reviewed register batch; no runtime mutation here. Cited mordheimer.net Extra Arm was independently verified (current core-warbands URL and indexed cited grade-1a page).
  - resolution (2026-11-10): **corrected** — Source subjects, recipient conditions and conditional Attack parameters corrected in the CSV. Construction now grants no attack for a Mutant shield/buckler and exactly one extra natural attack to a Possessed with Extra Arm, including an empty hand, as clarified by the user; the existing regression check was updated.

- [x] **rule/mordheim/cult-of-the-possessed/band--mutations/compiler.mutation-purchase-at-recruitment** · clause `whole--scope--mutation-construction` · scope YES
  - register text: “Mutations may be bought for a Mutant or a Possessed warrior only when they are recruited; any Mutant or Possessed may have one or more mutations”
  - KB node: `band--mutations` (has effect text)
  - KB effect: “Those who dwell in Mordheim soon develop horrible mutations, and the Cult of the Possessed seem to be especially susceptible. In addition, Mordheim attracts mutants from all over the Empire, who are always quick to join the Chaos covens. Most mutations are simply inconvenient or hideous, but some ma”
  - printed source: mordheimer.net / Mutations / https://mordheimer.net/docs/warbands/grade-1a-warbands/cult-of-the-possessed
  - disposition: **D1** — Derived wording — Effect contains recruitment-only mutation purchasing and one-or-more mutations for a Mutant/Possessed.

### `bands/mordheim/dreamwalkers-cult-of-morr-fbg/special-rules.yaml`

- [x] **rule/mordheim/dreamwalkers-cult-of-morr-fbg/dreamer--guiding-dream/mechanic.guiding-dream** · clause `whole--scope--guiding-dream-table` · scope YES
  - register text: “At the beginning of each battle the Dreamer must roll D6 and consult the Guiding Dream table: 1 Disturbing Vision (-1 Movement); 2-3 Vision of Truth (+1 to hit a nominated enemy hero); 4-5 Empowering Vision (+1 Strength against a nominated enemy hero); 6 Infuriating Vision (Frenzy against a nominated enemy hero)”
  - KB node: `dreamer--guiding-dream` (has effect text)
  - KB effect: “At the beginning of each battle, the Dreamer must roll D6 and consult the Guiding Dream table to discover what kind of vision Morr is sending him. 1 - Disturbing Vision: The vision of the previous night is clear, but incomplete. That worries the dreamer too much and he feels very tired the next day.”
  - printed source: mordheim-facebook-group / Guiding Dream / https://mordheimer.net/docs/warbands/grade-2a-warbands/dreamwalkers-cult-of-morr
  - disposition: **D1** — Derived wording — Full effect explicitly supplies the D6 table, four result bands and Movement/to-hit/Strength/Frenzy effects against nominated heroes; clause condenses intervening vision narrative.

### `bands/mordheim/druchii-mic/special-rules.yaml`

- [x] **rule/mordheim/druchii-mic/beastmaster--slavehounds/unimplemented.druchii-mic.beastmaster.slavehounds** · clause `whole` · scope NO
  - register text: “The Beastmaster may be accompanied by up to three Slavehounds, bought as henchmen and following all the rules listed for them.”
  - KB node: `beastmaster--slavehounds` (has effect text)
  - KB effect: “The Beastmaster may be accompanied by up to three Slavehounds. These are bought as henchmen and follow all rules listed for them.”
  - printed source: mordheim-index-catalog / 0-1 Beastmaster / Special Rules / Slavehounds / https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii
  - disposition: **D1** — Derived wording — Effect contains Beastmaster accompaniment by up to three Slavehounds, henchman purchase and inheritance of their rules.

### `bands/mordheim/dwarf-slayer-cult-web/special-rules.yaml`

- [x] **rule/mordheim/dwarf-slayer-cult-web/rememberer--pick-up-the-slack/unimplemented.dwarf-slayer-cult-web.rememberer.pick-up-the-slack** · clause `whole` · scope NO
  - register text: “If he was not taken out of action, the Rememberer may make a rarity or Dramatis Personae roll for each Slayer hero taken out of action this game, in addition to their normal rarity search.”
  - KB node: `rememberer--pick-up-the-slack` (has effect text)
  - KB effect: “If he was not taken out of action, the Rememberer may make a rarity or Dramatis Personae roll for each Slayer hero that was taken out of action this game in addition to their normal rarity search.”
  - printed source: mordheimer.net / 0-1 Rememberer / Special Rules / Pick up the Slack / https://mordheimer.net/docs/warbands/grade-2a-warbands/dwarf-slayer-cult
  - disposition: **D1** — Derived wording — Effect contains survival condition and one additional rarity/Dramatis Personae roll per out-of-action Slayer hero.

### `bands/mordheim/ghost-pirates-sar/special-rules.yaml`

- [x] **rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/profile.equipment-restrictions** · clause `armour-prohibition` · scope YES
  - register text: “The gibbet cage fastened around the skeleton forms a makeshift protection. This may not be lost, stolen, or given to other models.”
  - KB node: `gibbets--iron-cage` (has effect text)
  - KB effect: “The gibbet cage fastened around the skeleton forms a makeshift protection. Gibbets receive a 5+ armour save, as if they wear Heavy Armor. This may not be lost, stolen, or given to other models.”
  - printed source: broheim.net / Henchmen / 0-5 The Gibbets / Special Rules / https://broheim.net/downloads/warbands/supplement/sartosa/Ghost%20Pirates.pdf
  - disposition: **D1** — Derived wording — Effect contains the makeshift cage protection and non-transfer/loss/theft sentence; the omitted intervening armour-save sentence remains in the KB.

- [x] **rule/mordheim/ghost-pirates-sar/sea-singer--beauty-of-the-sea/mechanic.beauty-of-the-sea** · clause `whole` · scope YES
  - register text: “In order for a male, non-animal enemy to charge a Sea Singer he must pass a Leadership test or remain dazzled in place; if charged she may not be attacked back until a test is passed, and she causes Fear in female models, the whole counting as a form of Psychology.”
  - KB node: `sea-singer--beauty-of-the-sea` (has effect text)
  - KB effect: “In order for a male, non-animal enemy to charge a Sea Singer, he must pass a Leadership test, or else be dazzled at her beauty and remain in place. If charged by a Sea Singer, the model may not attack back in combat until he passes a Leadership Test in the beginning of the Combat Phase. Once a test ”
  - printed source: broheim.net / Heroes / 0-1 Sea Singer / Special Rules / https://broheim.net/downloads/warbands/supplement/sartosa/Ghost%20Pirates.pdf
  - disposition: **D3** — Register reverses the second charge condition: printed Ghost Pirates PDF p. 3, Beauty of the Sea, says the enemy charged BY a Sea Singer cannot attack back until a beginning-of-Combat-Phase Ld test succeeds. Reviewed correction: explicitly say when she charges the enemy; preserve once-passed immunity for that combat. KB already has the correct actor/direction and timing.
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

### `bands/mordheim/ghutani-rel/special-rules.yaml`

- [x] **rule/mordheim/ghutani-rel/band--slaves-can-lead/unimplemented.ghutani-rel.band.slaves-can-lead** · clause `whole` · scope NO
  - register text: “The honour code of the Arabian tribes demands that they treat slaves fairly, so a slave in an Arabian warband may become the warband leader.”
  - KB node: `band--slaves-can-lead` (has effect text)
  - KB effect: “The honour code of the Arabian tribes demands that they treat slaves fairly. It is a regular occurrence for slaves, or the sons of slaves, to gain high positions in Araby, especially if they can prove themselves on the battlefield. Therefore, it is possible for a slave in an Arabian warband to becom”
  - printed source: broheim.net / Arabian Tribes / Ghutani / Special Rules / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — Effect contains fair treatment of slaves and express eligibility of a slave to become warband leader; historical narrative is condensed.

### `bands/mordheim/guild-of-disgraced-engineers-mim/special-rules.yaml`

- [x] **rule/mordheim/guild-of-disgraced-engineers-mim/apprentice-engineers--assistant/unimplemented.guild-of-disgraced-engineers-mim.apprentice-engineers.assistant** · clause `whole` · scope NO
  - register text: “An Apprentice will assist the Expelled Engineer with his inventions; each apprentice dedicated to the project adds +1 to the Engineer's roll to create, or may search for rare items in place of the Engineer with the Engineer's rarity bonuses.”
  - KB node: `apprentice-engineers--assistant` (has effect text)
  - KB effect: “An Apprentice will assist the Expelled Engineer with his inventions; for each apprentice dedicated to the project post game the Expelled Engineer adds +1 to his roll to create. Alternatively an apprentice may search for rare items in place of the Engineer, gaining any bonuses to rarity rolls the Eng”
  - printed source: broheim.net / Heroes / 0-2 Apprentice Engineers / Special Rules / Assistant / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Guild Of Disgraced Engineers.pdf
  - disposition: **D1** — Derived wording — Effect contains +1 creation roll per project apprentice post-game and the alternative rare-item search using the Engineer’s rarity bonuses.

- [x] **rule/mordheim/guild-of-disgraced-engineers-mim/band--death-of-a-leader/unimplemented.guild-of-disgraced-engineers-mim.band.death-of-a-leader** · clause `whole` · scope NO
  - register text: “In the event the Expelled Engineer dies, he will pass the Book of Bad Ideas onto an Apprentice Engineer, who takes over the Title of Engineer.”
  - KB node: `band--death-of-a-leader` (has effect text)
  - KB effect: “In the event the Expelled Engineer dies, he will pass the Book of Bad Ideas onto an Apprentice Engineer, who will take over the Title of Engineer, allowing him to take the inventor special rule and hire a new apprentice.”
  - printed source: broheim.net / Special Rules / Death of a Leader / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Guild Of Disgraced Engineers.pdf
  - disposition: **D1** — Derived wording — Effect contains dead Engineer’s transfer of Book of Bad Ideas and Engineer title to an Apprentice; register omits the subsequent inventor/recruitment consequences only.

### `bands/mordheim/gunnery-school-of-nuln/special-rules.yaml`

- [x] **rule/mordheim/gunnery-school-of-nuln/band--proud-to-a-fault/compiler.proud-to-a-fault** · clause `whole` · scope YES
  - register text: “Members of the Gunnery School warband may never use non-black-powder ranged weapons; the restriction does not apply to Hired Swords or Dramatis Personae.”
  - KB node: `band--proud-to-a-fault` (has effect text)
  - KB effect: “Members of the Gunnery School warband may never use non-black-powder ranged weapons. This restriction does not apply to Hired Swords or Dramatis Personae.”
  - printed source: mordheimer.net / special rules / Proud To A Fault! / https://mordheimer.net/docs/warbands/grade-1b-warbands/gunnery-school-of-nuln
  - disposition: **D1** — Derived wording — The full effect prohibits non-black-powder ranged weapons and expressly exempts Hired Swords and Dramatis Personae.

- [x] **rule/mordheim/gunnery-school-of-nuln/marksmen--quick-reload/compiler.quick-reload** · clause `whole` · scope YES
  - register text: “Marksmen have the Hunter skill from the Mordheim rulebook, and a Marksman who becomes a Hero gains no further effect from taking the Hunter skill in addition.”
  - KB node: `marksmen--quick-reload` (has effect text)
  - KB effect: “Marksmen trained at the Gunnery School are forced to practice many drills day after day, including those that teach them to load their weapons for speed under high-pressure conditions. Marksmen have the Hunter skill from the Mordheim rulebook. A Marksman who becomes a Hero gains no further effect fr”
  - printed source: mordheimer.net / henchmen / 0 – 7 Marksmen / Special Rules / Quick Reload / https://mordheimer.net/docs/warbands/grade-1b-warbands/gunnery-school-of-nuln
  - disposition: **D1** — Derived wording — The full Quick Reload effect gives Marksmen Hunter and says promoted Heroes gain no further effect from taking Hunter again.

### `bands/mordheim/halflings-mic/special-rules.yaml`

- [x] **rule/mordheim/halflings-mic/halfling-elder--wizened-halfling/mechanic.wizened-halfling** · clause `whole` · scope YES
  - register text: “All halflings may also re-roll any failed leadership test when within 6 inches of the leader as well as using his leadership for both tests.”
  - KB node: `halfling-elder--wizened-halfling` (has effect text)
  - KB effect: “This old halfling is greatly respected by the other members of the warband and they never question his word. All halflings may also re-roll any failed leadership test when within 6" of the leader as well as using his leadership for both tests.”
  - printed source: mordheim-index-catalog / Halfling Special Skills / Wizened Halfling / https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings
  - disposition: **D1** — Derived wording — The effect grants Halflings within 6 inches the leader's Leadership for both tests and rerolling any failed Leadership test.

- [x] **rule/mordheim/halflings-mic/band--halfling-items/unimplemented.halflings-mic.band.halfling-items** · clause `knowledge-item-bonus-exemption` · scope NO
  - register text: “Halflings do not gain any bonuses from having Halfling items because they already know all the knowledge obtainable from them.”
  - KB node: `band--halfling-items` (has effect text)
  - KB effect: “Halflings do not gain any bonuses from having Halfling items (such as the Halfling Cookbook) because they already know all the knowledge that can be obtained from such things.”
  - printed source: mordheim-index-catalog / Special Rules / Halfling Items / https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings
  - disposition: **D1** — Derived wording — The effect denies bonuses from Halfling items because Halflings already possess their knowledge; the Cookbook is an illustrative example.

### `bands/mordheim/imperial-outriders/special-rules.yaml`

- [x] **rule/mordheim/imperial-outriders/band--dead-horses/unimplemented.imperial-outriders.band.dead-horses** · clause `whole` · scope NO
  - register text: “Dead horses must be replaced before any other income is spent. A warrior without a mount may not take part in a battle.”
  - KB node: `band--dead-horses` (has effect text)
  - KB effect: “Dead horses must be replaced before any other income is spent, using Treasures if necessary. A warrior without a mount may not take part in a battle.”
  - printed source: mordheimer.net / Further Mounted Rules / Dead Horses / https://mordheimer.net/docs/warbands/grade-1b-warbands/imperial-outriders
  - disposition: **D1** — Derived wording — The effect requires replacing dead horses before spending any other income, using Treasures if necessary, and bars unmounted warriors from battle.

### `bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml`

- [x] **rule/mordheim/lords-of-the-marsh-mim/band--scaly-skin/compiler.lizardmen-scaly-skin** · clause `whole` · scope YES
  - register text: “Fimir have a 6+ armour save that cannot be modified beyond 6 by Strength... Fimir Warriors have a 5+ armour save.”
  - KB node: `band--scaly-skin` (has effect text)
  - KB effect: “Fimir have a 6+ armour save that cannot be modified beyond 6 by Strength; a 'no save' result on the Critical Hit Charts negates it. Light armour adds +1. Fimir Warriors have a 5+ armour save.”
  - printed source: broheim.net / Special rules / Scaly Skin / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Lords Of The Marsh.pdf
  - disposition: **D1** — Derived wording — The effect gives Fimir a 6+ armour save with the Strength floor and Fimir Warriors a 5+ save; it also retains critical-hit negation and light armour details omitted by the ellipsis.

### `bands/mordheim/low-kings-mim/special-rules.yaml`

- [x] **rule/mordheim/low-kings-mim/band--underworld-contacts/unimplemented.low-kings-mim.band.underworld-contacts** · clause `whole` · scope NO
  - register text: “A Hero visiting a bordello, casino, dream parlour etc can re-roll any dice rolls made.”
  - KB node: `band--underworld-contacts` (has effect text)
  - KB effect: “A Hero visiting a bordello, casino, dream parlour etc (see Infamous Haunts) can re-roll any dice rolls made. The second result must always be accepted.”
  - printed source: broheim.net / Special rules / Underworld Contacts / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Low Kings.pdf
  - disposition: **D1** — Derived wording — The effect explicitly permits rerolling dice when visiting those Infamous Haunts and retains mandatory acceptance of the second result.

- [x] **rule/mordheim/low-kings-mim/racketeer--looter/unimplemented.low-kings-mim.racketeer.looter** · clause `whole` · scope NO
  - register text: “If the Hero takes any warriors of the enemy warband out of action, the Hero's warband receives one additional Treasure.”
  - KB node: `racketeer--looter` (has effect text)
  - KB effect: “The Hero is an expert in finding valuables on a victim before moving on. If the Hero takes any warriors of the enemy warband out of action (and he was not taken out of action himself), the Hero's warband receives one additional Treasure, in addition to the normal +1 Treasure he might already add thr”
  - printed source: broheim.net / Heroes / Racketeer / Special Rules / Looter / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Low Kings.pdf
  - disposition: **D3** — The cited Low Kings PDF, PDF page 3 / printed page 196, Looter, explicitly requires the Hero not to have been taken out of action himself. The register omits that eligibility condition and has no companion clause retaining it. Reviewed correction: restore the parenthetical not-Out-of-Action requirement in the reward trigger; retain Cutpurse addition and unchanged opposing Treasures in the referenced owning effect. KB already matches the source; no KB edit. Source verified 2026-11-10: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Low%20Kings.pdf
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`, `conditions`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

### `bands/mordheim/marauders-of-chaos/special-rules.yaml`

- [x] **rule/mordheim/marauders-of-chaos/band--marauder-special-skills-heart-of-the-warrior/unimplemented.marauders-of-chaos.band.marauder-special-skills-heart-of-the-warrior** · clause `heart-rout-and-all-alone` · scope NO
  - register text: “may re-roll any failed Rout test and is immune to All Alone tests”
  - KB node: `band--marauder-special-skills-heart-of-the-warrior` (has effect text)
  - KB effect: “Only the warband's leader may have this skill. He may re-roll any failed Rout test and is immune to fear and all alone tests.”
  - printed source: mordheimer.net / Marauder special skills / heart of the warrior / https://mordheimer.net/docs/warbands/grade-1c-warbands/marauders-of-chaos
  - disposition: **D1** — Derived wording — The effect explicitly grants failed Rout-test rerolls and All Alone immunity, alongside Fear immunity, to the leader only.

### `bands/mordheim/masters-of-horror-sylv/special-rules.yaml`

- [x] **rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform** · clause `transformation-state--scope--transformation-state` · scope YES
  - register text: “Roll a D6 each turn and consult the following. 1: Madness: your Bitten suffers from Stupidity this turn. If Transformed, they revert to human form. 2 to 5: Act as normal 6: Transformed: your Bitten gains Frenzy”
  - KB node: `the-bitten--transform` (has effect text)
  - KB effect: “Roll a D6 each turn and consult the following. Once transformed, the Bitten cast off all equipment (save for a dagger) and suffer no penalties for fighting unarmed. 1: Madness: your Bitten suffers from Stupidity this turn. If Transformed, they revert to human form. 2 to 5: Act as normal 6: Transform”
  - printed source: sylvania-supplement / 0-3 The Bitten / Special Rules / Transform / https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror
  - disposition: **D1** — Derived wording — The full Transform effect matches the cited source including the D6 table. The omitted duration and transformed-combat no-roll exception are explicitly preserved by companion register clause transformation-state--scope--transformation-duration, so this segmented state clause is D1 rather than a materially unconditional replacement rule. Sprint and equipment/unarmed consequences also have separate register clauses. Source verified 2026-11-10: https://mordheimer.net/docs/warbands/grade-2a-warbands/masters-of-horror

### `bands/mordheim/merchant-caravans/special-rules.yaml`

- [x] **rule/mordheim/merchant-caravans/band--merchant-special-skills-bribery/unimplemented.merchant-caravans.band.merchant-special-skills-bribery** · clause `whole` · scope NO
  - register text: “Whenever the warband has to take a Rout test, the Merchant may pay 5 gc per non-Hero member...”
  - KB node: `band--merchant-special-skills-bribery` (has effect text)
  - KB effect: “Whenever the warband has to take a Rout test, the Merchant may talk his hirelings into staying a little longer and face the danger. He may immediately pay 5 gc per non-Hero warband member (including Hired Swords!) still in the game. If he does, one member taken out of action already does not count f”
  - printed source: mordheimer.net / Merchant Special Skills / Bribery / https://mordheimer.net/docs/warbands/grade-1c-warbands/merchant-caravans
  - disposition: **D1** — Derived wording — The full Bribery effect contains the Rout-test trigger and immediate payment of 5 crowns per non-Hero still playing, including Hired Swords, then the model-count reduction and repeat-use conditions.

### `bands/mordheim/outlaws-of-stirwood-forest/special-rules.yaml`

- [x] **rule/mordheim/outlaws-of-stirwood-forest/band--bow-discipline/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “Every warrior may carry only one missile weapon at a time... crossbows are not permitted.”
  - KB node: `band--bow-discipline` (has effect text)
  - KB effect: “Every warrior may carry only one missile weapon at a time. Every warrior except the Cleric must carry a bow-type missile weapon, and crossbows are not permitted even if later skills would otherwise allow them.”
  - printed source: mordheimer.net / Special Rules / https://mordheimer.net/docs/warbands/grade-1b-warbands/outlaws-of-stirwood-forest
  - disposition: **D1** — Derived wording — The effect explicitly limits every warrior to one missile weapon and prohibits crossbows, retaining the bow requirement and Cleric exemption.

### `bands/mordheim/savage-orcs-kaz/special-rules.yaml`

- [x] **rule/mordheim/savage-orcs-kaz/band--orc-special-skills/unimplemented.savage-orcs-kaz.band.orc-special-skills** · clause `orc-special-skill-access` · scope YES
  - register text: “Savage Orc heroes may use the Orc special skills from TC6 instead of any of the standard skill lists available to them.”
  - KB node: `band--orc-special-skills` (has effect text)
  - KB effect: “Savage Orc heroes may use the Orc special skills from TC6 (White Dwarf 243) instead of any of the standard skill lists available to them.”
  - printed source: broheim.net / Orc Special Skills / https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
  - disposition: **D1** — Derived wording — The effect grants Savage Orc heroes TC6 Orc special skills instead of their standard lists; White Dwarf 243 is additional bibliographic detail.

### `bands/mordheim/sea-ghosts-mim/special-rules.yaml`

- [x] **rule/mordheim/sea-ghosts-mim/wayfinder--navigator/unimplemented.sea-ghosts-mim.wayfinder.navigator** · clause `whole` · scope NO
  - register text: “The Hero allows you to re-roll a single dice result per battle when within 6 inches of the warband's boat.”
  - KB node: `wayfinder--navigator` (has effect text)
  - KB effect: “Once the Wayfinder earns a captaincy aboard his own vessel he becomes Shipmaster. The Shipmaster can turn the tide when battles are being fought at sea. The Hero allows you to re-roll a single dice result per battle when within 6" of the warband's boat.”
  - printed source: broheim.net / Heroes / Wayfinder / Special Rules / Navigator / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Sea%20Ghosts.pdf
  - disposition: **D1** — Derived wording — The effect expressly permits one die-result reroll per battle within 6 inches of the warband's boat.

### `bands/mordheim/shallows-beasts-mim/special-rules.yaml`

- [x] **rule/mordheim/shallows-beasts-mim/mutant-priest--bite-attack/compiler.strikes-last-bite** · clause `whole` · scope YES
  - register text: “The Mutant-Priest has a powerful bite attack... The bite attack always strikes last.”
  - KB node: `mutant-priest--bite-attack` (has effect text)
  - KB effect: “The Mutant-Priest has a powerful bite attack. This bite attack uses the Priest's own strength to wound and receives no penalty for not using a weapon. The bite attack always strikes last, regardless of who charged or which weapon is used. The bite even attacks after double-handed weapons.”
  - printed source: broheim.net / Heroes / 0-1 Mutant-Priest / Special Rules / Bite Attack / https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Shallows%20Beasts.pdf
  - disposition: **D1** — Derived wording — The effect contains the Mutant-Priest bite attack and always-strikes-last rule, including charge/weapon independence and attacking after double-handed weapons.

### `bands/mordheim/skaven-clan-eshin/special-rules.yaml`

- [x] **rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-tail-fighting/special-rule.band--skaven-special-skills-tail-fighting** · clause `whole` · scope YES
  - register text: “The Skaven may wield a shield, knife or sword with his tail. A weapon grants one additional attack; a shield grants +1 to the armour save.”
  - KB node: `band--skaven-special-skills-tail-fighting` (has effect text)
  - KB effect: “The Skaven may wield a shield, knife or sword with his tail. A weapon grants one additional attack with that weapon; a shield grants +1 to the model's armour save.”
  - printed source: mordheimer.net / Skaven Special Skills / tail fighting / https://mordheimer.net/docs/warbands/grade-1a-warbands/skaven-eshin
  - disposition: **D1** — Derived wording — The effect permits shield, knife or sword in the tail, one additional attack with that weapon or +1 armour save with a shield.

### `bands/mordheim/skaven-of-clan-moulder-web/special-rules.yaml`

- [x] **rule/mordheim/skaven-of-clan-moulder-web/apprentices--novice-handler/unimplemented.skaven-of-clan-moulder-web.apprentices.novice-handler** · clause `whole` · scope NO
  - register text: “An Apprentice has access to the Goading system... but can only use the beneficial effect of either a Beastwhip or a Thingcatcher during a Goad, not both.”
  - KB node: `apprentices--novice-handler` (has effect text)
  - KB effect: “An Apprentice has access to the Goading system detailed below, but can only use the beneficial effect of either a Beastwhip or a Thingcatcher during a Goad, not both.”
  - printed source: mordheimer.net / 0-2 Apprentices / Special Rules / Novice Handler / https://mordheimer.net/docs/warbands/grade-2a-warbands/skaven-of-clan-moulder
  - disposition: **D1** — Derived wording — The effect grants Apprentices Goading access and limits beneficial equipment effects to either Beastwhip or Thingcatcher for a Goad, not both.

### `bands/mordheim/slavers-rel/special-rules.yaml`

- [x] **rule/mordheim/slavers-rel/band--extra-treasure/unimplemented.slavers-rel.band.extra-treasure** · clause `whole` · scope NO
  - register text: “A slaver warband will always count as gaining an extra piece of Treasure after every battle.”
  - KB node: `band--extra-treasure` (has effect text)
  - KB effect: “There are a lot of dinars to be made in the slave trade. As such a slaver warband will always count as gaining an extra piece of Treasure (as he sells non-fighting slaves) after every battle.”
  - printed source: broheim.net / Slavers / Special rules / https://broheim.net/downloads/fo/97RelicsoftheCrusadesPt2.pdf
  - disposition: **D1** — Derived wording — The effect expressly grants a Slaver warband one additional piece of Treasure after every battle; the omitted parenthesis explains selling non-fighting slaves.

### `bands/mordheim/snotlings-web/special-rules.yaml`

- [x] **rule/mordheim/snotlings-web/band--too-unruly/unimplemented.snotlings-web.band.too-unruly** · clause `whole` · scope NO
  - register text: “Snotlings may never use any Hired Swords or Dramatis Personae, with the stated exceptions.”
  - KB node: `band--too-unruly` (has effect text)
  - KB effect: “Snotlings may never use any Hired Swords or Dramatis Personae, with the exception of Snotling Hired Swords and DPs, or HS/DP that mention the warband by name.”
  - printed source: mordheimer.net / Special Rules / Too Unruly / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The full effect contains the hiring prohibition and specifies its exceptions: Snotling Hired Swords/DPs and HS/DP which name the warband.

- [x] **rule/mordheim/snotlings-web/runts--experience/unimplemented.snotlings-web.runts.experience** · clause `whole` · scope NO
  - register text: “Each Enemy Hero or Henchmen Group that knocks a Runt out of action must roll a D6, on a 5+ gains one experience point.”
  - KB node: `runts--experience` (has effect text)
  - KB effect: “Runts can earn experience as normal. However, Each Enemy Hero or Henchmen Group that knocks a Runt out of action must, after the battle roll a D6, on a result of a 5+ the warrior who killed the Runt gains one experience point as per the normal rules for gaining experience. On a roll of 1-4, the warr”
  - printed source: mordheimer.net / Runts / Special Rules / Experience / https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings
  - disposition: **D1** — Derived wording — The full effect specifies the post-battle D6 for each enemy Hero/Henchmen Group taking a Runt out of action: 5+ grants the killer one experience point, 1–4 nothing.

- [x] **rule/mordheim/snotlings-web/runts--teeny-hands/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “Runt Henchmen can only use a single One-Handed Weapon at a time... Runt henchmen are not allowed to take any types of armour. A Runt that rolls That Lad's Got Talent loses the rule.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — The worklist resolver selected runtime effect ID profile.equipment-restrictions rather than owning rule runts--teeny-hands. That rule's existing effect contains the one-active-one-handed-weapon limit, no armour and removal of Teeny Hands on Lad's Got Talent. Correct the worklist node/source reference, no KB backfill.

### `bands/mordheim/survivors-of-strigos-sylv/special-rules.yaml`

- [x] **rule/mordheim/survivors-of-strigos-sylv/band--undead-leader/unimplemented.survivors-of-strigos-sylv.band.undead-leader** · clause `undead-leader` · scope NO
  - register text: “the warband does not disband if the Strigoi is killed; may not hire a new one”
  - KB node: `band--undead-leader` (has effect text)
  - KB effect: “The Strigoi Vampire is the only Undead model in the warband. The warband does not disband if the Strigoi is killed, though it may not hire a new one.”
  - printed source: sylvania-supplement / Special Rules / Undead Leader / https://mordheimer.net/docs/warbands/grade-2a-warbands/survivors-of-strigos
  - disposition: **D1** — Derived wording — The effect expressly says the warband survives the Strigoi's death and cannot hire a replacement.

### `bands/trollheim/chaos-streets-undead-bloodlines/special-rules.yaml`

- [x] **rule/trollheim/chaos-streets-undead-bloodlines/band--von-carstein-power-dark-majesty/unimplemented.band-von-carstein-power-dark-majesty** · clause `leader-range` · scope YES
  - register text: “Increase the Vampire's Leader range by 6 inches (from 6 to 12).”
  - KB node: `band--von-carstein-power-dark-majesty` (has effect text)
  - KB effect: “Increase the Vampire's Leader range by 6" (from 6" to 12"). While the Vampire remains on the battlefield, the warband may re-roll failed Rout tests.”
  - printed source: chaos-in-the-streets / Von Carstein Special Skills / Dark Majesty / 
  - disposition: **D1** — Derived wording: full Dark Majesty effect explicitly increases the Vampire Leader range by 6 inches, from 6 to 12.

### `bands/trollheim/khemri-thieves-guild/special-rules.yaml`

- [x] **rule/trollheim/khemri-thieves-guild/guild-master-thief--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May not select Spear, Ankus, Shield or Heavy Armour... May not select Bagh Nakh at the listed warband-creation price.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — Elliptical quote: owning guild-master-thief--equipment-restrictions effect contains the listed weapon/armour prohibitions and Bagh Nakh creation-price restriction; worklist mistakenly matched the nested runtime effect ID.

- [x] **rule/trollheim/khemri-thieves-guild/guild-thief--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May not select Spear, Ankus, Shield or Heavy Armour... May not select Bagh Nakh at the listed warband-creation price.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording — Elliptical quote: owning guild-thief--equipment-restrictions effect contains the listed weapon/armour prohibitions and Bagh Nakh creation-price restriction; worklist mistakenly matched the nested runtime effect ID.

### `bands/trollheim/lustria-clan-pestilens/special-rules.yaml`

- [x] **rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-contagious/trait.contagious** · clause `contagious-reaction` · scope YES
  - register text: “A model that takes this Hero Out of Action in close combat must take a Toughness test; if the D6 result is higher than its Toughness it suffers one automatic Wound. A natural 6 always inflicts a Wound. Undead and Possessed are immune to this test.”
  - KB node: `band--clan-pestilens-special-skills-contagious` (has effect text)
  - KB effect: “Requires Rotten Body. A model that takes this Hero Out of Action in close combat must take a Toughness test. Roll D6; if the result is higher than that model's Toughness, it suffers one automatic Wound. A natural 6 always inflicts a Wound. Undead and Possessed are immune to this test.”
  - printed source: lustria / Clan Pestilens Special Skills / Contagious / 
  - disposition: **D1** — Derived punctuation: full Contagious effect contains the close-combat Out of Action trigger, Toughness test, automatic wound on natural 6, and Undead/Possessed immunity.

### `bands/trollheim/lustria-dark-elves/special-rules.yaml`

- [x] **rule/trollheim/lustria-dark-elves/corsairs--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May never use blackpowder weapons. May not select Black Venom or Draich; those entries are Heroes only. May not select the Beastmaster's Whip.”
  - KB node: `corsairs--equipment-restrictions` (has effect text)
  - KB effect: “May never use blackpowder weapons. May select the Sea Dragon Cloak even though Corsairs are not Heroes. May not select Black Venom or Draich; those entries are Heroes only. May not select the Beastmaster's Whip; it is Beastmaster only.”
  - printed source: lustria / Corsairs / 
  - disposition: **D1** — Derived partial quote: Corsairs effect explicitly contains all three prohibitions; its additional Sea Dragon Cloak permission does not contradict them.

### `bands/trollheim/lustria-lizardmen/special-rules.yaml`

- [x] **rule/trollheim/lustria-lizardmen/band--sacred-mark-venom-glands/special-rule.band--sacred-mark-venom-glands** · clause `whole` · scope YES
  - register text: “The Hero may make attacks with its teeth instead of its weapons; resolve them as Saurus Bite Attacks... +1 on the Injury roll.”
  - KB node: `band--sacred-mark-venom-glands` (has effect text)
  - KB effect: “Costs 40 gc. Skink Heroes only. The Hero may make attacks with its teeth instead of its weapons; resolve them as Saurus Bite Attacks. These attacks give the target +1 to its armour save regardless of the Skink's Strength and gain +1 on the Injury roll.”
  - printed source: lustria / Sacred Marks / Venom Glands / 
  - disposition: **D1** — Derived wording — Elliptical quote: Venom Glands effect contains replacing weapon attacks with Saurus Bite Attacks and +1 Injury; full text retains the target +1 armour-save qualification.

- [x] **rule/trollheim/lustria-lizardmen/saurus-braves--bite-attack/compiler.bite-attack** · clause `whole` · scope YES
  - register text: “A Saurus Brave makes one additional bite attack using its own Strength... resolved after attacks made with Great Weapons.”
  - KB node: `compiler.bite-attack` (**no effect text**)
  - disposition: **D1** — Derived wording — Elliptical quote: owning saurus-braves--bite-attack effect states one additional own-Strength bite resolved after Great Weapons; worklist matched nested compiler.bite-attack instead of owning node.

- [x] **rule/trollheim/lustria-lizardmen/saurus-totem-warrior--bite-attack/compiler.bite-attack** · clause `whole` · scope YES
  - register text: “The Saurus Totem Warrior makes one additional bite attack using its own Strength... striking last.”
  - KB node: `saurus-totem-warrior--bite-attack` (has effect text)
  - KB effect: “The Saurus Totem Warrior makes one additional bite attack using its own Strength to wound and suffers no penalty for fighting unarmed. The bite always strikes last, regardless of who charged or which weapons are used, and is resolved after attacks made with Great Weapons.”
  - printed source: lustria / Heroes / 0-1 Saurus Totem Warrior / Bite Attack / 
  - disposition: **D1** — Derived wording — Elliptical quote: Totem Warrior effect explicitly gives one additional own-Strength bite always striking last.

### `bands/trollheim/lustria-norse/special-rules.yaml`

- [x] **rule/trollheim/lustria-norse/band--norse-special-skills-battle-tongue/unimplemented.lustria-norse.band.norse-special-skills-battle-tongue** · clause `whole` · scope NO
  - register text: “Only the current warband leader may choose this skill. The radius of that warrior's Leader rule increases to 12 inches.”
  - KB node: `band--norse-special-skills-battle-tongue` (has effect text)
  - KB effect: “Only the current warband leader may choose this skill. The radius of that warrior's Leader rule increases to 12".”
  - printed source: lustria / Norse Special Skills / Battle Tongue / 
  - disposition: **D1** — Derived unit spelling: Battle Tongue effect states current leader only and Leader radius 12 inches.

### `bands/trollheim/lustria-pirates/special-rules.yaml`

- [x] **rule/trollheim/lustria-pirates/band--pirate-special-skills-booming-voice/unimplemented.lustria-pirates.band.pirate-special-skills-booming-voice** · clause `fleeing-reroll` · scope NO
  - register text: “Pirate Captain only. Once per turn, while the Captain is standing and not engaged in close combat, one Pirate within 8 inches who has just failed a test to flee from combat or to stop fleeing may re-roll that test.”
  - KB node: `band--pirate-special-skills-booming-voice` (has effect text)
  - KB effect: “Pirate Captain only. Once per turn, while the Captain is standing and not engaged in close combat, one Pirate within 8" who has just failed a test to flee from combat or to stop fleeing may re-roll that test.”
  - printed source: lustria / Pirate Special Skills / Booming Voice / 
  - disposition: **D1** — Derived unit spelling: Booming Voice effect contains Captain-only, once-per-turn, standing/unengaged, 8-inch recipient and failed fleeing-test re-roll conditions.

- [x] **rule/trollheim/lustria-pirates/crew--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May not select the Scourge; it is Heroes only. May not select a Parrot. May not carry the Pirate Flag.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording: owning crew--equipment-restrictions effect contains the Scourge, Parrot and Pirate Flag prohibitions; worklist matched nested profile.equipment-restrictions.

### `bands/trollheim/lustria-savage-goblins/special-rules.yaml`

- [x] **rule/trollheim/lustria-savage-goblins/red-teeth--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May not use missile weapons unless they have the Thrown Weapon rule. May not select the Sacrifice Dagger. May not select the Feather Headdress unless this model becomes the warband leader.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording: owning red-teeth--equipment-restrictions effect contains the thrown-weapon exception and both item restrictions; worklist matched nested profile.equipment-restrictions.

- [x] **rule/trollheim/lustria-savage-goblins/trackers--equipment-restrictions/profile.equipment-restrictions** · clause `whole` · scope YES
  - register text: “May not select the Sacrifice Dagger; it is Witch Doctor only. May not select the Feather Headdress unless this model becomes the warband leader.”
  - KB node: `profile.equipment-restrictions` (**no effect text**)
  - disposition: **D1** — Derived wording: owning trackers--equipment-restrictions effect contains both stated item restrictions; worklist matched nested profile.equipment-restrictions.

- [x] **rule/trollheim/lustria-savage-goblins/trackers--tracker-gear/compiler.tracker-gear** · clause `whole` · scope YES
  - register text: “Trackers begin every battle with a Rope and Hook and one set of Bolas... may not be sold or transferred, and any lost items are replaced automatically.”
  - KB node: `trackers--tracker-gear` (has effect text)
  - KB effect: “Trackers begin every battle with a Rope and Hook and one set of Bolas. These items may not be sold or transferred, and any lost items are replaced automatically for the next battle.”
  - printed source: lustria / Heroes / 0-2 Trackers / Tracker Gear / 
  - disposition: **D1** — Derived wording — Elliptical quote: Tracker Gear effect contains both starting items, transfer/sale prohibition and automatic replacement for the next battle.

### `bands/trollheim/trollheim-cult-of-the-possessed/special-rules.yaml`

- [x] **rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-extra-arm/special-rule.band--mutations-extra-arm** · clause `whole` · scope YES
  - register text: “A Mutant may use a one-handed weapon in the extra arm and gains +1 Attack, or may carry a Shield or Buckler. The Possessed gains the extra Attack but may not carry a weapon.”
  - KB node: `band--mutations-extra-arm` (has effect text)
  - KB effect: “A Mutant may use a one-handed weapon in the extra arm and gains +1 Attack in close combat, or may carry a Shield or Buckler in that arm. The Possessed gains the extra Attack but still may not carry a weapon. Cost: 40 gc.”
  - printed source: trollheim / Mutations / Extra Arm / 
  - disposition: **D1** — Derived wording: Extra Arm effect explicitly gives the Mutant weapon/attack or shield/buckler options and the Possessed extra attack without a weapon.

### `bands/trollheim/trollheim-skaven-clan-eshin/special-rules.yaml`

- [x] **rule/trollheim/trollheim-skaven-clan-eshin/band--skaven-special-skills-tail-fighting/special-rule.band--skaven-special-skills-tail-fighting** · clause `whole` · scope YES
  - register text: “The Skaven may wield a Dagger, Shield or Sword with his tail. A weapon grants one additional attack; a Shield grants +1 armour save.”
  - KB node: `band--skaven-special-skills-tail-fighting` (has effect text)
  - KB effect: “The Skaven may wield a Dagger, Shield or Sword with his tail. A weapon held this way grants one additional attack with that weapon; a Shield held this way grants +1 to the armour save instead.”
  - printed source: trollheim / Skaven Special Skills / Tail Fighting / 
  - disposition: **D1** — Derived wording: Tail Fighting effect explicitly lists Dagger/Shield/Sword and distinguishes the additional weapon attack from the shield +1 armour save.

### `catalog/items/trollheim.yaml`

- [x] **item/death_knife** · clause `whole` · scope YES
  - register text: “Attacks at -1 Strength, ignore armour saves and add +1 to Injury rolls.”
  - KB node: `death_knife` (**no effect text**)
  - printed source: chaos-in-the-streets / Deathbringer Assassin Equipment List / 
  - disposition: **D1** — Derived wording: death_knife.mechanic_id resolves to weapon.death-knife in catalog/mechanics/close-combat.yaml, whose effect states -1 Strength, ignore armour saves and +1 Injury.

### `catalog/items/weapons-close-combat.yaml`

- [x] **item/sword_scimitar** · clause `whole` · scope YES
  - register text: “A model armed with a sword may parry blows; a model may not parry attacks made with double or more its own Strength.”
  - KB node: `sword_scimitar` (**no effect text**)
  - printed source: mordheimer.net / Warrior equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/arabian-tomb-raiders; mordheimer.net / Slave equipment list / https://mordheimer.net/docs/warbands/grade-1b-warbands/arabian-tomb-raiders
  - disposition: **D1** — Derived wording — Existing canonical text: sword_scimitar.mechanic_id is weapon.sword; catalog/items/weapons-close-combat.yaml::sword contains the complete Parry text including the double-or-more-Strength prohibition, also structured in catalog/rules/resolution.yaml::parry.strength_limit.

### `catalog/mechanics/close-combat.yaml`

- [x] **mechanic/weapon.cathayan-longsword** · clause `whole` · scope YES
  - register text: “Range: Close Combat Strength: As user Special Rules Mastercrafted: Attacks made with a Cathayan longsword give the bearer +1 Initiative and +1 Weapon Skill.”
  - KB node: `weapon.cathayan-longsword` (has effect text)
  - KB effect: “A close combat weapon using the wielder's Strength, with Parry, Cutting Edge (an additional -1 armour save modifier), and Mastercrafted (+1 Weapon Skill and +1 Initiative for attacks with this sword).”
  - printed source: mordheimer.net / Soldier Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay; mordheimer.net / Ogre Equipment List / https://mordheimer.net/docs/warbands/grade-1c-warbands/maneaters
  - disposition: **D1** — Derived wording: full Cathayan Longsword effect explicitly states close combat, user Strength and Mastercrafted +1 WS/+1 Initiative.

- [x] **mechanic/weapon.starsword** · clause `whole` · scope YES
  - register text: “Range: Close Combat Strength: As user +1 Special Rules Parry: Can parry enemy blows Ignores Armour A Starsword ignores all armour saves except for ward and Dodge saves.”
  - KB node: `weapon.starsword` (has effect text)
  - KB effect: “A close combat weapon giving +1 Strength and Parry. Its attacks ignore armour saves; ward and Dodge saves are expressly retained.”
  - printed source: mordheimer.net / Heroines Equipment List / https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria; lustria / Amazons / Starsword / https://mordheimer.net/docs/testwarbands/grade-1b-warbands/amazons-lustria
  - disposition: **D1** — Derived wording: Starsword effect explicitly gives close combat, +1 Strength, Parry and ignored armour with ward/Dodge retained.

- [x] **mechanic/mechanic.mark-of-shornaal** · clause `whole` · scope YES
  - register text: “Enemy models that are not Immune to Psychology cannot attack a marked leader unless they pass a Leadership test on 3D6, discarding the lowest die.”
  - KB node: `mechanic.mark-of-shornaal` (has effect text)
  - KB effect: “Enemy models that are not Immune to Psychology cannot attack a marked leader in close combat unless they pass a Leadership test on 3D6, discarding the lowest die. On failure, they are hit automatically in close combat. Once passed, no further test is required that battle. Lizardmen Cold Blooded cann”
  - printed source: mordheimer.net / Mark of the Dark Gods / Mark of Shornaal the Serpent / https://mordheimer.net/docs/warbands/grade-1c-warbands/marauders-of-chaos
  - disposition: **D3** — Register overstates attack restriction by omitting "in close combat": the cited Mark of Shornaal source and KB both limit this Leadership gate to close combat. Reviewed correction should insert "in close combat" after "cannot attack a marked leader". Source: https://mordheimer.net/docs/warbands/grade-1c-warbands/marauders-of-chaos#mark-of-shornaal-the-serpent (Leader paragraph).
  - resolution (2026-11-10): **corrected** — Reviewed CSV edit applied to `clause_text`, `semantic_contract`, `conditions`; original notes preserved with an explicit superseding correction. Original identity and source fingerprint retained.

- [x] **mechanic/mechanic.myrmidia-eagle-friend** · clause `whole` · scope YES
  - register text: “The Priestess gains an eagle companion each time she acquires this mark... each successful attack inflicts a Strength 3 hit.”
  - KB node: `mechanic.myrmidia-eagle-friend` (has effect text)
  - KB effect: “The Priestess gains an eagle companion each time she acquires this mark. Eagles are weapons she directs: in close combat they strike first, use her Weapon Skill, and each successful attack inflicts a Strength 3 hit. Eagles cannot be attacked or slain and fly away when the Priestess is taken out of a”
  - printed source: liber-malefic / Priests for Every Occasion / Marks of Myrmidia / https://www.scribd.com/document/241727651/Miracle-workers-in-Mordheim
  - disposition: **D1** — Derived wording — Elliptical quote: full Eagle Friend effect explicitly gives one companion per acquired mark and a Strength 3 hit per successful eagle attack.
