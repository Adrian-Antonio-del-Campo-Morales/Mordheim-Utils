# Project backlog

Open defects, verification gaps and deferred capabilities.

## Local CI blockers

The 2026-11-12 local CI run on `719b3987` (Python 3.14.4, Node 22.16.0,
eight test workers) finished with 13 passing steps and four failing steps.

- **Python regression (`05-python-regression`).** The Scourge split left two
  catalogue checks failing: the normalized name `scourge` now matches
  `scourge` and `slaver_scourge`, and the generated catalogue has 465 items
  against an expected 464. Reconcile both checks with the two printed entries.
  The translation consistency check also found a missing Spanish name for
  `night-goblin-special-skills` in `sources/knowledge/registry/sources.yaml`;
  reuse the translation in the Crooked Moon band rules.
- **Extra Arm with a shield (`06-modular-e2e`).** The scenario
  `a-shield-in-the-extra-arm-still-adds-one-attack` still fails because the
  second attack's hit and wound rolls are unused. Confirm the printed rule and
  reconcile the attack sequence with the scenario.
- **Web lint (`14-web-lint`).** Resolve 12 ESLint errors in Warband Manager
  tests (unused bindings and explicit `any`). Rerun
  `npm run lint --workspace warband-manager-web` to verify ESLint and the
  presentation gate, which did not run.
- **Web campaign artefact (`15-web-test`).** The campaign obligations suite
  failed during collection. CI generates into `outputs/web-public/knowledge/`,
  but the test helper looks in `build/generated/knowledge-web/`. Align the
  helper with the generated artefact and rerun the campaign checks that depend
  on it, including the skipped variant construction and catalogue reader tests.

KB generation and determinism, the accepted E2E evidence baseline, eligibility,
TypeScript typechecks, package tests, web localization, the build and
post-build bundle guardrails passed. Combat Lab UI checks are outside this CI
selection and still need a Python environment with Tkinter.

## Item catalogue

### Derived descriptions awaiting their printed entries

These items show a description built from their equipment-list data (list, cost, rarity, bearers) and carry a `# Derived description` comment. Their entries are printed only in Spanish books that are neither online nor mirrored here: *Khemri* (`dispelling_scroll`, `icon_of_manann`, `whip`), *Lustria* (`feather_headdress`, `sacrifice_dagger`, `magic_tattoos`, `shrunken_head` for the Savage Goblins; `jungle_roast`, `magic_tattoo`, `spider_amulet`, `poisoned_darts` for the Pygmies) and *Chaos in the Streets* (`travel_staff`, `poison_darts`). The *Lustrian Artefacts* entry named *Spider Amulet* describes a different object from the Pygmy list item.

### Item coverage

List implemented items with missing or partial deterministic coverage using
`python tools/knowledge/clauses.py coverage --kind item --pending`.

## Modular integration and E2E coverage

The local CI run passed the accepted-evidence baseline check. After resolving
the modular E2E failure, run
`MORDHEIM_E2E_REQUIRE_COMPLETE=1 python -m pytest tests/integration/e2e -q`
on the delivered revision. Close when the scenarios, admitted-clause coverage
and accepted-evidence baseline pass with the existing clause identities.

## Web projection verification

Regenerate the web projection with `python tools/knowledge/generate_knowledge_web.py`.
Check that `outputs/web-public/knowledge/knowledge-web.json` publishes the
inherited rules, equipment access and skill access for the Karak Azgal
Guildsmen and Slayers with the correct profile recipients.

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
  `modular-100k` and re-sample `native-e2e-100k` from a clean commit.
- **Stale and affected deliveries to regenerate at the next re-sample.** The stored samples still carry the two retired Cleaver deliveries; the 8 deliveries drawn from the two Night Goblins (KAZ) scenarios edited on 2026-11-11 pin an old scenario sha256 and are classified stale; and the samples of the other deliveries naming KAZ goblins or Main Gauche bearers predate the Animosity and Main Gauche behaviour changes.

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

Stored samples live in `tests/engines/parity/reference_samples/`.
Running the modular engine requires explicit authorization.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause. Catalogue text is corrected; motor support remains pending by user decision (2026-11-10). Sunbolt shooting remains outside the duel. |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
