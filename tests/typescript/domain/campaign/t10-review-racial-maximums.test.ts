/**
 * T10 (post-review) — racial maxima by stable identity, and the printed
 * profiles that sit above their race's maximum.
 *
 * The review found that the maximum was resolved from a profile's *printed
 * name* (`racialMaximumKey(profile.name)`), which the same profile id shares
 * across several bands, and that the bound was applied to the printed statline
 * itself — which would refuse a profile the source prints. These tests drive the
 * real artefact: the rows carry a stable `race_key`, the race groups they govern
 * and the explicit `band_id`/`profile_id` keys; a profile resolves by those ids,
 * never by its display name; and a printed characteristic above the maximum is
 * legal to compose (the table bounds *increases*), while an unprinted increase
 * is still refused.
 *
 * Purity: plain Node, the real reader — no React, no DOM.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  characteristicBoundIssueFor,
  constructionIssuesOf,
  profileFactsOf,
  racialMaximumResolutionFor,
  racialMaximumsOf,
  bandRaceGroupIdsOf,
} from "@domain/campaign/construction";
import type { Campaign, CampaignDocument, Warrior } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

/** Short statline key → the long key the racial-maximum table publishes. */
const RACIAL_KEYS: Readonly<Record<string, string>> = {
  M: "movement",
  WS: "weapon_skill",
  BS: "ballistic_skill",
  S: "strength",
  T: "toughness",
  W: "wounds",
  I: "initiative",
  A: "attacks",
  Ld: "leadership",
};

interface ProfileRow {
  readonly id: string;
  readonly name: string;
  readonly band_id?: string;
  readonly characteristics?: Readonly<Record<string, unknown>>;
}

