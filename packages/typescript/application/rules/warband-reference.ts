import { ArtefactKnowledgeReader } from "../../adapters/knowledge-reader/index";
import type { ArtefactRow } from "../../adapters/knowledge-reader/artefact-types";
import { sourceDescriptionUnavailableText, unavailableText, type ResolvedKbText } from "../../adapters/knowledge-reader/presentation";
import { adaptDistanceText } from "./distance-display";
import { RulesCatalogue, type Locale, type RuleEntry } from "./rules-catalogue";
import { catalogueJoin, catalogueLabel, type CatalogueText } from "./catalogue-text";

type Text = ResolvedKbText | CatalogueText;
export type ReferenceRow = Readonly<Record<string, unknown>>;
export const referenceRows = (value: unknown): readonly ArtefactRow[] => Array.isArray(value)
  ? value.filter((row): row is ArtefactRow => row !== null && typeof row === "object" && !Array.isArray(row)) : [];
const object = (value: unknown): ReferenceRow => value !== null && typeof value === "object" && !Array.isArray(value) ? value as ReferenceRow : {};
const ids = (value: unknown): readonly string[] => Array.isArray(value) ? value.filter((id): id is string => typeof id === "string") : [];

export interface ReferenceEntry { readonly id: string; readonly name: Text; readonly effect: Text; }
export interface ReferenceEquipment extends ReferenceEntry {
  readonly kind: string; readonly cost: unknown; readonly notes?: Text;
}
export interface ReferenceEquipmentList {
  readonly id: string; readonly name: Text; readonly profiles: readonly Text[];
  readonly notes?: Text;
  readonly items: readonly ReferenceEquipment[]; readonly complete: boolean;
}
export interface ReferenceWarrior {
  readonly id: string; readonly name: Text; readonly type: string;
  readonly cost: unknown; readonly experience: unknown; readonly characteristics: ReferenceRow;
  readonly minimum: unknown; readonly maximum: unknown; readonly groupSize: ReferenceRow;
  readonly skillAccess: readonly string[]; readonly rules: readonly ReferenceEntry[];
  readonly startingEquipment: readonly Text[]; readonly restrictions?: Text;
}
export interface ReferenceVariant extends ReferenceEntry {
  readonly gold: unknown; readonly rules: readonly ReferenceEntry[];
  readonly members: readonly { readonly name: Text; readonly minimum: unknown; readonly maximum: unknown }[];
  readonly lists: readonly Text[];
  readonly bonuses: readonly { readonly name: Text; readonly characteristics: ReferenceRow }[];
}
export interface WarbandReference {
  readonly id: string; readonly name: Text; readonly roster: ReferenceRow;
  readonly warriors: readonly ReferenceWarrior[];
  readonly skills: readonly { readonly category: string; readonly entries: readonly ReferenceEntry[] }[];
  readonly abilities: readonly ReferenceEntry[]; readonly rules: readonly ReferenceEntry[];
  readonly equipment: readonly ReferenceEquipmentList[];
  readonly magic: readonly { readonly id: string; readonly name: Text; readonly users: readonly Text[]; readonly spells: readonly RuleEntry[] }[];
  readonly variants: readonly ReferenceVariant[]; readonly sourceUrls: readonly string[];
}

/** One layout for every band; source rows stay registered with the reader. */
export class WarbandReferences {
  constructor(private readonly knowledge: ArtefactKnowledgeReader) {}

  list(locale: Locale, query = "") {
    const normalize = (text: string) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
    const needle = normalize(query.trim());
    return this.knowledge.list("band").map((row) => ({
      id: String(row.id), name: this.knowledge.recordText(row, "name", locale), row,
    })).filter((band) => normalize(band.name).includes(needle))
      .sort((a, b) => a.name.localeCompare(b.name, locale, { sensitivity: "base" }));
  }

