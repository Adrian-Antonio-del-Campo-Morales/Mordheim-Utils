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
  resolveName,
} from "../../adapters/knowledge-reader/index";
import type { ArtefactRow } from "../../adapters/knowledge-reader/artefact-types";
import { adaptDistanceText } from "./distance-display";

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
  /** Owning band for a local band rule. */
  readonly band_id?: string;
  /** Original rule id when the browsable id is scoped by band. */
  readonly rule_id?: string;
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
  "band-rules",
  "conditions",
  "core-rules",
  "skills",
  "equipment",
  "spells",
  "scenarios",
  "injuries",
];

const CATEGORY_LABELS: Readonly<Record<string, string>> = {
  "special-rules": "Shared Rules",
  "band-rules": "Warband Rules",
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
  return adaptDistanceText(rawLocalizedEffect(row, locale), locale, entryIdOf(row));
}

function rawLocalizedEffect(
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
  }
  const effects = row.effects;
  if (effects && typeof effects === "object" && typeof (effects as Readonly<Record<string, unknown>>)[locale] === "string") {
    return String((effects as Readonly<Record<string, unknown>>)[locale]);
  }
  for (const key of ["effect", "description", "text", "note"]) {
    if (typeof row[key] === "string") return String(row[key]);
  }
  return locale === "es"
    ? "No hay texto descriptivo disponible."
    : "No descriptive text is available.";
}

function sourceRefs(row: Readonly<Record<string, unknown>>): readonly Readonly<Record<string, unknown>>[] {
  return Array.isArray(row.source_refs) ? row.source_refs as Readonly<Record<string, unknown>>[] : [];
}

