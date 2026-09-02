"""Dependencias deliberadas entre las áreas activas."""
from pathlib import Path
import ast
import subprocess
import sys
import os


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src/mordheim_combat_lab"


def imported_modules(area: str) -> set[str]:
    result = set()
    for path in (PACKAGE / area).rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                result.add(node.module)
    return result


def test_domain_does_not_depend_on_project_infrastructure():
    forbidden = ("mordheim_combat_lab.combat", "mordheim_combat_lab.knowledge",
                 "mordheim_combat_lab.ui", "mordheim_combat_lab.verification")
    assert not any(module.startswith(forbidden) for module in imported_modules("domain"))


def test_combat_does_not_load_yaml_or_knowledge_packages():
    imports = imported_modules("combat")
    assert "yaml" not in imports
    assert not any(module.startswith("mordheim_combat_lab.knowledge") for module in imports)


def test_application_and_persistence_have_no_tkinter_dependency():
    assert not any(module.startswith("tkinter") for area in ("application", "persistence")
                   for module in imported_modules(area))


def test_runtime_areas_do_not_import_verification_or_archive():
    for area in ("domain", "knowledge", "construction", "combat", "application", "persistence", "ui"):
        imports = imported_modules(area)
        assert not any(module.startswith(("mordheim_combat_lab.verification", "archive")) for module in imports)


def test_importing_package_is_lazy_about_ui_and_verification():
    command = [sys.executable, "-c", "import sys,mordheim_combat_lab; "
               "assert 'tkinter' not in sys.modules; "
               "assert 'mordheim_combat_lab.verification.audit' not in sys.modules"]
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
