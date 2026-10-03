# T13 L02–L05 — joint independent review

Independent, read-only review of four delivered lots: **L02 Vomit Attack**,
**L03 Spectral Touch activation**, **L04 Shifty activation** and **L05 canonical
choices/grants**. It does not certify T13, the optimized engines or any pending
GUI/backend flow.

## 1. Base examined and review limits

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, dirty working
  tree (the deliveries live there, not in HEAD). No `AGENTS.md` at the root.
- Entry capture: 35 production/KB/test files hashed and byte-copied to
  `build/cache/t13-parallel/l02-l05-independent-review/entry/`
  (`hashes.sha256`, `branch.txt`, `head.txt`, `status.txt`).
- Reviewed behaviour is the captured revision. **Four inputs drifted during the
  review** (concurrent L06 work: `kernel.py`, `modular/attacks.py`,
  `catalog/mechanics/close-combat.yaml`, `catalog/mechanics/execution.yaml`;
  Killing Blow, `weapon.shock-rod` and the extended L06 weapon guard). The
  Vomit/Spectral/Shifty seams and the L02–L05 guards are unchanged by that
  drift; the fresh runs below were executed against the live (drifted) revision
  and the entry copies were read for the captured revision. Post-drift hashes
  are in `entry/hashes-drift-after-review.sha256`.
- Scope limits: no full construction/semantic/parity/Web/CI suites were run, no
  finding was closed, no source/KB/test/doc was edited and no optimized or
  product certification is claimed.

## 2. Recommendation per delivery

| Lot | Recommendation | Reason |
| --- | --- | --- |
| **L02 Vomit Attack** | **Accept declared scope** (canonical compilation + modular replacement + explicit optimized refusal). No behaviour defect found. | The selected rule compiles a separate `vomit_attack` contribution; the normal weapon and the four base attacks survive; the modular policy replaces the whole normal pool with one automatic S5 armour-ignoring, unparryable attack and suppresses competing hand/extra/charge/Spawn allocation. |
| **L03 Spectral Touch** | **Accept declared scope**; one documentation-only correction (§3 F1). | Canonical Spirit Hosts receive `trait.spectral-touch` through the catalogue/shared construction/compiler without injection; per-hit natural-six provenance, R1–R4 extra wound, continuation, interruption and the Barrage prerequisite are the accepted ones; optimized entries refuse the unported effect. |
| **L04 Shifty** | **Accept declared scope** (four canonical Heroes + configured promoted Halflings via L05). | Elder/Cook/Thief/Youths select, compile once and execute; foreign profiles and unpromoted henchmen are refused; the pistol-only refusal is an explicit provisional execution boundary, not a tabletop prohibition, and no extra shot or fictitious fist is fabricated. |
| **L05 canonical choices** | **Accept declared scope**; one low-severity diagnostic defect (§3 F2). | Named tables separate membership/offering/compilation; promotions use conjunctive ID+type recipients; Runts count active positions separately from owned holstered items; complete kits distinguish unknown from explicitly empty; the Cleric exemption keeps the missile limit; markers and the single Iron Sinews route are truthful. |

## 3. Actionable findings

### F1 — README F056 reservation row contradicts the delivered L03 acceptance (documentation, low)

