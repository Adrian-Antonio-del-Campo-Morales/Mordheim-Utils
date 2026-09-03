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

_extensions = [
    Extension(
        "mordheim_combat._combat_native",
        sources=["src/mordheim_combat/native/_combat_native.pyx"],
        language="c",
        optional=True,
        extra_compile_args=_extra,
        extra_link_args=_extra,
    ),
]


def _native_buildable() -> bool:
    """Return True when a compatible C compiler is available.

    ``optional=True`` on the extension only tolerates compile errors once a
    compiler was found; a machine without one aborts earlier (for example with
    "Unable to find a compatible Visual Studio installation"), which would
    block the whole install.  Probing the compiler up front preserves the
    documented behaviour: no compiler, no native extension, pure-Python
    install.
    """
    try:
        from distutils.ccompiler import new_compiler

        new_compiler().initialize()
        return True
    except (Exception, SystemExit):
        return False


def _install() -> None:
    if cythonize is not None and _native_buildable():
        setup(ext_modules=cythonize(_extensions, language_level=3))
        return
    if cythonize is None:
        print("Cython not available; skipping the optional native backend "
              "(NumPy backend remains available).")
    else:
        print("No compatible C compiler found; skipping the optional native "
              "backend (NumPy backend remains available).")
    setup()


_install()
