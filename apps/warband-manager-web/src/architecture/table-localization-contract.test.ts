import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { isUiMessageKey, translate } from "../features/campaign/i18n-core";

type TableContract = {
  readonly source: string;
  readonly test: string;
  readonly tables: readonly { readonly className: string; readonly columns: number }[];
};

/**
 * Exhaustive table inventory. Adding a table requires adding it here and a
 * rendered feature test; each header and mobile cell label must come from the
 * selected locale rather than a stored ID, tag, or canonical English phrase.
 */
const tables: readonly TableContract[] = [
  { source: "features/advances/AdvancesPanel.tsx", test: "features/advances/PostBattleExperience.test.tsx", tables: [{ className: "advance-results", columns: 3 }] },
  { source: "features/equipment/EquipmentPanel.tsx", test: "features/equipment/EquipmentPanel.test.tsx", tables: [{ className: "mobile-cards", columns: 3 }] },
  { source: "features/exploration/ExplorationPanel.tsx", test: "features/exploration/ExplorationPanel.test.tsx", tables: [{ className: "exploration-results", columns: 2 }] },
  { source: "features/hirelings/HirelingsPanel.tsx", test: "features/hirelings/HirelingsPanel.test.tsx", tables: [{ className: "mobile-cards", columns: 5 }, { className: "mobile-cards", columns: 4 }, { className: "mobile-cards", columns: 3 }] },
  { source: "features/injuries/InjuriesPanel.tsx", test: "features/injuries/InjuriesPanel.test.tsx", tables: [{ className: "mobile-cards", columns: 5 }] },
  { source: "features/injuries/PostBattleInjuries.tsx", test: "features/injuries/PostBattleInjuries.test.tsx", tables: [{ className: "injury-results", columns: 3 }] },
  { source: "features/recruitment/GroupRecruitmentPanel.tsx", test: "features/recruitment/GroupRecruitmentPanel.test.tsx", tables: [{ className: "mobile-cards", columns: 6 }] },
  { source: "features/review/ReviewPanel.tsx", test: "features/review/ReviewPanel.test.tsx", tables: [{ className: "", columns: 6 }] },
];

const sourceRoot = resolve(process.cwd(), "src");

function text(path: string): string {
  return readFileSync(resolve(sourceRoot, path), "utf8");
}

describe("all web table localization contracts", () => {
  it("keeps a rendered test and a locale-aware header contract for every table", () => {
    for (const contract of tables) {
      const component = text(contract.source);
      expect(existsSync(resolve(sourceRoot, contract.test)), `${contract.source} needs a rendered test`).toBe(true);
      expect((component.match(/<table\b/g) ?? []).length, `${contract.source} table count`).toBe(contract.tables.length);
      expect((component.match(/<th\b/g) ?? []).length, `${contract.source} column count`).toBe(contract.tables.reduce((total, table) => total + table.columns, 0));
      expect(component, `${contract.source} must select table copy by locale`).toMatch(/translate\(\{\s*key:\s*"[^"]+"\s*\},\s*locale\)/);
      if (contract.tables.some((table) => table.className)) {
        const dataLabels = [...component.matchAll(/data-label=\{([^}]+)\}/g)].map((match) => match[1]);
        expect(dataLabels, `${contract.source} must label every mobile cell`).not.toHaveLength(0);
        for (const label of dataLabels) expect(label, `${contract.source} data label`).not.toMatch(/(?:\.id|_id|\.tag)/);
      }
    }
  });

  it("requires every table to select all of its interface copy by locale", () => {
    for (const contract of tables) {
      const component = text(contract.source);
      const keys = [...component.matchAll(/translate\(\{ key: "([^"]+)" \}, locale\)/g)].map((match) => match[1]);
      expect(keys.length, `${contract.source} uses the shared catalogue`).toBeGreaterThan(0);
      for (const key of keys) {
        expect(isUiMessageKey(key), key).toBe(true);
        if (!isUiMessageKey(key)) throw new Error(`Missing message ${key}`);
        for (const locale of ["es", "en"] as const) expect(translate({ key }, locale).trim(), `${key}.${locale}`).not.toBe("");
      }
    }
  });
});