- **Source:** [README](../README.md) F056 row ("Delivered for independent
  review, not accepted by this planning revision") versus
  [remaining plan](T13-T15-remaining-plan.md#execution-scheduling-update--2026-10-02)
  ("F056 … accepted within delivered F008/L03, 2026-10-03"),
  [follow-ups](T13-execution-follow-ups.md#t13-f056--spectral-touch-pool-fixtures-cannot-distinguish-per-hit-provenance)
  ("resolved, bounded witness acceptance within L03") and
  [F056 §9](T13-spectral-touch-provenance.md#9-coordinator-acceptance-within-l03--2026-10-03)
  ("Accepted … reservation released"). The sibling L02–L05 rows in the same
  table were updated to "reservation released"; F056's was not.
- **Expected/observed:** one consistent status for F056. Observed: three
  records state acceptance inside L03 and the reservation table still says the
  opposite.
- **Impact:** traceability only; no behaviour, data or access consequence. It
  does not reopen F056.
- **Minimal check:** read the three cited records against the reservation row.
- **Owner:** coordinator (L03 closing / README reservation table).

### F2 — published special-skill refusals carry an empty `rule_id` and a `()` list name (diagnostic, low)

- **Source:** `profileSkillLists` in
  `packages/typescript/domain/eligibility/index.ts` maps each
  `profile.skill-access` binding to `{ rule_id: "", category, skills }`; the
  refusal branch of `skillIssue` then prints
  `… (${lists.map((list) => list.rule_id).join(", ")})`.
- **Expected/observed:** a refusal should name the published list that refuses
  the member, or omit the parenthetical when no list id exists. Observed: the
  message ends in `()` and the issue carries `rule_id: ""`.
- **Reproducer (executed):** `python -X utf8` calling
  `mordheim_construction.eligibility.call("skillIssue", profile, skill, True)`
  with `adventurers-kaz/elf` and `skill.hard-to-kill` returns
  `… is not on the published special-skill list of adventurers-kaz/elf ().`
  (member `skill.fey` returns `None`; an empty list set still returns the
  distinct `skill_pending_special_list`). Evidence:
  `entry/f2-skill-list-message.txt`.
- **Impact:** user-facing diagnostic quality and `rule_id` traceability of
  named-table refusals. Legality and compilation are unaffected (the five
  executable members compile once, and unsupported members raise the explicit
  `named skills have no executable duel mechanic` error).
- **Owner:** L05 named-table projection; not a new lot.

## 4. Known pendings left outside these deliveries

Reused from the register, not re-listed as defects: F009 optimized Spectral
Touch and F006 optimized Shifty (L19/L20), F005/F026 pistol-only allocation
(L08), F061 Halfling Crude Belch (T13.4/R4), F057 parity count and F001's 30
historical pins (L01/owners), F018's generic Protectorate access and F028's
unsupported item routes (L11 and the named L06–L17 owners), F025 Spirit Knife,
F040 coverage reconciliation, F023/L06 weapon mappings. L18 owns visible
product/backend routing for all four lots; T14 owns independent certification.

## 5. Checks executed versus evidence reused

**Executed in this review (live revision, isolated command lines, no writes):**

| Check | Result |
| --- | --- |
| `pytest test_vomit_attack.py test_spectral_touch_activation.py test_shifty_activation.py tests/python/construction/test_t13_canonical_choices.py -q` | **113 passed** |
| `pytest test_shifty_poison_transport.py -q` | **5 passed** |
| `pytest test_spectral_touch_provenance.py -q` | **6 passed** |
| `skillIssue` transport probe for the named-table message (F2) | Reproduced |
| KB/source reads: canonical Night Haint/Halflings/Snotlings/Outlaws/UA rules, both exact mirrors, `profile_types` conjunctive filters, `activeWeaponIssues`, `equipmentSetIssues` Cleric exemption, `require_optimized_support`, R4 Barrage predicate, L02 replacement/pool suppression, L04 nomination and fist cap, L05 markers and Iron Sinews route | No further discrepancy |
| Entry re-hash after the runs | Only the four concurrent L06 files drifted; delivery seams unchanged |

**Reused (not repeated):** L02 16 strict/868 affected/43 focal/70 dependency
cases and its 7-case spec with 4 mutations; L03 23 canonical/891 affected/24
dependency/34 TS cases and its 10-case spec with 4 mutations; L04 35
canonical/84 focal/926 affected and its 11-case spec with 3 mutations; L05 39
focused/958 affected/82 TS/56 catalogue cases and its 4-case spec with 1
mutation; the four full-verify identity sets (566/152 → 567/151 → 569/151 →
570/150 obligations with the same 30 inherited source errors).

## 6. Concurrent drift limiting a conclusion

Only the four files listed in §1 changed after entry, all inside concurrent L06
work; none of them alters the L02–L05 decision keys, tags, guards or seams, and
the 124 fresh cases pass on the drifted revision. No conclusion here depends on
a coherent pre-drift set beyond the entry copies retained in the evidence
directory.

## 7. Priority corrections

1. **F1** — update the README F056 reservation row to the delivered L03
   acceptance (documentation; coordinator).
2. **F2** — name the published list in the `skill_not_permitted` message (or
   drop the empty parenthetical) and stop emitting an empty `rule_id`
   (L05 named-table projection).

No medium- or high-severity defect was found inside the declared L02–L05 scope.

## 8. Post-review correction of F1/F2 — 2026-10-03

The coordinator applied both corrections after this report; the reviewed scope,
limits and per-lot recommendations above stand as written.

- **F1 fixed:** the README F056 reservation row now records acceptance within
  delivered F008/L03 on 2026-10-03 with the reservation released, matching the
  remaining plan and the follow-ups register. The surrounding F056 scheduling
  prose was already consistent; only the row contradicted the three records.
- **F2 fixed:** `profileSkillLists` now iterates `applicableRules` and carries
  each publishing rule's id instead of `""`. The generated bundle was rebuilt
  (`build:eligibility`/`check:eligibility` current) and the same reproducer
  returns `rule_id: 'band--elf-special-skills'` with the list named in the
  message. Post-fix evidence:
  `entry/f2-skill-list-message-after-fix.txt`.
- **Re-verification:** 101 Python construction cases (canonical choices,
  shared eligibility, context parity, blockers, campaign obligations) and 53
  TypeScript cases (canonical choices, campaign blockers, shared-eligibility
  reconciliation, shared eligibility) pass, plus the `campaign-web-core`
  typecheck. Member control (`skill.fey` → `None`) and the pending-list code
  (`skill_pending_special_list`) are unchanged. No finding ID was added and no
  L02–L05 behavior was modified.
