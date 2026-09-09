"""Dice-driven dialogs for variable prices and variable hiring fees.

The KB declares variable amounts structurally (``optional_variable_cost`` on
Trading Post entries, ``"70+3D6"`` gold fees on Hired Swords, ``multiplier``
upgrade prices). The engine never rolls by itself; these dialogs collect the
player's roll (in-app or manual) and hand the resolved total back to the
write side.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from mordheim_campaign.ui.modality import make_modal

from mordheim_campaign.application.post_battle_catalogue import resolve_offer_price
from mordheim_campaign.ui.components import DiceResolutionCard
from mordheim_ui.i18n import tr, tr_message
from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application


class VariablePriceDialog(tk.Toplevel):
    """Resolve a variable-price offer: roll the cost dice, then buy.

    ``buy`` receives the resolved unit price in gc and returns the standard
    ``(ok, message)`` tuple of the write side.
    """

    def __init__(self, master: tk.Misc, *, offer, buy) -> None:
        super().__init__(master)
        self.title(tr('VARIABLE PRICE'))
        make_modal(self, master)
        count, sides = offer.price_dice or (1, 6)
        body = tk.Frame(self, bg=COLORS["panel"], padx=12, pady=10)
        body.pack(fill="both", expand=True)
        tk.Label(
            body, text=offer.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13),
        ).pack(anchor="w")
        tk.Label(
            body, text=offer.price_label, bg=COLORS["panel"], fg=COLORS["muted"],
            font=("Segoe UI", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(2, 8))
        self._status = tk.StringVar()
        resolved_price: dict[str, int] = {}
        tk.Label(
            body, textvariable=self._status, bg=COLORS["panel"], fg=COLORS["accent"],
            font=("Segoe UI Semibold", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(8, 0))

        def resolved(dice: list[int]) -> tuple[str, str, str]:
            price = resolve_offer_price(offer, sum(dice))
            if price is None:
                return tr('Cannot resolve'), tr('The offer price could not be computed.'), "warning"
            resolved_price["value"] = price
            return (
                tr('Price resolved'),
                tr('{} costs {} gc').format(offer.name, price),
                "success",
            )

        def purchase() -> None:
            if resolved_price.get("used") or "value" not in resolved_price:
                return
            ok, message = buy(resolved_price["value"])
            self._status.set(("✓ " if ok else "⚠ ") + tr_message(message))
            if ok:
                resolved_price["used"] = True
                self.after_idle(self.destroy)

        DiceResolutionCard(
            body, title=tr('COST ROLL'), subtitle=tr('Roll the declared cost dice; the total fixes the price.'),
            notation=f"{count}D{sides}", dice_count=count, dice_sides=sides, demo_dice=tuple(sides // 2 for _ in range(count)),
            combine="sum", outcome_title=tr('Price resolved'), outcome_detail=tr('The buy uses the rolled total.'),
            on_resolved=resolved,
            outcome_actions=((tr('BUY'), purchase, "Accent.TButton"),),
        ).pack(fill="x")
        ttk.Button(body, text=tr('CLOSE'), command=self.destroy).pack(anchor="e", pady=(8, 0))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(lambda: center_on_application(self))


class UpgradePriceDialog(tk.Toplevel):
    """Buy a multiplier-price upgrade over a base record the player picks.

    Multiplier-only offers (e.g. Gromril Weapon, 4× the base weapon price)
    apply to a weapon already owned; the player picks the record and the
    dialog buys the upgrade at ``multiplier × base price``.
    """

    def __init__(self, master: tk.Misc, *, offer, campaign, buy, weapon_hands) -> None:
        super().__init__(master)
        self.title(tr('UPGRADE PRICE'))
        make_modal(self, master)
        multiplier = offer.price_upgrade_multiplier or 1
        body = tk.Frame(self, bg=COLORS["panel"], padx=12, pady=10)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=offer.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(anchor="w")
        tk.Label(
            body, text=tr('{}× the price of the base record it upgrades. Pick the record:').format(multiplier),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(2, 8))
        rows = [
            row for row in campaign.inventory
            if row.value is not None and row.value > 0 and row.stash > 0
            and weapon_hands(row.base_item_id or row.id) is not None
        ]
        if not rows:
            tk.Label(
                body, text=tr('No owned records to upgrade. Buy the base item first.'),
                bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8), wraplength=430, justify="left",
            ).pack(anchor="w")
        for row in rows:
            line = tk.Frame(body, bg=COLORS["panel"])
            line.pack(fill="x", pady=1)
            tk.Label(
                line, text=f"{row.name}  ·  {row.value} gc", bg=COLORS["panel"], fg=COLORS["text"],
                font=("Segoe UI", 9), anchor="w",
            ).pack(side="left", fill="x", expand=True)
            ttk.Button(
                line, text=tr('UPGRADE ({} gc)').format(row.value * multiplier), style="Mini.TButton",
                command=lambda target=row: self._buy(target, multiplier, buy),
            ).pack(side="right")
        self._status = tk.StringVar()
        tk.Label(
            body, textvariable=self._status, bg=COLORS["panel"], fg=COLORS["accent"],
            font=("Segoe UI Semibold", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        ttk.Button(body, text=tr('CLOSE'), command=self.destroy).pack(anchor="e", pady=(8, 0))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(lambda: center_on_application(self))

    def _buy(self, row, multiplier: int, buy) -> None:
        ok, message = buy(row.value * multiplier, row)
        self._status.set(("✓ " if ok else "⚠ ") + tr_message(message))


class HirelingFeeDialog(tk.Toplevel):
    """Roll the variable hiring fee of a Hired Sword, then hire.

    ``hire`` receives the rolled fee total (dice only, before the flat base)
    and returns the standard ``(ok, message)`` tuple.
    """

    def __init__(self, master: tk.Misc, *, offer, hire) -> None:
        super().__init__(master)
        self.title(tr('HIRING FEE ROLL'))
        make_modal(self, master)
        count, sides = offer.fee_dice or (1, 6)
        body = tk.Frame(self, bg=COLORS["panel"], padx=12, pady=10)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=offer.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(anchor="w")
        tk.Label(
            body, text=tr('Hiring fee: {} + {}D{} gc').format(offer.fee_base_gc, count, sides),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(2, 8))
        self._status = tk.StringVar()
        resolved_fee: dict[str, int] = {}
        tk.Label(
            body, textvariable=self._status, bg=COLORS["panel"], fg=COLORS["accent"],
            font=("Segoe UI Semibold", 8), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(8, 0))

        def resolved(dice: list[int]) -> tuple[str, str, str]:
            resolved_fee["value"] = sum(dice)
            return (
                tr('Fee resolved'),
                tr('Total fee: {} gc').format((offer.fee_base_gc or 0) + sum(dice)),
                "success",
            )

        def confirm_hire() -> None:
            if resolved_fee.get("used") or "value" not in resolved_fee:
                return
            ok, message = hire(resolved_fee["value"])
            self._status.set(("✓ " if ok else "⚠ ") + tr_message(message))
            if ok:
                resolved_fee["used"] = True
                self.after_idle(self.destroy)

        DiceResolutionCard(
            body, title=tr('FEE ROLL'), subtitle=tr('Roll the fee dice; the engine adds the flat base.'),
            notation=f"{count}D{sides}", dice_count=count, demo_dice=tuple(sides // 2 for _ in range(count)),
            combine="sum", outcome_title=tr('Fee resolved'), outcome_detail=tr('The hire charges base + roll.'),
            on_resolved=resolved,
            outcome_actions=((tr('HIRE'), confirm_hire, "Accent.TButton"),),
        ).pack(fill="x")
        ttk.Button(body, text=tr('CLOSE'), command=self.destroy).pack(anchor="e", pady=(8, 0))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(lambda: center_on_application(self))
