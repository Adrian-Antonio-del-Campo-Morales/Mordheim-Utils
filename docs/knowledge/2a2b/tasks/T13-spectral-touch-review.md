# T13.3a — Spectral Touch / Q019 semantic review dossier

> Current ownership — 2026-10-02. The [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) is already implemented for both products. Pilot combat tests below prove the modular mechanism at their reviewed revision; injected tags do not establish canonical legal selection or activation. After the required source decisions, reuse shared eligibility for legal access and separately prove KB binding/compiler activation before optimized ports. Historical results and later acceptance sections retain their own stated limits.

Historical dossier prepared for human review on 2026-10-01. The user subsequently
accepted R1–R4; the [modular Barrage repair](T13-spectral-touch.md#accepted-r4-modular-repair--2026-10-01)
is now implemented and verified, with F007 awaiting independent implementation
review. Tables and pre-repair results below retain the examined entry behavior;
they are not the current Barrage contract. No canonical activation or port is certified.
Spirit Knife / Q146 is a separate obligation, not a beneficiary of this review.

## Examined entry and coordination

- Workspace: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`.
- Branch `2A2B`; HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`;
  local tracking status was ahead of `origin/2A2B` by one commit. No fetch was
  made, so this is local tracking information, not live remote synchronization.
- Entry captured at `2026-10-01T08:13:18.639611+00:00`. The tree contains
  concurrent user and T13 changes; HEAD alone is not the tested revision.
- Own evidence directory: `build/cache/t13-parallel/spectral-touch-review/`.
  `entry.json` contains environment, worktrees, status and 247 input SHA256s;
  `entry.diff` and `entry-staged.diff` preserve the tracked incoming differences.
  Untracked relevant inputs are identified by hash, not assumed to exist at HEAD.
- No applicable `AGENTS.md` was found in the workspace or its ancestor
  directories. The initiative coordination protocol and the user's explicit
  write boundary govern this lot.
- External A / R0 already owns source/reference/fingerprint evidence;
  external B / R2 already owns hireling/Dramatis Personae/Mazzalupo traceability
  and its construction test. Their reservations remain in the initiative
  README. Neither was launched, contacted, accepted or edited by this review.
- Shifty shares `pools.py`; its 44 tests were rerun. F003–F006 and the
  F005/F026 pistol-allocation dependency remain separate. No Shifty semantic
  review, canonical promotion or port was started.
- Shared TypeScript eligibility and the embedded Python bundle remain the
  current architecture. This review introduces no Python decision tables.
  The planning-time 211-test result has no matching input-hash manifest located
  for this review, so it is **not reused as current certification**. F035 stays
  open; no broad construction/extraction suite was repeated.

Critical input identities (complete values are intentionally retained):

| Input | SHA256 |
| --- | --- |
| `modular/attacks.py` | `95073dc56cdc1bbcca0abed8576ac474ff6d7ff02fc05839442ed69147d78b82` |
| `modular/state.py` | `69b7c2934fdcd53039a8e7ac64bfdff0f4c056ae851ee900afe14c79916c76aa` |
| `modular/pools.py` | `567a9636f7ac652d404c3c6cc09e6fb3748249dd5b6ee855005c30a25f669a0a` |
| `test_spectral_touch.py` | `87fb357a0f80c3827d185c8ba3f72e3fec069b534ec20058dc1ab485f84822eb` |
| `test_shifty.py` | `09b32382bbdf127c4493bd96f06ff3fa1b155df15b06d7767aa0377d07963f9c` |

The first four hashes match `spectral-touch/delivery.json`; the Spectral Touch
and Shifty delivery documents match too. Coordination documents have since
changed. `historical-comparison.json` records each comparison. This supports
reuse of the unchanged mechanism identity, not of the entire historical
397-test result against today's compiler/eligibility tree.

## Authorities and source locators

Original PDFs were consulted through web extraction and downloaded into this
lot's evidence directory. `sources.json` records URL, size and SHA256; selected
page text is retained in `*-selected.txt`. Night Haint web screenshots failed;
the original PDF text was independently extracted locally with pypdf. There is
no reliance on a secondary transcription for its operative sentence.

| Key | Authority and locator |
| --- | --- |
| N | [Call of the Night Haint](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf), PDF page 5 / printed 082, Spirit Hosts / Spectral Touch; PDF page 3 / printed 080, Spirit Knife; PDF page 1 / printed 078, Ethereal. |
| C | [Mordheim Part 1](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf), printed 5, rerolls; 16, armour/criticals; 17, injuries/removal; 19, hit/wound; 20–21, armour/parry/disabled opponents. PDF page numbers match those printed core-rule numbers. |
| L | [Rules Review / Errata](https://broheim.net/downloads/rules/Errata.pdf), PDF page 2, amendment headed Page 53 / Lucky Charm. |
| B | [Letters of the Damned 2](https://broheim.net/downloads/lod/LOD2.pdf), PDF/printed page 6, Estalian Diestro / Rapier / Barrage. |
| D | [Permanent design rulings](../../../decisions/design-rulings.md), Duel engine: automatic WS0, basic critical table, immediate Force of Will, synthetic hits, poison timing, equipment projection and Luck. These are project authority, not Night Haint quotations. |
| P | [Proposed Q019 contract](T13-spectral-touch.md#proposed-q019-contract-fixed-before-implementation), seven items; [contracts](T13-contracts.md), [implementation plan](T13-implementation-plan.md), [procedure](../../../guides/implement-and-verify-rules.md). |

**Explicit source content:** N ties the effect to a hit-roll six, prescribes an
immediate additional wound and retains the ordinary wound roll. The Spirit Host
sentence duplicates “wound”; the parallel Spirit Knife wording clarifies the
single contribution. Neither passage supplies a defensive-order algorithm,
Strength attribution or reaction/port contract. Its heart imagery is not an
operative immunity clause. N's Ethereal save is taken after the hit roll, so a
generic ward fixture cannot stand in for every printed special-save rule.

**Applicable general content:** C makes a reroll's second result binding;
armour is available per wound with Strength modifiers; criticals depend on
wound rolls; injuries use the highest relevant result and removal follows OOA.
C's ordinary parry cannot beat six and collective parry targets the highest
hit. A warrior cannot use its own knockdown/stun to finish the same opponent
automatically in that combat phase. L discards the first hit on a successful
Charm check. B grants another attack after hitting but failing to wound.

The canonical origin is
`sources/2B/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml#spirit-hosts--spectral-touch#trait.spectral-touch`.
The Q019 ledger row names the canonical rule in
`sources/knowledge/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml`;
its reviewed-text hash is
`4a738d269815cdb6218bbce31316686572b98944c046e5b3f3bc52323f1d08fb`.
The Q146 row instead targets `weapons-close-combat.yaml#spirit_knife` and
retains its own recipient, weapon and activation requirements.

## Decision table

“Recommend” below is advice for the human reviewer, never an accepted ruling.
References to source silence mean no specific composition instruction was found
in N; the general authorities above remain applicable.

| Point | Authority / evidence distinction | Current project proposal | Relevant alternative | Observable consequence and recommendation |
| --- | --- | --- | --- | --- |
| 1. Final natural six | N trigger; C reroll; D automatic-hit boundary. “Natural” is the project's reading of the die, not an extra adjective printed in N. | A successful final physical six qualifies; reroll six qualifies. Modified five, Sweep test, automatic hit and manufactured Mark success do not. | Treat displayed replacement success as six. | Would wrongly add damage without a qualifying die. Recommend the current provenance contract; no remaining source question identified here. |
| 2. Charm / ordinary and exceptional parry | L and C define discarded-hit behavior; N has no defense bypass. Exceptional-six permission is an existing engine seam, not a newly certified canonical defensive rule. | Resolve the original hit's defenses once; a discarded/parried hit has no extra contribution. | Extra damage before hit cancellation, or defend the extra as a fresh hit. | Would bypass cancellation or duplicate resources. Recommend current behavior; do not certify the synthetic Sword Master loadout. |
| 3. Extra versus ordinary wound | N explicitly preserves the ordinary contribution. | Extra bypasses Toughness/wound dice; resolve it before ordinary wound dice. A failed ordinary roll leaves extra damage intact. | Replace the ordinary wound, or require a second wound test for the extra. | Would erase or delay the printed contribution. Recommend current behavior, subject to the removal barrier in point 6. |
| 4. Saves, modifiers and order | C supplies general armour; N does not expressly identify the extra's attack modifiers. D/P supply the proposed composition. | Independent eligible armour then special saves; inherit actual attack Strength/penetration/magic/injury context. | A neutral direct wound with only applicable victim defenses; or an unsaveable wound. | Synthetic S4 dagger case changes armour threshold from a neutral treatment. Recommend armour by default, reject unsaveability without an exception; **R1** must settle inherited modifiers and retain source-specific save timing. |
| 5. Multiple damage / criticals / cap | N single contribution; C critical trigger; D basic-table contract. Fire multiplication versus the explicit contribution is a precedence interpretation. | Extra is exactly one before saves, no damage die/critical capacity; an ordinary critical affects only ordinary damage. Fire/flammability does not double the extra. | Let generic damage multipliers increase the extra. | Current critical case totals three; synthetic flammable/fire extra remains one. Recommend the current cap as the narrower reading; include cap precedence in **R1**. |
| 6. Injury, removal, rescue, reactions | C injuries/removal; D immediate Force of Will and once-per-wound reactions. N does not settle reactive removal of the attacker before continuation. | Apply extra injury and immediate reactions/rescue; continue if both remain active, stop if either is OUT. | Complete the already-landed ordinary hit before resolving reactive attacker removal. | Acid Blood can remove a one-Wound attacker and suppress `a.wound`; successful rescue retains continuation and spent resources. Recommend current immediate sequencing; **R2** requires explicit human scope. |
| 7. Newly knocked-down/stunned defender | C forbids the same warrior's automatic same-phase finishing; N keeps ordinary continuation. | Still roll ordinary wound and any required injury; no new finisher from extra injury. | Use the newly disabled state to auto-remove. | Wound roll 1 leaves the defender stunned; a later successful wound still requests injury. Recommend current behavior; not a remaining semantic choice. |
| 8. Prepared pool / ordering | C collective highest-hit parry; P batch convention. N's immediacy and intervening reactive state do not specify an algorithm. | Prepare all hits, resolve Charm/collective parry, then extra plus ordinary for each surviving hit in attack order. | Resolve each extra before preparing later hits/defenses. | Even a lethal first extra has later hit dice already drawn. Earlier wounds can interact differently with later parry resources/counters. Recommend retaining collective preparation but explicitly limit “immediate” to after collective hit defenses; **R3**. |
| 9. Multiple attacks / Barrage | N has a per-attack trigger, no once-per-phase limit; B is a separate source. Their composition is unstated. | Each new six qualifies. Barrage tests failure of the ordinary wound roll, even when the extra wounded. | Permit Barrage only when the whole attack failed to establish any wound, including the extra. | Reproducer totals two versus one; the saved-extra variant also needs a wound-versus-unsaved-damage definition. **R4:** recommend withholding Barrage after an established extra wound, saved or not, to respect its whole-attack prerequisite. This would require a future correction if accepted; current tests encode the other interpretation. |

## Cases, independent expectations and existing tests

Except the final canonical loading check, these use isolated pending tags or
synthetic compositions. They do not establish a legal Spirit Host equipment or
skill combination. Prefix `a` is a direct attack; `p.attack.N` is a prepared pool.
All omitted requests and decisions are forbidden, not randomly supplied.

| Case / authority | Ordered dice and decisions | Expected consequence / test mapping |
| --- | --- | --- |
| Six and continued miss — N | `a.hit=6`, `a.wound=1`; no decisions | W4 becomes W3, damage 1. `test_trigger_and_failed_ordinary_wound`. Five or absent tag: W4 unchanged. |
| Reroll / automatic — N+C+D | `a.hit=1`, `a.hit.reroll=6`, `a.wound=1`; automatic case only `a.wound=1` | Extra only for final physical six. `test_final_natural_reroll_six_qualifies`, `test_automatic_hit_has_no_natural_six`, modifier/Sweep/Mark tests. |
| Original-hit cancellation — L+C | `a.hit=6`, `a.lucky-charm=6`; exceptional fixture `a.hit=6`, `a.parry=6` | No wound requests; Charm consumed once or hit parried. `test_lucky_charm_discards_original_hit_and_extra`, `test_exceptional_parry_discards_spectral_hit`; isolated pool parry also reproduced. |
| Two saves — C plus proposed R1 | `a.hit=6`, extra armour 6, `a.wound=4`, ordinary armour 1 | Only ordinary contribution damages. `test_each_contribution_has_own_armour_save`; ward/regeneration parameter cases cover generic separate saves, not every printed defensive trigger. |
| Critical separation — N+C | `a.hit=6`, `a.wound=6`, `a.critical=3` | Damage 3, one critical capacity spent. `test_ordinary_critical_does_not_double_extra`; damage-die/fire cap and retroactive-armour-denial tests cover proposed R1 limits. |
| Immediate removal — C+D plus R2 | W1 defender: `a.hit=6`, extra injury 6 | OUT; no ordinary wound request. Acid Blood variant adds extra acid wound 4; exactly one reaction. `test_extra_removal_stops_ordinary_and_reacts_once`. |
| Rescue / attacker removal — D plus R2 | Extra injury 6, rescue 1, then ordinary wound 1; failed rescue 6 ends. Reactive attacker-removal fixture requests acid wound 4 and acid injury 6. | Rescue spends Force of Will; restored defender continues. Removed attacker stops. `test_rescue_is_immediate_before_ordinary_wound`, `test_extra_acid_blood_removing_attacker_cancels_ordinary`. |
| Disabled continuation — C+N | W1 defender: hit 6, extra injury 3, ordinary wound 1; successful variant ordinary wound 4, ordinary injury 1 | Stunned remains stunned; no automatic finisher. `test_extra_knockdown_or_stun_does_not_auto_finish_continuation`, `test_stun_then_successful_ordinary_wound_still_rolls_injury`. |
| Repetition / removal — N plus R3 | Two prepared hits 6,6, then ordinary wound 1,1; lethal variant first extra injury 6 | W4 becomes W2; lethal variant stops wound execution after first outcome while both hits were drawn. `test_repeated_pool_sixes_each_add_one_wound_after_hit_preparation`, `test_pool_lethal_extra_cancels_later_prepared_hit_wounds`. |
| Barrage ambiguity — B+N plus R4 | `r.hit=6`, extra armour 1, `r.wound=1`; accept `r.barrage`; next hit 5, wound 4, armour 1 | Current result: damage 2 / W2. Recommended whole-attack reading: damage 1 / W3, no Barrage request. `reproducer.py`; permanent Barrage tests currently support ordinary-roll-only reading. |
| Production boundary — current loader/compiler | Compile canonical `call-of-the-night-haint-mim` / `spirit-hosts` normally | No active spectral tag. Injection alone proves modular consumer; public replay also executes actual round/pool path. `test_real_spirit_host_is_pending_without_fixture_and_runs_with_pending_tag`, `test_pending_spirit_host_tag_reaches_actual_modular_duel_driver`. |

## Implementation trace and findings

Paths below are relative to `packages/python/combat-engine/mordheim_combat/`
unless explicitly identified otherwise; line numbers refer to the hashed entry.

- `phases.py:275` retains the final physical hit roll; automatic hits use zero.
  `modular/attacks.py:126–136` records provenance before Mark changes success.
  `modular/state.py:76–91` holds the prepared outcome flag.
- `modular/pools.py:69–149,225–242` prepares hits and collective defenses.
  Its normal and declined-Bear-Hug branches transport `natural_hit_six` at
  lines 280, 304 and 331. Selected whole-hit replacements have their own
  semantics; they are not implicitly certified Spectral Touch compositions.
- `modular/attacks.py:199–218` calls the common wound tail with
  `single_wound=True`, applies `_react_to_wound` immediately, and stops inactive
  participants. Ordinary processing follows at lines 226–305.
  `modular/attacks.py:308–407` handles saves, damage and injury for both paths.
- `modular/attacks.py:38–65` aggregates secondary damage, tracks already-reacted
  damage and resets hit provenance for each Barrage attack.
  `modular/aftermath.py:21–61` performs immediate rescue and reacts only to the
  unreacted damage. Tests demonstrate no duplicate Charm, Kusara suppression,
  critical capacity, Luck or Acid Blood processing in their covered cases.
- Production rounds use `_resolve_attack_pool`; the public modular duel replay
  exercises that route. Direct scenario adapters also call the attack resolver.
  Other real callers include cutlass counterattacks, infection, acid blood,
  fire, spines, Black Hunger and entanglement. Automatic synthetic hits do not
  create a six; fire explicitly neutralizes offensive globals. This is caller
  inspection, not a new certificate for every reaction composition.
- `StrictDice` verifies key, die size, value, order and full consumption;
  `StrictDecisions` verifies key, Boolean values and consumption. Both isolated
  mutations execute altered source in a separate namespace and monkeypatch
  only the test process: removing the trigger fails the damage expectation;
  suppressing continuation fails strict request consumption. Both were detected
  in the focused run; no shared source was temporarily edited.

**No source-unambiguous engine defect was reproduced in the checked contract.**
The Barrage behavior is a demonstrated semantic disagreement between candidate
readings, not an accepted defect. If R4's recommendation is adopted, route a
narrow correction of the Barrage predicate in `modular/attacks.py` and update
its strict fixtures in a separately reserved lot. Preserve accumulated damage,
reaction accounting and new-hit provenance; do not disable ordinary continuation.

Evidence/documentation gaps retained for follow-up:

1. The vocabulary registry already declares `trait.spectral-touch` as promoted;
   `TRAIT_TYPES`/production granting still lack activation and the canonical rule
   remains `implemented: NO`. Historical wording “not registered” must distinguish
   these two facts. This is documentation precision under F008, not authorization
   to change registry/compiler/YAML here.
2. Generic ward/regeneration and exceptional parry fixtures prove mechanics,
   not source-specific legal recipients or complete defensive timing. Hit-based
   defenses such as N's Ethereal require their own source-linked composition.
3. The focused file does not prove a changed reactive-defense/counter ordering
   under R3, selected Bear Hug replacement composition, or every attack caller.
   Add only the cases made necessary by the eventual ruling; green fixtures do
   not fill these gaps.
4. No executable source-linked Spectral Touch production specification was
   located in `tests/specs/semantic`. Q019/Q146 remain ledger questions.
   Normal Spirit Host compilation remains pending, as tested. NumPy/native
   Spectral Touch are not exercised or certified here.

## Commands, results and verification boundaries

Run from the workspace root with Python 3.10. Tests disabled bytecode and pytest
cache writes for this lot. The XML files are real pytest output.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest tests/python/combat/modular/test_spectral_touch.py tests/python/combat/modular/test_shifty.py -q -p no:cacheprovider --tb=short --junitxml=build/cache/t13-parallel/spectral-touch-review/focused.xml
python -X utf8 build/cache/t13-parallel/spectral-touch-review/reproducer.py
python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q -p no:cacheprovider --junitxml=build/cache/t13-parallel/spectral-touch-review/documentation.xml
```

- Focused run: **93 passed** (49 Spectral Touch, 44 Shifty), no failures/errors/
  skips, exit 0, 14.23 seconds. `focused.log`, `focused.exitcode.txt`, `focused.xml`.
- Isolated reproducer: exit 0; exact dice/decision and results in
  `reproducer.json` and `.log`. Also confirms exceptional-six cancellation
  through collective pool defenses without wound requests.
- Documentation check and final input-preservation result are recorded in
  `final.json` after dossier completion. No wider suite was justified by a code
  change because this lot changes no production code.
- Download initially failed with sandbox socket denial; the approved retry
  retained four originals. PDF extraction is evidence, not semantic acceptance.
- No 211-test construction reuse, full eligibility-extraction certificate,
  complete semantic gate, source repinning, native rebuild, parity/coverage
  advancement, statistical run, UI test, commit or push is claimed.

## Human decision package and next barrier

The following four choices remain after consulting the sources. Decide each
independently; approval of this dossier's usefulness is not approval of Q019.

| ID | Human question | Recommendation / scope |
| --- | --- | --- |
| R1 | Does the extra inherit this attack's save/injury modifiers and eligible defenses, while remaining capped at one despite generic damage multipliers? | Yes, with printed defense timing respected. Generic per-wound ward fixtures cannot relocate a printed after-hit save. Does not certify every equipment combination. |
| R2 | Are injury, rescue and reactions resolved before the ordinary contribution, stopping it when either participant remains removed? | Yes; explicitly include reactive attacker removal. Rescue allows ordinary continuation with current resources. |
| R3 | Does “immediate” mean after all pool hits and collective hit defenses are prepared, before this hit's ordinary wound roll? | Yes; record this batch boundary explicitly. Alternative sequential preparation requires shared-pool design and regression review. |
| R4 | Does a successful extra wound prevent Barrage even if the ordinary wound roll fails, including when the extra is saved? | Recommend yes: evaluate failure to establish a wound for the whole attack, not unsaved damage. Current proposal is no. A yes answer creates a repair requirement; no repair is authorized by this dossier. |

F007 and Q019 remain **in review**, pending recorded human decisions and any
required repairs/review. F008 and F009 remain **blocked** pending canonical
grant/specifications and actual optimized execution. F035 remains **open**.
F003–F006 remain unchanged. No source ledger or permanent ruling was edited.

After the human response, record its precise scope in the authorized
coordination documents and reserve the necessary future repair/specification
work. Do not close Q019/F007 on this dossier alone. Canonical activation requires
the reviewed recipient/grant path, source-linked cases and independently
reviewed data; optimized ports require the stabilized accepted contract.
The next requested dossier is Shifty; it has not been started.

## Subsequent disposition — accepted semantics and modular repair

The user accepted all four recommendations on 2026-10-01 (“las acepto todas”).
The accepted scope is recorded in the [permanent Q019 ruling](../../../decisions/design-rulings.md#spectral-touch-q019).
The subsequent user request to execute the coordinator's next task authorized
the narrow R4 repair. Its changed predicate now rejects saved/unsaved established
extra wounds before offering Barrage; real attack/pool/public replay witnesses
and isolated prerequisite mutations are in the [delivery](T13-spectral-touch.md#accepted-r4-modular-repair--2026-10-01).
The historical reproducer and 93 passes above describe the earlier proposal.
F007 remains in review for the implementation, F008/F009 retain their separate
canonical/optimized barriers, and Shifty decisions are not accepted by this lot.
