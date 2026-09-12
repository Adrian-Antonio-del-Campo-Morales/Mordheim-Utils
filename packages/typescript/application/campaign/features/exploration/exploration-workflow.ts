import type {
  CampaignDocument,
  KnowledgeReader,
  OpenPayload,
} from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";
import { hireHireling } from "../../../../domain/campaign/kernel/hirelings";

interface CatalogueReader extends KnowledgeReader {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  campaignRows?(section: string): readonly OpenPayload[];
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
}
type Result =
  | { ok: true; document: CampaignDocument; summary: ExplorationSummary }
  | { ok: false; message: string };
type FollowUpResult =
  | { ok: true; document: CampaignDocument }
  | { ok: false; message: string };
export interface ExplorationSummary {
  readonly dice_count: number;
  readonly total: number;
  readonly shards: number;
  readonly special: string | null;
}
const HUMAN_WARBAND_GROUPS = new Set([
  "warband-group.human",
  "warband-group.chaos-human",
  "warband-group.human-mercenary",
  "warband-group.undead",
]);
export function explorationDiscardRequired(
  document: CampaignDocument,
): boolean {
  return document.campaign.special_rules.some((row) =>
    /extra die.*discard|dado extra.*descarta/i.test(String(row["text"] ?? "")),
  );
}

function catalogue(reader: CatalogueReader) {
  const document = reader.campaignSection?.("exploration-and-income");
  return (document?.["exploration"] ?? {}) as Readonly<Record<string, unknown>>;
}
function magicalArtefacts(reader: CatalogueReader) {
  return ((
    reader.campaignSection?.("exploration-and-income")?.[
      "magical_artefacts"
    ] as OpenPayload | undefined
  )?.["results"] ?? []) as OpenPayload[];
}
function eligibleHiredSwords(
  document: CampaignDocument,
  reader: CatalogueReader,
) {
  const groups = new Set(
      (reader.list?.("warband_group") ?? [])
        .filter(
          (row) =>
            Array.isArray(row["band_ids"]) &&
            (row["band_ids"] as unknown[])
              .map(String)
              .includes(document.campaign.identity.band_id),
        )
        .map((row) => String(row["id"] ?? "")),
    ),
    expression = (raw: unknown): boolean => {
      if (!raw || typeof raw !== "object") return true;
      const row = raw as OpenPayload;
      if (typeof row["band_id"] === "string")
        return row["band_id"] === document.campaign.identity.band_id;
      if (typeof row["group_id"] === "string")
        return groups.has(row["group_id"]);
      if (Array.isArray(row["any_of"])) return row["any_of"].some(expression);
      if (Array.isArray(row["all_of"])) return row["all_of"].every(expression);
      return row["not"] !== undefined ? !expression(row["not"]) : false;
    };
  return (
    reader.campaignRows?.("hired-swords-and-dramatis:hired_swords") ?? []
  ).filter((row) => {
    const eligibility = (row["eligibility"] ?? {}) as OpenPayload,
      allowedGroups = (eligibility["allow_groups"] ?? []) as unknown[],
      allowedBands = (eligibility["allow_band_ids"] ?? []) as unknown[],
      forbiddenGroups = (eligibility["forbid_groups"] ?? []) as unknown[],
      forbiddenBands = (eligibility["forbid_band_ids"] ?? []) as unknown[];
    return (
      !forbiddenBands
        .map(String)
        .includes(document.campaign.identity.band_id) &&
      !forbiddenGroups.map(String).some((id) => groups.has(id)) &&
      (!(allowedGroups.length || allowedBands.length) ||
        allowedBands.map(String).includes(document.campaign.identity.band_id) ||
        allowedGroups.map(String).some((id) => groups.has(id))) &&
      expression(eligibility["expression"])
    );
  });
}
export function eligibleExplorationHeroes(document: CampaignDocument): number {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle =
    post &&
    document.campaign.battles.find((row) => row.number === post.battle_number);
  if (!battle) return 0;
  let heroes = new Set(
    document.campaign.warriors
      .filter((row) => row.kind === "hero")
      .map((row) => row.id),
  );
  for (const row of battle.absentees ?? [])
    heroes.delete(String(row["id"] ?? ""));
  if (battle.participants?.length) {
    const participants = new Set(
      battle.participants.map((row) => String(row["id"] ?? "")),
    );
    heroes = new Set([...heroes].filter((id) => participants.has(id)));
  }
  if (battle.out_of_action_ids)
    for (const id of battle.out_of_action_ids) heroes.delete(id);
  return heroes.size;
}
export function explorationDiceCount(
  document: CampaignDocument,
  reader: CatalogueReader,
): number {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle =
    post &&
    document.campaign.battles.find((row) => row.number === post.battle_number);
  if (!battle) return 0;
  const exploration = catalogue(reader);
  let count = 0;
  for (const row of (exploration["dice_allocation"] ?? []) as readonly Readonly<
    Record<string, unknown>
  >[]) {
    if (
      row["eligible_warrior"] === "hero" &&
      row["condition"] === "survived_battle"
    )
      count += Number(row["dice"] ?? 0) * eligibleExplorationHeroes(document);
    if (
      row["eligible_warrior"] === "warband" &&
      row["condition"] === "warband_won_battle" &&
      battle.result === "win"
    )
      count += Number(row["dice"] ?? 0);
  }
  const scenario = post.step_state?.["scenario_exploration"] as
    | OpenPayload
    | undefined;
  return (
    Math.min(count, Number(exploration["max_dice"] ?? 6)) +
    Math.max(0, Number(scenario?.["extra_dice"] ?? 0)) +
    (explorationDiscardRequired(document) ? 1 : 0)
  );
}
function matchingResult(
  exploration: Readonly<Record<string, unknown>>,
  dice: readonly number[],
) {
  const counts = new Map<number, number>();
  for (const die of dice) counts.set(die, (counts.get(die) ?? 0) + 1);
  const match = [...counts]
    .filter(([, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1] || b[0] - a[0])[0];
  if (!match) return null;
  const pattern = Array.from({ length: match[1] }, () => match[0]).join(",");
  return (
    (
      (exploration["results"] ?? []) as readonly Readonly<
        Record<string, unknown>
      >[]
    ).find((row) => row["dice_pattern"] === pattern) ?? null
  );
}
export function applyExploration(
  document: CampaignDocument,
  reader: CatalogueReader,
  dice: readonly number[],
): Result {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!post)
    return { ok: false, message: "No pending post-battle exploration." };
  if (
    !post.experience_applied ||
    (post.pending_advances ?? []).some((row) => !row["committed"])
  )
    return {
      ok: false,
      message: "Resolve experience and every advance before exploration.",
    };
  if (
    (post.step_state?.["exploration"] as OpenPayload | undefined)?.["resolved"]
  )
    return { ok: false, message: "Exploration has already been resolved." };
  const required = explorationDiceCount(document, reader),
    discarded =
      explorationDiscardRequired(document) && dice.length === required - 1;
  if (
    (dice.length !== required && !discarded) ||
    dice.some((die) => !Number.isInteger(die) || die < 1 || die > 6)
  )
    return {
      ok: false,
      message: `Exploration requires exactly ${required} valid D6 results.`,
    };
  const exploration = catalogue(reader);
  const total = dice.reduce((sum, die) => sum + die, 0);
  const cell = ((
    exploration["shards_chart"] as Readonly<Record<string, unknown>>
  )?.["cells"] ?? []) as readonly Readonly<Record<string, unknown>>[];
  const shardRow = cell.find((row) => {
    const bounds = ((row["when"] as Readonly<Record<string, unknown>>)?.[
      "dice_total"
    ] ?? {}) as Readonly<Record<string, unknown>>;
    return (
      total >= Number(bounds["min"] ?? 0) &&
      (bounds["max"] == null || total <= Number(bounds["max"]))
    );
  });
  const shards = Number(shardRow?.["shards"] ?? 0);
  const special = matchingResult(exploration, dice);
  const followups = [...(post.pending_follow_ups ?? [])];
  if (special)
    followups.push({
      type: "exploration_followup",
      step: 3,
      result_id: String(special["id"] ?? ""),
      description: `${String(special["outcome"] ?? "")} special result: resolve the KB follow-up effects.`,
      queue: special["follow_up"] ? [special["follow_up"]] : [],
      messages: [],
      hero_id: null,
    });
  const summary = {
    dice_count: dice.length,
    total,
    shards,
    special: special ? String(special["outcome"] ?? "") : null,
  };
  const changed = {
    ...post,
    wyrdstone_delta: (post.wyrdstone_delta ?? 0) + shards,
    pending_follow_ups: followups,
    step_state: {
      ...(post.step_state ?? {}),
      exploration: { resolved: true, dice: [...dice], ...summary },
    },
    event_log: [
      ...(post.event_log ?? []),
      {
        step: 3,
        type: "exploration",
        description: `${shards} wyrdstone shard(s) found.`,
      },
      ...(special
        ? [
            {
              step: 3,
              type: "exploration_special",
              description: String(special["outcome"] ?? ""),
              result_id: String(special["id"] ?? ""),
            },
          ]
        : []),
    ],
  };
  const staged = withCampaign(document, {
    ...document.campaign,
    post_battles: document.campaign.post_battles.map((row) =>
      row === post ? changed : row,
    ),
  });
  if (!special) return { ok: true, summary, document: staged };
  const next = pendingFollowup(staged);
  return {
    ok: true,
    summary,
    document: processQueue(staged, reader, next.post!, next.followup!),
  };
}

