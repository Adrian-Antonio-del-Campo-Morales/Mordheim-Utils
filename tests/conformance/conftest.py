"""Register the suite's support modules under the stable name ``mordheim_conformance``.

The modules import each other through that package name, so they never depend
on pytest's rootdir or on generic top-level names such as ``dice`` or ``runner``.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


package_name = "mordheim_conformance"
package_path = Path(__file__).parent
package_spec = spec_from_file_location(
    package_name, package_path / "__init__.py",
    submodule_search_locations=[str(package_path)],
)
if package_name not in sys.modules:
    package = module_from_spec(package_spec)
    sys.modules[package_name] = package
    package_spec.loader.exec_module(package)