  sheet(bandId: string, locale: Locale): WarbandReference | null {
    const band = this.knowledge.list("band").find((row) => row.id === bandId);
    if (!band) return null;
    const catalogue = new RulesCatalogue(this.knowledge);
    const profiles = this.knowledge.list("profile").filter((row) => row.band_id === bandId);
    const metadata = referenceRows(this.knowledge.campaignSection("warband-reference").rows).find((row) => row.band_id === bandId);
    const local = this.knowledge.rulesDocument("profile-special-rules").filter((row) => row.band_id === bandId);
    const localEntries = new Map(catalogue.entries("band-rules", locale).filter((entry) => entry.band_id === bandId).map((entry) => [entry.rule_id!, entry]));
    const shared = new Map(catalogue.entries("special-rules", locale).map((entry) => [entry.entry_id, entry]));
    const items = new Map(this.knowledge.list("item").map((row) => [String(row.id ?? row.item_id), row]));
    const itemEntries = new Map(catalogue.entries("equipment", locale).map((entry) => [entry.entry_id, entry]));
    const skillEntries = new Map(catalogue.entries("skills", locale).map((entry) => [entry.entry_id, entry]));
    const prose = (row: ArtefactRow): Text => {
      const field = ["effect", "description", "text", "note"].find((field) => field in row || `${field}_i18n` in row || (field === "effect" && "effects" in row));
      return field ? adaptDistanceText(this.knowledge.recordText(row, field as "effect" | "description" | "text" | "note", locale), locale, String(row.id ?? "")) : sourceDescriptionUnavailableText(locale);
    };
    const entry = (row: ArtefactRow): ReferenceEntry => ({ id: String(row.id ?? row.item_id), name: this.knowledge.recordText(row, "name", locale), effect: prose(row) });
    const fromRule = (ruleId: string): ReferenceEntry => {
      const rule = localEntries.get(ruleId) ?? shared.get(ruleId);
      return rule ? { id: ruleId, name: rule.name, effect: rule.effect } : { id: ruleId, name: unavailableText(locale), effect: unavailableText(locale) };
    };
    const delegated = referenceRows(metadata?.rule_refs);
    const rulesFor = (profileId?: string): ReferenceEntry[] => {
      const result = local.filter((row) => {
        const scope = object(row.applies_to);
        return profileId ? ids(scope.profile_ids).includes(profileId) : !ids(scope.profile_ids).length && !row.kind;
      }).map((row) => fromRule(String(row.id)));
      for (const row of delegated) {
        const scope = object(row.applies_to);
        if (profileId ? ids(scope.profile_ids).includes(profileId) : !ids(scope.profile_ids).length && !row.kind) result.push(fromRule(String(row.rule_ref)));
      }
      if (profileId) for (const ruleId of ids(profiles.find((row) => row.id === profileId)?.rule_ids)) {
        if (shared.has(ruleId)) result.push(fromRule(ruleId));
      }
      return [...new Map(result.map((rule) => [rule.id, rule])).values()];
    };
    const roster = object(band.roster);
    const members = referenceRows(roster.members);
    const warriors = profiles.map((profile): ReferenceWarrior => {
      const member = members.find((row) => row.profile_id === profile.id);
      const restrictions = referenceRows(metadata?.profile_restrictions).find((row) => row.profile_id === profile.id);
      const profileRestriction = restrictions ? this.knowledge.recordText(restrictions, "notes", locale) : unavailableText(locale);
      // A declared rule that owns the restriction and resolves localized prose
      // is authoritative; the legacy profile field only carries source
      // sentences and older translations, so it is the fallback.
      const restrictionRules = local.filter((row) => ids(object(row.applies_to).profile_ids).includes(String(profile.id))
        && referenceRows(object(row.runtime).effects).some((effect) => object(effect.binding).id === "profile.equipment-restrictions"))
        .map((row) => fromRule(String(row.id)))
        .filter((rule) => rule.effect !== unavailableText(locale));
      return {
        id: String(profile.id), name: this.knowledge.recordText(profile, "name", locale), type: String(profile.type ?? ""),
        cost: profile.cost, experience: profile.experience, characteristics: object(profile.characteristics),
        minimum: member?.minimum, maximum: member?.maximum, groupSize: object(member?.group_size ?? profile.group_size),
        skillAccess: ids(profile.skill_access), rules: rulesFor(String(profile.id)),
        startingEquipment: (Array.isArray(profile.fixed_equipment) ? profile.fixed_equipment : []).map((value) => {
          const id = typeof value === "string" ? value : String(object(value).item_id);
          return this.knowledge.recordText(items.get(id), "name", locale);
        }),
        ...(restrictionRules.length ? { restrictions: catalogueJoin(restrictionRules.map((rule) => rule.effect), "\n") }
          : profileRestriction !== unavailableText(locale) ? { restrictions: adaptDistanceText(profileRestriction, locale) }
            : ids(profile.equipment_restrictions).length ? { restrictions: unavailableText(locale) } : {}),
      };
    }).sort((a, b) => a.name.localeCompare(b.name, locale));
    const originalLists = referenceRows(metadata?.equipment_lists);
    const listRows = originalLists.length ? originalLists : [{ id: "recruitment", items: band.equipment_access }];
    const equipment = listRows.map((list): ReferenceEquipmentList => ({
      id: String(list.id), name: originalLists.length ? this.knowledge.recordText(list, "name", locale) : unavailableText(locale),
      complete: originalLists.length > 0,
      ...(list.notes || list.notes_i18n ? { notes: this.knowledge.recordText(list, "notes", locale) } : {}),
      profiles: profiles.filter((profile) => ids(object(list.applies_to).profile_types).includes(String(profile.type))
        || referenceRows(profile.equipment_access).some((access) => originalLists.length ? access.list_id === list.id : true)).map((profile) => this.knowledge.recordText(profile, "name", locale)),
      items: referenceRows(list.items).map((access): ReferenceEquipment => {
        const item = items.get(String(access.item_id));
        const resolved = itemEntries.get(String(access.item_id));
        return { id: String(access.item_id), name: resolved?.name ?? catalogueLabel("item-not-published", locale), effect: resolved?.effect ?? catalogueLabel("item-not-published", locale),
          kind: String(item?.kind ?? ""), cost: access.cost,
          ...(access.notes || access.notes_i18n ? { notes: this.knowledge.recordText(access, "notes", locale) } : {}) };
      }).sort((a, b) => a.name.localeCompare(b.name, locale)),
    })).filter((list) => list.items.length);
    const categories = [...new Set(warriors.flatMap((profile) => profile.skillAccess).filter((category) => category !== "special"))];
    const skills = categories.map((category) => ({ category, entries: this.knowledge.list("skill").filter((row) => row.category === category && row.kind === "general").map((row) => {
      const resolved = skillEntries.get(String(row.id));
      return resolved ? { id: String(row.id), name: resolved.name, effect: resolved.effect } : entry(row);
    }) }));
    const abilities = local.filter((row) => row.kind && row.kind !== "warband_variant").map((row) => fromRule(String(row.id)));
    const spells = catalogue.entries("spells", locale);
    const magic = this.knowledge.campaignSection("magic");
    const assignments = referenceRows(object(magic.lore_assignments).rows).filter((row) => (row.band == null || row.band === bandId) && profiles.some((profile) => profile.id === row.profile_id));
    const lores = referenceRows(magic.lores).filter((lore) => assignments.some((row) => row.lore === lore.id)).map((lore) => ({
      id: String(lore.id), name: this.knowledge.recordText(lore, "name", locale),
      users: profiles.filter((profile) => assignments.some((row) => row.lore === lore.id && row.profile_id === profile.id)).map((profile) => this.knowledge.recordText(profile, "name", locale)),
      spells: spells.filter((spell) => spell.lore_id === lore.id),
    }));
    const variants = referenceRows(band.variants).map((variant): ReferenceVariant => ({
      ...entry(variant), gold: variant.starting_gold, rules: ids(variant.rule_ids).map(fromRule),
      members: referenceRows(variant.roster_members).map((member) => ({ name: this.knowledge.recordText(profiles.find((profile) => profile.id === member.profile_id), "name", locale), minimum: member.minimum, maximum: member.maximum })),
      lists: ids(variant.equipment_lists).map((id) => this.knowledge.recordText(originalLists.find((list) => list.id === id), "name", locale)),
      bonuses: Object.entries(object(variant.profile_bonuses)).map(([id, stats]) => ({ name: this.knowledge.recordText(profiles.find((profile) => profile.id === id), "name", locale), characteristics: object(stats) })),
    }));
    const sources = [band, ...profiles, ...local, ...originalLists];
    const sourceUrls = [...new Set(sources.flatMap((row) => [...referenceRows(row.sources), ...referenceRows(row.source_refs), ...referenceRows([row.source])]).flatMap((source) => {
      try { const url = new URL(String(source.url)); return ["https:", "http:"].includes(url.protocol) ? [url.href] : []; } catch { return []; }
    }))];
    return { id: bandId, name: this.knowledge.recordText(band, "name", locale), roster, warriors, skills, abilities, rules: rulesFor(), equipment, magic: lores, variants, sourceUrls };
  }
}
