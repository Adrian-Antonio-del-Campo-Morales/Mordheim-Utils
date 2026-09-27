/**
 * T09 mandatory warband variants: published options, their construction
 * consequences and their persistence.
 *
 * The fixtures mirror the two shapes the promoted KB publishes:
 *
 * - `background.<slug>` (Khemri, Lahmian Brotherhood): the option declares the
 *   slots it opens (`roster_members`) and the `<slug>-<family>-equipment-list`
 *   lists it activates; the members it does not open keep their published `0/0`
 *   slot. The ids come from the shared Python compiler
 *   (`compiler.foreign-or-native-background` consumes `background.foreign` /
 *   `background.native` verbatim);
 * - `<bloodline>` (Chaos in the Streets, Undead Bloodlines): the plain option id
 *   is the profile's own `bloodline`, the chosen Vampire is the single warband
 *   leader (`minimum: 1, maximum: 1`) and the other bloodline stays locked
 *   (`band--choose-bloodline`).
 *
 * The real bands are swept end to end in `construction-kb-sweep.test.ts`; the
 * canonical option ids are gated against the KB in
 * `tests/python/construction/test_construction_variants.py`.
 *
 * Purity: plain Node, fake reader — no React, no DOM, no filesystem.
 */

import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file/index";
import type { KnowledgeQuery } from "@domain/campaign/kernel/ports";
import type { CampaignDocument, KnowledgeReader, KnowledgeResult } from "@domain/campaign/kernel/usecases";
import { createDraft } from "@domain/campaign/kernel/create-draft";
import { composeDraft } from "@domain/campaign/kernel/create-draft";
import { commitInitialWarband } from "@domain/campaign/kernel/commit-warband";
import type { Campaign } from "@domain/campaign/kernel/state";
import {
  bandFactsOf,
  equipmentIssueFor,
  profileFactsOf,
  rosterIssuesOf,
  variantFrameOf,
  variantGatesOf,
  variantRequirementOf,
  variantSlotOf,
} from "@domain/campaign/construction";
import { warbandVariants } from "@domain/campaign/band-variants";

/** Fake reader: rows keyed by `family:id`, exactly like the adapter's. */
function makeReader(rows: Record<string, Record<string, unknown>>): KnowledgeReader {
  const reader: KnowledgeReader = {
    queryKnowledge: (query: KnowledgeQuery): KnowledgeResult => {
      for (const [id, kind] of [
        ["band_id", "band"],
        ["profile_id", "profile"],
        ["item_id", "item"],
      ] as const) {
        if (query.id.kind !== id) continue;
        const row = rows[`${kind}:${query.id.value}`];
        if (!row) return { ok: false, reason: "not_found" };
        return {
          ok: true,
          record: {
            kind,
            id: query.id,
            names: (row.names as Record<string, string>) ?? { en: String(row.name ?? query.id.value) },
            data: row,
          },
        };
      }
      return { ok: false, reason: "not_found" };
    },
    queryMany: (queries) => queries.map((query) => reader.queryKnowledge(query)),
    list: () => [],
  };
  return reader;
}

const BACKGROUND_BAND = "lahmian-fixture";
const BLOODLINE_BAND = "bloodlines-fixture";

function profile(
  bandId: string,
  id: string,
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    id,
    band_id: bandId,
    collection: "trollheim",
    type: "henchman",
    name: id,
    cost: 25,
    characteristics: { M: 4, WS: 3, BS: 0, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    equipment_lists: [],
    equipment_access: [],
    equipment_forbids: [],
    fixed_equipment: [],
    skill_access: [],
    rule_ids: [],
    combat_traits: {},
    ...overrides,
  };
}

const UNDEAD_LIST = "Use only the Undead Equipment List assigned by the selected Foreign or Native background.";

