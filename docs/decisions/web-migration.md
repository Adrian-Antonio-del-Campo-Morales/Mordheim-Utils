# Warband Manager: desktop → web port

This is the single current guide for the functional and test migration. Read it before changing the web port. It describes the desired end state; verify claims against executable code and tests.

## Goal and scope

Port the Campaign Manager from `apps/warband-manager-desktop/` and `packages/python/campaign/mordheim_campaign/` to `apps/warband-manager-web/` and `packages/typescript/`, with equivalent domain outcomes, validation failures, persistence semantics and user-critical flows.

Included:

- campaign creation, draft, roster/equipment, battle recording, timeline and post-battle processing;
- advances, injuries/recovery, hirelings, exploration/searches, trading, upkeep, rewards and rules browsing;
- `.mordheim` v4 import/export and desktop ↔ web interoperability;
- accessible React UI, explicit in-memory sessions, import/export and dirty-loss protection;
- the campaign Knowledge Base required by the desktop `KnowledgePort`.

Excluded by product decision: Combat Lab and combat simulation, NumPy/Cython/Tkinter, YAML loading in the browser, browser storage (`localStorage`, IndexedDB and `sessionStorage`), desktop PDF implementation unless a separate product decision adds it. An excluded desktop test must carry a reason in the parity manifest.

## Traceability

The test traceability manifest is generated at `tests/web/parity/campaign-test-manifest.json` by `tools/make_test_manifest.py`. Each row is classified as:

- `implemented`: equivalent behavior is tested;
- `partial`: only a subset is covered, with a concrete follow-up;
- `blocked`: a required runtime operation or seam is missing;
- `excluded`: outside scope, with a reason;
- `pending`: not yet assessed (not allowed at final acceptance).

Do not infer parity from a file name or historical test count.

## Rules that must remain true

- `sources/knowledge/` is the only editorial KB source.
- `.mordheim` v4 is the only supported campaign format; readers explicitly reject v1–v3.
- Stable KB IDs identify bands, profiles, items, rules, scenarios and other entities; display names are locale data, never identity.
- The v4 `campaign` state and reconstructible `view` state remain separate. Open payloads are preserved verbatim.
- Domain/application TypeScript imports no React, DOM, browser storage, Python or filesystem APIs.
- The browser keeps campaigns in memory and exports explicitly.
- The web bundle contains no Combat Lab, simulation runtime, NumPy, Cython, Tkinter, source YAML or user campaign files.

## Integration and verification gates

### G1 — clean integration

Run from a clean checkout. Do not reset or stage another contributor's work.

### G2 — traceability

Regenerate the manifest. Repair targets through the generator or an explicit mapping. No applicable row may remain `pending`; every `partial`, `blocked` and `excluded` row has evidence, a follow-up or an accepted reason.

### G3 — functional parity

Critical path works end to end:

```text
create/import → draft → commit → battle → post-battle → review/export
```

Equivalent invalid operations, immutable transitions, undo/reload behavior and dirty-state outcomes are covered at domain/application level and through real UI seams.

### G4 — interoperability

All four v4 fixtures pass both readers. Demonstrate Python → TypeScript → Python and TypeScript → Python → TypeScript, including malformed corpus, unknown IDs, open payloads, snapshots, acquisition/copy costs, locales and non-Latin text.

### G5 — web quality and boundaries

The real KB asset loads in production composition; UI errors are announced; historical moments are read-only; keyboard/responsive checks pass; the bundle excludes prohibited code/data; typecheck, lint, tests and build pass.

### G6 — release

From a clean checkout, run the Python contract/campaign/web/architecture/knowledge suites, TypeScript package checks, web checks/build, post-build boundary checks and deterministic KB check. Then manually import a desktop campaign in the browser, edit/export it and reopen it in desktop. Publish only after CI is green and Pages serves the expected base path.

## Knowledge Base inventory

The web artefact is derived only from `sources/knowledge/`. Required inputs are:

- `registry/collections.yaml`, `registry/warband-groups.yaml`, `bands/**`;
- `catalog/items/*.yaml`, `catalog/skills/*.yaml`, `catalog/mechanics/*.yaml`;
- `catalog/rules/*.yaml`, including `catalog/rules/racial-maximums.yaml`;
- `catalog/campaign/trading-post.yaml`, `scenarios.yaml`, `post-battle-sequence.yaml`, `serious-injuries.yaml`, `experience-and-advances.yaml`, `exploration-and-income.yaml`, `magic.yaml`, `mutations.yaml`, `hired-swords-and-dramatis.yaml`, `scenario-rewards.yaml`, `warband-rating.yaml`, `recruitment-and-veterans.yaml` and `trading-and-rarity.yaml`;
- `catalog/hirelings/**/*.yaml` for hireling profiles, rules and traits.

The generated JSON must preserve stable IDs, locale names and the payloads needed by the application. Combat Lab runtime mappings (`simulation mappings`, `execution contract`, `runtime scope`) and `out-of-scope` items are excluded. Tests must verify that every required source exists, every fixture band resolves, and excluded surfaces do not leak.

## Operational decisions

- **Persistence:** v4 is the sole interchange format; `saved_at` is the only volatile field. The browser has no implicit disk persistence.
- **Knowledge delivery:** generate deterministic JSON from `sources/knowledge/`, copy it to `public/knowledge/knowledge-web.json` at build time, fetch it once at startup, and show a reader error if loading/validation fails. Do not inline the multi-megabyte artefact into JavaScript. Keep the current gzip budget enforced by the performance test.
- **Naming:** responsibility-oriented namespaces (`domain`, `application`, `adapters`, `features`) are the public TypeScript structure. Do not perform broad renames for product-name consistency. Remove the Python `application/state.py` compatibility shim only after all internal imports move to `domain.models`.
- **Deployment:** CI validates Python and TypeScript in separate jobs with a final green gate; Pages builds from `main`, publishes only `apps/warband-manager-web/dist/`, and rejects `.mordheim` files in the artefact. Pages source must be GitHub Actions.

## Definition of done

The port is complete only when G1–G6 pass, no applicable manifest row is pending, critical desktop operations have equivalent web outcomes and rejections, both file round trips preserve semantics, the real KB is used, framework boundaries hold, the browser critical path has accessible interaction evidence, and all remaining TODOs are explicitly non-critical accepted limitations.
