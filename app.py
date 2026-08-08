from __future__ import annotations

import json
import ctypes
import sys
import tkinter as tk
import webbrowser
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk
from uuid import uuid4

from PIL import Image, ImageFilter, ImageTk


APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
DATA_FILE = APP_DIR / "axes.json"
RESOURCE_DIR = (
    Path(getattr(sys, "_MEIPASS"))
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    else Path(__file__).resolve().parent
)
HOME_BACKGROUND = RESOURCE_DIR / "assets" / "home_background.png"
APP_ICON = RESOURCE_DIR / "assets" / "app_icon.ico"
SAVED_AXES_GIF = RESOURCE_DIR / "assets" / "saved_axes_corner.gif"
SAVED_AXES_SIDE_GIF = RESOURCE_DIR / "assets" / "saved_axes_side.gif"
NORMAL_RANK_ICON = RESOURCE_DIR / "assets" / "normal_rank_icon.png"
EXAM_FILTER_ICON = RESOURCE_DIR / "assets" / "exam_filter_icon.png"
TOWER_FILTER_ICON = RESOURCE_DIR / "assets" / "tower_filter_icon.png"
NAV_LOGO = RESOURCE_DIR / "assets" / "nav_logo.png"
HOME_CREATE_ICON = RESOURCE_DIR / "assets" / "home_create_icon.png"
HOME_VIEW_ICON = RESOURCE_DIR / "assets" / "home_view_icon.png"

COLORS = {
    "bg": "#eef7fb",
    "panel": "#ffffff",
    "nav": "#17466b",
    "primary": "#2b83c6",
    "primary_hover": "#1f6fae",
    "text": "#17324a",
    "muted": "#6d8293",
    "border": "#cfe1eb",
    "danger": "#d95763",
    "tag": "#e1f2fb",
}


def mode_display_name(mode: str) -> str:
    return "總力戰" if mode == "一般" else mode


@dataclass
class Axis:
    id: str
    name: str
    mode: str
    front: list[list[str]]
    back: list[list[str]]
    c_text: str = ""
    time_text: str = ""
    c_items: list[str] = field(default_factory=list)
    time_items: list[str] = field(default_factory=list)
    axis_rows: list[dict] = field(default_factory=list)
    button_items: list[dict] = field(default_factory=list)
    url: str = ""
    tower_boss: str = ""
    armor: str = ""
    view_note: str = ""
    exam_phases: dict[str, dict] = field(default_factory=dict)
    normal_phases: dict[str, dict] = field(default_factory=dict)


