# Project backlog

Open defects, verification gaps and deferred capabilities.

## Local CI blockers

The 2026-11-12 local CI re-run passed every step, including the presentation
gate after the audit calibration below. Combat Lab UI checks are outside this
CI selection and still need a Python environment with Tkinter.

## Presentation audit maintenance

The static GUI text audit runs in CI with no baseline and a single execution
mode (all GUI sources, resolved types, full flow trace — the retired
strict/deep tiers and the accepted-findings baseline were removed on
2026-11-12): any finding fails the gate. Its error rates are pinned by
`tests/applications/warband_manager/presentation/completeness/presentation-audit-corpus.test.mjs`
(leak cases that must be flagged, control cases that must stay clean, one
adversarial leak per precision exemption), which runs inside the gate. When a
new code pattern produces a false positive, fix the tool and add the pattern
as a CONTROL case next to a LEAK case for the same exemption; never silence it
in product code. Known limits: field-name heuristics for raw origins
(`rawFields` in `presentation-flow-audit.mjs`) and a step budget on flow
slices. Local resolution is symbol-keyed through the type checker
(2026-11-12), so shadowed or same-named locals — including a local function
shadowing `presentationOutput` — resolve to their own declarations.

## Item catalogue

### Derived descriptions awaiting their printed entries

These items show a description built from their equipment-list data (list, cost, rarity, bearers) and carry a `# Derived description` comment. Their entries are printed only in Spanish books that are neither online nor mirrored here: *Khemri* (`dispelling_scroll`, `icon_of_manann`, `whip`), *Lustria* (`feather_headdress`, `sacrifice_dagger`, `magic_tattoos`, `shrunken_head` for the Savage Goblins; `jungle_roast`, `magic_tattoo`, `spider_amulet`, `poisoned_darts` for the Pygmies) and *Chaos in the Streets* (`travel_staff`, `poison_darts`). The *Lustrian Artefacts* entry named *Spider Amulet* describes a different object from the Pygmy list item.

### Item coverage

List implemented items with missing or partial deterministic coverage using
`python tools/knowledge/clauses.py coverage --kind item --pending`.

## Rules-conformance coverage

The scenarios and the accepted-evidence baseline pass (2026-11-12 run: 5,248
passed). The completeness gate
(`MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`)
still reports 591 admitted identities without scenarios and 15 identities with
uncovered admitted clauses — an authoring backlog, not a regression. Close when
the gate passes with the existing clause identities.

- **Missing conformance scaffolds.** 225 admitted identities have no authoring
  file: `python tests/conformance/generate_skeletons.py --check` exits 1 listing
  224 hireling identities (commit 0a46aab6) and
  `night-goblins-kaz--band--animosity--mechanic.goblin-squabble` (35a01f4c).
  Close when the check exits 0.

## Combat Lab checklist popover closes during layout

Unverified report of `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`). Determine whether widget lifecycle
or test focus setup destroys the popover; close when both pass with their
theme, width and scrollbar assertions intact.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle. For stored
samples, use `python tools/mordheim-utils.py check samples compare` with the
candidate and modular stores. Keep the six-sigma gate for first-win,
second-win and unresolved rates, and verify source and input digests.

- **Native.** Run the native runtime and deterministic replay selections
  (`tests/engines/native/`): attack-event gating, pool allocation and Rapier
  Barrage touch the replay paths. Then requalify `--scenarios big` against
  `modular-100k` and re-sample `native-deliveries-100k` from a clean commit.
- **Stale and affected deliveries to regenerate at the next re-sample.** The stored samples still carry the two retired Cleaver deliveries; the 8 deliveries drawn from the two Night Goblins (KAZ) scenarios edited on 2026-11-11 pin an old scenario sha256 and are classified stale; and the samples of the other deliveries naming KAZ goblins or Main Gauche bearers predate the Animosity and Main Gauche behaviour changes.

- **NumPy stored delivery sample.** `numpy-deliveries-100k` predates the current engine.
  Re-sample it from a clean commit (the current engine passes every parity
  delivery against `modular-deliveries-100k` at 20,000 duels, including the Raging
  Peasants fist case that diverged in the stored sample).
- **Systematic delivery-campaign offset.** Every NumPy parity delivery passes the six-sigma
  gate, yet the rates lean one way: over the 1,815 distinct inputs the
  first-win z-scores average about +0.2 and the unresolved ones about +0.9
  against `modular-deliveries-100k`. The per-case z-scores share one seed, so their
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
- **Rejected parity deliveries.** Admission states of parity deliveries, not
  failing conformance tests: 2,485 deliveries never run: 1,491 need
  `initial_state` overrides or auxiliary participants the shared runner cannot
  express, 530 prescribe scripted decisions and 464 are expected construction
  refusals. The first two groups stay uncertified until the runner supports
  them.

Stored samples live in `tests/engines/parity/reference_samples/`.
Running the modular engine requires explicit authorization.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause. Catalogue text is corrected; motor support remains pending by user decision (2026-11-10). Sunbolt shooting remains outside the duel. |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
