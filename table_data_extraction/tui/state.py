from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from table_data_extraction.tui.models import RunMode


@dataclass
class AppSessionState:
    active_mode: RunMode = "plot"
    output_dir: Path | None = None
    last_output_path: Path | None = None
    last_command_preview: str = ""
    is_running: bool = False
