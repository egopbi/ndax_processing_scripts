from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from tkinter import Tk
from typing import TypeVar

ResultT = TypeVar("ResultT")


def _with_hidden_root(callback: Callable[[], ResultT]) -> ResultT:
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return callback()
    finally:
        root.destroy()


def choose_ndax_files(
    *, initial_dir: str | Path | None = None
) -> tuple[Path, ...]:
    initial_directory = (
        str(Path(initial_dir)) if initial_dir is not None else None
    )
    selected = _with_hidden_root(
        lambda: filedialog.askopenfilenames(
            title="Select NDAX files",
            filetypes=(("NDAX files", "*.ndax"), ("All files", "*.*")),
            initialdir=initial_directory,
        )
    )
    return tuple(Path(path) for path in selected)


def choose_output_directory(
    *, initial_dir: str | Path | None = None
) -> Path | None:
    initial_directory = (
        str(Path(initial_dir)) if initial_dir is not None else None
    )
    selected = _with_hidden_root(
        lambda: filedialog.askdirectory(
            title="Select output directory",
            initialdir=initial_directory,
            mustexist=True,
        )
    )
    if not selected:
        return None
    return Path(selected)
