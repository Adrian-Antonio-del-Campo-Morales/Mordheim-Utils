# Hired Swords and Dramatis Personae

`sources/knowledge/catalog/hirelings/` owns intrinsic profile identity,
characteristics, equipment, skills, rules and rating. Hiring fees, upkeep,
search procedure and eligibility belong to
`catalog/campaign/hired-swords-and-dramatis.yaml`; reusable group facts belong
to `registry/warband-groups.yaml`.

## Identity and invariants

- Hired Sword profiles use `hireling.hired-sword.<slug>`.
- Dramatis Personae use `hireling.dramatis.<slug>`.
- Campaign hiring entries use `campaign.hireling.<slug>` and reference a
  `profile_id`.
- Do not reuse a band profile merely because its name matches a hireling.
- Reference canonical item and skill IDs only after confirming equivalence.
- Keep unknown concepts in the profile's `unresolved_references`; never invent
  a canonical ID.
- Store campaign rolls, choices and rewards outside the KB.
- Evaluate dynamic roster/variant restrictions through
  `*.rule.campaign-eligibility`, using the canonical trait registry rather
  than application-maintained sets.

Profiles that require composite warriors, mounts or selectable personas remain
`status: out_of_scope` until the KB has an entity schema that can represent
them without flattening their rules.

## Resolving knowledge gaps

The authoritative backlog is the `unresolved_references` collection in each
profile. Add the missing canonical catalogue or schema, update references, and
remove only the entries that now resolve. [Project backlog](../TODO.md) groups
the remaining categories without duplicating volatile counts.

## Source provenance

Every profile, rule and hiring entry carries `source_refs`: the manual, the
printed page, the section and the URL of the document it was transcribed from.
The URL resolves in `registry/source-documents.yaml` to that document — one
entry per document, with every URL it is cited by and the path of the copy the
offline mirror (`build/cache/`) keeps. A citation the registry does not declare
fails `tests/python/knowledge/test_source_documents.py`.

The catalogue-vs-source cotejo goes the same way: `tools/knowledge/source_documents.py`
turns a record into the document that prints it and hands it to
`tools/knowledge/printed_entries.py`, which reads the entry as the document
prints it. A document whose copy is not downloaded is reported with the path it
is missing, never compared against an empty page.
`tools/knowledge/check_hireling_sources.py` is that cotejo as a command: it walks
both published catalogues — Hired Swords and Dramatis Personae, every grade — and
`--tree 2b` runs it over the staging tree with the same reading.

## Validation and loading

The matching schemas in `contracts/knowledge-editorial-v1/` define profile,
rule and trait shapes. Structural verification validates them before the
loader contract.

`mordheim_knowledge.campaign.load_hirelings(ruleset)` is the authorized read
path. It checks IDs, rule references and items; campaign loaders additionally
resolve every hiring `profile_id`. Coverage lives in
`tests/python/knowledge/test_campaign_loaders.py` and the editorial schema
tests.
