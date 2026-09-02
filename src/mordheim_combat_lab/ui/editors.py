"""ui.editors: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.application.catalogue import ProfileChoice
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import FighterBuild
from mordheim_combat_lab.ui.widgets.skills import SkillChecklist
import re as re
import tkinter as tk
from tkinter import ttk


FREE_SELECTION = "Special · Free selection"


ENERGY_FOCUS_RULE_ID = "band--battle-monks-special-skills-energy-focus"


class FighterEditor(ttk.Frame):
    """Legacy workbook layout; produces current typed ``FighterBuild`` values."""
    def __init__(self, parent, title: str, catalogue: CombatCatalogue, on_change=None):
        super().__init__(parent)
        self.title, self.catalogue, self.on_change = title, catalogue, on_change
        self.name = tk.StringVar(value=title); self.band = tk.StringVar(); self.profile_name = tk.StringVar()
        self.weapon_name = tk.StringVar(value="Free hand"); self.off_hand_name = tk.StringVar(value="Free hand")
        self.armour_name = tk.StringVar(value="No armour"); self.main_material_name = tk.StringVar(value="Normal"); self.off_material_name = tk.StringVar(value="Normal")
        self.main_poison_name = tk.StringVar(value="No poison"); self.off_poison_name = tk.StringVar(value="No poison")
        self.energy_focus_attacks = tk.IntVar(value=0)
        self.equipment_summary = tk.StringVar(value="None")
        self.manual_characteristics = {key: tk.IntVar(value=value) for key, value in (("WS",3),("S",3),("T",3),("W",1),("I",3),("A",1))}
        self._stat_limits = {key: 20 for key in self.manual_characteristics}
        self.summary = tk.StringVar(value="Choose a warband or Special · Free selection.")
        self._categories = {"core", "1a", "1b", "1c", "trollheim"}; self._band_packages = {}; self._profiles = {}; self._weapons = {}; self._active_off_hands = {}; self._main_skill_categories = ()
        self._equipment_vars = {}; self._equipment_options = {}; self._other_rule_ids = set()
        self._updating = False
        self._build_gui(); self.set_categories(self._categories)

    def _build_gui(self):
        identity = ttk.LabelFrame(self, text="Identity and Source", padding=(10,8)); identity.pack(fill="x", pady=(0,10))
        for column in (1,3,5): identity.columnconfigure(column, weight=1)
        for column, label, variable in ((0,"Name:",self.name),(2,"Warband:",self.band),(4,"Warrior:",self.profile_name)):
            ttk.Label(identity,text=label).grid(row=0,column=column,sticky="w",padx=(0,6))
            widget = ttk.Entry(identity,textvariable=variable) if column == 0 else ttk.Combobox(identity,textvariable=variable,state="readonly")
            widget.grid(row=0,column=column+1,sticky="ew",padx=(0,12) if column < 4 else 0)
            if column == 2: self.band_combo=widget; widget.bind("<<ComboboxSelected>>",self._band_changed)
            if column == 4: self.profile_combo=widget; widget.bind("<<ComboboxSelected>>",self._profile_changed)
        ttk.Label(identity,textvariable=self.summary,style="Muted.TLabel").grid(row=1,column=0,columnspan=6,sticky="w",pady=(6,0))
        ttk.Label(self,text="BASIC ATTRIBUTES",style="Section.TLabel").pack(anchor="w",pady=(2,4)); self.stats_frame=ttk.Frame(self); self.stats_frame.pack(fill="x",pady=(0,12))
        ttk.Label(self,text="EQUIPMENT",style="Section.TLabel").pack(anchor="w",pady=(0,4))
        hands=ttk.Frame(self); hands.pack(fill="x"); hands.columnconfigure((0,1),weight=1,uniform="hands"); self._hand(hands,"Main Hand",0,True); self._hand(hands,"Off Hand",1,False)
        lower=ttk.Frame(self,padding=(0,7,0,0)); lower.pack(fill="x"); lower.columnconfigure(1,weight=1); lower.columnconfigure(3,weight=1)
        ttk.Label(lower,text="Armour").grid(row=0,column=0,sticky="w",padx=(0,7)); self.armour_combo=ttk.Combobox(lower,textvariable=self.armour_name,state="readonly"); self.armour_combo.grid(row=0,column=1,sticky="ew",padx=(0,18)); self.armour_combo.bind("<<ComboboxSelected>>",self._notify_change)
        ttk.Label(lower,text="Equipment").grid(row=0,column=2,sticky="w",padx=(0,7)); self.equipment_button=ttk.Menubutton(lower,textvariable=self.equipment_summary); self.equipment_button.grid(row=0,column=3,sticky="ew")
        ttk.Label(self,text="SKILLS",style="Section.TLabel").pack(anchor="w",pady=(14,4)); self.skill_checklist=SkillChecklist(self,self._skills_changed); self.skill_checklist.configure_inline_counter(ENERGY_FOCUS_RULE_ID, value=0, command=self._energy_focus_changed); self.skill_checklist.pack(fill="x")

    def _hand(self,parent,title,column,main):
        panel=ttk.LabelFrame(parent,text=title,padding=(9,7)); panel.grid(row=0,column=column,sticky="ew",padx=(0,5) if column==0 else (5,0)); panel.columnconfigure(1,weight=1); panel.columnconfigure(3,weight=1)
        ttk.Label(panel,text="Weapon").grid(row=0,column=0,sticky="w",padx=(0,6)); combo=ttk.Combobox(panel,textvariable=self.weapon_name if main else self.off_hand_name,state="readonly"); combo.grid(row=0,column=1,sticky="ew",padx=(0,12)); combo.bind("<<ComboboxSelected>>",self._main_weapon_changed if main else self._off_hand_changed)
        ttk.Label(panel,text="Material").grid(row=0,column=2,sticky="w",padx=(0,6)); material=ttk.Combobox(panel,textvariable=self.main_material_name if main else self.off_material_name,state="readonly",width=14); material.grid(row=0,column=3,sticky="ew"); material.bind("<<ComboboxSelected>>",self._notify_change)
        ttk.Label(panel,text="Poison").grid(row=1,column=2,sticky="w",padx=(0,6),pady=(4,0)); poison=ttk.Combobox(panel,textvariable=self.main_poison_name if main else self.off_poison_name,state="readonly",width=14); poison.grid(row=1,column=3,sticky="ew",pady=(4,0)); poison.bind("<<ComboboxSelected>>",self._notify_change)
        if main: self.weapon_combo,self.main_material_combo,self.main_poison_combo=combo,material,poison
        else: self.off_hand_combo,self.off_material_combo,self.off_poison_combo=combo,material,poison

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
        """Use the minimum roll for random KB profiles, as the compiler does."""
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
    def _configure_options(self,choice):
        self._weapons={"Free hand":None, **{name:item_id for item_id,name in self.catalogue.weapons(choice)}}; self.weapon_combo.configure(values=tuple(self._weapons)); self.weapon_name.set("Free hand"); self._armours={name:item_id for item_id,name in self.catalogue.armours(choice)}; self.armour_combo.configure(values=tuple(self._armours)); self.armour_name.set("No armour"); self._materials={name:item_id for item_id,name in self.catalogue.materials(choice)}; self.main_material_combo.configure(values=tuple(self._materials)); self.off_material_combo.configure(values=tuple(self._materials)); self.main_material_name.set("Normal"); self.off_material_name.set("Normal"); self._poisons={name:item_id for item_id,name in self.catalogue.poisons(choice)}; self.main_poison_combo.configure(values=tuple(self._poisons)); self.off_poison_combo.configure(values=tuple(self._poisons)); self.main_poison_name.set("No poison"); self.off_poison_name.set("No poison"); self._configure_equipment(choice); self._main_weapon_changed()
    def _configure_equipment(self,choice):
        self._equipment_options={f"{kind}:{item_id}":(item_id,name,kind) for kind,entries in (("helmet",self.catalogue.helmets(choice)),("preparation",self.catalogue.preparations(choice))) for item_id,name in entries if item_id}; menu=tk.Menu(self.equipment_button,tearoff=False); self._equipment_vars={}
        for option_id,(_item_id,name,kind) in self._equipment_options.items():
            variable=tk.BooleanVar(value=False); self._equipment_vars[option_id]=variable
            prefix={"helmet":"Helmet", "preparation":"Preparation"}[kind]
            menu.add_checkbutton(label=f"{prefix}: {name}",variable=variable,command=lambda selected=option_id:self._equipment_changed(selected))
        self.equipment_button.configure(menu=menu); self._equipment_changed()
    def _main_weapon_changed(self,_event=None):
        main=self._weapons.get(self.weapon_name.get()); options={name:item_id for item_id,name in self.catalogue.off_hand_options(self.choice)}
        selected_ids = self.skill_checklist.selected_ids()
        _ordinary_skills, selected_warband_skills = self.catalogue.skill_rule_ids(selected_ids)
        arms_master=bool({
            "band--pit-fighter-skill-arms-master",
            "band--ogres-special-skills-master-of-arms",
        } & (set(selected_warband_skills) | set(selected_ids).intersection(self._other_rule_ids)))
        if main and self.catalogue.mechanic(main).get("hands")==2 and not arms_master: options={"Free hand":None}
        self._active_off_hands=options; self.off_hand_combo.configure(values=tuple(options)); self.off_hand_name.set("Free hand" if "Free hand" in options else next(iter(options),"Free hand")); self._off_hand_changed()
    def _skills_changed(self):
        energy_focus = ENERGY_FOCUS_RULE_ID in self.catalogue.skill_rule_ids(self.skill_checklist.selected_ids())[1]
        if not energy_focus:
            self.energy_focus_attacks.set(0)
        self.skill_checklist.set_inline_counter_value(self.energy_focus_attacks.get())
        self._main_weapon_changed(); self._notify_change()
    def _energy_focus_changed(self, value: int):
        self.energy_focus_attacks.set(value)
        self._notify_change()
    def _off_hand_changed(self,_event=None):
        item=self._active_off_hands.get(self.off_hand_name.get()); is_weapon=bool(item and item.startswith("weapon.")); self.off_material_combo.configure(state="readonly" if is_weapon else "disabled"); self.off_poison_combo.configure(state="readonly" if is_weapon else "disabled"); self._notify_change()
    def _equipment_changed(self, selected=None):
        if selected and self._equipment_vars[selected].get():
            _item_id, _name, kind = self._equipment_options[selected]
            if kind == "helmet":
                for option_id, (_other_id, _other_name, other_kind) in self._equipment_options.items():
                    if option_id != selected and other_kind == kind:
                        self._equipment_vars[option_id].set(False)
        names=[name for option_id,(_item_id,name,_kind) in self._equipment_options.items() if self._equipment_vars[option_id].get()]; self.equipment_summary.set(", ".join(names) if names else "None"); self._notify_change()
    def _selected(self,kind): return tuple(item_id for option_id,(item_id,_name,item_kind) in self._equipment_options.items() if item_kind==kind and self._equipment_vars[option_id].get())
    def build(self):
        selected_ids = self.skill_checklist.selected_ids()
        skill_ids, warband_skill_ids = self.catalogue.skill_rule_ids(selected_ids)
        special_rule_ids = (*warband_skill_ids, *(rule_id for rule_id in selected_ids if rule_id in self._other_rule_ids))
        main_weapon_id = "weapon.fist" if self.weapon_name.get() == "Free hand" else self._weapons.get(self.weapon_name.get(), "weapon.dagger")
        values=dict(main_weapon_id=main_weapon_id,off_hand_id=self._active_off_hands.get(self.off_hand_name.get()),armour_id=self._armours.get(self.armour_name.get(),"armour.no-armour"),defence_ids=self._selected("helmet"),main_material_id=self._materials.get(self.main_material_name.get(),"material.normal"),off_material_id=self._materials.get(self.off_material_name.get(),"material.normal"),preparation_ids=self._selected("preparation"),main_poison_id=self._poisons.get(self.main_poison_name.get()),off_poison_id=self._poisons.get(self.off_poison_name.get()),skill_ids=skill_ids,special_rule_ids=special_rule_ids,energy_focus_attacks=self.energy_focus_attacks.get())
        for key in self.manual_characteristics:self._normalise_stat(key)
        characteristics=Characteristics(*(self.manual_characteristics[key].get() for key in ("WS","S","T","W","I","A")))
        if self.choice is None:return FighterBuild(self.catalogue.ruleset,characteristics,**values)
        choice=self.choice; return FighterBuild(self.catalogue.ruleset,characteristics,collection=choice.collection,band_id=choice.band_id,profile_id=choice.profile_id,**values)
    def main_weapon_options(self): return tuple((item_id,name) for name,item_id in self._weapons.items())
    def load_build(self,build):
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
            if build.main_weapon_id == "weapon.fist": self.weapon_name.set("Free hand")
            else: self._set(self._weapons,self.weapon_name,build.main_weapon_id)
            self._main_weapon_changed(); self._set(self._active_off_hands,self.off_hand_name,build.off_hand_id); self._off_hand_changed(); self._set(self._armours,self.armour_name,build.armour_id); self._set(self._materials,self.main_material_name,build.main_material_id); self._set(self._materials,self.off_material_name,build.off_material_id)
            self._set(self._poisons,self.main_poison_name,build.main_poison_id); self._set(self._poisons,self.off_poison_name,build.off_poison_id)
            selected=set(build.defence_ids)|set(build.preparation_ids)
            for option_id,var in self._equipment_vars.items():
                item_id,_name,kind=self._equipment_options[option_id]
                var.set(item_id in selected)
            self._equipment_changed()
            ui_skill_ids = self.catalogue.skill_ui_ids(self.choice, build.skill_ids, build.special_rule_ids)
            self.skill_checklist.set_selected_ids((*ui_skill_ids, *(rule_id for rule_id in build.special_rule_ids if rule_id in self._other_rule_ids)))
            self.energy_focus_attacks.set(build.energy_focus_attacks); self._skills_changed()
        finally:
            self._finish_update(was_updating)
    @staticmethod
    def _set(values,variable,target):
        for name,value in values.items():
            if value==target:variable.set(name);return

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
