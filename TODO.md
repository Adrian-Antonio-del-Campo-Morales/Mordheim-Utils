# Project backlog

Unresolved defects, verification work and deferred capabilities. Procedures
belong in the linked guides; counts and execution details belong in generated
reports. A historical pass does not certify the current tree.


## Knowledge-base consolidation — handoff (2026-11-11)

The goal is for every useful fact to have one authoritative home inside `sources/knowledge/`. Redundant data is removed, information with possible future value is archived, and equivalent rule descriptions share text while preserving the intended application of each rule.

**Where the work stands (2026-11-11).** The first pass was committed as `53a7ee05`, with its handoff text completed in `618cf981`. Six follow-up rounds then audited that pass against the printed sources and finished the item catalogue; every count and claim in this section was re-checked against the committed tree, and the places where it had drifted are marked **Corrected**. The knowledge-base side of the consolidation is now complete for rules prose, mechanic prose, classification reasons, item descriptions and translations. What is left is listed under *Remaining consolidation work* below: four areas of data work, the user decisions in *Open decisions for the user*, and the per-item questions in *Item catalogue: open problems* after this section. No consolidation step is blocked on another.

The resulting model is documented in `docs/reference/knowledge-base.md`. The archive preserves the previous wording and migration records needed to understand the consolidation.

### Done

- **Clause register folded into the KB.** `clause-contracts.csv` and `source-scope-review.csv` moved to `docs/archive/clause-register/` with a migration report. Coverage identities now come from the KB through `mordheim_knowledge.clauses`. They include core rules, mechanics retained by the runtime, implemented items and `YES` rule effects. The records whose printed text has several observable parts or excludes a part retain their clauses in the form `{id, scope}`. Undivided records use their own identity as the coverage target. **Corrected:** 607 records declare the 1,114 clauses, not 351; the 351 figure is the subset of those records that is admitted to the coverage denominator, and it carries 842 of the clauses, including all 540 scoped `YES`. The remaining 272 clauses sit on records outside the denominator.

- **Contract prose removed from the KB.** The register's contract wording is preserved in the archive. Descriptions of what a test observes belong beside the scenario or test function. Explicit clause IDs and scopes remain where needed to distinguish parts of a rule and preserve deliberate exclusions.

- **Coverage tooling migrated.** `tools/knowledge/clauses.py` provides `inventory`, `coverage`, `check` and `report`. It joins the KB inventory with E2E `audit_id` and `covers` declarations and deterministic `@pytest.mark.covers` markers. `check report rules` runs the clause report. Use `python tools/knowledge/clauses.py coverage --pending` to list outstanding declared coverage.

- **Derived trackers retired.** `implemented-canonical-families.yaml` was removed because the family inventory is derivable from bindings. `registry/bindings.yaml` was removed because the staging trees it described no longer exist. The `clause_registry*.py` tooling and the Combat Lab `audit` export were also removed.

- **Mechanic prose removed.** All 507 mechanic descriptions and their `effect`/`effect_i18n` fields were removed from `catalog/mechanics/close-combat.yaml`. Rules, skills and items bound to a mechanic supply the display text, which the web generator projects onto mechanic rows. Twenty-seven items without text received the description previously stored on their mechanic. The 27 mechanics with no record supplying their text retain a short `note`. The previous descriptions are preserved in `docs/archive/mechanic-texts-2026-11-11.json`.

- **Classification reasons converted to codes.** The 2,139 free-text `reason` values became 13 `reason_codes` declared in `registry/runtime-schema.yaml`. Each code has English and Spanish labels. The loader and editorial schema enforce the vocabulary, and Combat Lab renders the appropriate label. The original text is archived in `docs/archive/reason-texts.csv`.