function pendingFollowup(document: CampaignDocument) {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const followup = post?.pending_follow_ups?.find(
    (row) => row["type"] === "exploration_followup",
  );
  return { post, followup };
}
function processQueue(
  document: CampaignDocument,
  reader: CatalogueReader,
  post: NonNullable<ReturnType<typeof pendingFollowup>["post"]>,
  followup: OpenPayload,
): CampaignDocument {
  const queue = [...((followup["queue"] ?? []) as OpenPayload[])];
  const messages = [...((followup["messages"] ?? []) as string[])];
  let gold = post.gold_delta ?? 0;
  let shards = post.wyrdstone_delta ?? 0;
  let inventory = [...document.campaign.inventory];
  let warriors = [...document.campaign.warriors];
  let specialRules = [...document.campaign.special_rules];
  let uniqueRewardIds = [...(document.campaign.unique_reward_ids ?? [])];
  let pendingAdvances = [...(post.pending_advances ?? [])];
  const removedWarriorIds = new Set<string>();
  let current = { ...followup };
  const grantItem = (id: string, amount: number) => {
    if (amount <= 0) return;
    const known = reader.queryKnowledge({ id: { kind: "item_id", value: id } });
    const name = known.ok ? String(known.record.names["en"] ?? id) : id;
    const existing = inventory.find((row) => row.id === id);
    inventory = existing
      ? inventory.map((row) =>
          row.id === id
            ? { ...row, owned: row.owned + amount, stash: row.stash + amount }
            : row,
        )
      : [
          ...inventory,
          {
            id,
            name,
            category: String(
              known.ok ? (known.record.data["kind"] ?? "Reward") : "Reward",
            ),
            owned: amount,
            equipped: 0,
            stash: amount,
            value: 0,
          },
        ];
    messages.push(`+${amount} ${name}`);
  };
  const actor = (reference: unknown) => {
    let id = reference;
    if (typeof id === "string" && id.startsWith("$")) id = current["hero_id"];
    if (id === "leader") return warriors.find((row) => row.kind === "hero");
    return warriors.find((row) => row.id === id);
  };
  const addGroupMember = (id: string) => {
    warriors = warriors.map((row) => {
      if (row.id !== id) return row;
      const quantity = row.quantity ?? 1;
      return {
        ...row,
        quantity: quantity + 1,
        equipment: row.equipment.map((item) =>
          item.per_model && item.transferable === false
            ? {
                ...item,
                quantity: item.quantity + Math.max(1, item.quantity / quantity),
              }
            : item,
        ),
      };
    });
  };
  const grantExperience = (recipient: string, value: number) => {
    const targets =
      recipient === "leader"
        ? warriors.filter((row) => row.kind === "hero").slice(0, 1)
        : recipient === "heroes"
          ? warriors.filter((row) => row.kind === "hero")
          : warriors.filter((row) => row.id === recipient);
    const eligible = targets.filter((warrior) => {
      const profile = reader.queryKnowledge({
        id: { kind: "profile_id", value: String(warrior.profile_id ?? "") },
      });
      return (
        !profile.ok ||
        (profile.record.data["can_gain_experience"] !== false &&
          profile.record.data["type"] !== "animal")
      );
    });
    const prior = new Map(eligible.map((row) => [row.id, row.experience]));
    warriors = warriors.map((row) =>
      eligible.some((target) => target.id === row.id)
        ? { ...row, experience: row.experience + value }
        : row,
    );
    const tables = (reader.campaignSection?.("experience-and-advances")?.[
      "advance_thresholds"
    ] ?? {}) as OpenPayload;
    for (const warrior of warriors.filter((row) => prior.has(row.id))) {
      const kind =
          warrior.kind === "hero" || warrior.kind === "hireling"
            ? "hero"
            : "henchman",
        thresholds = (tables[kind] ?? []) as unknown[];
      for (const threshold of thresholds
        .map(Number)
        .filter(
          (threshold) =>
            prior.get(warrior.id)! < threshold &&
            threshold <= warrior.experience &&
            !pendingAdvances.some(
              (row) =>
                String(row["warrior_id"]) === warrior.id &&
                Number(row["threshold"]) === threshold,
            ),
        ))
        pendingAdvances.push({
          warrior_id: warrior.id,
          warrior_name: warrior.name,
          table: warrior.kind,
          threshold,
          roll_total: null,
          subroll: null,
          committed: false,
          applied_label: "",
        });
    }
    messages.push(`+${value} XP to ${recipient}`);
  };
  while (queue.length) {
    const node = queue.shift()!;
    const kind = String(node["type"] ?? "");
    if (kind === "sequence") {
      queue.unshift(...((node["steps"] ?? []) as OpenPayload[]));
      continue;
    }
    if (kind === "conditional") {
      const cases = (node["cases"] ?? []) as OpenPayload[];
      const selected = cases.find((item) => {
        const when = (item["when"] ?? {}) as OpenPayload;
        const actual =
          when["field"] === "context.band_id"
            ? document.campaign.identity.band_id
            : Number(current["last_roll"] ?? 0);
        return when["operator"] === "equals"
          ? String(actual) === String(when["value"])
          : when["operator"] === "in" &&
              ((when["value"] ?? []) as unknown[])
                .map(String)
                .includes(String(actual));
      });
      queue.unshift(
        ...((selected?.["then"] ?? node["default"] ?? []) as OpenPayload[]),
      );
      continue;
    }
    if (kind === "choose_henchman_group") {
      const human = reader
        .list?.("warband_group")
        .some(
          (row) =>
            HUMAN_WARBAND_GROUPS.has(String(row["id"] ?? "")) &&
            Array.isArray(row["band_ids"]) &&
            (row["band_ids"] as unknown[])
              .map(String)
              .includes(document.campaign.identity.band_id),
        );
      const options = human
        ? warriors
            .filter((row) => {
              if (row.kind !== "henchman") return false;
              const profile = reader.queryKnowledge({
                id: { kind: "profile_id", value: String(row.profile_id ?? "") },
              });
              return (
                profile.ok &&
                Array.isArray(profile.record.data["equipment_access"]) &&
                profile.record.data["equipment_access"].length > 0
              );
            })
            .map((row) => ({
              id: row.id,
              label: row.name,
              then: [{ type: "prisoner_join_group", warrior_id: row.id }],
            }))
        : [];
      if (node["allow_decline"] !== false)
        options.push({
          id: "decline",
          label: "Do not recruit the prisoner",
          then: [],
        });
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_option",
          label: String(node["label"] ?? "Choose a Henchman group"),
          options,
        },
      };
      break;
    }
    if (kind === "choose_warriors") {
      const forbidden = new Set(
        ((node["exclude_profiles"] ?? []) as unknown[]).map((value) =>
          String(value).toLowerCase(),
        ),
      );
      const options = warriors
        .filter((row) => !forbidden.has(row.profile_name.toLowerCase()))
        .map((row) => ({ id: row.id, label: row.name }));
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_warriors",
          label: String(node["label"] ?? "Choose warriors"),
          options,
          maximum: Number(node["maximum"] ?? 1),
          text: String(node["text"] ?? "Selected: {warriors}"),
          expires_after_battles: node["expires_after_battles"],
        },
      };
      break;
    }
    if (kind === "choose_equipment") {
      const options = warriors.flatMap((warrior) =>
        warrior.equipment
          .filter((item) => item.quantity > 0)
          .map((item) => ({
            id: `${warrior.id}:${item.item_id}`,
            label: `${warrior.name} — ${item.name}`,
            hero_id: warrior.id,
            then: [
              {
                type: "grant_rule",
                recipient: "hero",
                text: String(node["text"] ?? "").replace("{item}", item.name),
              },
            ],
          })),
      );
      if (!options.length) {
        messages.push("No equipped item is eligible; reward skipped");
        continue;
      }
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_option",
          label: String(node["label"] ?? "Choose equipment"),
          options,
        },
      };
      break;
    }
    if (kind === "choose_hireling") {
      const options = eligibleHiredSwords(document, reader)
        .filter(
          (row) =>
            !warriors.some(
              (warrior) => warrior.profile_id === row["profile_id"],
            ),
        )
        .map((row) => {
          const id = String(row["profile_id"]),
            profile = reader.queryKnowledge({
              id: { kind: "hireling_id", value: id },
            });
          return {
            id,
            label: String(profile.ok ? (profile.record.names["en"] ?? id) : id),
            then: [
              {
                type: "hire_free_hireling",
                profile_id: id,
                upkeep_resources: (row["upkeep"] as OpenPayload | undefined)?.[
                  "resources"
                ],
              },
            ],
          };
        });
      if (!options.length) {
        messages.push("No legal Hired Sword is currently available");
        continue;
      }
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_option",
          label: String(node["label"] ?? "Choose a Hired Sword"),
          options,
        },
      };
      break;
    }
    if (kind === "magical_artefact_table") {
      const artefacts = magicalArtefacts(reader),
        identifiers = new Set(
          artefacts.map(
            (row) =>
              `magical_artefact.${String(row["id"] ?? "").replace("campaign.magical-artefact.", "")}`,
          ),
        ),
        unavailable = new Set([
          ...uniqueRewardIds,
          ...inventory.filter((row) => row.owned > 0).map((row) => row.id),
        ]);
      if (
        identifiers.size &&
        [...identifiers].every((id) => unavailable.has(id))
      ) {
        current = {
          ...current,
          queue,
          messages,
          pending: {
            kind: "choose_option",
            label: "No unique artefacts remain available.",
            options: [
              {
                id: "artefacts-exhausted",
                label: "Record resolution at the table",
                then: [],
              },
            ],
          },
        };
        break;
      }
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "roll",
          label: "Magical artefact roll",
          dice_count: 1,
          dice_sides: 6,
          spec: { type: "magical_artefact" },
        },
      };
      break;
    }
    if (kind === "choose_one" && !warriors.some((row) => row.kind === "hero")) {
      messages.push("No eligible hero for the choice; skipped");
      continue;
    }
    if (kind === "choose_one" || kind === "choose_option") {
      current = {
        ...current,
        queue,
        messages,
        pending:
          kind === "choose_one"
            ? {
                kind: "choose_hero",
                label: String(node["bind"] ?? "Choose a Hero"),
              }
            : {
                kind: "choose_option",
                label: String(node["label"] ?? "Choose an outcome"),
                options: node["options"] ?? [],
              },
      };
      break;
    }
    if (kind === "characteristic_test" || kind === "roll_table") {
      const dice = (node["dice"] ?? {}) as OpenPayload;
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "roll",
          label:
            kind === "characteristic_test"
              ? `${String(node["characteristic"])} test`
              : "Follow-up roll",
          dice_count: Number(dice["count"] ?? 1),
          dice_sides: Number(dice["sides"] ?? 6),
          spec: node,
        },
      };
      break;
    }
    if (
      (kind === "grant" || kind === "reward.grant") &&
      node["recipient"] === "hero" &&
      !warriors.some((row) => row.kind === "hero")
    ) {
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_option",
          label: "No Hero is available for this reward.",
          options: [
            {
              id: "no-hero-resolution",
              label: "Record resolution at the table",
              then: [],
            },
          ],
        },
      };
      break;
    }
    if (
      (kind === "grant" || kind === "reward.grant") &&
      node["recipient"] === "hero" &&
      !current["hero_id"]
    ) {
      current = {
        ...current,
        queue,
        messages,
        pending: {
          kind: "choose_hero",
          label: String(
            node["label"] ?? "Choose the Hero who receives this reward",
          ),
          continuation: node,
        },
      };
      break;
    }
    if (kind === "grant" || kind === "reward.grant") {
      const recipient =
        node["recipient"] === "hero"
          ? String(current["hero_id"] ?? "hero")
          : String(node["recipient"] ?? "warband");
      const resources = (node["resources"] ?? {}) as Record<string, unknown>;
      let deferred = false;
      const resourceEntries = Object.entries(resources);
      for (const [index, [resource, raw]] of resourceEntries.entries()) {
        const spec = (
          typeof raw === "object" && raw ? raw : { kind: "fixed", value: raw }
        ) as OpenPayload;
        if (spec["kind"] !== "fixed") {
          const dice = (spec["dice"] ?? {}) as OpenPayload,
            continuation = {
              ...node,
              resources: Object.fromEntries(resourceEntries.slice(index + 1)),
              items: node["items"] ?? [],
            };
          current = {
            ...current,
            queue,
            messages,
            pending: {
              kind: "roll",
              label: `${resource} reward`,
              dice_count: Number(dice["count"] ?? 1),
              dice_sides: Number(dice["sides"] ?? 6),
              resource,
              recipient,
              multiplier: Number(spec["multiplier"] ?? 1),
              offset: Number(spec["offset"] ?? 0),
              continuation,
            },
          };
          deferred = true;
          break;
        }
        const value = Number(spec["value"] ?? 0);
        if (resource === "gold_crowns") gold += value;
        else if (resource === "wyrdstone_fragments") shards += value;
        else if (resource === "experience") grantExperience(recipient, value);
        else if (resource.startsWith("item:"))
          grantItem(resource.slice(5), value);
        else messages.push(`${resource}: ${value} (recorded as a note)`);
      }
      if (deferred) break;
      if (node["note"]) messages.push(String(node["note"]));
      const items = (node["items"] ?? []) as OpenPayload[];
      for (const [index, item] of items.entries()) {
        const quantity = (item["quantity"] ?? {}) as OpenPayload;
        const id = String(item["item_id"]);
        if (quantity["kind"] !== "fixed") {
          const dice = (quantity["dice"] ?? {}) as OpenPayload,
            continuation = {
              ...node,
              resources: {},
              items: items.slice(index + 1),
            };
          current = {
            ...current,
            queue,
            messages,
            pending: {
              kind: "roll",
              label: `${id} quantity roll`,
              dice_count: Number(dice["count"] ?? 1),
              dice_sides: Number(dice["sides"] ?? 6),
              resource: `item:${id}`,
              recipient,
              multiplier: Number(quantity["multiplier"] ?? 1),
              offset: Number(quantity["offset"] ?? 0),
              continuation,
            },
          };
          deferred = true;
          break;
        }
        grantItem(id, Number(quantity["value"] ?? 1));
      }
      if (deferred) break;
      continue;
    }
    if (kind === "warrior.miss_games") {
      const target = actor(node["subject"]);
      const games = node["games"] as OpenPayload | number | undefined;
      const value =
        typeof games === "object"
          ? Number(games["value"] ?? 1)
          : Number(games ?? 1);
      if (target) {
        warriors = warriors.map((row) =>
          row.id === target.id
            ? {
                ...row,
                games_to_miss: (row.games_to_miss ?? 0) + value,
                absence_reason: String(node["reason"] ?? "Injury"),
              }
            : row,
        );
        messages.push(`${target.name} misses ${value} game(s)`);
      }
      continue;
    }
    if (kind === "roster.remove_warrior") {
      const target = actor(node["subject"]);
      if (!target) {
        messages.push("No warrior was selected for removal");
        continue;
      }
      const lost = new Map<string, number>();
      for (const item of target.equipment)
        if (item.transferable !== false)
          lost.set(item.item_id, (lost.get(item.item_id) ?? 0) + item.quantity);
      inventory = inventory
        .map((row) => {
          const quantity = lost.get(row.id) ?? 0;
          return quantity
            ? {
                ...row,
                owned: Math.max(0, row.owned - quantity),
                equipped: Math.max(0, row.equipped - quantity),
              }
            : row;
        })
        .filter((row) => row.owned > 0);
      warriors = warriors.filter((row) => row.id !== target.id);
      pendingAdvances = pendingAdvances.filter(
        (row) => row["warrior_id"] !== target.id || row["committed"],
      );
      removedWarriorIds.add(target.id);
      messages.push(
        String(node["note"] ?? `${target.name} leaves the warband`),
      );
      continue;
    }
    if (kind === "prisoner_join_group") {
      const target = warriors.find(
        (row) =>
          row.id === String(node["warrior_id"] ?? "") &&
          row.kind === "henchman",
      );
      const band = reader.queryKnowledge({
        id: { kind: "band_id", value: document.campaign.identity.band_id },
      });
      const members =
        band.ok &&
        Array.isArray(
          (band.record.data["roster"] as OpenPayload | undefined)?.["members"],
        )
          ? ((band.record.data["roster"] as OpenPayload)[
              "members"
            ] as OpenPayload[])
          : [];
      const member =
        target &&
        members.find((row) => row["profile_id"] === target.profile_id);
      const models = warriors.reduce(
          (total, row) => total + (row.quantity ?? 1),
          0,
        ),
        taken = target
          ? warriors
              .filter((row) => row.profile_id === target.profile_id)
              .reduce((total, row) => total + (row.quantity ?? 1), 0)
          : 0,
        maximum = Number(member?.["maximum"] ?? Infinity),
        groupMaximum = Number(
          (member?.["group_size"] as OpenPayload | undefined)?.["maximum"] ??
            Infinity,
        );
      if (
        !target ||
        models >= document.campaign.configuration.maximum_models ||
        taken >= maximum ||
        (target.quantity ?? 1) >= groupMaximum
      ) {
        messages.push("The prisoner cannot join that group");
        continue;
      }
      addGroupMember(target.id);
      messages.push(
        `One member joined ${target.name} for 0 gc; equipment remains pending.`,
      );
      continue;
    }
    if (kind === "hire_free_hireling") {
      const upkeep = Object.entries(
        (node["upkeep_resources"] ?? {}) as OpenPayload,
      ).flatMap(([id, row]) => {
        const cost = (row as OpenPayload)?.["cost"];
        return Number.isInteger(cost) ? [[id, Number(cost)] as const] : [];
      });
      const hired = hireHireling(
        withCampaign(document, { ...document.campaign, warriors }),
        {
          profile_id: String(node["profile_id"] ?? ""),
          fee: 0,
          upkeep_resources: upkeep,
        },
        reader,
      );
      if (!hired.ok) {
        messages.push("The selected Hired Sword could not be added");
        continue;
      }
      warriors = hired.state.campaign.warriors.map((row) =>
        row.profile_id === node["profile_id"]
          ? {
              ...row,
              special_rules: [
                ...(row.special_rules ?? []),
                "Returning a Favour: no hiring fee; upkeep begins after the next battle",
              ],
            }
          : row,
      );
      messages.push(
        `${warriors[warriors.length - 1]?.name ?? "Hired Sword"} joins for the next battle without a hiring fee`,
      );
      continue;
    }
    if (kind === "grant_rule") {
      const text = String(node["text"] ?? "").trim();
      if (node["recipient"] === "hero") {
        const target = actor("$hero_id");
        if (!target) {
          current = {
            ...current,
            queue,
            messages,
            pending: {
              kind: "choose_hero",
              label: String(node["label"] ?? "Choose a Hero"),
              continuation: node,
            },
          };
          break;
        }
        warriors = warriors.map((row) =>
          row.id === target.id
            ? {
                ...row,
                special_rules: [
                  ...new Set([...(row.special_rules ?? []), text]),
                ],
                skill_access: [
                  ...new Set([
                    ...(row.skill_access ?? []),
                    ...(text.startsWith("Academic skill access")
                      ? ["Academic"]
                      : []),
                    ...(text.startsWith("Combat skill access")
                      ? ["Combat"]
                      : []),
                  ]),
                ],
                skills: text.startsWith("Haggle")
                  ? [...new Set([...row.skills, "Haggle"])]
                  : row.skills,
              }
            : row,
        );
        messages.push(`${target.name}: ${text}`);
      } else {
        if (text && !specialRules.some((row) => row["text"] === text))
          specialRules.push({
            source: String(current["result_id"] ?? "exploration"),
            text,
            expires_after_battles: node["expires_after_battles"],
            consume_when_opponent_contains:
              node["consume_when_opponent_contains"] ?? [],
          });
        messages.push(text);
      }
      continue;
    }
    if (kind === "grant_compound_item") {
      const id = String(node["reward_id"] ?? "");
      const name = String(node["name"] ?? id);
      const existing = inventory.find((row) => row.id === id);
      inventory = existing
        ? inventory.map((row) =>
            row.id === id
              ? { ...row, owned: row.owned + 1, stash: row.stash + 1 }
              : row,
          )
        : [
            ...inventory,
            {
              id,
              name,
              category: String(node["category"] ?? "Weapon"),
              owned: 1,
              equipped: 0,
              stash: 1,
              value: 0,
              special_rules: (node["rules"] ?? []) as string[],
              base_item_id: String(node["base_item_id"] ?? ""),
            },
          ];
      messages.push(`+1 ${name} (stash)`);
      continue;
    }
    if (kind === "grant_special_item") {
      const id = String(node["item_id"] ?? "");
      const name = String(node["name"] ?? id);
      if (
        uniqueRewardIds.includes(id) ||
        inventory.some((row) => row.id === id && row.owned > 0)
      ) {
        messages.push(`${name} already appeared; reward skipped`);
        continue;
      }
      const toStash = node["recipient"] === "stash";
      const target = actor("$hero_id");
      if (!toStash && !target && !warriors.some((row) => row.kind === "hero")) {
        current = {
          ...current,
          queue,
          messages,
          pending: {
            kind: "choose_option",
            label: "No Hero is available for this reward.",
            options: [
              {
                id: "keep-in-stash",
                label: "Keep the item in the stash",
                then: [{ ...node, recipient: "stash" }],
              },
            ],
          },
        };
        break;
      }
      if (!toStash && !target) {
        current = {
          ...current,
          queue,
          messages,
          pending: {
            kind: "choose_hero",
            label: String(node["label"] ?? "Choose a bearer"),
            continuation: node,
          },
        };
        break;
      }
      const rules = String(node["text"] ?? "") ? [String(node["text"])] : [];
      inventory = [
        ...inventory,
        {
          id,
          name,
          category: "Magical Artefact",
          owned: 1,
          equipped: toStash ? 0 : 1,
          stash: toStash ? 1 : 0,
          value: 0,
          rarity: "Unique",
          special_rules: rules,
        },
      ];
      if (target && !toStash)
        warriors = warriors.map((row) =>
          row.id === target.id
            ? {
                ...row,
                equipment: [
                  ...row.equipment,
                  {
                    item_id: id,
                    name,
                    quantity: 1,
                    acquisition: "scenario_reward",
                    unit_cost: 0,
                    per_model: false,
                    transferable: true,
                    special_rules: rules,
                  },
                ],
              }
            : row,
        );
      uniqueRewardIds.push(id);
      messages.push(
        toStash ? `${name} kept in stash` : `${target!.name} receives ${name}`,
      );
      continue;
    }
    if (kind === "grant_free_profile") {
      const wanted = String(node["profile_name"] ?? "").toLowerCase(),
        profile = (reader.list?.("profile") ?? []).find(
          (row) =>
            row["band_id"] === document.campaign.identity.band_id &&
            [
              String(row["name"] ?? ""),
              String((row["names"] as OpenPayload | undefined)?.["en"] ?? ""),
            ].some((name) => name.toLowerCase().includes(wanted)),
        );
      const profileId = String(profile?.["id"] ?? ""),
        band = reader.queryKnowledge({
          id: { kind: "band_id", value: document.campaign.identity.band_id },
        }),
        member =
          band.ok &&
          Array.isArray(
            (band.record.data["roster"] as OpenPayload | undefined)?.[
              "members"
            ],
          )
            ? (
                (band.record.data["roster"] as OpenPayload)[
                  "members"
                ] as OpenPayload[]
              ).find((row) => row["profile_id"] === profileId)
            : undefined,
        models = warriors.reduce(
          (total, row) => total + (row.quantity ?? 1),
          0,
        ),
        taken = warriors
          .filter((row) => row.profile_id === profileId)
          .reduce((total, row) => total + (row.quantity ?? 1), 0),
        maximum = Number(member?.["maximum"] ?? Infinity),
        existing = warriors.find(
          (row) => row.kind === "henchman" && row.profile_id === profileId,
        ),
        groupMaximum = Number(
          (member?.["group_size"] as OpenPayload | undefined)?.["maximum"] ??
            Infinity,
        );
      if (
        !profile ||
        !member ||
        models >= document.campaign.configuration.maximum_models ||
        taken >= maximum ||
        (existing && (existing.quantity ?? 1) >= groupMaximum)
      ) {
        messages.push(
          `No legal roster slot/profile for free ${String(node["profile_name"] ?? "")}`,
        );
        continue;
      }
      if (existing) {
        addGroupMember(existing.id);
        messages.push(
          `One free ${existing.profile_name} joined ${existing.name}`,
        );
        continue;
      }
      const stats = Object.fromEntries(
        Object.entries(
          (profile["characteristics"] ?? {}) as OpenPayload,
        ).filter(
          (entry): entry is [string, number] => typeof entry[1] === "number",
        ),
      );
      const name = String(
          (profile["names"] as OpenPayload | undefined)?.["en"] ??
            profile["name"] ??
            profileId,
        ),
        equipment = (
          Array.isArray(profile["fixed_equipment"])
            ? profile["fixed_equipment"]
            : []
        )
          .filter((id): id is string => typeof id === "string")
          .map((item_id) => {
            const item = reader.queryKnowledge({
              id: { kind: "item_id", value: item_id },
            });
            return {
              item_id,
              name: String(
                item.ok ? (item.record.names["en"] ?? item_id) : item_id,
              ),
              quantity: 1,
              acquisition: "fixed",
              per_model: true,
            };
          });
      warriors = [
        ...warriors,
        {
          id: `${profileId}#reward-${warriors.filter((row) => row.profile_id === profileId).length + 1}`,
          name: `${name} Group`,
          profile_name: name,
          kind: "henchman",
          stats,
          equipment,
          skills: [],
          experience: Number(profile["experience"] ?? 0),
          quantity: 1,
          cost: Number(profile["cost"] ?? 0),
          profile_id: profileId,
          skill_access: [],
        },
      ];
      messages.push(`One free ${name} joined the warband`);
      continue;
    }
    current = {
      ...current,
      queue,
      messages: [...messages, `Pending unsupported desktop follow-up: ${kind}`],
      pending: { kind: "external", label: `Resolve ${kind} at the table` },
    };
    break;
  }
  const finished = !queue.length && !current["pending"];
  // Match by id: the caller may pass a spread copy of the parked follow-up
  // (`{...followup}`), so object identity is not reliable here.
  const followId = String(followup["id"] ?? "");
  const followups = (
    finished
      ? (post.pending_follow_ups ?? []).filter(
          (row) => String(row["id"] ?? "") !== followId,
        )
      : (post.pending_follow_ups ?? []).map((row) =>
          String(row["id"] ?? "") === followId
            ? { ...current, queue, messages }
            : row,
        )
  ).filter((row) => !removedWarriorIds.has(String(row["warrior_id"] ?? "")));
  const changedPost = {
    ...post,
    gold_delta: gold,
    wyrdstone_delta: shards,
    pending_advances: pendingAdvances,
    pending_follow_ups: followups,
    equipment_obligations: (post.equipment_obligations ?? []).filter(
      (row) => !removedWarriorIds.has(String(row["warrior_id"] ?? "")),
    ),
    searches: Object.fromEntries(
      Object.entries(post.searches ?? {}).filter(
        ([id]) => !removedWarriorIds.has(id),
      ),
    ),
    ...(finished
      ? {
          event_log: [
            ...(post.event_log ?? []),
            {
              step: 3,
              type: "exploration_followup",
              description: messages.join("; ") || "follow-up complete",
            },
          ],
        }
      : {}),
  };
  return withCampaign(document, {
    ...document.campaign,
    inventory,
    warriors,
    special_rules: specialRules,
    unique_reward_ids: uniqueRewardIds,
    post_battles: document.campaign.post_battles.map((row) =>
      row === post ? changedPost : row,
    ),
  });
}
export function continueExploration(
  document: CampaignDocument,
  reader: CatalogueReader,
  input: {
    roll?: number;
    hero_id?: string;
    option_id?: string;
    warrior_ids?: readonly string[];
    confirm_external?: boolean;
  },
): FollowUpResult {
  const { post, followup } = pendingFollowup(document);
  if (!post || !followup)
    return { ok: false, message: "No exploration follow-up is pending." };
  let current = { ...followup };
  const pending = (current["pending"] ?? null) as OpenPayload | null;
  if (!pending)
    return {
      ok: true,
      document: processQueue(document, reader, post, current),
    };
  const queue = [...((current["queue"] ?? []) as OpenPayload[])];
  const messages = [...((current["messages"] ?? []) as string[])];
  if (pending["kind"] === "choose_hero") {
    if (
      !document.campaign.warriors.some(
        (row) => row.id === input.hero_id && row.kind === "hero",
      )
    )
      return {
        ok: false,
        message: "Choose a Hero still present in the warband.",
      };
    current = { ...current, hero_id: input.hero_id };
    const continuation = pending["continuation"];
    if (continuation) queue.unshift(continuation as OpenPayload);
  } else if (pending["kind"] === "choose_option") {
    const option = ((pending["options"] ?? []) as OpenPayload[]).find(
      (row) => String(row["id"]) === input.option_id,
    );
    if (!option)
      return { ok: false, message: "Choose one of the available outcomes." };
    if (typeof option["hero_id"] === "string")
      current = { ...current, hero_id: option["hero_id"] };
    messages.push(String(option["label"] ?? input.option_id));
    queue.unshift(...((option["then"] ?? []) as OpenPayload[]));
  } else if (pending["kind"] === "choose_warriors") {
    const selected = [...new Set(input.warrior_ids ?? [])],
      eligible = new Set(
        ((pending["options"] ?? []) as OpenPayload[]).map((row) =>
          String(row["id"]),
        ),
      ),
      maximum = Number(pending["maximum"] ?? 1);
    if (
      selected.length > maximum ||
      selected.some(
        (id) =>
          !eligible.has(id) ||
          !document.campaign.warriors.some((row) => row.id === id),
      )
    )
      return {
        ok: false,
        message: `Choose at most ${maximum} eligible warriors.`,
      };
    const names = document.campaign.warriors
      .filter((row) => selected.includes(row.id))
      .map((row) => row.name);
    queue.unshift({
      type: "grant_rule",
      recipient: "warband",
      text: String(pending["text"] ?? "").replace(
        "{warriors}",
        names.join(", ") || "none",
      ),
      expires_after_battles: pending["expires_after_battles"],
    });
  } else if (pending["kind"] === "roll") {
    const count = Number(pending["dice_count"] ?? 1),
      sides = Number(pending["dice_sides"] ?? 6),
      roll = input.roll;
    if (
      !Number.isInteger(roll) ||
      Number(roll) < count ||
      Number(roll) > count * sides
    )
      return {
        ok: false,
        message: `Roll must be between ${count} and ${count * sides}.`,
      };
    const spec = (pending["spec"] ?? {}) as OpenPayload;
    current = { ...current, last_roll: roll };
    if (pending["continuation"]) {
      queue.unshift(pending["continuation"] as OpenPayload);
      queue.unshift({
        type: "grant",
        recipient: pending["recipient"],
        resources: {
          [String(pending["resource"])]: {
            kind: "fixed",
            value:
              Number(roll) * Number(pending["multiplier"] ?? 1) +
              Number(pending["offset"] ?? 0),
          },
        },
      });
    } else if (spec["type"] === "magical_artefact") {
      const artefact = magicalArtefacts(reader).find(
        (row) => Number(row["roll"] ?? 0) === roll,
      );
      if (!artefact)
        messages.push(`Magical artefact roll ${roll} has no result`);
      else {
        const id = `magical_artefact.${String(artefact["id"] ?? "").replace("campaign.magical-artefact.", "")}`;
        if (
          document.campaign.unique_reward_ids?.includes(id) ||
          document.campaign.inventory.some(
            (row) => row.id === id && row.owned > 0,
          )
        ) {
          messages.push(
            `${String(artefact["result"] ?? id)} already appeared; roll again`,
          );
          queue.unshift({ type: "magical_artefact_table" });
        } else
          queue.unshift({
            type: "grant_special_item",
            recipient: "hero",
            label: `Choose the bearer of ${String(artefact["result"] ?? id)}`,
            item_id: id,
            name: String(artefact["result"] ?? id),
            text: String(artefact["effect"] ?? ""),
          });
      }
    } else if (spec["type"] === "resource_roll")
      queue.unshift({
        type: "grant",
        recipient: spec["recipient"],
        resources: {
          [String(spec["resource"])]: {
            kind: "fixed",
            value:
              Number(roll) * Number(spec["multiplier"] ?? 1) +
              Number(spec["offset"] ?? 0),
          },
        },
      });
    else if (spec["type"] === "roll_table") {
      const branch = ((spec["branches"] ?? []) as OpenPayload[]).find((row) => {
        const when = (row["when"] ?? {}) as OpenPayload;
        return (
          Number(roll) >= Number(when["min"] ?? 0) &&
          (when["max"] == null || Number(roll) <= Number(when["max"]))
        );
      });
      queue.unshift(
        ...((branch?.["then"] ?? spec["default"] ?? []) as OpenPayload[]),
      );
    } else if (spec["type"] === "characteristic_test") {
      let reference = spec["actor"];
      if (typeof reference === "string" && reference.startsWith("$"))
        reference = current["hero_id"];
      const target =
        reference === "leader"
          ? document.campaign.warriors.find((row) => row.kind === "hero")
          : document.campaign.warriors.find((row) => row.id === reference);
      const keys: Record<string, string> = {
        toughness: "T",
        leadership: "Ld",
        strength: "S",
        initiative: "I",
        weapon_skill: "WS",
        attacks: "A",
        wounds: "W",
        movement: "M",
        ballistic_skill: "BS",
      };
      const key =
        keys[String(spec["characteristic"])] ?? String(spec["characteristic"]);
      const value =
          Number(target?.stats[key] ?? 3) +
          Number(target?.stat_modifiers?.[key] ?? 0),
        success =
          String(spec["success_when"] ?? "") === "roll_less_than_characteristic"
            ? Number(roll) < value
            : Number(roll) <= value;
      messages.push(
        `${target?.name ?? "test"} ${success ? "succeeded" : "failed"} (${roll} vs ${value})`,
      );
      queue.unshift(
        ...((spec[success ? "on_success" : "on_failure"] ??
          []) as OpenPayload[]),
      );
    }
  } else if (pending["kind"] === "external" && input.confirm_external)
    messages.push(String(pending["label"]));
  else
    return { ok: false, message: "Complete the pending exploration choice." };
  current = { ...current, queue, messages };
  delete current["pending"];
  const staged = withCampaign(document, {
    ...document.campaign,
    post_battles: document.campaign.post_battles.map((row) =>
      row === post
        ? {
            ...post,
            pending_follow_ups: (post.pending_follow_ups ?? []).map((item) =>
              item === followup ? current : item,
            ),
          }
        : row,
    ),
  });
  const stagedContext = pendingFollowup(staged);
  return {
    ok: true,
    document: processQueue(
      staged,
      reader,
      stagedContext.post!,
      stagedContext.followup!,
    ),
  };
}
