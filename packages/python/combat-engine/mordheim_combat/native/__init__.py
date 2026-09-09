"""mordheim_combat.native: compiled Cython duel engine.

This package holds the sources of the compiled batch backend
(``_combat_native.pyx``/``.pxd`` and the pure-Python ``_combat_compile.py``
folding layer).  The built extension keeps the historical module name
``mordheim_combat._combat_native`` so importers and already-compiled
binaries are unaffected by the source layout.
"""
