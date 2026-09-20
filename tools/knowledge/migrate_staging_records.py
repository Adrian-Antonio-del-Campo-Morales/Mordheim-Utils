# -*- coding: utf-8 -*-
"""Bring a staging tree's band records to the canonical KB shape.

Ported from the active KB (``sources/knowledge``) and from
``docs/reference/knowledge-base.md``:

* ``profiles.yaml``: ``fixed_equipment`` / ``equipment_restrictions`` are lists
  of item ids and prose strings -- never mappings. There is no ``references``
  field: a profile either carries its own data or the source note moves into
  ``equipment_restrictions``.
* ``equipment-access.yaml``: only ``item_id`` / ``cost`` / ``notes``
  (``price_override`` is KB-canonical too) per item, and equipment lists carry
  no ``notes`` -- availability and price notes belong to the item.
* ``band.yaml``: the roster holds ``minimum_models``, ``maximum_models``,
  ``starting_gold`` and ``members`` (``profile_id`` / ``minimum`` /
  ``maximum`` / ``group_size``) only.

Usage::

    python tools/knowledge/migrate_2b_records.py --tree 2B           # dry run
    python tools/knowledge/migrate_2b_records.py --tree 2B --write
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import yaml

ITEM_KEYS = {'item_id', 'cost', 'notes', 'price_override'}
MEMBER_KEYS = {'profile_id', 'minimum', 'maximum', 'group_size'}
ROSTER_KEYS = {'minimum_models', 'maximum_models', 'starting_gold', 'members'}

# Equipment-list notes that belong to the items they qualify. Each action is
# ('item', <match kind>, <needle>, <note>) or ('restrict', None, None, <prose>)
# where <prose> lands on the equipment_restrictions of the profiles using the list.
LIST_NOTE_ACTIONS: dict[tuple[str, str], list[tuple]] = {
    ('blood-dragons-mou', 'blood-dragon-equipment-list'): [
        ('item', 'exact', 'warhorse', 'Vampire only.'),
        ('item', 'exact', 'barding', 'Vampire only.'),
        ('restrict', None, None, 'May not use missile weapons.'),
    ],
    ('bretonnian-brigands-mou', 'brigand-equipment-list'): [
        ('item', 'exact', 'crossbow', 'Heroes only.'),
        ('item', 'exact', 'horse', 'Heroes only; starting price only.'),
        ('item', 'exact', 'warhorse', 'Heroes only; starting price only.'),
        ('item', 'exact', 'heavy_armour', 'Heroes only.'),
        ('item', 'exact', 'barding', 'Heroes only.'),
    ],
    ('bretonnian-brigands-mou', 'poacher-equipment-list'): [
        ('item', 'exact', 'hunting_arrows', 'Starting price only.'),
    ],
    # Rapier / Heavy Armour are absent from this list, which already expresses
    # "not available to this warband".
    ('bretonnian-buccaneers-sar', 'pirate-equipment-list'): [
        ('omit', None, None, 'rapier and heavy armour absent from the list'),
    ],
    ('disciples-of-maldred-mou', 'disciples-equipment-list'): [
        ('restrict', None, None, 'May not use missile weapons.'),
    ],
    ('disciples-of-maldred-mou', 'men-at-arms-equipment-list'): [
        ('restrict', None, None, 'May not use missile weapons.'),
    ],
    ('estalian-corsairs-sar', 'pirate-equipment-list'): [
        ('item', 'exact', 'rapier', 'Estalians only.'),
        ('item', 'exact', 'heavy_armour', 'Estalians only.'),
        ('omit', None, None, 'crossbows absent from the list'),
    ],
    ('ghutani-rel', 'townsmen-equipment-list'): [
        ('restrict', None, None, 'Restricted to Townsmen.'),
    ],
    ('muzil-rel', 'townsmen-equipment-list'): [
        ('restrict', None, None, 'Restricted to Townsmen.'),
    ],
    ('turjuk-rel', 'townsmen-equipment-list'): [
        ('restrict', None, None, 'Restricted to Townsmen.'),
    ],
    ('khorne-raiders-sar', 'madbrain-equipment-list'): [
        ('restrict', None, None, 'The Armour section is available to Quartermasters and Flayerkin only.'),
    ],
    ('lost-the-mou', 'greycoats-equipment-list'): [
        ('restrict', None, None, 'May not wear armour.'),
    ],
    ('lothern-sea-patrol-sar', 'warrior-equipment-list'): [
        ('item', 'prefix', 'ithilmar',
         'Warband creation price: Ithilmar Weapon costs double, Ithilmar Armour costs 60 gc.'),
    ],
    ('necrarchs-mou', 'defiled-equipment-list'): [
        ('item', 'contains', 'bow', 'Defiled only.'),
    ],
    ('pirates-of-the-cathayan-sea-sar', 'monk-equipment-list'): [
        ('restrict', None, None, 'May not wear armour.'),
    ],
    # The robes are not a purchasable item, so their protection is stated on the
    # profiles that wear them.
    ('skaven-of-clan-pestilens-mou', 'clan-pestilence-equipment-list'): [
        ('restrict', None, None,
         'The robes offer protection equal to soft leather and count as light armour when combined '
         'with the scattered pieces of chain mail or plate some plague monks wear underneath.'),
    ],
    ('skaven-of-clan-pestilens-mou', 'clanrat-equipment-list'): [
        ('item', 'exact', 'flail', 'Plague Monks and Initiates only.'),
    ],
    ('slayer-pirates-sar', 'pirate-equipment-list'): [
        ('restrict', None, None, 'May not wear armour.'),
    ],
    ('slayer-pirates-sar', 'gunner-equipment-list'): [
        ('restrict', None, None, 'May not wear armour.'),
    ],
    ('wasteland-privateers-sar', 'pirate-equipment-list'): [
        ('item', 'exact', 'handgun', 'Wastelanders only.'),
    ],
    ('wood-elves-of-arden-mou', 'wood-elf-equipment-list'): [
        ('item', 'prefix', 'ithilmar',
         'Warband creation price: Ithilmar Weapon costs double, Ithilmar Armour costs 60 gc. '
         'Ithilmar gear and the asterisked prices follow the Mousillon supplement notes.'),
    ],
    ('wood-elves-of-arden-mou', 'scout-equipment-list'): [
        ('item', 'prefix', 'ithilmar',
         'Warband creation price: Ithilmar Weapon costs double, Ithilmar Armour costs 60 gc.'),
    ],
}

# Roster-member notes that cannot live on the roster: they become profile
# equipment restrictions (the KB's own home for warband-composition prose).
MEMBER_NOTES_AS_RESTRICTION = {'Replaces', 'Replace', 'Never more', 'No more', 'May not have more',
                               '0-4 per', 'Does not count towards'}
# Member notes resolving to data already copied into the profile.
MEMBER_NOTES_DROPPED = {'Same as Da Mob'}
# Roster notes already stripped from ``band.yaml`` by an earlier pass, carried
# here so the source facts survive as profile restrictions.
RELOCATED_MEMBER_NOTES: dict[tuple[str, str], list[str]] = {
    ('blood-dragons-mou', 'grave-guards'): ['Never more Grave Guards than Skeletons'],
    ('dark-elf-corsairs-mou', 'specialist'): ['Does not count towards the maximum warband size'],
    ('disciples-of-maldred-mou', 'squires'): ['Never more Squires than Knights'],
    ('disciples-of-maldred-mou', 'men-at-arms'): ['0-4 per Questing Knight'],
    ('orc-pirates-sar', 'goblin-enjuneer'): ['Replaces Orc Shaman'],
    ('orc-pirates-sar', 'goblin-swabbies'): ['Replaces Goblin Warriors in the henchmen list'],
    ('pirates-of-the-cathayan-sea-sar', 'dragon-monk'): ["Replaces one Shanghai'er"],
    ('pirates-of-the-cathayan-sea-sar', 'floordogs'): ['Never more Floordogs than Deck Hands'],
    ('slayer-pirates-sar', 'thaggi'): ['May not have more Thaggi than other Henchmen'],
}
# Notes already stated by the package's own profile rule, so relocating them
# would duplicate content.
DUPLICATED_BY_PROFILE_RULE: dict[tuple[str, str], list[str]] = {
    # `hunting-hound--dog-handler` states the ratio verbatim.
    ('woodsmen-de-artois-mou', 'hunting-hound'): ['No more Hunting Hounds than Trappers'],
}

# Da Mob values (KB orc-mob) for the Orc Pirates profiles the source defines as
# "same as Da Mob".
DA_MOB = {
    'boss': {
        'cost': 80, 'experience': 20,
        'characteristics': {'M': 4, 'WS': 4, 'BS': 4, 'S': 4, 'T': 4, 'W': 1, 'I': 3, 'A': 1, 'Ld': 8},
        'skill_access': ['combat', 'shooting', 'strength', 'speed', 'special'],
    },
    'big-uns': {
        'cost': 40, 'experience': 15,
        'characteristics': {'M': 4, 'WS': 4, 'BS': 3, 'S': 3, 'T': 4, 'W': 1, 'I': 3, 'A': 1, 'Ld': 7},
        'skill_access': ['combat', 'shooting', 'strength', 'special'],
    },
    'orc-boyz': {
        'cost': 25, 'experience': 0,
        'characteristics': {'M': 4, 'WS': 3, 'BS': 3, 'S': 3, 'T': 4, 'W': 1, 'I': 2, 'A': 1, 'Ld': 7},
        'skill_access': [],
    },
}
DA_MOB_RULE = 'band--da-mob-rules'

PRICE = re.compile(r'^(\d+) gc$')


def load(path: str) -> dict:
    with open(path, encoding='utf-8') as handle:
        return yaml.safe_load(handle)


def save(path: str, doc: dict, write: bool) -> None:
    if not write:
        return
    with open(path, 'w', encoding='utf-8') as handle:
        yaml.safe_dump(doc, handle, allow_unicode=True, sort_keys=False,
                       default_flow_style=False, width=100)


def matches(kind: str, needle: str, item_id: str) -> bool:
    if kind == 'exact':
        return item_id == needle
    if kind == 'prefix':
        return item_id.startswith(needle)
    return needle in item_id


def migrate_equipment_access(path: str, band: str, write: bool, report: list[str]) -> None:
    doc = load(path)
    touched = False
    for lst in doc.get('equipment_lists') or []:
        actions = LIST_NOTE_ACTIONS.get((band, lst.get('id')))
        if 'notes' in lst:
            if not actions:
                report.append(f'!! {band}/{lst.get("id")}: list note has no action, left in place')
            else:
                report.append(f'{band}/{lst.get("id")}: list note distributed')
                del lst['notes']
                touched = True
        for item in lst.get('items') or []:
            if not isinstance(item, dict):
                continue
            stray = [k for k in item if k not in ITEM_KEYS]
            for key in stray:
                fragment = str(key)
                match = PRICE.match(fragment)
                if item.get('cost') is None and match:
                    item['cost'] = int(match.group(1))
                    report.append(f'{band}/{item.get("item_id")}: cost restored from note {fragment!r}')
                else:
                    existing = str(item.get('notes') or '').strip()
                    item['notes'] = f'{existing} {fragment}'.strip()
                    report.append(f'{band}/{item.get("item_id")}: stray key {fragment!r} folded into notes')
                del item[key]
                touched = True
        if not actions:
            continue
        for action in actions:
            if action[0] == 'restrict':
                continue
            if action[0] == 'omit':
                report.append(f'{band}/{lst.get("id")}: {action[3]} (no item to annotate)')
                continue
            _, kind, needle, note = action
            hits = [i for i in (lst.get('items') or [])
                    if isinstance(i, dict) and matches(kind, needle, str(i.get('item_id') or ''))]
            if not hits:
                report.append(f'!! {band}/{lst.get("id")}: no item matches {kind} {needle!r}')
                continue
            for item in hits:
                existing = str(item.get('notes') or '').strip()
                if note in existing:
                    continue
                item['notes'] = f'{existing} {note}'.strip()
                report.append(f'{band}/{item["item_id"]}: +note {note!r}')
                touched = True
    if touched:
        save(path, doc, write)


def list_restrictions() -> dict[str, list[str]]:
    """Equipment-list notes that qualify the profiles allowed to buy from the list."""
    out: dict[str, list[str]] = {}
    for (_, list_id), actions in LIST_NOTE_ACTIONS.items():
        texts = [a[3] for a in actions if a[0] == 'restrict']
        if texts:
            out.setdefault(list_id, []).extend(texts)
    return out


def migrate_profiles(path: str, band: str, write: bool, report: list[str],
                     restrictions: dict[str, list[str]],
                     by_list: dict[str, list[str]]) -> None:
    doc = load(path)
    touched = False
    for profile in doc.get('profiles') or []:
        extra: list[str] = []
        for list_id in (profile.get('equipment_lists') or []):
            for text in by_list.get(list_id, []):
                if text not in (profile.get('equipment_restrictions') or []):
                    extra.append(text)
        for key in ('fixed_equipment', 'equipment_restrictions'):
            value = profile.get(key)
            if not value or not any(isinstance(e, dict) for e in value):
                continue
            out = []
            for entry in value:
                if not isinstance(entry, dict):
                    out.append(entry)
                    continue
                if 'item_id' in entry:
                    out.append(entry['item_id'])
                    if entry.get('note'):
                        extra.append(entry['note'])
                elif 'note' in entry:
                    extra.append(entry['note'])
                else:
                    head, value_ = next(iter(entry.items()))
                    # A label head (``Weapons/Armour``) keeps its colon; a subject
                    # head (``Animals``) joins a lower-case continuation with a space.
                    label = '/' in head or str(value_).strip()[:1].isupper()
                    extra.append(f'{head}{": " if label else " "}{value_}')
            profile[key] = out
            report.append(f'{band}/{profile["id"]}: {key} mapping(s) flattened')
            touched = True
        for text in RELOCATED_MEMBER_NOTES.get((band, profile['id']), []):
            restrictions.setdefault(profile['id'], []).append(text)
        for text in restrictions.get(profile['id'], []):
            profile.setdefault('equipment_restrictions', [])
            if text not in profile['equipment_restrictions']:
                profile['equipment_restrictions'].append(text)
                report.append(f'{band}/{profile["id"]}: +restriction {text!r}')
                touched = True
        for text in DUPLICATED_BY_PROFILE_RULE.get((band, profile['id']), []):
            restrictions_for = profile.get('equipment_restrictions') or []
            if text in restrictions_for:
                profile['equipment_restrictions'] = [r for r in restrictions_for if r != text]
                report.append(f'{band}/{profile["id"]}: -restriction {text!r} (already a profile rule)')
                touched = True
        for text in extra:
            profile.setdefault('equipment_restrictions', [])
            if text not in profile['equipment_restrictions']:
                profile['equipment_restrictions'].append(text)
                report.append(f'{band}/{profile["id"]}: +restriction {text!r}')
                touched = True
        if DA_MOB_RULE in (profile.get('rule_ids') or []):
            profile['rule_ids'] = [r for r in profile['rule_ids'] if r != DA_MOB_RULE]
            report.append(f'{band}/{profile["id"]}: band rule dropped from profile rule_ids')
            touched = True
        if 'references' in profile:
            report.append(f'{band}/{profile["id"]}: dropped references '
                          f'{profile["references"]}')
            del profile['references']
            touched = True
        if band == 'orc-pirates-sar' and profile['id'] in DA_MOB:
            values = dict(DA_MOB[profile['id']])
            values['rule_ids'] = []
            if any(profile.get(key) != value for key, value in values.items()):
                profile.update(values)
                report.append(f'{band}/{profile["id"]}: filled from Da Mob values')
                touched = True
    if touched:
        save(path, doc, write)


def drop_list_translations(path: str, band: str, write: bool, report: list[str],
                           preserved: dict[str, str]) -> None:
    """Equipment lists carry ``id``/``name``/``items``/``source`` only.

    The KB never translates a list name; the Spanish text is preserved in the
    tree's conformance notes instead of in an invented field.
    """
    doc = load(path)
    touched = False
    for lst in doc.get('equipment_lists') or []:
        block = lst.get('name_i18n')
        if not isinstance(block, dict):
            continue
        text = str(block.get('es') or '').strip()
        if text:
            preserved[f'{band}/{lst.get("id")}'] = text
        del lst['name_i18n']
        report.append(f'{band}/{lst.get("id")}: list name_i18n retired ({text!r})')
        touched = True
    if touched:
        save(path, doc, write)


def strip_band_rules_from_profiles(path: str, band: str, write: bool, report: list[str]) -> None:
    """A profile lists its own rules; ``band--`` rules belong to band.yaml."""
    doc = load(path)
    touched = False
    for profile in doc.get('profiles') or []:
        refs = profile.get('rule_ids') or []
        band_rules = [r for r in refs if str(r).startswith('band--')]
        if not band_rules:
            continue
        profile['rule_ids'] = [r for r in refs if not str(r).startswith('band--')]
        report.append(f'{band}/{profile["id"]}: band rules removed from profile rule_ids {band_rules}')
        touched = True
    if touched:
        save(path, doc, write)


def sync_band_rule_ids(path: str, band: str, rules: list[dict], write: bool,
                       report: list[str]) -> None:
    """Every ``band--`` rule of the package is listed in band.yaml rule_ids."""
    doc = load(path)
    listed = list(doc.get('rule_ids') or [])
    for variant in doc.get('variants') or []:
        listed += list(variant.get('rule_ids') or [])
    known = {str(r.get('id')) for r in rules}
    missing = sorted({str(r.get('id')) for r in rules
                      if str(r.get('id', '')).startswith('band--')} - set(listed))
    if not missing:
        return
    doc['rule_ids'] = list(doc.get('rule_ids') or []) + missing
    report.append(f'{band}: band.yaml rule_ids gained {missing}')
    save(path, doc, write)


def migrate_band(path: str, band: str, write: bool, report: list[str]) -> dict[str, list[str]]:
    doc = load(path)
    touched = False
    restrictions: dict[str, list[str]] = {}
    roster = doc.get('roster') or {}
    for key in sorted(set(roster) - ROSTER_KEYS):
        report.append(f'{band}: dropped roster.{key} = {roster[key]!r}')
        del roster[key]
        touched = True
    for member in roster.get('members') or []:
        for key in sorted(set(member) - MEMBER_KEYS):
            note = str(member[key])
            if note in MEMBER_NOTES_DROPPED:
                report.append(f'{band}/{member["profile_id"]}: dropped member note {note!r}')
            elif any(note.startswith(prefix) for prefix in MEMBER_NOTES_AS_RESTRICTION):
                restrictions.setdefault(member['profile_id'], []).append(note)
                report.append(f'{band}/{member["profile_id"]}: member note -> restriction {note!r}')
            else:
                report.append(f'!! {band}/{member["profile_id"]}: unhandled member note {note!r}')
                continue
            del member[key]
            touched = True
    if touched:
        save(path, doc, write)
    return restrictions


def deliver_preserved(tree: str, preserved: dict[str, str], report: list[str]) -> None:
    """Append retired in-package text to the tree's conformance notes."""
    notes = os.path.join('sources', tree, 'conformance-notes.md')
    lines = ['', '## Text retired from the packages (the KB has no field for it)', '',
             '| Where | Text |', '|---|---|']
    for where, text in sorted(preserved.items()):
        lines.append(f'| `{where}` | {text} |')
    with open(notes, 'a', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    report.append(f'{notes}: {len(preserved)} retired list name(s) preserved')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', default='2B')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()

    root = f'sources/{args.tree}/bands'
    report: list[str] = []
    preserved: dict[str, str] = {}
    by_list = list_restrictions()
    for band_path in sorted(glob.glob(f'{root}/*/*/band.yaml')):
        band = os.path.basename(os.path.dirname(band_path))
        rules: list[dict] = []
        rules_path = os.path.join(os.path.dirname(band_path), 'special-rules.yaml')
        if os.path.exists(rules_path):
            for doc in yaml.safe_load_all(open(rules_path, encoding='utf-8')):
                if isinstance(doc, dict):
                    rules += doc.get('rules') or []
        sync_band_rule_ids(band_path, band, rules, args.write, report)
        restrictions = migrate_band(band_path, band, args.write, report)
        profiles = os.path.join(os.path.dirname(band_path), 'profiles.yaml')
        if os.path.exists(profiles):
            migrate_profiles(profiles, band, args.write, report, restrictions, by_list)
            strip_band_rules_from_profiles(profiles, band, args.write, report)
        access = os.path.join(os.path.dirname(band_path), 'equipment-access.yaml')
        if os.path.exists(access):
            migrate_equipment_access(access, band, args.write, report)
            drop_list_translations(access, band, args.write, report, preserved)

    if preserved and args.write:
        deliver_preserved(args.tree, preserved, report)

    print(f'{len(report)} action(s)' + ('' if args.write else ' (dry run)'))
    for line in report:
        print('  ' + line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
