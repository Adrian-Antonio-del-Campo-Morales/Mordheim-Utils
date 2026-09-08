"""Deliberate dependencies between the monorepo packages."""
from pathlib import Path
import ast
import subprocess
import sys
import os


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SHARED_PACKAGES = ("mordheim_core", "mordheim_knowledge", "mordheim_construction", "mordheim_combat")
RUNTIME_AREAS = ("application", "persistence", "ui")


def imported_modules(package: str, area: str = "") -> set[str]:
    base = SRC / package / area if area else SRC / package
    result = set()
    for path in base.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                result.add(node.module)
    return result


def test_core_does_not_depend_on_project_infrastructure():
    forbidden = ("mordheim_combat", "mordheim_knowledge",
                 "mordheim_combat_lab.ui", "mordheim_combat_lab.verification")
    assert not any(module.startswith(forbidden) for module in imported_modules("mordheim_core"))


def test_combat_does_not_load_yaml_or_knowledge_packages():
    imports = imported_modules("mordheim_combat")
    assert "yaml" not in imports
    assert not any(module.startswith("mordheim_knowledge") for module in imports)


def test_shared_packages_never_import_the_applications():
    for package in SHARED_PACKAGES:
        imports = imported_modules(package)
        assert not any(module.startswith("mordheim_combat_lab") for module in imports), package


def test_application_and_persistence_have_no_tkinter_dependency():
    assert not any(module.startswith("tkinter") for area in ("application", "persistence")
                   for module in imported_modules("mordheim_combat_lab", area))


def test_runtime_areas_do_not_import_verification_or_archive():
    modules = [imported_modules(package) for package in SHARED_PACKAGES]
    modules += [imported_modules("mordheim_combat_lab", area) for area in RUNTIME_AREAS]
    for imports in modules:
        assert not any(module.startswith(("mordheim_combat_lab.verification", "archive")) for module in imports)


def test_importing_package_is_lazy_about_ui_and_verification():
    command = [sys.executable, "-c", "import sys,mordheim_combat_lab; "
               "assert 'tkinter' not in sys.modules; "
               "assert 'mordheim_combat_lab.verification.audit' not in sys.modules"]
    environment = {**os.environ, "PYTHONPATH": str(SRC)}
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def test_campaign_application_and_persistence_have_no_tkinter_dependency():
    for area in ("application", "persistence"):
        imports = imported_modules("mordheim_campaign", area)
        assert not any(module.startswith("tkinter") for module in imports), area


def test_campaign_domain_stays_pure():
    """The campaign domain imports no UI, no locale singletons, no filesystem.

    Web migration Phase 2: the domain (models, builders, services) is the code
    the web port reuses. It must not depend on Tkinter/``mordheim_ui``, on the
    ``mordheim_knowledge``/``mordheim_ui`` i18n singletons, or on ``pathlib``.
    KB access is injected (builders receive the KnowledgePort); the models
    never import it.
    """
    imports = imported_modules("mordheim_campaign", "domain")
    forbidden = ("tkinter", "mordheim_ui", "pathlib", "mordheim_knowledge")
    assert not any(module.startswith(forbidden) for module in imports), imports


def test_campaign_domain_does_not_import_the_application_layer():
    """Domain modules depend on the application only for typing (TYPE_CHECKING)."""
    for path in (SRC / "mordheim_campaign" / "domain").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
                ("mordheim_campaign.application", "mordheim_campaign.persistence", "mordheim_campaign.ui")
            ):
                # Only allowed inside ``if TYPE_CHECKING:`` blocks.
                assert node.col_offset > 0 or _inside_type_checking(tree, node), (
                    f"{path.name} imports {node.module} at runtime"
                )


def _inside_type_checking(tree: ast.AST, node: ast.AST) -> bool:
    for top in ast.walk(tree):
        if isinstance(top, ast.If) and (
            isinstance(top.test, ast.Name) and top.test.id == "TYPE_CHECKING"
            or isinstance(top.test, ast.Attribute) and top.test.attr == "TYPE_CHECKING"
        ):
            if any(child is node for child in ast.walk(top)):
                return True
    return False


def test_campaign_ui_reads_kb_only_through_application():
    imports = imported_modules("mordheim_campaign", "ui")
    assert not any(module.startswith(("mordheim_knowledge", "mordheim_construction", "yaml")) for module in imports)


def test_campaign_application_never_imports_ui():
    for area in ("application", "persistence"):
        imports = imported_modules("mordheim_campaign", area)
        assert not any(module.startswith(("mordheim_campaign.ui", "tkinter")) for module in imports), area