function backgroundReader(): KnowledgeReader {
  return makeReader({
    [`band:${BACKGROUND_BAND}`]: {
      id: BACKGROUND_BAND,
      name: "Lahmian Fixture",
      collection: "trollheim",
      rule_ids: ["band--background-selection"],
      roster: {
        minimum_models: 2,
        maximum_models: 15,
        starting_gold: 500,
        requires_variant_selection: true,
        members: [
          { profile_id: "vampire", minimum: 1, maximum: 1 },
          { profile_id: "slaves", minimum: 0, maximum: 0 },
          { profile_id: "wraiths", minimum: 0, maximum: 0 },
          { profile_id: "skeletons", minimum: 0, maximum: null },
        ],
      },
      equipment_access: [
        { item_id: "scimitar", list_id: "foreign-undead-equipment-list", cost: 12 },
        { item_id: "katar", list_id: "native-undead-equipment-list", cost: 9 },
      ],
      variants: [
        {
          id: "background.foreign",
          names: { en: "Foreign Background", es: "Trasfondo Foráneo" },
          rule_ids: ["band--background-selection"],
          roster_members: [{ profile_id: "slaves" }],
          equipment_lists: ["foreign-undead-equipment-list"],
        },
        {
          id: "background.native",
          names: { en: "Native Background", es: "Trasfondo Nativo" },
          rule_ids: ["band--background-selection"],
          roster_members: [{ profile_id: "wraiths" }],
          equipment_lists: ["native-undead-equipment-list"],
        },
      ],
    },
    [`profile:vampire`]: profile(BACKGROUND_BAND, "vampire", {
      type: "hero",
      cost: 90,
      characteristics: { M: 5, WS: 5, BS: 4, S: 4, T: 4, W: 2, I: 6, A: 2, Ld: 8 },
      equipment_lists: ["foreign-undead-equipment-list", "native-undead-equipment-list"],
      equipment_access: [
        { item_id: "scimitar", list_id: "foreign-undead-equipment-list", cost: 12 },
        { item_id: "katar", list_id: "native-undead-equipment-list", cost: 9 },
      ],
      equipment_restrictions: [UNDEAD_LIST],
    }),
    [`profile:slaves`]: profile(BACKGROUND_BAND, "slaves", {
      equipment_lists: ["foreign-undead-equipment-list"],
      equipment_access: [{ item_id: "scimitar", list_id: "foreign-undead-equipment-list", cost: 12 }],
      equipment_restrictions: ["Foreign background only.", "Use the Foreign Warband Undead Equipment List."],
    }),
    [`profile:wraiths`]: profile(BACKGROUND_BAND, "wraiths", {
      cost: 45,
      equipment_lists: ["native-undead-equipment-list"],
      equipment_access: [{ item_id: "katar", list_id: "native-undead-equipment-list", cost: 9 }],
      equipment_restrictions: ["Native background only."],
    }),
    [`profile:skeletons`]: profile(BACKGROUND_BAND, "skeletons", {
      cost: 35,
      equipment_access: [{ item_id: "sword", list_id: "skeleton-list", cost: 10 }],
      equipment_restrictions: [UNDEAD_LIST],
    }),
    "item:scimitar": { item_id: "scimitar", name: "Scimitar", kind: "close-combat-weapon" },
    "item:katar": { item_id: "katar", name: "Katar", kind: "close-combat-weapon" },
    "item:sword": { item_id: "sword", name: "Sword", kind: "close-combat-weapon" },
  });
}

