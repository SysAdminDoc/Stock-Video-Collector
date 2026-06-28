import ast
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
BUILD_SCRIPT = ROOT / "tools" / "build_release.py"


def _app_version():
    tree = ast.parse(APP.read_text(encoding="utf-8"), filename=str(APP))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "APP_VERSION":
                return ast.literal_eval(node.value)
    raise AssertionError("APP_VERSION not found")


class ReleaseHygieneTests(unittest.TestCase):
    def test_version_surfaces_are_synchronized(self):
        version = _app_version()
        readme = README.read_text(encoding="utf-8")
        changelog = CHANGELOG.read_text(encoding="utf-8")
        source = APP.read_text(encoding="utf-8")

        self.assertIn(f"version-{version}-blue", readme)
        self.assertIn(f"## [v{version}]", changelog)
        self.assertIn("APP_WINDOW_TITLE", source)
        self.assertIn("setWindowTitle(APP_WINDOW_TITLE)", source)

    def test_release_build_script_verifies_metadata(self):
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "--verify-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"v{_app_version()}", result.stdout)


if __name__ == "__main__":
    unittest.main()
