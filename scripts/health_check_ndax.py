from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.config import CSV_COLUMNS, PLOT_X_COLUMN, PLOT_Y_COLUMN, SOURCE_FILE
from table_data_extraction.health import format_health_check_report, run_health_check


def main() -> int:
    plot_columns = [PLOT_X_COLUMN, PLOT_Y_COLUMN]
    required_columns = [*plot_columns, *CSV_COLUMNS]

    try:
        result = run_health_check(SOURCE_FILE, required_columns=required_columns)
    except Exception as error:
        print(f"Health check failed: {error}", file=sys.stderr)
        return 1

    print(
        format_health_check_report(
            result,
            plot_columns=plot_columns,
            csv_columns=CSV_COLUMNS,
        )
    )
    return 1 if result.missing_columns else 0


if __name__ == "__main__":
    raise SystemExit(main())
