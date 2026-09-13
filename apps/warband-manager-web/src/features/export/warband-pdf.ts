/**
 * Printable warband roster sheet — port of the desktop exporter
 * (`packages/python/campaign/mordheim_campaign/persistence/warband_pdf.py`).
 *
 * Renders the warband of one timeline moment as a sheet in the style of the
 * printed Mordheim warband rosters: one rounded parchment card per warrior
 * (name/type ruled rows, the black characteristic table, an EQUIPMENT /
 * SKILLS split, and the XP tick-box band), heroes and hired swords first,
 * then henchman groups, closing with a warband-summary page (treasure,
 * warband value, stored equipment, battle log).
 *
 * A committed state renders its own snapshot (deep-copied at commit time), so
 * a historical moment exports exactly as it was; the draft (or any non-state
 * moment) renders the live roster. Layout units are millimetres and follow
 * the desktop constants (A4 210×297, 10 mm margins, 190 mm card width) so the
 * two exporters stay comparable.
 *
 * Rendering uses the pdf-lib Times core fonts — the same Times family the
 * desktop used via fpdf2 — and transliterates glyphs outside WinAnsi so
 * generation never crashes on campaign data.
 */
import { PDFDocument, StandardFonts, rgb, type PDFFont, type PDFPage } from "pdf-lib";

import { experienceTotal, modelCount, rating, treasury } from "@domain/campaign/kernel/document";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import type { Battle, CampaignDocument, InventoryItem, TimelineState, Warrior } from "../campaign/types";
import { knowledgeName, readableValue } from "../campaign/displayText";
import { adaptCharacteristicValue } from "@app/rules/distance-display";

type Locale = "es" | "en";
type RGB = ReturnType<typeof rgb>;

// --- Geometry (millimetres, matching the desktop constants) -----------------
const PT = 72 / 25.4; // PDF points per millimetre
const PAGE_W = 210;
const PAGE_H = 297;
const LM = 10;
const TM = 10;
const RM = 10;
const BREAK_TRIGGER = PAGE_H - 16;
const CARD_TOTAL_WIDTH = 190;
const LEFT_COL_W = 60;
const MID_COL_W = 60;
const HERO_CARD_HEIGHT = 39;
const HENCHMAN_CARD_HEIGHT = 30;
const CARD_GAP = 2.5;
const CARD_AREA_BOTTOM = PAGE_H - 22;

const px = (mm: number) => mm * PT;
const py = (mm: number) => (PAGE_H - mm) * PT;

// --- Mordheim palette: aged parchment and iron-gall ink ---------------------
const PARCHMENT = rgb(246 / 255, 240 / 255, 222 / 255);
const INK = rgb(42 / 255, 33 / 255, 24 / 255);
const INK_SOFT = rgb(110 / 255, 90 / 255, 62 / 255);
const BOX_FILL_EARNED = rgb(206 / 255, 194 / 255, 166 / 255);
const WHITE = rgb(1, 1, 1);

/** Canonical storage order of the characteristics and their sheet headers. */
const STAT_KEYS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const;
const STAT_HEADERS: Record<Locale, readonly string[]> = {
  en: ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"],
  es: ["M", "HA", "HP", "F", "R", "H", "I", "A", "L"],
};

/** XP tracks: heroes and hired swords 2×45, henchman groups a single 14. */
const HERO_XP_ROWS = 2;
const HERO_XP_PER_ROW = 45;
const HENCHMAN_XP_PER_ROW = 14;
const HERO_ADVANCE_THRESHOLDS = new Set([2, 4, 6, 8, 11, 14, 17, 20, 24, 28, 32, 36, 41, 46, 51, 57, 63, 69, 76, 83, 90]);
const HENCHMAN_ADVANCE_THRESHOLDS = new Set([2, 5, 9, 14]);

