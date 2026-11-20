import unittest
from unittest.mock import patch

from app import Axis, AxisEditor


class RefactorTests(unittest.TestCase):
    def test_character_copy_template_keeps_only_roles(self):
        source = Axis(
            id="source",
            name="原始軸",
            mode="考試",
            front=[["舊角色"]],
            back=[],
            axis_rows=[{"type": "axis", "time": "1", "c": "2", "items": []}],
            button_items=[{"text": "角色A", "color": "#123456"}],
            url="https://example.com",
            tower_boss="首領",
            armor="裝甲",
            view_note="備註",
            exam_phases={
                "P1": {
                    "axis_rows": [{"type": "axis", "time": "3", "c": "4"}],
                    "button_items": [{"text": "P1角色", "color": "#654321"}],
                    "view_note": "P1備註",
                },
            },
        )

        copied = AxisEditor._character_copy_template(source)

        self.assertEqual(copied.id, "")
        self.assertEqual(copied.name, "")
        self.assertEqual(copied.url, "")
        self.assertEqual(copied.mode, "考試")
        self.assertEqual(copied.axis_rows, [])
        self.assertEqual(copied.view_note, "")
        self.assertEqual(copied.tower_boss, "")
        self.assertEqual(copied.armor, "")
        self.assertEqual(copied.button_items, source.button_items)
        self.assertIsNot(copied.button_items, source.button_items)
        self.assertEqual(copied.exam_phases["P1"]["axis_rows"], [])
        self.assertEqual(
            copied.exam_phases["P1"]["button_items"],
            source.exam_phases["P1"]["button_items"],
        )
        self.assertEqual(copied.exam_phases["P1"]["view_note"], "")

    def test_save_requires_name_and_url(self):
        class ValueStub:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        editor = AxisEditor.__new__(AxisEditor)
        editor.name_var = ValueStub("")
        editor.url_var = ValueStub("")
        editor.mode_var = ValueStub("一般")

        with patch("app.messagebox.showinfo") as showinfo:
            editor.save_axis()

        showinfo.assert_called_once_with(
            "尚未完成", "請輸入名稱（標題）與網址。",
        )

        editor.name_var = ValueStub("測試軸")
        with patch("app.messagebox.showinfo") as showinfo:
            editor.save_axis()

        showinfo.assert_called_once_with("尚未完成", "請輸入網址。")

    def test_persist_axis_replaces_matching_id_without_appending(self):
        original = Axis(id="same", name="old", mode="一般", front=[], back=[])
        untouched = Axis(id="other", name="other", mode="一般", front=[], back=[])
        replacement = Axis(id="same", name="new", mode="一般", front=[], back=[])

        class StoreStub:
            def __init__(self):
                self.axes = [original, untouched]
                self.saved = None

            def load(self):
                return list(self.axes)

            def save(self, axes):
                self.saved = axes

        editor = AxisEditor.__new__(AxisEditor)
        editor.store = StoreStub()
        editor._persist_axis(replacement)

        self.assertEqual([axis.name for axis in editor.store.saved], ["new", "other"])

    def test_normalize_phases_preserves_legacy_fallback_and_copies_lists(self):
        rows = [{"type": "axis", "time": "1.0", "c": "19.9", "items": []}]
        items = [{"text": "A", "color": "#fff"}]
        source = {
            "P1": {"axis_rows": rows, "button_items": items},
            "P2": {"axis_rows": [], "button_items": [], "view_note": 123},
        }

        result = AxisEditor._normalize_phases(source, "legacy")

        self.assertEqual(result["P1"]["view_note"], "legacy")
        self.assertEqual(result["P2"]["view_note"], "123")
        self.assertEqual(result["P1"]["axis_rows"], rows)
        self.assertIsNot(result["P1"]["axis_rows"], rows)
        self.assertIsNot(result["P1"]["button_items"], items)


if __name__ == "__main__":
    unittest.main()
