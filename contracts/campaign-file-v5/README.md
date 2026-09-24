# `.mordheim` campaign file — format v5

**Status:** current interoperability contract for the desktop and web
applications.
**Schema:** [`campaign-file-v5.schema.json`](./campaign-file-v5.schema.json)
(JSON Schema draft 2020-12).
**Fixtures:** [`fixtures/`](./fixtures/) — validated documents for tests and
porting.

## Purpose

`.mordheim` v5 is the **neutral representation of campaign state** shared by
the Python desktop application and the React/TypeScript web application. It is
not a serialisation of Python dataclasses or React components: the structure is
organised by responsibility (identity, configuration, resources, timeline
entities) so both implementations read and write the same document.

Applications write and read **only v5** and reject older versions with a clear
message.

## Document shape

```json
{
  "marker": "MORDHEIM_CAMPAIGN_MANAGER",
  "format_version": 5,
  "saved_at": "2026-09-08T18:30:00+00:00",
  "campaign": { "identity": {}, "configuration": {}, "resources": {}, "warriors": [], "battles": [], "states": [], "post_battles": [], "inventory": [], "special_rules": [], "unique_reward_ids": [], "manual_log": [] },
  "view": { "active_view": "campaign", "selected_moment": "state:7" }
}
```

### Top-level fields

| Field | Type | Policy |
| --- | --- | --- |
| `marker` | string, exactly `MORDHEIM_CAMPAIGN_MANAGER` | Required. Documents without it are rejected before any version check. |
| `format_version` | integer, exactly `5` | Required. v1–v4 are retired and rejected with a message naming the found and supported versions. |
| `saved_at` | ISO-8601 UTC timestamp | Required on write. **Volatile**: two saves of an unchanged campaign differ only here. Semantic comparison must ignore it. |
| `campaign` | object | Required. The campaign state (below). |
| `view` | object | Optional. Reconstructible UI selection state; a reader may ignore or reset any part of it. |

## Sections of `campaign`

- **`identity`** — who the campaign is: `campaign_name`, `warband_name`,
  `warband_type`, `started` (display text), plus the stable KB identity
  `collection` / `band_id` / `ruleset` and the optional `mercenary_variant`
  (string or null). `band_id` is mandatory; a loader must refuse documents
  whose warband cannot be resolved against its KB.
- **`configuration`** — `is_draft` (required) plus the draft construction
  limits `starting_gold` (default 500), `minimum_models` (3),
  `maximum_models` (15), `hero_limit` (5). Writers emit the limits when
  `is_draft` is true; readers must not rely on them otherwise.
- **`resources`** — campaign-level counters: `stash_value`, `rare_finds`,
  `treasures`, `campaign_points`. Wyrdstone shards live on the timeline
  states, not here.
- **`current_state_number`** — newest committed timeline state number (0 for
  a draft or a campaign without committed states). In v3 this lived inside
  the flat campaign payload; since v4 it is a first-class field because it is
  genuine campaign state, not view selection.
- **`warriors` / `battles` / `states` / `post_battles` / `inventory`** — the
  timeline entities. Array order is document order and is meaningful: states
  and battles are ordered by `number`. In v3 these were flat siblings of the
  metadata; v4 grouped them under typed sections and v5 retains that shape.
- **`special_rules` / `unique_reward_ids` / `manual_log`** — campaign-level
  rules in effect, generated-unique-reward history and user corrections.

### Element highlights

- **`warrior.equipment`** entries carry the stable `item_id` plus the captured
  display `name` (a locale snapshot, not a reference).
- **`warrior.upkeep_resources`** is an array of `[resource_id, amount]` pairs —
  JSON has no tuples.
- **`post_battle.completed_steps`** is a sorted array of step indices — JSON
  has no sets.
- **`battle.out_of_action_ids`** is `null` when not recorded (legacy
  distinction kept from v3: `null` ≠ empty list).
- Free-form payload maps (`step_state`, `searches`, `acknowledgements`,
  `scenario_results`, `participants`, `pending_advances`,
  `pending_follow_ups`, `injury_records`, `battle_start_checks`,
  `pending_battle_draft`) are **unconstrained objects** by policy: the web
  port must carry them verbatim without interpreting every key. See
  *Unknown fields* below.

## Unknown fields and forward compatibility

The schema pins `additionalProperties: false` only where the shape is fully
owned by the contract (identity, configuration, resources, typed entity
fields). Payload maps stay open so a newer writer does not silently lose data
for an older reader. **It is always the writer's responsibility to emit
documents valid against this schema**; a reader may apply this schema strictly
on load and reject unknown top-level sections, but should preserve open-payload
content verbatim when re-exporting.

