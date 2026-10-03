# T13-F056 — Spectral Touch mixed-hit provenance witnesses

Delivered for independent review on 2026-10-02. This lot converts the F1
finding's mixed-provenance observation into maintained strict regressions on
the real modular pool. **F056 is not accepted or closed here**, F007 is not
reopened and no canonical activation, optimized port or T13.4 certification is
claimed.

## 1. Contract, scope and references

The accepted contract under test is the permanent ruling
[Spectral Touch Q019](../../../decisions/design-rulings.md#spectral-touch-q019),
specifically: a successful final natural hit six establishes one immediate
extra wound (R1), and "each new hit has its own natural-die provenance". The
pool convention (contract item 7) prepares all hit dice and resolves collective
defences before processing each surviving hit's extra and ordinary
contributions in attack order.

Supporting reviewed evidence:

- [Independent implementation review](T13-spectral-touch-independent-review.md):
  F1 (the maintained suite cannot distinguish per-hit from whole-pool
  provenance) and its proposed witness; §13 records the coordinator acceptance
  and the F056 boundary.
- [Spectral Touch delivery](T13-spectral-touch.md): the implemented modular
  contract, `AttackOutcome.natural_hit_six` provenance transport and the
  accepted R4 Barrage repair.
- [Execution follow-ups](T13-execution-follow-ups.md): the F056 entry and its
  close criterion ("the maintained witness passes on the actual engine, fails
  under the isolated pooled-provenance mutant, fully consumes its exact
  dice/decisions and does not alter production inputs").
- Verification system: [implement and verify rules](../../../guides/implement-and-verify-rules.md)
  (strict dice/decisions, mutation detected by behaviour) and
  [verification](../../../reference/verification.md) (L1 deterministic per-rule
  evidence; a survivor/detector gap is answered with a deterministic test).
- Read-only prior evidence: the F007 review's
  [`probe.py`](../../../../build/cache/t13-parallel/spectral-touch-independent-review/probe.py)
  (`mixed_pool_provenance`), its `mutant_plugin.py` pooled mutant and the
  coordinator's
  [`check.py`](../../../../build/cache/t13-parallel/spectral-touch-coordinator-acceptance/check.py).
  Those files were read, never executed or overwritten, and their observations
  were converted into maintained assertions rather than copied.

**Scope limits.** Only the two-hit mixed pool with hit faces 6/5 and 5/6 and
failed ordinary wounds is covered. Barrage continuation, saves, injury and
reaction paths already have maintained cases in
[`test_spectral_touch.py`](../../../../tests/python/combat/modular/test_spectral_touch.py);
this lot adds the missing per-hit-provenance detector and does not re-certify
the rest of the contract.

## 2. Added cases and the errors they distinguish

One new file:
[`test_spectral_touch_provenance.py`](../../../../tests/python/combat/modular/test_spectral_touch_provenance.py)
(6 strict cases). Each runs the real `_resolve_attack_pool` with explicit
synthetic `CompiledFighter` inputs, the maintained `initialize_fighter` helper
and fully strict `StrictDice`/`StrictDecisions` tapes; both tapes are finished,
so any unexpected, missing or reordered request fails.

| Case | Composition | Distinguishes |
| --- | --- | --- |
| `test_mixed_successful_hits_keep_per_hit_natural_six_provenance[6-5]` / `[5-6]` | Spectral tag; hits 6 and 5, both successful; both ordinary wounds fail | Only the hit whose own die is six adds the extra wound: damages `[1, 0]` for 6/5 and `[0, 1]` for 5/6; defender ends at 3 wounds |
| `test_mixed_hits_without_spectral_touch_add_no_extra_wound[6-5]` / `[5-6]` | Same faces without the trait | Both hits still land, damages `[0, 0]`, defender keeps 4 wounds, no Spectral roll appears |
| `test_pooled_provenance_mutant_is_rejected_by_the_mixed_witness[6-5]` / `[5-6]` | Maintained witness first on the real engine, then under the isolated pooled mutant | The witness passes unmutated and rejects the mutant with a semantic assertion |

Every case asserts: the collective hit-preparation order (both `…attack.N.hit`
requests before any `…attack.N.wound` request), the exact ordered request tape,
the outcome count and per-hit order via `hit_roll`, per-hit damages, the final
defender wounds, the absence of unexpected decisions and the absence of any
`spectral-touch` roll key. The mixed cases never rely on the total wounds
alone; the per-hit damage list is the primary discriminator.

## 3. Synthetic fixture construction and provenance

The file does **not** call `compile_fighter` or any construction helper. At
delivery time, concurrent warrior-construction centralization was changing that
frontier; the [shared eligibility reference](../../../reference/eligibility.md)
now describes the completed migration. It builds two explicit `CompiledFighter`
values locally:

- profile shape `Characteristics(3, 3, 3, 4, 3, 1)` — WS3/S3/T3/W4/I3/A1,
  mirroring the F007 review probe;
- main `weapon.axe`, no off hand, no extra attacks, a `weapon.fist` unarmed
  fallback;
- the attacker carries the pilot `trait.spectral-touch` tag; canonical Spirit
  Host activation is F008 and is not claimed;
- no armour (save 7), no natural save, no ward/regeneration, no parry capacity
  and no reaction traits, so no die can hide the difference;
- hit faces 6/5 both beat the WS3-vs-WS3 target of 4; both ordinary wound rolls
  are 1, which always fails S3 vs T3 (needs 4); the extra contribution is
  dice-free by the accepted contract (review B7).

**These inputs test engine composition, not legality.** They do not show that a
Spirit Host can acquire the weapon or the trait through the product.

## 4. Entry, concurrent drift and separation

Entry capture (branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`,
dirty tree) and SHA256 of every input actually used are recorded in
[`entry.json`](../../../../build/cache/t13-parallel/spectral-touch-provenance/entry.json),
produced by the reproducible
[`capture_entry.py`](../../../../build/cache/t13-parallel/spectral-touch-provenance/capture_entry.py).
Re-running never overwrites a previous capture: the old `entry.json` is moved
to `entry-<UTC stamp>.json`.

The reviewed engine hashes match the F007 review inputs
(`pools.py 567a9636…`, `attacks.py 55e05e32…`), so the reviewed behavior was
re-exercised unchanged. The concurrent centralization work is confined to
construction modules and its plan document; none of its files is touched, and
any drift there is neither attributed to F056 nor used to demand a freeze.

Separation is enforced by construction: no production file, no existing test,
no KB source, no specification and no shared document was modified. The only
writes are the two authorized new files plus this evidence directory.

## 5. Commands, results and exit codes

All commands run from the repository root with `python -X utf8`; logs and JUnit
XML are retained in `build/cache/t13-parallel/spectral-touch-provenance/`.

| Command | Exit | Result |
| --- | --- | --- |
| `python -X utf8 -m pytest tests/python/combat/modular/test_spectral_touch_provenance.py -q -p no:cacheprovider --junitxml=…/new-suite.xml` | 0 | **6 passed** in 0.14s (`new-suite.log`) |
| `python -X utf8 -m pytest tests/python/combat/modular/test_spectral_touch_provenance.py tests/python/combat/modular/test_spectral_touch.py tests/python/combat/modular/test_shifty.py tests/python/combat/modular/test_shifty_poison_transport.py -q -p no:cacheprovider --junitxml=…/focal.xml` | 0 | **112 passed** in 12.76s = 6 new + 57 Spectral + 44 Shifty + 5 F060 (`focal.log`), no failures/errors/skips |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q -p no:cacheprovider` | 0 | **1 passed** in 0.08s, run after the last documentation edit (`documentation.log`) |

An earlier post-documentation run exposed one broken relative link in this
file (the guides/reference links needed one more `../`); it was fixed and the
check re-run green.

Per-module counts were read back from the retained XML, not assumed. No
coverage update, pin refresh, global generator, construction, TypeScript, port
or T14 command was run: none is a concrete dependency of this test-only lot.

## 6. Mutant and the assertions that detect it

[`mutations.py`](../../../../build/cache/t13-parallel/spectral-touch-provenance/mutations.py)
runs every maintained witness in a dedicated process with the engine's per-hit
provenance replaced in memory (a compiled in-memory copy of `pools.py`, the same
substitution pattern the new test file uses), then restores the module
attribute. No live engine file is edited and no new mutation framework is
introduced. Results are in `mutations.json` / `mutations.log`; the script exits
1 if the baseline fails or a mutation survives.

| Mutation | Injected fault | Detected by | Failing maintained assertion |
| --- | --- | --- | --- |
| M1 `pooled` | every prepared hit shares `any(prepared_hit.natural_hit_six)` | both mixed witnesses | `per-hit damages [1, 1] != [1, 0]` at test line 108 |
| M2 `suppressed` | per-hit provenance is suppressed entirely | both mixed witnesses | `per-hit damages [0, 0] != [1, 0]` at test line 108 |

Both are detected by the semantic per-hit damage assertion, not by an import
error, `TypeError` or preparation failure; the maintained in-file mutant test
additionally asserts the failure message contains the damage list, so the
detection cannot silently move to an unrelated failure. No real defect was
found; no engine repair was needed or performed.

## 7. Limits and pendings

- **Canonical activation remains open (F008).** The trait is injected, not
  granted; `spirit-hosts--spectral-touch` still does not reach the production
  consumer. Owner: F008 route; include this witness before accepting that lot;
  close per that entry.
- **Optimized backends remain open (F009).** NumPy/native were not executed and
  no optimized Spectral Touch support is claimed. Owner: F009; resume after
  F008; close when matching hit provenance is proved per backend.
- **Barrage/resource composition** retains its own maintained cases; this lot
  does not extend them and does not reopen the accepted R4 repair.
- **Centralization drift.** If the concurrent agent changes `pools.py`,
  `attacks.py`, `phases.py` or the strict dice helpers, re-run the new suite
  and re-capture `entry.json`; only the affected subset needs revalidation.
  This lot intentionally does not depend on the compiler.

**Reproducer for the whole lot:** run the three commands in §5 from the
repository root; all three must exit 0. For the mutation proof run
`python -X utf8 build/cache/t13-parallel/spectral-touch-provenance/mutations.py`
and confirm `all_mutations_detected: true` with exit 0.

## 8. Review handoff

Delivered for independent review. Acceptance/closure of F056 belongs to the
coordinator after verifying this document, the new suite and the retained
evidence. The test file's SHA256 is recorded in `entry.json`; re-run
`capture_entry.py` to confirm the reviewed revision. No production input or
existing test changed.

## 9. Coordinator acceptance within L03 — 2026-10-03

**Accepted for F056's maintained mixed-hit witness; reservation released.** The
delivered test bytes match the coordinator's immutable L03 entry hash. Six fresh
maintained cases pass at the current revision, including the two in-memory
pooled-mutant detection cases. L02's narrow optional-Vomit pool integration has
changed `pools.py` since the external entry; this acceptance uses fresh execution
and preserves the accepted Spectral resolution code, rather than reusing the old
pool hash as current evidence.

The coordinator independently authored source-linked **canonical** Spirit Host
A3 cases with faces 6/5/1 and 5/6/1. Both pass normally. Running the delivered
in-memory pooled mutant against those cases fails specifically at the incorrectly
added per-hit damage (`got 1, expected 0`) in both orders. This confirms the
discriminator beyond the external synthetic two-hit helper. The maintained
external test and its pre-acceptance document body are otherwise preserved.

Full L03 verification and the public modular request now prove F008 canonical
activation; the historical pending statements in sections 1–8 describe this
external lot's entry, not the final canonical state. F009 optimized ports remain
pending and are explicitly refused; no optimized/T14/GUI certificate is implied.
No new source ruling, engine repair, standalone review assignment, agent launch,
commit or push accompanied this acceptance.

Reproduce with the unchanged
`tests/python/combat/modular/test_spectral_touch_provenance.py` and the new
[canonical tests](../../../../tests/python/combat/modular/test_spectral_touch_activation.py).
Independent replay and protected-byte checks are retained in
`build/cache/t13-parallel/spectral-touch-activation/f056-independent-review.json`
and `delivery-review.json`; the [L03 delivery](T13-spectral-touch.md#l03-canonical-activation--2026-10-03)
records scope, commands and remaining owners.
