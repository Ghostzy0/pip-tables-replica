"""Build an unsigned/ad-hoc-signed macOS arm64 app. Never downloads at runtime."""
import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("edition", nargs="?", choices=["replica"], default="replica")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise SystemExit("This package recipe is verified only for macOS arm64.")
    plus = False
    name = "Tables Replica"
    entry = "launch.py"
    identity = "tables-replica"
    licenses = root / "licenses"
    if not licenses.is_dir():
        raise SystemExit("Dependency licence copies are required before packaging.")
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
               "--name", name, "--osx-bundle-identifier", "io.github.ghostzy0." + identity,
               "--target-arch", "arm64", "--add-data", str(licenses) + ":licenses",
               "--add-data", str(root / "THIRD-PARTY-NOTICES.md") + ":.",
               "--exclude-module", "PySide6.QtQml", "--exclude-module", "PySide6.QtNetwork",
               "--exclude-module", "tkinter", "--exclude-module", "pytest", entry]
    environment = {**os.environ, "PYINSTALLER_CONFIG_DIR": str(root / "build" / "cache")}
    subprocess.run(command, cwd=root, env=environment, check=True)
    bundle = root / "dist" / (name + ".app")
    import plistlib
    info = bundle / "Contents" / "Info.plist"
    values = plistlib.loads(info.read_bytes())
    values.update(CFBundleShortVersionString="0.2.0" if plus else "0.1.0", CFBundleVersion="2" if plus else "1", NSHighResolutionCapable=True,
                  LSMinimumSystemVersion="13.0", NSHumanReadableCopyright="Copyright 2026 Tables Replica contributors. MIT application; LGPLv3 Qt libraries.")
    info.write_bytes(plistlib.dumps(values))
    # Only the declared runtime closure, never arbitrary developer packages.
    runtime_names = ["duckdb", "PySide6-Essentials", "shiboken6", "openpyxl", "et-xmlfile", "defusedxml"]
    native = {}
    for file in sorted((bundle / "Contents").rglob("*")):
        if file.is_file() and not file.is_symlink():
            with file.open("rb") as stream:
                magic = stream.read(4)
            if magic in {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe"}:
                dependencies = subprocess.check_output(["otool", "-L", str(file)], text=True).splitlines()[1:]
                native[str(file.relative_to(bundle))] = [line.strip() for line in dependencies]
    inventory = {"scope": "declared runtime Python distributions and actual bundled Mach-O load commands; build tools are pinned separately in requirements-lock.txt",
                 "runtime_distributions": {name: importlib.metadata.version(name) for name in runtime_names},
                 "Python": platform.python_version(), "native_artifacts": native,
                 "variant": args.edition}
    (bundle / "Contents" / "Resources" / "dependency-inventory.json").write_text(json.dumps(inventory, indent=2)+"\n")
    # Info.plist/resources changed after bundling; re-sign only our own bundle.
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(bundle)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)], check=True)
    print(bundle)


if __name__ == "__main__":
    main()
