# -*- coding: utf-8 -*-
"""Strip the prose a ``rule_ref`` rule restates, the way the active KB does.

The KB defines a band rule that restates a shared rule as ``rule_ref:
<shared-rule.id>`` **instead of** a duplicated ``effect`` (see
``docs/reference/knowledge-base.md``, "Shared rule text"). No KB band rule carries
both, and no consumer can render the local prose: ``mordheim_knowledge.loader.
shared_rule_text``, ``combat_lab…catalogue._rule_text`` and
``generate_knowledge_web._build_rules_prose`` all resolve ``rule_ref`` to the shared
record and skip the local ``effect``.

This pass removes ``effect`` / ``effect_i18n`` from such rules and archives the
retracted wording (EN + ES) in ``sources/<tree>/retired-rule-restatements.md`` so the
band's own transcription is not lost, only relocated out of a slot nothing reads.

Safety: every file is reloaded after the edit and compared leaf by leaf; the script
aborts unless the *only* difference is the removal of those two keys.

Usage::

    python tools/knowledge/strip_rule_ref_restatements.py                 # dry run
    python tools/knowledge/strip_rule_ref_restatements.py --write
    python tools/knowledge/strip_rule_ref_restatements.py --tree 2B --write
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import yaml

TREES = ('2A', '2B')


def load(path: str) -> dict:
    with open(path, encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


def dump(path: str, doc: dict) -> None:
    text = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100)
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def flatten(node, prefix='') -> dict:
    out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            out.update(flatten(value, f'{prefix}.{key}' if prefix else str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.update(flatten(value, f'{prefix}[{index}]'))
    else:
        out[prefix] = node
    return out


def archive_markdown(tree: str, rows: list[dict]) -> str:
    lines = [
        f'# Prosa retirada de las reglas `rule_ref` de {tree}',
        '',
        'Decisión (2026-09-15): la KB define una regla que repite una regla compartida como',
        '`rule_ref: <shared-rule.id>` **en lugar de** un `effect` duplicado, y ningún',
        'consumidor renderiza la prosa local —`shared_rule_text`, `catalogue._rule_text` y el',
        'generador web resuelven siempre el registro compartido—. Estas reglas llevaban las',
        'dos cosas, así que la prosa local se retiró para dejar la forma KB exacta.',
        '',
        'La redacción de la fuente (EN y su traducción ES) se conserva aquí: la vista no',
        'cambia, porque ese texto ya se ignoraba al renderizar; el texto que se muestra sigue',
        'siendo el de la regla compartida de `sources/knowledge/catalog/rules/special-rules.yaml`.',
        '',
        'Regenerable con `python tools/knowledge/strip_rule_ref_restatements.py --tree '
        + tree + ' --write` (idempotente).',
        '',
    ]
    for row in sorted(rows, key=lambda r: (r['band'], r['rule'])):
        lines.append(f"## `{row['band']}` → `{row['rule']}` (`{row['rule_ref']}`)")
        lines.append('')
        lines.append(f"**Nombre:** {row['name']} — ES: {row['name_es'] or '—'}")
        lines.append('')
        for label, value in (('EN (fuente)', row['effect']), ('ES (traducción)', row['effect_es'])):
            if not value:
                continue
            lines.append(f'**{label}:**')
            lines.append('')
            lines.append('> ' + ' '.join(str(value).split()))
            lines.append('')
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', default='both', help='2A, 2B or both')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()

    trees = TREES if args.tree == 'both' else (args.tree,)
    failures = 0
    for tree in trees:
        rows: list[dict] = []
        changed_files = 0
        for path in sorted(glob.glob(f'sources/{tree}/bands/*/*/special-rules.yaml')):
            band = os.path.basename(os.path.dirname(path))
            before = load(path)
            before_leaves = flatten(before)
            doc = load(path)
            dirty = False
            for rule in doc.get('rules') or []:
                ref = rule.get('rule_ref')
                if not ref or ('effect' not in rule and 'effect_i18n' not in rule):
                    continue
                names = rule.get('name_i18n') or {}
                rows.append({
                    'band': band,
                    'rule': str(rule.get('id')),
                    'rule_ref': str(ref),
                    'name': str(rule.get('name') or ''),
                    'name_es': str(names.get('es') or ''),
                    'effect': str(rule.get('effect') or ''),
                    'effect_es': str((rule.get('effect_i18n') or {}).get('es') or ''),
                })
                rule.pop('effect', None)
                rule.pop('effect_i18n', None)
                dirty = True
            if not dirty:
                continue
            after_leaves = flatten(doc)
            removed = {k: v for k, v in before_leaves.items() if k not in after_leaves}
            added = {k: v for k, v in after_leaves.items() if k not in before_leaves}
            kept_changed = {k for k in after_leaves
                            if k in before_leaves and after_leaves[k] != before_leaves[k]}
            bad = {k for k in removed if not k.endswith(('.effect', '.effect_i18n.es'))}
            if bad or added or kept_changed:
                print(f'ABORT {path}: unexpected change {sorted(bad | set(added) | kept_changed)[:5]}')
                failures += 1
                continue
            changed_files += 1
            if args.write:
                dump(path, doc)
        print(f'{tree}: {len(rows)} rule(s) to strip across {changed_files} file(s)'
              f'{" [written]" if args.write else " [dry run]"}')
        if args.write and rows:
            out = f'sources/{tree}/retired-rule-restatements.md'
            with open(out, 'w', encoding='utf-8', newline='\n') as handle:
                handle.write(archive_markdown(tree, rows))
            print(f'  archived wording in {out}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
