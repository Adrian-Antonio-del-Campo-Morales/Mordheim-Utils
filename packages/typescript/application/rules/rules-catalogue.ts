/**
 * Application-level RulesCatalogue — the web counterpart of the desktop
 * The browser read model mirrors the desktop campaign rules catalogue.
 * `adapters/knowledge-reader/rules_catalogue_parity.test.ts`; coverage:
 * `rules-catalogue.test.ts`).
 *
 * Read model for the RULES browser: browsable categories in display order,
 * localized entries, accent-insensitive search and profile cross-links.
 * Pure — no React, no DOM; the KB is read through the injected
 * `ArtefactKnowledgeReader` only.
 */

import {
  ArtefactKnowledgeReader,
} from "../../adapters/knowledge-reader/index";
import type { ArtefactRow } from "../../adapters/knowledge-reader/artefact-types";
import { fieldValues, unavailableText, type ResolvedKbText } from "../../adapters/knowledge-reader/presentation";
import { adaptDistanceText } from "./distance-display";
import { catalogueJoin, catalogueLabel, catalogueNumber, cataloguePunctuation, isCatalogueLabel, type CatalogueText } from "./catalogue-text";

/** Locale code used for display text (matches the KB artefact locales). */
export type Locale = "en" | "es";

/** One browsable KB row, resolved to the requested locale. */
export interface RuleEntry {
  readonly category_id: string;
  readonly entry_id: string;
  readonly name: ResolvedKbText | CatalogueText;
  readonly effect: ResolvedKbText | CatalogueText;
  /** Free detail chips (e.g. "Speed", "Close Combat Weapon", "difficulty 7"). */
  readonly tags: readonly (ResolvedKbText | CatalogueText)[];
  /** Raw `source_refs` rows (label + url preserved for the UI). */
  readonly source_refs: readonly Readonly<Record<string, unknown>>[];
  /** Owning lore id for spell entries (used by cross-links). */
  readonly lore_id?: string;
  /** Owning band for a local band rule. */
  readonly band_id?: string;
  /** Original rule id when the browsable id is scoped by band. */
  readonly rule_id?: string;
}

/** A browsable category in display order. */
export interface RulesCategory {
  readonly category_id: string;
  readonly label: CatalogueText;
}

/** One warband profile that can take / carries the browsed entry. */
export interface ProfileLink {
  readonly band: ResolvedKbText;
  readonly profile: ResolvedKbText;
  readonly profile_id: string;
  readonly relation: CatalogueText;
}

const CATEGORY_ORDER = [
  "special-rules",
  "band-rules",
  "conditions",
  "core-rules",
  "skills",
  "equipment",
  "spells",
  "scenarios",
  "injuries",
] as const;

function unaccentLower(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
}

/** Desktop `str.title()`: "close-combat-weapon" -> "Close Combat Weapon". */
function titleCase(value: string): string {
  return value
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toLocaleUpperCase());
}

function entryIdOf(row: Readonly<Record<string, unknown>>): string {
  return String(row.id ?? row.item_id ?? "");
}

/** Resolve only fields explicitly provided in the requested locale. */
function sourceRefs(row: Readonly<Record<string, unknown>>): readonly Readonly<Record<string, unknown>>[] {
  return Array.isArray(row.source_refs) ? row.source_refs as Readonly<Record<string, unknown>>[] : [];
}

export class RulesCatalogue {
  constructor(private readonly knowledge: ArtefactKnowledgeReader) {}

  private translatedText(row: Readonly<Record<string, unknown>>, locale: Locale): ResolvedKbText | null {
    for (const field of ["effect", "description", "text", "note"] as const) {
      // Presence is structural only. A declared but untranslated field must
      // stay unavailable; a later field cannot silently replace it.
      if (field in row || `${field}_i18n` in row || Object.keys(fieldValues(row, field)).length) {
        return adaptDistanceText(this.knowledge.recordText(row, field, locale), locale, entryIdOf(row));
      }
    }
    return null;
  }

  private localizedEffect(row: Readonly<Record<string, unknown>>, locale: Locale): ResolvedKbText {
    return this.translatedText(row, locale) ?? unavailableText(locale);
  }

  /** The browsable categories, in display order, excluding empty ones. */
  categories(locale: Locale = "en"): RulesCategory[] {
    return CATEGORY_ORDER
      .filter((categoryId) => this.entries(categoryId).length > 0)
      .map((categoryId) => ({
        category_id: categoryId,
        label: catalogueLabel(categoryId, locale),
      }));
  }

