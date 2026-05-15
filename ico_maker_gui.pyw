from __future__ import annotations

import ctypes
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Callable, Iterable

import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageOps

    PIL_AVAILABLE = True
    PIL_IMPORT_ERROR = ""
    try:
        RESAMPLE = Image.Resampling.LANCZOS
    except AttributeError:
        RESAMPLE = Image.LANCZOS
except Exception as exc:
    Image = None
    ImageOps = None
    RESAMPLE = None
    PIL_AVAILABLE = False
    PIL_IMPORT_ERROR = str(exc)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

SCRIPT_DIR = Path(__file__).resolve().parent
APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else SCRIPT_DIR
)
OUTPUT_ROOT = APP_DIR / "output"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
SUPPORTED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}

WINDOW_BG = "#F5F1E8"
CARD_BG = "#FFF9EE"
LIST_BG = "#FFFDF8"
TEXT_DARK = "#243119"
TEXT_MID = "#4A5A3B"
TEXT_WARM = "#6A5530"
BORDER = "#A88F5E"
MUTED_BORDER = "#D6CCBC"
GREEN = "#395B3A"
BROWN = "#7A5C33"
ORANGE = "#C16C2E"
HOVER_BG = "#FFF2D8"

TITLE_TEXT = "ICO \u5236\u4f5c\u5de5\u5177"
SUBTITLE_TEXT = (
    "\u9009\u62e9\u56fe\u7247\u6216\u76f4\u63a5\u62d6\u5165\u9762\u677f\uff0c"
    "\u70b9\u51fb\u201c\u5f00\u59cb\u5236\u4f5c\u201d\u540e\u81ea\u52a8\u88c1\u526a"
    "\u4e3a\u6b63\u65b9\u5f62\u5e76\u751f\u6210\u591a\u5c3a\u5bf8 ICO\u3002"
)
DROP_TEXT_READY = (
    "\u5c06\u56fe\u7247\u62d6\u5230\u8fd9\u91cc\n"
    "\u6216\u70b9\u51fb\u6b64\u533a\u57df\u9009\u62e9\u56fe\u7247"
)
DROP_TEXT_NO_DND = (
    "\u70b9\u51fb\u6b64\u533a\u57df\u9009\u62e9\u56fe\u7247\n"
    "\u62d6\u62fd\u529f\u80fd\u672a\u542f\u7528\uff0c\u53ef\u5148\u8fd0\u884c"
    "\u201c\u5b89\u88c5\u4f9d\u8d56.bat\u201d"
)
SIZE_TEXT = (
    "\u8f93\u51fa\u5c3a\u5bf8\uff1a16x16\uff0c24x24\uff0c32x32\uff0c48x48\uff0c"
    "64x64\uff0c128x128\uff0c256x256"
)


def enable_windows_dpi_awareness() -> None:
    if not sys.platform.startswith("win"):
        return

    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(-4):
            return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def apply_tk_scaling(root: tk.Tk) -> None:
    if not sys.platform.startswith("win"):
        return

    try:
        scaling = float(root.winfo_fpixels("1i")) / 72.0
        root.tk.call("tk", "scaling", scaling)
    except Exception:
        pass


def crop_to_square(image: Image.Image) -> Image.Image:
    width, height = image.size
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    return image.crop((left, top, left + edge, top + edge))


def build_output_folder_name(source: Path, existing_names: dict[str, int]) -> str:
    base_name = source.stem
    count = existing_names.get(base_name, 0) + 1
    existing_names[base_name] = count
    return base_name if count == 1 else f"{base_name}_{count}"


