from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "ICO_Maker"
ICON_FILE = BASE_DIR / "output" / "poker" / "256x256.ico"
DIST_DIR = BASE_DIR / "dist"
WORK_DIR = BASE_DIR / "build" / "pyinstaller"
SPEC_FILE = BASE_DIR / f"{APP_NAME}.spec"
SCRIPT_FILE = BASE_DIR / "ico_maker_gui.pyw"


def remove_if_exists(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def main() -> int:
    remove_if_exists(WORK_DIR)
    remove_if_exists(DIST_DIR / f"{APP_NAME}.exe")
    remove_if_exists(SPEC_FILE)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(WORK_DIR),
        "--specpath",
        str(BASE_DIR),
        "--collect-all",
        "tkinterdnd2",
        "--hidden-import=PIL._tkinter_finder",
    ]

    if ICON_FILE.exists():
        command.extend(["--icon", str(ICON_FILE)])
    else:
        print(f"Icon file not found: {ICON_FILE}")
        print("Building without a custom exe icon.")

    command.append(str(SCRIPT_FILE))

    print("Running build command:")
    print(" ".join(f'"{part}"' if " " in part else part for part in command))

    completed = subprocess.run(command, cwd=BASE_DIR)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
