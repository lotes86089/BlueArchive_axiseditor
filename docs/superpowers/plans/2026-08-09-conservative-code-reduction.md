# Conservative Code Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce confirmed dead and duplicate code without changing the GUI, workflow, saved JSON structure, or compatibility behavior.

**Architecture:** Keep the existing single-file Tkinter application structure. Add only two private helpers for duplicated phase normalization and axis persistence, while deleting dead instance state and simplifying one callback construction.

**Tech Stack:** Python standard library, Tkinter, Pillow, `unittest`.

## Global Constraints

- Do not change any Tkinter widget, size, color, spacing, text, placement, or event binding.
- Preserve all legacy JSON fields and fallback behavior.
- Do not change `axes.json`.
- Do not add dependencies.
- Do not merge drag-and-drop or scrolling implementations.

---

### Task 1: Phase normalization helper

**Files:**
- Modify: `app.py:568-601`
- Create: `test_refactor.py`

**Interfaces:**
- Produces: `AxisEditor._normalize_phases(source: dict, legacy_view_note: str) -> dict`
- Consumes: phase dictionaries containing `axis_rows`, `button_items`, and optional `view_note`.

- [ ] **Step 1: Write the failing normalization test**

```python
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m unittest test_refactor.RefactorTests.test_normalize_phases_preserves_legacy_fallback_and_copies_lists -v`

Expected: FAIL because `_normalize_phases` does not exist.

- [ ] **Step 3: Implement the minimal helper and replace both comprehensions**

```python
@staticmethod
def _normalize_phases(source: dict, legacy_view_note: str) -> dict:
    return {
        phase: {
            "axis_rows": list(data.get("axis_rows", [])),
            "button_items": list(data.get("button_items", [])),
            "view_note": str(data.get(
                "view_note", legacy_view_note if phase == "P1" else "",
            )),
        }
        for phase, data in source.items()
    }
```

Use it for both `axis.exam_phases` and `axis.normal_phases`, passing `axis.view_note if axis else ""`.

- [ ] **Step 4: Run the normalization test**

Run: `python -m unittest test_refactor -v`

Expected: PASS.

### Task 2: Shared persistence helper

**Files:**
- Modify: `app.py:1802-1850`
- Modify: `test_refactor.py`

**Interfaces:**
- Produces: `AxisEditor._persist_axis(axis: Axis) -> None`
- Consumes: `self.store.load()` and `self.store.save(axes)`.

- [ ] **Step 1: Add a persistence behavior test**

```python
def test_persist_axis_replaces_matching_id_without_appending(self):
    original = Axis(id="same", name="old", mode="一般")
    untouched = Axis(id="other", name="other", mode="一般")
    replacement = Axis(id="same", name="new", mode="一般")

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
```

Also import `Axis` from `app`.

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m unittest test_refactor.RefactorTests.test_persist_axis_replaces_matching_id_without_appending -v`

Expected: FAIL because `_persist_axis` does not exist.

- [ ] **Step 3: Implement `_persist_axis` and call it from both note-saving methods**

```python
def _persist_axis(self, axis: Axis) -> None:
    axes = self.store.load()
    for index, saved_axis in enumerate(axes):
        if saved_axis.id == axis.id:
            axes[index] = axis
            self.store.save(axes)
            break
```

Replace only the duplicated persistence tails. Preserve note comparison, phase selection, and mutation order.

- [ ] **Step 4: Run all refactor tests**

Run: `python -m unittest test_refactor -v`

Expected: PASS.

### Task 3: Delete dead state and simplify transition callback

**Files:**
- Modify: `app.py:368-372, 568-576, 889-907, 1082-1113, 1249-1258, 1485-1487`

**Interfaces:**
- Preserves: `Axis.back` and serialized `"back": []`.
- Deletes: `self.back_entries`, `self.dragged_axis_row`, and `self.dragged_axis_card`.

- [ ] **Step 1: Remove dead assignments**

Delete all initialization and reset assignments for `self.back_entries`, plus the two unread dragged-item assignments. Change axis creation from the empty comprehension to:

```python
back=[],
```

- [ ] **Step 2: Simplify transition button construction**

Create the label, create `row_data`, then create the X button once with:

```python
command=lambda row=row_data: self.delete_transition_row(row)
```

Remove the child traversal and callback overwrite. Keep every widget option and packing option unchanged.

- [ ] **Step 3: Run static and unit checks**

Run: `python -m py_compile app.py test_refactor.py`

Run: `python -m unittest test_refactor -v`

Expected: both commands succeed.

- [ ] **Step 4: Verify no dead-state references remain**

Run: `rg -n "back_entries|dragged_axis_row|dragged_axis_card" app.py`

Expected: no matches.

### Task 4: GUI and repository verification

**Files:**
- Verify: `app.py`
- Verify unchanged: `axes.json`

**Interfaces:**
- Consumes: the real `AxisEditor` constructor and page builders.
- Produces: no files or persisted data.

- [ ] **Step 1: Run a GUI smoke check without entering the event loop**

Run: `python -c "import app; ui=app.AxisEditor(); ui.update(); ui.show_editor(); ui.update(); ui.show_axes(); ui.update(); ui.destroy(); print('GUI_SMOKE_OK')"`

Expected: prints `GUI_SMOKE_OK` with no Tkinter exception.

- [ ] **Step 2: Confirm user data is untouched**

Run: `git diff -- axes.json`

Expected: no output.

- [ ] **Step 3: Review scope and line reduction**

Run: `git diff --check`

Run: `git diff --stat`

Expected: only `app.py` and `test_refactor.py` implementation changes, with `app.py` net shorter.

- [ ] **Step 4: Commit the verified refactor**

```bash
git add app.py test_refactor.py docs/superpowers/plans/2026-08-09-conservative-code-reduction.md
git commit -m "refactor: reduce duplicate editor code"
```
