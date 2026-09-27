/**
 * T09 construction sweep over the real generated artefact.
 *
 * Every band of the promoted KB must offer at least one legal starting
 * selection, and every refusal must be the declared one. The sweep drives the
 * real `createDraft` → `commitInitialWarband` path through
 * `ArtefactKnowledgeReader`, so a band that cannot be built fails here instead
 * of in the interface.
 *
 * Bands that declare `roster.requires_variant_selection` are built by choosing
 * the first published option and handing it to `createDraft`, exactly as the
 * interface must ask the player to (`background.foreign`, `bloodline.lahmia`…);
 * an artefact that predates the T09 variant contract (`outputs/`, regenerated
 * by T12) publishes no options for those bands, and the sweep then reports them
 * as the declared refusals the obsolete artefact explains.
 *
 * `MORDHEIM_KNOWLEDGE_ARTEFACT` points the sweep at one artefact file, which is
 * how the freshly generated artefact of `build/generated` is verified without
 * writing the versioned Web artefact T12 owns.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { createDraft } from "@domain/campaign/kernel/create-draft";
import { commitInitialWarband } from "@domain/campaign/kernel/commit-warband";
import type { KnowledgeReader } from "@domain/campaign/kernel/usecases";
import {
  bandFactsOf,
  profileExclusionFor,
  variantRequirementOf,
} from "@domain/campaign/construction";
import { warbandVariants } from "@domain/campaign/band-variants";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

/** Bands whose mandatory choice the promoted KB declares. */
const VARIANT_BANDS = ["chaos-streets-undead-bloodlines", "khemri-lahmian-brotherhood"];

interface RosterMember {
  profile_id?: string;
  minimum?: number;
}

describe.skipIf(!ARTEFACT_PATH)("T09 construction: every applicable band builds", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader: KnowledgeReader = ArtefactKnowledgeReader.from(artefact);
  const bands = artefact.bands as { id: string; roster?: { members?: RosterMember[] } }[];

  it("promotes at least the whole collection", () => {
    expect(bands.length).toBeGreaterThan(50);
    expect(reader.list("band").length).toBe(bands.length);
  });

  it("builds a legal starting selection for every band the source allows", () => {
    const refusals: Record<string, string> = {};
    const declaredRefusals: string[] = [];
    let built = 0;
    for (const band of bands) {
      const bandId = String(band.id);
      const mandatory = (band.roster?.members ?? []).filter(
        (member) => typeof member.minimum === "number" && member.minimum > 0,
      );
      const excluded = mandatory.filter(
        (member) => member.profile_id && profileExclusionFor(bandId, member.profile_id) !== null,
      );
      const requirement = variantRequirementOf(reader, bandId);
      const blocked =
        excluded.length > 0 || (requirement.required && requirement.options.length === 0);
      // The interface asks for the mandatory choice first and then builds the
      // draft for it; an artefact without options cannot offer that step.
      const variantId = requirement.required ? requirement.options[0]?.id ?? null : null;
      const created = createDraft(bandId, reader, undefined, variantId);
      if (!created.ok) {
        if (blocked) declaredRefusals.push(bandId);
        else refusals[bandId] = created.message;
        continue;
      }
      const committed = commitInitialWarband(created.state, reader);
      if (!committed.ok) {
        if (blocked) declaredRefusals.push(bandId);
        else refusals[bandId] = committed.message;
        continue;
      }
      built += 1;
    }
    expect(built).toBeGreaterThan(0);
    expect(refusals).toEqual({});
    expect(built).toBe(bands.length - declaredRefusals.length);
    // A declared refusal is only acceptable when the artefact cannot offer the
    // step: a mandatory member the runtime scope excludes, or a mandatory
    // choice whose options the artefact does not publish (the pre-T12 artefact).
    for (const bandId of declaredRefusals) {
      const requirement = variantRequirementOf(reader, bandId);
      const members = (bands.find((band) => String(band.id) === bandId)?.roster?.members ?? []).filter(
        (member) => typeof member.minimum === "number" && member.minimum > 0,
      );
      expect(
        (requirement.required && requirement.options.length === 0) ||
          members.some(
            (member) => member.profile_id && profileExclusionFor(bandId, member.profile_id) !== null,
          ),
      ).toBe(true);
    }
  });

  it("publishes the canonical option ids for both mandatory choices", () => {
    const missing = bands
      .map((band) => String(band.id))
      .filter((bandId) => {
        const requirement = variantRequirementOf(reader, bandId);
        return requirement.required && requirement.options.length === 0;
      });
    const optionsOf = (bandId: string): string[] =>
      variantRequirementOf(reader, bandId).options.map((option) => option.id);
    // The artefact of `outputs/` predates the T09 variant contract and is
    // regenerated by T12; a fresh artefact publishes both choices.
    if (missing.length > 0) {
      expect(missing).toEqual(VARIANT_BANDS);
      return;
    }
    // Khemri ids are the shared Python compiler's own vocabulary
    // (`compiler.foreign-or-native-background` consumes `background.foreign` /
    // `background.native`); the bloodline ids are the profiles' published
    // `bloodline` values.
    expect(optionsOf("khemri-lahmian-brotherhood")).toEqual([
      "background.foreign",
      "background.native",
    ]);
    expect(optionsOf("chaos-streets-undead-bloodlines")).toEqual([
      "blood-dragon",
      "lahmia",
      "necrarch",
      "strigoi",
      "von-carstein",
    ]);

    for (const bandId of VARIANT_BANDS) {
      const band = bandFactsOf(reader, bandId);
      if (!band) continue;
      const options = warbandVariants(reader, bandId);
      const opened = new Set(options.flatMap((option) => (option.roster_members ?? []).map((row) => row.profile_id)));
      for (const member of band.members) {
        if (member.maximum !== 0) continue;
        // No slot of a mandatory choice may be locked without an option that
        // opens it, and no option may open a slot the roster does not gate.
        expect(opened.has(member.profile_id)).toBe(true);
      }
      for (const profileId of opened) {
        expect(band.members.some((member) => member.profile_id === profileId)).toBe(true);
      }
    }
    // The printed bound of a reopened slot is published only where the source
    // fixes it: the bloodline Vampire is the single leader, the rest wait for
    // the KB and are reported as pending, never guessed.
    const bloodlines = warbandVariants(reader, "chaos-streets-undead-bloodlines");
    for (const option of bloodlines) {
      const leader = option.roster_members?.find((row) => row.profile_id.endsWith("-vampire"));
      expect(leader?.minimum).toBe(1);
      expect(leader?.maximum).toBe(1);
    }
  });

  it("returns the stable verdicts on real profiles, away from any interface", () => {
    const profileFacts = (bandId: string, profileId: string) =>
      reader.queryKnowledge({ id: { kind: "profile_id", value: profileId } }).ok
        ? (reader as KnowledgeReader & { list(kind: string): readonly Record<string, unknown>[] })
            .list("profile")
            .find((row) => row["id"] === profileId && row["band_id"] === bandId)
        : null;
    // A variant-locked member stays locked until its option is chosen: the
    // published slot is `0/0` and the gate is the declared restriction.
    const bloodline = variantRequirementOf(reader, "chaos-streets-undead-bloodlines");
    if (bloodline.options.length > 0) {
      expect(profileFacts("chaos-streets-undead-bloodlines", "lahmia-vampire")?.["bloodline"]).toBe(
        "lahmia",
      );
    }
    expect(profileExclusionFor("guild-of-disgraced-engineers-mim", "gyrocopter")).not.toBeNull();
  });
});
