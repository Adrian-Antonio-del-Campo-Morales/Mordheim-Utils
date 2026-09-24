# -*- coding: utf-8 -*-
"""Bring a staging tree's ``special-rules.yaml`` runtime blocks to the canonical KB shape.

Ported from the active KB (``sources/knowledge``) and from the contract in
``sources/knowledge/registry/runtime-schema.yaml``:

* ``runtime`` requires ``scope``, ``implemented``, ``grant`` and ``effects``.
* ``effects`` always lives inside ``runtime`` (never as a rule-level sibling).
* Equivalent rules share ``binding.kind`` + ``binding.id`` + ``binding.parameters``
  with the KB's canonical binding for the same ``rule_ref``.
* A selectable rule declares its ``kind``.

Usage::

    python tools/knowledge/migrate_2b_kb_schema.py            # dry run
    python tools/knowledge/migrate_2b_kb_schema.py --tree 2B --write
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import yaml

# Canonical runtime per shared rule_ref, taken verbatim from the KB rules that
# reference the same rule_ref (reason strings included).
KB_CANON: dict[str, dict] = {
    'shared-rule.armour-2': {
        'scope': 'NO', 'implemented': 'NO',
        'reason': 'Out of scope: no effect applies to the isolated 1v1 duel or legal fighter skill/equipment construction.',
    },
    'shared-rule.hard-to-kill': {
        'scope': 'YES', 'implemented': 'YES',
        'binding': {'kind': 'mechanic', 'id': 'skill.hard-to-kill'},
    },
    'shared-rule.hard-head-2': {
        'scope': 'YES', 'implemented': 'YES',
        'binding': {'kind': 'trait', 'id': 'trait.concussion-immune', 'parameters': {'value': True}},
    },
    'shared-rule.no-pain': {
        'scope': 'YES', 'implemented': 'YES',
        'binding': {'kind': 'mechanic', 'id': 'skill.ignore-pain'},
    },
    'shared-rule.immune-to-poison': {
        'scope': 'YES', 'implemented': 'YES',
        'binding': {'kind': 'trait', 'id': 'trait.poison-immune', 'parameters': {'value': True}},
    },
    'shared-rule.vomit-attack': {
        'scope': 'YES', 'implemented': 'YES', 'grant': 'selectable', 'kind': 'profile_ability',
        'binding': {'kind': 'mechanic', 'id': 'weapon.vomit-attack'},
    },
    'shared-rule.may-not-run': {
        'scope': 'LATER', 'implemented': 'NO',
        'reason': 'Deferred subsystem: psychology or mounts.',
    },
    'shared-rule.wizard': {
        'scope': 'NO', 'implemented': 'NO',
        'reason': 'Out of scope: campaign, shooting, movement, terrain, deployment, or non-duel context.',
    },
    'shared-rule.leader': {
        'scope': 'LATER', 'implemented': 'NO',
        'reason': 'Deferred subsystem: psychology.',
    },
    'shared-rule.stupidity': {
        'scope': 'LATER', 'implemented': 'NO',
        'reason': 'Deferred subsystem: psychology or mounts.',
    },
    'shared-rule.stupidity-2': {
        'scope': 'LATER', 'implemented': 'NO',
        'reason': 'Deferred subsystem: psychology.',
    },
    'shared-rule.experience': {
        'scope': 'NO', 'implemented': 'NO',
        'reason': 'Out of scope: campaign, shooting, movement, terrain, deployment, or non-duel context.',
    },
    'shared-rule.large-target': {
        'scope': 'NO', 'implemented': 'NO',
        'reason': 'Out of scope: shooting.',
    },
    'shared-rule.fear': {
        'scope': 'LATER', 'implemented': 'NO',
        'reason': 'Deferred subsystem: psychology.',
    },
}

# Invented binding ids -> the KB binding that already implements the same mechanic.
BINDING_ALIAS: dict[str, dict] = {
    'trait.immune-to-poison': {'kind': 'trait', 'id': 'trait.poison-immune', 'parameters': {'value': True}},
    'trait.regeneration': {'kind': 'mechanic', 'id': 'skill.regeneration'},
    'trait.vomit-attack': {'kind': 'mechanic', 'id': 'weapon.vomit-attack'},
    'trait.ignore-club-special-rules': {'kind': 'trait', 'id': 'trait.concussion-immune', 'parameters': {'value': True}},
}

RUNTIME_KEYS = ('scope', 'implemented', 'grant', 'effects')


def rule_blocks(lines: list[str]) -> list[tuple[int, int]]:
    starts = [i for i, line in enumerate(lines) if line.startswith('- id: ')]
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        out.append((start, end))
    return out


def key_extent(lines: list[str], start: int, end: int, key: str, indent: int) -> tuple[int, int] | None:
    """Return (first, last+1) line indexes of ``key``'s value inside a block.

    Block-sequence items sit at the same indentation as their key
    (``effects:`` / ``- id:``), so a sibling key stops them only when it does
    not open a sequence item of its own.
    """
    prefix = ' ' * indent + key + ':'
    for i in range(start, end):
        if lines[i].startswith(prefix):
            j = i + 1
            while j < end:
                line = lines[j]
                if not line.strip():
                    j += 1
                    continue
                depth = len(line) - len(line.lstrip(' '))
                if depth < indent:
                    break
                if depth == indent and not line.lstrip().startswith('- '):
                    break
                j += 1
            return i, j
    return None


def render_runtime(runtime: dict) -> list[str]:
    text = yaml.safe_dump({'runtime': runtime}, allow_unicode=True, sort_keys=False,
                          default_flow_style=False, width=100).rstrip('\n')
    return ['  ' + line for line in text.split('\n')]


def effect_for(canon: dict, band: str, subject: str, slug: str) -> dict:
    if 'binding' in canon:
        return {'id': canon['binding']['id'], 'scope': canon['scope'], 'binding': canon['binding']}
    return {
        'id': f'unimplemented.{band}.{subject}.{slug}',
        'scope': canon['scope'],
        'binding': None,
        'reason': canon['reason'],
    }


def migrate(path: Path, write: bool) -> list[str]:
    band = path.parent.name
    lines = path.read_text(encoding='utf-8').split('\n')
    notes: list[str] = []

    for start, end in reversed(rule_blocks(lines)):
        block = lines[start:end]
        parsed = yaml.safe_load('\n'.join(block))
        head = parsed[0] if isinstance(parsed, list) and parsed else parsed
        if not isinstance(head, dict) or 'id' not in head:
            continue
        rule_id = head['id']
        canon = KB_CANON.get(head.get('rule_ref')) if head.get('rule_ref') else None

        changed = False
        sibling = key_extent(lines, start, end, 'effects', 2)
        runtime = dict(head.get('runtime') or {})
        effects: list[dict] = [dict(e) for e in (runtime.get('effects') or [])]

        if sibling:
            effects = [dict(e) for e in (head.get('effects') or [])]
            changed = True
            notes.append(f'{band}/{rule_id}: folded rule-level effects into runtime')

        for eff in effects:
            binding = eff.get('binding') if isinstance(eff, dict) else None
            if isinstance(binding, dict) and binding.get('id') in BINDING_ALIAS:
                old = binding['id']
                eff['binding'] = BINDING_ALIAS[old]
                eff['id'] = BINDING_ALIAS[old]['id']
                changed = True
                notes.append(f'{band}/{rule_id}: binding {old} -> {eff["id"]}')

        if not effects and canon:
            at = head.get('applies_to') or {}
            profiles = at.get('profile_ids') or []
            subject = '-'.join(profiles) if profiles else 'band'
            slug = rule_id.split('--', 1)[1] if '--' in rule_id else rule_id
            effects = [effect_for(canon, band, subject, slug)]
            changed = True
            notes.append(f'{band}/{rule_id}: added runtime.effects from {head["rule_ref"]}')

        if canon:
            for key, value in (('scope', canon['scope']), ('implemented', canon['implemented']),
                               ('grant', canon.get('grant', runtime.get('grant')))):
                if value is not None and runtime.get(key) != value:
                    runtime[key] = value
                    changed = True

        # KB pairing invariant: profile_ids never pairs with grant band, and
        # band:true never pairs with grant profile (0 cases in the active KB).
        applies = head.get('applies_to') or {}
        if isinstance(applies, dict):
            grant = runtime.get('grant')
            if 'profile_ids' in applies and grant == 'band':
                runtime['grant'] = 'profile'
                changed = True
                notes.append(f'{band}/{rule_id}: grant band -> profile (applies_to.profile_ids)')
            elif applies.get('band') and grant == 'profile':
                runtime['grant'] = 'band'
                changed = True
                notes.append(f'{band}/{rule_id}: grant profile -> band (applies_to.band)')

        if effects:
            runtime['effects'] = effects

        ordered = {k: runtime[k] for k in RUNTIME_KEYS if k in runtime}
        ordered.update({k: v for k, v in runtime.items() if k not in RUNTIME_KEYS})

        if not changed:
            continue

        new_block = list(block)
        if sibling:
            del new_block[sibling[0] - start:sibling[1] - start]
        ext = key_extent(new_block, 0, len(new_block), 'runtime', 2)
        rendered = render_runtime(ordered)
        if ext:
            new_block[ext[0]:ext[1]] = rendered
        else:
            insert_at = next((i for i, l in enumerate(new_block) if l.startswith('  name:')), len(new_block))
            new_block[insert_at:insert_at] = rendered

        if canon and canon.get('kind') and not any(l.startswith('  kind:') for l in new_block):
            id_at = next(i for i, l in enumerate(new_block) if l.startswith('- id: '))
            new_block.insert(id_at + 1, f'  kind: {canon["kind"]}')

        lines[start:end] = new_block

    if write and notes:
        path.write_text('\n'.join(lines), encoding='utf-8')
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', default='2B', help='staging tree under sources/ (default: 2B)')
    parser.add_argument('--write', action='store_true', help='apply the migration')
    args = parser.parse_args()

    pattern = f'sources/{args.tree}/bands/*/*/special-rules.yaml'
    notes: list[str] = []
    for name in sorted(glob.glob(pattern)):
        notes += migrate(Path(name), args.write)
    print(f'{len(notes)} change(s)' + ('' if args.write else ' (dry run)'))
    for note in notes:
        print('  ' + note)
    return 0


if __name__ == '__main__':
    sys.exit(main())