/** Transliteration of glyphs outside the Times/WinAnsi core charset. */
const TRANSLITERATION: Record<string, string> = {
  "\u2014": "-",
  "\u2013": "-",
  "\u2212": "-",
  "\u2018": "'",
  "\u2019": "'",
  "\u201c": '"',
  "\u201d": '"',
  "\u2026": "...",
  "\u26a0": "!",
  "\u{1f3b2}": "[dice]",
  "\u2192": "->",
  "\u2039": "<",
  "\u203a": ">",
  "\u2022": "-",
  "\u00a0": " ",
  "\u00d7": "x",
};

interface Fonts {
  readonly normal: PDFFont;
  readonly bold: PDFFont;
  readonly italic: PDFFont;
  readonly boldItalic: PDFFont;
}

type FontStyle = keyof Fonts;

/** Locale labels, mirroring the desktop STRINGS catalogue for these keys. */
function buildLabels(locale: Locale) {
  if (locale === "es") {
    return {
      draft: "BORRADOR",
      state: (number: number) => `ESTADO #${number}`,
      battle: (number: number) => `Batalla #${number}`,
      advances: "Mejoras",
      name: "Nombre",
      type: "Tipo",
      equipment: "Equipamiento",
      skills: "Habilidades",
      number: "Número",
      warbandName: "NOMBRE DE LA BANDA:",
      warbandType: "TIPO DE BANDA:",
      treasure: "TESORO",
      goldCrowns: "Coronas de Oro:",
      wyrdstone: "Piedra Bruja:",
      warbandValue: "VALOR DE LA BANDA",
      totalExperience: "Experiencia Total:",
      members: (models: number) => `Miembros ( ${models} ) x 5:`,
      rating: "Valor:",
      storedEquipment: "EQUIPO ALMACENADO",
      notes: "NOTAS",
    };
  }
  return {
    draft: "DRAFT",
    state: (number: number) => `STATE #${number}`,
    battle: (number: number) => `Battle #${number}`,
    advances: "Advances",
    name: "Name",
    type: "Type",
    equipment: "Equipment",
    skills: "Skills",
    number: "Number",
    warbandName: "Warband name:",
    warbandType: "Warband type:",
    treasure: "Treasure",
    goldCrowns: "Gold Crowns:",
    wyrdstone: "Wyrdstone:",
    warbandValue: "Warband value",
    totalExperience: "Total experience:",
    members: (models: number) => `Members ( ${models} ) x 5:`,
    rating: "Rating:",
    storedEquipment: "Stored equipment",
    notes: "Notes",
  };
}

type Labels = ReturnType<typeof buildLabels>;

interface RectOptions {
  readonly fill?: RGB;
  readonly border?: RGB;
  readonly lineWidth?: number;
  readonly round?: boolean;
  readonly radius?: number;
}

/** A4 parchment document with a per-page ink frame and page-number footer. */
class Sheet {
  private readonly allowed: Set<number>;
  private page!: PDFPage;
  private pageNo = 0;
  private font: PDFFont;
  private fontSize = 10;
  private textColor: RGB = INK;
  private drawColor: RGB = INK;
  private fillColor: RGB = WHITE;
  private lineWidth = 0.2;

  x = LM;
  y = TM;

  constructor(private readonly pdf: PDFDocument, private readonly fonts: Fonts) {
    this.font = fonts.normal;
    this.allowed = new Set(fonts.normal.getCharacterSet());
  }

  /** Screen arbitrary campaign text down to the WinAnsi core charset. */
  private safe(raw: string): string {
    let out = "";
    for (const ch of String(raw ?? "")) {
      const mapped = TRANSLITERATION[ch];
      if (mapped !== undefined) {
        out += mapped;
        continue;
      }
      out += this.allowed.has(ch.codePointAt(0) as number) ? ch : "?";
    }
    return out;
  }

  private header(): void {
    this.page.drawRectangle({ x: 0, y: 0, width: px(PAGE_W), height: px(PAGE_H), color: PARCHMENT });
    this.page.drawRectangle({ x: px(7), y: py(290), width: px(196), height: px(283), borderColor: INK_SOFT, borderWidth: px(0.4) });
    this.page.drawRectangle({ x: px(8.5), y: py(288.5), width: px(193), height: px(280), borderColor: INK_SOFT, borderWidth: px(0.15) });
    this.textColor = INK;
  }

