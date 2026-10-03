/**
 * T13-F017 — automatic band grants must honour their recipient filters.
 *
 * Expectations come from the canonical KB (sources/knowledge/bands/mordheim/
 * adventurers-kaz/special-rules.yaml, profiles.yaml) and the accepted F035
 * register, never from applicableRules output.  The shared contract cases in
 * tests/fixtures/eligibility/band-rule-recipients.json run against this direct
 * TypeScript export and the embedded bundle in
 * tests/python/construction/test_band_rule_recipients.py.
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { applicableRules, type BandPackage, type EditorialProfile } from "@domain/eligibility/index";

interface Case { name: string; package: BandPackage; profile: EditorialProfile; expected_rule_ids: string[] }
const cases: Case[] = JSON.parse(readFileSync(
  new URL("../../fixtures/eligibility/band-rule-recipients.json", import.meta.url), "utf8",
)).cases;

describe("T13-F017 shared band-rule recipient contract", () => {
  for (const row of cases) it(row.name, () => {
    expect(applicableRules(row.package, row.profile).map((rule) => rule.id)).toEqual(row.expected_rule_ids);
  });
});

describe("T13-F017 canonical adventurers-kaz tables", () => {
  // Facts copied from sources/knowledge/bands/mordheim/adventurers-kaz/
  // special-rules.yaml (id, applies_to, runtime.grant per rule) and profiles.yaml
  // (dwarf declares dwarf--hard-to-kill in rule_ids).  The four tables name
  // exactly one recipient each; the two controls are genuinely band-wide and
  // stay unimplemented, proving applicability is separate from combat support.
  const pack: BandPackage = {
    band: { id: "adventurers-kaz" },
    profiles: [],
    equipment_lists: [],
    special_rules: [
      { id: "band--dwarf-special-skills", applies_to: { band: true, profile_ids: ["dwarf"] }, runtime: { grant: "band", implemented: "YES" } },
      { id: "band--elf-special-skills", applies_to: { band: true, profile_ids: ["elf"] }, runtime: { grant: "band", implemented: "YES" } },
      { id: "band--barbarian-special-skills", applies_to: { band: true, profile_ids: ["barbarian"] }, runtime: { grant: "band", implemented: "YES" } },
      { id: "band--noble-special-skills", applies_to: { band: true, profile_ids: ["imperial-noble"] }, runtime: { grant: "band", implemented: "YES" } },
      { id: "band--no-fixed-leader", applies_to: { band: true }, runtime: { grant: "band", implemented: "NO" } },
      { id: "band--hired-swords", applies_to: { band: true }, runtime: { grant: "band", implemented: "NO" } },
      { id: "dwarf--hard-to-kill", applies_to: { profile_ids: ["dwarf"] }, runtime: { grant: "profile", implemented: "YES" } },
    ],
  };
  const wide = ["band--no-fixed-leader", "band--hired-swords"];
  const expected: Record<string, string[]> = {
    wizard: wide,
    elf: ["band--elf-special-skills", ...wide],
    barbarian: ["band--barbarian-special-skills", ...wide],
    "imperial-noble": ["band--noble-special-skills", ...wide],
    dwarf: ["dwarf--hard-to-kill", "band--dwarf-special-skills", ...wide],
    "imperial-captain": wide,
    "cannon-fodder": wide,
  };

  it("gives each canonical table to its named profile and nothing else", () => {
    for (const [profileId, ids] of Object.entries(expected)) {
      expect(applicableRules(pack, { id: profileId } as EditorialProfile).map((rule) => rule.id), profileId)
        .toEqual(ids);
    }
  });
});
