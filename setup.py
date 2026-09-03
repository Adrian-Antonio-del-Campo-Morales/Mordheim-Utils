"""Build configuration for the compiled native combat backend.

The package keeps setuptools as its backend (see pyproject.toml).  This file
only declares the Cython extension consumed by ``mordheim_combat.vectorized``
as ``mordheim_combat._combat_native``.  Machines without a C compiler simply
skip the extension: ``available_backends()`` then reports only NumPy.
"""

import os

from setuptools import Extension
from setuptools import setup

try:
    from Cython.Build import cythonize
except ImportError:  # pragma: no cover - build-time only
    cythonize = None

# Sanitizer support for local debugging: set COMBAT_NATIVE_CFLAGS to inject
# flags into both the compile and link steps (e.g. "/fsanitize=address").
_extra = os.environ.get("COMBAT_NATIVE_CFLAGS", "").split()

extensions = [
    Extension(
        "mordheim_combat._combat_native",
        sources=["src/mordheim_combat/native/_combat_native.pyx"],
        language="c",
        optional=True,
        extra_compile_args=_extra,
        extra_link_args=_extra,
    ),
]
if cythonize is not None:
    extensions = cythonize(extensions, language_level=3)

setup(ext_modules=extensions)
