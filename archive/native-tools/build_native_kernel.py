"""external.build_native_kernel: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from Cython.Build import cythonize
import os as os
from pathlib import Path
from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext
import subprocess as subprocess


ROOT = Path(__file__).resolve().parents[1]


SOURCE = ROOT / "src" / "mordheim_combat_lab" / "_combat_fast.pyx"


def windows_sdk_bin():
    sdk_root = Path(os.environ.get("ProgramFiles(x86)", "")) / "Windows Kits" / "10" / "bin"
    candidates = sorted(
        (path / "x64" for path in sdk_root.iterdir() if path.is_dir()),
        reverse=True,
    ) if sdk_root.is_dir() else ()
    return next((path for path in candidates if (path / "rc.exe").is_file()), None)


class NativeBuildExt(build_ext):
    def build_extensions(self):
        sdk_bin = windows_sdk_bin()
        if sdk_bin is None:
            raise SystemExit("Could not find rc.exe from the 64-bit Windows SDK.")
        if not getattr(self.compiler, "initialized", True):
            self.compiler.initialize()
        # setuptools 80 sometimes omits the SDK from PATH even after vcvars64 loads it.
        if hasattr(self.compiler, "_paths"):
            self.compiler._paths = f"{sdk_bin}{os.pathsep}{self.compiler._paths}"
        # A Python extension does not need a manifest. Prevent link.exe from launching
        # rc.exe on its own, which fails with some older SDK installations.
        if hasattr(self.compiler, "manifest_setup_ldargs"):
            self.compiler.manifest_setup_ldargs = lambda *args: None
            self.compiler.manifest_get_embed_info = lambda *args: None
        super().build_extensions()


def activate_msvc():
    if subprocess.run(
        ["where.exe", "cl.exe"], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0:
        return True
    candidates = (
        Path(os.environ.get("ProgramFiles(x86)", ""))
        / "Microsoft Visual Studio" / "2019" / "Community"
        / "VC" / "Auxiliary" / "Build" / "vcvars64.bat",
        Path(os.environ.get("ProgramFiles", ""))
        / "Microsoft Visual Studio" / "2022" / "BuildTools"
        / "VC" / "Auxiliary" / "Build" / "vcvars64.bat",
    )
    script = next((path for path in candidates if path.is_file()), None)
    if script is None:
        return False
    output = subprocess.check_output(
        f'cmd.exe /d /s /c ""{script}" >nul && set"',
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in output.splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            os.environ[name] = value
    return subprocess.run(
        ["where.exe", "cl.exe"], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def main():
    if not activate_msvc():
        raise SystemExit(
            "64-bit Visual C++ Build Tools are required to compile the kernel."
        )
    extension = Extension(
        "mordheim_combat_lab._combat_fast",
        [str(SOURCE)],
        extra_compile_args=["/O2"],
    )
    distribution = Distribution({
        "ext_modules": cythonize(
            [extension],
            compiler_directives={"language_level": 3},
        )
    })
    command = NativeBuildExt(distribution)
    command.build_lib = str(ROOT / "src")
    command.build_temp = str(ROOT / "build" / "cython")
    command.ensure_finalized()
    command.run()


if __name__ == "__main__":
    main()
