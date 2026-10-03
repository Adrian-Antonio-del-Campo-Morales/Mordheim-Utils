# T13.1 — Local simulation contracts and real-engine replay

> Current ownership — 2026-10-02. Read the [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) before resuming this lot. Shared eligibility already decides legal choices for both products; Python still compiles characteristic bonuses and combat effects and carries local simulation context. The accepted contracts and recorded evidence below retain that bounded scope. They neither duplicate eligibility nor certify every legal choice's battle behavior.

This lot implements the shared foundation in the [T13 plan](T13-implementation-plan.md).
[T13.0](T13-inventory.md) and its [origin register](T13-obligations.csv) remain the source/scope authority.
The [initiative README](../README.md) owns reservations and phase status.

## Entry and boundaries

Entry: `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, branch `2A2B`, clean checkout.
The user's previous UI/language work is included in that fixed entry. This lot edits no
KB/source, campaign application, Combat Lab UI, language asset or semantic fingerprint.
No rule binding or implementation mark is promoted by these foundation tests.

Combat Lab participants are configured local simulation instances. Their IDs never
identify a campaign member. Two instances may share the same canonical `fighter_id`.
There is no campaign import/service, `member_ids`, `battle_number`, or roster event.

## Consultation

Implementation follows [Implement and verify rules](../../../guides/implement-and-verify-rules.md):
reuse the responsible layers, share context preparation, inject dice and decisions,
and exercise real operators. [Verification](../../../reference/verification.md)
distinguishes deterministic evidence from statistical/whole-phase certification.
Existing combat timing/critical/reaction rulings in
[Design rulings](../../../decisions/design-rulings.md) remain applicable.

The local facts are motivated by included clauses, rather than campaign fields:

- Canonical [Mercenary profiles](../../../../sources/knowledge/bands/mordheim/mercenaries/profiles.yaml)
  retain Movement and Leadership (the captain has M4/Ld8).
- [Clan Pristekk rules](../../../../sources/knowledge/bands/mordheim/skaven-of-clan-pristekk-sc/special-rules.yaml)
  require handler Leadership and a supplied 6-inch relationship.
- [Underworld Alliance rules](../../../../sources/knowledge/bands/mordheim/underworld-alliance-mim/special-rules.yaml)
  contain nearby Boglar/engagement facts and local explosion recipients within 2 inches.

These references justify inputs. Their proximity/psychology/explosion mechanisms are
not implemented or certified here. T13.0 source questions, including the unreliable
condition summaries and Spectral Touch ordering, continue to gate dependent clauses.

## Characteristics and compilation

`Characteristics` preserves its original six positional combat statistics. Optional
keyword-only `movement` and `leadership` store nonnegative integers; `None` means
unknown. Boolean and fractional inputs are rejected. No racial cap or arbitrary
replacement value is invented. An operator requiring an unknown fact must reject it
through `PreparedDuelContext.characteristic`, rather than using zero.

Profile compilation keeps numeric canonical M/Ld. A supplied six-stat advance inherits
those two facts; explicit M/Ld overrides win. Dash/random contextual characteristics
remain unknown, without extra RNG consumption. Existing random WS/S/T/W/I/A handling
is unchanged. Compiler bonuses and attribute-analysis reconstruction preserve both
optional fields. The existing editor can continue supplying six statistics: compilation
restores canonical M/Ld. Exposing contextual controls belongs to T13.6.

The kernel keeps the six-stat tuple and adds named M/Ld fields. Native folding also
carries the optional values; `FighterC` records values and presence separately. This
is preservation of facts, not a claim that future M/Ld mechanics already consume them.
Existing source-verified `construction_tags` and effect tags supply classification;
this lot adds no classification inferred from names.

## Explicit local context

[`DuelContext`](../../../../packages/python/core/mordheim_core/models.py) is immutable
and picklable. It contains the two local IDs, optional configured neighbors with side
and condition, supplied edge-to-edge distances in inches, optional contact pairs,
terrain labels, charge participants and initial active participant. Tuple conversion
protects supplied list snapshots from subsequent caller mutation.

IDs must be nonempty and unique within the request. Relationships reference known,
distinct local participants. Distances must be finite/nonnegative and cannot duplicate
an unordered pair. Contact contradicts a supplied nonzero edge distance. Missing
distance/contact facts remain unknown; no geometry, line of sight or path is inferred.
Neighbor side IDs use the local `first`/`second` sides when they belong to either duel
side. Additional side labels are local facts, not band/campaign IDs.

`charging=None` retains the historical random choice of exactly one charger; explicit
`()` means neither and a two-ID tuple means both. Explicit charging requires an initial
player-turn owner. Charge and clock are independent: the active participant can differ
from the charger. Alternating player turns derive from that owner, not from charge.

[`prepare_duel_context`](../../../../packages/python/core/mordheim_core/context.py)
is the common preparation boundary used by the kernel, modular initialization, NumPy
batch driver, native entry and replay. It binds the same compiled fighters to local
instances and provides strict participant, required-characteristic and distance lookup.
Transient conditions, resources, penalties and expiry continue using existing fighter
state. There is no generic encounter/event framework or autonomous battle simulator.

## Actual consumers and transport

The modular round consumes independent charge flags and player-turn ownership, retaining
context with immutable state transitions. NumPy and native use the same supplied flags
for priority, attack pools, reactions, recovery and turn-sensitive operators. Proof
includes charge attack bonuses and Inspiring Sermon with neither fighter charging.

Public requests, scalar samples, NumPy batch segments, process pools and Combat Lab
battery workers carry context. `DuelExecutionSettings.request` and `simulate_battery`
accept optional context without UI changes. Native exports `CONTEXT_VERSION=1`; a stale
extension cannot silently accept a context it ignores. Explicit native selection rejects
unsupported plans. Automatic selection may route an unsupported/stale plan to NumPy.

With no context, historical initialization order, generator and decisions remain.
An empty context preserves the same draw order/results. This lot does not unify seeded
streams: scalar charge precedes initialization; optimized initialization precedes charge.

## Deterministic proof seam

[`replay_duel`](../../../../apps/combat-lab/mordheim_combat_lab/verification/parity/_replay.py)
runs a single actual duel through modular round resolution, NumPy's observed batch core
or the rebuilt native batch core. Native observations are copied from C state before
freeing it. Explicit native replay never calls a fallback or the modular operator.

Scripts reuse `StrictDice`/`StrictDecisions`. Each backend's physical draw/decision order
is independently authored, checked and fully consumed. Optimized binary charge/tie
requests consume explicit D2 fixture entries; they never return fabricated zeros.
Integer bounds are checked (native inclusive bounds become NumPy exclusive bounds).
Missing, extra, wrong-sided and invalid-valued draws/choices fail.

Observation records backend identity, winner, actual rounds, wounds, conditions,
spent expendable resources, roll requests and decisions. Winner conventions are
normalized explicitly; the initialization marker `disability.N` is not a spent
resource. Round counters use int64 to prevent the observed 32768-round overflow.
Native callback ownership rejects nested batches, propagates exceptions and clears
ownership on every exit. Production PCG execution remains unchanged.

Current permanent cases cover ordinary hit/wound/injury/removal, absence/misses,
priority ties, both random charge directions, a D3 preparation, lucky-charm consumption,
Bull Charge acceptance/rejection, explicit turn-sensitive attack counts, disability,
pool transport, invalid facts, callback bounds/reentry/cleanup and counter overflow.
They prove this small supported path, not all T13 obligations. Physical dice labels and
legacy decision keys are not yet uniform semantic-role identities across all backends;
future mechanism lots must author/review their role ordering and observable state,
including additional native decisions and duration/reaction compositions.

## Validation and reproducibility

Final validation is recorded below. Independent review accepted the contract/replay
scope after both reproduced observation defects and the coverage concerns were fixed. Ignored local evidence:
`build/cache/t13-1/`. The six legacy samples use seed31, 200 duels, batch67, max5 rounds,
plain/Crimson Shade mace versus sword/lucky charm. Entry source copies came from HEAD,
including the original native binary; final results must match all six tuples exactly.
The evidence includes native source/binary SHA256, build log, test XML, semantic reports,
parity certificate and line-coverage review. Generated C is rebuilt by Cython, never edited.

On this Windows checkout, the first GCC on PATH is 32-bit. The successful build uses the
installed 64-bit compiler and Python's Win64 ABI declaration, through existing setup:

```powershell
$env:CC = 'C:/msys64/mingw64/bin/gcc.exe'
$env:LDSHARED = 'C:/msys64/mingw64/bin/gcc.exe -shared'
$env:COMBAT_NATIVE_CFLAGS = '-DMS_WIN64'
python setup.py build_ext --inplace --compiler=mingw32 --force
python -m pytest tests/python/combat/test_duel_context.py tests/python/verification/test_duel_replay.py -q
python tools/mordheim-utils.py verify --json
python tools/mordheim-utils.py parity --json --require-complete
python tools/mordheim-utils.py coverage-gate --json
```

The standard portable rebuild remains `python -m pip install -e .`; an optional
extension build that succeeds at installation alone does not prove a usable native
backend. Inspect fresh-process identity and exercise its real observed entry.


## Accepted evidence — 2026-09-30

- Final fresh-process check: **78 passed** (75 new context/replay cases, local Markdown
  links and two existing workbook round trips). Native replay executed the compiled
  extension, including 32768 rounds and callback failure/cleanup; no tests skipped.
- Broader construction/combat/verification/battery/architecture run: **4342 passed**.
  Five semantic/audit failures also reproduce with the unchanged HEAD engine/core
  sources. The sixth failure was a newly introduced README encoding error; it was
  repaired and the final documentation check is green. The subsequent native,
  contract and architecture run passed all **97** cases before the last two added
  error-path tests; those two also passed and are included in the final 78-case run.
- `verify --json`: entry and final JSON are exactly identical. Structural validation
  succeeds for **1050 profiles**. Semantic validation still has **455 source-changed
  errors**, 171 verified/547 pending obligations and the pre-existing audit-status
  failures. Nothing was repinned or marked implemented to hide those findings.
- `parity --json --require-complete`: **exit0**, seven deterministic operator groups
  and the applicable specification replay complete. No statistical/deep/truncation
  certificate for all T13 mechanisms is claimed by this foundation lot.
- `coverage-gate --update-budget --json`: **418 passed**, gate exit0; modular97.07%,
  NumPy93.75%, phases96.94%. The old budget was already stale for 30 driver lines at
  HEAD, even while its 343 selected tests passed. Independent line/statement review
  preserves **2851** formerly covered unchanged executable statements across18 modules;
  **zero losses**. Changed covered blocks have tested replacements. Native import
  failure and actual process-pool cancellation are covered rather than discarded.
  The committed budget matches the accepted measurement and includes the new suites.
- Legacy seed31 samples are bit-for-bit unchanged for modular, NumPy and native:
  plain `(35,99,66)`, `(37,77,86)`, `(30,97,73)`; Crimson Shade `(49,83,68)`,
  `(45,75,80)`, `(46,92,62)`, respectively (wins first/second/unresolved, 200 each).
- Final compiler/build exit0: GCC x86_64 through existing setuptools/Cython setup.
  Loaded `_combat_native.cp310-win_amd64.pyd`, context ABI1, numeric effect layout55.
  Source SHA256: `fbf16326c5d7f6500ab70a4e67c46bf269df326a8f10f9cfed64d860259a21f9`.
  Binary SHA256: `580b54c565816e6495489d91f005973108e096cd28ea9921fdd8a71795989794`.
- Independent review: source/context/clock/pool paths, five targeted observed cases,
  fixes and coverage reconciliation accepted. The coordinator owns final integration.
  Authored-file whitespace check passes; generated C retains Cython's own emitted
  whitespace and is included as generator output, not a manual patch.

The five baseline failures and broader source reconciliation remain explicit work for
later source/mechanism lots and T14. T13.1 is accepted; overall T13 remains in progress.

## Handoff

T13.2 can consume these contracts. It owns canonical grants/selection/recipient routing;
T13.3-6 own the respective new behavior, semantic roles/choices, expiry and product
access. X1-X4 exclusions remain. T14 owns full certification/reconciliation; the existing
source-fingerprint failures are not repaired by automatically refreshing pins here.
No commit or push is part of this lot.