def convert_image_to_ico_set(source_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        prepared = ImageOps.exif_transpose(image).convert("RGBA")
        square = crop_to_square(prepared)

        for size in ICO_SIZES:
            icon = square.resize((size, size), RESAMPLE)
            icon.save(output_dir / f"{size}x{size}.ico", format="ICO")


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES


class IconMakerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.selected_files: list[Path] = []
        self.processing = False

        self.root.title(TITLE_TEXT)
        self.root.geometry("920x760")
        self.root.minsize(860, 700)
        self.root.configure(bg=WINDOW_BG)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.root, bg=WINDOW_BG, padx=28, pady=22)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(5, weight=1)

        self._build_ui()
        self._register_drop_targets()
        self._bind_drop_zone_clicks()
        self._refresh_ui_state()
        self._update_wraplengths()

    def _build_ui(self) -> None:
        self.title_label = tk.Label(
            self.main_frame,
            text=TITLE_TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
            bg=WINDOW_BG,
            fg=TEXT_DARK,
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, 6))

        self.subtitle_label = tk.Label(
            self.main_frame,
            text=SUBTITLE_TEXT,
            font=("Microsoft YaHei UI", 11),
            bg=WINDOW_BG,
            fg=TEXT_MID,
            justify="center",
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        self.drop_frame = tk.Frame(
            self.main_frame,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=2,
            bd=0,
            cursor="hand2",
            height=140,
        )
        self.drop_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.drop_frame.grid_propagate(False)
        self.drop_frame.columnconfigure(0, weight=1)
        self.drop_frame.rowconfigure(0, weight=1)

        self.drop_label = tk.Label(
            self.drop_frame,
            text=self._drop_text(),
            font=("Microsoft YaHei UI", 13),
            bg=CARD_BG,
            fg=TEXT_WARM,
            justify="center",
            cursor="hand2",
        )
        self.drop_label.grid(row=0, column=0, sticky="nsew")

        self.action_bar = tk.Frame(self.main_frame, bg=WINDOW_BG)
        self.action_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 14))
        self.action_bar.columnconfigure(0, weight=1)

        controls = tk.Frame(self.action_bar, bg=WINDOW_BG)
        controls.grid(row=0, column=0, sticky="w")

        self.select_button = self._build_button(
            controls,
            "\u9009\u62e9\u6587\u4ef6",
            self.select_files,
            GREEN,
        )
        self.select_button.pack(side="left")

        self.clear_button = self._build_button(
            controls,
            "\u6e05\u7a7a\u5217\u8868",
            self.clear_files,
            BROWN,
        )
        self.clear_button.pack(side="left", padx=10)

        self.open_output_button = self._build_button(
            controls,
            "\u6253\u5f00\u8f93\u51fa\u6587\u4ef6\u5939",
            self.open_output_folder,
            BROWN,
        )
        self.open_output_button.pack(side="left")

        self.run_button = self._build_button(
            self.action_bar,
            "\u5f00\u59cb\u5236\u4f5c",
            self.start_processing,
            ORANGE,
            width=12,
            pady=10,
        )
        self.run_button.grid(row=0, column=1, sticky="e")

        self.list_label = tk.Label(
            self.main_frame,
            text="\u5f85\u5904\u7406\u6587\u4ef6",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=WINDOW_BG,
            fg=TEXT_DARK,
            anchor="w",
        )
        self.list_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.list_container = tk.Frame(
            self.main_frame,
            bg=LIST_BG,
            highlightbackground=MUTED_BORDER,
            highlightthickness=1,
        )
        self.list_container.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.list_container.columnconfigure(0, weight=1)
        self.list_container.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(
            self.list_container,
            selectmode=tk.EXTENDED,
            exportselection=False,
            font=("Consolas", 11),
            bg=LIST_BG,
            fg="#2E2A24",
            bd=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        scrollbar = tk.Scrollbar(self.list_container, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        self.info_label = tk.Label(
            self.main_frame,
            text=SIZE_TEXT,
            font=("Microsoft YaHei UI", 10),
            bg=WINDOW_BG,
            fg=TEXT_MID,
            anchor="w",
            justify="left",
        )
        self.info_label.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        self.status_label = tk.Label(
            self.main_frame,
            text="",
            font=("Microsoft YaHei UI", 10),
            bg=WINDOW_BG,
            fg=BROWN,
            anchor="w",
            justify="left",
        )
        self.status_label.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self.main_frame.bind("<Configure>", self._on_resize)

    def _build_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg_color: str,
        *,
        width: int | None = None,
        pady: int = 9,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=bg_color,
            fg="white",
            activebackground=bg_color,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=16,
            pady=pady,
            width=width,
            cursor="hand2",
        )

    def _drop_text(self) -> str:
        if DND_AVAILABLE:
            return DROP_TEXT_READY
        return DROP_TEXT_NO_DND

    def _register_drop_targets(self) -> None:
        if not DND_AVAILABLE:
            return

        for widget in (self.root, self.drop_frame, self.drop_label, self.file_listbox):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.on_drop)

    def _bind_drop_zone_clicks(self) -> None:
        for widget in (self.drop_frame, self.drop_label):
            widget.bind("<Button-1>", self._handle_drop_zone_click)
            widget.bind("<Enter>", self._highlight_drop_zone)
            widget.bind("<Leave>", self._reset_drop_zone)

    def _handle_drop_zone_click(self, _event: tk.Event) -> None:
        if not self.processing:
            self.select_files()

    def _highlight_drop_zone(self, _event: tk.Event) -> None:
        self.drop_frame.configure(bg=HOVER_BG)
        self.drop_label.configure(bg=HOVER_BG)

    def _reset_drop_zone(self, _event: tk.Event) -> None:
        self.drop_frame.configure(bg=CARD_BG)
        self.drop_label.configure(bg=CARD_BG)

    def _on_resize(self, _event: tk.Event) -> None:
        self._update_wraplengths()

    def _update_wraplengths(self) -> None:
        width = max(self.main_frame.winfo_width() - 40, 360)
        self.subtitle_label.configure(wraplength=width)
        self.info_label.configure(wraplength=width)
        self.status_label.configure(wraplength=width)

    def select_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="\u9009\u62e9\u56fe\u7247\u6587\u4ef6",
            filetypes=[
                (
                    "\u56fe\u7247\u6587\u4ef6",
                    "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp",
                ),
                ("\u6240\u6709\u6587\u4ef6", "*.*"),
            ],
        )
        self.add_files(file_paths)

    def on_drop(self, event: object) -> None:
        raw_paths = self.root.tk.splitlist(event.data)
        self.add_files(raw_paths)

    def add_files(self, file_paths: Iterable[str]) -> None:
        new_files: list[Path] = []
        rejected: list[str] = []

        for raw_path in file_paths:
            path = Path(raw_path)

            if is_supported_image(path):
                new_files.append(path.resolve())
                continue

            if path.is_dir():
                directory_images = [
                    candidate.resolve()
                    for candidate in sorted(path.iterdir())
                    if is_supported_image(candidate)
                ]
                if directory_images:
                    new_files.extend(directory_images)
                else:
                    rejected.append(path.name or str(path))
                continue

            rejected.append(path.name or raw_path)

        if new_files:
            merged = {str(path): path for path in self.selected_files}
            for path in new_files:
                merged[str(path)] = path
            self.selected_files = list(merged.values())
            self._refresh_listbox()

        self._refresh_ui_state(rejected)

    def clear_files(self) -> None:
        if not self.selected_files:
            return

        self.selected_files.clear()
        self._refresh_listbox()
        self._refresh_ui_state()

    def open_output_folder(self) -> None:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

        try:
            if hasattr(os, "startfile"):
                os.startfile(OUTPUT_ROOT)
            else:
                messagebox.showinfo(
                    "\u6253\u5f00\u8f93\u51fa\u6587\u4ef6\u5939",
                    f"\u8f93\u51fa\u6587\u4ef6\u5939\u4f4d\u7f6e\uff1a\n{OUTPUT_ROOT}",
                )
        except OSError as exc:
            messagebox.showerror(
                "\u6253\u5f00\u5931\u8d25",
                (
                    "\u65e0\u6cd5\u6253\u5f00\u8f93\u51fa\u6587\u4ef6\u5939\uff1a\n"
                    f"{OUTPUT_ROOT}\n\n{exc}"
                ),
            )

    def _refresh_listbox(self) -> None:
        self.file_listbox.delete(0, tk.END)
        for path in self.selected_files:
            self.file_listbox.insert(tk.END, str(path))

    def _refresh_ui_state(self, rejected: list[str] | None = None) -> None:
        if not PIL_AVAILABLE:
            message = (
                "Pillow \u4f9d\u8d56\u4e0d\u53ef\u7528\uff0c"
                "\u8bf7\u5148\u53cc\u51fb\u201c\u5b89\u88c5\u4f9d\u8d56.bat\u201d\u3002"
            )
            if PIL_IMPORT_ERROR:
                message += f"\n\u5bfc\u5165\u9519\u8bef\uff1a{PIL_IMPORT_ERROR}"
            self.status_label.config(text=message)
            self.run_button.config(state="disabled")
        elif self.processing:
            self.status_label.config(
                text="\u6b63\u5728\u5904\u7406\u56fe\u7247\uff0c\u8bf7\u7a0d\u5019..."
            )
            self.run_button.config(state="disabled", text="\u5236\u4f5c\u4e2d...")
        else:
            status_parts = []
            if self.selected_files:
                status_parts.append(
                    f"\u5df2\u9009\u62e9 {len(self.selected_files)} \u4e2a\u6587\u4ef6\u3002"
                )
                status_parts.append(f"\u8f93\u51fa\u4f4d\u7f6e\uff1a{OUTPUT_ROOT}")
            else:
                status_parts.append(
                    "\u8bf7\u9009\u62e9\u56fe\u7247\u6587\u4ef6\uff0c"
                    "\u6216\u5c06\u56fe\u7247\u62d6\u5230\u4e0a\u65b9\u533a\u57df\u3002"
                )

            if rejected:
                status_parts.append(
                    "\u4ee5\u4e0b\u6587\u4ef6\u672a\u52a0\u5165\uff1a"
                    + ", ".join(rejected[:4])
                )

            self.status_label.config(text="\n".join(status_parts))
            self.run_button.config(
                state=("normal" if self.selected_files else "disabled"),
                text="\u5f00\u59cb\u5236\u4f5c",
            )

        controls_state = "disabled" if self.processing else "normal"
        self.select_button.config(state=controls_state)
        self.clear_button.config(state=controls_state)
        self.open_output_button.config(state=controls_state)
        self.drop_label.config(text=self._drop_text())

    def start_processing(self) -> None:
        if not PIL_AVAILABLE:
            message = (
                "\u8bf7\u5148\u53cc\u51fb\u201c\u5b89\u88c5\u4f9d\u8d56.bat\u201d"
                "\u5b89\u88c5\u6240\u9700\u4f9d\u8d56\u3002"
            )
            if PIL_IMPORT_ERROR:
                message += f"\n\nPillow \u5bfc\u5165\u5931\u8d25\uff1a\n{PIL_IMPORT_ERROR}"
            messagebox.showerror(
                "\u7f3a\u5c11\u4f9d\u8d56",
                message,
            )
            return

        if not self.selected_files or self.processing:
            return

        self.processing = True
        self._refresh_ui_state()

        worker = threading.Thread(
            target=self._process_files_worker,
            args=(list(self.selected_files),),
            daemon=True,
        )
        worker.start()

    def _process_files_worker(self, file_paths: list[Path]) -> None:
        created_dirs: list[Path] = []
        failures: list[tuple[Path, str]] = []
        name_counter: dict[str, int] = {}

        for source_path in file_paths:
            try:
                folder_name = build_output_folder_name(source_path, name_counter)
                output_dir = OUTPUT_ROOT / folder_name
                convert_image_to_ico_set(source_path, output_dir)
                created_dirs.append(output_dir)
            except Exception as exc:
                failures.append((source_path, str(exc)))

        self.root.after(0, lambda: self._finish_processing(created_dirs, failures))

    def _finish_processing(
        self, created_dirs: list[Path], failures: list[tuple[Path, str]]
    ) -> None:
        self.processing = False
        self._refresh_ui_state()

        messages = []
        if created_dirs:
            shown_dirs = "\n".join(str(path) for path in created_dirs[:6])
            messages.append(
                f"\u5df2\u751f\u6210 {len(created_dirs)} "
                f"\u4e2a\u8f93\u51fa\u6587\u4ef6\u5939\uff1a\n{shown_dirs}"
            )
        if failures:
            shown_failures = "\n".join(
                f"{path.name}: {error}" for path, error in failures[:6]
            )
            messages.append(
                f"\u4ee5\u4e0b\u6587\u4ef6\u5904\u7406\u5931\u8d25\uff1a\n{shown_failures}"
            )

        if failures and not created_dirs:
            messagebox.showerror("\u5904\u7406\u5931\u8d25", "\n\n".join(messages))
        elif failures:
            messagebox.showwarning("\u5904\u7406\u5b8c\u6210", "\n\n".join(messages))
        else:
            messagebox.showinfo("\u5904\u7406\u5b8c\u6210", "\n\n".join(messages))


def create_root() -> tk.Tk:
    if DND_AVAILABLE:
        return TkinterDnD.Tk()
    return tk.Tk()


def show_fatal_error(exc: BaseException) -> None:
    error_log = APP_DIR / "error.log"
    error_log.write_text(traceback.format_exc(), encoding="utf-8")

    fallback_root = tk.Tk()
    fallback_root.withdraw()
    messagebox.showerror(
        "\u7a0b\u5e8f\u542f\u52a8\u5931\u8d25",
        (
            "\u7a0b\u5e8f\u542f\u52a8\u65f6\u53d1\u751f\u9519\u8bef\uff1a\n"
            f"{exc}\n\n"
            "\u8be6\u7ec6\u4fe1\u606f\u5df2\u5199\u5165\uff1a\n"
            f"{error_log}"
        ),
    )
    fallback_root.destroy()


def main() -> None:
    enable_windows_dpi_awareness()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    root = create_root()
    apply_tk_scaling(root)
    IconMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        show_fatal_error(exc)