function singleWarriorDocument(bandId: string, warrior: Warrior): CampaignDocument {
  const campaign: Campaign = {
    identity: { campaign_name: "Racial", warband_name: "Band", warband_type: bandId, band_id: bandId, mercenary_variant: null },
    configuration: { is_draft: true, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 0,
    warriors: [warrior],
    battles: [],
    states: [],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
  return { campaign, view: {} };
}

function warriorFrom(profile: ProfileRow): Warrior {
  const stats: Record<string, number> = {};
  for (const [key, value] of Object.entries(profile.characteristics ?? {})) {
    if (typeof value === "number") stats[key] = value;
  }
  return {
    id: `${profile.id}#1`,
    name: profile.name,
    profile_name: profile.id,
    kind: "hero",
    stats,
    equipment: [],
    skills: [],
    experience: 0,
    cost: 0,
    quantity: 1,
    profile_id: profile.id,
  };
}

describe.skipIf(!ARTEFACT_PATH)("T10 review: racial maxima by stable identity", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8")) as { profiles: ProfileRow[] };
  const reader = ArtefactKnowledgeReader.from(artefact as never);
  const rows = racialMaximumsOf(reader);

  it("keys every row by a stable race key, and pins the rows the catalogue does not bind", () => {
    expect(rows.length).toBeGreaterThan(0);
    for (const row of rows) {
      // The race is a machine key, never a printed name.
      expect(row.race_key, row.id).toMatch(/^[a-z0-9_]+$/);
      for (const key of row.profile_keys) {
        expect(key.band_id, row.id).not.toBe("");
        expect(key.profile_id, row.id).not.toBe("");
      }
    }
    // Every row reaches a band through a race group or an exact band/profile
    // key, except the four the catalogue publishes without any binding: their
    // race has no profile in the shipped bands (or the profile exists and the
    // binding is still to be published). They are enumerated, not hidden.
    const unbound = rows
      .filter((row) => row.group_ids.length === 0 && row.profile_keys.length === 0)
      .map((row) => row.id)
      .sort();
    expect(unbound).toEqual([
      "campaign.limit.racial-maximum.black-orc",
      "campaign.limit.racial-maximum.liche-restless-dead",
      "campaign.limit.racial-maximum.warrior-of-chaos",
      "campaign.limit.racial-maximum.werecreature-norse",
    ]);
  });

  it("resolves the same profile id to each band's own row, never by the display name", () => {
    // Two bands print a `bull-centaur`; each publishes its own statline.
    expect(racialMaximumResolutionFor(reader, "black-dwarfs", "bull-centaur").row?.id)
      .toBe("campaign.limit.racial-maximum.bull-centaur-black-dwarfs");
    expect(racialMaximumResolutionFor(reader, "sons-of-hashut", "bull-centaur").row?.id)
      .toBe("campaign.limit.racial-maximum.bull-centaur-sons-of-hashut");
    // An explicit key beats the band's race group: the Ogre that Ostlanders hire
    // is an Ogre, not a Human, although the band's race is Human.
    expect(bandRaceGroupIdsOf(reader, "ostlanders")).toEqual(["warband-group.human"]);
    expect(racialMaximumResolutionFor(reader, "ostlanders", "ogre").row?.id)
      .toBe("campaign.limit.racial-maximum.ogre");
    expect(racialMaximumResolutionFor(reader, "ostlanders", "swordsmen").row?.id)
      .toBe("campaign.limit.racial-maximum.human");
    // The row is chosen by id only: the profile's printed name is irrelevant.
    const ogre = artefact.profiles.find((profile) => profile.band_id === "ostlanders" && profile.id === "ogre")!;
    expect(ogre.name).toBe("Ogre");
  });

  it("says exactly why a profile has no row instead of exempting it silently", () => {
    expect(bandRaceGroupIdsOf(reader, "marauders-of-chaos")).toEqual([
      "warband-group.chaos-human",
      "warband-group.human",
    ]);
    // The Lahmian vampire is not among the vampire row's explicit keys.
    const unresolved = racialMaximumResolutionFor(reader, "khemri-lahmian-brotherhood", "lahmian-vampire");
    expect(unresolved.row).toBeNull();
    expect(unresolved.status).toBe("no-race-key");
    // An unknown profile is its own state, never a silent bound.
    expect(racialMaximumResolutionFor(reader, "ostlanders", "").status).toBe("unknown-profile");
  });

  it("accepts every printed statline above the band-derived maximum and still refuses an unprinted increase", () => {
    // Census over the fresh artefact: the (band, profile, stat) entries whose
    // printed characteristic sits above the maximum the band's identity resolves
    // to. The printed statline is the anchor the maximum is measured from — the
    // table bounds *increases* — so all of them are legal to compose. The count
    // is pinned so the coverage cannot silently shrink.
    const above: { readonly band_id: string; readonly profile_id: string; readonly stat: string; readonly printed: number; readonly max: number }[] = [];
    for (const profile of artefact.profiles) {
      const bandId = profile.band_id;
      if (!bandId) continue;
      const resolution = racialMaximumResolutionFor(reader, bandId, profile.id, rows);
      if (!resolution.row) continue;
      for (const [stat, long] of Object.entries(RACIAL_KEYS)) {
        const printed = profile.characteristics?.[stat];
        const bound = resolution.row.characteristics[long];
        if (typeof printed === "number" && typeof bound === "number" && printed > bound) {
          above.push({ band_id: bandId, profile_id: profile.id, stat, printed, max: bound });
        }
      }
    }
    // The source prints several such profiles (e.g. the Flagellants at Ld 10
    // against the Human maximum of 9). None of them is a construction error.
    expect(above).toHaveLength(54);
    expect(new Set(above.map((entry) => `${entry.band_id}/${entry.profile_id}`)).size).toBe(40);
    expect(above.some((entry) => entry.profile_id === "flagellants" && entry.stat === "Ld")).toBe(true);

    for (const entry of above) {
      const profile = artefact.profiles.find((row) => row.band_id === entry.band_id && row.id === entry.profile_id)!;
      const warrior = warriorFrom(profile);
      const document = singleWarriorDocument(entry.band_id, warrior);
      const issues = constructionIssuesOf(reader, document.campaign);
      expect(
        issues.some((issue) => issue.code === "characteristic_bound_exceeded"),
        `${entry.band_id}/${entry.profile_id}`,
      ).toBe(false);
      // ...and no report either: the profile is printed, so it is bounded, not unknown.
      expect(
        issues.some((issue) => issue.code === "characteristic_bound_unknown"),
        `${entry.band_id}/${entry.profile_id}`,
      ).toBe(false);
    }

    // The very same statline raised one point above the printed profile is an
    // unprinted increase and is still refused, with the row that bounds it.
    const sample = above[0]!;
    const profile = artefact.profiles.find((row) => row.band_id === sample.band_id && row.id === sample.profile_id)!;
    const facts = profileFactsOf(reader, sample.band_id, sample.profile_id)!;
    const bound = racialMaximumResolutionFor(reader, sample.band_id, sample.profile_id, rows).row!;
    const printed = facts.characteristics[sample.stat];
    const issue = characteristicBoundIssueFor({
      profile: facts,
      stat: sample.stat,
      value: (typeof printed === "number" ? printed : sample.printed) + 1,
      row: bound,
      printed: typeof printed === "number" ? printed : null,
    });
    expect(issue?.code).toBe("characteristic_bound_exceeded");
    expect(issue?.rule_id).toBe(bound.id);
  });
});
