"""Give a checkout or git worktree its own virtual environment, and prove it.

Every checkout must run its own sources: an editable install records absolute
paths, so a venv shared between worktrees silently imports the packages (and
the compiled native extension) of whichever checkout created it.  This tool
uses the standard library only, so any Python 3.10+ can run it before a venv
exists::

    python3 tools/setup_worktree.py            # create or repair <root>/.venv, then verify
    python3 tools/setup_worktree.py --check    # verify only; exit 1 when not isolated
    python3 tools/setup_worktree.py --node     # also install this checkout's npm workspaces
    python3 tools/setup_worktree.py --recreate # discard <root>/.venv and build it again

``<root>`` is the git top level of the current directory (``--root`` overrides
it).  Setup creates ``<root>/.venv`` from the running interpreter's base Python,
installs the checkout editable with its ``dev`` extra, and builds the native
extension in place when the install did not leave one importable from
``<root>``.  Verification runs the venv's interpreter in a clean environment
(no ``PYTHONPATH``, no inherited ``VIRTUAL_ENV``, outside the checkout) and
requires every project package and the native extension to resolve under
``<root>``.  A missing compiler is reported, not hidden: verification then
fails for the native extension unless ``--allow-no-native`` is given.

Exit codes: 0 isolated, 1 not isolated (the report names every offending
import), 2 setup failure.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

#: Importable project packages and the compiled extension, checked by origin.
PROJECT_MODULES = (
    "mordheim_core",
    "mordheim_knowledge",
    "mordheim_construction",
    "mordheim_combat",
    "mordheim_combat_lab",
)
NATIVE_MODULE = "mordheim_combat._combat_native"

_PROBE = """
import importlib, json, sys
report = {"executable": sys.executable, "prefix": sys.prefix, "modules": {}}
for name in sys.argv[1:]:
    try:
        module = importlib.import_module(name)
        report["modules"][name] = {"file": module.__file__}
    except Exception as error:
        report["modules"][name] = {"error": f"{type(error).__name__}: {error}"}
print(json.dumps(report))
"""


def git_root(start: Path) -> Path:
    """The checkout or worktree top level containing ``start``."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=start, text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit(f"setup: {start} is not inside a git checkout; pass --root")
    return Path(out.strip()).resolve()


def venv_python(root: Path) -> Path:
    scripts = "Scripts" if os.name == "nt" else "bin"
    name = "python.exe" if os.name == "nt" else "python"
    return root / ".venv" / scripts / name


