from __future__ import annotations

from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main(argv: Sequence[str] | None = None) -> int:
    try:
        from table_data_extraction.tui.app import main as tui_main
    except ModuleNotFoundError as error:
        missing_module = getattr(error, "name", None)
        if missing_module not in {
            "table_data_extraction.tui",
            "table_data_extraction.tui.app",
        }:
            raise
        print(
            (
                "NDAX TUI is not available yet. "
                "The future UI entrypoint will live in "
                "table_data_extraction.tui.app."
            ),
            file=sys.stderr,
        )
        if missing_module != "table_data_extraction.tui.app":
            print(f"Import error: {error}", file=sys.stderr)
        return 1

    return tui_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
