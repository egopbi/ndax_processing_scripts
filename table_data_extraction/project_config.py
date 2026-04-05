from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, TypeAlias

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "project_config.yaml"

ConfigPath = tuple[str, ...]
SchemaValidator: TypeAlias = Callable[[Any, ConfigPath], None]
SchemaNode: TypeAlias = dict[str, "SchemaNode"] | SchemaValidator


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _format_path(path: ConfigPath) -> str:
    return ".".join(path)


def _raise_expected_mapping(path: ConfigPath) -> None:
    if not path:
        raise ValueError(
            "project_config.yaml must contain a top-level mapping."
        )
    raise ValueError(
        f"Config section '{_format_path(path)}' must be a mapping."
    )


def _validate_string(value: Any, path: ConfigPath) -> None:
    if not isinstance(value, str):
        raise ValueError(
            f"Config key '{_format_path(path)}' must be a string."
        )


def _validate_string_list(value: Any, path: ConfigPath) -> None:
    if not isinstance(value, list):
        raise ValueError(f"Config key '{_format_path(path)}' must be a list.")

    for item in value:
        if not isinstance(item, str):
            raise ValueError(
                f"Config key '{_format_path(path)}' must contain only strings."
            )


def _validate_string_mapping(value: Any, path: ConfigPath) -> None:
    if not isinstance(value, dict):
        raise ValueError(
            f"Config key '{_format_path(path)}' must be a mapping."
        )

    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(
                f"Config key '{_format_path(path)}' must contain only string keys and string values."
            )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_positive_int(value: Any, path: ConfigPath) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(
            f"Config key '{_format_path(path)}' must be a positive integer."
        )


def _validate_odd_window_points(value: Any, path: ConfigPath) -> None:
    _validate_positive_int(value, path)
    if value < 3 or value % 2 == 0:
        raise ValueError(
            f"Config key '{_format_path(path)}' must be an odd integer >= 3."
        )


def _validate_non_negative_number(value: Any, path: ConfigPath) -> None:
    if not _is_number(value) or value < 0:
        raise ValueError(
            f"Config key '{_format_path(path)}' must be a non-negative number."
        )


def _validate_axis_limits(value: Any, path: ConfigPath) -> None:
    if value is None:
        return
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(
            f"Config key '{_format_path(path)}' must be null or a two-item sequence."
        )

    for item in value:
        if item is not None and not _is_number(item):
            raise ValueError(
                f"Config key '{_format_path(path)}' must contain only numbers or null."
            )


def _validate_schema(
    value: Any, schema: SchemaNode, path: ConfigPath = ()
) -> None:
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            _raise_expected_mapping(path)

        for key, child_schema in schema.items():
            child_path = (*path, key)
            if key not in value:
                raise KeyError(
                    f"Missing required config key: {_format_path(child_path)}"
                )
            _validate_schema(value[key], child_schema, child_path)
        return

    schema(value, path)


_CONFIG_SCHEMA: SchemaNode = {
    "paths": {
        "output_dir": _validate_string,
    },
    "plot": {
        "palette": _validate_string_list,
        "defaults": {
            "x_column": _validate_string,
            "y_column": _validate_string,
            "x_limits": _validate_axis_limits,
            "y_limits": _validate_axis_limits,
        },
    },
    "csv": {
        "defaults": {
            "columns": _validate_string_list,
        },
    },
    "comparison_table": {
        "extrema_detection": {
            "window_points": _validate_odd_window_points,
            "zero_threshold": _validate_non_negative_number,
            "min_zone_points": _validate_positive_int,
            "min_extrema_separation_points": _validate_positive_int,
        },
    },
}


@lru_cache(maxsize=1)
def _load_project_config_cached() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        loaded = yaml.safe_load(file)

    _validate_schema(loaded, _CONFIG_SCHEMA)

    normalized = _normalize(loaded)
    normalized["_meta"] = {
        "config_path": str(CONFIG_PATH),
        "root_dir": str(ROOT_DIR),
    }
    return normalized


def load_project_config() -> dict[str, Any]:
    return deepcopy(_load_project_config_cached())


load_project_config.cache_clear = _load_project_config_cached.cache_clear  # type: ignore[attr-defined]
