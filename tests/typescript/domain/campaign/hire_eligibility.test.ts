/**
 * Parity port of desktop `tests/python/campaign/test_hire_eligibility.py` (15 test
 * functions → behavioural equivalents). Traceability: manifest rows with
 * `web_target: tests/typescript/domain/campaign/hire_eligibility.test.ts`.
 *
 * Driven by the real web KB artefact (`campaign.hirelings.profiles.rules`,
 * `campaign.hirelings.traits`, `campaign.warband_groups`) — no curated trait
 * sets, mirroring the desktop test's "facts come from the KB" contract.
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  declaredDynamicRules,
  dynamicRulesForProfile,
  evaluateRule,
  type Decision,
  type WarbandHireContext,
} from "@domain/campaign/hire-eligibility";

const ARTEFACT = JSON.parse(
  readFileSync(
    resolve(__dirname, "../../../../outputs/web-public/knowledge/knowledge-web.json"),
    "utf-8",
  ),
) as {
  bands: { id: string }[];
  campaign: {
    hirelings: {
      profiles: { id: string; rule_ids?: string[]; rules?: { id: string }[] }[];
      traits: Record<string, string[]>;
    };
    warband_groups: { id: string; kind: string; band_ids: string[] }[];
  };
};

const PROFILES = ARTEFACT.campaign.hirelings.profiles;

const TRAITS = new Map(
  Object.entries(ARTEFACT.campaign.hirelings.traits).map(([id, list]) => [id, new Set(list)]),
);
const GROUPS_OF = (bandId: string): Set<string> => {
  const out = new Set<string>();
  for (const group of ARTEFACT.campaign.warband_groups) {
    if (group.band_ids.includes(bandId)) out.add(group.id);
  }
  return out;
};

function ctx(
  bandId: string,
  opts: {
    member?: string[];
    hired?: string[];
    variant?: string | null;
  } = {},
): WarbandHireContext {
  return {
    band_id: bandId,
    band_groups: GROUPS_OF(bandId),
    member_profile_ids: new Set(opts.member ?? []),
    hired_sword_profile_ids: new Set(opts.hired ?? []),
    variant: opts.variant ?? null,
    hireling_traits: TRAITS,
  };
}

/** All dynamic decisions for one profile in the given context. */
function decide(
  profileId: string,
  context: WarbandHireContext,
): Decision[] {
  return dynamicRulesForProfile(profileId, PROFILES).map((ruleId) =>
    evaluateRule(ruleId, context),
  );
}

