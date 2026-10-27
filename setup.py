"""Build configuration for the compiled native combat backend.

The package keeps setuptools as its backend (see pyproject.toml).  This file
declares the Cython extension consumed by ``mordheim_combat.native`` as
``mordheim_combat._combat_native``.

The native engine is not optional: there is no other optimized backend, so a
missing C compiler or a failed Cython compilation must fail the installation
instead of producing a package that cannot run a duel.  Cython itself is a
build requirement declared in ``pyproject.toml``.
"""

import os

from setuptools import Extension
from setuptools import setup

try:
    from Cython.Build import cythonize
except ImportError as error:  # pragma: no cover - build-time only
    raise SystemExit(
        "Cython is required to build the native combat extension. Install it "
        "with `python -m pip install cython` (it is declared in the project's "
        "build requirements) and run the installation again."
    ) from error

_SOURCE = "packages/python/combat-engine/mordheim_combat/native/_combat_native.pyx"

# Sanitizer support for local debugging: set COMBAT_NATIVE_CFLAGS to inject
# flags into both the compile and link steps (e.g. "/fsanitize=address").
_extra = os.environ.get("COMBAT_NATIVE_CFLAGS", "").split()

_extensions = [
    Extension(
        "mordheim_combat._combat_native",
        sources=[_SOURCE],
        language="c",
        extra_compile_args=_extra,
        extra_link_args=_extra,
    ),
]

setup(ext_modules=cythonize(_extensions, language_level=3))