function bloodlineReader(): KnowledgeReader {
  return makeReader({
    [`band:${BLOODLINE_BAND}`]: {
      id: BLOODLINE_BAND,
      name: "Undead Bloodlines Fixture",
      collection: "trollheim",
      rule_ids: ["band--choose-bloodline", "band--vampiric-powers"],
      roster: {
        minimum_models: 1,
        maximum_models: 15,
        starting_gold: 500,
        requires_variant_selection: true,
        members: [
          { profile_id: "lahmia-vampire", minimum: 0, maximum: 0 },
          { profile_id: "strigoi-vampire", minimum: 0, maximum: 0 },
          { profile_id: "carrion-ghoul", minimum: 0, maximum: 0 },
          { profile_id: "ghouls", minimum: 0, maximum: null },
        ],
      },
      equipment_access: [],
      variants: [
        {
          id: "lahmia",
          names: { en: "Lahmia", es: "Lahmia" },
          rule_ids: ["band--choose-bloodline", "band--vampiric-powers"],
          roster_members: [{ profile_id: "lahmia-vampire", minimum: 1, maximum: 1 }],
        },
        {
          id: "strigoi",
          names: { en: "Strigoi", es: "Strigoi" },
          rule_ids: ["band--choose-bloodline", "band--vampiric-powers"],
          roster_members: [
            { profile_id: "strigoi-vampire", minimum: 1, maximum: 1 },
            { profile_id: "carrion-ghoul" },
          ],
        },
      ],
    },
    [`profile:lahmia-vampire`]: profile(BLOODLINE_BAND, "lahmia-vampire", {
      type: "hero",
      cost: 90,
      bloodline: "lahmia",
    }),
    [`profile:strigoi-vampire`]: profile(BLOODLINE_BAND, "strigoi-vampire", {
      type: "hero",
      cost: 90,
      bloodline: "strigoi",
    }),
    [`profile:carrion-ghoul`]: profile(BLOODLINE_BAND, "carrion-ghoul", {
      type: "hero",
      cost: 45,
      equipment_restrictions: ["Available only to a Strigoi warband."],
    }),
    [`profile:ghouls`]: profile(BLOODLINE_BAND, "ghouls", { cost: 25 }),
  });
}

function draftOk(result: ReturnType<typeof createDraft>): CampaignDocument {
  if (!result.ok) throw new Error(result.message);
  return result.state;
}

function withVariant(document: CampaignDocument, variantId: string | null): CampaignDocument {
  return {
    ...document,
    campaign: {
      ...document.campaign,
      identity: { ...document.campaign.identity, mercenary_variant: variantId },
    },
  };
}