describe("dynamic hire-eligibility rules (desktop test_hire_eligibility.py)", () => {
  it("every dynamic rule is declared on a hireling profile in the artefact", () => {
    const declared = declaredDynamicRules(PROFILES);
    expect(declared.size).toBe(18);
    // Each declared rule carries prose either inline on the profile
    // (`profiles[].rules[]`) or in the shared `hirelings.rules` section
    // (artefact emits both shapes). No id without prose anywhere.
    const sharedRules = (ARTEFACT.campaign.hirelings as unknown as { rules?: { id: string }[] }).rules ?? [];
    const proseEverywhere = new Set<string>([
      ...sharedRules.map((r) => r.id),
      ...PROFILES.flatMap((p) => (p.rules ?? []).map((r) => r.id)),
    ]);
    for (const id of declared) {
      expect(proseEverywhere.has(id), id).toBe(true);
    }
  });

  it("dwarf and elf employer rules: sisters reject them", () => {
    const context = ctx("sisters-of-sigmar");
    for (const profile of [
      "hireling.hired-sword.dwarf-troll-slayer",
      "hireling.hired-sword.dwarf-treasure-hunter",
      "hireling.hired-sword.runesmith-journeyman",
    ]) {
      const decisions = decide(profile, context);
      expect(decisions.length).toBeGreaterThan(0);
      for (const d of decisions) expect(d.kind, profile).toBe("rejected");
    }
    // Elf Ranger looks for Dwarf employers; Sisters are humans.
    const decisions = decide("hireling.hired-sword.elf-ranger", context);
    expect(decisions[0].kind).toBe("rejected");
  });

  it("elf presence opens the dwarf hires and dwarf opens elf ranger", () => {
    const withElf = ctx("mercenaries", {
      hired: ["hireling.hired-sword.elf-ranger"],
    });
    for (const profile of [
      "hireling.hired-sword.dwarf-troll-slayer",
      "hireling.hired-sword.dwarf-treasure-hunter",
      "hireling.hired-sword.runesmith-journeyman",
    ]) {
      const decisions = decide(profile, withElf);
      for (const d of decisions) expect(d.kind, profile).toBe("allowed");
    }
    const withDwarf = ctx("mercenaries", {
      hired: ["hireling.hired-sword.dwarf-troll-slayer"],
    });
    const decisions = decide("hireling.hired-sword.elf-ranger", withDwarf);
    expect(decisions[0].kind).toBe("allowed");
  });

  it("mercenary variant rules", () => {
    const plain = ctx("mercenaries");
    expect(decide("hireling.hired-sword.warrior-priest-of-sigmar", plain)[0].kind).toBe("needs_variant");
    expect(decide("hireling.hired-sword.wolf-priest-of-ulric", plain)[0].kind).toBe("needs_variant");

    const middenheim = ctx("mercenaries", { variant: "middenheim" });
    expect(decide("hireling.hired-sword.wolf-priest-of-ulric", middenheim)[0].kind).toBe("allowed");
    expect(decide("hireling.hired-sword.warrior-priest-of-sigmar", middenheim)[0].kind).toBe("rejected");

    const reikland = ctx("mercenaries", { variant: "reikland" });
    expect(decide("hireling.hired-sword.wolf-priest-of-ulric", reikland)[0].kind).toBe("rejected");
    expect(decide("hireling.dramatis.maximilian-the-mad", reikland)[0].kind).toBe("allowed");
    expect(decide("hireling.dramatis.maximilian-the-mad", middenheim)[0].kind).toBe("rejected");

    // Fixed-provenance human-mercenary bands are never Middenheimers.
    const tilean = ctx("tileans", { variant: "middenheim" });
    expect(decide("hireling.hired-sword.wolf-priest-of-ulric", tilean)[0].kind).toBe("rejected");
  });

  it("highwayman/roadwarden mutual exclusion", () => {
    const clean = ctx("mercenaries");
    expect(decide("hireling.hired-sword.highwayman", clean)[0].kind).toBe("allowed");
    expect(decide("hireling.hired-sword.roadwarden", clean)[0].kind).toBe("allowed");

    const withRoadwarden = ctx("mercenaries", {
      hired: ["hireling.hired-sword.roadwarden"],
    });
    expect(decide("hireling.hired-sword.highwayman", withRoadwarden)[0].kind).toBe("rejected");
    const withHighwayman = ctx("mercenaries", {
      hired: ["hireling.hired-sword.highwayman"],
    });
    expect(decide("hireling.hired-sword.roadwarden", withHighwayman)[0].kind).toBe("rejected");
  });

  it("witch hunter spellcaster restriction (priests are not spellcasters)", () => {
    const clean = ctx("mercenaries");
    expect(decide("hireling.hired-sword.witch-hunter", clean)[0].kind).toBe("allowed");

    const withWarlock = ctx("mercenaries", {
      hired: ["hireling.hired-sword.warlock"],
    });
    expect(decide("hireling.hired-sword.witch-hunter", withWarlock)[0].kind).toBe("rejected");

    const withPriest = ctx("mercenaries", {
      hired: ["hireling.hired-sword.priest-of-morr"],
    });
    expect(decide("hireling.hired-sword.witch-hunter", withPriest)[0].kind).toBe("allowed");
  });

  it("roster composition rules (cathayan, grave robber, ippan shu, dijin katal)", () => {
    const sisters = ctx("sisters-of-sigmar");
    expect(decide("hireling.hired-sword.cathayan-merchant", sisters)[0].kind).toBe("allowed");

    const undead = ctx("undead");
    expect(decide("hireling.hired-sword.grave-robber", undead)[0].kind).toBe("allowed");
    expect(decide("hireling.hired-sword.grave-robber", sisters)[0].kind).toBe("rejected");

    expect(decide("hireling.dramatis.grand-master-ippan-shu", sisters)[0].kind).toBe("allowed");
    expect(decide("hireling.dramatis.grand-master-ippan-shu", ctx("skaven-clan-eshin"))[0].kind).toBe("rejected");

    expect(decide("hireling.dramatis.dijin-katal-the-renegade-assassin", sisters)[0].kind).toBe("allowed");
    const withElf = ctx("mercenaries", { hired: ["hireling.hired-sword.elf-mage"] });
    expect(decide("hireling.dramatis.dijin-katal-the-renegade-assassin", withElf)[0].kind).toBe("rejected");
  });

  it("evil hired sword and fear rules", () => {
    const withDarkElf = ctx("mercenaries", {
      hired: ["hireling.hired-sword.dark-elf-assassin"],
    });
    expect(decide("hireling.hired-sword.shadow-warrior", withDarkElf)[0].kind).toBe("rejected");

    const withPriest = ctx("mercenaries", {
      hired: ["hireling.hired-sword.warrior-priest-of-sigmar"],
    });
    expect(decide("hireling.hired-sword.knight-of-the-white-wolf", withPriest)[0].kind).toBe("rejected");

    const withOgre = ctx("mercenaries", {
      hired: ["hireling.hired-sword.ogre-bodyguard"],
    });
    expect(decide("hireling.hired-sword.ninja-gnoblar", withOgre)[0].kind).toBe("rejected");
  });

  it("william: automatic for mercenaries, conditional for good-aligned, rejected for evil", () => {
    const bard = "hireling.dramatis.william-schakestange-master-bard";
    expect(decide(bard, ctx("mercenaries"))[0].kind).toBe("allowed");
    const kislevites = decide(bard, ctx("kislevites"))[0];
    expect(kislevites.kind).toBe("conditional");
    if (kislevites.kind === "conditional") expect(kislevites.roll_ge).toBe(4);
    expect(decide(bard, ctx("cult-of-the-possessed"))[0].kind).toBe("rejected");
  });

  it("rule facts come from the KB trait registry (no curated sets)", () => {
    const expectTrait = (id: string, trait: string) =>
      expect(TRAITS.get(id)?.has(trait) ?? false, `${id} ~ ${trait}`).toBe(true);
    expectTrait("hireling.hired-sword.elf-mage", "elf");
    expectTrait("hireling.hired-sword.dwarf-troll-slayer", "dwarf");
    expectTrait("hireling.hired-sword.highwayman", "human");
    expectTrait("hireling.hired-sword.grave-robber", "undead");
    expectTrait("hireling.hired-sword.warlock", "spellcaster");
    expectTrait("hireling.hired-sword.elf-mage", "spellcaster");
    expectTrait("hireling.hired-sword.warrior-priest-of-sigmar", "priest");
    expectTrait("hireling.hired-sword.priest-of-morr", "priest");
    expectTrait("hireling.hired-sword.wolf-priest-of-ulric", "priest");
    expectTrait("hireling.hired-sword.dark-elf-assassin", "evil");
    expectTrait("hireling.hired-sword.ninja-gnoblar", "evil");
    expectTrait("hireling.hired-sword.ogre-bodyguard", "fear-causing");
    expectTrait("hireling.hired-sword.dark-mage", "fear-causing");
  });
});