function translatedText(row: Readonly<Record<string, unknown>>, locale: Locale): string {
  if (locale === "en") return localizedEffect(row, locale);
  let text = "";
  for (const key of ["effect", "description", "text", "note"]) {
    const values = row[`${key}_i18n`];
    if (values && typeof values === "object" && typeof (values as Readonly<Record<string, unknown>>)[locale] === "string") {
      text = String((values as Readonly<Record<string, unknown>>)[locale]);
      break;
    }
  }
  if (!text) {
    const effects = row.effects;
    text = effects && typeof effects === "object" && typeof (effects as Readonly<Record<string, unknown>>)[locale] === "string"
      ? String((effects as Readonly<Record<string, unknown>>)[locale]) : "";
  }
  return adaptDistanceText(text, locale, entryIdOf(row));
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
        : localizedEffect(row, locale);
    const ruleId = entryIdOf(row);
    const bandId = categoryId === "band-rules" ? String(row.band_id ?? "") : "";
    const name = resolveName(row as ArtefactRow, locale);
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

  private scenarioText(row: Readonly<Record<string, unknown>>, locale: Locale): string {
    const parts = [localizedEffect(row, locale)];
    parts.push(locale === "es"
      ? `Ambientación: ${String(row.setting ?? "—")} · Modalidad: ${String(row.player_mode ?? "—")} · Autor: ${String(row.author ?? "—")}`
      : `Setting: ${String(row.setting ?? "—")} · Mode: ${String(row.player_mode ?? "—")} · Author: ${String(row.author ?? "—")}`);
    const progression = row.progression && typeof row.progression === "object"
      ? row.progression as Readonly<Record<string, unknown>> : {};
    const experience = Array.isArray(progression.experience)
      ? progression.experience as Readonly<Record<string, unknown>>[] : [];
    if (experience.length) {
      parts.push(locale === "es" ? "Experiencia:" : "Experience:");
      for (const award of experience) {
        const standard: Readonly<Record<string, string>> = {
          "campaign.experience.award.survives": "Sobrevive a la batalla",
          "campaign.experience.award.winning-leader": "El jefe de la banda vencedora",
          "campaign.experience.award.per-enemy-out-of-action": "Por cada enemigo dejado fuera de combate",
        };
        const text = translatedText(award, locale);
        const fallback = locale === "es" ? standard[String(award.ref ?? "")] : titleCase(String(award.ref ?? "").split(".").pop() ?? "");
        if (text || fallback) parts.push(`• ${text || fallback}`);
      }
    }
    const loot = progression.loot && typeof progression.loot === "object"
      ? progression.loot as Readonly<Record<string, unknown>> : null;
    if (loot) {
      const lootText = translatedText(loot, locale);
      if (lootText) parts.push(`${locale === "es" ? "Botín" : "Loot"}: ${lootText}`);
      if (locale === "en" && Array.isArray(loot.contents)) {
        for (const content of loot.contents as Readonly<Record<string, unknown>>[]) {
          parts.push(`• ${String(content.roll ?? "")} ${String(content.reward ?? "")}`.trim());
        }
      }
    }
    if (locale === "en" && typeof progression.wyrdstone === "string") {
      parts.push(`Wyrdstone: ${progression.wyrdstone}`);
    }
    if (locale === "en" && Array.isArray(progression.notes)) {
      parts.push(`Notes: ${(progression.notes as unknown[]).map(String).join(" ")}`);
    }
    return parts.filter(Boolean).join("\n\n");
  }

  private injuryTableText(row: Readonly<Record<string, unknown>>, locale: Locale): string {
    const results = Array.isArray(row.results) ? row.results as Readonly<Record<string, unknown>>[] : [];
    const es: Readonly<Record<string, string>> = {
      Dead: "Muerto", "Multiple Injuries": "Heridas múltiples", "Leg Wound": "Herida en la pierna",
      "Arm Wound": "Herida en el brazo", Madness: "Locura", "Smashed Leg": "Pierna aplastada",
      "Chest Wound": "Herida en el pecho", "Blinded In One Eye": "Tuerto", "Old Battle Wound": "Vieja herida de guerra",
      "Nervous Condition": "Problema nervioso", "Hand Injury": "Herida en la mano", "Deep Wound": "Herida profunda",
      Robbed: "Robado", "Full Recovery": "Recuperación completa", "Bitter Enmity": "Enemistad acérrima",
      Captured: "Capturado", Hardened: "Curtido", "Horrible Scars": "Cicatrices horribles",
      "Sold To The Pits": "Vendido a los pozos", "Survives Against The Odds": "Sobrevive contra todo pronóstico",
      Removed: "Eliminado",
    };
    const dice = row.dice && typeof row.dice === "object" ? row.dice as Readonly<Record<string, unknown>> : {};
    const heading = locale === "es"
      ? `Tabla de ${String(dice.count ?? "")}D${String(dice.sides ?? "")}. Resultados:`
      : `${String(dice.count ?? "")}D${String(dice.sides ?? "")} table. Results:`;
    return [heading, ...results.map((result) => {
      const canonical = String(result.result ?? result.id ?? "");
      const name = locale === "es" ? es[canonical] ?? canonical : canonical;
      const note = translatedText(result, locale);
      return `${String(result.roll ?? "")} — ${name}${note ? `: ${note}` : ""}`;
    })].join("\n");
  }

  private tagsFor(
    categoryId: string,
    row: Readonly<Record<string, unknown>>,
    locale: Locale,
  ): readonly string[] {
    const label = (value: string) => {
      const canonical = titleCase(value);
      if (locale !== "es") return canonical;
      return ({
        Speed: "Velocidad", Combat: "Combate", Shooting: "Disparo", Academic: "Académicas", Strength: "Fuerza", Special: "Especiales",
        "Close Combat Weapon": "Arma de combate cuerpo a cuerpo", "Ranged Weapon": "Arma a distancia", Armour: "Armadura",
        "Shield Or Defence": "Escudo o defensa", "Combat Equipment": "Equipo de combate", "Material Or Upgrade": "Material o mejora",
        Hero: "Héroe", Henchman: "Secuaz", Multiplayer: "Multijugador",
      } as Readonly<Record<string, string>>)[canonical] ?? canonical;
    };
    switch (categoryId) {
      case "skills": {
        const table = String(row.category ?? "").trim();
        return table && table !== "None" ? [label(table)] : [];
      }
      case "equipment": {
        const kind = String(row.kind ?? "").trim();
        return kind ? [label(kind)] : [];
      }
      case "spells": {
        const loreName = row._lore && typeof row._lore === "object"
          ? resolveName(row._lore as ArtefactRow, locale)
          : titleCase(String(row.lore_id ?? ""));
        const difficulty = row.difficulty;
        return [difficulty !== undefined && difficulty !== null
          ? `${loreName} · difficulty ${String(difficulty)}`
          : loreName];
      }
      case "scenarios": {
        const mode = String(row.player_mode ?? "").trim();
        return mode ? [label(mode)] : [];
      }
      case "injuries": {
        const applies = String(row.applies_to ?? "").trim();
        return applies ? [label(applies)] : [];
      }
      case "band-rules": {
        const bandId = String(row.band_id ?? "");
        const band = this.knowledge.list("band").find((item) => String(item.id) === bandId);
        return band ? [resolveName(band, locale)] : bandId ? [bandId] : [];
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