class AxisStore:
    def load(self) -> list[Axis]:
        if not DATA_FILE.exists():
            return []
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return [Axis(**item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError):
            messagebox.showwarning("資料讀取失敗", "axes.json 格式異常，暫時以空白資料開啟。")
            return []

    def save(self, axes: list[Axis]) -> None:
        DATA_FILE.write_text(
            json.dumps([asdict(axis) for axis in axes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class PillEntry(tk.Frame):
    """Short text input that turns submitted text into removable buttons."""

    def __init__(
        self, master: tk.Misc, title: str, values: list[str] | None = None,
        on_drag=None, get_color=None,
    ):
        super().__init__(master, bg=COLORS["panel"])
        self.values: list[dict] = []
        self.tag_widgets: list[tk.Frame] = []
        self.on_drag = on_drag
        self.get_color = get_color or (lambda: COLORS["tag"])
        tk.Label(
            self, text=title, bg=COLORS["panel"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(anchor="w")

        input_row = tk.Frame(self, bg=COLORS["panel"])
        input_row.pack(anchor="w", pady=(5, 8))
        self.variable = tk.StringVar()
        entry = ttk.Entry(input_row, textvariable=self.variable, width=6)
        entry.pack(side="left")
        entry.bind("<Return>", lambda _event: self.add_value())
        self.palette_button = tk.Button(
            input_row, text="🎨", command=self.choose_color, cursor="hand2",
            bg=COLORS["tag"], activebackground=COLORS["tag"], relief="flat",
            padx=8, pady=4, font=("Segoe UI Emoji", 10),
        )
        self.palette_button.pack(side="left", padx=(7, 0))
        self.add_button = tk.Button(
            input_row, text="新增", command=self.add_value, cursor="hand2",
            bg=COLORS["primary"], fg="white", activebackground=COLORS["primary_hover"],
            activeforeground="white", relief="flat", padx=13, pady=4,
            font=("Microsoft JhengHei UI", 9, "bold"),
        )
        self.add_button.pack(side="left", padx=(5, 0))

        self.tags = tk.Frame(self, bg=COLORS["panel"])
        self.tags.pack(fill="x", anchor="w")
        self.tags.bind("<Configure>", self._reflow_tags)
        for value in values or []:
            self._append(value)

    def choose_color(self) -> None:
        initial = self.get_color()
        color = colorchooser.askcolor(initialcolor=initial, title="選擇按鈕顏色")[1]
        if color:
            self.selected_color = color
            self.palette_button.configure(bg=color, activebackground=color)

    def add_value(self) -> None:
        value = self.variable.get().strip()
        if value:
            self._append({"text": value, "color": getattr(self, "selected_color", self.get_color())})
            self.variable.set("")

    def _append(self, value) -> None:
        item = value if isinstance(value, dict) else {"text": str(value), "color": COLORS["tag"]}
        item = {"text": str(item.get("text", "")), "color": item.get("color", COLORS["tag"])}
        self.values.append(item)
        color = item["color"]
        tag = tk.Frame(self.tags, bg=color, highlightthickness=1,
                       highlightbackground=COLORS["border"])
        self.tag_widgets.append(tag)
        label = tk.Label(tag, text=item["text"], bg=color, fg=COLORS["text"],
                         anchor="w", padx=8, pady=4, cursor="hand2")
        label.pack(side="left")
        tk.Button(
            tag, text="×", command=lambda: self._remove(item, tag), cursor="hand2",
            bg=color, fg=COLORS["danger"], activebackground="#f9dfe2",
            relief="flat", font=("Arial", 12, "bold"), padx=8,
        ).pack(side="right")
        if self.on_drag:
            for widget in (tag, label):
                widget.bind("<ButtonPress-1>", lambda e, v=item: self.on_drag(e, v))
        self.after_idle(self._reflow_tags)

    def _remove(self, value: dict, widget: tk.Widget) -> None:
        self.values.remove(value)
        self.tag_widgets.remove(widget)
        widget.destroy()
        self.after_idle(self._reflow_tags)

    def _reflow_tags(self, _event=None) -> None:
        """Lay tags out in rows so every item remains reachable at narrow widths."""
        available = max(1, self.tags.winfo_width())
        x = y = 0
        row_height = 0
        for widget in self.tag_widgets:
            width = max(1, widget.winfo_reqwidth())
            height = max(1, widget.winfo_reqheight())
            if x and x + width > available:
                x = 0
                y += row_height + 4
                row_height = 0
            widget.grid_forget()
            widget.place(x=x, y=y)
            x += width + 7
            row_height = max(row_height, height)
        self.tags.configure(height=y + row_height if self.tag_widgets else 1)

    def get_values(self) -> list[str]:
        pending = self.variable.get().strip()
        return [item["text"] for item in self.values] + ([pending] if pending else [])

    def get_items(self) -> list[dict]:
        items = [dict(item) for item in self.values]
        pending = self.variable.get().strip()
        if pending:
            items.append({"text": pending, "color": getattr(self, "selected_color", self.get_color())})
        return items


class AutoWrapText(tk.Text):
    """Compact wrapped note field that grows with its content."""

    def __init__(
        self, master: tk.Misc, value: str = "", width: int = 18,
        max_lines: int = 4, on_height_change=None,
    ):
        super().__init__(
            master, width=width, height=1, wrap="word", undo=True,
            bg="white", fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="solid", borderwidth=1, highlightthickness=0,
            font=("Microsoft JhengHei UI", 9), padx=5, pady=3,
        )
        self.wrap_width = width
        self.max_lines = max_lines
        self.on_height_change = on_height_change
        self.insert("1.0", value)
        self.bind("<KeyRelease>", self.adjust_height, add="+")
        self.after_idle(self.adjust_height)

    def get_text(self) -> str:
        return self.get("1.0", "end-1c")

    def adjust_height(self, _event=None) -> None:
        lines = 0
        for logical_line in self.get_text().split("\n"):
            lines += max(1, (len(logical_line) + self.wrap_width - 1) // self.wrap_width)
        desired = min(self.max_lines, max(1, lines))
        if int(self.cget("height")) != desired:
            self.configure(height=desired)
        if self.on_height_change:
            self.on_height_change(desired)


class DropZone(tk.Frame):
    def __init__(self, master: tk.Misc, values: list[str] | None = None):
        super().__init__(
            master, bg="#f7fbfd", width=410, height=48,
            highlightthickness=2, highlightbackground=COLORS["border"],
        )
        self.pack_propagate(False)
        self.values: list[dict] = []
        self.items = tk.Frame(self, bg="#f7fbfd")
        self.items.pack(fill="both", expand=True, padx=5, pady=5)
        self.hint = tk.Label(
            self.items, text="拖曳項目到這裡", bg="#f7fbfd", fg=COLORS["muted"],
            font=("Microsoft JhengHei UI", 9),
        )
        self.hint.pack(side="left", padx=8)
        for value in values or []:
            self.add(value)

    def add(self, value) -> None:
        entry = value if isinstance(value, dict) else {"text": str(value), "color": COLORS["tag"]}
        entry = {"text": str(entry.get("text", "")), "color": entry.get("color", COLORS["tag"])}
        if not self.values:
            self.hint.pack_forget()
        self.values.append(entry)
        color = entry["color"]
        item = tk.Frame(self.items, bg=color, highlightthickness=1,
                        highlightbackground=COLORS["border"])
        item.pack(side="left", padx=3)
        tk.Label(item, text=entry["text"], bg=color, fg=COLORS["text"],
                 padx=7, pady=3).pack(side="left")
        tk.Button(
            item, text="×", command=lambda: self.remove(entry, item), cursor="hand2",
            bg=color, fg=COLORS["danger"], activebackground="#f9dfe2",
            relief="flat", font=("Arial", 11, "bold"), padx=6,
        ).pack(side="right")

    def remove(self, value: dict, widget: tk.Widget) -> None:
        self.values.remove(value)
        widget.destroy()
        if not self.values:
            self.hint.pack(side="left", padx=8)

    def contains(self, root_x: int, root_y: int) -> bool:
        return (
            self.winfo_rootx() <= root_x <= self.winfo_rootx() + self.winfo_width()
            and self.winfo_rooty() <= root_y <= self.winfo_rooty() + self.winfo_height()
        )


class ScrollFrame(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=COLORS["bg"])
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self.canvas = canvas
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = tk.Frame(canvas, bg=COLORS["bg"])
        window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Enter>", lambda _e: canvas.bind_all(
            "<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))


class AnimatedGifLabel(tk.Label):
    """A self-contained animated GIF label that stops cleanly when destroyed."""

    def __init__(self, master: tk.Misc, path: Path, max_width: int = 220):
        super().__init__(master, bg=COLORS["bg"], borderwidth=0)
        self.source = Image.open(path)
        self.frame_count = getattr(self.source, "n_frames", 1)
        self.frame_index = 0
        self.after_id: str | None = None
        scale = min(1.0, max_width / self.source.width)
        self.image_size = (
            max(1, round(self.source.width * scale)),
            max(1, round(self.source.height * scale)),
        )
        delay = self.load_frame(0)
        self.after_id = self.after(delay, self.show_next_frame)
        self.bind("<Destroy>", self.stop_animation, add="+")

    def load_frame(self, index: int) -> int:
        self.source.seek(index)
        image = self.source.convert("RGBA")
        if image.size != self.image_size:
            image = image.resize(self.image_size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        self.configure(image=self.photo)
        return max(20, int(self.source.info.get("duration", 100)))

    def show_next_frame(self) -> None:
        if not self.winfo_exists():
            return
        self.frame_index = (self.frame_index + 1) % self.frame_count
        delay = self.load_frame(self.frame_index)
        self.after_id = self.after(delay, self.show_next_frame)

    def stop_animation(self, _event=None) -> None:
        if self.after_id:
            try:
                self.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        if getattr(self, "source", None):
            self.source.close()
            self.source = None


class AxisEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blue Archive 軸編輯器")
        try:
            self.iconbitmap(default=str(APP_ICON))
        except tk.TclError:
            pass
        self.geometry("1040x760")
        self.minsize(850, 620)
        self.configure(bg=COLORS["bg"])
        self.store = AxisStore()
        self.editing_id: str | None = None
        self.front_entries: list[PillEntry] = []
        self.back_entries: list[PillEntry] = []
        self.drop_zones: list[DropZone] = []
        self.c_vars: list[tk.StringVar] = []
        self.time_vars: list[tk.StringVar] = []
        self.axis_layout: list[dict] = []
        self.decimal_entries: set[tk.Widget] = set()
        self._decimal_key_down = False
        self.drag_window: tk.Toplevel | None = None
        self._configure_style()
        self.show_home()
        self.decimal_poll_after_id = self.after(10, self.poll_keypad_decimal)
        self.bind("<Destroy>", self.stop_decimal_poll, add="+")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TEntry", fieldbackground="white", bordercolor=COLORS["border"],
                        lightcolor=COLORS["border"], darkcolor=COLORS["border"], padding=7)

    def choice_checkbox(self, master: tk.Misc, **kwargs) -> tk.Checkbutton:
        """Button-style checkbox without the platform's X-shaped indicator."""
        return tk.Checkbutton(
            master,
            indicatoron=False,
            bg="#e7f2f8",
            fg=COLORS["text"],
            selectcolor="#79b9e4",
            activebackground="#cce7f5",
            activeforeground=COLORS["text"],
            relief="flat",
            overrelief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=13,
            pady=7,
            cursor="hand2",
            font=("Microsoft JhengHei UI", 11, "bold"),
            **kwargs,
        )

    def clear_window(self) -> None:
        self.decimal_entries.clear()
        for widget in self.winfo_children():
            widget.destroy()

    def nav(self, active: str = "") -> None:
        bar = tk.Frame(self, bg=COLORS["nav"], height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        if NAV_LOGO.exists():
            with Image.open(NAV_LOGO) as source:
                logo = source.convert("RGBA")
            alpha_box = logo.getchannel("A").getbbox()
            if alpha_box:
                logo = logo.crop(alpha_box)
            outline_width = 1
            target_height = 46 - outline_width * 2
            target_width = max(1, round(logo.width * target_height / logo.height))
            logo = logo.resize(
                (target_width, target_height), Image.Resampling.LANCZOS,
            )
            outlined_logo = Image.new(
                "RGBA",
                (target_width + outline_width * 2,
                 target_height + outline_width * 2),
                (0, 0, 0, 0),
            )
            padded_alpha = Image.new("L", outlined_logo.size, 0)
            padded_alpha.paste(
                logo.getchannel("A"), (outline_width, outline_width),
            )
            expanded_alpha = padded_alpha.filter(
                ImageFilter.MaxFilter(outline_width * 2 + 1),
            )
            white_outline = Image.new(
                "RGBA", outlined_logo.size, (255, 255, 255, 255),
            )
            white_outline.putalpha(expanded_alpha)
            outlined_logo.alpha_composite(white_outline)
            outlined_logo.alpha_composite(
                logo, (outline_width, outline_width),
            )
            self.nav_logo_image = ImageTk.PhotoImage(outlined_logo)
            tk.Label(
                bar, image=self.nav_logo_image, bg=COLORS["nav"], borderwidth=0,
            ).pack(side="left", padx=28)
        else:
            tk.Label(
                bar, text="BLUE ARCHIVE", bg=COLORS["nav"], fg="white",
                font=("Microsoft JhengHei UI", 16, "bold"),
            ).pack(side="left", padx=28)
        buttons = tk.Frame(bar, bg=COLORS["nav"])
        buttons.pack(side="right", padx=(0, 20))
        for text, command in (("首頁", self.show_home), ("看軸", self.show_list), ("新建立", self.show_editor)):
            tk.Button(
                buttons, text=text, command=command, cursor="hand2",
                bg=COLORS["primary"] if active == text else COLORS["nav"],
                fg="white", activebackground=COLORS["primary"], activeforeground="white",
                relief="flat", padx=18, pady=9, font=("Microsoft JhengHei UI", 10, "bold"),
            ).pack(side="left", padx=(0, 8))

    def show_home(self) -> None:
        self.clear_window()
        self.home_button_images = []
        self.nav("首頁")
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        try:
            self.home_source_image = Image.open(HOME_BACKGROUND).convert("RGB")
            self.home_background = ImageTk.PhotoImage(self.home_source_image)
            self.home_background_width = None
            background = canvas.create_image(
                0, 0, image=self.home_background, anchor="center",
            )
            canvas.bind(
                "<Configure>",
                lambda event: self.resize_home_background(
                    canvas, background, event.width, event.height,
                ),
            )
        except (OSError, tk.TclError):
            self.home_source_image = None
            self.home_background = None

        create_card = self.big_button(
            canvas, "＋  新建立", "建立總力戰/考試/爬塔隊伍軸",
            self.show_editor, HOME_CREATE_ICON,
        )
        view_card = self.big_button(
            canvas, "☰  看軸", "查看、編輯或刪除已儲存的軸",
            self.show_list, HOME_VIEW_ICON,
        )
        create_window = canvas.create_window(0, 0, window=create_card, anchor="center")
        view_window = canvas.create_window(0, 0, window=view_card, anchor="center")
        canvas.bind(
            "<Configure>",
            lambda event: self.position_home_content(
                canvas, create_window, view_window, event.width, event.height,
            ),
            add="+",
        )

    def resize_home_background(
        self, canvas: tk.Canvas, image_item: int, width: int, height: int,
    ) -> None:
        if not self.home_source_image or width < 2:
            return
        canvas.coords(image_item, width / 2, height / 2)
        if getattr(self, "home_background_width", None) == width:
            return
        source_width, source_height = self.home_source_image.size
        scaled_height = max(1, round(source_height * width / source_width))
        resized = self.home_source_image.resize(
            (width, scaled_height), Image.Resampling.LANCZOS,
        )
        self.home_background = ImageTk.PhotoImage(resized)
        self.home_background_width = width
        canvas.itemconfigure(image_item, image=self.home_background)

    def position_home_content(
        self, canvas: tk.Canvas, create_card: int, view_card: int,
        width: int, height: int,
    ) -> None:
        center_x, center_y = width / 2, height / 2
        canvas.coords(create_card, center_x - 160, center_y)
        canvas.coords(view_card, center_x + 160, center_y)

    def big_button(
        self, master: tk.Misc, title: str, subtitle: str, command,
        image_path: Path | None = None,
    ) -> tk.Frame:
        card = tk.Frame(master, bg=COLORS["panel"], highlightthickness=1,
                        highlightbackground=COLORS["border"], width=300, height=150)
        card.pack_propagate(False)
        button = tk.Button(
            card, text=title, command=command, cursor="hand2", relief="flat",
            bg=COLORS["panel"], fg=COLORS["primary"], activebackground="#edf7fc",
            font=("Microsoft JhengHei UI", 16, "bold"),
        )
        if image_path and image_path.exists():
            with Image.open(image_path) as source:
                icon = source.convert("RGBA")
            alpha_box = icon.getchannel("A").getbbox()
            if alpha_box:
                icon = icon.crop(alpha_box)
            target_height = 26
            target_width = max(1, round(icon.width * target_height / icon.height))
            icon = icon.resize(
                (target_width, target_height), Image.Resampling.LANCZOS,
            )
            photo = ImageTk.PhotoImage(icon)
            self.home_button_images.append(photo)
            button.configure(image=photo, compound="right", padx=8)
        button.pack(fill="both", expand=True)
        tk.Label(card, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"],
                 font=("Microsoft JhengHei UI", 9)).pack(pady=(0, 18))
        return card

    def show_editor(self, axis: Axis | None = None) -> None:
        self.clear_window()
        # Widgets from the previous editor page have been destroyed by clear_window,
        # so their cached references must also be reset before mode selection.
        self.front_entries = []
        self.back_entries = []
        self.drop_zones = []
        self.c_vars = []
        self.time_vars = []
        self.axis_layout = []
        self.nav("新建立")
        self.editing_id = axis.id if axis else None
        self.view_note_value = axis.view_note if axis else ""
        self.exam_phases = {
            phase: {
                "axis_rows": list(data.get("axis_rows", [])),
                "button_items": list(data.get("button_items", [])),
                "view_note": str(data.get(
                    "view_note", axis.view_note if axis and phase == "P1" else "",
                )),
            }
            for phase, data in (axis.exam_phases if axis else {}).items()
        }
        self.normal_phases = {
            phase: {
                "axis_rows": list(data.get("axis_rows", [])),
                "button_items": list(data.get("button_items", [])),
                "view_note": str(data.get(
                    "view_note", axis.view_note if axis and phase == "P1" else "",
                )),
            }
            for phase, data in (axis.normal_phases if axis else {}).items()
        }
        self.normal_phases_enabled = bool(self.normal_phases)
        self.current_exam_phase = "P1"
        scroll = ScrollFrame(self)
        scroll.pack(fill="both", expand=True)
        panel = tk.Frame(scroll.body, bg=COLORS["panel"], highlightthickness=1,
                         highlightbackground=COLORS["border"])
        panel.pack(fill="x", padx=55, pady=32)
        tk.Label(panel, text="編輯軸" if axis else "新建立軸", bg=COLORS["panel"],
                 fg=COLORS["text"], font=("Microsoft JhengHei UI", 22, "bold")).pack(
                     anchor="w", padx=30, pady=(25, 18))

        meta = tk.Frame(panel, bg=COLORS["panel"])
        meta.pack(fill="x", padx=30)
        tk.Label(meta, text="名稱", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Microsoft JhengHei UI", 10, "bold")).pack(anchor="w")
        self.name_var = tk.StringVar(value=axis.name if axis else "")
        ttk.Entry(meta, textvariable=self.name_var).pack(fill="x", pady=(5, 15))
        tk.Label(meta, text="網址", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Microsoft JhengHei UI", 10, "bold")).pack(anchor="w")
        self.url_var = tk.StringVar(value=axis.url if axis else "")
        ttk.Entry(meta, textvariable=self.url_var).pack(fill="x", pady=(5, 15))
        tk.Label(meta, text="類型（擇一）", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Microsoft JhengHei UI", 10, "bold")).pack(anchor="w")
        self.mode_var = tk.StringVar(value=axis.mode if axis else "")
        self.boss_var = tk.StringVar(value=axis.tower_boss if axis else "")
        self.armor_var = tk.StringVar(value=axis.armor if axis else "")
        choices = tk.Frame(meta, bg=COLORS["panel"])
        choices.pack(fill="x", pady=(5, 15))
        for text, value in (("總力戰", "一般"), ("考試", "考試"), ("爬塔", "爬塔")):
            self.choice_checkbox(
                choices, text=text, variable=self.mode_var, onvalue=value, offvalue="",
                command=self._mode_changed,
            ).pack(side="left", padx=(0, 24))
        self.tower_options = tk.Frame(meta, bg=COLORS["panel"])
        self.tower_options.pack(fill="x", pady=(0, 12))
        if self.mode_var.get() == "爬塔":
            self.build_tower_options()
        else:
            self.tower_options.pack_forget()

        self.exam_phase_bar = tk.Frame(panel, bg=COLORS["panel"])
        self.fields = tk.Frame(panel, bg=COLORS["panel"])
        self.fields.pack(fill="x", padx=30)
        if self.mode_var.get() == "考試":
            self.build_exam_phase_buttons()
        elif self.mode_var.get() == "一般":
            self.build_normal_phase_buttons()
        if axis:
            if axis.mode == "考試":
                phase_data = self.exam_phases.get("P1", {})
                self._build_fields(
                    axis.front, axis.back,
                    phase_data.get("axis_rows"), phase_data.get("button_items"),
                )
            elif axis.mode == "一般" and self.normal_phases_enabled:
                phase_data = self.normal_phases.get("P1", {})
                self._build_fields(
                    axis_rows=phase_data.get("axis_rows"),
                    button_items=phase_data.get("button_items"),
                )
            else:
                rows = axis.axis_rows or [{
                    "c": axis.c_text,
                    "time": axis.time_text,
                    "items": list(axis.c_items) + list(axis.time_items),
                }]
                self._build_fields(axis.front, axis.back, rows, axis.button_items)

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x", padx=30, pady=28)
        self.action_button(actions, "＋", self.add_axis_row_safe, COLORS["primary"]).pack(
            side="left")
        self.action_button(actions, "＋轉場", self.add_transition_row_safe,
                           COLORS["danger"]).pack(side="left", padx=(7, 0))
        self.action_button(actions, "儲存", self.save_axis, COLORS["primary"]).pack(
            side="left", padx=(18, 0))
        self.action_button(actions, "清空", self.clear_axis_rows, "#8296a5").pack(
            side="left", padx=(7, 0))
        self.action_button(actions, "返回", self.show_list, "#5f7180").pack(
            side="left", padx=(7, 0))

    def _mode_changed(self) -> None:
        if self.mode_var.get() == "爬塔":
            self.tower_options.pack(fill="x", pady=(0, 12))
            self.build_tower_options()
        else:
            self.boss_var.set("")
            self.armor_var.set("")
            for child in self.tower_options.winfo_children():
                child.destroy()
            self.tower_options.pack_forget()
        if self.mode_var.get() == "考試":
            self.current_exam_phase = "P1"
            self.build_exam_phase_buttons()
        elif self.mode_var.get() == "一般":
            self.current_exam_phase = "P1"
            self.build_normal_phase_buttons()
        else:
            self.exam_phase_bar.pack_forget()
        if self.mode_var.get() and not self.front_entries:
            self._build_fields()

    def build_exam_phase_buttons(self) -> None:
        self.exam_phase_bar.pack(fill="x", padx=30, pady=(0, 12), before=self.fields)
        for child in self.exam_phase_bar.winfo_children():
            child.destroy()
        tk.Label(
            self.exam_phase_bar, text="子軸：", bg=COLORS["panel"],
            fg=COLORS["text"], font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left")
        for phase in ("P1", "P2", "P3"):
            selected = phase == self.current_exam_phase
            self.action_button(
                self.exam_phase_bar, phase,
                lambda value=phase: self.switch_exam_phase(value),
                COLORS["primary"] if selected else "#8296a5",
            ).pack(side="left", padx=(5, 0))

    def build_normal_phase_buttons(self) -> None:
        self.exam_phase_bar.pack(fill="x", padx=30, pady=(0, 12), before=self.fields)
        for child in self.exam_phase_bar.winfo_children():
            child.destroy()
        tk.Label(
            self.exam_phase_bar, text="子軸：", bg=COLORS["panel"],
            fg=COLORS["text"], font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left")
        if self.normal_phases_enabled:
            for phase in ("P1", "P2", "P3", "P4"):
                if phase not in self.normal_phases:
                    continue
                phase_group = tk.Frame(self.exam_phase_bar, bg=COLORS["panel"])
                phase_group.pack(side="left", padx=(5, 0))
                self.action_button(
                    phase_group, phase,
                    lambda value=phase: self.switch_exam_phase(value),
                    COLORS["primary"] if phase == self.current_exam_phase else "#8296a5",
                ).pack(side="left")
                if phase != "P1":
                    tk.Button(
                        phase_group, text="X",
                        command=lambda value=phase: self.delete_normal_phase(value),
                        cursor="hand2", bg=COLORS["danger"], fg="white",
                        activebackground="#bd3e4a", activeforeground="white",
                        relief="flat", padx=7, pady=7,
                        font=("Arial", 9, "bold"),
                    ).pack(side="left")
        self.action_button(
            self.exam_phase_bar, "＋子軸", self.add_normal_phase, "#3a9b84",
        ).pack(side="left", padx=(8, 0))

    def add_normal_phase(self) -> None:
        if not self.front_entries:
            self._build_fields()
        if not self.normal_phases_enabled:
            self.normal_phases_enabled = True
            self.store_current_editor_phase(self.normal_phases)
            self.normal_phases["P2"] = {
                "axis_rows": [], "button_items": [], "view_note": "",
            }
            self.current_exam_phase = "P2"
            self._build_fields()
            self.build_normal_phase_buttons()
            return
        self.store_current_editor_phase(self.normal_phases)
        new_phase = next(
            (phase for phase in ("P1", "P2", "P3", "P4")
             if phase not in self.normal_phases),
            None,
        )
        if new_phase is None:
            messagebox.showinfo("已達上限", "總力戰軸最多可建立 P1～P4 四組子軸。")
            return
        self.normal_phases[new_phase] = {
            "axis_rows": [], "button_items": [], "view_note": "",
        }
        self.current_exam_phase = new_phase
        self._build_fields()
        self.build_normal_phase_buttons()

    def delete_normal_phase(self, phase: str) -> None:
        if phase == "P1" or phase not in self.normal_phases:
            return
        if not messagebox.askyesno(
            "確認刪除子軸",
            f"確定要刪除 {phase} 嗎？刪除後無法復原。",
        ):
            return
        if phase != self.current_exam_phase and self.front_entries:
            self.store_current_editor_phase(self.normal_phases)
        del self.normal_phases[phase]
        if phase == self.current_exam_phase:
            available = [
                value for value in ("P1", "P2", "P3", "P4")
                if value in self.normal_phases
            ]
            previous = [value for value in available if value < phase]
            self.current_exam_phase = previous[-1] if previous else available[0]
            phase_data = self.normal_phases[self.current_exam_phase]
            self._build_fields(
                axis_rows=phase_data.get("axis_rows"),
                button_items=phase_data.get("button_items"),
            )
        self.build_normal_phase_buttons()

    def collect_editor_data(self) -> dict:
        rows = []
        for row in self.axis_layout:
            if row["type"] == "transition":
                rows.append({"type": "transition"})
            else:
                rows.append({
                    "type": "axis",
                    "c": row["c_var"].get().strip(),
                    "time": row["time_var"].get().strip(),
                    "items": list(row["zone"].values),
                    "note": row["note_widget"].get_text(),
                })
        return {
            "axis_rows": rows,
            "button_items": self.front_entries[0].get_items() if self.front_entries else [],
        }

    def store_current_editor_phase(self, phase_store: dict[str, dict]) -> None:
        data = self.collect_editor_data()
        existing = phase_store.get(self.current_exam_phase, {})
        data["view_note"] = existing.get(
            "view_note",
            self.view_note_value if self.current_exam_phase == "P1" else "",
        )
        phase_store[self.current_exam_phase] = data

    def switch_exam_phase(self, phase: str) -> None:
        if phase == self.current_exam_phase:
            return
        phase_store = self.exam_phases if self.mode_var.get() == "考試" else self.normal_phases
        if self.front_entries:
            self.store_current_editor_phase(phase_store)
        self.current_exam_phase = phase
        phase_data = phase_store.get(phase, {})
        self._build_fields(
            axis_rows=phase_data.get("axis_rows"),
            button_items=phase_data.get("button_items"),
        )
        if self.mode_var.get() == "考試":
            self.build_exam_phase_buttons()
        else:
            self.build_normal_phase_buttons()

    def build_tower_options(self) -> None:
        for child in self.tower_options.winfo_children():
            child.destroy()
        boss_row = tk.Frame(self.tower_options, bg=COLORS["panel"])
        boss_row.pack(fill="x", pady=(2, 6))
        tk.Label(
            boss_row, text="爬塔首領：", bg=COLORS["panel"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left")
        for boss in ("賽特", "火龍", "提法瑞斯"):
            self.choice_checkbox(
                boss_row, text=boss, variable=self.boss_var,
                onvalue=boss, offvalue="", command=self.build_tower_armor_options,
            ).pack(side="left", padx=(4, 12))
        self.armor_row = tk.Frame(self.tower_options, bg=COLORS["panel"])
        self.armor_row.pack(fill="x")
        self.build_tower_armor_options(reset=False)

    def build_tower_armor_options(self, reset: bool = True) -> None:
        if reset:
            self.armor_var.set("")
        for child in self.armor_row.winfo_children():
            child.destroy()
        armor_options = {
            "賽特": ("特甲", "輕甲"),
            "火龍": ("特甲", "重甲"),
            "提法瑞斯": ("彈力", "重甲"),
        }.get(self.boss_var.get(), ())
        if not armor_options:
            return
        tk.Label(
            self.armor_row, text="裝甲：", bg=COLORS["panel"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left")
        for armor in armor_options:
            self.choice_checkbox(
                self.armor_row, text=armor, variable=self.armor_var,
                onvalue=armor, offvalue="",
            ).pack(side="left", padx=(4, 12))

    def _build_fields(self, front=None, back=None, axis_rows=None, button_items=None) -> None:
        for child in self.fields.winfo_children():
            child.destroy()
        self.front_entries, self.back_entries = [], []
        # Flatten data created by earlier versions so saved axes remain editable.
        previous_values = [
            value
            for group in list(front or []) + list(back or [])
            for value in group
        ]
        entry = PillEntry(
            self.fields, "內容", button_items or previous_values,
            self.begin_drag, lambda: COLORS["tag"],
        )
        entry.pack(fill="x", pady=(5, 13))
        self.front_entries.append(entry)
        self.drop_zones = []
        self.c_vars = []
        self.time_vars = []
        self.axis_layout = []
        header = tk.Frame(self.fields, bg=COLORS["panel"])
        header.pack(fill="x", pady=(6, 3))
        header.grid_columnconfigure(0, minsize=35)
        header.grid_columnconfigure(1, minsize=90)
        header.grid_columnconfigure(2, minsize=55)
        header.grid_columnconfigure(3, weight=1)
        for column, title in enumerate(("time", "C", "軸"), start=1):
            tk.Label(
                header, text=title, anchor="center", bg=COLORS["panel"],
                fg=COLORS["text"], font=("Microsoft JhengHei UI", 10, "bold"),
            ).grid(row=0, column=column, sticky="ew", padx=(0, 12), pady=(0, 5))

        rows_box = tk.Frame(
            self.fields, bg="#f7fbfd", height=420, highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        rows_box.pack(fill="x")
        rows_box.pack_propagate(False)
        rows_canvas = tk.Canvas(rows_box, bg="#f7fbfd", highlightthickness=0)
        rows_scroll = ttk.Scrollbar(rows_box, orient="vertical", command=rows_canvas.yview)
        table = tk.Frame(rows_canvas, bg="#f7fbfd")
        table.grid_columnconfigure(0, minsize=35)
        table.grid_columnconfigure(1, minsize=90)
        table.grid_columnconfigure(2, minsize=55)
        table.grid_columnconfigure(3, weight=1)
        table_window = rows_canvas.create_window((0, 0), window=table, anchor="nw")
        table.bind(
            "<Configure>",
            lambda _e: rows_canvas.configure(scrollregion=rows_canvas.bbox("all")),
        )
        rows_canvas.bind(
            "<Configure>",
            lambda e: rows_canvas.itemconfigure(table_window, width=e.width),
        )
        rows_canvas.configure(yscrollcommand=rows_scroll.set)
        rows_canvas.pack(side="left", fill="both", expand=True)
        rows_scroll.pack(side="right", fill="y")
        rows_canvas.bind(
            "<Enter>", lambda _e: rows_canvas.bind_all(
                "<MouseWheel>",
                lambda e: rows_canvas.yview_scroll(int(-e.delta / 120), "units"),
            )
        )
        rows_canvas.bind("<Leave>", lambda _e: rows_canvas.unbind_all("<MouseWheel>"))
        self.axis_table = table
        self.axis_rows_canvas = rows_canvas
        self.row_drop_indicator = tk.Frame(table, bg="#ef3340", height=4)
        self.axis_next_row = 1
        rows = axis_rows if axis_rows else [{"c": "", "time": "", "items": []}]
        for row in rows:
            if row.get("type") == "transition":
                self.add_transition_row()
            else:
                self.add_axis_row(row)
    def add_axis_row_safe(self) -> None:
        if not self.front_entries:
            messagebox.showinfo("尚未選擇類型", "請先選擇「總力戰」、「爬塔」或「考試」。")
            return
        self.add_axis_row()

    def add_transition_row_safe(self) -> None:
        if not self.front_entries:
            messagebox.showinfo("尚未選擇類型", "請先選擇「總力戰」、「爬塔」或「考試」。")
            return
        self.add_transition_row()

    def add_axis_row(self, data=None) -> None:
        if not isinstance(data, dict):
            data = {"c": "", "time": "", "items": []}
        row_number = self.axis_next_row
        self.axis_next_row += 1
        c_var = tk.StringVar(value=str(data.get("c", "")))
        time_var = tk.StringVar(value=str(data.get("time", "")))
        self.c_vars.append(c_var)
        self.time_vars.append(time_var)
        time_entry = ttk.Entry(self.axis_table, textvariable=time_var, width=9)
        time_entry.bind("<KeyPress>", self.handle_entry_keypress)
        self.decimal_entries.add(time_entry)
        handle = tk.Label(
            self.axis_table, text="☰", bg=COLORS["panel"], fg=COLORS["muted"],
            cursor="fleur", padx=7, font=("Arial", 13, "bold"),
        )
        handle.grid(row=row_number, column=0, sticky="ns", pady=1)
        time_entry.grid(
            row=row_number, column=1, sticky="ew", padx=(0, 12), pady=1)
        c_entry = ttk.Entry(
            self.axis_table, textvariable=c_var, width=5, justify="center",
        )
        c_entry.bind("<KeyPress>", self.handle_entry_keypress)
        self.decimal_entries.add(c_entry)
        c_entry.grid(row=row_number, column=2, sticky="ew", padx=(0, 12), pady=1)
        axis_cell = tk.Frame(self.axis_table, bg=COLORS["panel"])
        axis_cell.grid(row=row_number, column=3, sticky="ew", pady=1)
        zone = DropZone(axis_cell, list(data.get("items", [])))
        zone.pack(side="left", fill="x", expand=True)
        note_entry = AutoWrapText(
            zone.items, value=str(data.get("note", "")), width=18,
            on_height_change=lambda lines, container=zone: container.configure(
                height=max(44, 24 * lines + 12),
            ),
        )
        note_entry.pack(side="right", padx=6, pady=3)
        delete_button = tk.Button(
            axis_cell, text="X", cursor="hand2", bg=COLORS["danger"], fg="white",
            activebackground="#bd3e4a", activeforeground="white", relief="flat",
            padx=10, pady=7, font=("Arial", 10, "bold"),
        )
        delete_button.pack(side="right", padx=(8, 0))
        delete_button.configure(
            command=lambda: self.delete_axis_row(
                c_var, time_var, zone, c_entry, time_entry, axis_cell, handle)
        )
        self.drop_zones.append(zone)
        row_data = {
            "type": "axis", "c_var": c_var, "time_var": time_var, "zone": zone,
            "widgets": [handle, time_entry, c_entry, axis_cell],
            "anchor": axis_cell,
            "note_widget": note_entry,
        }
        self.axis_layout.append(row_data)
        handle.bind("<ButtonPress-1>", lambda _e, row=row_data: self.start_row_drag(row))
        handle.bind("<B1-Motion>", lambda e, row=row_data: self.preview_row_drop(e, row))
        handle.bind("<ButtonRelease-1>", lambda e, row=row_data: self.finish_row_drag(e, row))

    def handle_entry_keypress(self, event: tk.Event) -> str | None:
        """Block native keypad decimal handling and insert exactly one period."""
        keysym = getattr(event, "keysym", "")
        physical_decimal = self.is_keypad_decimal_down()
        if getattr(event, "keycode", None) != 110 and keysym not in (
            "KP_Decimal", "KP_Separator", "KP_Delete",
        ) and not (keysym == "Delete" and physical_decimal):
            return None
        if not self._decimal_key_down:
            self.insert_decimal(event.widget)
        self._decimal_key_down = True
        return "break"

    @staticmethod
    def insert_decimal(entry: tk.Widget) -> None:
        try:
            entry.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        entry.insert(tk.INSERT, ".")

    @staticmethod
    def is_keypad_decimal_down() -> bool:
        if sys.platform != "win32":
            return False
        # VK_DECIMAL (0x6E) is independent of the active Windows input method.
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x6E) & 0x8000)

    def poll_keypad_decimal(self) -> None:
        """Catch VK_DECIMAL even when a Chinese IME consumes Tk key events."""
        down = self.is_keypad_decimal_down()
        if down and not self._decimal_key_down:
            focused = self.focus_get()
            if focused in self.decimal_entries:
                self.insert_decimal(focused)
        self._decimal_key_down = down
        self.decimal_poll_after_id = self.after(10, self.poll_keypad_decimal)

    def stop_decimal_poll(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        after_id = getattr(self, "decimal_poll_after_id", None)
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError:
                pass
            self.decimal_poll_after_id = None

    def add_transition_row(self) -> None:
        row_number = self.axis_next_row
        self.axis_next_row += 1
        transition = tk.Frame(self.axis_table, bg=COLORS["panel"])
        transition.grid(row=row_number, column=1, columnspan=3, sticky="ew")
        tk.Label(
            transition, text="轉場", bg=COLORS["panel"], fg=COLORS["danger"],
            font=("Microsoft JhengHei UI", 12, "bold"), pady=8,
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            transition, text="X", command=lambda: self.delete_transition_row(row_data),
            cursor="hand2", bg=COLORS["danger"], fg="white",
            activebackground="#bd3e4a", activeforeground="white", relief="flat",
            padx=10, pady=5, font=("Arial", 10, "bold"),
        ).pack(side="right")
        row_data = {
            "type": "transition", "widget": transition, "anchor": transition,
        }
        # The button command closes over row_data and runs only after construction.
        for child in transition.winfo_children():
            if isinstance(child, tk.Button):
                child.configure(command=lambda row=row_data: self.delete_transition_row(row))
        self.axis_layout.append(row_data)

    def delete_transition_row(self, row: dict) -> None:
        if row in self.axis_layout:
            self.axis_layout.remove(row)
        row["widget"].destroy()
        self.relayout_axis_rows()

    def start_row_drag(self, row: dict) -> None:
        self.dragged_axis_row = row
        row["widgets"][0].configure(bg=COLORS["tag"], fg=COLORS["primary"])
        self.axis_rows_canvas.configure(cursor="fleur")

    def drop_target(self, y_root: int, row: dict) -> tuple[list[dict], int, int]:
        remaining = [candidate for candidate in self.axis_layout if candidate is not row]
        target_index = len(remaining)
        line_y = 0
        for index, candidate in enumerate(remaining):
            anchor = candidate["anchor"]
            midpoint = anchor.winfo_rooty() + anchor.winfo_height() // 2
            if y_root < midpoint:
                target_index = index
                line_y = anchor.winfo_y()
                break
        else:
            if remaining:
                last = remaining[-1]["anchor"]
                line_y = last.winfo_y() + last.winfo_height()
        return remaining, target_index, line_y

    def preview_row_drop(self, event: tk.Event, row: dict) -> None:
        canvas_top = self.axis_rows_canvas.winfo_rooty()
        canvas_bottom = canvas_top + self.axis_rows_canvas.winfo_height()
        if event.y_root < canvas_top + 28:
            self.axis_rows_canvas.yview_scroll(-1, "units")
            self.update_idletasks()
        elif event.y_root > canvas_bottom - 28:
            self.axis_rows_canvas.yview_scroll(1, "units")
            self.update_idletasks()
        _remaining, _target, line_y = self.drop_target(event.y_root, row)
        self.row_drop_indicator.place(
            x=4, y=max(0, line_y - 2),
            width=max(20, self.axis_table.winfo_width() - 8), height=4,
        )
        self.row_drop_indicator.lift()

    def finish_row_drag(self, event: tk.Event, row: dict) -> None:
        if row not in self.axis_layout:
            return
        row["widgets"][0].configure(bg=COLORS["panel"], fg=COLORS["muted"])
        remaining, target_index, _line_y = self.drop_target(event.y_root, row)
        remaining.insert(target_index, row)
        self.axis_layout = remaining
        self.row_drop_indicator.place_forget()
        self.axis_rows_canvas.configure(cursor="")
        self.relayout_axis_rows()

    def relayout_axis_rows(self) -> None:
        for grid_row, row in enumerate(self.axis_layout, start=1):
            if row["type"] == "transition":
                row["widget"].grid_configure(row=grid_row)
            else:
                for widget in row["widgets"]:
                    widget.grid_configure(row=grid_row)

    def delete_axis_row(
        self, c_var: tk.StringVar, time_var: tk.StringVar, zone: DropZone,
        c_entry: tk.Widget, time_entry: tk.Widget, axis_cell: tk.Widget,
        handle: tk.Widget,
    ) -> None:
        index = self.drop_zones.index(zone)
        self.drop_zones.pop(index)
        self.c_vars.pop(index)
        self.time_vars.pop(index)
        self.axis_layout = [
            row for row in self.axis_layout
            if row.get("zone") is not zone
        ]
        c_entry.destroy()
        time_entry.destroy()
        axis_cell.destroy()
        handle.destroy()
        self.relayout_axis_rows()

    def begin_drag(self, event: tk.Event, value) -> None:
        item = value if isinstance(value, dict) else {"text": str(value), "color": COLORS["tag"]}
        self.drag_window = tk.Toplevel(self)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes("-topmost", True)
        tk.Label(
            self.drag_window, text=item["text"], bg=item.get("color", COLORS["primary"]),
            fg=COLORS["text"],
            padx=10, pady=5, font=("Microsoft JhengHei UI", 9, "bold"),
        ).pack()
        self.drag_window.geometry(f"+{event.x_root + 8}+{event.y_root + 8}")
        self.bind("<B1-Motion>", self._drag_motion)
        self.bind("<ButtonRelease-1>", lambda e, v=item: self._drag_release(e, v))

    def _drag_motion(self, event: tk.Event) -> None:
        if self.drag_window:
            self.drag_window.geometry(f"+{event.x_root + 8}+{event.y_root + 8}")

    def _drag_release(self, event: tk.Event, value) -> None:
        for zone in self.drop_zones:
            if zone.contains(event.x_root, event.y_root):
                zone.add(value)
                break
        if self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")

    def clear_axis_rows(self) -> None:
        if not self.front_entries:
            return
        for row in list(self.axis_layout):
            if row["type"] == "transition":
                row["widget"].destroy()
            else:
                for widget in row["widgets"]:
                    widget.destroy()
        self.drop_zones = []
        self.c_vars = []
        self.time_vars = []
        self.axis_layout = []
        self.axis_next_row = 1
        self.add_axis_row()

    def save_axis(self) -> None:
        name, mode = self.name_var.get().strip(), self.mode_var.get()
        if not name or mode not in ("一般", "爬塔", "考試"):
            messagebox.showinfo("尚未完成", "請輸入名稱並選擇「總力戰」、「爬塔」或「考試」。")
            return
        if mode == "爬塔" and (not self.boss_var.get() or not self.armor_var.get()):
            messagebox.showinfo("尚未完成", "爬塔軸請選擇首領與裝甲類型。")
            return
        editor_data = self.collect_editor_data()
        rows = editor_data["axis_rows"]
        if mode == "考試":
            self.store_current_editor_phase(self.exam_phases)
            for phase in ("P1", "P2", "P3"):
                self.exam_phases.setdefault(
                    phase, {"axis_rows": [], "button_items": [], "view_note": ""},
                )
        elif mode == "一般" and self.normal_phases_enabled:
            self.store_current_editor_phase(self.normal_phases)
        first_axis_row = next((row for row in rows if row["type"] == "axis"), None)
        axis = Axis(
            id=self.editing_id or uuid4().hex,
            name=name,
            mode=mode,
            front=[entry.get_values() for entry in self.front_entries],
            back=[entry.get_values() for entry in self.back_entries],
            c_text=first_axis_row["c"] if first_axis_row else "",
            time_text=first_axis_row["time"] if first_axis_row else "",
            c_items=first_axis_row["items"] if first_axis_row else [],
            time_items=[],
            axis_rows=rows,
            button_items=editor_data["button_items"],
            url=self.url_var.get().strip(),
            tower_boss=self.boss_var.get() if mode == "爬塔" else "",
            armor=self.armor_var.get() if mode == "爬塔" else "",
            view_note=self.view_note_value,
            exam_phases=self.exam_phases if mode == "考試" else {},
            normal_phases=self.normal_phases if mode == "一般" else {},
        )
        axes = self.store.load()
        match = next((i for i, item in enumerate(axes) if item.id == axis.id), None)
        if match is None:
            axes.append(axis)
        else:
            axes[match] = axis
        try:
            self.store.save(axes)
        except OSError as error:
            messagebox.showerror("儲存失敗", str(error))
            return
        messagebox.showinfo("儲存完成", f"「{name}」已儲存。")
        self.show_list()

    def show_list(self) -> None:
        self.clear_window()
        self.nav("看軸")
        scroll = ScrollFrame(self)
        scroll.pack(fill="both", expand=True)
        self.list_scroll = scroll
        body = tk.Frame(scroll.body, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=55, pady=32)
        title_row = tk.Frame(body, bg=COLORS["bg"])
        title_row.pack(fill="x")
        title_left = tk.Frame(title_row, bg=COLORS["bg"])
        title_left.pack(side="left", fill="both", expand=True)
        tk.Label(
            title_left, text="已儲存的軸", bg=COLORS["bg"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 22, "bold"),
        ).pack(anchor="w")
        if SAVED_AXES_GIF.exists():
            AnimatedGifLabel(title_row, SAVED_AXES_GIF).pack(side="right", anchor="ne")
        if SAVED_AXES_SIDE_GIF.exists():
            AnimatedGifLabel(title_row, SAVED_AXES_SIDE_GIF).pack(
                side="right", anchor="ne", padx=(0, 8),
            )
        axes = self.store.load()
        if not axes:
            tk.Label(body, text="目前還沒有資料，先建立第一個軸吧！", bg=COLORS["bg"],
                     fg=COLORS["muted"], font=("Microsoft JhengHei UI", 12)).pack(pady=100)
            return
        filters = tk.Frame(title_left, bg=COLORS["bg"])
        filters.pack(side="bottom", fill="x", anchor="sw", pady=(14, 0))
        self.show_normal_var = tk.BooleanVar(value=True)
        self.show_tower_var = tk.BooleanVar(value=False)
        self.show_exam_var = tk.BooleanVar(value=True)
        self.filter_boss_var = tk.StringVar()
        self.filter_armor_var = tk.StringVar()
        tk.Label(
            filters, text="顯示：", bg=COLORS["bg"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left")
        for text, variable in (
            ("總力戰", self.show_normal_var),
            ("考試", self.show_exam_var),
            ("爬塔", self.show_tower_var),
        ):
            filter_button = self.choice_checkbox(
                filters, text=text, variable=variable,
                command=lambda: self.update_list_tower_filters(axes),
            )
            filter_button.configure(padx=5, pady=2)
            icon_path = {
                "總力戰": NORMAL_RANK_ICON,
                "考試": EXAM_FILTER_ICON,
                "爬塔": TOWER_FILTER_ICON,
            }[text]
            if icon_path.exists():
                with Image.open(icon_path) as source:
                    icon = source.convert("RGBA")
                icon.thumbnail((30, 30), Image.Resampling.LANCZOS)
                icon_canvas = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
                icon_canvas.alpha_composite(
                    icon, ((30 - icon.width) // 2, (30 - icon.height) // 2),
                )
                if not hasattr(self, "filter_icons"):
                    self.filter_icons = {}
                self.filter_icons[text] = ImageTk.PhotoImage(icon_canvas)
                filter_button.configure(
                    image=self.filter_icons[text], compound="left",
                )
            filter_button.pack(side="left", padx=(4, 14))
        self.tower_filter_options = tk.Frame(body, bg=COLORS["bg"])
        self.axis_cards = tk.Frame(body, bg=COLORS["bg"])
        self.axis_cards.pack(fill="both", expand=True)
        self.update_list_tower_filters(axes, reset=False)

    def update_list_tower_filters(self, axes: list[Axis], reset: bool = False) -> None:
        if reset:
            self.filter_armor_var.set("")
        for child in self.tower_filter_options.winfo_children():
            child.destroy()
        if self.show_tower_var.get():
            self.tower_filter_options.pack(
                fill="x", pady=(8, 8), before=self.axis_cards,
            )
            boss_row = tk.Frame(self.tower_filter_options, bg=COLORS["bg"])
            boss_row.pack(fill="x", pady=2)
            tk.Label(
                boss_row, text="爬塔首領：", bg=COLORS["bg"], fg=COLORS["text"],
                font=("Microsoft JhengHei UI", 9, "bold"),
            ).pack(side="left")
            for boss in ("賽特", "火龍", "提法瑞斯"):
                self.choice_checkbox(
                    boss_row, text=boss, variable=self.filter_boss_var,
                    onvalue=boss, offvalue="",
                    command=lambda: self.update_list_tower_filters(axes, reset=True),
                ).pack(side="left", padx=(4, 12))
            armor_options = {
                "賽特": ("特甲", "輕甲"),
                "火龍": ("特甲", "重甲"),
                "提法瑞斯": ("彈力", "重甲"),
            }.get(self.filter_boss_var.get(), ())
            if armor_options:
                armor_row = tk.Frame(self.tower_filter_options, bg=COLORS["bg"])
                armor_row.pack(fill="x", pady=2)
                tk.Label(
                    armor_row, text="裝甲：", bg=COLORS["bg"], fg=COLORS["text"],
                    font=("Microsoft JhengHei UI", 9, "bold"),
                ).pack(side="left")
                for armor in armor_options:
                    self.choice_checkbox(
                        armor_row, text=armor, variable=self.filter_armor_var,
                        onvalue=armor, offvalue="",
                        command=lambda: self.render_axis_cards(axes),
                    ).pack(side="left", padx=(4, 12))
        else:
            self.tower_filter_options.pack_forget()
        self.render_axis_cards(axes)

    def render_axis_cards(self, axes: list[Axis]) -> None:
        for child in self.axis_cards.winfo_children():
            child.destroy()
        self.list_all_axes = axes
        self.visible_axis_cards = []
        self.axis_card_drop_indicator = tk.Frame(
            self.axis_cards, bg="#ef3340", height=4,
        )
        selected_modes = set()
        if self.show_normal_var.get():
            selected_modes.add("一般")
        if self.show_tower_var.get():
            selected_modes.add("爬塔")
        if self.show_exam_var.get():
            selected_modes.add("考試")
        visible_axes = [axis for axis in axes if axis.mode in selected_modes]
        if self.show_tower_var.get() and self.filter_boss_var.get():
            visible_axes = [
                axis for axis in visible_axes
                if axis.mode != "爬塔" or axis.tower_boss == self.filter_boss_var.get()
            ]
        if self.show_tower_var.get() and self.filter_armor_var.get():
            visible_axes = [
                axis for axis in visible_axes
                if axis.mode != "爬塔" or axis.armor == self.filter_armor_var.get()
            ]
        if not visible_axes:
            tk.Label(
                self.axis_cards, text="沒有符合目前篩選條件的軸。",
                bg=COLORS["bg"], fg=COLORS["muted"],
                font=("Microsoft JhengHei UI", 11),
            ).pack(pady=70)
            return
        for axis in visible_axes:
            card = tk.Frame(self.axis_cards, bg=COLORS["panel"], highlightthickness=1,
                            highlightbackground=COLORS["border"])
            card.pack(fill="x", pady=7)
            handle = tk.Label(
                card, text="☰", bg=COLORS["panel"], fg=COLORS["muted"],
                cursor="fleur", padx=8, font=("Arial", 15, "bold"),
            )
            handle.pack(side="left", fill="y", padx=(8, 0), pady=10)
            info = tk.Frame(card, bg=COLORS["panel"])
            info.pack(side="left", fill="both", expand=True, padx=18, pady=13)
            tk.Label(info, text=axis.name, bg=COLORS["panel"], fg=COLORS["text"],
                     font=("Microsoft JhengHei UI", 13, "bold")).pack(anchor="w")
            description = mode_display_name(axis.mode)
            if axis.mode == "爬塔" and axis.tower_boss:
                description += f"  ·  {axis.tower_boss}"
                if axis.armor:
                    description += f"  ·  {axis.armor}"
            tk.Label(info, text=description,
                     bg=COLORS["panel"], fg=COLORS["muted"],
                     font=("Microsoft JhengHei UI", 9)).pack(anchor="w", pady=(3, 0))
            if axis.url:
                link = tk.Label(
                    info, text=axis.url, bg=COLORS["panel"], fg=COLORS["primary"],
                    cursor="hand2", font=("Microsoft JhengHei UI", 9, "underline"),
                )
                link.pack(anchor="w", pady=(3, 0))
                link.bind("<Button-1>", lambda _e, url=axis.url: self.open_url(url))
            actions = tk.Frame(card, bg=COLORS["panel"])
            actions.pack(side="right", padx=16, pady=16)
            self.action_button(actions, "查看", lambda a=axis: self.show_view(a),
                               "#3a9b84").pack(side="left")
            self.action_button(actions, "編輯", lambda a=axis: self.show_editor(a),
                               COLORS["primary"]).pack(side="left", padx=5)
            self.action_button(actions, "刪除", lambda a=axis: self.delete_axis(a),
                               COLORS["danger"]).pack(side="left")
            card_data = {"axis": axis, "card": card, "handle": handle}
            self.visible_axis_cards.append(card_data)
            handle.bind(
                "<ButtonPress-1>",
                lambda _e, item=card_data: self.start_axis_card_drag(item),
            )
            handle.bind(
                "<B1-Motion>",
                lambda e, item=card_data: self.preview_axis_card_drop(e, item),
            )
            handle.bind(
                "<ButtonRelease-1>",
                lambda e, item=card_data: self.finish_axis_card_drag(e, item),
            )

    def start_axis_card_drag(self, item: dict) -> None:
        self.dragged_axis_card = item
        item["handle"].configure(bg=COLORS["tag"], fg=COLORS["primary"])

    def axis_card_drop_target(
        self, y_root: int, item: dict,
    ) -> tuple[list[dict], int, int]:
        remaining = [
            candidate for candidate in self.visible_axis_cards
            if candidate is not item
        ]
        target_index = len(remaining)
        line_y = 0
        for index, candidate in enumerate(remaining):
            card = candidate["card"]
            midpoint = card.winfo_rooty() + card.winfo_height() // 2
            if y_root < midpoint:
                target_index = index
                line_y = card.winfo_y()
                break
        else:
            if remaining:
                last = remaining[-1]["card"]
                line_y = last.winfo_y() + last.winfo_height() + 7
        return remaining, target_index, line_y

    def preview_axis_card_drop(self, event: tk.Event, item: dict) -> None:
        canvas = self.list_scroll.canvas
        canvas_top = canvas.winfo_rooty()
        canvas_bottom = canvas_top + canvas.winfo_height()
        if event.y_root < canvas_top + 36:
            canvas.yview_scroll(-1, "units")
            self.update_idletasks()
        elif event.y_root > canvas_bottom - 36:
            canvas.yview_scroll(1, "units")
            self.update_idletasks()
        _remaining, _target, line_y = self.axis_card_drop_target(
            event.y_root, item,
        )
        self.axis_card_drop_indicator.place(
            x=0, y=max(0, line_y - 2),
            width=max(20, self.axis_cards.winfo_width()), height=4,
        )
        self.axis_card_drop_indicator.lift()

    def finish_axis_card_drag(self, event: tk.Event, item: dict) -> None:
        if item not in self.visible_axis_cards:
            return
        item["handle"].configure(bg=COLORS["panel"], fg=COLORS["muted"])
        remaining, target_index, _line_y = self.axis_card_drop_target(
            event.y_root, item,
        )
        remaining.insert(target_index, item)
        old_order = [entry["axis"].id for entry in self.visible_axis_cards]
        new_order = [entry["axis"] for entry in remaining]
        self.axis_card_drop_indicator.place_forget()
        if [axis.id for axis in new_order] == old_order:
            return
        visible_ids = set(old_order)
        visible_positions = [
            index for index, axis in enumerate(self.list_all_axes)
            if axis.id in visible_ids
        ]
        for position, axis in zip(visible_positions, new_order):
            self.list_all_axes[position] = axis
        try:
            self.store.save(self.list_all_axes)
        except OSError as error:
            messagebox.showerror("排序儲存失敗", str(error))
            self.render_axis_cards(self.list_all_axes)
            return
        self.render_axis_cards(self.list_all_axes)

    def show_view(self, axis: Axis, exam_phase: str = "P1") -> None:
        self.clear_window()
        self.nav("看軸")
        scroll = ScrollFrame(self)
        scroll.pack(fill="both", expand=True)
        panel = tk.Frame(
            scroll.body, bg=COLORS["panel"], highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        panel.pack(fill="x", padx=55, pady=32)
        header = tk.Frame(panel, bg=COLORS["panel"])
        header.pack(fill="x", padx=30, pady=(25, 20))
        tk.Label(
            header, text=axis.name, bg=COLORS["panel"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 22, "bold"),
        ).pack(side="left")
        categories = [mode_display_name(axis.mode)]
        if axis.mode == "爬塔" and axis.tower_boss:
            categories.append(axis.tower_boss)
            if axis.armor:
                categories.append(axis.armor)
        for category in categories:
            tk.Label(
                header, text=category, bg=COLORS["tag"], fg=COLORS["primary"],
                padx=12, pady=5, font=("Microsoft JhengHei UI", 10, "bold"),
            ).pack(side="left", padx=(12, 0))
        if axis.url:
            link = tk.Label(
                panel, text=axis.url, bg=COLORS["panel"], fg=COLORS["primary"],
                cursor="hand2", font=("Microsoft JhengHei UI", 10, "underline"),
            )
            link.pack(anchor="w", padx=30, pady=(0, 15))
            link.bind("<Button-1>", lambda _e, url=axis.url: self.open_url(url))
        has_subaxes = axis.mode == "考試" or (
            axis.mode == "一般" and bool(axis.normal_phases)
        )
        phase_store = (
            axis.exam_phases if axis.mode == "考試" else axis.normal_phases
        ) if has_subaxes else {}
        phase_data = phase_store.get(exam_phase, {}) if has_subaxes else {}
        current_time = (
            phase_data.get(
                "view_note", axis.view_note if exam_phase == "P1" else "",
            )
            if has_subaxes else axis.view_note
        )
        overview_note_var = tk.StringVar(value=current_time)
        overview_row = tk.Frame(panel, bg=COLORS["panel"])
        overview_row.pack(fill="x", padx=30, pady=(0, 15))
        tk.Label(
            overview_row, text="目前時間", bg=COLORS["panel"], fg=COLORS["text"],
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))
        overview_note = ttk.Entry(
            overview_row, textvariable=overview_note_var, width=35,
        )
        overview_note.pack(side="left")
        overview_note.bind("<KeyPress>", self.handle_entry_keypress)
        self.decimal_entries.add(overview_note)
        overview_note.bind(
            "<Return>",
            lambda _e: self.save_overview_note(
                axis, overview_note_var, exam_phase,
            ),
        )
        overview_note.bind(
            "<FocusOut>",
            lambda _e: self.save_overview_note(
                axis, overview_note_var, exam_phase,
            ),
        )

        if has_subaxes:
            phase_bar = tk.Frame(panel, bg=COLORS["panel"])
            phase_bar.pack(fill="x", padx=30, pady=(0, 12))
            tk.Label(
                phase_bar, text="子軸：", bg=COLORS["panel"],
                fg=COLORS["text"], font=("Microsoft JhengHei UI", 10, "bold"),
            ).pack(side="left")
            phase_names = (
                ("P1", "P2", "P3") if axis.mode == "考試"
                else tuple(phase for phase in ("P1", "P2", "P3", "P4")
                           if phase in axis.normal_phases)
            )
            for phase in phase_names:
                self.action_button(
                    phase_bar, phase,
                    lambda value=phase: self.show_view(axis, value),
                    COLORS["primary"] if phase == exam_phase else "#8296a5",
                ).pack(side="left", padx=(5, 0))
            rows = phase_store.get(exam_phase, {}).get("axis_rows", [])
        else:
            rows = axis.axis_rows or [{
                "c": axis.c_text,
                "time": axis.time_text,
                "items": list(axis.c_items) + list(axis.time_items),
            }]
        table_header = tk.Frame(panel, bg=COLORS["panel"])
        table_header.pack(fill="x", padx=30)
        table_header.grid_columnconfigure(0, minsize=64)
        table_header.grid_columnconfigure(1, minsize=90)
        table_header.grid_columnconfigure(2, minsize=55)
        table_header.grid_columnconfigure(3, weight=1)
        all_view_buttons = []
        finish_buttons = []
        reset_button = tk.Button(
            table_header, text="reset", cursor="hand2", bg="#3a9b64", fg="white",
            activebackground="#2d7c4f", activeforeground="white", relief="flat",
            padx=8, pady=4, font=("Arial", 9, "bold"),
        )
        reset_button.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 7))
        for column, title in enumerate(("time", "C", "軸"), start=1):
            tk.Label(
                table_header, text=title, anchor="center", bg=COLORS["panel"],
                fg=COLORS["text"], font=("Microsoft JhengHei UI", 10, "bold"),
            ).grid(row=0, column=column, sticky="ew", padx=(0, 12), pady=(0, 7))

        view_rows_box = tk.Frame(
            panel, bg="#f7fbfd", height=420, highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        view_rows_box.pack(fill="x", padx=30)
        view_rows_box.pack_propagate(False)
        view_canvas = tk.Canvas(view_rows_box, bg="#f7fbfd", highlightthickness=0)
        view_scroll = ttk.Scrollbar(
            view_rows_box, orient="vertical", command=view_canvas.yview,
        )
        table = tk.Frame(view_canvas, bg="#f7fbfd")
        table.grid_columnconfigure(0, minsize=64)
        table.grid_columnconfigure(1, minsize=90)
        table.grid_columnconfigure(2, minsize=55)
        table.grid_columnconfigure(3, weight=1)
        table_window = view_canvas.create_window((0, 0), window=table, anchor="nw")
        table.bind(
            "<Configure>",
            lambda _e: view_canvas.configure(scrollregion=view_canvas.bbox("all")),
        )
        view_canvas.bind(
            "<Configure>",
            lambda e: view_canvas.itemconfigure(table_window, width=e.width),
        )
        view_canvas.configure(yscrollcommand=view_scroll.set)
        view_canvas.pack(side="left", fill="both", expand=True)
        view_scroll.pack(side="right", fill="y")
        view_canvas.bind(
            "<Enter>", lambda _e: view_canvas.bind_all(
                "<MouseWheel>",
                lambda e: view_canvas.yview_scroll(int(-e.delta / 120), "units"),
            )
        )
        view_canvas.bind("<Leave>", lambda _e: view_canvas.unbind_all("<MouseWheel>"))
        for row_number, row in enumerate(rows):
            if row.get("type") == "transition":
                tk.Label(
                    table, text="轉場", bg=COLORS["panel"], fg=COLORS["danger"],
                    font=("Microsoft JhengHei UI", 12, "bold"), pady=8,
                ).grid(row=row_number, column=0, columnspan=4, sticky="ew")
                continue
            finish = tk.Button(
                table, text="finish", cursor="hand2", bg="#657783", fg="white",
                activebackground="#4f606b", activeforeground="white", relief="flat",
                padx=8, pady=5, font=("Arial", 9, "bold"),
            )
            finish.grid(row=row_number, column=0, sticky="ew", padx=(0, 8), pady=1)
            finish_buttons.append(finish)
            for column, value in enumerate((row.get("time", ""), row.get("c", ""))):
                field_frame = tk.Frame(
                    table, bg="#f7fbfd", highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    width=55 if column == 1 else 90, height=34,
                )
                field_frame.grid(row=row_number, column=column + 1, sticky="ew",
                                 padx=(0, 12), pady=1)
                field_frame.grid_propagate(False)
                tk.Label(
                    field_frame, text=value, bg="#f7fbfd", fg=COLORS["text"],
                    font=("Microsoft JhengHei UI", 9),
                ).place(relx=.5, rely=.5, anchor="center")
            zone = tk.Frame(
                table, bg="#f7fbfd", height=44, highlightthickness=2,
                highlightbackground=COLORS["border"],
            )
            zone.grid(row=row_number, column=3, sticky="ew", pady=1)
            zone.grid_propagate(False)
            row_buttons = []
            for raw_item in row.get("items", []):
                item = raw_item if isinstance(raw_item, dict) else {
                    "text": str(raw_item), "color": COLORS["tag"],
                }
                button = tk.Button(
                    zone, text=item.get("text", ""), bg=item.get("color", COLORS["tag"]),
                    fg=COLORS["text"], activebackground="#aeb6bc", cursor="hand2",
                    relief="flat", padx=9, pady=4,
                    highlightthickness=1, highlightbackground=COLORS["border"],
                )
                button.original_color = item.get("color", COLORS["tag"])
                button.is_gray = False
                button.configure(command=lambda b=button: self.toggle_view_item(b))
                button.pack(side="left", padx=4, pady=7)
                row_buttons.append(button)
                all_view_buttons.append(button)
            note_entry = AutoWrapText(
                zone, value=str(row.get("note", "")), width=18,
                on_height_change=lambda lines, container=zone: container.configure(
                    height=max(44, 24 * lines + 12),
                ),
            )
            note_entry.pack(side="right", padx=6, pady=3)
            note_entry.bind(
                "<FocusOut>",
                lambda _e, index=row_number, widget=note_entry:
                self.save_view_note(axis, rows, index, widget, exam_phase),
            )
            finish.is_finished = False
            finish.configure(
                command=lambda buttons=row_buttons, control=finish:
                self.toggle_view_row(buttons, control)
            )
        reset_button.configure(
            command=lambda: self.reset_view_buttons(
                all_view_buttons, finish_buttons, view_canvas,
            )
        )
        view_actions = tk.Frame(panel, bg=COLORS["panel"])
        view_actions.pack(anchor="e", padx=30, pady=25)
        self.action_button(
            view_actions, "編輯", lambda: self.show_editor(axis), COLORS["primary"],
        ).pack(side="left")
        self.action_button(view_actions, "返回", self.show_list, "#8296a5").pack(
            side="left", padx=(7, 0))

    def toggle_view_item(self, button: tk.Button) -> None:
        button.is_gray = not button.is_gray
        color = "#666d72" if button.is_gray else button.original_color
        button.configure(bg=color, activebackground=color)

    def toggle_view_row(self, buttons: list[tk.Button], control: tk.Button) -> None:
        control.is_finished = not control.is_finished
        for button in buttons:
            button.is_gray = control.is_finished
            color = "#666d72" if control.is_finished else button.original_color
            button.configure(bg=color, activebackground=color)
        control.configure(bg="#3f4a51" if control.is_finished else "#657783")

    def save_view_note(
        self, axis: Axis, rows: list[dict], row_index: int,
        note_widget: AutoWrapText, exam_phase: str = "",
    ) -> None:
        note = note_widget.get_text()
        if rows[row_index].get("note", "") == note:
            return
        rows[row_index]["note"] = note
        if axis.mode in ("考試", "一般") and exam_phase and (
            axis.mode == "考試" or axis.normal_phases
        ):
            phase_store = axis.exam_phases if axis.mode == "考試" else axis.normal_phases
            phase_data = phase_store.setdefault(exam_phase, {})
            phase_data["axis_rows"] = rows
        else:
            axis.axis_rows = rows
        axes = self.store.load()
        for index, saved_axis in enumerate(axes):
            if saved_axis.id == axis.id:
                axes[index] = axis
                self.store.save(axes)
                break

    def save_overview_note(
        self, axis: Axis, variable: tk.StringVar, exam_phase: str = "",
    ) -> None:
        note = variable.get()
        has_subaxes = axis.mode == "考試" or (
            axis.mode == "一般" and bool(axis.normal_phases)
        )
        if has_subaxes and exam_phase:
            phase_store = (
                axis.exam_phases if axis.mode == "考試" else axis.normal_phases
            )
            phase_data = phase_store.setdefault(exam_phase, {})
            if phase_data.get("view_note", "") == note:
                return
            phase_data["view_note"] = note
        else:
            if axis.view_note == note:
                return
            axis.view_note = note
            self.view_note_value = note
        axes = self.store.load()
        for index, saved_axis in enumerate(axes):
            if saved_axis.id == axis.id:
                axes[index] = axis
                self.store.save(axes)
                break

    def reset_view_buttons(
        self, buttons: list[tk.Button], controls: list[tk.Button],
        canvas: tk.Canvas,
    ) -> None:
        for button in buttons:
            button.is_gray = False
            button.configure(
                bg=button.original_color, activebackground=button.original_color,
            )
        for control in controls:
            control.is_finished = False
            control.configure(bg="#657783", activebackground="#4f606b")
        canvas.yview_moveto(0)

    def open_url(self, url: str) -> None:
        target = url.strip()
        if not target:
            return
        if "://" not in target:
            target = "https://" + target
        webbrowser.open(target)

    def action_button(self, master: tk.Misc, text: str, command, color: str) -> tk.Button:
        return tk.Button(
            master, text=text, command=command, cursor="hand2", bg=color, fg="white",
            activebackground=color, activeforeground="white", relief="flat",
            padx=18, pady=7, font=("Microsoft JhengHei UI", 10, "bold"),
        )

    def delete_axis(self, axis: Axis) -> None:
        if not messagebox.askyesno("確認刪除", f"確定要刪除「{axis.name}」嗎？"):
            return
        axes = [item for item in self.store.load() if item.id != axis.id]
        self.store.save(axes)
        self.show_list()


if __name__ == "__main__":
    AxisEditor().mainloop()
