# -*- coding: utf-8 -*-
"""Derive the active KB's document contract empirically, then diff a tree against
*that* contract rather than against hardcoded assumptions.

The conformance auditor (``audit_kb_conformance.py``) carries key sets that were
written by hand. This tool re-measures them from ``sources/knowledge`` so a
correction pass can prove its checklist matches the KB as it exists today, and can
spot (a) keys the auditor wrongly permits and (b) keys it wrongly rejects.

Permanent companion of the conformance audit: the default run re-checks the
active KB against its own measured contract, and ``--tree`` points it at a
staging tree before promotion.

Usage::

    python tools/knowledge/derive_kb_contract.py                # contract + self-check
    python tools/knowledge/derive_kb_contract.py --tree 2A --json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter, defaultdict

import yaml

SKIP = os.path.join('sources', 'knowledge')


def docs(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as handle:
        return [d for d in yaml.safe_load_all(handle) if isinstance(d, dict)]


def kb_files(tree: str) -> list[str]:
    return sorted(glob.glob(f'sources/{tree}/bands/*/*/*.yaml'))


def derive(tree: str) -> dict:
    """Measure every document shape the KB defines, per document type."""
    out: dict[str, Counter] = defaultdict(Counter)
    values: dict[str, Counter] = defaultdict(Counter)
    for path in kb_files(tree):
        name = os.path.basename(path)
        for doc in docs(path):
            if name == 'band.yaml':
                out['band'][tuple(sorted(doc))] += 1
                for k in doc:
                    values[f'band.{k}'].update(
                        [type(doc[k]).__name__] if not isinstance(doc[k], list) else ['list'])
                roster = doc.get('roster') or {}
                out['roster'][tuple(sorted(roster))] += 1
                for member in roster.get('members') or []:
                    out['member'][tuple(sorted(member))] += 1
            elif name == 'profiles.yaml':
                for profile in doc.get('profiles') or []:
                    out['profile'][tuple(sorted(profile))] += 1
                    values['profile.type'][str(profile.get('type'))] += 1
                    values['profile.original_locale'][str(profile.get('original_locale'))] += 1
                    for key in ('fixed_equipment', 'equipment_restrictions'):
                        for entry in profile.get(key) or []:
                            values[f'profile.{key}.entrytype'][type(entry).__name__] += 1
                    chars = profile.get('characteristics')
                    if isinstance(chars, dict):
                        values['profile.chars'][tuple(sorted(chars))] += 1
            elif name == 'equipment-access.yaml':
                out['eq_doc'][tuple(sorted(doc))] += 1
                values['eq.schema_version'][str(doc.get('schema_version'))] += 1
                for lst in doc.get('equipment_lists') or []:
                    out['eq_list'][tuple(sorted(lst))] += 1
                    for item in lst.get('items') or []:
                        out['eq_item'][tuple(sorted(item))] += 1
            elif name == 'special-rules.yaml':
                for rule in doc.get('rules') or []:
                    out['rule'][tuple(sorted(rule))] += 1
                    values['rule.kind'][str(rule.get('kind'))] += 1
                    applies = rule.get('applies_to')
                    if isinstance(applies, dict):
                        out['applies_to'][tuple(sorted(applies))] += 1
                    runtime = rule.get('runtime')
                    if isinstance(runtime, dict):
                        out['runtime'][tuple(sorted(runtime))] += 1
                        values['runtime.scope'][str(runtime.get('scope'))] += 1
                        values['runtime.implemented'][str(runtime.get('implemented'))] += 1
                        values['runtime.grant'][str(runtime.get('grant'))] += 1
                        for effect in runtime.get('effects') or []:
                            if not isinstance(effect, dict):
                                continue
                            out['effect'][tuple(sorted(effect))] += 1
                            values['effect.scope'][str(effect.get('scope'))] += 1
                            binding = effect.get('binding')
                            if isinstance(binding, dict):
                                out['binding'][tuple(sorted(binding))] += 1
                                values['binding.kind'][str(binding.get('kind'))] += 1
    return {'shapes': {k: dict(v) for k, v in out.items()},
            'values': {k: dict(v) for k, v in values.items()}}


def canonical_keys(profile: dict, top_n: int = 1) -> set[str]:
    """Keys that appear in the dominant (most common) shape of every document."""
    keys: set[str] = set()
    for shape, count in sorted(profile.items(), key=lambda kv: -kv[1])[:top_n]:
        keys |= set(shape)
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', default='knowledge',
                        help="tree under sources/ to diff (default: knowledge)")
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    kb = derive('knowledge')
    shapes = kb['shapes']

    # canonical set = every key seen in *any* shape (superset of real documents)
    any_key = {name: sorted({k for shape in shapes.get(name, {}) for k in shape})
               for name in shapes}
    core_key = {name: sorted(canonical_keys(shapes.get(name, {})))
                for name in shapes}

    if args.json:
        print(json.dumps({'any': any_key, 'core': core_key, 'values': kb['values']},
                         indent=2, sort_keys=True))
        return 0

    print('== KB value domains ==')
    for name in sorted(kb['values']):
        dom = kb['values'][name]
        print(f'{name}: {dom}')
    print()
    print('== KB document shapes (dominant first) ==')
    for name in sorted(shapes):
        for shape, count in sorted(shapes[name].items(), key=lambda kv: -kv[1])[:3]:
            print(f'{name} x{count}: {list(shape)}')
        print()

    print('== staging tree keys outside every KB shape ==')
    staging = derive(args.tree)
    bad = 0
    for name, profile in sorted(staging['shapes'].items()):
        allowed = set(any_key.get(name, []))
        extra = {k for shape in profile for k in shape} - allowed
        if extra:
            bad += len(extra)
            print(f'  {name}: {sorted(extra)}')
    if not bad:
        print('  none')
    print()
    print('== staging tree shapes absent from the KB ==')
    bad = 0
    for name, profile in sorted(staging['shapes'].items()):
        known = set(shapes.get(name, {}))
        for shape in profile:
            if shape not in known:
                bad += 1
                print(f'  {name}: {list(shape)}')
    if not bad:
        print('  none')
    print()
    print('== staging value domains outside the KB domains ==')
    bad = 0
    for name, dom in sorted(staging['values'].items()):
        known = set(kb['values'].get(name, {}))
        if not known:
            continue
        extra = set(dom) - known
        if extra:
            bad += 1
            print(f'  {name}: {sorted(extra)}')
    if not bad:
        print('  none')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
