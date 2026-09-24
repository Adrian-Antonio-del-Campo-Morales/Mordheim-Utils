# -*- coding: utf-8 -*-
"""Audit a knowledge tree's shape against the active KB patterns.

Read-only, and permanent: point it at the active KB to prove the published
documents still match the contract (0 deviations is the expected baseline), or
at a staging tree to check it before promotion. Reports every deviation class
the KB contract defines, so a correction pass has one reproducible checklist
instead of ad-hoc greps.

Checks
------
* ``band.yaml``: top-level keys, roster keys, member keys, rule_ids listing
  (every ``band--`` rule present in the package must be listed).
* ``profiles.yaml``: profile keys, ``type`` vocabulary, the nine
  ``characteristics`` keys, dict entries in ``fixed_equipment`` /
  ``equipment_restrictions``, invented ``references``, ``skill_access`` tokens.
* ``equipment-access.yaml``: document / list / item keys.
* ``special-rules.yaml``: rule keys, ``applies_to`` shapes, the runtime
  contract (required fields, values, selectable ``kind``), rule-level
  ``effects``, effect ``id``/``scope``, ``binding.kind`` vocabulary,
  ``binding.id`` reuse vs the KB, ``rule_ref`` resolution, and staged bindings
  declared in ``registry/bindings.yaml`` (reported as ``binding-pending-promotion``).

Usage::

    python tools/knowledge/audit_kb_conformance.py                 # the active KB
    python tools/knowledge/audit_kb_conformance.py --tree 2A       # a staging tree
    python tools/knowledge/audit_kb_conformance.py --tree 2B --json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

KB_BANDS = 'sources/knowledge/bands'
KB_BAND_KEYS = {'id', 'canonical_family', 'name', 'name_i18n', 'original_locale', 'ruleset',
                'categories', 'grade', 'setting', 'publication', 'status', 'sources', 'roster',
                'rule_ids', 'variants', 'schema_version'}
KB_ROSTER_KEYS = {'minimum_models', 'maximum_models', 'starting_gold', 'members'}
KB_MEMBER_KEYS = {'profile_id', 'minimum', 'maximum', 'group_size'}
KB_PROFILE_KEYS = {'id', 'name', 'type', 'cost', 'experience', 'characteristics',
                   'equipment_lists', 'fixed_equipment', 'equipment_restrictions',
                   'skill_access', 'source', 'source_path', 'name_i18n', 'rule_ids',
                   'combat_traits', 'group_size', 'components'}
KB_TYPES = {'hero', 'henchman', 'animal', 'summoned'}
KB_CHARS = ['M', 'WS', 'BS', 'S', 'T', 'W', 'I', 'A', 'Ld']
KB_EQ_DOC_KEYS = {'schema_version', 'band_id', 'equipment_lists'}
KB_EQ_LIST_KEYS = {'id', 'name', 'items', 'source', 'loadouts'}
KB_ITEM_KEYS = {'item_id', 'cost', 'notes', 'price_override'}
KB_RULE_KEYS = {'id', 'name', 'name_i18n', 'effect', 'effect_i18n', 'source', 'applies_to',
                'runtime', 'rule_ref', 'kind', 'eligibility', 'skill_category',
                'runtime_selectable'}
KB_SCOPES = {'YES', 'NO', 'LATER'}
KB_GRANTS = {'profile', 'band', 'selectable', 'none'}
KB_RULE_KINDS = {'warband_skill', 'mutation', 'blessing', 'virtue', 'mark', 'modification',
                 'profile_ability', 'warband_variant'}
KB_BINDING_KINDS = {'mechanic', 'trait', 'profile', 'compiler'}
PROFILE_SKILL_TOKENS = {'combat', 'shooting', 'academic', 'strength', 'speed', 'special',
                        'pirate', 'musicianship', 'cavalry'}
# Classes that are reported but are not defects: they are adjudicated, documented
# findings (a mechanic with no KB equivalent, a rule that restates a shared rule it
# also references). They do not make the audit red.
INFO_CLASSES = {'binding-unseen', 'binding-pending-promotion'}


def docs(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as handle:
        return [d for d in yaml.safe_load_all(handle) if isinstance(d, dict)]


def kb_bindings() -> set[str]:
    out: set[str] = set()
    for path in glob.glob(f'{KB_BANDS}/*/*/special-rules.yaml'):
        for doc in docs(path):
            for rule in doc.get('rules') or []:
                for effect in ((rule.get('runtime') or {}).get('effects') or []):
                    binding = effect.get('binding') if isinstance(effect, dict) else None
                    if isinstance(binding, dict) and binding.get('id'):
                        out.add(str(binding['id']))
    return out


def registered_bindings() -> set[str]:
    """Binding ids declared in registry/bindings.yaml (staged, pre-promotion)."""
    path = 'sources/knowledge/registry/bindings.yaml'
    out: set[str] = set()
    if os.path.exists(path):
        for doc in docs(path):
            for entry in doc.get('bindings') or []:
                if isinstance(entry, dict) and entry.get('id'):
                    out.add(str(entry['id']))
    return out


def kb_rule_refs() -> set[str]:
    out: set[str] = set()
    for path in glob.glob(f'{KB_BANDS}/*/*/special-rules.yaml'):
        for doc in docs(path):
            for rule in doc.get('rules') or []:
                if rule.get('rule_ref'):
                    out.add(str(rule['rule_ref']))
    shared = 'sources/knowledge/catalog/rules/special-rules.yaml'
    if os.path.exists(shared):
        for doc in docs(shared):
            for rule in doc.get('rules') or []:
                out.add(str(rule.get('id')))
    return out


def kb_key_sets() -> dict[str, set[str]]:
    """Every key the active KB itself carries, per document context.

    The hand-written sets above are the baseline; the KB is the contract as it
    exists today, so a key its own documents use must never be reported as
    invented (``chaos-streets-undead-bloodlines`` carries ``profile.bloodline``
    and ``roster.requires_variant_selection``, and its summoning rules carry
    ``summoned_count`` / ``summoned_profile_id``). Measured once per run from
    ``sources/knowledge``; the tree under audit contributes nothing, so a
    staging tree still cannot smuggle in a key the KB does not use.
    """
    out: dict[str, set[str]] = {
        name: set() for name in ('band', 'roster', 'member', 'profile', 'rule',
                                 'eq-doc', 'eq-list', 'eq-item')
    }
    for path in glob.glob(f'{KB_BANDS}/*/*/band.yaml'):
        doc = docs(path)[0]
        out['band'] |= set(doc)
        roster = doc.get('roster') or {}
        out['roster'] |= set(roster)
        for member in roster.get('members') or []:
            out['member'] |= set(member)
    for path in glob.glob(f'{KB_BANDS}/*/*/profiles.yaml'):
        for doc in docs(path):
            for profile in doc.get('profiles') or []:
                out['profile'] |= set(profile)
    for path in glob.glob(f'{KB_BANDS}/*/*/special-rules.yaml'):
        for doc in docs(path):
            for rule in doc.get('rules') or []:
                out['rule'] |= set(rule)
    for path in glob.glob(f'{KB_BANDS}/*/*/equipment-access.yaml'):
        for doc in docs(path):
            out['eq-doc'] |= set(doc)
            for entry in doc.get('equipment_lists') or []:
                out['eq-list'] |= set(entry)
                for item in entry.get('items') or []:
                    if isinstance(item, dict):
                        out['eq-item'] |= set(item)
    return out


def audit(tree: str) -> dict:
    report: dict[str, list] = defaultdict(list)
    bindings = kb_bindings()
    pending_bindings = registered_bindings()
    refs = kb_rule_refs()
    known = kb_key_sets()
    band_keys = KB_BAND_KEYS | known['band']
    roster_keys = KB_ROSTER_KEYS | known['roster']
    member_keys = KB_MEMBER_KEYS | known['member']
    profile_keys = KB_PROFILE_KEYS | known['profile']
    rule_keys = KB_RULE_KEYS | known['rule']
    eq_doc_keys = KB_EQ_DOC_KEYS | known['eq-doc']
    eq_list_keys = KB_EQ_LIST_KEYS | known['eq-list']
    item_keys = KB_ITEM_KEYS | known['eq-item']
    bands = sorted(os.path.basename(os.path.dirname(p))
                   for p in glob.glob(f'sources/{tree}/bands/*/*/band.yaml'))
    for band in bands:
        root = f'sources/{tree}/bands/*/{band}'
        band_path = glob.glob(f'{root}/band.yaml')
        if not band_path:
            continue
        band_doc = docs(band_path[0])[0]
        for key in sorted(set(band_doc) - band_keys):
            report['band-key'].append(f'{band}: band.yaml key {key!r}')
        roster = band_doc.get('roster') or {}
        for key in sorted(set(roster) - roster_keys):
            report['roster-key'].append(f'{band}: roster.{key}')
        for member in roster.get('members') or []:
            for key in sorted(set(member) - member_keys):
                report['member-key'].append(f'{band}/{member.get("profile_id")}: member.{key}')

        rules_path = glob.glob(f'{root}/special-rules.yaml')
        rules: list[dict] = []
        if rules_path:
            for doc in docs(rules_path[0]):
                rules += doc.get('rules') or []
        listed = set(band_doc.get('rule_ids') or [])
        for variant in band_doc.get('variants') or []:
            listed |= set(variant.get('rule_ids') or [])
        band_rules = {str(r.get('id')) for r in rules if str(r.get('id', '')).startswith('band--')}
        for rule_id in sorted(band_rules - listed):
            report['rule-not-listed'].append(f'{band}: band rule {rule_id!r} missing from band.yaml')
        for rule_id in sorted(listed - {str(r.get("id")) for r in rules}):
            report['rule-dangling'].append(f'{band}: rule_ids lists unknown rule {rule_id!r}')

        profile_ids: set[str] = set()
        profiles_path = glob.glob(f'{root}/profiles.yaml')
        if profiles_path:
            for doc in docs(profiles_path[0]):
                for profile in doc.get('profiles') or []:
                    profile_ids.add(str(profile.get('id')))
                    pid = profile.get('id')
                    for key in sorted(set(profile) - profile_keys):
                        report['profile-key'].append(f'{band}/{pid}: profile key {key!r}')
                    if profile.get('type') not in KB_TYPES:
                        report['profile-type'].append(f'{band}/{pid}: type {profile.get("type")!r}')
                    chars = profile.get('characteristics')
                    if isinstance(chars, dict) and set(chars) != set(KB_CHARS):
                        report['characteristics'].append(
                            f'{band}/{pid}: characteristics keys {sorted(chars)}')
                    for key in ('fixed_equipment', 'equipment_restrictions'):
                        value = profile.get(key) or []
                        if any(isinstance(entry, dict) for entry in value):
                            report['profile-dict-entry'].append(f'{band}/{pid}: {key} holds a mapping')
                    for token in profile.get('skill_access') or []:
                        if token not in PROFILE_SKILL_TOKENS:
                            report['skill-token'].append(f'{band}/{pid}: skill_access {token!r}')
                    for rule_id in profile.get('rule_ids') or []:
                        if str(rule_id).startswith('band--'):
                            report['profile-band-rule'].append(f'{band}/{pid}: {rule_id}')
                        elif rule_id not in {str(r.get("id")) for r in rules}:
                            report['profile-rule-dangling'].append(f'{band}/{pid}: {rule_id}')

        access_path = glob.glob(f'{root}/equipment-access.yaml')
        if access_path:
            for doc in docs(access_path[0]):
                for key in sorted(set(doc) - eq_doc_keys):
                    report['eq-doc-key'].append(f'{band}: equipment-access.{key}')
                for lst in doc.get('equipment_lists') or []:
                    for key in sorted(set(lst) - eq_list_keys):
                        report['eq-list-key'].append(f'{band}/{lst.get("id")}: list.{key}')
                    for item in lst.get('items') or []:
                        if not isinstance(item, dict):
                            continue
                        for key in sorted(set(item) - item_keys):
                            report['eq-item-key'].append(
                                f'{band}/{lst.get("id")}/{item.get("item_id")}: item key {key!r}')

        for rule in rules:
            rule_id = str(rule.get('id'))
            for key in sorted(set(rule) - rule_keys):
                report['rule-key'].append(f'{band}/{rule_id}: rule key {key!r}')
            if 'effects' in rule:
                report['rule-effects-sibling'].append(f'{band}/{rule_id}')
            applies = rule.get('applies_to')
            if isinstance(applies, dict) and set(applies) - {'band', 'profile_ids'}:
                report['applies-to'].append(f'{band}/{rule_id}: {sorted(applies)}')
            runtime = rule.get('runtime')
            if not isinstance(runtime, dict):
                continue
            for field in ('scope', 'implemented', 'grant', 'effects'):
                if field not in runtime:
                    report['runtime-field'].append(f'{band}/{rule_id}: runtime.{field} missing')
            if runtime.get('scope') not in KB_SCOPES:
                report['runtime-value'].append(f'{band}/{rule_id}: scope {runtime.get("scope")!r}')
            if str(runtime.get('implemented')) not in {'YES', 'NO'}:
                report['runtime-value'].append(
                    f'{band}/{rule_id}: implemented {runtime.get("implemented")!r}')
            if runtime.get('grant') not in KB_GRANTS:
                report['runtime-value'].append(f'{band}/{rule_id}: grant {runtime.get("grant")!r}')
            if runtime.get('grant') == 'selectable' and rule.get('kind') not in KB_RULE_KINDS:
                report['selectable-kind'].append(f'{band}/{rule_id}: kind {rule.get("kind")!r}')
            # KB pairing: profile_ids never pairs with grant band, and band:true
            # never pairs with grant profile (0 cases in the active KB).
            if isinstance(applies, dict):
                grant = runtime.get('grant')
                if 'profile_ids' in applies and grant == 'band':
                    report['grant-scope'].append(
                        f'{band}/{rule_id}: applies_to.profile_ids with grant band')
                elif applies.get('band') and grant == 'profile':
                    report['grant-scope'].append(
                        f'{band}/{rule_id}: applies_to.band with grant profile')
            effects = runtime.get('effects')
            if not effects:
                report['runtime-effects-empty'].append(f'{band}/{rule_id}')
            for effect in effects or []:
                if not isinstance(effect, dict):
                    report['effect-shape'].append(f'{band}/{rule_id}: non-dict effect')
                    continue
                if not effect.get('id'):
                    report['effect-shape'].append(f'{band}/{rule_id}: effect without id')
                if effect.get('scope') not in KB_SCOPES:
                    report['effect-shape'].append(
                        f'{band}/{rule_id}: effect scope {effect.get("scope")!r}')
                binding = effect.get('binding')
                if isinstance(binding, dict):
                    if binding.get('kind') not in KB_BINDING_KINDS:
                        report['binding-kind'].append(
                            f'{band}/{rule_id}: binding.kind {binding.get("kind")!r}')
                    if binding.get('id') and binding['id'] not in bindings:
                        # Registry-declared ids are staged, not unknown: they are reported
                        # apart so the CI gate (tests/python/knowledge/test_binding_registry.py)
                        # stays the authority on registration.
                        if binding['id'] in pending_bindings:
                            report['binding-pending-promotion'].append(
                                f'{band}/{rule_id}: {binding["id"]} (declared in registry/bindings.yaml)')
                        else:
                            report['binding-unseen'].append(f'{band}/{rule_id}: {binding["id"]}')
                elif effect.get('scope') in {'NO', 'LATER'} and not effect.get('reason'):
                    report['effect-no-reason'].append(f'{band}/{rule_id}: {effect.get("id")}')
            ref = rule.get('rule_ref')
            if ref and str(ref) not in refs:
                report['rule-ref'].append(f'{band}/{rule_id}: {ref}')
            # A rule that references a shared rule *and* restates the prose is a shape
            # the KB never uses (0 of 898 band rules): every consumer renders the shared
            # record and ignores the local ``effect``, so the restatement is currently
            # dead text. Reported for adjudication, not counted as a defect.
            if ref and rule.get('effect'):
                report['rule-ref-restated'].append(f'{band}/{rule_id}: {ref}')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', default='knowledge',
                        help="tree under sources/ to audit (default: knowledge, the active KB)")
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--show', type=int, default=8, help='examples per class')
    args = parser.parse_args()

    report = audit(args.tree)
    if args.json:
        print(json.dumps({k: len(v) for k, v in sorted(report.items())}, indent=2))
        return 0

    counted = {k: v for k, v in report.items() if k not in INFO_CLASSES}
    info = {k: v for k, v in report.items() if k in INFO_CLASSES}
    total = sum(len(v) for v in counted.values())
    print(f'sources/{args.tree}: {total} deviation(s) across {len(counted)} class(es)'
          f' (+{sum(len(v) for v in info.values())} informational)')
    for kind, items in sorted(counted.items()):
        print(f'\n## {kind} ({len(items)})')
        for item in items[:args.show]:
            print('  ' + item)
        if len(items) > args.show:
            print(f'  … {len(items) - args.show} more')
    for kind, items in sorted(info.items()):
        print(f'\n## {kind} ({len(items)}) [informational]')
        for item in items[:args.show]:
            print('  ' + item)
        if len(items) > args.show:
            print(f'  … {len(items) - args.show} more')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
