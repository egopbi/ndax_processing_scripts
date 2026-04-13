from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RunMode = Literal["plot", "table", "convert", "health-check"]


@dataclass(frozen=True)
class PlotRunConfig:
    files: tuple[Path, ...]
    y_column: str
    x_column: str = "Time"
    labels: tuple[str, ...] | None = None
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None
    separate: bool = False
    output_path: Path | None = None


@dataclass(frozen=True)
class TableRunConfig:
    files: tuple[Path, ...]
    y_column: str
    anchor_x: tuple[float, ...]
    x_column: str = "Time"
    labels: tuple[str, ...] | None = None
    output_path: Path | None = None


@dataclass(frozen=True)
class ConvertRunConfig:
    files: tuple[Path, ...]
    columns: tuple[str, ...]


@dataclass(frozen=True)
class HealthCheckRunConfig:
    file: Path


@dataclass(frozen=True)
class SubprocessCommand:
    mode: RunMode
    argv: tuple[str, ...]
    cwd: Path
    output_path: Path | None = None


@dataclass(frozen=True)
class StreamChunk:
    stream: Literal["stdout", "stderr"]
    text: str


@dataclass(frozen=True)
class CompletedCommand:
    command: SubprocessCommand
    returncode: int
    stdout: str
    stderr: str
    was_cancelled: bool = False
