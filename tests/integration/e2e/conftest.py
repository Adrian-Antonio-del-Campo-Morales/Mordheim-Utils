"""Load the local support package despite the hyphenated directory name."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


package_name = "mordheim_modular_e2e"
package_path = Path(__file__).parent
package_spec = spec_from_file_location(
    package_name, package_path / "__init__.py",
    submodule_search_locations=[str(package_path)],
)
if package_name not in sys.modules:
    package = module_from_spec(package_spec)
    sys.modules[package_name] = package
    package_spec.loader.exec_module(package)
