# Project backlog

Open defects, verification gaps and deferred capabilities. Each entry states
what is pending and when it is done.

## Rules-conformance coverage

- **Authoring backlog.** 663 of 2,396 admitted identities have no scenarios and
  21 of 443 admitted clauses are uncovered. Check with
  `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1 python -m pytest tests/conformance -q`;
  done when the gate passes.
- **Missing scaffolds.** 300 admitted identities have no authoring file (224
  hireling identities, the bindings added on 2026-11-13, and
  `night-goblins-kaz--band--animosity--mechanic.goblin-squabble`). Done when
  `python tests/conformance/generate_skeletons.py --check` exits 0.
- **Scenarios on placeholder identities.** 60 scenarios still name placeholder
  identities of rules whose duel effect is now bound (the seven supplied-condition
  splits: Petru potions, Mad Scientist alchemy, Danse Macabre, Fungus Brew,
  Dwarf Brewers, Power Grab, Goading; plus Reikland, Mad Cap Masters,
  Constructs, Rememberer, the living Tomb Scorpions and the Stone Golem). They
  count as outside-scope scenarios. Done when they are moved onto the bound
  identities (and their parity deliveries re-pinned).
- **Weak scenarios.** Rule-removal probing showed scenarios whose dice never
  reach the rule's boundary (Strength of Steel, Strike to Injure, Unarmed
  Critical Strikes, Unstoppable Charge). Done when each positive scenario fails
  with its rule removed.

## Runtime classification

- **Bindings that execute nothing.** `trait.pit-fighter` (six Mordheim Pit
  Fighters profiles; construction tests pin the trait tag),
  `compiler.warrior-wizard` (the Liche) and `condition.large-target` (three
  hired-sword rules) read as implemented, but no engine or compiler code
  consumes them. Decide per binding: implement it, or unbind it.
- **Saurus bite.** `compiler.bite-attack` never strikes last (only
  `rule.strikes-last-bite` does, `modular/rounds.py`), although the printed bite
  "always strikes last".
- **Bagh Nakh through Trading.** The Thieves' Guild list entry names the
  Hashashiyyin as the creation-price bearer; the printed "other members must
  acquire it through Trading" path is not modelled because
  `catalog/campaign/trading-post.yaml` is Mordheim's post, where Bagh Nakh is not
  sold. Add the Khemri trading entry (rarity, recipients).
- **Thrown weapons and `non-thrown-ranged`.** `no-missiles-or-armour` lets thrown
  weapons pass a text that bans "any missile weapons"; record a ruling or
  change the token.
- **Close-combat items marked `out_of_scope`.** Spike-Jawed Snatcher, Gas Mask,
  Cathayan Plate Armour, Corpse Liquor and Pneumatic Arm: review their duel
  status in the item catalogue.
- **Untracked supplied conditions.** 38 conditions of
  `catalog/rules/conditions.yaml` have no mirror in
  `catalog/mechanics/close-combat.yaml`, so no rule can bind them and the
  inventory does not track them (runes, Witch and Weaponsmith services, Master
  Craftsman, serious-injury states). Mirror the duel-relevant ones when their
  rules are bound.
- **Snotling Mob "Dodgy".** Crooked Moon prints "+D6 dodge save" where every
  other copy prints "6+": verify the source.
- **Sharing proposals left out.** Set Traps, Netter, Addict, Frantic,
  Swashbuckler, two Wizard / Spellcaster pairs, the "Immune to Psychology" texts
  that lack "never leaves combat", and a Large Target text that spells out +1 To
  Hit. Decide each with the equivalence rule of `docs/reference/knowledge-base.md`.

## Item catalogue

- **Derived descriptions awaiting printed entries.** These items carry a
  `# Derived description` comment; their entries are printed only in Spanish books
  not mirrored here: *Khemri* (`dispelling_scroll`, `icon_of_manann`, `whip`),
  *Lustria* (`feather_headdress`, `sacrifice_dagger`, `magic_tattoos`,
  `shrunken_head` for the Savage Goblins; `jungle_roast`, `magic_tattoo`,
  `spider_amulet`, `poisoned_darts` for the Pygmies) and *Chaos in the Streets*
  (`travel_staff`, `poison_darts`). The *Lustrian Artefacts* *Spider Amulet* is a
  different object from the Pygmy list item.
- **Item coverage.** List implemented items with missing or partial
  deterministic coverage with
  `python tools/knowledge/clauses.py coverage --kind item --pending`.

## Engine coverage lost with the retired replay suites

The coverage budget was regenerated on 2026-11-13; 282 statements that the
retired replay suites covered are no longer covered (127 in
`vectorized/_operators.py`, 78 in `vectorized/_attacks.py`, 28 in
`vectorized/_driver.py`, 24 in `phases.py`, 25 across `modular/`). Done when they
are covered again or explicitly accepted as out of scope.

## Combat Lab checklist popover

Unverified `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`; needs Tkinter). Done when both pass
with their theme, width and scrollbar assertions intact.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle with the
six-sigma gate (`python tools/mordheim-utils.py check samples compare`).
Stored samples live in `tests/engines/parity/reference_samples/`; running the
modular engine requires explicit authorization.

- **Native.** Run `tests/engines/native/` (attack-event gating, pool allocation
  and Rapier Barrage touch the replay paths), then requalify `--scenarios big`
  against `modular-100k` and re-sample `native-deliveries-100k` from a clean
  commit.
- **NumPy.** Re-sample `numpy-deliveries-100k` from a clean commit (the current
  engine passes every delivery against `modular-deliveries-100k` at 20,000
  duels).
- **Stale stores.** In each delivery store, 254 records name scenario ids that no
  longer exist and 249 admitted deliveries have no record; 11 deliveries are
  stale (8 Night Goblins KAZ, 3 Extra Arm). KAZ goblin and Main Gauche samples
  predate their behaviour changes. Regenerate at the next re-sample.
- **Systematic offset.** NumPy deliveries all pass, but first-win z-scores
  average about +0.2 and unresolved ones about +0.9 over 1,815 inputs (one shared
  seed). Determine whether it is an engine difference or the oracle-provenance
  problem.
- **Oracle provenance.** The stored modular samples carry a source digest that
  matches no commit. Confirm which inputs later commits affect, or regenerate
  with authorization, before claiming current-engine certification.
- **Survivor condition.** On `scenario/stateful` the winner of a decided duel is
  not Standing in 1.56 % (Modular) vs 1.98 % (NumPy) of duels. Decide whether the
  terminal condition should become a compared magnitude.
- **Portable native digests.** Add a line-ending rule for `.pyx`/`.pxd` in
  `.gitattributes` so Windows and Linux checkouts produce the same digest.
- **Rejected deliveries.** 1,484 deliveries need `initial_state` overrides or
  auxiliary participants and 529 prescribe scripted decisions; they stay
  uncertified until the shared runner supports them.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause (motor support pending by user decision, 2026-11-10). |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