  /** All rows of one category, resolved to the requested locale. */
  entries(categoryId: string, locale: Locale = "en"): RuleEntry[] {
    const rows = this.rawRows(categoryId);
    const tagged = rows.map((row) => this.toEntry(categoryId, row, locale));
    return [...tagged].sort((left, right) =>
      left.name.localeCompare(right.name, locale, { sensitivity: "base" }),
    );
  }

  /** Look up one entry by stable id; `null` when absent. */
  entry(categoryId: string, entryId: string, locale: Locale = "en"): RuleEntry | null {
    return this.entries(categoryId, locale).find((row) => row.entry_id === entryId) ?? null;
  }

  /**
   * Accent-insensitive search over names and effects, optionally scoped to a
   * category. An empty query yields no hits (desktop parity).
   */
  search(
    query: string,
    options: { readonly category_id?: string; readonly locale?: Locale } = {},
  ): RuleEntry[] {
    const locale = options.locale ?? "en";
    const needle = unaccentLower(query.trim());
    if (!needle) return [];
    const categoryIds = options.category_id
      ? [options.category_id]
      : CATEGORY_ORDER.filter((categoryId) => this.entries(categoryId).length > 0);
    const hits: RuleEntry[] = [];
    for (const categoryId of categoryIds) {
      for (const entry of this.entries(categoryId, locale)) {
        if (
          unaccentLower(entry.name).includes(needle) ||
          unaccentLower(entry.effect).includes(needle) ||
          unaccentLower(entry.tags.join(" ")).includes(needle)
        ) {
          hits.push(entry);
        }
      }
    }
    return hits;
  }

  /**
   * Warband profiles that can take / carry this entry. Supported categories:
   * skills (table access or starting skill), equipment (permitted or starting
   * equipment), shared/local rules (band package rules) and spells (assigned wizard
   * lore). Categories without roster semantics yield no links.
   */
  profileLinks(categoryId: string, entry: RuleEntry, locale: Locale = "en"): ProfileLink[] {
    if (categoryId !== "skills" && categoryId !== "equipment" && categoryId !== "special-rules" && categoryId !== "band-rules" && categoryId !== "spells") {
      return [];
    }
    const bands = new Map(
      this.knowledge.list("band").map((band) => [String(band.id), this.knowledge.recordText(band, "name", locale)]),
    );
    const links: ProfileLink[] = [];
    for (const profile of this.knowledge.list("profile")) {
      const profileId = String(profile.id ?? "");
      const relation = this.profileRelation(categoryId, entry, profile);
      if (!relation) continue;
      links.push({
        band: bands.get(String(profile.band_id ?? "")) ?? unavailableText(locale),
        profile: this.knowledge.recordText(profile, "name", locale),
        profile_id: profileId,
        relation: catalogueLabel(relation, locale),
      });
    }
    return links.sort((left, right) =>
      `${left.band}:${left.profile}`.localeCompare(`${right.band}:${right.profile}`, locale),
    );
  }

  // ------------------------------------------------------------- internals

  private rawRows(categoryId: string): readonly Readonly<Record<string, unknown>>[] {
    switch (categoryId) {
      case "special-rules":
        return this.knowledge.rulesDocument("special-rules");
      case "band-rules":
        return this.knowledge.rulesDocument("profile-special-rules");
      case "conditions":
        return this.knowledge.rulesDocument("conditions");
      case "core-rules":
        return this.knowledge.rulesDocument("core-combat");
      case "skills":
        return this.knowledge.list("skill");
      case "equipment":
        return this.knowledge.list("item");
      case "spells": {
        const lores = this.knowledge.campaignSection("magic").lores;
        return Array.isArray(lores)
          ? (lores as Readonly<Record<string, unknown>>[]).flatMap((lore) => {
              const spells = lore.spells;
              return Array.isArray(spells)
                ? (spells as Readonly<Record<string, unknown>>[]).map((spell) => ({
                    ...spell,
                    lore_id: lore.id,
                    _lore: lore,
                    _spell: spell,
                  }))
                : [];
            })
          : [];
      }
      case "scenarios": {
        const scenarios = this.knowledge.campaignSection("scenarios").scenarios;
        return Array.isArray(scenarios) ? scenarios as Readonly<Record<string, unknown>>[] : [];
      }
      case "injuries": {
        const tables = this.knowledge.campaignSection("serious-injuries").tables;
        return Array.isArray(tables) ? tables as Readonly<Record<string, unknown>>[] : [];
      }
      default:
        return [];
    }
  }