## Validation and errors

A reader must reject, with distinct, actionable messages:

1. not a JSON object, or unreadable/invalid JSON;
2. missing or wrong `marker` (not a Mordheim campaign file);
3. `format_version` other than `5` — explicitly naming v1–v4 as retired and unsupported;
4. schema violations (missing required fields, wrong types, unknown
   top-level/section properties);
5. a `campaign.identity.band_id` that its KB cannot resolve (reference
   validation happens against the KB, not the schema).

## Fixtures

| Fixture | Covers |
| --- | --- |
| `draft.json` | `is_draft: true`, construction limits, initial roster, `selected_moment: "draft:0"` |
| `active-campaign.json` | Confirmed states, completed battles and post-battles, live roster |
| `pending-post-battle.json` | Resumable mid-sequence work: incomplete steps, pending advances, follow-ups |
| `full-inventory.json` | Equipped/stash split, rarity, item special rules, state snapshots with roster+inventory |

Fixtures are valid documents, not tests: every fixture must validate against
the schema, and `saved_at` in fixtures is illustrative. The Python writer is
the reference producer; the fixtures were generated from real application
state and then committed.

## Semantic comparison

To compare two documents semantically (round-trip checks), compare everything
except `saved_at`. Compare `view` only when the test intends to check the
selection; a loader is free to normalise invalid selections.

## Ownership

The schema and fixtures are the single source of truth for the format. The
Python reader/writer (`packages/python/campaign/mordheim_campaign/persistence/campaigns.py`) and the TypeScript `campaign-file` adapter must implement this contract;
neither side may introduce format extensions without updating the schema and
fixtures first.

### Structured advance presentation

Web writers add `applied_result` to a pending advance's open payload. It is
one of `{kind: "characteristic", characteristic, amount}`, `{kind: "skill", id}`,
`{kind: "spell", id}`, `{kind: "duplicate-spell", id, modifier}`, or
`{kind: "external"}`. IDs remain canonical and are resolved in the current
presentation locale. `applied_label` remains for desktop interoperability;
web presentation prefers the structured result. Existing v5 documents without
this field use the exact legacy-result adapter; unknown legacy prose is kept
in the file but displayed as a localized unavailable notice. Unknown open
payload fields must survive round trips unchanged.

`roll_history_events` stores ordered advance facts: `advance-cap` with
`characteristic` and numeric `cap`, `henchmen-reroll` with numeric `total`,
`hero-limit` with numeric `limit`, and `group-promoted` without parameters.
Existing history is preserved as `{kind: "legacy", text}` when a web writer
first appends a fact. `roll_history` is still written for desktop readers.
The web prefers `roll_history_events`; unknown or malformed facts display
the localized unavailable notice without discarding the original payload.

### Structured event presentation

The existing open `event_log` payloads also carry facts for localized web
presentation. Legacy `description` remains unchanged for desktop readers.

| Event type | Presentation facts |
| --- | --- |
| `buy_item`, `buy_rare_item`, `sell_item` | `item_id`, numeric `quantity`, numeric total `gold` |
| `upgrade_weapon` | `base_item_id`, upgrade `item_id`, numeric total `gold` |
| `hire` | `profile_id`, `costs` pairs of resource identifier and numeric amount |
| `recruit` | `profile_id`, `warrior_id`, `warrior_personal_name`, numeric `quantity`, numeric total `gold` |
| `recruit_member` | `profile_id`, `warrior_id`, `warrior_personal_name`, `quantity: 1`, numeric total `gold`, boolean `equipment_pending` |
| `scenario_spell_reward` | `warrior_id`, `warrior_personal_name`, two exact `spell_ids` |
| `dismiss_member`, `dismiss_warrior` | `warrior_id`, `warrior_personal_name`, numeric `quantity` |
| `hireling_upkeep` | `warrior_id`, `warrior_personal_name`, boolean `pay`, resource `costs` |
| `manual_resource_correction` | `resource`, numeric `delta`, personal `reason` |
| `manual_item_correction` | `item_id`, numeric `quantity`, personal `reason` |

`warrior_personal_name` is a snapshot of the explicitly personal warrior field,
including when the warrior leaves the roster. It is not a KB display name.
Entity references resolve afresh in the active locale. Missing or malformed
facts produce a localized unavailable notice; unknown legacy payloads survive
saving. These additions use the schema's existing open event objects and do
not change the file version or enable versions 1–4.
