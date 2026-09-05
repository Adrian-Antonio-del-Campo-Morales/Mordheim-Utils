# `registry/` — the lookup and constraint layer

The registry holds the small files that give the rest of the KB its shape:
collections, rulesets, editorial sources, band aliases, cross-band warband
groups and the runtime classification schema. Full layout:
[the knowledge-base guide](../../../docs/knowledge-base-guide.md).

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

**Added during the audit (14):**

- `hochland-bandits`, `kislevites`, `merchant-caravans`, `pirates`,
  `lustria-pirates` — the page declares Hired Swords access identical to a
  Human Mercenary warband (pirates: «same access to Hired Swords & any other
  items as for a regular human Mercenary Warband»).
- `imperial-outriders` — mounted swords only, including the Roadwarden
  (good-aligned contract).
- `outlaws-of-stirwood-forest` — only 4 exclusions (Bounty Hunter, Wolf-Priest
  of Ulric, Norse Shaman, Dark Elf Assassin); the remaining swords, including
  the good-aligned contract ones, stay available.
- `bretonnian-knights`, `bretonnian-chapel-guard`,
  `chaos-streets-bretonnian-knights` — Bretonnian knightly order (Chivalry,
  Holy Water, no poisons/drugs).
- `chaos-streets-sigmar-protectorate` — mirror of
  `warband-group.sigmar-devoted` (Sisters of Sigmar and Witch Hunters were
  already included).
- `lustria-high-elves` — mirror of `warband-group.high-elf` (Shadow Warriors
  and Sons of Nagarythe were already included).
- `mootlanders` — halfling race, no contrary declaration on the page (race
  convention).
- `gunnery-school-of-nuln` — imperial state institution; the page does not
  publish a Hired Swords section (documented inference).

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
