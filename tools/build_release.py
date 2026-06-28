#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "artlist_scraper.py"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
PACKAGE_NAME = "Stock-Video-Collector"
ARTIFACT = ROOT / "dist" / f"{PACKAGE_NAME}.exe"


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
    if args.verify_only:
        print(f"release metadata ok: v{version}")
        return 0

    clean_outputs()
    build()
    if not ARTIFACT.exists():
        raise RuntimeError(f"PyInstaller did not produce {ARTIFACT}")

    size_mb = ARTIFACT.stat().st_size / (1024 * 1024)
    print(f"built {ARTIFACT}")
    print(f"version v{version}")
    print(f"size {size_mb:.2f} MB")
    print(f"sha256 {sha256(ARTIFACT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
