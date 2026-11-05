"""Provenance of a result: which sources and build produced it.

Shared by the verification tools and the runtime services (benchmark
baselines, calibration profiles), so it lives outside ``verification``.

Parity campaigns are long, so results computed by an older engine are reused
on purpose.  A provenance difference is therefore a *warning*, never a refusal:
``provenance_warning`` prints it prominently and returns the text so the caller
can also embed it in its report.  Only faults of the run itself (a pool worker
running another engine than its parent, a requested backend that is missing)
are errors, and those are decided by the callers.

Engine digests hash the Python/Cython sources each engine executes, including
the packages it imports from the others: NumPy imports ``modular.state``,
``modular.equipment`` and ``modular.mutations``; the native backend runs
through ``vectorized.simulate_duel`` and its compile helpers.  The built native
extension is hashed separately (``build_sha256``): its bytes differ between
machines and compilers even for identical sources.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ENGINES = ("modular", "numpy", "native")


def engine_sources(engine: str, combat: Path, core: Path) -> tuple[Path, ...]:
    """Source files whose behaviour one engine's results depend on.

    ``combat`` is the ``mordheim_combat`` package directory and ``core`` the
    ``mordheim_core`` one.  A native-only change never moves the modular or
    NumPy digests; a modular change moves all three, because the candidates
    import modular helpers.
    """
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}; choose one of {', '.join(ENGINES)}")
    paths = [
        combat / "__init__.py",
        combat / "phases.py",
        *sorted((combat / "modular").glob("*.py")),
        *sorted(core.glob("*.py")),
    ]
    if engine in ("numpy", "native"):
        paths += [
            combat / "kernel.py",
            combat / "vector_dice.py",
            *sorted((combat / "vectorized").glob("*.py")),
        ]
    if engine == "native":
        paths += [
            combat / "_combat_compile.py",
            *sorted((combat / "native").glob("*.py")),
            *sorted((combat / "native").glob("*.pyx")),
            *sorted((combat / "native").glob("*.pxd")),
        ]
    return tuple(paths)


def digest_files(paths: Iterable[Path], root: Path) -> str:
    """SHA-256 over (relative label, bytes) of each file, order-independent."""
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        try:
            label = path.relative_to(root).as_posix()
        except ValueError:
            label = path.name
        digest.update(label.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def native_build_sha256() -> str | None:
    """SHA-256 of the imported native extension, or ``None`` when absent."""
    try:
        from mordheim_combat import _combat_native
    except ImportError:
        return None
    return hashlib.sha256(Path(_combat_native.__file__).read_bytes()).hexdigest()


def imported_package_dirs() -> dict[str, Path]:
    """Directories the engine packages were actually imported from."""
    import mordheim_combat
    import mordheim_core

    return {
        "mordheim_combat": Path(mordheim_combat.__file__).resolve().parent,
        "mordheim_core": Path(mordheim_core.__file__).resolve().parent,
    }


def source_revision(root: Path) -> dict[str, object]:
    """Git commit, branch and dirty state of ``root``; ``None`` fields if unknown."""
    def git(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args], text=True, cwd=str(root), stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None

    commit = git("rev-parse", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=no")
    changed = [] if status is None else [line[3:] for line in status.splitlines() if line.strip()]
    return {
        "commit": commit.strip() if commit else None,
        "branch": branch.strip() if branch else None,
        "dirty": None if status is None else bool(changed),
        "dirty_paths": changed[:50],
    }


def provenance_warning(message: str, *, stream=None) -> str:
    """Print one prominent provenance warning and return its text."""
    text = f"PROVENANCE WARNING: {message}"
    print(f"\n!!! {text}\n", file=stream or sys.stderr, flush=True)
    return text


def describe_difference(what: str, recorded: object, current: object) -> str | None:
    """A one-line description when ``recorded`` and ``current`` differ."""
    if recorded == current:
        return None
    def short(value: object) -> str:
        return value[:12] if isinstance(value, str) and len(value) == 64 else repr(value)
    return f"{what} differs (recorded {short(recorded)}, current {short(current)})"


def run_provenance(root: Path, engines: Iterable[str], *, emit: bool = True) -> dict[str, object]:
    """Provenance block of one run: what executed, from where, at which revision.

    Digests are taken from the packages actually imported, so they describe
    the engine that ran even when it is not this checkout's.  Engine copies
    imported from outside ``root`` and uncommitted sources are reported as
    warnings (printed when ``emit``), never as errors.
    """
    root = Path(root).resolve()
    dirs = imported_package_dirs()
    warnings: list[str] = []
    for name, directory in dirs.items():
        if root not in directory.parents:
            warnings.append(
                f"{name} was imported from {directory.as_posix()}, outside "
                f"{root.as_posix()}; the recorded digests describe that copy"
            )
    revision = source_revision(root)
    if revision["dirty"]:
        shown = ", ".join(revision["dirty_paths"][:5])
        more = len(revision["dirty_paths"]) - 5
        warnings.append(
            "the checkout has uncommitted changes, so these results match no commit "
            f"({shown}{f' and {more} more' if more > 0 else ''})"
        )
    engines = tuple(engines)
    block: dict[str, object] = {
        "revision": revision,
        "imported_from": {name: directory.as_posix() for name, directory in dirs.items()},
        "engine_digests": {
            engine: digest_files(engine_sources(
                engine, dirs["mordheim_combat"], dirs["mordheim_core"]), root)
            for engine in engines
        },
        "native_build_sha256": native_build_sha256() if "native" in engines else None,
        "warnings": warnings,
    }
    if emit:
        for message in warnings:
            provenance_warning(message)
    return block


__all__ = (
    "ENGINES",
    "describe_difference",
    "digest_files",
    "engine_sources",
    "imported_package_dirs",
    "native_build_sha256",
    "provenance_warning",
    "run_provenance",
    "source_revision",
)