- **Repeated rule prose consolidated.** The shared catalogue grew from 68 to 143 rules. The number of band rules using `rule_ref` rose from 377 to 742, removing 365 local text copies. Equivalent texts that differed only in the recipient's name were rewritten in neutral form, such as “this warrior”. Eleven numbered or duplicate shared IDs were renamed or retired. The four “never gains Experience” texts were consolidated. The record of merges, rewrites and renames is in `docs/archive/prose-consolidation-2026-11-11.json`. **Corrected:** `no-pain-undead` and `troll-stupidity` are the *new* names given to the retired `no-pain-4` and `stupidity-2`; they are live shared rules, not retirements. The retired IDs are the eleven listed in `retired_shared_rules` in the archive, which `tests/knowledge/test_shared_rule_fusions.py` pins. The catalogue held 144 rules after the `no-armour` correction below, and 148 after the 2026-11-11 equipment-restriction consolidation.

- **Substantive rule variants retained.** Texts with differences affecting rule application remain separate. These include Skaven hatred variants, wooded versus jungle terrain, two versus one random spell, `+D6` versus `6+` dodge saves, and the Red Fury, Monstrosity and Iron Sinews variants. Future consolidation should preserve those distinctions.

- **Web references updated.** The web artefact gained a `delegating-rules` stem so warrior cards can resolve a band rule ID to its shared text. The generator also projects the printing records' descriptions onto mechanic rows.

- **E2E corpus reworked.** Scaffolds stopped copying register text, and identities were re-keyed to current effect IDs. `covers` is optional because undivided identities require no explicit clause list.

- **Statistical deliveries refreshed.** All 5,163 statistical deliveries were re-pointed at the renamed or re-keyed scaffolds after checking that the scenario bodies were unchanged. The delivery edits were limited to `source` and `case.origin`. The script used for this migration was kept outside the repository.