  private toEntry(
    categoryId: string,
    row: Readonly<Record<string, unknown>>,
    locale: Locale,
  ): RuleEntry {
    const tags = this.tagsFor(categoryId, row, locale);
    const effect = categoryId === "scenarios"
      ? this.scenarioText(row, locale)
      : categoryId === "injuries"
        ? this.injuryTableText(row, locale)
        : this.localizedEffect(row._spell && typeof row._spell === "object" ? row._spell as ArtefactRow : row, locale);
    const ruleId = entryIdOf(row);
    const bandId = categoryId === "band-rules" ? String(row.band_id ?? "") : "";
    const resolvedName = this.knowledge.recordText(row._spell && typeof row._spell === "object" ? row._spell as ArtefactRow : row, "name", locale);
    const name = resolvedName;
    return {
      category_id: categoryId,
      entry_id: bandId ? `${bandId}:${ruleId}` : ruleId,
      name,
      effect,
      tags,
      source_refs: sourceRefs(row),
      ...(categoryId === "spells" && row.lore_id !== undefined ? { lore_id: String(row.lore_id) } : {}),
      ...(bandId ? { band_id: bandId, rule_id: ruleId } : {}),
    };
  }

  private scenarioText(row: Readonly<Record<string, unknown>>, locale: Locale): CatalogueText {
    const parts: (CatalogueText | ResolvedKbText)[] = [this.localizedEffect(row, locale)];
    const enumValue = (value: unknown) => typeof value === "string" && isCatalogueLabel(value) ? catalogueLabel(value, locale) : unavailableText(locale);
    parts.push(catalogueJoin([
      catalogueJoin([catalogueLabel("setting", locale), enumValue(row.setting)], ": "),
      catalogueJoin([catalogueLabel("mode", locale), enumValue(row.player_mode)], ": "),
    ], " · "));
    if (typeof row.author === "string" && row.author.trim()) parts.push(catalogueJoin([catalogueLabel("author", locale), this.knowledge.recordText(row, "author", locale)], ": "));
    const progression = row.progression && typeof row.progression === "object"
      ? row.progression as Readonly<Record<string, unknown>> : {};
    const experience = Array.isArray(progression.experience)
      ? progression.experience as Readonly<Record<string, unknown>>[] : [];
    if (experience.length) {
      parts.push(catalogueJoin([catalogueLabel("experience", locale), cataloguePunctuation(":")], ""));
      for (const award of experience) {
        const ref = String(award.ref ?? "");
        const resolution = this.knowledge.resolveKbText({ kind: "record", id: ref }, "name", locale);
        const text = this.translatedText(award, locale) ?? (resolution.ok ? resolution.text : unavailableText(locale));
        parts.push(catalogueJoin([cataloguePunctuation("• "), text], ""));
      }
    }
    const loot = progression.loot && typeof progression.loot === "object"
      ? progression.loot as Readonly<Record<string, unknown>> : null;
    if (loot) {
      const lootText = this.translatedText(loot, locale);
      if (lootText) parts.push(catalogueJoin([catalogueLabel("loot", locale), lootText], ": "));
      if (Array.isArray(loot.contents)) {
        for (const content of loot.contents as Readonly<Record<string, unknown>>[]) {
          const reward = this.knowledge.recordText(content, "reward", locale);
          const roll = catalogueNumber(content.roll);
          parts.push(catalogueJoin([cataloguePunctuation("• "), catalogueJoin(roll ? [roll, reward] : [reward])], ""));
        }
      }
    }
    if (typeof progression.wyrdstone === "string") {
      parts.push(catalogueJoin([catalogueLabel("wyrdstone", locale), this.knowledge.recordText(progression, "wyrdstone", locale)], ": "));
    }
    if (Array.isArray(progression.notes)) {
      parts.push(catalogueJoin([catalogueLabel("notes", locale), this.knowledge.recordText(progression, "notes", locale)], ": "));
    }
    return catalogueJoin(parts, "\n\n");
  }

  private injuryTableText(row: Readonly<Record<string, unknown>>, locale: Locale): CatalogueText {
    const results = Array.isArray(row.results) ? row.results as Readonly<Record<string, unknown>>[] : [];
    const dice = row.dice && typeof row.dice === "object" ? row.dice as Readonly<Record<string, unknown>> : {};
    const count = catalogueNumber(dice.count) ?? unavailableText(locale);
    const sides = catalogueNumber(dice.sides) ?? unavailableText(locale);
    const diceText = catalogueJoin([count, cataloguePunctuation("D"), sides], "");
    const heading = locale === "es"
      ? catalogueJoin([catalogueLabel("table-of", locale), diceText, catalogueLabel("results", locale)])
      : catalogueJoin([diceText, catalogueLabel("results", locale)]);
    return catalogueJoin([heading, ...results.map((result) => {
      const roll = catalogueNumber(result.roll) ?? unavailableText(locale);
      const name = this.knowledge.recordText(result, "result", locale);
      const note = this.translatedText(result, locale);
      const line = catalogueJoin([roll, name], " — ");
      return note ? catalogueJoin([line, note], ": ") : line;
    })], "\n");
  }

