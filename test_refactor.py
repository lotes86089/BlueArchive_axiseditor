import unittest

from app import AxisEditor


class RefactorTests(unittest.TestCase):
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
