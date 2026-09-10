import fontkit from "@pdf-lib/fontkit";
import { PDFDocument, rgb } from "pdf-lib";

import type { CampaignDocument } from "../campaign/types";

const A4: [number, number] = [595.28, 841.89];

export async function createWarbandPdf(document: CampaignDocument, locale: "es" | "en"): Promise<Uint8Array> {
  const pdf = await PDFDocument.create();
  pdf.registerFontkit(fontkit);
  const fontBytes = await fetch(`${import.meta.env.BASE_URL}fonts/NotoSans.ttf`).then((response) => {
    if (!response.ok) throw new Error(`Font request failed: HTTP ${response.status}`);
    return response.arrayBuffer();
  });
  const font = await pdf.embedFont(fontBytes);
  const { campaign } = document;
  const labels = locale === "es"
    ? { roster: "Banda", treasury: "Tesorería", rating: "Valoración", inventory: "Almacén", xp: "EXP", equipment: "Equipo", skills: "Habilidades / heridas", state: "Estado", draft: "Borrador", post: "Postbatalla" }
    : { roster: "Warband", treasury: "Treasury", rating: "Rating", inventory: "Stash", xp: "XP", equipment: "Equipment", skills: "Skills / injuries", state: "State", draft: "Draft", post: "Post-battle" };
  const selected = String(document.view.selected_moment ?? "draft:0");
  const stateNumber = /^state:\d+$/.test(selected) ? Number(selected.slice(6)) : null;
  const snapshot = stateNumber !== null && Number.isInteger(stateNumber) ? campaign.states.find((row) => row.number === stateNumber) : undefined;
  const postNumber = /^post:\d+$/.test(selected) ? Number(selected.slice(5)) : null;
  const warriors = snapshot?.roster ?? campaign.warriors;
  const inventory = snapshot?.inventory ?? campaign.inventory;
  const moment = snapshot ? `${labels.state} #${snapshot.number} · ${snapshot.date}` : postNumber === null ? labels.draft : `${labels.post} #${postNumber}`;
  let page = pdf.addPage(A4);
  let y = 790;
  const write = (text: string, size = 10, x = 42) => {
    const words = text.split(/\s+/); const lines: string[] = []; let line = "";
    for (const word of words) { const candidate = line ? `${line} ${word}` : word; if (line && font.widthOfTextAtSize(candidate, size) > A4[0] - x - 42) { lines.push(line); line = word; } else line = candidate; }
    if (line) lines.push(line);
    for (const row of lines) { if (y < 55) { page = pdf.addPage(A4); y = 790; } page.drawText(row, { x, y, size, font, color: rgb(.12, .12, .1) }); y -= size + 5; }
    y -= 2;
  };
  write(campaign.identity.warband_name, 24);
  write(`${campaign.identity.campaign_name} · ${campaign.identity.warband_type} · ${moment}`, 11);
  write(`${labels.treasury}: ${snapshot?.gold ?? campaign.configuration.starting_gold} gc   ${labels.rating}: ${snapshot?.rating ?? 0}`, 10);
  y -= 8;
  write(labels.roster.toUpperCase(), 13);
  for (const warrior of warriors) {
    write(`${warrior.name} · ${warrior.profile_name}${warrior.kind !== "hero" ? ` (${warrior.quantity ?? 1})` : ""} · ${labels.xp} ${warrior.experience}`, 11);
    const stats = Object.entries(warrior.stats).map(([key, value]) => `${key} ${value + (warrior.stat_modifiers?.[key] ?? 0)}`).join("   ");
    if (stats) write(stats, 8, 54);
    const equipment = warrior.equipment.map((entry) => `${entry.quantity}× ${entry.name}`).join(", ");
    if (equipment) write(`${labels.equipment}: ${equipment}`, 8, 54);
    if (warrior.skills.length) write(warrior.skills.join(", "), 8, 54);
    const conditions = [warrior.condition_detail ?? warrior.condition, ...(warrior.special_rules ?? [])].filter(Boolean).join(", ");
    if (conditions) write(`${labels.skills}: ${conditions}`, 8, 54);
    y -= 5;
  }
  if (inventory.length) {
    write(labels.inventory.toUpperCase(), 13);
    for (const item of inventory) write(`${item.name}: ${item.stash} / ${item.owned}`, 9, 54);
  }
  return pdf.save();
}