  private tagsFor(
    categoryId: string,
    row: Readonly<Record<string, unknown>>,
    locale: Locale,
  ): readonly (ResolvedKbText | CatalogueText)[] {
    const label = (value: string): CatalogueText | null => {
      const canonical = titleCase(value);
      return isCatalogueLabel(canonical) ? catalogueLabel(canonical, locale) : null;
    };
    switch (categoryId) {
      case "skills": {
        const table = String(row.category ?? "").trim();
        return table && table !== "None" && label(table) ? [label(table)!] : [];
      }
      case "equipment": {
        const kind = String(row.kind ?? "").trim();
        return kind && label(kind) ? [label(kind)!] : [];
      }
      case "spells": {
        const loreName = row._lore && typeof row._lore === "object"
          ? this.knowledge.recordText(row._lore as ArtefactRow, "name", locale)
          : unavailableText(locale);
        const difficulty = row.difficulty;
        return [difficulty !== undefined && difficulty !== null
          ? catalogueJoin([loreName, catalogueJoin([catalogueLabel("difficulty", locale), catalogueNumber(difficulty) ?? unavailableText(locale)]),], " · ")
          : loreName];
      }
      case "scenarios": {
        const mode = String(row.player_mode ?? "").trim();
        return mode && label(mode) ? [label(mode)!] : [];
      }
      case "injuries": {
        const applies = String(row.applies_to ?? "").trim();
        return applies && label(applies) ? [label(applies)!] : [];
      }
      case "band-rules": {
        const bandId = String(row.band_id ?? "");
        const band = this.knowledge.list("band").find((item) => String(item.id) === bandId);
        // A broken reference is not player-facing metadata; never leak its id.
        return band ? [this.knowledge.recordText(band, "name", locale)] : [];
      }
      default:
        return [];
    }
  }

  private profileRelation(
    categoryId: string,
    entry: RuleEntry,
    profile: ArtefactRow,
  ): "starting skill" | "skill table" | "starting equipment" | "permitted equipment" | "special rule" | "spell lore" | null {
    const entryId = entry.entry_id;
    if (categoryId === "skills") {
      const skill = this.knowledge.list("skill").find((row) => String(row.id) === entryId);
      if (!skill) return null;
      const category = String(skill.category ?? "").toLocaleLowerCase();
      const access = Array.isArray(profile.skill_access)
        ? profile.skill_access.map((value) => String(value).toLocaleLowerCase())
        : [];
      const traits = profile.combat_traits && typeof profile.combat_traits === "object"
        ? profile.combat_traits as Readonly<Record<string, unknown>>
        : {};
      const starting = Array.isArray(traits.starting_skills)
        ? (traits.starting_skills as unknown[]).map(String)
        : [];
      if (starting.includes(entryId)) return "starting skill";
      if (category && access.includes(category)) return "skill table";
      return null;
    }
    if (categoryId === "equipment") {
      const fixed = Array.isArray(profile.fixed_equipment)
        ? (profile.fixed_equipment as unknown[]).map((value) =>
            typeof value === "string" ? value : String((value as Readonly<Record<string, unknown>>).item_id ?? ""))
        : [];
      if (fixed.includes(entryId)) return "starting equipment";
      const permitted = Array.isArray(profile.equipment_access)
        ? (profile.equipment_access as Readonly<Record<string, unknown>>[]).map((value) => String(value.item_id ?? ""))
        : [];
      if (permitted.includes(entryId)) return "permitted equipment";
      return null;
    }
    if (categoryId === "special-rules" || categoryId === "band-rules") {
      const ruleId = entry.rule_id ?? entryId;
      if (entry.band_id && String(profile.band_id ?? "") !== entry.band_id) return null;
      return Array.isArray(profile.rule_ids) && profile.rule_ids.map(String).includes(ruleId)
        ? "special rule"
        : null;
    }
    // spells
    const loreAssignments = this.knowledge.campaignSection("magic").lore_assignments as
      | Readonly<Record<string, unknown>>
      | undefined;
    const rows = Array.isArray(loreAssignments?.rows) ? loreAssignments.rows as Readonly<Record<string, unknown>>[] : [];
    const assigned = rows.some((assignment) =>
      String(assignment.profile_id ?? "") === String(profile.id ?? "") &&
      (assignment.band == null || String(assignment.band) === String(profile.band_id ?? "")) &&
      String(assignment.lore ?? "") === String(entry.lore_id ?? ""));
    return assigned ? "spell lore" : null;
  }
}