describe("construction contracts: mandatory warband variants", () => {
  it("resolves the published option: its slots open and its lists activate", () => {
    const reader = backgroundReader();
    const band = bandFactsOf(reader, BACKGROUND_BAND);
    expect(band).toBeTruthy();
    expect(band?.requires_variant_selection).toBe(true);
    expect(band?.variant_dimensions).toEqual(["background"]);
    expect(band?.equipment_lists).toEqual([
      "foreign-undead-equipment-list",
      "native-undead-equipment-list",
    ]);
    expect(warbandVariants(reader, BACKGROUND_BAND).map((option) => option.id)).toEqual([
      "background.foreign",
      "background.native",
    ]);
    expect(variantGatesOf(reader, band!)).toEqual([
      { profile_id: "slaves", option_ids: ["background.foreign"] },
      { profile_id: "wraiths", option_ids: ["background.native"] },
    ]);

    const foreign = variantFrameOf(reader, band!, "background.foreign");
    expect(foreign.available.map((member) => member.profile_id)).toEqual([
      "vampire",
      "slaves",
      "skeletons",
    ]);
    expect(foreign.removed_profiles).toEqual(["wraiths"]);
    expect(foreign.equipment_lists).toEqual(["foreign-undead-equipment-list"]);
    expect(foreign.leader_profile).toBeNull();
    expect(foreign.unstructured).toBe(false);

    const native = variantFrameOf(reader, band!, "background.native");
    expect(native.available.map((member) => member.profile_id)).toEqual([
      "vampire",
      "wraiths",
      "skeletons",
    ]);
    expect(native.removed_profiles).toEqual(["slaves"]);

    // Two options that open the same slot are reported with both ids.
    const shared = makeReader({
      [`band:${BACKGROUND_BAND}`]: {
        id: BACKGROUND_BAND,
        name: "Lahmian Fixture",
        collection: "trollheim",
        rule_ids: [],
        roster: {
          minimum_models: 1,
          maximum_models: 15,
          starting_gold: 500,
          requires_variant_selection: true,
          members: [
            { profile_id: "vampire", minimum: 1, maximum: 1 },
            { profile_id: "slaves", minimum: 0, maximum: 0 },
          ],
        },
        equipment_access: [],
        variants: [
          { id: "background.foreign", names: { en: "Foreign" }, rule_ids: [], roster_members: [{ profile_id: "slaves" }] },
          { id: "background.native", names: { en: "Native" }, rule_ids: [], roster_members: [{ profile_id: "slaves" }] },
        ],
      },
      [`profile:vampire`]: profile(BACKGROUND_BAND, "vampire", { type: "hero" }),
      [`profile:slaves`]: profile(BACKGROUND_BAND, "slaves"),
    });
    expect(variantGatesOf(shared, bandFactsOf(shared, BACKGROUND_BAND)!)).toEqual([
      { profile_id: "slaves", option_ids: ["background.foreign", "background.native"] },
    ]);
  });

  it("keeps the background's lists closed while the choice is open", () => {
    const reader = backgroundReader();
    const vampire = profileFactsOf(reader, BACKGROUND_BAND, "vampire")!;
    // Both printed lists are declared, so no list is active before the choice:
    // the member cannot buy from either of them yet.
    expect(equipmentIssueFor(reader, vampire, "scimitar")).toMatchObject({
      code: "equipment_not_permitted",
    });
    expect(equipmentIssueFor(reader, vampire, "scimitar", "background.foreign")).toBeNull();
    expect(equipmentIssueFor(reader, vampire, "katar", "background.foreign")).toMatchObject({
      code: "equipment_not_permitted",
    });
    expect(equipmentIssueFor(reader, vampire, "katar", "background.native")).toBeNull();

    // A member that declares none of the option's lists keeps no active list.
    const skeletons = profileFactsOf(reader, BACKGROUND_BAND, "skeletons")!;
    expect(equipmentIssueFor(reader, skeletons, "sword", "background.native")).toBeNull();
    expect(equipmentIssueFor(reader, skeletons, "katar", "background.native")).toMatchObject({
      code: "equipment_not_permitted",
    });

    // The members the option does not open stay locked while it is selected.
    const wraiths = profileFactsOf(reader, BACKGROUND_BAND, "wraiths")!;
    expect(equipmentIssueFor(reader, wraiths, "katar", "background.foreign")).toMatchObject({
      code: "equipment_not_permitted",
    });
    expect(equipmentIssueFor(reader, wraiths, "katar", "background.native")).toBeNull();
  });

  it("requires the choice, publishes it and refuses an unknown one", () => {
    const reader = backgroundReader();
    const locked = draftOk(createDraft(BACKGROUND_BAND, reader));
    expect(locked.campaign.identity.mercenary_variant).toBeNull();
    expect(rosterIssuesOf(reader, locked.campaign).map((issue) => issue.code)).toEqual([
      "variant_selection_required",
    ]);
    expect(commitInitialWarband(locked, reader).ok).toBe(false);

    const unknownDraft = createDraft(BACKGROUND_BAND, reader, undefined, "background.bogus");
    expect(unknownDraft.ok).toBe(false);
    if (!unknownDraft.ok) expect(unknownDraft.message).toContain("Unknown warband variant");

    const forged: Campaign = {
      ...locked.campaign,
      identity: { ...locked.campaign.identity, mercenary_variant: "background.bogus" },
    };
    const issues = rosterIssuesOf(reader, forged);
    expect(issues.map((issue) => issue.code)).toEqual(["variant_unknown_option"]);
    expect(commitInitialWarband(withVariant(locked, "background.bogus"), reader).ok).toBe(false);

    const chosen = draftOk(createDraft(BACKGROUND_BAND, reader, undefined, "background.foreign"));
    expect(chosen.campaign.identity.mercenary_variant).toBe("background.foreign");
    // Every opened slot stays reported while the source does not fix its bound.
    expect(rosterIssuesOf(reader, chosen.campaign).map((issue) => issue.code)).toEqual([
      "variant_member_maximum_unpublished",
      "variant_member_maximum_unpublished",
    ]);
    expect(rosterIssuesOf(reader, chosen.campaign).map((issue) => issue.subject_ids[1])).toEqual([
      "background.foreign",
      "background.native",
    ]);
    expect(commitInitialWarband(chosen, reader).ok).toBe(true);

    const native = draftOk(createDraft(BACKGROUND_BAND, reader, undefined, "background.native"));
    expect(native.campaign.warriors.map((row) => row.profile_id)).not.toContain("slaves");
    expect(
      variantFrameOf(reader, bandFactsOf(reader, BACKGROUND_BAND)!, "background.native").available.map(
        (member) => member.profile_id,
      ),
    ).toContain("wraiths");
    expect(commitInitialWarband(native, reader).ok).toBe(true);
  });

  it("reports a slot no option opens and a slot without a published maximum", () => {
    const orphan = makeReader({
      [`band:${BACKGROUND_BAND}`]: {
        id: BACKGROUND_BAND,
        name: "Lahmian Fixture",
        collection: "trollheim",
        rule_ids: [],
        roster: {
          minimum_models: 1,
          maximum_models: 15,
          starting_gold: 500,
          requires_variant_selection: true,
          members: [
            { profile_id: "vampire", minimum: 1, maximum: 1 },
            { profile_id: "jackals", minimum: 0, maximum: 0 },
            { profile_id: "orphan", minimum: 0, maximum: 0 },
          ],
        },
        equipment_access: [],
        variants: [
          {
            id: "background.native",
            names: { en: "Native Background" },
            rule_ids: [],
            roster_members: [{ profile_id: "jackals" }, { profile_id: "ghost" , maximum: 3 }],
          },
        ],
      },
      [`profile:vampire`]: profile(BACKGROUND_BAND, "vampire", { type: "hero" }),
      [`profile:jackals`]: profile(BACKGROUND_BAND, "jackals"),
      [`profile:orphan`]: profile(BACKGROUND_BAND, "orphan"),
      [`profile:ghost`]: profile(BACKGROUND_BAND, "ghost"),
    });
    const draft = draftOk(createDraft(BACKGROUND_BAND, orphan, undefined, "background.native"));
    const codes = variantRequirementOf(orphan, BACKGROUND_BAND).required
      ? rosterIssuesOf(orphan, draft.campaign).map((issue) => issue.code)
      : [];
    expect(codes).toEqual([
      "variant_gate_unpublished",
      "variant_member_maximum_unpublished",
    ]);
    // The unpublished bound opens the slot up to the warband size, never wider,
    // and a slot no option opens stays out of the frame.
    const frame = variantFrameOf(orphan, bandFactsOf(orphan, BACKGROUND_BAND)!, "background.native");
    expect(frame.available.map((member) => member.profile_id)).toEqual([
      "vampire",
      "jackals",
    ]);
    expect(frame.removed_profiles).toEqual(["orphan"]);
    expect(variantSlotOf(warbandVariants(orphan, BACKGROUND_BAND)[0], "jackals")?.maximum).toBeUndefined();
    expect(commitInitialWarband(draft, orphan).ok).toBe(true);

    const noOptions = makeReader({
      [`band:${BACKGROUND_BAND}`]: {
        id: BACKGROUND_BAND,
        name: "Lahmian Fixture",
        collection: "trollheim",
        rule_ids: [],
        roster: {
          minimum_models: 1,
          maximum_models: 15,
          starting_gold: 500,
          requires_variant_selection: true,
          members: [{ profile_id: "vampire", minimum: 1, maximum: 1 }],
        },
        equipment_access: [],
        variants: [],
      },
      [`profile:vampire`]: profile(BACKGROUND_BAND, "vampire", { type: "hero" }),
    });
    const requirement = variantRequirementOf(noOptions, BACKGROUND_BAND);
    expect(requirement.required).toBe(true);
    expect(requirement.options).toEqual([]);
    const emptyDraft = draftOk(createDraft(BACKGROUND_BAND, noOptions));
    expect(rosterIssuesOf(noOptions, emptyDraft.campaign).map((issue) => issue.code)).toEqual([
      "variant_options_missing",
    ]);
    expect(commitInitialWarband(emptyDraft, noOptions).ok).toBe(false);
  });

  it("refuses the members the chosen background forbids", () => {
    const reader = backgroundReader();
    const native = draftOk(createDraft(BACKGROUND_BAND, reader, undefined, "background.native"));
    const composed = composeDraft(
      native,
      { band_id: BACKGROUND_BAND, rows: [{ profile_id: "slaves", kind: "henchman", quantity: 1, equipment: [] }] },
      reader,
    );
    expect(composed.ok).toBe(false);
    if (!composed.ok) {
      expect(composed.message).toContain("not available under the selected warband variant");
    }
    const foreign = draftOk(createDraft(BACKGROUND_BAND, reader, undefined, "background.foreign"));
    expect(
      composeDraft(
        foreign,
        { band_id: BACKGROUND_BAND, rows: [{ profile_id: "slaves", kind: "henchman", quantity: 1, equipment: [] }] },
        reader,
      ).ok,
    ).toBe(true);
    expect(
      rosterIssuesOf(reader, { ...native.campaign, warriors: [...native.campaign.warriors, { ...native.campaign.warriors[0], id: "slaves#1", profile_id: "slaves", kind: "henchman", quantity: 1 }] })
        .map((issue) => issue.code),
    ).toContain("profile_not_permitted_for_variant");
  });

  it("makes the chosen bloodline the leader and opens only its slots", () => {
    const reader = bloodlineReader();
    const band = bandFactsOf(reader, BLOODLINE_BAND)!;
    expect(variantGatesOf(reader, band)).toEqual([
      { profile_id: "lahmia-vampire", option_ids: ["lahmia"] },
      { profile_id: "strigoi-vampire", option_ids: ["strigoi"] },
      { profile_id: "carrion-ghoul", option_ids: ["strigoi"] },
    ]);

    const lahmia = variantFrameOf(reader, band, "lahmia");
    expect(lahmia.leader_profile).toBe("lahmia-vampire");
    expect(lahmia.available).toEqual([
      { profile_id: "lahmia-vampire", minimum: 1, maximum: 1, group_size: null },
      { profile_id: "ghouls", minimum: 0, maximum: null, group_size: null },
    ]);
    expect(lahmia.removed_profiles).toEqual(["strigoi-vampire", "carrion-ghoul"]);

    const strigoi = variantFrameOf(reader, band, "strigoi");
    expect(strigoi.leader_profile).toBe("strigoi-vampire");
    expect(strigoi.available.map((member) => member.profile_id)).toEqual([
      "strigoi-vampire",
      "carrion-ghoul",
      "ghouls",
    ]);
    expect(strigoi.removed_profiles).toEqual(["lahmia-vampire"]);
    // The Strigoi-only member is opened by the option and its scored as the
    // slot the option opens, not by a prose sentence of its own profile.
    expect(profileFactsOf(reader, BLOODLINE_BAND, "carrion-ghoul")?.equipment_restrictions).toEqual([
      "Available only to a Strigoi warband.",
    ]);

    const draft = draftOk(createDraft(BLOODLINE_BAND, reader, undefined, "lahmia"));
    expect(draft.campaign.identity.mercenary_variant).toBe("lahmia");
    expect(draft.campaign.warriors.map((row) => row.profile_id)).toContain("lahmia-vampire");
    expect(draft.campaign.warriors.map((row) => row.profile_id)).not.toContain("strigoi-vampire");
    expect(commitInitialWarband(draft, reader).ok).toBe(true);

    const foreign = composeDraft(
      draft,
      {
        band_id: BLOODLINE_BAND,
        rows: [{ profile_id: "strigoi-vampire", kind: "hero", quantity: 1, equipment: [] }],
      },
      reader,
    );
    expect(foreign.ok).toBe(false);

    const strigoiDraft = draftOk(createDraft(BLOODLINE_BAND, reader, undefined, "strigoi"));
    expect(strigoiDraft.campaign.warriors.map((row) => row.profile_id)).toContain("strigoi-vampire");
    expect(commitInitialWarband(strigoiDraft, reader).ok).toBe(true);
    const ghoulRow = composeDraft(
      strigoiDraft,
      {
        band_id: BLOODLINE_BAND,
        rows: [{ profile_id: "carrion-ghoul", kind: "hero", quantity: 1, equipment: [] }],
      },
      reader,
    );
    // The slot is open for the Strigoi option: the only refusal left is the
    // fixture's hero limit, never a variant one.
    expect(ghoulRow.ok).toBe(false);
    if (!ghoulRow.ok) {
      expect(ghoulRow.reason).toBe("limit_reached");
      expect(ghoulRow.message).not.toContain("variant");
    }

    // Switching the choice without its leader leaves the mandatory slot empty.
    const switched = withVariant(draft, "strigoi");
    const committed = commitInitialWarband(switched, reader);
    expect(committed.ok).toBe(false);
    expect(rosterIssuesOf(reader, switched.campaign).map((issue) => issue.code)).toEqual(
      expect.arrayContaining(["roster_minimum_missing", "profile_not_permitted_for_variant"]),
    );
  });

  it("round-trips both choices through a v5 file", () => {
    const reader = bloodlineReader();
    const adapter = new CampaignFileV5Adapter();
    const committed = commitInitialWarband(
      draftOk(createDraft(BLOODLINE_BAND, reader, undefined, "lahmia")),
      reader,
    );
    expect(committed.ok).toBe(true);
    if (!committed.ok) return;
    const serialized = adapter.serializeCampaign(committed.state.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const parsed = parseCampaignFileDetailed(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.campaign.identity.mercenary_variant).toBe("lahmia");
    expect(parsed.campaign.warriors.map((row) => row.profile_id)).toContain("lahmia-vampire");
    expect(parsed.campaign.configuration.is_draft).toBe(false);
    // Restoring the file restores the frame: the option still opens its slot.
    const restored = variantFrameOf(
      reader,
      bandFactsOf(reader, BLOODLINE_BAND)!,
      parsed.campaign.identity.mercenary_variant,
    );
    expect(restored.available.map((member) => member.profile_id)).toContain("lahmia-vampire");
    expect(restored.removed_profiles).toEqual(["strigoi-vampire", "carrion-ghoul"]);

    const backgroundReaderInstance = backgroundReader();
    const backgroundCommitted = commitInitialWarband(
      draftOk(createDraft(BACKGROUND_BAND, backgroundReaderInstance, undefined, "background.native")),
      backgroundReaderInstance,
    );
    expect(backgroundCommitted.ok).toBe(true);
    if (!backgroundCommitted.ok) return;
    const backgroundSerialized = adapter.serializeCampaign(backgroundCommitted.state.campaign);
    expect(backgroundSerialized.ok).toBe(true);
    if (!backgroundSerialized.ok) return;
    const backgroundParsed = parseCampaignFileDetailed(backgroundSerialized.text);
    expect(backgroundParsed.ok).toBe(true);
    if (!backgroundParsed.ok) return;
    expect(backgroundParsed.campaign.identity.mercenary_variant).toBe("background.native");
    const restoredBackground = variantFrameOf(
      backgroundReaderInstance,
      bandFactsOf(backgroundReaderInstance, BACKGROUND_BAND)!,
      backgroundParsed.campaign.identity.mercenary_variant,
    );
    expect(restoredBackground.available.map((member) => member.profile_id)).toContain("wraiths");
    expect(restoredBackground.removed_profiles).toEqual(["slaves"]);
  });

  it("reports a published option without any construction consequence", () => {
    const reader = makeReader({
      [`band:${BACKGROUND_BAND}`]: {
        id: BACKGROUND_BAND,
        name: "Tribes Fixture",
        collection: "mordheim",
        rule_ids: [],
        roster: {
          minimum_models: 1,
          maximum_models: 12,
          starting_gold: 500,
          requires_variant_selection: true,
          members: [{ profile_id: "marauders", minimum: 1, maximum: 1 }],
        },
        equipment_access: [],
        variants: [{ id: "tribe.kurgan", names: { en: "Kurgan" }, rule_ids: [] }],
      },
      [`profile:marauders`]: profile(BACKGROUND_BAND, "marauders", { type: "hero" }),
    });
    const requirement = variantRequirementOf(reader, BACKGROUND_BAND);
    expect(requirement.required).toBe(true);
    expect(requirement.options.map((option) => option.id)).toEqual(["tribe.kurgan"]);
    const band = bandFactsOf(reader, BACKGROUND_BAND)!;
    expect(variantFrameOf(reader, band, "tribe.kurgan").unstructured).toBe(true);
    const draft = draftOk(createDraft(BACKGROUND_BAND, reader, undefined, "tribe.kurgan"));
    const issues = rosterIssuesOf(reader, draft.campaign);
    expect(issues.map((issue) => issue.code)).toEqual(["variant_consequence_unstructured"]);
    expect(issues[0].owner_task).toBe("KB");
  });
});
