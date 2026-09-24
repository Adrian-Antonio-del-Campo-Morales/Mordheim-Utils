# -*- coding: utf-8 -*-
"""One-off: restore special-rules.yaml files damaged by a bad runtime render."""
import glob
import os
import shutil

import yaml

BK = '/tmp/2b-backup-1789503658/bands/mordheim'
restored = []
for f in sorted(glob.glob('sources/2B/bands/mordheim/*/special-rules.yaml')):
    band = os.path.basename(os.path.dirname(f))
    bad = False
    for doc in yaml.safe_load_all(open(f, encoding='utf-8')):
        if not isinstance(doc, dict):
            continue
        for rule in doc.get('rules', []) or []:
            if rule.get('runtime') is None and 'scope' in rule:
                bad = True
    if bad:
        shutil.copyfile(os.path.join(BK, band, 'special-rules.yaml'), f)
        restored.append(band)
print('restored', len(restored))
for band in restored:
    print(' ', band)
