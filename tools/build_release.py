#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
from importlib import metadata as importlib_metadata
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "artlist_scraper.py"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
LOCK_FILE = ROOT / "requirements-lock.txt"
PACKAGE_NAME = "Stock-Video-Collector"
ARTIFACT = ROOT / "dist" / f"{PACKAGE_NAME}.exe"
RELEASE_METADATA_DIR = ROOT / "build" / "release-verification"
DEPENDENCY_SNAPSHOT = RELEASE_METADATA_DIR / "dependency-snapshot.json"
AUDIT_REPORT = RELEASE_METADATA_DIR / "dependency-audit.json"
AUDIT_CACHE_DIR = RELEASE_METADATA_DIR / f"pip-audit-cache-{os.getpid()}"
CORE_LOCKED_DEPENDENCIES = {
    "imageio-ffmpeg",
    "keyring",
    "pip",
    "pip-audit",
    "playwright",
    "pyinstaller",
    "pyqt6",
    "setuptools",
}


def canonical_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(name).strip()).lower()


def read_app_version() -> str:
    tree = ast.parse(APP_FILE.read_text(encoding="utf-8"), filename=str(APP_FILE))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "APP_VERSION":
                    value = ast.literal_eval(node.value)
                    if isinstance(value, str) and value:
                        return value
    raise RuntimeError("APP_VERSION was not found in artlist_scraper.py")


def verify_version_sync(version: str) -> None:
    errors = []
    readme = README.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else ""
    source = APP_FILE.read_text(encoding="utf-8")

    if f"version-{version}-blue" not in readme:
        errors.append(f"README badge does not match APP_VERSION {version}")
    if f"## [v{version}]" not in changelog:
        errors.append(f"CHANGELOG.md does not contain a v{version} entry")
    if f'APP_VERSION = "{version}"' not in source:
        errors.append("artlist_scraper.py APP_VERSION literal is not synchronized")
    if "setWindowTitle(APP_WINDOW_TITLE)" not in source:
        errors.append("Main window title does not use APP_WINDOW_TITLE")
    if errors:
        raise RuntimeError("\n".join(errors))


def parse_lock_file() -> dict[str, str]:
    if not LOCK_FILE.exists():
        raise RuntimeError(f"{LOCK_FILE.name} is missing; release dependencies are not reproducible")
    pins: dict[str, str] = {}
    errors = []
    for line_no, raw_line in enumerate(LOCK_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") or "==" not in line:
            errors.append(f"{LOCK_FILE.name}:{line_no} must be an exact package==version pin")
            continue
        name, version = line.split("==", 1)
        name = canonical_package_name(name)
        version = version.split(";", 1)[0].strip()
        if not name or not version:
            errors.append(f"{LOCK_FILE.name}:{line_no} has an invalid package pin")
            continue
        pins[name] = version
    missing_core = sorted(CORE_LOCKED_DEPENDENCIES - set(pins))
    if missing_core:
        errors.append(f"{LOCK_FILE.name} is missing core release pins: {', '.join(missing_core)}")
    if not pins:
        errors.append(f"{LOCK_FILE.name} contains no package pins")
    if errors:
        raise RuntimeError("\n".join(errors))
    return pins


def installed_packages() -> dict[str, str]:
    packages = {}
    for dist in importlib_metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            packages[canonical_package_name(name)] = dist.version
    return packages


def verify_dependency_lock() -> dict[str, str]:
    locked = parse_lock_file()
    installed = installed_packages()
    errors = []
    for name, expected in sorted(locked.items()):
        actual = installed.get(name)
        if actual is None:
            errors.append(f"{name}=={expected} is pinned but not installed")
        elif actual != expected:
            errors.append(f"{name} is {actual}, expected locked version {expected}")
    unmanaged = sorted(set(installed) - set(locked))
    if unmanaged:
        errors.append("installed packages not present in requirements-lock.txt: " + ", ".join(unmanaged))
    if errors:
        raise RuntimeError("Release dependency lock mismatch:\n" + "\n".join(errors))
    return locked


def write_dependency_snapshot(version: str, locked: dict[str, str]) -> None:
    RELEASE_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "application": PACKAGE_NAME,
        "version": version,
        "python": sys.version,
        "executable": sys.executable,
        "requirements_lock": {
            "path": str(LOCK_FILE.relative_to(ROOT)),
            "sha256": sha256(LOCK_FILE),
            "package_count": len(locked),
        },
        "packages": [{"name": name, "version": locked[name]} for name in sorted(locked)],
    }
    DEPENDENCY_SNAPSHOT.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def run_dependency_audit() -> None:
    RELEASE_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "--requirement",
        str(LOCK_FILE),
        "--no-deps",
        "--format",
        "json",
        "--output",
        str(AUDIT_REPORT),
        "--cache-dir",
        str(AUDIT_CACHE_DIR),
        "--progress-spinner",
        "off",
        "--timeout",
        "30",
    ]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Dependency audit failed; see {AUDIT_REPORT}") from exc


def verify_release_dependencies(version: str) -> int:
    locked = verify_dependency_lock()
    write_dependency_snapshot(version, locked)
    run_dependency_audit()
    return len(locked)


def remove_within_repo(path: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    root = ROOT.resolve()
    if root not in resolved.parents and resolved != root:
        raise RuntimeError(f"Refusing to remove path outside repo: {resolved}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
    else:
        resolved.unlink()


def clean_outputs() -> None:
    remove_within_repo(ROOT / "dist")
    remove_within_repo(ROOT / "build")
    remove_within_repo(ROOT / f"{PACKAGE_NAME}.spec")


def build() -> None:
    data_sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        PACKAGE_NAME,
        "--icon",
        "icon.ico",
        "--add-data",
        f"icon.png{data_sep}.",
        "--runtime-hook",
        "build_hooks/runtime_hook_mp.py",
        "artlist_scraper.py",
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and build the release EXE.")
    parser.add_argument("--verify-only", action="store_true", help="check version sync without building")
    args = parser.parse_args()

    version = read_app_version()
    verify_version_sync(version)
    if not args.verify_only:
        clean_outputs()
    dependency_count = verify_release_dependencies(version)
    if args.verify_only:
        print(f"release metadata ok: v{version}")
        print(f"dependency lock ok: {dependency_count} packages")
        print(f"dependency audit ok: {AUDIT_REPORT.relative_to(ROOT)}")
        return 0

    build()
    if not ARTIFACT.exists():
        raise RuntimeError(f"PyInstaller did not produce {ARTIFACT}")

    size_mb = ARTIFACT.stat().st_size / (1024 * 1024)
    print(f"built {ARTIFACT}")
    print(f"version v{version}")
    print(f"size {size_mb:.2f} MB")
    print(f"sha256 {sha256(ARTIFACT)}")
    print(f"dependency_snapshot {DEPENDENCY_SNAPSHOT.relative_to(ROOT)}")
    print(f"dependency_audit {AUDIT_REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
