"""persistence.warband_pdf: PDF export of the warband at one timeline moment.

Renders the warband of a single campaign moment — the initial draft or any
committed ``WarbandStateVM`` — as a printable roster in the style of the
printed Mordheim warband sheets: one rounded card per warrior (NAME/TYPE with
ruled label rows, the black stat table, an EQUIPO/HABILIDADES split region
and the XP tick-box band), heroes and henchmen groups separated, and a
closing warband-summary page (treasure, warband value, stored equipment,
notes).

The moment's roster and inventory come from the state's snapshot (deep-copied
at commit time), so a historical state exports exactly as it was; a draft
exports the live roster.

Layer rules honoured: no Tkinter, no YAML — this module renders the view
models it is given and never loads the KB. Display labels go through the
sanctioned shared reader ``mordheim_ui.i18n.tr`` (a pure data module), so the
PDF follows ``MORDHEIM_LOCALE`` like the rest of the interface.

The generator is ``fpdf2`` with the built-in Times core fonts (latin-1);
glyphs outside latin-1 are transliterated by :func:`_safe` so generation can
never crash on campaign data.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from mordheim_campaign.application.state import CampaignVM, WarriorVM
from mordheim_ui.i18n import current_locale, tr

#: Canonical storage order of the fighter characteristics and its per-locale
#: sheet abbreviations (es follows the printed Spanish sheets: HA/HP/F/R/H/L).
_STAT_KEYS = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")
_STAT_HEADERS = {
    "en": ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"),
    "es": ("M", "HA", "HP", "F", "R", "H", "I", "A", "L"),
}

#: Transliteration of common non-latin-1 glyphs before the latin-1 fallback.
_TRANSLITERATION = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2212": "-",  # minus sign
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2026": "...",  # ellipsis
    "\u26a0": "!",  # warning sign
    "\U0001f3b2": "[dice]",  # dice emoji
    "\u2192": "->",  # rightwards arrow
    "\u2039": "<",  # single left angle quote
    "\u203a": ">",  # single right angle quote
    "\u2022": "-",  # bullet
    "\u00a0": " ",  # no-break space
    "\u00d7": "x",  # multiplication sign is not in the Times core charset
}

HERO_CARD_HEIGHT = 39.0
HENCHMAN_CARD_HEIGHT = 30.0
CARD_GAP = 2.5
CARD_TOTAL_WIDTH = 190.0
LEFT_COL_W = 60.0
MID_COL_W = 60.0

#: XP tracks, one box per experience point: heroes and hired swords get
#: 90 boxes in two rows, henchman groups a single row of 14.
HERO_XP_ROWS, HERO_XP_PER_ROW = 2, 45
HENCHMAN_XP_PER_ROW = 14
#: Advance points of the printed band sheet — the boxes drawn with a thicker
#: border (heroes up to 90 XP, henchmen up to 14 XP).
HERO_ADVANCE_THRESHOLDS = (2, 4, 6, 8, 11, 14, 17, 20, 24, 28, 32, 36, 41, 46, 51, 57, 63, 69, 76, 83, 90)
HENCHMAN_ADVANCE_THRESHOLDS = (2, 5, 9, 14)


def _safe(text) -> str:
    """Makes arbitrary campaign text safe for the latin-1 core fonts."""
    text = str(text)
    for key, value in _TRANSLITERATION.items():
        text = text.replace(key, value)
    return text.encode("latin-1", "replace").decode("latin-1")


class _WarbandPDF(FPDF):
    """A4 document with a page-number footer."""

    def footer(self):
        self.set_y(-13)
        self.set_font("Times", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, text=_safe(str(self.page_no())), align="C")


def _resolve_data(campaign: CampaignVM, state_number: int | None):
    """Returns (roster, inventory, snapshot) for the requested moment.

    A committed state renders its own snapshot; snapshots predating the
    snapshot feature (empty roster) fall back to the live campaign, as does
    the draft.
    """
    snapshot = None
    if state_number is not None:
        snapshot = next((row for row in campaign.states if row.number == state_number), None)
    if snapshot is not None and snapshot.roster:
        return snapshot.roster, snapshot.inventory, snapshot
    return campaign.warriors, campaign.inventory, snapshot


def _moment_label(campaign: CampaignVM, state_number: int | None) -> str:
    if state_number is None:
        return tr('DRAFT')
    snapshot = next((row for row in campaign.states if row.number == state_number), None)
    label = tr('STATE #{}').format(state_number)
    if snapshot is None:
        return label
    if snapshot.date:
        label += f" - {snapshot.date}"
    if snapshot.label:
        label += f" - {snapshot.label}"
    return label


# ---------------------------------------------------------------------------
# Warrior card
# ---------------------------------------------------------------------------

def _stat_values(warrior: WarriorVM) -> list[str]:
    return [str(warrior.stats.get(key)) if warrior.stats.get(key) is not None else "" for key in _STAT_KEYS]


def _equipment_lines(warrior: WarriorVM) -> str:
    lines = []
    for item in warrior.equipment:
        # In a multi-minion group every listed quantity is the group size
        # (already shown on the TIPO line): the printed sheets list bare
        # item names, never "x N" per entry.
        if warrior.quantity > 1 or item.quantity <= 1:
            lines.append(item.name)
        else:
            lines.append(f"{item.name} x{item.quantity}")
    return "\n".join(lines)


def _skills_lines(warrior: WarriorVM) -> str:
    lines = list(warrior.skills)
    if warrior.condition:
        line = warrior.condition
        if warrior.condition_detail:
            line += f" ({warrior.condition_detail})"
        lines.append(line)
    if warrior.stat_advances:
        advances = ", ".join(f"{key} +{value}" for key, value in sorted(warrior.stat_advances.items()))
        lines.append(f"{tr('Advances')}: {advances}")
    return "\n".join(lines)


def _type_text(warrior: WarriorVM) -> str:
    text = warrior.profile_name or warrior.kind
    if warrior.quantity > 1:
        text += f" x{warrior.quantity}"
    return text


def _stat_block(pdf: _WarbandPDF, x: float, y: float, warrior: WarriorVM, header_h: float, value_h: float) -> None:
    headers = _STAT_HEADERS.get(current_locale(), _STAT_HEADERS["en"])
    cell_w = (LEFT_COL_W - 4.0) / len(_STAT_KEYS)
    pdf.set_font("Times", "B", 6.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(30, 30, 30)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.25)
    for index, header in enumerate(headers):
        pdf.set_xy(x + index * cell_w, y)
        pdf.cell(cell_w, header_h, text=_safe(header), border=1, align="C", fill=True)
    pdf.set_font("Times", "", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    for index, value in enumerate(_stat_values(warrior)):
        pdf.set_xy(x + index * cell_w, y + header_h)
        pdf.cell(cell_w, value_h, text=_safe(value), border=1, align="C", fill=True)


def _box_region(
    pdf: _WarbandPDF,
    x: float,
    y: float,
    width: float,
    bottom: float,
    label: str,
    content: str,
    rule_x1: float,
    rule_x2: float,
) -> None:
    """One EQUIPO/HABILIDADES cell: caps label, rule under it, content below."""
    pdf.set_xy(x, y)
    pdf.set_font("Times", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(width, 4.2, text=_safe(label))
    pdf.set_line_width(0.25)
    pdf.line(rule_x1, y + 4.6, rule_x2, y + 4.6)
    if content:
        pdf.set_xy(x, y + 5.2)
        pdf.set_font("Times", "", 7.5)
        pdf.multi_cell(width, 3.0, text=_safe(content), new_x="LMARGIN", new_y="NEXT")


def _xp_boxes(
    pdf: _WarbandPDF,
    x: float,
    y: float,
    warrior: WarriorVM,
    per_row: int,
    rows: int,
    box_w: float,
    box_h: float,
    stride: float,
    thresholds,
) -> None:
    """The experience track: one box per XP. Advance-point boxes carry a
    thicker border, as on the printed band sheet; boxes of experience already
    earned are filled grey."""
    capacity = per_row * rows
    reached = int(warrior.experience)
    threshold_set = set(thresholds)
    band_w = per_row * stride - (stride - box_w)
    start_x = x + (CARD_TOTAL_WIDTH - band_w) / 2.0
    for index in range(capacity):
        number = index + 1
        row, column = divmod(index, per_row)
        px = start_x + column * stride
        py = y + row * (box_h + 1.0)
        pdf.set_draw_color(0, 0, 0)
        if number in threshold_set:
            pdf.set_line_width(0.55)  # thicker border marks an advance point
        else:
            pdf.set_line_width(0.2)
        if number <= reached:
            pdf.set_fill_color(200, 200, 200)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.rect(px, py, box_w, box_h, style="DF")


def _warrior_card(pdf: _WarbandPDF, warrior: WarriorVM, y: float, height: float) -> None:
    x = pdf.l_margin
    hero = warrior.kind == "hero"
    # Hero cards fit six per page, henchman cards eight, as on the printed
    # sheets: compact ruled rows, stat table, XP band.
    if hero:
        name_y, name_rule = y + 1.2, y + 5.9
        type_y, type_rule = y + 6.2, y + 10.4
        stats_y = y + 11.4
        band_h = 12.0
    else:
        name_y, name_rule = y + 0.9, y + 5.2
        type_y, type_rule = y + 5.5, y + 9.5
        stats_y = y + 10.4
        band_h = 8.0
    top_h = height - band_h
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)
    pdf.set_line_width(0.9)
    pdf.rect(x, y, CARD_TOTAL_WIDTH, height, round_corners=True, corner_radius=3.0)

    # Left column: ruled NOMBRE / TIPO rows, then the stat table.
    lx = x + 2.5
    pdf.set_line_width(0.25)
    pdf.set_xy(lx, name_y)
    pdf.set_font("Times", "B", 9.5)
    pdf.cell(17, 4.3, text=_safe(tr('Name')))
    pdf.set_font("Times", "", 8)
    pdf.cell(LEFT_COL_W - 20, 4.3, text=_safe(warrior.name))
    pdf.line(lx, name_rule, x + LEFT_COL_W - 2.5, name_rule)
    pdf.set_xy(lx, type_y)
    pdf.set_font("Times", "B", 8.5)
    pdf.cell(13, 3.8, text=_safe(tr('Type')))
    pdf.set_font("Times", "", 7)
    pdf.cell(LEFT_COL_W - 16, 3.8, text=_safe(_type_text(warrior)))
    pdf.line(lx, type_rule, x + LEFT_COL_W - 2.5, type_rule)
    if hero:
        _stat_block(pdf, lx, stats_y, warrior, 4.2, 5.0)
    else:
        _stat_block(pdf, lx, stats_y, warrior, 4.0, 4.6)

    # EQUIPO / HABILIDADES: one region split by a vertical divider, labels
    # ruled underneath, as on the printed sheets.
    pdf.line(x + LEFT_COL_W, y + 1.0, x + LEFT_COL_W, y + top_h - 1.0)
    pdf.line(x + LEFT_COL_W + MID_COL_W, y + 1.0, x + LEFT_COL_W + MID_COL_W, y + top_h - 1.0)
    _box_region(
        pdf, x + LEFT_COL_W + 2.5, y + 1.4, MID_COL_W - 5.0, y + top_h,
        tr('Equipment'), _equipment_lines(warrior),
        x + LEFT_COL_W + 1.0, x + LEFT_COL_W + MID_COL_W - 1.0,
    )
    _box_region(
        pdf, x + LEFT_COL_W + MID_COL_W + 2.5, y + 1.4,
        CARD_TOTAL_WIDTH - LEFT_COL_W - MID_COL_W - 5.0, y + top_h,
        tr('Skills'), _skills_lines(warrior),
        x + LEFT_COL_W + MID_COL_W + 1.0, x + CARD_TOTAL_WIDTH - 1.0,
    )

    # XP band across the full card width.
    pdf.line(x + 1.0, y + top_h, x + CARD_TOTAL_WIDTH - 1.0, y + top_h)
    if hero:
        _xp_boxes(pdf, x, y + top_h + 2.0, warrior, HERO_XP_PER_ROW, HERO_XP_ROWS,
                  3.4, 3.0, 4.2, HERO_ADVANCE_THRESHOLDS)
    else:
        pdf.set_xy(x + 2.5, y + top_h + 1.6)
        pdf.set_font("Times", "B", 8.5)
        pdf.cell(24, 4.2, text=_safe(tr('Number')))
        pdf.set_font("Times", "", 7)
        pdf.cell(10, 4.2, text=_safe(f"{warrior.experience} XP"))
        _xp_boxes(pdf, x, y + top_h + 2.4, warrior, HENCHMAN_XP_PER_ROW, 1,
                  4.6, 3.2, 5.7, HENCHMAN_ADVANCE_THRESHOLDS)


# ---------------------------------------------------------------------------
# Summary page
# ---------------------------------------------------------------------------

def _page_title(pdf: _WarbandPDF, text: str) -> None:
    pdf.set_font("Times", "B", 15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 9, text=_safe(text), new_x="LMARGIN", new_y="NEXT")


def _summary_line(pdf: _WarbandPDF, label: str, value: str = "") -> None:
    pdf.set_font("Times", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, text=_safe(f"{label} {value}"), new_x="LMARGIN", new_y="NEXT")


def _summary_box(pdf: _WarbandPDF, x: float, y: float, w: float, h: float, title: str, lines: list[str]) -> None:
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.45)
    pdf.rect(x, y, w, h, round_corners=True, corner_radius=3.0)
    pdf.set_xy(x + 4.0, y + 3.0)
    pdf.set_font("Times", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w - 8.0, 6.0, text=_safe(title))
    pdf.set_xy(x + 4.0, y + 10.5)
    pdf.set_font("Times", "", 10.5)
    if lines:
        pdf.multi_cell(w - 8.0, 5.4, text=_safe("\n".join(lines)), new_x="LMARGIN", new_y="NEXT")


def _summary_data(campaign: CampaignVM, snapshot) -> dict:
    if snapshot is not None:
        return {
            "gold": snapshot.gold,
            "shards": snapshot.wyrdstone,
            "xp": snapshot.experience,
            "models": snapshot.models,
            "rating": snapshot.rating,
        }
    return {
        "gold": campaign.draft_treasury,
        "shards": 0,
        "xp": campaign.draft_experience,
        "models": campaign.draft_model_count,
        "rating": campaign.draft_rating,
    }


def _render_summary_page(pdf: _WarbandPDF, campaign: CampaignVM, inventory, snapshot, moment: str) -> None:
    pdf.add_page()
    pdf.set_font("Times", "I", 8.5)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 5.0, text=_safe(moment), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    data = _summary_data(campaign, snapshot)
    _page_title(pdf, campaign.warband_name)
    _summary_line(pdf, tr('Warband name:'), campaign.warband_name)
    _summary_line(pdf, tr('Warband type:'), campaign.warband_type)

    y = pdf.get_y() + 4.0
    box_w = (CARD_TOTAL_WIDTH - 8.0) / 2.0
    _summary_box(
        pdf, pdf.l_margin, y, box_w, 30.0, tr('Treasure'),
        [f"{tr('Gold Crowns:')} {data['gold']}", "", f"{tr('Wyrdstone:')} {data['shards']}"],
    )
    _summary_box(
        pdf, pdf.l_margin + box_w + 8.0, y, box_w, 30.0, tr('Warband value'),
        [
            f"{tr('Total experience:')} {data['xp']}",
            tr('Members ( {} ) x 5:').format(data['models']),
            f"{tr('Rating:')} {data['rating']}",
        ],
    )

    stash_lines = [
        f"{item.name} x{item.stash}" if item.stash > 1 else item.name
        for item in inventory if item.stash > 0
    ]
    battle_lines = [
        tr('Battle #{}').format(battle.number) + f" - {battle.scenario} vs. {battle.opponent} - {battle.result}"
        for battle in campaign.battles
        if snapshot is None or battle.number <= snapshot.number
    ]
    box_h = pdf.h - y - 30.0 - 20.0
    _summary_box(pdf, pdf.l_margin, y + 38.0, box_w, box_h, tr('Stored equipment'), stash_lines)
    _summary_box(pdf, pdf.l_margin + box_w + 8.0, y + 38.0, box_w, box_h, tr('Notes'), battle_lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def export_warband_pdf(path, campaign: CampaignVM, *, state_number: int | None = None) -> Path:
    """Writes the warband at one timeline moment as a PDF roster sheet.

    ``state_number=None`` renders the draft (live roster); a number renders
    the committed ``WarbandStateVM`` of that number from its snapshot. The
    destination directory is created if missing and the resolved path is
    returned.
    """
    roster, inventory, snapshot = _resolve_data(campaign, state_number)

    pdf = _WarbandPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    # Card pages hold cards only — no page title, no group headers — to use
    # the full sheet. The moment identification lives on the summary page.
    heroes = [warrior for warrior in roster if warrior.kind == "hero"]
    hirelings = [warrior for warrior in roster if warrior.kind == "hireling"]
    henchmen = [warrior for warrior in roster if warrior.kind not in {"hero", "hireling"}]
    card_area_bottom = pdf.h - 22.0

    def _render_group(warriors: list[WarriorVM], card_height: float) -> None:
        for warrior in warriors:
            if pdf.get_y() + card_height > card_area_bottom:
                pdf.add_page()
            _warrior_card(pdf, warrior, pdf.get_y(), card_height)
            pdf.set_y(pdf.get_y() + card_height + CARD_GAP)

    _render_group(heroes, HERO_CARD_HEIGHT)
    # Hired Swords earn experience like heroes: same card, own group.
    _render_group(hirelings, HERO_CARD_HEIGHT)
    _render_group(henchmen, HENCHMAN_CARD_HEIGHT)

    _render_summary_page(pdf, campaign, inventory, snapshot, _moment_label(campaign, state_number))

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destination))
    return destination
