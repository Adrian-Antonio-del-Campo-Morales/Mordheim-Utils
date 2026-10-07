# T13 — F019 The Silence bound-equipment integration

Execution report for **T13-F019 — The Silence equipment-token integration**,
reserved in the [initiative checklist](../README.md). It connects the real
Combat Lab bound-equipment stage to the shared prohibition decision with the
canonical item facts, regenerates the desktop bundle with the maintained
builder and proves the verdict through both consumers. It does not accept or
close F019, does not implement F016/F020/F021 and does not certify T13.2. It is
delivered for independent review.

Entry: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, working
tree with 274 modified/untracked entries owned by other lots. Closing revision:
same branch and HEAD. **No `AGENTS.md` exists** in the repository or its parent
directories; the dispatch is the instruction set. The checklist reservation
"F019 — The Silence equipment-token integration" was confirmed before editing,
and the accepted F017 repair
([independent acceptance](T13-band-rule-recipients.md#10-independent-coordinator-acceptance--2026-10-02))
was verified present and re-run. `bridge.ts` was read only and still matches its
entry hash.

Input hashes were captured before any edit in
`build/cache/t13-parallel/silence-equipment/entry/inputs.sha256.txt` (31
inputs). After the repair, exactly the four authorized files differ
(`entry/drift-after.txt`): `index.ts`, `eligibility.py`, `restrictions.py` and
the generated `_eligibility.js`. Every other input — `bridge.ts`, the compiler,
the adapters, the canonical YAML, the KB item/mechanics files, the existing
tests and fixtures, the shared documentation and the retained reproducers —
still matches its entry hash. As in F017, the eligibility sources are untracked
in this worktree, so the recorded hashes and logs are the attributable record.

## 1. Contract, sources and repaired layer

The canonical rule `silent-brotherhood-sc/band--the-silence`
(`sources/knowledge/bands/mordheim/silent-brotherhood-sc/special-rules.yaml`,
lines 70–99) is `runtime.scope/implemented: YES`, `grant: band`, and binds
`profile.equipment-restrictions` with `forbids: [blackpowder, animal]`:
"No warband member or hired sword may ever use blackpowder weapons or animals."

Accepted F035 reproduced the split defect: `equipmentIssue`/`tokenForbids`
already refuse both tokens when they receive item facts, but
`buildRestriction(..., "boundEquipment")` interpreted only five tokens
(`armour`, `ranged-weapons`, `heavy-armour`, `weapon.lance`, `defence.helmet`)
and the Python `validate` adapter deliberately sent an **empty catalogue** for
that stage. So the rule was decided but not enforced at the stage, and the only
pistol route was incidentally rejected by the equipment list.

The repair keeps the one shared decision and touches only the transport and the
specialist stage:

| Layer | File | Change |
| --- | --- | --- |
| Shared facts type | `packages/typescript/domain/eligibility/index.ts` | `Catalogue.items` optional canonical item projection |
| Shared stage integration | same `index.ts` | `carriedItemFacts` resolver + vocabulary-token block in `boundEquipment`, after the legacy checks |
| Transport projection | `packages/python/roster-construction/mordheim_construction/eligibility.py` | `_catalogue` projects canonical item facts; `validate("boundEquipment", ...)` uses the installed catalogue for the caller's root |
| Root forwarding | `packages/python/roster-construction/mordheim_construction/restrictions.py` | `_validate_bound_equipment_restrictions(..., root=None)` forwards the caller's root; no decision logic |
| Generated bundle | `_eligibility.js` | rebuilt only with `npm run build:eligibility` |

No new interpretation was added. The stage decides the tokens the shared
vocabulary interprets and the legacy block does not already handle; the shared
`equipmentIssue` is the only verdict, and Python only projects and transports.

## 2. Projected facts and ID/mapping resolution

- **Projection (Python).** `_catalogue(collection, ruleset, root)` now adds
  `items`: every canonical row from `load_items(ruleset, root)` keyed by item ID
  with exactly `kind`, `mechanic_id` and `tags` (470 items today). It carries no
  decisions and is cached per `(collection, ruleset, root)` with the existing
  runtime, keeping roots and catalogues isolated.
- **Resolution (shared TS).** `carriedItemFacts(catalogue, id)` returns the
  direct item row when `id` is an item ID; otherwise it collects every item
  whose `mechanic_id` equals the selected mechanic and returns facts with the
  **union of their tags**, `mechanic_id: id`, and `kind` only when all aliases
  agree (otherwise `""`). It matches no name, translation or arbitrary string.
- **Documented collision.** Mechanic `weapon.pistol` has two canonical aliases:
  `pistol` (`ranged-weapon`, blackpowder) and `pistol_brace`
  (`trollheim-equipment`, blackpowder). The kinds disagree, so the merged kind
  is empty; the tag union preserves the prohibition, and the regressions cover
  both alias orders so no first-alias choice can lose it. The empty kind is
  inert here because the shared vocabulary tokens are tag-based and the five
  legacy tokens are decided before this block.
- **Missing/ambiguous facts.** An unmapped mechanic or an item with no tags
  resolves to `null` and produces no verdict from the tokens (the legacy checks
  are unaffected). Null or absent equipment positions are skipped, so they can
  never match the unmechanised items (`crossbow_pistol`, `warhound`) that share
  the null `mechanic_id`.
- **Animal facts.** `warhound` is `kind: out-of-scope`, `tags: [animal]`, with
  no mechanic and no equipment-list route; the stage can only see it as a raw
  item ID in a bound position.

## 3. Attributable changes and closing hashes

| File | Entry → closing SHA-256 | Nature |
| --- | --- | --- |
| `packages/typescript/domain/eligibility/index.ts` | `b02f33bb…` → `19104d23a5b04c26137d81819db96eb0480cc97e6e3b1cbbba1448241a9fa3c7` | facts type, resolver, stage block (CRLF preserved) |
| `packages/python/roster-construction/mordheim_construction/eligibility.py` | `8ac69bb5…` → `ec179b1a57cf5b1fd0390ae4efd6b2b52f9063b5c99e3d2402f40bcd0923b0bc` | item projection + stage routing |
| `packages/python/roster-construction/mordheim_construction/restrictions.py` | `84b8f814…` → `da11479a941ccfbdb3e1721269b9e0ed74fb065ebe3e08f2b6ad9ace20864b6c` | root forwarding only |
| `packages/python/roster-construction/mordheim_construction/_eligibility.js` | `b80e8050…` → `fceeeda2daab8fd86e141117e6bd14ae173a18e58212eaabb8a21469a707211c` | generated; source digest `2df1e73a…` → `3e68e36ac4493c678bcb99eb17a7f2386b25f9e85a298f05f4741bd8143ec0b6` (independently recomputed) |
| `packages/typescript/domain/eligibility/bridge.ts` | `4d529e7f…` → unchanged | read only |

New deliverables: `tests/typescript/domain/silence-equipment.test.ts`
(`f4580ba7…`), `tests/python/construction/test_silence_equipment.py`
(`2cf178d1…`) and the shared canonical facts fixture
`tests/fixtures/eligibility/silence-equipment.json` (`03ff08c7…`). The Python
suite verifies the fixture against the live KB on every run, so the fixture
cannot drift silently.

## 4. Before / after evidence

Logs under `build/cache/t13-parallel/silence-equipment/validation/` and
`.../reproducers/logs/`. The retained F019 reproducer was re-run unchanged from
its original path with its original hash `0cdd9e79…`.

| Check | Before | After |
| --- | --- | --- |
| `repro_f019_silence.py` (retained) | exit 1 — "compiler boundEquipment stage accepted a blackpowder main weapon" | **exit 0 — "F019 expectation holds at both layers"; the stage refusal now reads `"blackpowder" is forbidden for silent-brotherhood-sc/silent-master.`** |
| New TS suite | exit 1 — 4 failed / 7 | exit 0 — 7 passed |
| New Python suite | exit 1 — 7 failed / 8 | exit 0 — 8 passed |
| `repro_f017_recipients.py` (retained) | — | exit 0 — F017 preserved |
| TS `shared-eligibility band-rule-recipients silence-equipment` | — | exit 0 — 47 passed |
| `npm run typecheck --workspace campaign-web-core` | — | exit 0 |
| Focused Python (shared + band + silence) | — | exit 0 — 55 passed |
| `tools/mordheim-utils.py tests --scope construction -q` | 481 passed (F017 close) | **489 passed** (481 + 8 new) |
| `tests/python/combat` | — | exit 0 — 496 passed |
| `tests/python/architecture/test_documentation.py` | 1 passed | 1 passed |

The new suites were written and run first against the unfixed code, failing
exactly on the missing stage enforcement (the Python red run failed the seven
enforcement/physical-position cases and passed only the legacy-preservation
case). Expectations are never adjusted to obtain green.

## 5. Stage evidence and its callers

The maintained caller chain is unchanged and now reaches the decision:
`compiler.compile_fighter` → `restrictions._validate_profile_selections` →
`_validate_bound_equipment_restrictions(..., root)` → `eligibility.validate` →
`desktop_call` → `bridge.desktopCall` → `buildRestriction(context,
"boundEquipment")`. The rebuilt `boundEquipment` block keeps the five legacy
checks in their original order and messages, then evaluates the remaining
shared-vocabulary tokens over every equipment position the stage processes
(`main`/`off`/`extra` hands, armour, defences) with `equipmentIssue` on a
neutral profile. Because it runs before `profileSelections`, the refusal is now
attributed to the rule instead of the equipment list.

The isolated mutation proof
(`build/cache/t13-parallel/silence-equipment/mutation/detect_integration_removal.py`,
exit 0) evaluates the maintained bundle and three in-memory variants in
separate MiniRacer instances — no live file is mutated:

```
maintained bundle:     0 of 4 expectations fail
integration removed:   2 expectations fail   (blackpowder, animal accepted again)
null guards removed:   2 expectations fail   (permitted kit falsely refused)
empty catalogue (old): 2 expectations fail   (the old adapter loses the refusal)
PROOF HOLDS: every removed integration part is detected by the maintained expectations
```

The null-guard variant records a real development defect the regressions caught:
without the guards, `null` positions matched the two items with a null
`mechanic_id` and falsely refused permitted kits. The maintained suites keep
that behaviour covered.

Consumer-level evidence: the semantic specifications that exercise the
`suppress-bound-equipment-restrictions` mutation seam (seven specs:
Bretonnian vows, Taal strictures, savage equipment) still run and report zero
errors (`validation/semantic-f019-relevant.log`). The broader
`tests/python/verification/test_semantics.py` fails only on the inherited
30 "source changed" pin measurements against KB rules this lot did not touch
(`validation/inherited-f057.log`); the log keeps the exact names and causes and
they are not attributed to this repair.

## 6. Preservation of F017 and the earlier prohibitions

- F017's accepted repair is untouched: `applicableRules` and its tests were not
  modified, and the retained reproducer exits 0. The new TS suite adds no
  recipient assertions; the existing 13 TS + 26 Python band-rule cases pass.
- The five legacy bound-equipment tokens keep their diagnostics, checks and
  order (`armour` → `ranged-weapons` → `heavy-armour` → `weapon.lance` →
  `defence.helmet`), including the combined `["armour", "blackpowder"]` case
  where the armour message still wins; the vows specs above re-prove
  lance/helmet/armour refusals through the maintained compilation route.
- Permitted and unknown seams stay legal: untagged mechanics, unmapped
  mechanics, missing bindings and tokens outside the shared vocabulary produce
  no stage verdict; no access, list, price or free-build behaviour changed.
- The browser path and `equipmentIssue` semantics are unchanged; only the
  specialist stage gained the transport it was missing.

## 7. Exact disposition of blackpowder and animal

- **Blackpowder — enforced at the responsible stage.** A Silence member with
  `weapon.pistol` (or any mechanic whose canonical alias carries the tag) is now
  refused by `boundEquipment` with the shared rule message, through the real
  Python transport and the maintained compiler route. The equipment list no
  longer masks the clause; the retained reproducer attributes the refusal to
  the corrected stage.
- **Animal — decision proved, stage boundary proved, no admitted route today.**
  `equipmentIssue`/`tokenForbids` refuse the canonical `warhound` facts, and the
  stage refuses an animal-tagged ID in a bound position. But no Combat Lab
  construction position, mechanic or equipment list currently admits an animal:
  this lot did not invent slots, purchases, mounts or participants. The
  limitation is precise and recorded: animal is enforced wherever bound
  equipment can carry its facts, with no canonical route to exercise beyond the
  boundary witness.

## 8. Limits and follow-ups

1. **F019 acceptance.** Reproducer: the retained `repro_f019_silence.py` plus the
   two new suites. Impact: The Silence's blackpowder clause is enforced at the
   stage; animal has decision and boundary proof but no admitted route. Owner:
   coordinator independent review. Resume: this delivery. Close criterion: the
   registered criterion — restrictions proved at their responsible boundary, or
   concrete unsupported categories documented without claiming Python
   enforcement. This report claims the second half for animal explicitly.
2. **Crossbow vocabulary side effect (F020).** Reproducer: a crossbow-tagged
   item in a bound position. Impact: the generic vocabulary path would enforce
   the outlaws' `crossbow` prohibition if a Combat Lab route existed; no
   crossbow mechanic exists, so it stays latent, and no F020 set/loadout work
   was done. Owner: F020/T13.2. Resume: when the ranged/set-loadout route is
   scoped. Close criterion: F020's own register.
3. **Animal route.** Reproducer: none beyond the boundary witness. Impact: an
   admitted animal construction (warhound-style participant or equipment) would
   need the same rule-attributed refusal. Owner: KB/product owner if that route
   is approved. Resume: with a canonical animal route. Close criterion: the
   route refuses the token by rule.
4. **Inherited semantic pins.** Reproducer:
   `tests/python/verification/test_semantics.py::test_structural_success_is_not_semantic_success`
   (30 `source changed` errors). Impact: aggregate semantic certification is
   stale for KB changes made by other lots; none of it involves this lot's
   files or the bound-equipment specs (0 errors). Owner: F057/coordinator.
   Resume: with the pin-reconciliation lot. Close criterion: pins re-measured
   there; this lot neither re-pinned nor certified them.

## 9. Reproducible evidence

`build/cache/t13-parallel/silence-equipment/`

- `entry/` — `head.txt`, `date.txt`, `git-status.txt`, `inputs.sha256.txt`
  (31 entry hashes), `drift-after.txt` (only the four authorized files changed;
  bridge unchanged).
- `validation/` — before/after TS logs, build/check logs, focused Python,
  typecheck, the inherited semantic-pin log with names and causes, and the
  seam-spec probe (`probe_semantic_f019.py` + `semantic-f019-relevant.log`).
- `reproducers/logs/` — `repro_f019_before.log` (stage accepted, exit 1),
  `repro_f019_after.log` (exit 0, stage-attributed refusal), `repro_f017_after.log`.
- `mutation/` — `detect_integration_removal.py` + `.log`.
- `checks/` — `postedit.sha256.txt` and `manifest.json` with all hashes.

Status: **delivered for independent review**; F019 remains open, F016/F020/F021
remain untouched, and no commit or push was made.

## 10. Independent coordinator acceptance — 2026-10-02

**Accepted; F019 resolved and reservation released.** This appendix supersedes
the delivery's pending-review status. F016/F020/F021 and T13.2 remain open.

Independent evidence: `build/cache/t13-parallel/silence-equipment-coordinator-review/`.

- All 25 delivered files verify byte-for-byte (`postedit.sha256.txt`, exit 0).
  Against the captured entry inputs, exactly the four authorized files differ,
  matching `drift-after.txt`; the bridge is unchanged, the bundle's recomputed
  source marker is `3e68e36a…`, and fresh `check:eligibility` confirms the
  generated bundle is current. Record precision: §9's "31 entry hashes" — the
  verified `entry/inputs.sha256.txt` contains 32 unique checksum lines.
- The retained unchanged reproducer `repro_f019_silence.py` (`0cdd9e79…`, the
  F035 original) exits 0 with the stage-attributed refusal
  (`"blackpowder" is forbidden for silent-brotherhood-sc/silent-master.`),
  output-identical to the delivered after-log and still distinct from the
  before-log (exit 1, "accepted (no refusal)"). The F017 reproducer also exits 0.
- Fresh suites: **47 TypeScript passed** (7 new + 18 shared + 13 F017 + 9 F035),
  **8 Python passed**, the full construction scope **489 passed**, typecheck
  exit 0, and the documentation test passes. The delivered semantic probe
  reruns identically: the seven bound-equipment seam specs report 0 errors; the
  30 `source changed` pins remain inherited, F057-owned KB-digest errors this
  lot did not touch.
- The submitted isolated mutation proof reruns identically: 0/4 maintained
  failures; integration removal, both null-guard removals and the old
  empty-catalogue transport are each detected. No live file was mutated.
- Transport/stage audit: `boundEquipment` now routes through `desktop_call`
  with the canonical item projection; the stage reuses
  `equipmentIssue`/`tokenForbids` on neutral profile facts after the five legacy
  checks; both null guards are present; `restrictions.py` only forwards the
  root. Legacy diagnostics, token order, permitted kits and F017 behavior are
  preserved, and no rule was copied into Python.
- Animal criterion independently tested (`probe_animal_criterion.py`, exit 0):
  the shared decision refuses the canonical `warhound` facts; both the transport
  and the maintained seam refuse an animal-tagged bound position; all three
  animal items (`warhound`, `warhorse`, `hunting_hounds`) carry no mechanic and
  no mapping. Precision recorded: three bands' raw equipment lists do price a
  `warhound` (12 bands' `equipment-access.yaml` mention animal ids), but the
  maintained equipment projection offers none — "no equipment list admits an
  animal" means no admitted construction route, and no participant/equipment
  slot was invented. The generic `crossbow` vocabulary path is likewise latent
  (all crossbow items are out_of_scope/unmapped).
- Retained, not rerun: the combat suite (496) and the full slow
  `test_semantics.py` file; the seam-spec probe above is the relevant semantic
  evidence. No visible-flow, T14 or T13.2 completion is claimed.

F016 may now reserve its separately scoped route work because F019's
reservation is released; F020/F021 remain open with their own criteria and the
crossbow side effect recorded in §8. The delivered report body (§§1–§9), tests,
fixture, production code and executor evidence were preserved during
acceptance; only coordination documents and this appendix were edited. No
commit, push or agent launch occurred.

## 11. Coordination record corrections — 2026-10-02

The 30 inherited `source changed` pairs belong to **T13-F001**, not F057.
This supersedes the owner proposed in §8 item 4 and the earlier §10 attribution.
F057 owns the stale parity-inventory count and its current gate repair; it does
not authorize source-pin refreshes. The original report body and frozen review
JSON/logs retain their historical wording; this correction governs future routing.

F019's acceptance and unsupported-animal disposition remain unchanged. Five
current source/transport/bundle hashes and all five accepted coordination-file
hashes matched the incoming review record before these documentary corrections.
The preserved §§1–§9 prefix still hashes to the delivered `b3d05428…`.
The remaining-plan candidate table now routes F016 rather than reopening F019;
no F016 implementation or reservation is started by this correction.

## 12. H5 source verification — item family tags (2026-10-04)

Follow-up asked whether the crossbow pistol is a crossbow and/or a blackpowder
weapon in the primary sources, and to touch tags only if the source proves it.
Decision and provenance, claim by claim.

- **`crossbow_pistol` is not a blackpowder weapon.** The rulebook prints it in
the **Missile Weapons** section (mordheimer.net `docs/weapons-armour/missile`:
"miniature crossbows with all the power and accuracy of the real thing"; Range
10", S4, Shoot In Hand-To-Hand) and it is absent from the Blackpowder section
(`docs/weapons-armour/blackpowder`). The optional blackpowder misfire rules
enumerate "(handgun, pistol, blunderbuss, warplock pistol, etc)" and do not
include it. The official FAQ entry "Q. Does the crossbow pistol count as a
pistol in the case of the Pistolier skill? A. Yes. All weapons with the name
pistol (Warplock, duelling, Crossbow) are pistols." (Annual 2002 p. 105)
classifies it as a *pistol for that skill* by name, not as powder, and the
Ultimate FAQ sentence "Pistols are listed under Blackpowder weapons…" answers
the missile-weapon-limit question ("a brace of pistols counts as two missile
weapons"), not the family of the crossbow pistol. **Decisive:** both published
lists of warbands that ban blackpowder sell it — Silent Brotherhood
(broheim.net `…/sealedcity/Silent Brotherhood.pdf` p. 3 equipment list, 35 gc,
in the warband whose The Silence reads "No warband member or hired sword may
ever use blackpowder weapons or animals") and Dark Elves (mordheimer.net
`…/grade-1b-warbands/dark-elves`: "Dark Elves may never use black powder
weapons", list sells `crossbow_pistol` at 35 gc).
- **`crossbow_pistol` counts in the `crossbow` family for prohibitions.** It
fires crossbow bolts and the printed description calls it a miniature crossbow;
the Outlaws' "crossbows are not permitted" is a family prohibition and the
audit's family check expects every item of the family to carry the tag, so a
missing tag would silently hole that clause. Documented tension:

  the Quick Shot errata carves it **out of that one skill**
  ("shoot twice per turn with a bow or crossbow (but not a crossbow pistol)",
  already verbatim in `skill.quick-shot`), and the Pistolier FAQ calls it a
  pistol **for that skill**; neither redefines the weapon family.

- **`superior_blackpowder` carries the `blackpowder` tag.** It is a batch of
superior blackpowder (out-of-scope consumable, "+1 Strength to all blackpowder
weapons … for one game"); the catalogue already tags out-of-scope family items
(`warhorse`/`warhound`/`hunting_hounds` → `animal`). Classification only: no
combat support is added (the combat engine has no blackpowder references and
its simulation mapping stays `out_of_scope`), and no band that forbids
blackpowder offers it in an equipment list, so purchase verdicts are unchanged.
The tag does reach the hiring clauses: the Dwarf Slayer Pirate's printed kit
carries the item, so the Knights of the Bitter Moors' "no Black Powder" clause
(likewise The Silence) now reports the blackpowder exclusion for him — he was
already rejected as not applicable to Humans, and the affected regression was
updated to assert the band clause.

Data changed: `sources/knowledge/catalog/items/weapons-ranged.yaml`
(`crossbow_pistol` → `tags: [crossbow]`) and
`sources/knowledge/catalog/items/out-of-scope.yaml` (`superior_blackpowder` →
`tags: [blackpowder]`). Regressions updated with the same provenance: the F019
fixture and its two suites (the brotherhood's crossbow pistol is kept legal and
the blackpowder position witnesses use `weapon.pistol`), `construction-blockers`
(the tag assertion and the corrected `equipmentIssueFor` verdict), the T10
application gate (the printed purchase is accepted; an unlisted blackpowder
item is still refused by the composition) and the reconciliation suite's
synthetic vocabulary case. Audit delta after the change: the three
`forbidden_family_missing_tag` findings disappear (the two Outlaws
`crossbow_pistol` rows and the Silent Brotherhood `superior_blackpowder` row)
and the five `offer_refused` rows for
`silent-brotherhood-sc/crossbow_pistol` disappear; every other check keeps the
`findings.json` counts.

Bibliographic limits: the Silent Brotherhood PDF cannot be fetched by the
read-only URL reader (`application/pdf` unsupported); its p. 3 equipment list is
quoted from the repository's canonical copy and the search snippet, the same
page already cited by `equipment-access.yaml`. The p. 105 Annual FAQ entry was
read through the transcribed FAQ text of the Mordheim FAQ (scribd) and the
mordheimer.net FAQ pages.
