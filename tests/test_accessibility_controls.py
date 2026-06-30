import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

import artlist_scraper as app


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"
README = ROOT / "README.md"


class AccessibilityStaticTests(unittest.TestCase):
    def test_hidden_shortcut_bindings_are_not_registered(self):
        source = APP.read_text(encoding="utf-8")
        self.assertNotIn("Q" + "Shortcut(", source)
        self.assertNotIn("Q" + "KeySequence(", source)
        self.assertNotIn("Keyboard " + "Shortcut", source)

    def test_readme_no_longer_documents_keyboard_shortcuts(self):
        readme = README.read_text(encoding="utf-8")
        self.assertNotIn("Keyboard " + "Shortcuts", readme)
        self.assertIn("Accessibility metadata", readme)

    def test_visible_selection_controls_and_focus_order_are_wired(self):
        source = APP.read_text(encoding="utf-8")
        self.assertIn("btn_select_visible", source)
        self.assertIn("btn_clear_selection", source)
        self.assertIn("self.tabs.currentIndex() != 2", source)
        self.assertIn("_apply_accessibility_metadata", source)
        self.assertIn("QWidget.setTabOrder", source)


class AccessibilityWidgetSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    def test_clip_card_exposes_readable_metadata(self):
        row = {
            "clip_id": "clip-1",
            "title": "Sunset Harbor",
            "source_site": "Pexels",
            "resolution": "1920x1080",
            "duration": "12s",
            "dl_status": "done",
            "favorited": 1,
            "user_rating": 4,
            "tags": "sunset, harbor",
        }
        card = app.ClipCard(row)
        try:
            self.assertEqual(card.focusPolicy(), Qt.FocusPolicy.StrongFocus)
            self.assertIn("Clip card Sunset Harbor", card.accessibleName())
            self.assertIn("source Pexels", card.accessibleDescription())
            self.assertIn("status done", card.accessibleDescription())
            self.assertTrue(any(lbl.text() == "Done" for lbl in card.findChildren(QLabel)))
        finally:
            card.deleteLater()

    def test_toast_exposes_status_message(self):
        parent = QWidget()
        parent.resize(640, 360)
        toast = app.ToastNotification(parent, "Archive verified", level="success", duration=50)
        try:
            self.assertIn("success notification", toast.accessibleName())
            self.assertIn("Archive verified", toast.accessibleDescription())
        finally:
            toast.deleteLater()
            parent.deleteLater()


if __name__ == "__main__":
    unittest.main()