  private footer(): void {
    const text = String(this.pageNo);
    const size = 8;
    const width = PAGE_W - RM - LM;
    const tw = this.fonts.italic.widthOfTextAtSize(text, size);
    this.page.drawText(text, {
      x: px(LM + (width - tw) / 2),
      y: py(281 + this.baselineMm(6, size)),
      size,
      font: this.fonts.italic,
      color: INK_SOFT,
    });
  }

  /** Baseline offset (mm) that vertically centres a line in a cell. */
  private baselineMm(cellHeight: number, size = this.fontSize): number {
    const line = this.font.heightAtSize(size);
    const ascent = this.font.heightAtSize(size, { descender: false });
    return (cellHeight - line / PT) / 2 + ascent / PT;
  }

  addPage(): void {
    this.page = this.pdf.addPage([px(PAGE_W), px(PAGE_H)]);
    this.pageNo += 1;
    this.header();
    this.footer();
    this.x = LM;
    this.y = TM;
  }

  setFont(style: FontStyle, size: number): void {
    this.font = this.fonts[style];
    this.fontSize = size;
  }

  setTextColor(color: RGB): void {
    this.textColor = color;
  }

  setDrawColor(color: RGB): void {
    this.drawColor = color;
  }

  setFillColor(color: RGB): void {
    this.fillColor = color;
  }

  setLineWidth(width: number): void {
    this.lineWidth = width;
  }

  setXY(x: number, y: number): void {
    this.x = x;
    this.y = y;
  }

  setY(y: number): void {
    this.y = y;
  }

  getY(): number {
    return this.y;
  }

  ln(height: number): void {
    this.y += height;
    this.x = LM;
  }

  private ensureSpace(height: number): void {
    if (this.y + height > BREAK_TRIGGER) this.addPage();
  }

  rect(x: number, y: number, w: number, h: number, options: RectOptions = {}): void {
    const { fill, border, lineWidth = 0.2, round = false, radius = 2 } = options;
    if (round) {
      const r = Math.max(0, Math.min(radius, Math.min(w, h) / 2));
      this.page.drawSvgPath(roundedRectPath(w, h, r), {
        x: px(x),
        y: py(y),
        scale: PT,
        color: fill,
        borderColor: border,
        borderWidth: border ? lineWidth : undefined,
      });
      return;
    }
    this.page.drawRectangle({
      x: px(x),
      y: py(y + h),
      width: px(w),
      height: px(h),
      color: fill,
      borderColor: border,
      borderWidth: border ? px(lineWidth) : undefined,
    });
  }

  line(x1: number, y1: number, x2: number, y2: number): void {
    this.page.drawLine({
      start: { x: px(x1), y: py(y1) },
      end: { x: px(x2), y: py(y2) },
      thickness: px(this.lineWidth),
      color: this.drawColor,
    });
  }

  polygon(points: readonly (readonly [number, number])[], color: RGB): void {
    const path = `${points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ")} Z`;
    this.page.drawSvgPath(path, { x: px(0), y: py(0), scale: PT, color });
  }

  cell(
    w: number,
    h: number,
    raw: string,
    options: { border?: boolean; align?: "L" | "C" | "R"; fill?: boolean; newX?: "RIGHT" | "LMARGIN"; newY?: "TOP" | "NEXT" } = {},
  ): void {
    const { border = false, align = "L", fill = false, newX = "RIGHT", newY = "TOP" } = options;
    this.ensureSpace(h);
    const width = w > 0 ? w : PAGE_W - RM - this.x;
    const x0 = this.x;
    const y0 = this.y;
    if (fill) this.rect(x0, y0, width, h, { fill: this.fillColor });
    if (border) this.rect(x0, y0, width, h, { border: this.drawColor, lineWidth: this.lineWidth });
    const text = this.safe(raw);
    if (text) {
      const tw = this.font.widthOfTextAtSize(text, this.fontSize);
      const tx = align === "C" ? x0 + (width - tw) / 2 : align === "R" ? x0 + width - tw : x0;
      this.page.drawText(text, {
        x: px(tx),
        y: py(y0 + this.baselineMm(h)),
        size: this.fontSize,
        font: this.font,
        color: this.textColor,
      });
    }
    this.x = newX === "LMARGIN" ? LM : x0 + width;
    this.y = newY === "NEXT" ? y0 + h : y0;
  }

