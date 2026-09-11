/**
 * Application-level RulesCatalogue — the web counterpart of the desktop
 * `mordheim_campaign/application/rules_catalogue.py` (parity source:
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
  resolveName,
} from "../../adapters/knowledge-reader/index";
import type { ArtefactRow } from "../../adapters/knowledge-reader/artefact-types";

/** Locale code used for display text (matches the KB artefact locales). */
export type Locale = "en" | "es";

/** One browsable KB row, resolved to the requested locale. */
export interface RuleEntry {
  readonly category_id: string;
  readonly entry_id: string;
  readonly name: string;
  readonly effect: string;
  /** Free detail chips (e.g. "Speed", "Close Combat Weapon", "difficulty 7"). */
  readonly tags: readonly string[];
  /** Raw `source_refs` rows (label + url preserved for the UI). */
  readonly source_refs: readonly Readonly<Record<string, unknown>>[];
  /** Owning lore id for spell entries (used by cross-links). */
  readonly lore_id?: string;
}

/** A browsable category in display order. */
export interface RulesCategory {
  readonly category_id: string;
  readonly label: string;
}

/** One warband profile that can take / carries the browsed entry. */
export interface ProfileLink {
  readonly band: string;
  readonly profile: string;
  readonly profile_id: string;
  readonly relation: string;
}

const CATEGORY_ORDER: readonly string[] = [
  "special-rules",
  "conditions",
  "core-rules",
  "skills",
  "equipment",
  "spells",
  "scenarios",
  "injuries",
];

const CATEGORY_LABELS: Readonly<Record<string, string>> = {
  "special-rules": "Special Rules",
  conditions: "Conditions",
  "core-rules": "Core Rules",
  skills: "Skills",
  equipment: "Equipment",
  spells: "Spells",
  scenarios: "Scenarios",
  injuries: "Serious Injuries",
};

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

/** Resolve the descriptive text of a KB row for the locale (en -> es chain). */
function localizedEffect(
  row: Readonly<Record<string, unknown>>,
  locale: Locale,
): string {
  for (const key of ["effect", "description", "text", "note"]) {
    const translated = row[`${key}_i18n`];
    if (
      translated &&
      typeof translated === "object" &&
      typeof (translated as Readonly<Record<string, unknown>>)[locale] === "string"
    ) {
      return String((translated as Readonly<Record<string, unknown>>)[locale]);
    }
    if (typeof row[key] === "string") return String(row[key]);
  }
  return locale === "es"
    ? "No hay texto descriptivo disponible."
    : "No descriptive text is available.";
}

function sourceRefs(row: Readonly<Record<string, unknown>>): readonly Readonly<Record<string, unknown>>[] {
  return Array.isArray(row.source_refs) ? row.source_refs as Readonly<Record<string, unknown>>[] : [];
}

export class RulesCatalogue {
  constructor(private readonly knowledge: ArtefactKnowledgeReader) {}

  /** The browsable categories, in display order, excluding empty ones. */
  categories(): RulesCategory[] {
    return CATEGORY_ORDER
      .filter((categoryId) => this.entries(categoryId).length > 0)
      .map((categoryId) => ({
        category_id: categoryId,
        label: CATEGORY_LABELS[categoryId] ?? categoryId,
      }));
  }

  /** All rows of one category, resolved to the requested locale. */
  entries(categoryId: string, locale: Locale = "en"): RuleEntry[] {
    const rows = this.rawRows(categoryId);
    const tagged = rows.map((row) => this.toEntry(categoryId, row, locale));
    // Desktop ordering: skills/equipment grouped by tag then name; spells by name.
    return categoryId === "skills" || categoryId === "equipment"
      ? [...tagged].sort((left, right) =>
          `${(left.tags[0] ?? "")}:${left.name}`.localeCompare(
            `${(right.tags[0] ?? "")}:${right.name}`,
            locale,
          ))
      : tagged;
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
          unaccentLower(entry.effect).includes(needle)
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
   * equipment), special rules (band package rules) and spells (assigned wizard
   * lore). Categories without roster semantics yield no links.
   */
  profileLinks(categoryId: string, entry: RuleEntry, locale: Locale = "en"): ProfileLink[] {
    if (categoryId !== "skills" && categoryId !== "equipment" && categoryId !== "special-rules" && categoryId !== "spells") {
      return [];
    }
    const bands = new Map(
      this.knowledge.list("band").map((band) => [String(band.id), resolveName(band, locale)]),
    );
    const relationLabel = (relation: string) =>
      locale === "es"
        ? ({
            "starting skill": "habilidad inicial",
            "skill table": "tabla de habilidades",
            "starting equipment": "equipo inicial",
            "permitted equipment": "equipo permitido",
            "package rule": "regla de banda",
            "spell lore": "saber mágico",
          }[relation] ?? relation)
        : relation;
    const links: ProfileLink[] = [];
    for (const profile of this.knowledge.list("profile")) {
      const profileId = String(profile.id ?? "");
      const relation = this.profileRelation(categoryId, entry, profile);
      if (!relation) continue;
      links.push({
        band: bands.get(String(profile.band_id ?? "")) ?? String(profile.band_id ?? ""),
        profile: resolveName(profile, locale),
        profile_id: profileId,
        relation: relationLabel(relation),
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
                    _lore_name: resolveName(lore as ArtefactRow, "en"),
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
    const tags = this.tagsFor(categoryId, row);
    return {
      category_id: categoryId,
      entry_id: entryIdOf(row),
      name: resolveName(row as ArtefactRow, locale),
      effect: localizedEffect(row, locale),
      tags,
      source_refs: sourceRefs(row),
      ...(categoryId === "spells" && row.lore_id !== undefined ? { lore_id: String(row.lore_id) } : {}),
    };
  }

  private tagsFor(
    categoryId: string,
    row: Readonly<Record<string, unknown>>,
  ): readonly string[] {
    switch (categoryId) {
      case "skills": {
        const table = String(row.category ?? "").trim();
        return table && table !== "None" ? [titleCase(table)] : [];
      }
      case "equipment": {
        const kind = String(row.kind ?? "").trim();
        return kind ? [titleCase(kind)] : [];
      }
      case "spells": {
        const loreName = String(row._lore_name ?? "").trim() || titleCase(String(row.lore_id ?? ""));
        const difficulty = row.difficulty;
        return [difficulty !== undefined && difficulty !== null
          ? `${loreName} · difficulty ${String(difficulty)}`
          : loreName];
      }
      case "scenarios": {
        const mode = String(row.player_mode ?? "").trim();
        return mode ? [titleCase(mode)] : [];
      }
      case "injuries": {
        const applies = String(row.applies_to ?? "").trim();
        return applies ? [titleCase(applies)] : [];
      }
      default:
        return [];
    }
  }

  private profileRelation(
    categoryId: string,
    entry: RuleEntry,
    profile: ArtefactRow,
  ): string | null {
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
    if (categoryId === "special-rules") {
      return Array.isArray(profile.rule_ids) && profile.rule_ids.map(String).includes(entryId)
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