def clean_environment() -> dict[str, str]:
    """The caller's environment without anything that redirects imports."""
    env = {key: value for key, value in os.environ.items()
           if key not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONSTARTUP")}
    foreign = os.environ.get("VIRTUAL_ENV")
    if foreign:
        scripts = str(Path(foreign) / ("Scripts" if os.name == "nt" else "bin"))
        env["PATH"] = os.pathsep.join(
            part for part in env.get("PATH", "").split(os.pathsep) if part != scripts)
    return env


def probe(python: Path, modules: tuple[str, ...]) -> dict:
    """Import ``modules`` with ``python`` in a clean process outside any checkout."""
    with tempfile.TemporaryDirectory() as neutral:
        completed = subprocess.run(
            [str(python), "-I", "-c", _PROBE, *modules],
            cwd=neutral, env=clean_environment(), capture_output=True, text=True,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"{python} could not run the import probe: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def isolation_problems(root: Path, report: dict, *, require_native: bool = True,
                       require_local_venv: bool = True) -> list[str]:
    """Every way ``report`` (from :func:`probe`) imports outside ``root``.

    ``require_local_venv`` also demands that the interpreter be ``root/.venv``;
    callers that accept another dedicated interpreter (CI installs the
    checkout into the runner's Python) check the import origins only.
    """
    root = root.resolve()
    problems = []
    prefix = Path(report["prefix"]).resolve()
    if require_local_venv and prefix != (root / ".venv").resolve():
        problems.append(f"interpreter prefix is {prefix}, not {root / '.venv'}")
    for name, entry in report["modules"].items():
        if "error" in entry:
            if name == NATIVE_MODULE and not require_native:
                continue
            problems.append(f"{name} does not import: {entry['error']}")
            continue
        origin = Path(entry["file"]).resolve()
        if root not in origin.parents:
            problems.append(f"{name} is imported from {origin}, outside {root}")
    return problems


def _run(argv: list[str], root: Path) -> None:
    print("+ " + " ".join(argv), flush=True)
    completed = subprocess.run(argv, cwd=root, env=clean_environment())
    if completed.returncode != 0:
        raise SystemExit(f"setup: command failed with exit code {completed.returncode}")


def base_python() -> str:
    """The interpreter a new venv is built from (never another venv's wrapper)."""
    return getattr(sys, "_base_executable", None) or sys.executable


def setup(root: Path, *, recreate: bool, node: bool) -> None:
    venv = root / ".venv"
    if recreate and venv.exists():
        print(f"removing {venv}")
        shutil.rmtree(venv)
    python = venv_python(root)
    if not python.exists():
        _run([base_python(), "-m", "venv", str(venv)], root)
    _run([str(python), "-m", "pip", "install", "--upgrade", "pip"], root)
    _run([str(python), "-m", "pip", "install", "-e", ".[dev]"], root)
    # The editable install may leave the extension in its build directory or
    # skip it; the checkout's own copy must sit next to its sources.
    native = probe(python, (NATIVE_MODULE,))["modules"][NATIVE_MODULE]
    if "error" in native or root not in Path(native["file"]).resolve().parents:
        _run([str(python), "-m", "pip", "install", "cython>=3.1", "setuptools>=69"], root)
        _run([str(python), "setup.py", "build_ext", "--inplace"], root)
    if node:
        npm = shutil.which("npm")
        if npm is None:
            raise SystemExit("setup: --node needs npm on PATH")
        _run([npm, "ci"], root)


def check(root: Path, *, require_native: bool) -> int:
    python = venv_python(root)
    if not python.exists():
        print(f"NOT ISOLATED: {root} has no .venv; run python3 tools/setup_worktree.py")
        return 1
    report = probe(python, (*PROJECT_MODULES, NATIVE_MODULE))
    problems = isolation_problems(root, report, require_native=require_native)
    print(f"checkout: {root}")
    print(f"interpreter: {report['executable']}")
    for name, entry in report["modules"].items():
        print(f"  {name}: {entry.get('file') or entry.get('error')}")
    if problems:
        print("NOT ISOLATED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("isolated: every project package and the native extension come from this checkout")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 tools/setup_worktree.py",
        description="Create or verify this checkout's own .venv and imports.",
    )
    parser.add_argument("--root", type=Path, default=None,
                        help="checkout to set up (default: git top level of the current directory)")
    parser.add_argument("--check", action="store_true", help="verify only; change nothing")
    parser.add_argument("--recreate", action="store_true", help="discard and rebuild .venv")
    parser.add_argument("--node", action="store_true", help="also run npm ci in the checkout")
    parser.add_argument("--allow-no-native", action="store_true",
                        help="accept a checkout without the native extension (no C compiler)")
    args = parser.parse_args(argv)
    root = (args.root.resolve() if args.root else git_root(Path.cwd()))
    if not (root / "pyproject.toml").exists():
        print(f"setup: {root} is not a Mordheim Utils checkout", file=sys.stderr)
        return 2
    if not args.check:
        try:
            setup(root, recreate=args.recreate, node=args.node)
        except SystemExit as error:
            print(error, file=sys.stderr)
            return 2
    try:
        return check(root, require_native=not args.allow_no_native)
    except RuntimeError as error:
        print(f"setup: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover - command entry point
    raise SystemExit(main())