  multiCell(width: number, lineHeight: number, raw: string): void {
    for (const line of this.wrap(raw, width)) {
      this.ensureSpace(lineHeight);
      if (line) {
        this.page.drawText(line, {
          x: px(this.x),
          y: py(this.y + this.baselineMm(lineHeight)),
          size: this.fontSize,
          font: this.font,
          color: this.textColor,
        });
      }
      this.y += lineHeight;
    }
    this.x = LM;
  }

  private wrap(raw: string, width: number): string[] {
    const text = this.safe(raw);
    const maxWidth = px(width);
    const lines: string[] = [];
    for (const paragraph of text.split("\n")) {
      if (paragraph.length === 0) {
        lines.push("");
        continue;
      }
      let line = "";
      for (const word of paragraph.split(/\s+/).filter(Boolean)) {
        const candidate = line ? `${line} ${word}` : word;
        if (line && this.font.widthOfTextAtSize(candidate, this.fontSize) > maxWidth) {
          lines.push(line);
          line = word;
        } else {
          line = candidate;
        }
      }
      if (line) lines.push(line);
    }
    return lines;
  }
}

/** SVG y-down rounded-rectangle path in millimetres. */
function roundedRectPath(w: number, h: number, r: number): string {
  return [
    `M ${r} 0`,
    `H ${w - r}`,
    `A ${r} ${r} 0 0 1 ${w} ${r}`,
    `V ${h - r}`,
    `A ${r} ${r} 0 0 1 ${w - r} ${h}`,
    `H ${r}`,
    `A ${r} ${r} 0 0 1 0 ${h - r}`,
    `V ${r}`,
    `A ${r} ${r} 0 0 1 ${r} 0`,
    "Z",
  ].join(" ");
}

interface RenderContext {
  readonly sheet: Sheet;
  readonly labels: Labels;
  readonly locale: Locale;
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly bandId: string;
}

function momentLabel(campaign: CampaignDocument["campaign"], stateNumber: number | null, labels: Labels): string {
  if (stateNumber === null) return labels.draft;
  const snapshot = campaign.states.find((row) => row.number === stateNumber);
  let label = labels.state(stateNumber);
  if (!snapshot) return label;
  if (snapshot.date) label += ` - ${snapshot.date}`;
  if (snapshot.label) label += ` - ${snapshot.label}`;
  return label;
}

// ---------------------------------------------------------------------------
// Warrior card
// ---------------------------------------------------------------------------

function statValues(warrior: Warrior, locale: Locale): string[] {
  return STAT_KEYS.map((key) => {
    const value = warrior.stats[key];
    if (value === undefined || value === null) return "";
    return adaptCharacteristicValue(key, value, locale, warrior.stat_modifiers?.[key] ?? 0);
  });
}

function equipmentLines(warrior: Warrior, knowledge: ArtefactKnowledgeReader | undefined, locale: Locale): string {
  // In a multi-minion group every listed quantity is the group size (already
  // shown on the type line): the printed sheets list bare item names.
  const groupSize = warrior.quantity ?? 1;
  return warrior.equipment
    .map((entry) => {
      const name = knowledgeName(knowledge, "item", entry.item_id, locale, entry.name);
      return groupSize > 1 || entry.quantity <= 1 ? name : `${name} x${entry.quantity}`;
    })
    .join("\n");
}

