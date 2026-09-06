# `registry/` — the lookup and constraint layer

The registry holds the small files that give the rest of the KB its shape:
collections, rulesets, editorial sources, band aliases, cross-band warband
groups and the runtime classification schema. Full layout and the
classification contract:
[the KB guide](../../../docs/reference/knowledge-base.md).

## Files

| File | Content |
| --- | --- |
| `collections.yaml` | The two collections, `mordheim` and `trollheim`, both bound to the `mordheim` ruleset. |
| `rulesets.yaml` | The active ruleset (`mordheim`). |
| `sources.yaml` | Registered editorial sources (e.g. `mordheimer.net`). |
| `aliases.yaml` | Band aliases for name normalization (e.g. "Amazons (Lustria)" → `amazons-lustria`). |
| `warband-groups.yaml` | Cross-band groups by race/alignment/faction (e.g. `warband-group.orc`, `warband-group.chaotic`, `warband-group.good-aligned`) used by access and restriction logic. |
| `runtime-schema.yaml` | **The classification contract.** Defines `scope`, `implemented`, `grant`, `effects`, binding kinds and the invariants every rule must satisfy. |
| `runtime-scope.yaml` | Scope policy of the runtime: `close-combat-only`, plus a list of mechanics excluded with a reason. |

Group IDs are namespaced `warband-group.<slug>`; eligibility and restriction
blocks of the campaign catalogues reference them exactly by that id
(`mordheim_knowledge.campaign.load_warband_groups` validates all references;
tests in `tests/knowledge/test_campaign_loaders.py`).

## The `good-aligned` audit

`warband-group.good-aligned` holds **40 warbands** and is the alignment group
the good-aligned Hired Swords (e.g. the Warrior Priest of Sigmar contract) and
William Schäkestange's conditional acceptance are evaluated against. Its
membership was audited warband by warband against mordheimer.net, and the
`status: partial` marker was removed. It does not contradict
`warband-group.evil` nor `warband-group.chaotic`.

**Method.** The warband pages on the site do not publish an alignment tag, so
the classification relies on:

1. the official Hired Swords availability texts — express parity of access
   with the Human Mercenary warbands, unrestricted access to good-aligned
   contract swords, or short exclusion lists that leave them available; and
2. membership of canonically good races/orders (Dwarfs, High Elves, Halflings,
   Sigmar's orders, Bretonnian knights, imperial institutions), when the
   warband does not belong to the registry's own evil/chaotic groups.

**Residual doubts — warbands with no source declaration, treated as
non-good/neutral and therefore NOT included:** `horned-hunters`,
`lustrian-reavers`, `khemri-mages`, `khemri-thieves-guild`,
`chaos-streets-arcane-society`, `chaos-streets-deathbringers`,
`chaos-streets-mordheim-inhabitants`, `lustria-pygmies`, and the orc/goblin
warbands (`black-orcs`, `orc-mob`, `forest-goblins`, `night-goblins-*`,
`lustria-savage-goblins`, `khemri-hobgoblin-raiders`,
`chaos-streets-greenskins`), which the hiring canon expressly excludes
(«Orcs & Goblins»). If a future source classifies them, the audit must be
repeated only for those warbands.

The per-warband membership (including the 14 warbands added during the audit,
with the source clause or race convention that justified each) lives in
`warband-groups.yaml` itself.