- **Item catalogue consolidated (2026-11-11).** The source documents were read directly: broheim.net PDFs (*Pit Fighters*, *Hochland Bandits*, *Gunnery School of Nuln*, *Black Dwarfs*, *Pirates*, *Dark Elves*, *Lahmian*, Town Cryer #29) and a local mirror of mordheimer.net; scanned pages were rendered and read.
  - *Printed entries written* for `trident`, `main_gauche`, `disease_dagger`, `double_barrelled_handgun`, `mechanical_suit`, `swivel_gun` (its old text was a fragment of the Grape Shot rule), `cat_o_nine_tails` (was truncated), `snake_whip` (the Lahmian Serpent Whip), `throwing_axe`, `dark_elf_blade_weapon_upgrade`, `wagon_stagecoach` (it carried the boats' pointer) and `spiked_gauntlet`. Each record names its printed source in a comment.
  - *References added* where two records are one printed item: `small_ladder` → `large_ladder` (“Ladders (small/large)”), and Spanish *Lustria*/*Chaos in the Streets* rows matched by list, cost and bearers to the English entry of the same book: `beastmaster_whip` → `beastlash`, `mage_staff` → `mage_staff_of_hoeth`, `ancestral_claw` → `claw_of_the_old_ones`, `scourge` → `cat_o_nine_tails`, `horned_rat_amulet` → `warpstone_amulet`, `anointed_bolts` → `blessed_bolts`, and `carronade` and its three ammunitions → `swivel_gun`, `ball_shot`, `chain_shot` and `grape_shot`.
  - *Cleaned:* 14 items had a source-and-grade citation (“Town Cryer #29 ( 1b )”) pasted at the start of their text in both locales, now removed (the source stays in `source_refs`). Two Spanish names were not words: `double_barrelled_handgun` is now “Arcabuz de Dos Cañones” and `swivel_gun` “Cañón Giratorio”.
  - Behaviour is unchanged: only `effect`, `effect_i18n`, `effect_ref` and the two names moved. The regenerated artefact differs from the previous build only in the text of those items.

- **Campaign spell lores checked against the sources (not duplication).** `forest-goblin-magic` and `goblin-magic` are printed as separate lists on mordheimer.net, and their wording differs in ways that change the rule: `'Eadbanger` fires bolts equal to the Shaman's *Attacks* in one list and the Shaman's *Base Attacks* in the other, and `leap-of-waaagh` ignores terrain in only one of them. `woodland-incantations` (Wood Elves of Athel Loren, mordheimer.net) and `wood-elven-spells` (Wood Elves of Arden, *Mousillon* PDF) are two warbands' own lists, each printed under the heading “Woodland Incantations”, with the same six spells at the same difficulties and no rule difference — only punctuation and phrasing. All four lores keep their own records and spell ids: each is the printed list of its warband, and the KB transcribes each faithfully.

- **Printed-text follow-ups.** `quarter_staff` published only its Balanced rule; its printed entry (*Pirates of the Cathayan Sea*, which prints the Border Town Burning Cathayan equipment) also carries Parry and Freestyle, which is what `weapon.quarter-staff` already compiles, so the text now matches the mechanic. `victuals` opened its English text with a scraped “Fire :” label that the Border Town Burning book does not print, and that the Spanish never had; it is removed.

- **Name normalisation applied.** `normalize_names.py --write` ran as its own change: 26 name fields in `catalog/campaign/mutations.yaml` and 4 in `registry/sources.yaml`. The parsed content differs from the committed tree only in the sixteen Spanish mutation-chart names added by this consolidation and one English title-case fix (“Night Goblin special skills” → “Night Goblin Special Skills”); everything else was quoting. The check now reports 0 files to change.

- **Observables for E2E authors documented.** The convention was already stated in two places — `docs/reference/verification.md` (“The observable the test checks belongs in the test's docstring, not in the knowledge base”) and the E2E README (“What a scenario observes is written in the scenario's own comments”). The README now also points at the archived contract wording in `docs/archive/clause-register/clause-contracts.csv`, so an author can read the retired phrasing without it returning to the knowledge base.

- **Equipment-restriction prose consolidated (2026-11-11).** Of the 122 `*--equipment-restrictions` band rules, 55 now reference a shared text: the 32 existing references plus 23 repointed, grouped by what the binding forbids, where the whole text is the prohibition the binding encodes (recipient name aside). Four shared prohibitions were added — `no-missiles-or-armour` (the four Slayer rules), `no-equipment-but-bones` (Ghouls and Charnel Guard), `no-equipment-unarmed` and `no-weapons-unarmed` — bringing the catalogue to 148, and `wulfen-no-equipment` was renamed `no-weapons-or-armour-unarmed` when the Zombies, Shadowed and Warhounds of Chaos joined the two Wulfen; `rule_ref` references rose from 742 to 765. The 67 rules that keep local prose carry more than the prohibition — a reason, an equipment list, a printed list line or extra mechanics — and stay as printed evidence. Original texts and equivalence notes are archived in `docs/archive/prose-consolidation-2026-11-11-equipment.json`. No runtime binding, `profiles.yaml` line or clause identity changed (inventory digest still `122ce88789e8`); profile `equipment_restrictions` lines were left as printed because the shared texts say what the member texts said, so no joint rewording was needed. Evidence: a refusal harness (equipment offer sets plus carried-kit validation, 968 checks over every profile of the 18 affected bands) is identical before and after, and the regenerated artefact differs only in the delegated rule ids of the 25 affected profiles and the digests. Four pinned counts moved and were updated: `tests/knowledge/test_shared_rule_fusions.py`, `tests/knowledge/fixtures/parity/rules_catalogue.json`, `rules-catalogue.test.ts` and `presentation-completeness-regression.test.tsx`. Targeted checks run: the knowledge fusion, translation, artefact, parity-vector and editorial-schema suites; the construction equipment-restrictions, band-rule-recipients and catalogue-runtime suites; the 206 E2E executions of the affected rules and the E2E integrity suite; and the web rules-catalogue, presentation-completeness, warband-reference, displayText, knowledge-reader and parity-vector suites.

### Verification at handoff

The handoffs report passing format, name, structural, schema-strictness, clause and skeleton/scaffold checks, subject to the pre-existing failures and name-normalisation exceptions listed below.

The knowledge, construction, full E2E battery, Combat Lab non-UI, tooling, Modular engine, web Vitest and TypeScript package suites passed apart from the recorded exceptions. The Combat Lab UI tests require Tkinter.

The comments in `.github/workflows/ci.yml` were updated. CI had yet to run on the branch.

### Verification of the follow-up rounds

Every round used targeted checks only, as instructed; the full batteries have not been re-run since the handoff above, and no engine sampling was run.

Structural checks pass on the current tree and are the ones to repeat after any change: `format_yaml.py --check` (700 files, 0 would change), `normalize_names.py --check` (0 would change since the normalisation above), `clauses.py check` (0 unknown references, the same 30 reviews to reconcile), `clauses.py inventory` (4,424 identities, digest `122ce88789e8` — it moved once, when the Cleaver mechanic was retired), `audit_schema_strictness.py` (42 findings, all justified), `audit_kb_conformance.py --json` (byte-identical to the committed tree, so no deviation was added to its 103) and `generate_knowledge_web.py --check` after regenerating the artefact.

Behaviour evidence for the changes that touched bindings: the armour harness compiled every profile of the 61 bands carrying an armour restriction against five body armours, a shield, a buckler, a helmet and the Sea Dragon cloak, on the committed tree and on the corrected one — all 3,834 outcomes, refusal messages included, are identical. The Cleaver and Axe were compared field by field before merging. For prose-only rounds the regenerated artefact was diffed against the previous build, and only the intended records differ.

Tests run in the earlier rounds, which still reflect their areas: the knowledge suites (fusion, translation, band parity, artefact, parity vectors, editorial schema, contracts, strictness, catalogue, campaign, source documents), the construction files that name the changed records, the E2E integrity suite, the E2E scenarios of every changed rule, `test_weapon_variant_combat.py`, the compiled-builds generator tests and the E2E delivery selection; on the web side the presentation-completeness, displayText, WarriorCard, knowledge-reader, visible-fallback and warband-reference suites, the TypeScript rules, parity, construction and eligibility suites, and `tsc --noEmit`. Five pinned counts moved with the consolidation and were updated: `tests/knowledge/test_shared_rule_fusions.py`, `tests/knowledge/fixtures/parity/rules_catalogue.json` (read by both the Python and TypeScript parity vectors), `rules-catalogue.test.ts`, `presentation-completeness-regression.test.tsx` and `test_catalogue_runtime.py`.

**Not yet verified:** the full Python, E2E, Combat Lab, engine and web batteries, and CI, have not run since `53a7ee05`. That is the first thing to do with this branch.

### Open decisions for the user

- **Night Goblins (KAZ) Animosity.** `band--animosity` prints the same text as Crooked Moon's rule, which binds `mechanic.goblin-squabble`. Aligning the KAZ binding changed every KAZ Night Goblin fighter and broke 13 unrelated E2E scenarios. The alignment was reverted, and the rule retains `out-of-scope.group`. Decide whether the two bands should share the simulated behaviour or whether the KAZ rule requires a different interpretation. If the shared binding is adopted, the affected scenarios need to reflect that intended behaviour.

- **Clause scope versus effect scope.** `python tools/knowledge/clauses.py check` lists 30 clauses admitted as `YES` under effects classified `NO` or `LATER`. These came from the register and were retained to preserve the existing E2E identities. Reconcile each clause with its effect by deciding whether the effect should be reclassified or the clause should be withdrawn from admitted coverage.

- **Undead recipient variants.** The shared descriptions `no-pain-undead`, `immune-to-psychology-undead`, `immune-to-poison-undead`, `may-not-run-undead` and `cause-fear-undead` refer to “all warriors with the Undead special rule”. They remain separate from the corresponding per-warrior descriptions. Decide whether that recipient distinction warrants separate shared texts or can be represented while consolidating the wording.

### Remaining consolidation work

Each entry carries a rough effort and risk. *Risk* means the chance of changing behaviour or breaking evidence, not the chance of being wrong about the source.

- **Run the full batteries and CI.** Effort: low (machine time). Risk: medium — this is what would surface anything the targeted checks missed. Nothing else here should start before it.

- **Hireling identities and coverage.** Effort: medium. Risk: medium. Rules in `catalog/hirelings/*/rules.yaml` and inline hireling profile rules are outside the coverage identity inventory. Add them to `mordheim_knowledge.clauses` when their E2E or marker coverage starts; it moves the identity count and the inventory digest, so the pinned counts move with it.

- **TypeScript construction ledger.** Effort: medium. Risk: medium to high. `packages/typescript/domain/campaign/construction-clauses.json` remains a separate clause-like store owned by the eligibility domain (26 open clauses, 35 transfers), deliberately left outside this migration. Review whether the same consolidation approach applies while preserving its eligibility responsibilities; refusals and their order must stay identical.

- **Spanish review against the printed Spanish sources.** Effort: medium. Risk: low — editorial, no behaviour. Two bodies of text need it. First, the Spanish of the shared rules neutralised during the consolidation, identified in `docs/archive/prose-consolidation-2026-11-11.json`. Second, the translations added on 2026-11-11: 19 band `*--equipment-restrictions` rules whose `effect_i18n.es` was the literal `es`; 90 profile, hireling, mechanic and condition names and 37 hireling and condition effects whose Spanish copied the English (counting each record where a name repeats across the mechanics and conditions catalogues); 16 random-mutation chart names; the 27 mechanic `note` texts (the mechanics schema now declares `note_i18n`); and the Spanish of every new item description. The four `lore.prayers-of-*` notes had Spanish in the English field and now carry English. These are editorial translations built from the KB's own terms (Frenesí, Rencor, Todo Solo, Fregones and so on), not transcriptions of printed Spanish. Internal editorial notes (hireling list notes, file-level notes) were deliberately left in English. No KB text field is missing its Spanish, carries a placeholder or repeats its English, apart from the proper names *Bec de Corbin* and *Aberrantius Vigortia*.

- **Item descriptions and duplicates: done on 2026-11-11.** Every item publishes a description in English and Spanish, either its own printed entry or an `effect_ref` to the item it names (46 references). No two distinct items share copied text any more, apart from two derived descriptions that coincide (`jungle_roast` and `spider_amulet`). The work and its sources are in the Done list above; the per-item questions it left are in *Item catalogue: open problems* after this section, and the largest of them — 13 descriptions derived from equipment-list data — is blocked on Spanish books that are neither online nor mirrored here.

### Shared texts that fused different printed wordings

Comparing every fused shared rule against the printed texts it replaced (the members in `members_repointed`, read at `84a634db`) shows that 52 of the 107 fused IDs took members whose recorded printed texts differ by more than the recipient's name. Most differences are typographic — curly quotes, capitalisation, a stray space, "quarter staff" against "quarterstaff" — or flavour wording that does not change how the rule applies, and those are legitimate under the equivalence review. The cases below are the ones where the shared text does not say what the member's source says.

Corrected already:

- **Armour prohibitions reworded to match their bindings (behaviour unchanged).** Every armour-only prohibition now says what its `profile.equipment-restrictions` binding forbids:
  - `shared-rule.no-armour` (“This warrior may never wear any form of armour.”) covers the 17 rules that bind `forbids: armour`, which refuses every armour item including shields, bucklers and helmets. Besides the original nine, it now covers `kislevites`, `beastmen-raiders` (Shaman), `horned-hunters` (Initiates, Zealots), `necrarchs-mou` (Nosferatu), `savage-orcs-kaz` (Weirdo), `sisters-of-sigmar` (Augur) and `khemri-cursed-of-karak-zorn` (Troll Slayer), whose local texts said the same thing with a different recipient. Rules whose text carries more than the prohibition (a reason, or the list that applies) keep their own prose.
  - `shared-rule.no-body-armour` replaces `may-not-wear-armour`: “This warrior may not wear body armour. Shields, bucklers and helmets are not affected by this restriction.” It covers the 7 rules that bind `forbids: armour-suit`: the Sartosan, Wasteland, Bretonnian, Khorne and Cathayan pirates, the Nipponese Warrior Monks and the Lost Greycoats. `khemri-tomb-guardians` (Mortuary Acolytes) and the Cathayan Dragon Monks keep local texts reworded to “body armour”.
  - `estalian-corsairs-sar/pirates--no-armour` keeps a local text naming exactly what it forbids (light armour and toughened leathers) and what stays available (heavy armour, shields, bucklers and helmets).
  - The matching profile `equipment_restrictions` lines (EN and ES) were reworded the same way. None of the old or new lines contains a phrase that the profile-prose matcher in `domain/eligibility` (`index.ts` near line 1822) turns into a refusal, except the Dragon Monk's “never wear armour”, whose refusal set the `armour-suit` binding already enforces first.
  - Behaviour check: every profile of the 61 bands with an armour binding was compiled with five body armours, shield, buckler, helmet and the Sea Dragon cloak, against the committed KB and the corrected one. All 3,834 outcomes, including the refusal messages, are identical.
  - Display fix: `application/rules/warband-reference.ts` showed no restriction for a warrior whose equipment-restriction rule delegates its prose with `rule_ref`, and fell back to the profile line instead. It now also reads the `delegating-rules` stem. The gap affected every delegated restriction rule, including those the 2026-11-11 consolidation created.
  - Sources: the pirate and monk documents print no armour prohibition. The prohibition lives in the profile descriptions the KB carries, and those, not the published lists, define the intended behaviour.

- **Cleaver merged into the Axe.** `weapon.cleaver` and `weapon.axe` compiled to the same weapon (Strength as user, armour penetration 1); the only difference was a `weapon.cleaver` tag that no engine reads. Both Cleaver items now bind `weapon.axe`, and the `weapon.cleaver` mechanic, its E2E case and its two statistical deliveries were removed (identities 4,425 → 4,424; inventory digest now `122ce88789e8`). The frozen corpora (`compiled-cases.json` and existing `compiled-builds.json` entries) were left as they are: their cleaver fighters already carry the Axe tag and profile. One axe build was added to `compiled-builds.json` for the retargeted modular test. The stored reference samples still contain the two retired deliveries' results; drop them at the next re-sample.

- **`infiltration` restrictions restored.** Two members printed a restriction the shared text drops: `khemri-thieves-guild` ("Ruffians may not take this skill.") and `lustria-savage-goblins` ("Red Teeth and the Witch Doctor may not take this skill.", whose entry also stops before the tie-break roll). Both keep their own prose again.

- **`black-hunger` magnitude restored.** `lustria-clan-pestilens` and `trollheim-skaven-clan-eshin` print the metric Movement bonus `1D6 x 0.4" + 1"`, which is not the `+D3"` of the shared text. Both keep their own prose again.

- **Fabricated item descriptions replaced.** `toughened_leathers`, `wyrdstone_pendulum` and `warhorse` published the source name "Wahapedia" as their description in both locales. They now carry their printed entries (see “Item catalogue consolidated” in the Done list).

- **`no-weapons-or-armour` printed line restored.** `strigoi-kaz/bats--equipment-restrictions` and `strigoi-kaz/fell-bats--equipment-restrictions` print only the profile line “Equipment: None” (*Karak Azgal* PDF, pp. 53-54). They keep that line as local prose instead of the shared sentence about never using or needing weapons or armour.

- **`excellent-sight` centimetre variant restored.** The Spanish *Lustria* rule reads “Los Elfos pueden distinguir enemigos ocultos al doble de distancia que un guerrero normal (el doble de su atributo de Iniciativa en cm)”, per a 2010 transcription of the Dark Elves entry whose other rules match the KB records. That is a different distance from the shared text's inches, so `lustria-dark-elves` and `lustria-high-elves` keep their own prose. The High Elf page itself could not be retrieved; its text uses the same book's rule sentence, as the earlier record described it identically. The Wood Elf and Sea Ghost members stay shared: “All the Elves in a Wood Elf Warband” and “All the Elves” are the warband's elves either way.

Checked and kept:

- **`leader`.** The four printed variants, confirmed against *Human Pirates*, *Relics of the Crusades 2*, *Karak Azgal* and mordheimer.net, all state one rule: a member of the warband within 6" of the leader may use his Leadership for Leadership tests. “Any pirate” and “any warrior” are the members of the warband in those sources, and the Human Pirates text sends hired swords to the normal rules. The shared text applies the same way to all 52 references.

Checked and clear: the 61 members that carry no local prose (across `troll-stupidity`, `never-gain-experience`, `dwarf-hard-head`, `dwarf-armour` and the five `*-undead` texts) already referenced a shared rule before the consolidation, so they gained no text they did not display. Eight of those nine IDs are pure renames with identical wording; only `never-gain-experience` changed, folding three recipient-named texts into the neutral form, which the policy admits. No band rule acquired prose it previously lacked.

The audit is reproducible: compare each `members_repointed` entry's `effect` at `84a634db` with the shared text it now references.

### Pre-existing failures and environment blockers

- **Sunstaff Lustria translation (resolved 2026-11-11).** The item's Spanish prose was added. The two Python failures (`test_translation_coverage.py`, `test_knowledge_artefact.py::test_campaign_items_include_entries_outside_combat_lab_scope`) and three web failures (`presentation-completeness-equipment.test.tsx` twice and `visible-fallback-families.test.ts`) now pass. Its melee profile remains pending under Knowledge gaps.

- **Extra Arm with a shield.** The E2E scenario `band--mutations-extra-arm::a-shield-in-the-extra-arm-still-adds-one-attack` also fails on the committed tree.

- **Name normalisation (resolved 2026-11-11).** The pre-existing title-case and quoting drift in `catalog/campaign/mutations.yaml` and `registry/sources.yaml` was normalised by running `normalize_names.py --write` as a self-contained step, touching nothing but name scalars; `normalize_names.py --check` now reports 0 files to change. It had never failed CI: the check reported the drift but exited 0.

- **Generated web artefact.** One web test requires a `build/generated` artefact that was unavailable in the worktree.

- **Combat Lab UI environment.** The UI tests require Tkinter, which was unavailable in the Python environment used for verification.



## Item catalogue: open problems

Left over from the 2026-11-11 item consolidation. Each entry is independent; none was changed because it would alter behaviour, needs a decision, or needs a source that is not available. The two entries that only needed a source check — the Victuals “Fire :” label and the Quarter Staff text — were resolved on 2026-11-11 and are recorded in the handoff's Done list.

### Main Gauche omits its printed +1 enemy armour save

The Hochland Bandits entry prints “Parry, +1 Enemy Armour Save”, and `main_gauche` now shows it. `weapon.main-gauche` compiles with `parry` only (`catalog/mechanics/execution.yaml`), so a wound from the Main Gauche gives the defender no save bonus. Decide whether to add `target_armour_bonus: 1`. The same mechanic also serves the Estalian Diestro modes (`mechanic.main-gauche-modes`), whose printed entry should be checked first.

### Items that are the same object but differ in combat status

Each pair now shares one printed entry, but the Spanish *Lustria* row is `out_of_scope` while the English entry is `implemented`: `beastmaster_whip`/`beastlash`, `ancestral_claw`/`claw_of_the_old_ones` and `scourge`/`cat_o_nine_tails`. A Lustria Dark Elf Beastmaster, Amazon or Pirate/Norse Hero cannot take into the duel a weapon the English warband can. Decide whether to bind the Spanish rows to the same mechanics.

### Derived descriptions awaiting their printed entries

These items show a description built from their equipment-list data (list, cost, rarity, bearers) and carry a `# Derived description` comment. Their entries are printed only in Spanish books that are neither online nor mirrored here: *Khemri* (`dispelling_scroll`, `icon_of_manann`, `whip`), *Lustria* (`feather_headdress`, `sacrifice_dagger`, `magic_tattoos`, `shrunken_head` for the Savage Goblins; `jungle_roast`, `magic_tattoo`, `spider_amulet`, `poisoned_darts` for the Pygmies) and *Chaos in the Streets* (`travel_staff`, `poison_darts`). The Lustria *Spider Amulet* artefact (mordheimer.net, Lustrian Artefacts) is a different object from the Pygmy list item.

### Dark Elf Blade price

The Dark Elves PDF prints the upgrade at “+20 gold crowns to weapon/Rare 9”, and `dark_elf_blade_weapon_upgrade` shows that printed text. The mordheimer.net list and the KB equipment list charge +15 gc. Decide which price is authoritative.

### Throwing Axe rules outside the Dwarf Slayer Cult

`throwing_axe` now shows the Dwarf Slayer Cult entry, the only printed one, including its Slayer availability and the Axe Thrower skill. The Hochland Bandits, Khorne Raiders, Slayer Pirates, Marauders, Norse and Savage Orc lists print the row only. Decide whether those bands' Throwing Axe follows that entry or needs its own (the Norse list's “same as Throwing Knives” row is a separate item).

### Item coverage

Of 163 implemented items, 159 have no deterministic test naming them and 1 more is only partly covered. Use `python tools/knowledge/clauses.py coverage --kind item --pending` to inspect the outstanding declarations.

## Modular integration and E2E coverage

Strict E2E coverage of the modular oracle is unconfirmed. Close it with
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` over `tests/integration/e2e/` on the delivered
revision, preserving the accepted-evidence baseline and clause identities.
Pending clauses: `python tools/knowledge/clauses.py coverage --pending`.
See the [verification reference](docs/reference/verification.md#modular-integration-closure).

## Web projection verification

Verify Dwarf inheritance in the generated web projection, with evidence from
`outputs/web-public/knowledge/knowledge-web.json` (generate it with
`python tools/knowledge/generate_knowledge_web.py`; never hand-edit it).

## Combat Lab checklist popover closes during layout

Unverified report of `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`). Determine whether widget lifecycle
or test focus setup destroys the popover; close when both pass with their
theme, width and scrollbar assertions intact.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle. Native was
ported from NumPy, so agreement between the two never exonerates a deviation
they share. Keep tolerances and reference provenance intact; procedures are in
the [verification reference](docs/reference/verification.md).

- **Native.** Run the native runtime and deterministic replay selections
  (`tests/engines/native/`): attack-event gating, pool allocation and Rapier
  Barrage touch the replay paths. Then requalify `--scenarios big` against
  `modular-100k` and re-sample `native-e2e-100k` from a clean commit.
- **NumPy stored E2E sample.** `numpy-e2e-100k` predates the current engine.
  Re-sample it from a clean commit (the current engine passes every E2E
  delivery against `modular-e2e-100k` at 20,000 duels, including the Raging
  Peasants fist case that diverged in the stored sample).
- **Systematic E2E offset.** Every NumPy E2E delivery passes the six-sigma
  gate, yet the rates lean one way: over the 1,815 distinct inputs the
  first-win z-scores average about +0.2 and the unresolved ones about +0.9
  against `modular-e2e-100k`. The per-case z-scores share one seed, so their
  mean is less significant than it looks. Determine whether this is an engine
  difference or the oracle-provenance problem below.
- **Oracle provenance.** The stored modular samples carry a source digest that
  matches no commit, and modular commits followed them. Confirm which inputs
  those commits can affect, or regenerate the affected samples with
  authorization, before claiming current-engine certification.
- **Survivor condition (NumPy).** Campaigns compare the winner only. On
  `scenario/stateful` (20,000 duels) the winner of a decided duel is not
  Standing in 1.56 % of duels for Modular and 1.98 % for NumPy. Decide whether
  this is an ordering difference in the deciding round, and whether the
  terminal condition should become a compared magnitude.
- **Portable native digests.** `.pyx` and `.pxd` files have no line-ending rule
  in `.gitattributes`, so Windows and Linux checkouts of one commit produce
  different native digests and spurious provenance warnings.
- **Rejected E2E deliveries.** 2,485 deliveries never run: 1,491 need
  `initial_state` overrides or auxiliary participants the shared runner cannot
  express, 530 prescribe scripted decisions and 464 are expected construction
  refusals. The first two groups stay uncertified until the runner supports
  them.

Stored samples live in `tests/engines/parity/reference_samples/` (seed 2026,
50 rounds for E2E). Compare without running either engine:
`python tools/mordheim-utils.py check samples compare --scenarios e2e
--backend <numpy|native> --store <candidate> --reference-store <modular store>`.
Running the modular engine requires explicit authorization.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause. Catalogue text is corrected; motor support remains pending by user decision (2026-11-10). Sunbolt shooting remains outside the duel. |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md). Scope
changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).
