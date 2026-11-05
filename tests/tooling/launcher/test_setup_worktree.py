"""Worktree isolation: each checkout runs its own venv, packages and native build.

The probe itself is exercised once against the running interpreter; the
decisions are checked on synthetic probe reports, so no venv is created here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools import setup_worktree as setup


def _report(root: Path, *, prefix: Path | None = None, origin: Path | None = None,
            native_error: str | None = None) -> dict:
    base = origin or root
    modules = {name: {"file": str(base / "packages" / name / "__init__.py")}
               for name in setup.PROJECT_MODULES}
    modules[setup.NATIVE_MODULE] = (
        {"error": native_error} if native_error
        else {"file": str(base / "packages" / "_combat_native.so")})
    return {"executable": "python", "prefix": str(prefix or root / ".venv"), "modules": modules}


def test_a_checkout_importing_only_itself_is_isolated(tmp_path):
    assert setup.isolation_problems(tmp_path, _report(tmp_path)) == []


def test_another_checkout_venv_and_imports_are_named(tmp_path):
    other = tmp_path / "main-checkout"
    root = tmp_path / "worktree"
    problems = setup.isolation_problems(root, _report(root, prefix=other / ".venv", origin=other))
    assert problems[0].startswith("interpreter prefix is")
    named = " ".join(problems)
    for module in (*setup.PROJECT_MODULES, setup.NATIVE_MODULE):
        assert f"{module} is imported from" in named
    # CI installs into its own interpreter: only the import origins matter then.
    ci = setup.isolation_problems(root, _report(root, prefix=Path(sys.prefix)),
                                  require_local_venv=False)
    assert ci == []


def test_a_missing_native_extension_fails_unless_allowed(tmp_path):
    report = _report(tmp_path, native_error="ImportError: no compiler")
    assert setup.isolation_problems(tmp_path, report) == [
        f"{setup.NATIVE_MODULE} does not import: ImportError: no compiler"]
    assert setup.isolation_problems(tmp_path, report, require_native=False) == []


def test_probe_ignores_pythonpath_and_the_current_directory(tmp_path, monkeypatch):
    decoy = tmp_path / "decoy"
    (decoy / "mordheim_core").mkdir(parents=True)
    (decoy / "mordheim_core" / "__init__.py").write_text("")
    monkeypatch.setenv("PYTHONPATH", str(decoy))
    monkeypatch.chdir(decoy)
    report = setup.probe(Path(sys.executable), ("mordheim_core",))
    entry = report["modules"]["mordheim_core"]
    assert decoy not in Path(entry.get("file", "/")).parents


def test_check_reports_a_checkout_without_venv(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert setup.main(["--root", str(tmp_path), "--check"]) == 1
    assert "has no .venv" in capsys.readouterr().out


def test_root_defaults_to_the_git_top_level(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "nested").mkdir()
    assert setup.git_root(tmp_path / "nested") == tmp_path.resolve()
    with pytest.raises(SystemExit, match="not inside a git checkout"):
        setup.git_root(Path("/"))
