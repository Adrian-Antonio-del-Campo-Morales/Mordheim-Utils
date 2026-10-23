"""MiniRacer imports with explicit packed layouts on Python 3.14+.

mini-racer 0.14.1 relies on ctypes' deprecated implicit MSVC layout. Declare
the same layout before its two structures are created. Remove this adapter
when the pinned upstream release declares these layouts itself.
"""
from __future__ import annotations

from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder, SourceFileLoader
import sys


_STRUCTURES = {
    "py_mini_racer._dll": "_RawValue",
    "py_mini_racer._objects": "_ArrayBufferByte",
}


class _LayoutLoader(SourceFileLoader):
    def get_code(self, fullname):
        # Compile the corrected source directly, without reading/writing pyc
        # caches or modifying the installed dependency.
        source = self.get_source(fullname)
        declaration = f"class {_STRUCTURES[fullname]}(ctypes.Structure):"
        if source is None or source.count(declaration) != 1:
            raise ImportError(f"Unexpected MiniRacer structure in {fullname}")
        source = source.replace(declaration, declaration + '\n    _layout_ = "ms"', 1)
        return self.source_to_code(source, self.path)


class _LayoutFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname not in _STRUCTURES:
            return None
        spec = PathFinder.find_spec(fullname, path)
        if spec is not None and isinstance(spec.loader, SourceFileLoader):
            spec.loader = _LayoutLoader(fullname, spec.origin)
        return spec


if sys.version_info >= (3, 14):
    _finder = _LayoutFinder()
    sys.meta_path.insert(0, _finder)
    try:
        from py_mini_racer import JSEvalException, MiniRacer
    finally:
        sys.meta_path.remove(_finder)
else:
    from py_mini_racer import JSEvalException, MiniRacer


__all__ = ["JSEvalException", "MiniRacer"]