function skillsLines(warrior: Warrior, labels: Labels, knowledge: ArtefactKnowledgeReader | undefined, locale: Locale, bandId: string): string {
  const lines = warrior.skills.map((skill) => knowledgeName(knowledge, "skill", skill, locale, skill, warrior.profile_id, bandId));
  if (warrior.condition) {
    let line = readableValue(warrior.condition, locale);
    if (warrior.condition_detail) {
      line += ` (${knowledgeName(knowledge, "injury", warrior.condition_detail, locale, warrior.condition_detail)})`;
    }
    lines.push(line);
  }
  const advances = warrior.stat_advances ?? {};
  if (Object.keys(advances).length > 0) {
    const rendered = Object.entries(advances)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key} +${value}`)
      .join(", ");
    lines.push(`${labels.advances}: ${rendered}`);
  }
  return lines.join("\n");
}

function typeText(warrior: Warrior, knowledge: ArtefactKnowledgeReader | undefined, locale: Locale): string {
  let text = knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name || warrior.kind);
  const groupSize = warrior.quantity ?? 1;
  if (groupSize > 1) text += ` x${groupSize}`;
  return text;
}

function statBlock(sheet: Sheet, x: number, y: number, warrior: Warrior, headerH: number, valueH: number, locale: Locale): void {
  const headers = STAT_HEADERS[locale] ?? STAT_HEADERS.en;
  const cellW = (LEFT_COL_W - 4) / STAT_KEYS.length;
  sheet.setFont("bold", 6.5);
  sheet.setTextColor(PARCHMENT);
  sheet.setFillColor(INK);
  sheet.setDrawColor(INK);
  sheet.setLineWidth(0.25);
  headers.forEach((header, index) => {
    sheet.setXY(x + index * cellW, y);
    sheet.cell(cellW, headerH, header, { border: true, align: "C", fill: true });
  });
  sheet.setFont("normal", 8);
  sheet.setTextColor(INK);
  sheet.setFillColor(WHITE);
  statValues(warrior, locale).forEach((value, index) => {
    sheet.setXY(x + index * cellW, y + headerH);
    sheet.cell(cellW, valueH, value, { border: true, align: "C", fill: true });
  });
}

function boxRegion(sheet: Sheet, x: number, y: number, width: number, label: string, content: string, ruleX1: number, ruleX2: number): void {
  sheet.setXY(x, y);
  sheet.setFont("bold", 9);
  sheet.setTextColor(INK);
  sheet.cell(width, 4.2, label);
  sheet.setLineWidth(0.25);
  sheet.line(ruleX1, y + 4.6, ruleX2, y + 4.6);
  if (content) {
    sheet.setXY(x, y + 5.2);
    sheet.setFont("normal", 7.5);
    sheet.multiCell(width, 3.0, content);
  }
}

function xpBoxes(
  sheet: Sheet,
  x: number,
  y: number,
  experience: number,
  perRow: number,
  rows: number,
  boxW: number,
  boxH: number,
  stride: number,
  thresholds: Set<number>,
  bandWidth?: number,
): void {
  const capacity = perRow * rows;
  const reached = Math.trunc(Number(experience) || 0);
  const step = bandWidth !== undefined ? (bandWidth - boxW) / (perRow - 1) : stride;
  const bandW = (perRow - 1) * step + boxW;
  const startX = x + (CARD_TOTAL_WIDTH - bandW) / 2;
  for (let index = 0; index < capacity; index += 1) {
    const number = index + 1;
    const row = Math.floor(index / perRow);
    const column = index % perRow;
    sheet.rect(startX + column * step, y + row * (boxH + 1.0), boxW, boxH, {
      fill: number <= reached ? BOX_FILL_EARNED : WHITE,
      border: INK,
      lineWidth: thresholds.has(number) ? 0.55 : 0.2, // thicker border = advance point
    });
  }
}

function warriorCard(ctx: RenderContext, warrior: Warrior, y: number, height: number): void {
  const { sheet, labels, locale, knowledge, bandId } = ctx;
  const x = LM;
  const hero = warrior.kind === "hero";
  // Hero cards fit six per page, henchman cards eight.
  const geometry = hero
    ? { nameY: y + 1.2, nameRule: y + 5.9, typeY: y + 6.2, typeRule: y + 10.4, statsY: y + 11.4, bandH: 12, headerH: 4.2, valueH: 5.0 }
    : { nameY: y + 0.9, nameRule: y + 5.2, typeY: y + 5.5, typeRule: y + 9.5, statsY: y + 10.4, bandH: 8, headerH: 4.0, valueH: 4.6 };
  const topH = height - geometry.bandH;

  sheet.rect(x, y, CARD_TOTAL_WIDTH, height, { round: true, radius: 3, fill: PARCHMENT, border: INK, lineWidth: 0.9 });
  sheet.rect(x + 1.1, y + 1.1, CARD_TOTAL_WIDTH - 2.2, height - 2.2, { round: true, radius: 2.2, border: INK_SOFT, lineWidth: 0.2 });
  sheet.setDrawColor(INK);
  sheet.setTextColor(INK);

  const lx = x + 2.5;
  const labelW = 19;
  sheet.setLineWidth(0.25);
  sheet.setXY(lx, geometry.nameY);
  sheet.setFont("bold", 9.5);
  sheet.cell(labelW, 4.3, labels.name);
  sheet.setFont("normal", 8);
  sheet.cell(LEFT_COL_W - labelW - 2.5, 4.3, warrior.name);
  sheet.line(lx, geometry.nameRule, x + LEFT_COL_W - 2.5, geometry.nameRule);

  sheet.setXY(lx, geometry.typeY);
  sheet.setFont("bold", 8.5);
  sheet.cell(labelW, 3.8, labels.type);
  sheet.setFont("normal", 7);
  sheet.cell(LEFT_COL_W - labelW - 2.5, 3.8, typeText(warrior, knowledge, locale));
  sheet.line(lx, geometry.typeRule, x + LEFT_COL_W - 2.5, geometry.typeRule);

  statBlock(sheet, lx, geometry.statsY, warrior, geometry.headerH, geometry.valueH, locale);

  sheet.line(x + LEFT_COL_W, y + 1, x + LEFT_COL_W, y + topH - 1);
  sheet.line(x + LEFT_COL_W + MID_COL_W, y + 1, x + LEFT_COL_W + MID_COL_W, y + topH - 1);
  boxRegion(
    sheet,
    x + LEFT_COL_W + 2.5,
    y + 1.4,
    MID_COL_W - 5,
    labels.equipment,
    equipmentLines(warrior, knowledge, locale),
    x + LEFT_COL_W + 1,
    x + LEFT_COL_W + MID_COL_W - 1,
  );
  boxRegion(
    sheet,
    x + LEFT_COL_W + MID_COL_W + 2.5,
    y + 1.4,
    CARD_TOTAL_WIDTH - LEFT_COL_W - MID_COL_W - 5,
    labels.skills,
    skillsLines(warrior, labels, knowledge, locale, bandId),
    x + LEFT_COL_W + MID_COL_W + 1,
    x + CARD_TOTAL_WIDTH - 1,
  );

  sheet.line(x + 1, y + topH, x + CARD_TOTAL_WIDTH - 1, y + topH);
  if (hero) {
    xpBoxes(sheet, x, y + topH + 2, warrior.experience, HERO_XP_PER_ROW, HERO_XP_ROWS, 3.4, 3.0, 4.2, HERO_ADVANCE_THRESHOLDS, 182);
  } else {
    sheet.setXY(x + 2.5, y + topH + 1.6);
    sheet.setFont("bold", 8.5);
    sheet.cell(24, 4.2, labels.number);
    sheet.setFont("normal", 7);
    sheet.cell(10, 4.2, `${Math.trunc(Number(warrior.experience) || 0)} XP`);
    xpBoxes(sheet, x, y + topH + 2.4, warrior.experience, HENCHMAN_XP_PER_ROW, 1, 4.6, 3.2, 5.7, HENCHMAN_ADVANCE_THRESHOLDS);
  }
}

// ---------------------------------------------------------------------------
// Summary page
// ---------------------------------------------------------------------------

function pageTitle(sheet: Sheet, title: string): void {
  sheet.setTextColor(INK);
  sheet.setFont("bold", 15);
  sheet.cell(0, 9, title.toUpperCase().split("").join(" "), { align: "C", newX: "LMARGIN", newY: "NEXT" });
  const y = sheet.getY() + 0.5;
  const midX = LM + CARD_TOTAL_WIDTH / 2;
  sheet.setDrawColor(INK_SOFT);
  sheet.setLineWidth(0.35);
  sheet.line(LM + 15, y, midX - 7, y);
  sheet.line(midX + 7, y, LM + CARD_TOTAL_WIDTH - 15, y);
  sheet.polygon(
    [
      [midX, y - 1.6],
      [midX + 1.6, y],
      [midX, y + 1.6],
      [midX - 1.6, y],
    ],
    INK,
  );
  sheet.ln(3.5);
}

function summaryBox(sheet: Sheet, x: number, y: number, w: number, h: number, title: string, lines: readonly string[]): void {
  sheet.rect(x, y, w, h, { round: true, radius: 3, fill: WHITE, border: INK, lineWidth: 0.45 });
  sheet.rect(x + 1, y + 1, w - 2, h - 2, { round: true, radius: 2.2, border: INK_SOFT, lineWidth: 0.15 });
  sheet.setXY(x + 4, y + 3);
  sheet.setFont("bold", 12);
  sheet.setTextColor(INK);
  sheet.cell(w - 8, 6, title);
  sheet.setDrawColor(INK_SOFT);
  sheet.setLineWidth(0.25);
  sheet.line(x + 4, y + 9.8, x + w - 4, y + 9.8);
  sheet.setXY(x + 4, y + 11);
  sheet.setFont("normal", 10.5);
  sheet.setTextColor(INK);
  if (lines.length) sheet.multiCell(w - 8, 5.4, lines.join("\n"));
}

function summaryData(campaign: CampaignDocument["campaign"], snapshot: TimelineState | undefined) {
  if (snapshot) {
    return { gold: snapshot.gold, shards: snapshot.wyrdstone, xp: snapshot.experience, models: snapshot.models, value: snapshot.rating };
  }
  return {
    gold: treasury(campaign),
    shards: 0,
    xp: experienceTotal(campaign.warriors),
    models: modelCount(campaign.warriors),
    value: rating(campaign.warriors),
  };
}

function renderSummaryPage(
  ctx: RenderContext,
  campaign: CampaignDocument["campaign"],
  inventory: readonly InventoryItem[],
  snapshot: TimelineState | undefined,
  moment: string,
): void {
  const { sheet, labels, locale, knowledge } = ctx;
  sheet.addPage();
  sheet.setFont("italic", 8.5);
  sheet.setTextColor(INK_SOFT);
  sheet.cell(0, 5, moment, { align: "R", newX: "LMARGIN", newY: "NEXT" });
  sheet.ln(1);

  const data = summaryData(campaign, snapshot);
  pageTitle(sheet, campaign.identity.warband_name);
  sheet.setFont("bold", 12);
  sheet.setTextColor(INK);
  sheet.cell(0, 7, `${labels.warbandName} ${campaign.identity.warband_name}`, { newX: "LMARGIN", newY: "NEXT" });
  sheet.cell(0, 7, `${labels.warbandType} ${campaign.identity.warband_type}`, { newX: "LMARGIN", newY: "NEXT" });

  const y = sheet.getY() + 4;
  const boxW = (CARD_TOTAL_WIDTH - 8) / 2;
  summaryBox(sheet, LM, y, boxW, 30, labels.treasure, [
    `${labels.goldCrowns} ${data.gold}`,
    "",
    `${labels.wyrdstone} ${data.shards}`,
  ]);
  summaryBox(sheet, LM + boxW + 8, y, boxW, 30, labels.warbandValue, [
    `${labels.totalExperience} ${data.xp}`,
    labels.members(data.models),
    `${labels.rating} ${data.value}`,
  ]);

  const stashLines = inventory
    .filter((item) => item.stash > 0)
    .map((item) => {
      const name = knowledgeName(knowledge, "item", item.id, locale, item.name);
      return item.stash > 1 ? `${name} x${item.stash}` : name;
    });
  const battleLines = campaign.battles
    .filter((battle) => !snapshot || battle.number <= snapshot.number)
    .map((battle: Battle) => {
      const scenario = knowledgeName(knowledge, "scenario", battle.scenario, locale, battle.scenario);
      return `${labels.battle(battle.number)} - ${scenario} vs. ${battle.opponent} - ${readableValue(battle.result, locale)}`;
    });
  const boxH = PAGE_H - y - 30 - 20;
  summaryBox(sheet, LM, y + 38, boxW, boxH, labels.storedEquipment, stashLines);
  summaryBox(sheet, LM + boxW + 8, y + 38, boxW, boxH, labels.notes, battleLines);
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

function renderGroup(ctx: RenderContext, warriors: readonly Warrior[], cardHeight: number): void {
  const { sheet } = ctx;
  // Homogeneous spacing: a group that fills one page spreads evenly from the
  // top margin to the card area bottom; otherwise the minimum gap keeps
  // multi-page flow compact.
  const area = CARD_AREA_BOTTOM - TM;
  const count = warriors.length;
  let gap = CARD_GAP;
  if (count > 1 && count * (cardHeight + CARD_GAP) - CARD_GAP <= area) {
    gap = Math.min(8, (area - count * cardHeight) / (count - 1));
  }
  for (const warrior of warriors) {
    let y0 = sheet.getY();
    if (y0 + cardHeight > CARD_AREA_BOTTOM) {
      sheet.addPage();
      y0 = sheet.getY();
    }
    warriorCard(ctx, warrior, y0, cardHeight);
    // The card's own drawing moves the cursor, so the next position is
    // computed from the card origin to keep spacing regular.
    sheet.setY(y0 + cardHeight + gap);
  }
}

export async function createWarbandPdf(
  document: CampaignDocument,
  locale: Locale,
  knowledge?: ArtefactKnowledgeReader,
): Promise<Uint8Array> {
  const { campaign } = document;
  const pdf = await PDFDocument.create();
  const fonts: Fonts = {
    normal: await pdf.embedFont(StandardFonts.TimesRoman),
    bold: await pdf.embedFont(StandardFonts.TimesRomanBold),
    italic: await pdf.embedFont(StandardFonts.TimesRomanItalic),
    boldItalic: await pdf.embedFont(StandardFonts.TimesRomanBoldItalic),
  };
  const labels = buildLabels(locale);

  const selected = String(document.view.selected_moment ?? "draft:0");
  const stateNumber = /^state:\d+$/.test(selected) ? Number(selected.slice(6)) : null;
  const snapshot = stateNumber !== null ? campaign.states.find((row) => row.number === stateNumber) : undefined;
  const frozen = snapshot !== undefined && (snapshot.roster?.length ?? 0) > 0 ? snapshot : undefined;
  const roster = frozen?.roster ?? campaign.warriors;
  const inventory = frozen?.inventory ?? campaign.inventory;

  const sheet = new Sheet(pdf, fonts);
  sheet.addPage();
  const ctx: RenderContext = { sheet, labels, locale, knowledge, bandId: campaign.identity.band_id };
  // Card pages hold cards only: the moment identification lives on the summary.
  const heroes = roster.filter((warrior) => warrior.kind === "hero" || warrior.kind === "hireling");
  const henchmen = roster.filter((warrior) => warrior.kind !== "hero" && warrior.kind !== "hireling");
  renderGroup(ctx, heroes, HERO_CARD_HEIGHT);
  renderGroup(ctx, henchmen, HENCHMAN_CARD_HEIGHT);
  renderSummaryPage(ctx, campaign, inventory, snapshot, momentLabel(campaign, stateNumber, labels));

  return pdf.save();
}
