# T13 — R0 context-data evidence review

Execution delivery for the bounded, read-only investigation reserved as
**R0 — context-data evidence review** in the [initiative checklist](../README.md).
It documents, for exactly the 125 `snapshot_content_change` pairs of the
[read-only manifest](T13-context-data-manifest.json), which context data changed
between the pre-snapshot revision `eb85e95` and the current working tree, and
which maintained consumers read that data.

Sections 1–10 retain the agent handoff. Section 11 records subsequent independent
coordinator acceptance, class disposition and follow-up routing. The execution
itself did not authorize a pin edit or adopt a semantic ruling. **No source pin, specification,
canonical document, tool or shared register was modified by this lot**, and
nothing is marked accepted or closed here. In particular, [T13-F001](T13-execution-follow-ups.md#t13-f001--inherited-semantic-failures-and-stale-source-fingerprints)
and [T13-F035](T13-execution-follow-ups.md#t13-f035--revalidate-affected-t13-construction-evidence-after-eligibility-extraction)
keep their existing status.

## 1. Entry state and preservation of parallel work

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, as required by
  the dispatch. The working tree carried 192 modified/untracked entries from
  other lots at entry; they were preserved untouched. `sources/knowledge` was
  and stayed clean against HEAD, and no file of this lot overlaps another
  reservation.
- The [manifest](T13-context-data-manifest.json) was verified before any use:
  SHA-256 `86aa8194f1d96ca5d616ab2b26ac8fe930322902a49a82748f5d930f101357cd`,
  exactly the dispatched value; 125 entries with 125 unique `finding_key` values
  and 125 unique `(spec_file, specification, target)` keys; 48 specification
  files; 17 canonical files; classification `snapshot_content_change`; entry
  HEAD `1b7f7cf…`; historical snapshot `eb85e95`; source matrix
  [`T13-source-fingerprint-review.csv`](T13-source-fingerprint-review.csv) with
  SHA-256 `72c4eb02…` (matches the accepted 580-row matrix). All 48
  `entry_spec_sha256` values matched the working tree byte-for-byte.
- The accepted R0 translation-pin lot is part of the input: its delivery
  [`T13-translation-pins.md`](T13-translation-pins.md) (SHA-256 `1ef049a5…`) and
  its 300 updated pins are compatible with the baseline reused here
  (155 residual errors = 125 context + 30 historical).
- The reservation row **R0 — context-data evidence review** is present in the
  [checklist](../README.md) and reserves exactly: the read-only 125-pair
  manifest, the write-only new `T13-context-data-review.md`/`.csv`, and
  `build/cache/t13-parallel/context-data-review/**`. No pin change, semantic
  ruling, canonical/code/shared-doc edit or F001/F035 closure is authorized.
- Concurrent writers changed the [checklist](../README.md) during the lot
  (entry SHA-256 `9f9180b6…`; `78ea9aca…` at the closing check) and
  [verification.md](../../../reference/verification.md) (entry `1dc2e473…`;
  `8149f7f0…` at closing). The reservation row and the cited eligibility
  paragraph were re-read at closing and are unchanged in scope; the
  [follow-up register](T13-execution-follow-ups.md) stayed at `d684a270…`.
  Only checks governed by those documents were repeated; nothing else was
  invalidated.

Entry input SHA-256 (full values in `entry-state.json`):

| Input | SHA-256 |
| --- | --- |
| `docs/knowledge/2a2b/README.md` | `9f9180b6f027d42a…` |
| `docs/knowledge/2a2b/tasks/T13-T15-remaining-plan.md` | `7aeb0a8a2cd57168…` |
| `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` | `d684a270b8667d0b…` |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.md` | `847d5232254396ad…` |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.csv` | `72c4eb027910460d…` |
| `docs/knowledge/2a2b/tasks/T13-translation-pins.md` | `1ef049a512910a08…` |
| `docs/reference/eligibility.md` | `0bafbf699fb4ea20…` |
| `docs/reference/verification.md` | `1dc2e473c0519e07…` |
| `docs/guides/implement-and-verify-rules.md` | `e0d1596566be11bb…` |
| `apps/.../verification/inventory.py` | `e2460dc45da41d2d…` |
| `apps/.../verification/audit.py` | `98f0e8a3f2c1aee8…` |
| `packages/typescript/domain/eligibility/index.ts` | `06d8942614ef8238…` |
| `packages/typescript/domain/eligibility/bridge.ts` | `4d529e7f1d53a41b…` |
| `packages/python/.../mordheim_construction/eligibility.py` | `8ac69bb5a4e543d9…` |
| `packages/python/.../mordheim_construction/selection.py` | `70cf27c135b47321…` |
| `packages/python/.../mordheim_construction/compiler.py` | `e0609525f55918b9…` |
| `packages/python/.../mordheim_construction/contracts.py` | `f9b6b9963452f4c4…` |

## 2. Scope reconciliation: exactly the 125 context-data pairs

All 125 manifest entries were revalidated at entry (`entry-state.json`,
`revalidation_ok: 125/125`, `blocked: 0`):

1. the located `sources[].digest` in the specification still equals
   `expected_digest`;
2. the live maintained `inventory()` fingerprint equals `current_digest`;
3. the fingerprint recomputed over the extracted `eb85e95` KB equals
   `expected_digest`;
4. every target resolves in both inventories (718 obligations each).

The manifest is exactly the `source_digest_changed_snapshot_context_data` subset
of the accepted 580-row matrix: same 125 finding keys, same specification/
canonical identities and same expected/current digests (validation check
`manifest_is_accepted_matrix_context_subset`). No pair was omitted, renamed or
absorbed by a group.

| Group | Findings | Changed profiles | Non-i18n removals | Translation-only additions |
| --- | ---: | --- | ---: | --- |
| `CTX-mordheim-beastmen-raiders` | 6 | beastmen-shaman | 1 | 2 name + 2 notes (access); 1 restrictions_i18n (profiles) |
| `CTX-mordheim-black-orcs` | 12 | orc-nuttaz | 1 | 2 name + 4 notes (access); 4 restrictions_i18n |
| `CTX-mordheim-bretonnian-chapel-guard` | 8 | knights-errant, questing-knight | 4 | 3 name + 3 notes (access); 2 restrictions_i18n |
| `CTX-mordheim-dwarf-rangers` | 9 | dwarf-troll-slayers | 2 | 2 name + 3 notes (access); 1 restrictions_i18n |
| `CTX-mordheim-dwarf-treasure-hunters` | 10 | dwarf-troll-slayers | 2 | 2 name + 6 notes (access) |
| `CTX-mordheim-horned-hunters` | 4 | initiates, zealots | 4 | 2 name + 2 notes (access); 3 restrictions_i18n |
| `CTX-mordheim-norse-explorers-btb` | 4 | beserkers | 1 | 3 name + 3 notes (access); 2 restrictions_i18n |
| `CTX-mordheim-norse-explorers-lustria` | 4 | beserkers | 1 | 3 name + 3 notes (access); 2 restrictions_i18n |
| `CTX-mordheim-orc-mob` | 5 | orc-shaman | 1 | 2 name + 3 notes (access); 2 restrictions_i18n |
| `CTX-mordheim-pit-fighters` | 17 | dwarf-troll-slayer | 2 | 9 name + 5 notes (access); 1 restrictions_i18n |
| `CTX-mordheim-sisters-of-sigmar` | 1 | augur | 1 | 1 name + 5 notes (access) |
| `CTX-mordheim-tomb-guardians` | 4 | liche-priest | 1 | 2 name + 5 notes (access); 1 restrictions_i18n |
| `CTX-trollheim-chaos-streets-dwarf-treasure-hunters` | 10 | dwarf-troll-slayers | 2 | 2 name + 6 notes (access) |
| `CTX-trollheim-chaos-streets-greenskins` | 5 | orc-shaman | 1 | 2 name + 8 notes (access); 2 restrictions_i18n |
| `CTX-trollheim-chaos-streets-pit-fighters` | 11 | dwarf-troll-slayer | 2 | 10 name + 3 notes (access) |
| `CTX-trollheim-khemri-cursed-of-karak-zorn` | 9 | troll-slayer | 2 | 1 name + 5 notes (access); 2 restrictions_i18n |
| `CTX-trollheim-khemri-tomb-guardians` | 6 | mortuary-priest | 1 | 2 name + 6 notes (access); 3 restrictions_i18n |
| **Total** | **125** | **19 profiles** | **29** | **148 translation records** |

The scanner also found one adjacent rule row with a non-i18n change,
`band--human-maximum-characteristics` in `sisters-of-sigmar/special-rules.yaml`
(the effect no longer names `(campaign.limit.racial-maximum.human)`). It is
**not** an exception to the 125-pair claim: it produces no obligation in the
current inventory and no specification or finding targets it, and 0 of the 125
canonical rows changed (`rule-rows-check.json`). It is recorded as an
observation for the coordinator, not as a context-data exception.

## 3. Field-level change analysis

### 3.1 Method

The already-retained `eb85e95` KB extraction
(`build/cache/t13-parallel/source-fingerprints/eb85e95-knowledge/sources/knowledge`)
was compared with the working-tree KB. For each of the 17 referenced band
directories, `profiles.yaml`, `equipment-access.yaml` and `band.yaml` were
loaded and structurally diffed (`diff-context.py`), producing one record per
difference with document, node identity, field path, operation, previous value,
current value and an `*_i18n` classification. Lists are aligned by `id`/
`profile_id`/`item_id` when unique, otherwise by sequence alignment, so a
changed list is reported at field granularity instead of as a whole-list
replacement. A first-pass check (`repro-analysis.py`/`removal-impact.json`) was
superseded by `compensation-check.py` and `access-probe.py`, which resolve raw
equipment-list item ids through the maintained mappings; it is retained only as
an iteration record and is not used for any conclusion.

Raw (i18n-included) diffs were additionally cross-checked against
`git diff eb85e95 1b7f7cf -- <17 band dirs>`, which shows 34 changed files
(17 `profiles.yaml` + 17 `equipment-access.yaml`) and no `band.yaml` change.

### 3.2 Document-level result

| Document | Files changed | Non-i18n changes | Translation-only changes |
| --- | ---: | ---: | ---: |
| `profiles.yaml` | 17 | 29 | 26 (`equipment_restrictions_i18n`) |
| `equipment-access.yaml` | 17 | 0 | 122 (50 `name_i18n`, 72 `notes_i18n`) |
| `band.yaml` | 0 | 0 | 0 |

Because the maintained fingerprint includes the whole context documents, the
translation-only additions move the digest even where no semantic field changed.
Absence is distinguished from empty state: every removal leaves the profile with
`equipment_restrictions: []` (an empty list, present), not a missing key; the
JSON diff records `new: null` only to mean "element removed".

### 3.3 The 29 non-i18n changes: removed `equipment_restrictions` entries

Every non-i18n change is a **removal** of one free-text restriction entry from a
profile. There are no non-i18n additions or modifications in these documents.
The removed values, grouped by band, are:

| Band | Profile | Field path | Op | Removed value | Current value |
| --- | --- | --- | --- | --- | --- |
| mordheim/beastmen-raiders | beastmen-shaman | `profiles[beastmen-shaman].equipment_restrictions[0]` | remove | May select weapons from the Beastmen Equipment List, but may never wear armour. | `[]` |
| mordheim/black-orcs | orc-nuttaz | `profiles[orc-nuttaz].equipment_restrictions[0]` | remove | May use the Henchmen List, but Savage prevents them from using any armour or ranged weapons. | `[]` |
| mordheim/bretonnian-chapel-guard | knights-errant | `profiles[knights-errant].equipment_restrictions[0]` | remove | May not wear a Helmet (Vain). | `[]` |
| mordheim/bretonnian-chapel-guard | knights-errant | `profiles[knights-errant].equipment_restrictions[1]` | remove | As Knights, may not use missile weapons except Holy Water, drugs or poisons, and may not learn spells (prayers are allowed). | `[]` |
| mordheim/bretonnian-chapel-guard | questing-knight | `profiles[questing-knight].equipment_restrictions[0]` | remove | May not take a Lance (Vow of Poverty). | `[]` |
| mordheim/bretonnian-chapel-guard | questing-knight | `profiles[questing-knight].equipment_restrictions[1]` | remove | As a Knight, may not use missile weapons except Holy Water, drugs or poisons, and may not learn spells (prayers are allowed). | `[]` |
| mordheim/dwarf-rangers | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[0]` | remove | May select weapons from the Dwarf Warrior Equipment List. | `[]` |
| mordheim/dwarf-rangers | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[1]` | remove | May never carry or use missile weapons or any form of armour. | `[]` |
| mordheim/dwarf-treasure-hunters | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[0]` | remove | May select weapons from the Dwarf Warrior Equipment List. | `[]` |
| mordheim/dwarf-treasure-hunters | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[1]` | remove | May never carry or use missile weapons or any form of armour. | `[]` |
| mordheim/horned-hunters | initiates | `profiles[initiates].equipment_restrictions[0]` | remove | May select weapons from the Horned Hunter Equipment List. | `[]` |
| mordheim/horned-hunters | initiates | `profiles[initiates].equipment_restrictions[1]` | remove | May never wear armour (Strictures). | `[]` |
| mordheim/horned-hunters | zealots | `profiles[zealots].equipment_restrictions[0]` | remove | May select weapons from the Henchmen Equipment List. | `[]` |
| mordheim/horned-hunters | zealots | `profiles[zealots].equipment_restrictions[1]` | remove | May never wear armour (Strictures). | `[]` |
| mordheim/norse-explorers-btb | beserkers | `profiles[beserkers].equipment_restrictions[0]` | remove | May select weapons from the Hero Equipment List, but may never wear armour. | `[]` |
| mordheim/norse-explorers-lustria | beserkers | `profiles[beserkers].equipment_restrictions[0]` | remove | May select weapons from the Hero Equipment List, but may never wear armour. | `[]` |
| mordheim/orc-mob | orc-shaman | `profiles[orc-shaman].equipment_restrictions[0]` | remove | May select weapons from the Orc Equipment List, but may never wear armour. | `[]` |
| mordheim/pit-fighters | dwarf-troll-slayer | `profiles[dwarf-troll-slayer].equipment_restrictions[0]` | remove | May select weapons from the Ogre & Slayer Equipment List, but may never use missile weapons or any form of armour. | `[]` |
| mordheim/pit-fighters | dwarf-troll-slayer | `profiles[dwarf-troll-slayer].equipment_restrictions[1]` | remove | Dwarf Axe and Gromril Weapon options are available only to the Dwarf Troll Slayer. | `[]` |
| mordheim/sisters-of-sigmar | augur | `profiles[augur].equipment_restrictions[0]` | remove | May select weapons from the Sisters of Sigmar Equipment List, but may never wear armour. | `[]` |
| mordheim/tomb-guardians | liche-priest | `profiles[liche-priest].equipment_restrictions[0]` | remove | May select weapons from the Liche Priest Equipment List, but may never wear armour because it interferes with spell casting. | `[]` |
| trollheim/chaos-streets-dwarf-treasure-hunters | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[0]` | remove | May select weapons from the Dwarf Warrior Equipment List. | `[]` |
| trollheim/chaos-streets-dwarf-treasure-hunters | dwarf-troll-slayers | `profiles[dwarf-troll-slayers].equipment_restrictions[1]` | remove | May never use missile weapons or any form of armour. | `[]` |
| trollheim/chaos-streets-greenskins | orc-shaman | `profiles[orc-shaman].equipment_restrictions[0]` | remove | May select weapons from the Orc Equipment List, but may never wear armour. | `[]` |
| trollheim/chaos-streets-pit-fighters | dwarf-troll-slayer | `profiles[dwarf-troll-slayer].equipment_restrictions[0]` | remove | May select weapons from the Dwarf Troll Slayer Equipment List. | `[]` |
| trollheim/chaos-streets-pit-fighters | dwarf-troll-slayer | `profiles[dwarf-troll-slayer].equipment_restrictions[1]` | remove | May never use missile weapons or any form of armour. | `[]` |
| trollheim/khemri-cursed-of-karak-zorn | troll-slayer | `profiles[troll-slayer].equipment_restrictions[0]` | remove | May select close-combat weapons from the Cursed of Karak-Zorn Equipment List. | `[]` |
| trollheim/khemri-cursed-of-karak-zorn | troll-slayer | `profiles[troll-slayer].equipment_restrictions[1]` | remove | May never use missile weapons or any form of armour. | `[]` |
| trollheim/khemri-tomb-guardians | mortuary-priest | `profiles[mortuary-priest].equipment_restrictions[0]` | remove | May select weapons from the Mortuary Priest Equipment List, but may never wear armour because it interferes with the Priest's powers. | `[]` |

The 29 removals cover 19 distinct profiles. A manual line-level check of the
raw `git diff` confirmed that no other non-i18n field in these 34 documents
changed; one apparent re-wrap (`ogre-pit-fighter`, `pit-fighters/profiles.yaml`)
is YAML plain-scalar folding and compares equal after parsing, so the structural
diff correctly reports no change.

### 3.4 Translation-only changes

148 changes are `*_i18n` additions only: 50 equipment-list `name_i18n`, 72 item
`notes_i18n` and 26 `equipment_restrictions_i18n` translations. Considering
these 148 additions alone, recursively stripping `*_i18n` keys leaves no
structural difference. The 29 non-i18n deletions described separately in §3.3
remain. Translation additions do not alter maintained decision inputs; they
still move the digest because the fingerprint includes complete documents.

### 3.5 The rule-row claim

The accepted review's claim holds for every one of the 125 pairs: comparing the
exact `special-rules.yaml` row addressed by each target, with `*_i18n` keys
stripped, shows **0 changed rows** across all 17 files. The context change is
therefore entirely in the digest context documents, exactly as classified. The
only adjacent non-i18n row change (sisters `band--human-maximum-characteristics`)
is outside the 125 and has no obligation or finding (§2).

## 4. Consumers traced

### 4.1 The maintained decision path (Combat Lab)

1. `mordheim_knowledge.loader.load_bands` loads the band package including each
   profile's `equipment_restrictions` free text.
2. `mordheim_construction/eligibility.py:package_facts` projects the profile
   keys `("id", "type", "skill_access", "equipment_lists", "fixed_equipment",
   "equipment_restrictions", "rule_ids")` into the JavaScript facts. It does
   **not** project any `*_i18n` key, so translations can never reach a decision.
3. The generated bundle (`_eligibility.js`) exposes two maintained branches in
   `packages/typescript/domain/eligibility/index.ts`:
   - `buildRestriction(..., "boundEquipment")` (lines ~310–313) reads the
     structured `profile.equipment-restrictions` bindings collected from the
     profile's automatic special rules and rejects armour, ranged weapons, heavy
     armour, lances or helmets by `forbids` category;
   - `buildRestriction(..., "profileSelections")` (lines ~403–405) joins the
     free-text `equipment_restrictions` and matches the maintained keyword list
     (`never wear armour`, `any form of armour`, …) to forbid armour, off-hand
     or two-handed weapons.
4. `mordheim_construction/restrictions.py:_validate_profile_selections` calls
   `boundEquipment` **before** `profileSelections` inside `compile_fighter`;
   `selection.py` supplies the package, profile and automatic rule bindings.
5. `mordheim_construction/selection.py` resolves the band/profile and the
   applicable rules; it does not read the free text directly.

Consequence: for the 17 profiles whose removed text matched an armour keyword,
the same ban is still enforced by a structured binding that already existed at
`eb85e95` (the rule rows are unchanged). The removals delete a duplicate free
text, not an effective restriction. `compensation-check.json` shows all 17
keyword profiles have a `profile.equipment-restrictions` binding with
`forbids: [armour]` (for `orc-nuttaz` also `ranged-weapons`), supplied by rules
such as `dwarf-troll-slayers--no-armour`, `augur--no-armour`,
`mortuary-priest--no-armour`. The two non-keyword profiles have structured
`defence.helmet` (`knights-errant--vain`) and `weapon.lance`
(`questing-knight--vow-of-poverty`) bindings.

The equipment-access probe shows this compensation is substantive, not vacuous:
16 of the 19 affected profiles can legally equip at least one armour item
according to the current access decision; 14 of them both offer armour and carry
the structured `forbids: armour` binding, so only the binding prevents armour.
Without it, removing the free text would have changed the decision.

### 4.2 Adjacent consumers (Warband Manager, read-only trace)

- `packages/python/campaign/mordheim_campaign/application/knowledge_port.py:335`
  and `packages/typescript/application/campaign/service.ts:585` use
  `equipment_restrictions` only when `equipment_lists` is empty, to block
  purchased equipment. None of the 19 affected profiles has empty lists
  (`repro-matrix.json`, `empty_equipment_lists: 0` in both revisions), so the
  condition is unchanged.
- `packages/typescript/application/rules/warband-reference.ts:108-120` prefers
  the structured rule effect, then the free text, then an "unavailable" label;
  with the free text removed, the structured effect still renders.
- `tools/knowledge/generate_knowledge_web.py:634-637` publishes
  `profile_restrictions` from the free text plus `equipment_restrictions_i18n`;
  it consumed the translation additions and now publishes empty profile
  restriction lists for the affected profiles.
- `packages/typescript/domain/campaign/construction.ts:335`,
  `tools/knowledge/audit_kb_conformance.py`, `tools/knowledge/derive_kb_contract.py`
  reference the field for projection, contract derivation and auditing.

### 4.3 What the trace cannot show

A source search locates code; the reproductions below show the current consumer
executing. Neither proves how the pre-extraction engine behaved, whether a legal
choice's combat effect is implemented, or that some other consumer outside this
trace does not read the free text. No other consumer of
`equipment_restrictions` in the working tree was found by
`grep -rn equipment_restrictions --include=*.py --include=*.ts packages apps tools tests`
beyond the ones listed.

## 5. Reproductions

All reproductions used the maintained APIs only: `compile_fighter`,
`eligibility.validate`/`desktop_call` and `load_bands`/`runtime_bindings`, with
the real band packages of each revision. No tag was injected, no profile was
fabricated and no contract was altered.

### 5.1 Canonical compile witnesses

Same build against the live KB and the extracted `eb85e95` KB
(`repro-compile.json`): 8/8 scenarios produce the same outcome and message.

| Scenario | Class | Build | Live KB | `eb85e95` |
| --- | --- | --- | --- | --- |
| armour-ban-dwarf-rangers | changed (armour keyword) | dwarf-troll-slayers + light armour | rejected: `armour is forbidden…` | rejected: same message |
| armour-ban-dwarf-treasure | changed (armour keyword) | dwarf-troll-slayers + light armour | rejected | rejected |
| armour-ban-pit-fighters | changed (armour keyword) | dwarf-troll-slayer + light armour | rejected | rejected |
| armour-ban-horned-hunters | changed (armour keyword) | initiates + light armour | rejected | rejected |
| helmet-text-knights-errant | changed (no keyword) | knights-errant + helmet | rejected: `helmet is forbidden…` | rejected: same message |
| control-helmet-questing-knight | control | questing-knight + helmet | accepted | accepted |
| control-runesmith-armour | control | runesmith + light armour | accepted | accepted |
| control-questing-knight-armour | control | questing-knight + light armour | accepted | accepted |

### 5.2 Stage separation

`repro-stages.json` separates the two branches for the same builds. Example
`dwarf-rangers/dwarf-troll-slayers` + light armour:

| Revision | `equipment_restrictions` | `boundEquipment` | `profileSelections` |
| --- | --- | --- | --- |
| live | `[]` | `armour is forbidden…` (structured binding) | `None` |
| `eb85e95` | 2 entries | `armour is forbidden…` (structured binding) | `armour is forbidden…` (free text) |

The final compile decision is the structured one in both revisions; the free
text was already redundant for this profile. `knights-errant` + helmet behaves
analogously (structured `defence.helmet`), while the `questing-knight` armour
control is accepted in both revisions.

### 5.3 Full affected-profile matrix

`repro-matrix.json` runs the same armour build for all 19 affected profiles on
both revisions: **0 compile-outcome differences** (same outcome and message).
13 profiles show a stage-level difference (the free-text branch was active on
`eb85e95`, silent live) that never reaches the final decision because the
structured binding rejects first; 6 profiles behave identically at both stages.
No profile in the set is uncompensated, and no affected profile has empty
equipment lists.

### 5.4 Commands and exit codes

All commands from the repository root with `python -X utf8`; exit 0 unless noted.

| Step | Command | Artifact |
| --- | --- | --- |
| Entry check | `build/cache/t13-parallel/context-data-review/entry-check.py` | `entry-state.json`/`.txt` |
| Context diff | `diff-context.py` | `context-diff.json`, `context-diff-summary.txt` |
| Rule-row check | `rule-rows-check.py` | `rule-rows-check.json` |
| Compensation | `compensation-check.py` | `compensation-check.json` |
| Access probe | `access-probe.py` | `access-probe.json` |
| Compile witnesses | `repro-compile.py` | `repro-compile.json` |
| Stage separation | `repro-stages.py` | `repro-stages.json` |
| Profile matrix | `repro-matrix.py` | `repro-matrix.json` |
| Deliverable | `generate-deliverable.py` | `T13-context-data-review.csv`, `delivery-summary.json` |
| Validation | `validate-deliverable.py` | `deliverable-validation.json` (20/20 checks, exit 0) |
| Documentation links | `python -m pytest tests/python/architecture/test_documentation.py -q` | run after the last edit of this document |

### 5.5 Limits of the reproductions

The `eb85e95` runs use the **current** consumer against historical data. They
prove that the data change alone does not flip the current decision in the
reproduced scenarios; they do not prove the behaviour of the historical engine
or of removed/renamed code, and they do not certify a combat effect. Reproduction
coverage is one armour scenario per affected profile plus the helmet/lance
class; other item classes were not probed because none of the removed texts
matches their maintained branches. The inherited focused-suite baseline
(`test_semantics.py`: 1 failed / 3782 passed, the structural audit test on the
155 residual pins) was reused, not re-run, because this lot changed no source,
specification or KB file; no semantic corpus, coverage, parity or other-lot
suite was repeated.

## 6. Contradictions, limits and pending decisions

- **No contradiction** with the accepted classification was found: all 125 pairs
  keep their rule row unchanged; all non-i18n differences are the 29 removals in
  the 17 `profiles.yaml` files; `equipment-access.yaml` changes are translation
  only; `band.yaml` is unchanged. The one adjacent non-i18n row change is
  documented in §2 and is not part of the 125.
- **Historical data vs observed behaviour.** §3 is a data diff; §5 is current
  consumer behaviour over two data revisions. Neither establishes what the
  historical engine would compute, and a legal choice is not evidence that a
  duel effect exists.
- **Unprobed consumers/classes.** Translation rendering beyond the traced
  generators, campaign persistence of old records, and any downstream consumer
  outside this checkout were not executed. The free-text field still exists and
  is still read by the keyword branch for other profiles; its removal here does
  not delete the branch.
- **Pending decisions (coordinator):**
  1. Whether the 125 pins may be repinned after reviewing these groups, and
     whether that is one decision for all 17 groups or per class (all classes
     share the same evidence shape).
  2. Whether the removals are an accepted de-duplication policy (free text
     replaced by structured `profile.equipment-restrictions` bindings) or
     whether the source/band owner must restore any removed wording.
  3. Whether the presentation fallback (`warband-reference.ts`, generated
     knowledge web) needs a follow-up now that affected profiles render no free
     text (the structured rule effect remains available).
  4. Whether F035's eligibility revalidation must cover these context changes;
     this lot deliberately does not close F035.
- **No new finding is required.** All pairs carry existing IDs from the
  manifest (`T13-F001` 125×, `T13-F035` 13×, `T13-F017` 11×, `T13-F014` 8×,
  `T13-F010` 3×, `T13-F016` 2×). If the coordinator wants a dedicated entry for
  the de-duplication policy or the presentation fallback, the proposed text is:
  *"T13-Fxxx (provisional): the 17 affected bands drop free-text
  `equipment_restrictions` entries already enforced by structured
  `profile.equipment-restrictions` bindings. Decide the de-duplication policy,
  confirm every consumer reads the structured form, and route any presentation
  regression before the affected pins are repinned."* No ID is assigned here
  and the shared register was not edited.

## 7. Proposed grouping for later review or repair

The evidence supports reviewing the 125 by three classes instead of pair by
pair, with the CSV preserving individual traceability:

1. **G1 — armour-ban de-duplication (117 findings, 16 groups).** Profiles whose
   removed text matched a maintained armour keyword; each has a structured
   `forbids: armour` binding and a reproduced unchanged decision. A single
   coordinator review of the class can cover the pin policy; any wording
   restoration belongs to the source/band owner.
2. **G2 — non-keyword removals (8 findings, `bretonnian-chapel-guard`).**
   `knights-errant` (Vain helmet; knightly missile/spell text) and
   `questing-knight` (Vow of Poverty lance). Structured `defence.helmet` /
   `weapon.lance` bindings remain; the missile/spell clause is enforced by other
   compiler contracts (`compiler.chivalry`, `compiler.no-missile-weapons`), which
   this lot did not re-certify.
3. **G3 — translation-only additions (all groups).** 148 `*_i18n` records that
   must not influence the pin decision by themselves; only their presence in the
   digest moved. They are candidates for a presentation/regeneration check, not
   for a semantic review.

Suggested order: coordinator accepts the class analysis for G1 (cheapest, 117
findings), then G2 (source wording check), then decides pin and presentation
actions for G3. No repair was started by this lot.

## 8. Evidence inventory

Everything below is read-only evidence under
`build/cache/t13-parallel/context-data-review/` (ignored by Git) except the two
versioned deliverables. Scripts are small and re-runnable; JSON inputs were not
edited by hand.

| Artifact | Contents |
| --- | --- |
| `entry-check.py`, `entry-state.json/.txt` | manifest/matrix hashes, entry spec hashes, 125-pair revalidation |
| `diff-context.py`, `context-diff.json`, `context-diff-summary.txt` | field-level doc diffs with per-change classification |
| `rule-rows-check.py`, `rule-rows-check.json` | rule-row re-check and the adjacent sisters observation |
| `compensation-check.py`, `compensation-check.json` | removals vs structured bindings and access offers |
| `access-probe.py`, `access-probe.json` | maintained access decision for the 19 profiles |
| `repro-analysis.py`, `removal-impact.json` | superseded first pass (not used; see §3.1) |
| `repro-compile.py/.json`, `repro-stages.py/.json`, `repro-matrix.py/.json` | canonical compile, stage-level and full-matrix reproductions |
| `generate-deliverable.py`, `delivery-summary.json` | generator and aggregate counts |
| `validate-deliverable.py`, `deliverable-validation.json` | 20 integrity checks, all passed |
| `T13-context-data-review.csv` | the versioned 125-row deliverable |

## 9. Validation performed

- **Scope**: 125 CSV rows; finding keys and `(spec_file, specification, target)`
  pairs identical to the manifest; 48 specification files; 17 canonical files;
  17 context groups; the manifest is the accepted matrix's context-data subset.
- **Integrity**: every `expected_digest`/`current_digest` equals the accepted
  `findings.json` values; every JSON column parses; every row has non-empty
  changed fields and at least one reproduction; `follow_up_ids` are carried
  unchanged from the manifest; the rule-row check reports 0 changed rows among
  the 125.
- **Bytes**: UTF-8, LF only (no CR), no tabs, no trailing whitespace, file ends
  with LF; required columns present and non-empty. All checks passed
  (`deliverable-validation.json`).
- **Documentation**: `tests/python/architecture/test_documentation.py` run after
  the last edit of this document; local links resolve.
- **Not run**: semantic corpus, coverage, parity, native, web or other-lot
  suites, and the `refresh_spec_digests.py` rewrite (never authorized here).

## 10. Delivery summary

- **Tarea/lote:** R0 — context-data evidence review (read-only investigation,
  125 manifest pairs).
- **Revisión de entrada y revisión probada:** `1b7f7cf…` + working tree; entry
  hashes in §1; closing check in `closing-check.json`; the compared KB
  revisions are the live tree and the extracted `eb85e95` snapshot.
- **Archivos creados:** `T13-context-data-review.md`,
  `T13-context-data-review.csv` and the ignored evidence directory. No other
  file was written; no commit or push.
- **Decisiones y fuentes:** none adopted; source reading per §3–§5, decisions
  left to the coordinator (§6).
- **Pasos completados:** manifest/entry verification, 125-pair revalidation,
  field-level diffs, rule-row and compensation checks, access probe, three
  reproduction layers, CSV/MD generation and 20 validation checks.
- **Comandos y códigos:** §5.4; all exit 0 except the reused baseline (not
  re-run). The validator exits 0 with 20/20 checks.
- **Casos cubiertos y omisiones:** all 125 pairs traced and grouped; 19/19
  affected profiles reproduced with 0 decision differences; omitted: historical
  engine behaviour, presentation execution, other consumer classes outside the
  grep scope (§4.3, §5.5).
- **Evidencia reproducible:** §5.4 and `delivery-summary.json`; the CSV carries
  `evidence_refs` per row.
- **Bloqueos y dependencias:** none for this lot; F001/F035 unchanged;
  pin decisions are the coordinator's.
- **Archivos que pueden liberarse:** none reserved by this lot beyond the two
  deliverables; the R0 context-data reservation may be released by the
  coordinator after review.
- **Siguiente acción recomendada al coordinador:** review the three proposed
  classes (§7), decide the de-duplication policy and pin disposition, and route
  any presentation/regeneration follow-up; do not close F001/F035 or accept the
  lot from this handoff.

## 11. Coordinator acceptance and class disposition — 2026-10-01

**Accepted as bounded research; external reservation released.** The coordinator
performed independent checks to resolve specific acceptance questions, without
repeating the agent's investigation. Evidence is retained separately under
`build/cache/t13-parallel/context-data-coordinator-review/`.

- Exact manifest hash and CSV identities/digests: 125/125 match. Fresh maintained
  inventories over live and historical KB reproduce all current/expected
  fingerprints; every registered specification pin still holds its expected
  digest. The 48 specification and 17 canonical source-file entry hashes match.
- Independent context comparison confirms 34 changed documents and exactly
  29 free-text restriction removals across 19 profiles. Access/band documents
  have no non-i18n difference. All other non-i18n profile data is equal after
  accounting for those removals. Three historical context files were compared
  directly with their `eb85e95` Git objects and match the retained extraction.
- Relevant loader-adapter/compiler/contracts/shared-decision input hashes match
  the agent's entry. The existing embedded-bundle freshness test passes (1 test).
  Five independent canonical compilation probes agree for both data revisions:
  Slayer armour refusal plus allowed Runesmith armour; Knight Errant helmet
  refusal plus allowed Questing Knight helmet; Questing Knight lance refusal.
  The existing full 19-profile matrix is reused with matching inputs.
- The only later changed inputs are coordinator documentation. KB is clean;
  manifest, matrix, CSV, pins and product code were not edited by this review.

**Disposition:** retain the existing deduplication for the reviewed context
groups. Structured canonical rules/access remain the authoritative restrictions;
do not restore duplicate profile text merely to recover an old fingerprint.
G1's 117 and G2's eight pairs are eligible for a separately reserved, exact
125-pair pin-only refresh after entry revalidation. G3 translation additions
need no separate semantic ruling. This accepts the observed data-change impact,
not general correctness of every restriction or the historical engine.

The current reference renderer gives localized structured restriction-rule
effects priority over the legacy profile fallback. Empty legacy fields therefore
do not by themselves demonstrate blank restrictions in the visible reference.
No renderer execution was part of either investigation. The coordinator records
[F041](T13-execution-follow-ups.md#t13-f041--verify-restriction-presentation-after-structured-deduplication)
for T15 to check all affected profiles in EN/ES, including compound clauses and
equipment-list notes; this is an unexecuted presentation check, not a proven bug.
No new text, generator or product repair is authorized by this acceptance.

F001 remains open: the 125 pins have not moved and the 30 historical pairs
retain their separate owner review. F035 remains open: these reproductions and
bundle freshness do not replace the affected T13 construction/fixture gates.
F040 retains its separate independent-review status. Documentation links are
checked after the acceptance edits. No agent, commit or push was initiated.
