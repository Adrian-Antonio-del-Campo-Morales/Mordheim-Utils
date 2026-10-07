"""ui: Fighter build editors."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.application.catalogue import ProfileChoice
from mordheim_combat_lab.ui.widgets.choice import ChoiceBox
from mordheim_combat_lab.ui.widgets.choice import ChoiceVar
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild
from mordheim_ui.i18n import tr
from mordheim_combat_lab.ui.widgets.skills import SkillChecklist
import re as re
import tkinter as tk
from tkinter import ttk


FREE_SELECTION = "Special · Free selection"


ENERGY_FOCUS_RULE_ID = "band--battle-monks-special-skills-energy-focus"



# Optional facts describe an already qualified individual, never a provider or cast.
_SUPPLIED_CHOICES = {
    "fauna_animal_kind": ("Animal qualification for Tranquil Fauna", {"ordinary": "Ordinary animal", "handled": "Animal Handler controlled", "large-predator": "Large predatory beast"}),
    "animal_handler_leadership": ("Qualified Animal Handler Leadership", {value: str(value) for value in range(11)}),
    "house_guard_house": ("House Guard house", {"fierezza": "Fierezza", "halcon": "Halcon", "baluardo": "Baluardo"}),
    "vampire_bloodline": ("Vampire bloodline", {"strigoi": "Strigoi", "blood-dragon": "Blood Dragon", "necrarch": "Necrarch", "lahmian": "Lahmian", "von-carstein": "Von Carstein"}),
    "fighter_kind": ("Fighter role", {"hero": "Hero", "henchman": "Henchman", "animal": "Animal", "summoned": "Summoned"}),
    "snorri_drunk_result": ("Snorri: pre-battle drinking result (2-6; 1 = absent)", {
        2: "2: WS and S -1", 3: "3: No effect", 4: "4: All combatants -1 to hit",
        5: "5: Strength +1", 6: "6: Frenzy"}),
    "mercenary_origin": ("Mercenary origin", {"reikland": "Reikland", "marienburg": "Marienburg", "middenheim": "Middenheim", "other": "Other mercenary origin"}),
    "creature_kind": ("Creature nature", {"living": "Living", "undead": "Undead", "daemon": "Daemon", "possessed": "Possessed"}),
    "species": ("Species", {value: value.title() for value in ("human", "dwarf", "skaven", "orc", "goblin", "halfling", "ogre", "beastman")}),
    "active_command": ("Active Command", {"follow-me-mine-pugnacious-ones": "Follow Me", "art-thou-ready-to-die-fighting": "Ready to Die"}),
    "wheelo_fitting": ("Legal Wheelo fitting", {"axe": "Axe", "club": "Club", "spear": "Spear", "morning-star": "Morning Star"}),
    # Cold-Blooded is printed differently for Lizardmen (Psychology) and Fimir
    # (Leadership); the caller declares which printed version the warrior has.
    "cold_blooded_origin": ("Cold-Blooded origin", {"lizardmen": "Lizardmen (Psychology)", "fimir": "Fimir (Leadership)"}),
}
_SUPPLIED_FLAGS = {
    "lit_item": "Carrying an open flame", "normal_animal": "Ordinary animal",
    "chaos_follower": "Follower of Chaos", "onogal_follower": "Follower of Onogal",
    "ulric_rival": "Named rival of Ulric (Witch Hunter or listed Sigmarite)",
    "aquatic": "Aquatic model", "flesh_peddler_mark": "Opponent is the nominated Flesh-Peddler mark",
    "guiding_dream_target": "Opponent is the nominated Guiding Dream Hero",
    "lizardman": "Lizardman", "vampire": "Vampire",
    "righteous_charge_active": "Righteous Charge already qualified",
}

class FighterEditor(ttk.Frame):
    """Legacy workbook layout; produces current typed ``FighterBuild`` values."""
    def __init__(self, parent, title: str, catalogue: CombatCatalogue, on_change=None):
        super().__init__(parent)
        self.title, self.catalogue, self.on_change = title, catalogue, on_change
        self.name = tk.StringVar(value=title); self.band = tk.StringVar(); self.profile_name = tk.StringVar()
        # Equipment choices keep the KB item id as the stored value; the
        # combobox renders the localized label for that id.
        self.weapon = ChoiceVar("weapon.fist", master=self)
        self.off_hand = ChoiceVar(None, master=self)
        self.armour = ChoiceVar("armour.no-armour", master=self)
        self.main_material = ChoiceVar("material.normal", master=self)
        self.off_material = ChoiceVar("material.normal", master=self)
        self.main_poison = ChoiceVar(None, master=self)
        self.off_poison = ChoiceVar(None, master=self)
        self.energy_focus_attacks = tk.IntVar(value=0)
        self.eagle_friends = tk.StringVar(value="")
        self.elf_kind = ChoiceVar(None, master=self)
        self.elf_kind.set_options({None: "Use profile identity", "high": "High Elf", "dark": "Dark Elf", "other": "Neither High nor Dark Elf"})
        self.sex = ChoiceVar(None, master=self)
        self.sex.set_options({None: "Use profile identity", "male": "Male", "female": "Female"})
        self.causes_fear = tk.BooleanVar(value=False)
        self.stupidity = tk.BooleanVar(value=False)
        self.stupidity_exempt = tk.BooleanVar(value=False)
        self.stupidity_initial_failed = tk.BooleanVar(value=False)
        self.stupidity_leadership = tk.StringVar(value="")
        self.stupidity_leadership_bonus = tk.StringVar(value="")
        self.leadership = tk.StringVar(value="")
        self.supplied_choices = {}
        for key, (_label, options) in _SUPPLIED_CHOICES.items():
            variable = ChoiceVar(None, master=self)
            variable.set_options({None: "Use profile identity", **options})
            self.supplied_choices[key] = variable
        self.supplied_flags = {key: tk.BooleanVar(value=False) for key in _SUPPLIED_FLAGS}
        self.condition_labels = {choice.id: choice.name for choice in catalogue.conditions()}
        self.condition_vars = {condition_id: tk.BooleanVar(value=False) for condition_id in self.condition_labels}
        self.mounted = tk.BooleanVar(value=False)
        self._supplied_traits = {}
        self._owned_item_ids = None
        self._owned_for_choice = None
        self.equipment_summary = tk.StringVar(value="None")
        self.manual_characteristics = {key: tk.IntVar(value=value) for key, value in (("WS",3),("S",3),("T",3),("W",1),("I",3),("A",1))}
        self._stat_limits = {key: 20 for key in self.manual_characteristics}
        self.summary = tk.StringVar(value="Choose a warband or Special · Free selection.")
        self._categories = {"core", "1a", "1b", "1c", "trollheim"}; self._band_packages = {}; self._profiles = {}; self._weapons = {}; self._active_off_hands = {}; self._main_skill_categories = ()
        self._equipment_vars = {}; self._equipment_options = {}; self._other_rule_ids = set()
        self._updating = False
        self._build_gui(); self.set_categories(self._categories)

    def _build_gui(self):
        identity = ttk.LabelFrame(self, text=tr("Identity and Source"), padding=(10,8)); identity.pack(fill="x", pady=(0,10))
        for column in (1,3,5): identity.columnconfigure(column, weight=1)
        for column, label, variable in ((0,"Name:",self.name),(2,"Warband:",self.band),(4,"Warrior:",self.profile_name)):
            ttk.Label(identity,text=label).grid(row=0,column=column,sticky="w",padx=(0,6))
            widget = ttk.Entry(identity,textvariable=variable) if column == 0 else ttk.Combobox(identity,textvariable=variable,state="readonly")
            widget.grid(row=0,column=column+1,sticky="ew",padx=(0,12) if column < 4 else 0)
            if column == 2: self.band_combo=widget; widget.bind("<<ComboboxSelected>>",self._band_changed)
            if column == 4: self.profile_combo=widget; widget.bind("<<ComboboxSelected>>",self._profile_changed)
        ttk.Label(identity,textvariable=self.summary,style="Muted.TLabel").grid(row=1,column=0,columnspan=6,sticky="w",pady=(6,0))
        ttk.Label(self,text=tr("BASIC ATTRIBUTES"),style="Section.TLabel").pack(anchor="w",pady=(2,4)); self.stats_frame=ttk.Frame(self); self.stats_frame.pack(fill="x",pady=(0,12))
        ttk.Label(self,text=tr("EQUIPMENT"),style="Section.TLabel").pack(anchor="w",pady=(0,4))
        hands=ttk.Frame(self); hands.pack(fill="x"); hands.columnconfigure((0,1),weight=1,uniform="hands"); self._hand(hands,tr("Main Hand"),0,True); self._hand(hands,tr("Off Hand"),1,False)
        lower=ttk.Frame(self,padding=(0,7,0,0)); lower.pack(fill="x"); lower.columnconfigure(1,weight=1); lower.columnconfigure(3,weight=1)
        ttk.Label(lower,text=tr("Armour")).grid(row=0,column=0,sticky="w",padx=(0,7)); self.armour_combo=ChoiceBox(lower,self.armour,self._notify_change); self.armour_combo.grid(row=0,column=1,sticky="ew",padx=(0,18))
        ttk.Label(lower,text=tr("Equipment")).grid(row=0,column=2,sticky="w",padx=(0,7)); self.equipment_button=ttk.Menubutton(lower,textvariable=self.equipment_summary); self.equipment_button.grid(row=0,column=3,sticky="ew")
        ttk.Label(self,text=tr("SKILLS"),style="Section.TLabel").pack(anchor="w",pady=(14,4)); self.skill_checklist=SkillChecklist(self,self._skills_changed); self.skill_checklist.configure_inline_counter(ENERGY_FOCUS_RULE_ID, value=0, command=self._energy_focus_changed); self.skill_checklist.pack(fill="x")
        facts = ttk.Frame(self, padding=(0, 8, 0, 0)); facts.pack(fill="x")
        ttk.Checkbutton(facts, text=tr("Causes Fear (already active)"), variable=self.causes_fear,
                        command=self._notify_change).pack(side="left")
        ttk.Label(facts, text=tr("Leadership (blank = unknown)")).pack(side="left", padx=(12, 4))
        ttk.Entry(facts, textvariable=self.leadership, width=4).pack(side="left")
        identity = ttk.Frame(self); identity.pack(fill="x", pady=(4, 0))
        ttk.Label(identity, text=tr("Elf identity")).pack(side="left", padx=(0, 4))
        ChoiceBox(identity, self.elf_kind, self._notify_change, width=28).pack(side="left")
        ttk.Label(identity, text=tr("Sex (for source conditions)")).pack(side="left", padx=(12, 4))
        ChoiceBox(identity, self.sex, self._notify_change, width=22).pack(side="left")
        supplied = ttk.LabelFrame(self, text=tr("Supplied individual facts"), padding=(8, 5))
        supplied.pack(fill="x", pady=(6, 0))
        for row, (key, (label, _options)) in enumerate(_SUPPLIED_CHOICES.items()):
            ttk.Label(supplied, text=tr(label)).grid(row=row, column=0, sticky="w", padx=(0, 8))
            ChoiceBox(supplied, self.supplied_choices[key], self._notify_change, width=24).grid(row=row, column=1, sticky="ew")
        for row, (key, label) in enumerate(_SUPPLIED_FLAGS.items()):
            ttk.Checkbutton(supplied, text=tr(label), variable=self.supplied_flags[key],
                            command=self._notify_change).grid(row=row, column=2, sticky="w", padx=(12, 0))
        ttk.Label(supplied, text=tr("Eagle companions (blank = one with Eagle Friend)")).grid(
            row=len(_SUPPLIED_CHOICES), column=0, sticky="w")
        ttk.Entry(supplied, textvariable=self.eagle_friends, width=6).grid(
            row=len(_SUPPLIED_CHOICES), column=1, sticky="w")
        self.eagle_friends.trace_add("write", lambda *_: self._notify_change())
        ttk.Checkbutton(supplied, text=tr("Mounted"), variable=self.mounted,
                        command=self._notify_change).grid(row=len(_SUPPLIED_CHOICES) + 1, column=0, columnspan=2, sticky="w")
        self.leadership.trace_add("write", lambda *_: self._notify_change())
        psychology = ttk.LabelFrame(self, text=tr("Stupidity — supplied individual conditions"), padding=(8, 5))
        psychology.pack(fill="x", pady=(6, 0))
        for row, (label, variable) in enumerate((
            ("Acquired Stupidity", self.stupidity),
            ("Stupidity exemption already active", self.stupidity_exempt),
            ("Previous Stupidity test failed", self.stupidity_initial_failed),
        )):
            ttk.Checkbutton(psychology, text=tr(label), variable=variable,
                            command=self._notify_change).grid(row=row, column=0, sticky="w")
        for row, (label, variable) in enumerate((
            ("Eligible handler's own Leadership within 6\"", self.stupidity_leadership),
            ("Brood Mentality bonus already active", self.stupidity_leadership_bonus),
        )):
            ttk.Label(psychology, text=tr(label)).grid(row=row, column=1, sticky="w", padx=(10, 4))
            ttk.Entry(psychology, textvariable=variable, width=4).grid(row=row, column=2)
            variable.trace_add("write", lambda *_: self._notify_change())
        conditions = ttk.LabelFrame(self, text=tr("Supplied conditions (already acquired)"), padding=(8, 5))
        conditions.pack(fill="x", pady=(6, 0))
        for row, (condition_id, variable) in enumerate(self.condition_vars.items()):
            ttk.Checkbutton(conditions, text=self.condition_labels[condition_id],
                            variable=variable, command=self._notify_change).grid(
                row=row // 2, column=row % 2, sticky="w", padx=(0, 12))

    def _hand(self,parent,title,column,main):
        panel=ttk.LabelFrame(parent,text=title,padding=(9,7)); panel.grid(row=0,column=column,sticky="ew",padx=(0,5) if column==0 else (5,0)); panel.columnconfigure(1,weight=1); panel.columnconfigure(3,weight=1)
        ttk.Label(panel,text=tr("Weapon")).grid(row=0,column=0,sticky="w",padx=(0,6))
        if main:
            combo=ChoiceBox(panel,self.weapon,self._main_weapon_changed)
            material=ChoiceBox(panel,self.main_material,self._notify_change,width=14)
            poison=ChoiceBox(panel,self.main_poison,self._notify_change,width=14)
            self.weapon_combo,self.main_material_combo,self.main_poison_combo=combo,material,poison
        else:
            combo=ChoiceBox(panel,self.off_hand,self._off_hand_changed)
            material=ChoiceBox(panel,self.off_material,self._notify_change,width=14)
            poison=ChoiceBox(panel,self.off_poison,self._notify_change,width=14)
            self.off_hand_combo,self.off_material_combo,self.off_poison_combo=combo,material,poison
        combo.grid(row=0,column=1,sticky="ew",padx=(0,12))
        ttk.Label(panel,text=tr("Material")).grid(row=0,column=2,sticky="w",padx=(0,6)); material.grid(row=0,column=3,sticky="ew")
        ttk.Label(panel,text=tr("Poison")).grid(row=1,column=2,sticky="w",padx=(0,6),pady=(4,0)); poison.grid(row=1,column=3,sticky="ew",pady=(4,0))

    def set_categories(self,categories:set[str]):
        self._categories=set(categories)
        packages=self.catalogue.bands_for_categories(self._categories)
        labels={str(p.band["name"]):0 for p in packages}
        for p in packages: labels[str(p.band["name"])] += 1
        self._band_packages={(str(p.band["name"]) if labels[str(p.band["name"])] == 1 else f"{p.band['name']} ({p.collection.title()})"):p for p in packages}
        names=(FREE_SELECTION,*sorted(self._band_packages)); current=self.band.get(); self.band_combo.configure(values=names)
        # The legacy workbook opens in Free Selection, where all six stat
        # cards are directly editable.  A KB profile remains available from
        # the same Warband selector when the user wants its fixed profile.
        all_skills = self.catalogue.skills(None)
        self._main_skill_categories = tuple(sorted({str(skill.category) for skill in all_skills}))
        self.skill_checklist.set_skills(all_skills, categories=self._main_skill_categories)
        self.band.set(current if current in names else FREE_SELECTION); self._band_changed()
    @property
    def is_free_selection(self): return self.band.get()==FREE_SELECTION
    @property
    def choice(self)->ProfileChoice|None: return None if self.is_free_selection else self._profiles[self.profile_name.get()]

    def _band_changed(self,_event=None):
        was_updating = self._begin_update()
        try:
            if self.is_free_selection:
                all_skills = self.catalogue.skills(None)
                self.profile_combo.configure(values=(),state="disabled"); self.profile_name.set(""); self._stat_limits = {key: 20 for key in self.manual_characteristics}; self._render_stats(); self._configure_options(None); self._set_rule_choices(all_skills, ()); self.summary.set("Free selection loaded · all implemented duel skills are available.")
            else:
                package=self._band_packages[self.band.get()]; self._profiles={c.name:c for c in self.catalogue.profiles(package.collection,str(package.band["id"]))}; self.profile_combo.configure(values=tuple(self._profiles),state="readonly"); self.profile_name.set(next(iter(self._profiles),"")); self._profile_changed()
        finally:
            self._finish_update(was_updating)

    def _profile_changed(self,_event=None):
        was_updating = self._begin_update()
        try:
            if self.is_free_selection:
                return
            profile=self.catalogue.profile(self.choice)
            self.leadership.set(str(profile["characteristics"].get("Ld"))
                                if isinstance(profile["characteristics"].get("Ld"), int) else "")
            for key in self.manual_characteristics:
                self.manual_characteristics[key].set(self._initial_stat(profile["characteristics"][key]))
            self._stat_limits = self._profile_stat_limits(profile)
            allowed_skills = self.catalogue.skills(self.choice)
            selectable_rules = self.catalogue.selectable_rules(self.choice)
            self._render_stats(); self._configure_options(self.choice); self._set_rule_choices(allowed_skills, selectable_rules); self.summary.set(str(profile.get("type", "fighter")).capitalize())
        finally:
            self._finish_update(was_updating)
    def _profile_stat_limits(self, profile):
        """Read optional racial maxima without inventing unavailable KB data."""
        declared = profile.get("characteristic_maxima") or profile.get("characteristics_maximum") or {}
        return {key: int(declared.get(key, 20)) for key in self.manual_characteristics}
    def _set_rule_choices(self, skills, other_rules):
        """Render Other Rules as a peer card in the shared skill selector."""
        other_rules = tuple(replace(rule, category="other rules") for rule in other_rules)
        self._other_rule_ids = {rule.id for rule in other_rules}
        choices = (*skills, *other_rules)
        self.skill_checklist.set_skills(choices, categories=(*self._main_skill_categories, "other rules"))
        self.skill_checklist.set_enabled_ids(self.catalogue.in_scope_skill_ids(choices))
        energy_focus_ui_id = next(
            (choice.id for choice in choices if choice.rule_id == ENERGY_FOCUS_RULE_ID),
            "",
        )
        self.skill_checklist.configure_inline_counter(
            energy_focus_ui_id,
            value=self.energy_focus_attacks.get(),
            command=self._energy_focus_changed,
        )
    @staticmethod
    def _initial_stat(value):
        """Use the minimum roll for random KB profiles, as the compiler does.

        Composite models (e.g. the Carnival of Chaos plague cart) declare
        ``null`` characteristics; the compiler resolves those profiles with
        default characteristics, so the editor assumes the same floor value.
        """
        if value is None:
            return 1
        if isinstance(value, int):
            return value
        match = re.fullmatch(r"(\d*)D(\d+)(?:\+(\d+))?", str(value), re.IGNORECASE)
        if not match:
            raise ValueError(f"Unsupported characteristic value: {value!r}")
        return int(match.group(1) or 1) + int(match.group(3) or 0)
    def _render_stats(self):
        for widget in self.stats_frame.winfo_children():widget.destroy()
        for index,key in enumerate(("WS","S","T","W","I","A")):
            # A compact group per statistic keeps both controls adjacent to
            # its value while allowing all six attributes to remain in one
            # row.  Grid placement directly on stats_frame would otherwise
            # distribute spare width between the buttons and the value box.
            self.stats_frame.columnconfigure(index, weight=1, uniform="stats")
            group = ttk.Frame(self.stats_frame)
            group.grid(row=0,column=index,sticky="n",padx=6)
            group.grid_anchor("center")
            ttk.Label(group,text=key,style="Muted.TLabel",font=("Segoe UI Semibold",12)).grid(row=0,column=0,columnspan=3,pady=(2,7))
            ttk.Button(group,text="−",style="Stat.TButton",command=lambda stat=key:self._change_stat(stat,-1)).grid(row=1,column=0,sticky="ns")
            entry=ttk.Entry(group,textvariable=self.manual_characteristics[key],style="StatValue.TEntry",width=3,justify="center",font=("Segoe UI Semibold",24)); entry.grid(row=1,column=1,padx=6); entry.bind("<FocusOut>",lambda _event, stat=key:self._normalise_stat(stat))
            ttk.Button(group,text="+",style="Stat.TButton",command=lambda stat=key:self._change_stat(stat,1)).grid(row=1,column=2,sticky="ns")
    def _change_stat(self, key, delta):
        minimum = 1 if key in {"W", "A"} else 0
        self.manual_characteristics[key].set(min(self._stat_limits[key], max(minimum, self.manual_characteristics[key].get() + delta)))
        self._notify_change()
    def _normalise_stat(self, key):
        minimum = 1 if key in {"W", "A"} else 0
        try: value = int(self.manual_characteristics[key].get())
        except (tk.TclError, ValueError): value = minimum
        self.manual_characteristics[key].set(min(self._stat_limits[key], max(minimum, value)))
        self._notify_change()
    def _labelled(self, pairs):
        """Map value → display label, resolving KB names for real ids."""
        return {item_id: self.catalogue.localized_name(item_id, name) if item_id else name for item_id, name in pairs}

    def _configure_options(self,choice):
        self._weapon_options={None:"Free hand", **dict(self.catalogue.weapons(choice))}; self.weapon.set_options(self._labelled(self._weapon_options.items())); self.weapon.set("weapon.fist" if "weapon.fist" in self._weapon_options else None)
        self._armour_options=dict(self.catalogue.armours(choice)); self.armour.set_options(self._labelled(self._armour_options.items())); self.armour.set("armour.no-armour")
        self._material_options=dict(self.catalogue.materials(choice)); self.main_material.set_options(self._labelled(self._material_options.items())); self.off_material.set_options(self._labelled(self._material_options.items())); self.main_material.set("material.normal"); self.off_material.set("material.normal")
        self._poison_options=dict(self.catalogue.poisons(choice)); self.main_poison.set_options(self._labelled(self._poison_options.items())); self.off_poison.set_options(self._labelled(self._poison_options.items())); self.main_poison.set(None); self.off_poison.set(None)
        self._configure_equipment(choice); self._main_weapon_changed()

    def _exception_rule_ids(self):
        """Canonical rules whose binding lifts the two-hand loadout limit.

        The exception is a selectable rule, so the fact depends on what the
        warrior currently has chosen — not on a local list of ids.
        """
        return self.catalogue.hand_exception_rule_ids(self.choice, self._selected_rule_ids())

    def _selected_rule_ids(self):
        ordinary, special = self.catalogue.skill_rule_ids(self.skill_checklist.selected_ids())
        return tuple((*special, *(rule_id for rule_id in self.skill_checklist.selected_ids()
                                  if rule_id in self._other_rule_ids)))
    
    def _is_free_selection(self):
        return self.choice is None

    def _equipment_reasons(self, choice, item_ids, *, slot: str, main_weapon_id=None, off_hand_id=None):
        """Refusal motive per candidate, decided once by the shared module.

        The editor never filters a candidate out and never decides locally:
        the shared batch returns the reason the option is incompatible in the
        current draft, and the widget renders it as a disabled entry.
        """
        if choice is None or not item_ids:
            return {}
        try:
            reasons = self.catalogue.equipment_decisions(
                choice, tuple(item_ids), slot=slot, main_weapon_id=main_weapon_id,
                off_hand_id=off_hand_id, skills=self._selected_skill_ids(),
                exception_rule_ids=self._exception_rule_ids(),
            )
        except (KeyError, TypeError, ValueError):
            # A transport or projection failure is an explicit operation error:
            # it never falls back to permissive local rules.
            return {}
        return {item_id: reason for item_id, reason in reasons.items() if reason}

    def _selected_skill_ids(self):
        ordinary, special = self.catalogue.skill_rule_ids(self.skill_checklist.selected_ids())
        return (*ordinary, *special)

    def _recalculate_availability(self):
        """Recompute option states after the relevant selections changed."""
        was_updating = self._begin_update()
        try:
            self._main_weapon_changed()
            self._off_hand_changed()
            self._armour_changed()
        finally:
            self._finish_update(was_updating)
    def _configure_equipment(self,choice):
        self._equipment_options={f"{kind}:{item_id}":(item_id,name,kind) for kind,entries in (("helmet",self.catalogue.helmets(choice)),("preparation",self.catalogue.preparations(choice))) for item_id,name in entries if item_id}; menu=tk.Menu(self.equipment_button,tearoff=False); self._equipment_vars={}
        for option_id,(_item_id,name,kind) in self._equipment_options.items():
            variable=tk.BooleanVar(value=False); self._equipment_vars[option_id]=variable
            prefix={"helmet":"Helmet", "preparation":"Preparation"}[kind]
            menu.add_checkbutton(label=f"{tr(prefix)}: {self.catalogue.localized_name(_item_id, name)}",variable=variable,command=lambda selected=option_id:self._equipment_changed(selected))
        self.equipment_button.configure(menu=menu); self._equipment_changed()
    def _main_weapon_changed(self,_event=None):
        """Offer every off-hand option; the shared decision marks the refused ones.

        A two-hand main weapon does not delete the off-hand list: the affected
        entries stay visible and disabled with their motive, and a previously
        chosen off hand is retained until the user removes it.
        """
        main=self.weapon.get(); options={None:"Free hand", **dict(self.catalogue.off_hand_options(self.choice)[1:])}
        reasons = self._equipment_reasons(
            self.choice, [item_id for item_id in options if item_id], slot="off",
            main_weapon_id=main, off_hand_id=self.off_hand.get(),
        )
        self._active_off_hands=options; self.off_hand.set_options(self._labelled(options.items()), reasons)
        if not self.off_hand._has(self.off_hand.get()):
            self.off_hand.set(None)
        self._off_hand_changed()
    def _armour_changed(self,_event=None):
        """Refusal motives of the armour, material and poison slots."""
        if self.choice is None:
            return
        armour_reasons = self._equipment_reasons(
            self.choice, [item_id for item_id in self._armour_options if item_id], slot="main",
            main_weapon_id=self.weapon.get(), off_hand_id=self.off_hand.get(),
        )
        self.armour.set_options(self._labelled(self._armour_options.items()), armour_reasons)
        material_reasons = self._equipment_reasons(
            self.choice, [item_id for item_id in self._material_options if item_id], slot="main",
            main_weapon_id=self.weapon.get(), off_hand_id=self.off_hand.get(),
        )
        self.main_material.set_options(self._labelled(self._material_options.items()), material_reasons)
        self.off_material.set_options(self._labelled(self._material_options.items()), material_reasons)
        poison_reasons = self._equipment_reasons(
            self.choice, [item_id for item_id in self._poison_options if item_id], slot="main",
            main_weapon_id=self.weapon.get(), off_hand_id=self.off_hand.get(),
        )
        self.main_poison.set_options(self._labelled(self._poison_options.items()), poison_reasons)
        self.off_poison.set_options(self._labelled(self._poison_options.items()), poison_reasons)
    def _skills_changed(self):
        energy_focus = ENERGY_FOCUS_RULE_ID in self.catalogue.skill_rule_ids(self.skill_checklist.selected_ids())[1]
        if not energy_focus:
            self.energy_focus_attacks.set(0)
        self.skill_checklist.set_inline_counter_value(self.energy_focus_attacks.get())
        # Skills change the applicable rules, so every dependent option state
        # is recalculated from the shared decision rather than from a local table.
        self._recalculate_availability(); self._notify_change()
    def _energy_focus_changed(self, value: int):
        self.energy_focus_attacks.set(value)
        self._notify_change()
    def _off_hand_changed(self,_event=None):
        item=self.off_hand.get(); is_weapon=bool(item and item.startswith("weapon.")); self.off_material_combo.configure(state="readonly" if is_weapon else "disabled"); self.off_poison_combo.configure(state="readonly" if is_weapon else "disabled"); self._armour_changed(); self._notify_change()
    def _equipment_changed(self, selected=None):
        if selected and self._equipment_vars[selected].get():
            _item_id, _name, kind = self._equipment_options[selected]
            if kind == "helmet":
                for option_id, (_other_id, _other_name, other_kind) in self._equipment_options.items():
                    if option_id != selected and other_kind == kind:
                        self._equipment_vars[option_id].set(False)
        names=[self.catalogue.localized_name(item_id, name) for option_id,(item_id,name,_kind) in self._equipment_options.items() if self._equipment_vars[option_id].get()]; self.equipment_summary.set(", ".join(names) if names else tr("None")); self._notify_change()
    def _selected(self,kind): return tuple(item_id for option_id,(item_id,_name,item_kind) in self._equipment_options.items() if item_kind==kind and self._equipment_vars[option_id].get())
    def build(self):
        selected_ids = self.skill_checklist.selected_ids()
        skill_ids, warband_skill_ids = self.catalogue.skill_rule_ids(selected_ids)
        special_rule_ids = (*warband_skill_ids, *(rule_id for rule_id in selected_ids if rule_id in self._other_rule_ids))
        main_weapon_id = "weapon.fist" if self.weapon.get() in (None, "weapon.fist") else self.weapon.get()
        values=dict(main_weapon_id=main_weapon_id,off_hand_id=self.off_hand.get(),armour_id=self.armour.get() or "armour.no-armour",defence_ids=self._selected("helmet"),main_material_id=self.main_material.get() or "material.normal",off_material_id=self.off_material.get() or "material.normal",preparation_ids=self._selected("preparation"),main_poison_id=self.main_poison.get(),off_poison_id=self.off_poison.get(),skill_ids=skill_ids,special_rule_ids=special_rule_ids,energy_focus_attacks=self.energy_focus_attacks.get())
        for key in self.manual_characteristics:self._normalise_stat(key)
        traits = dict(self._supplied_traits)
        if self.elf_kind.get() is not None: traits["elf_kind"] = self.elf_kind.get()
        else: traits.pop("elf_kind", None)
        if self.sex.get() is not None: traits["sex"] = self.sex.get()
        else: traits.pop("sex", None)
        if self.causes_fear.get(): traits["causes_fear"] = True
        else: traits.pop("causes_fear", None)
        for key in ("stupidity", "stupidity_exempt", "stupidity_initial_failed"):
            if getattr(self, key).get(): traits[key] = True
            else: traits.pop(key, None)
        for key in ("stupidity_leadership", "stupidity_leadership_bonus"):
            value = getattr(self, key).get().strip()
            if value: traits[key] = int(value)
            else: traits.pop(key, None)
        count = self.eagle_friends.get().strip()
        if count: traits['eagle_friends'] = int(count)
        else: traits.pop('eagle_friends', None)
        for key, variable in self.supplied_choices.items():
            if variable.get() is None: traits.pop(key, None)
            else: traits[key] = variable.get()
        for key, variable in self.supplied_flags.items():
            if variable.get(): traits[key] = True
            else: traits.pop(key, None)
        values["condition_ids"] = tuple(
            condition_id for condition_id, variable in self.condition_vars.items() if variable.get())
        values["mounted"] = self.mounted.get()
        values["owned_item_ids"] = self._owned_item_ids if self.choice == self._owned_for_choice else None
        values["trait_overrides"] = traits
        leadership = self.leadership.get().strip()
        characteristics=Characteristics(*(self.manual_characteristics[key].get() for key in ("WS","S","T","W","I","A")),
                                        leadership=int(leadership) if leadership else None)
        if self.choice is None:return FighterBuild(self.catalogue.ruleset,characteristics,**values)
        choice=self.choice; return FighterBuild(self.catalogue.ruleset,characteristics,collection=choice.collection,band_id=choice.band_id,profile_id=choice.profile_id,**values)
    def main_weapon_options(self): return tuple((item_id,name) for item_id,name in self._weapon_options.items())
    def load_build(self,build):
        if "sex" in build.trait_overrides and build.trait_overrides["sex"] not in ("male", "female"):
            raise ValueError("sex must be male or female")
        if "elf_kind" in build.trait_overrides and build.trait_overrides["elf_kind"] not in ("high", "dark", "other"):
            raise ValueError("elf_kind must be high, dark or other")
        for key, (_label, options) in _SUPPLIED_CHOICES.items():
            if key in build.trait_overrides and build.trait_overrides[key] not in options:
                raise ValueError(f"invalid supplied {key}")
        for key in _SUPPLIED_FLAGS:
            if not isinstance(build.trait_overrides.get(key, False), bool):
                raise ValueError(f"{key} must be a boolean")
        count = build.trait_overrides.get("eagle_friends")
        if count is not None and (type(count) is not int or count < 1):
            raise ValueError("eagle_friends must be a positive integer")
        fear = build.trait_overrides.get("causes_fear", False)
        if not isinstance(fear, bool):
            raise ValueError("causes_fear must be a boolean")
        for key in ("stupidity", "stupidity_exempt", "stupidity_initial_failed"):
            if not isinstance(build.trait_overrides.get(key, False), bool):
                raise ValueError(f"{key} must be a boolean")
        for key in ("stupidity_leadership", "stupidity_leadership_bonus"):
            value = build.trait_overrides.get(key)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{key} must be a non-negative integer")
        was_updating = self._begin_update()
        try:
            if build.characteristics and not build.band_id:
                self.band.set(FREE_SELECTION); self._band_changed(); values=(build.characteristics.weapon_skill,build.characteristics.strength,build.characteristics.toughness,build.characteristics.wounds,build.characteristics.initiative,build.characteristics.attacks)
                for key,value in zip(("WS","S","T","W","I","A"),values):self.manual_characteristics[key].set(value)
            else:
                package=next(p for p in self.catalogue.bands_for_categories(set()) if p.collection==build.collection and p.band["id"]==build.band_id)
                if package not in self._band_packages.values():self.set_categories(set(package.band.get("categories") or ()))
                self.band.set(next(name for name,value in self._band_packages.items() if value == package)); self._band_changed(); self.profile_name.set(next(name for name,choice in self._profiles.items() if choice.profile_id==build.profile_id)); self._profile_changed()
                if build.characteristics:
                    for key,value in zip(("WS","S","T","W","I","A"),(build.characteristics.weapon_skill,build.characteristics.strength,build.characteristics.toughness,build.characteristics.wounds,build.characteristics.initiative,build.characteristics.attacks)):self.manual_characteristics[key].set(value)
            self.weapon.set(("weapon.fist" if "weapon.fist" in self._weapon_options else None) if build.main_weapon_id == "weapon.fist" else build.main_weapon_id)
            self._main_weapon_changed(); self.off_hand.set_by_value(build.off_hand_id, default=None); self._off_hand_changed(); self.armour.set_by_value(build.armour_id, default="armour.no-armour"); self.main_material.set_by_value(build.main_material_id, default="material.normal"); self.off_material.set_by_value(build.off_material_id, default="material.normal")
            self.main_poison.set_by_value(build.main_poison_id); self.off_poison.set_by_value(build.off_poison_id)
            selected=set(build.defence_ids)|set(build.preparation_ids)
            for option_id,var in self._equipment_vars.items():
                item_id,_name,kind=self._equipment_options[option_id]
                var.set(item_id in selected)
            self._equipment_changed()
            ui_skill_ids = self.catalogue.skill_ui_ids(self.choice, build.skill_ids, build.special_rule_ids)
            self._supplied_traits = dict(build.trait_overrides)
            self._owned_item_ids = build.owned_item_ids
            self._owned_for_choice = self.choice
            self.eagle_friends.set(str(build.trait_overrides.get("eagle_friends", "")))
            self.elf_kind.set(build.trait_overrides.get("elf_kind"))
            self.sex.set(build.trait_overrides.get("sex"))
            for key, variable in self.supplied_choices.items():
                variable.set(build.trait_overrides.get(key))
            for key, variable in self.supplied_flags.items():
                variable.set(build.trait_overrides.get(key, False))
            for condition_id, variable in self.condition_vars.items():
                variable.set(condition_id in build.condition_ids)
            self.mounted.set(build.mounted)
            self.causes_fear.set(fear)
            for key in ("stupidity", "stupidity_exempt", "stupidity_initial_failed"):
                getattr(self, key).set(build.trait_overrides.get(key, False))
            for key in ("stupidity_leadership", "stupidity_leadership_bonus"):
                value = build.trait_overrides.get(key)
                getattr(self, key).set("" if value is None else str(value))
            if build.characteristics is not None:
                self.leadership.set(str(build.characteristics.leadership)
                                    if build.characteristics.leadership is not None else "")
            self.skill_checklist.set_selected_ids((*ui_skill_ids, *(rule_id for rule_id in build.special_rule_ids if rule_id in self._other_rule_ids)))
            self.energy_focus_attacks.set(build.energy_focus_attacks); self._skills_changed()
        finally:
            self._finish_update(was_updating)

    def refresh_labels(self):
        """Re-render every equipment label after a locale change.

        Option values and their refusal motives are preserved; only the display
        text is refreshed.
        """
        for combo in (self.weapon_combo, self.off_hand_combo, self.armour_combo, self.main_material_combo, self.off_material_combo, self.main_poison_combo, self.off_poison_combo):
            combo.refresh_labels()
        self._recalculate_availability()

    def _begin_update(self):
        was_updating = self._updating
        self._updating = True
        return was_updating

    def _finish_update(self, was_updating):
        self._updating = was_updating
        if not was_updating:
            self._notify_change()

    def _notify_change(self,_event=None):
        if not self._updating and self.on_change:self.on_change()


__all__=["FighterEditor","FREE_SELECTION"]
