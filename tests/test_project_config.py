from pathlib import Path

import pytest
import yaml

from table_data_extraction.project_config import load_project_config


@pytest.fixture(autouse=True)
def clear_project_config_cache() -> None:
    load_project_config.cache_clear()
    yield
    load_project_config.cache_clear()


def _write_config(config_path: Path, data: dict[str, object]) -> None:
    config_path.write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


def _valid_config() -> dict[str, object]:
    return {
        "paths": {"output_dir": "output"},
        "plot": {
            "palette": [
                "#1718FE",
                "#D35400",
                "#128A0C",
                "#7A44F6",
                "#C0392B",
                "#008AA6",
                "#1B1F28",
                "#A61E4D",
            ],
            "defaults": {
                "x_column": "Time",
                "y_column": "Voltage",
            },
        },
        "csv": {
            "defaults": {
                "columns": [
                    "Time",
                    "Voltage",
                    "Current(mA)",
                    "Charge_Capacity(mAh)",
                    "Discharge_Capacity(mAh)",
                ],
            },
        },
        "comparison_table": {
            "extrema_detection": {
                "window_points": 9,
                "zero_threshold": 5.0,
                "min_zone_points": 5,
                "min_extrema_separation_points": 5,
            },
        },
    }


def test_load_project_config_reads_palette_and_defaults_without_labels() -> (
    None
):
    config = load_project_config()

    assert "source_file" not in config["paths"]
    assert config["paths"]["output_dir"] == "output"
    assert config["plot"]["palette"][:3] == ["#1718FE", "#D35400", "#128A0C"]
    assert config["plot"]["defaults"]["x_column"] == "Time"
    assert config["plot"]["defaults"]["y_column"] == "Voltage"
    assert config["csv"]["defaults"]["columns"] == [
        "Time",
        "Voltage",
        "Current(mA)",
        "Charge_Capacity(mAh)",
        "Discharge_Capacity(mAh)",
    ]
    assert config["comparison_table"]["extrema_detection"] == {
        "window_points": 9,
        "zero_threshold": 5.0,
        "min_zone_points": 5,
        "min_extrema_separation_points": 5,
    }
    assert "labels" not in config


def test_load_project_config_resolves_root_config_path() -> None:
    config = load_project_config()

    config_path = Path(config["_meta"]["config_path"])
    expected_path = Path(__file__).resolve().parents[1] / "project_config.yaml"

    assert config_path == expected_path
    assert config_path.name == "project_config.yaml"
    assert config_path.is_file()


def test_load_project_config_returns_isolated_copy_per_call() -> None:
    first = load_project_config()
    first["plot"]["defaults"]["x_column"] = "Mutated"
    first["csv"]["defaults"]["columns"].append("Injected")

    second = load_project_config()

    assert second is not first
    assert second["plot"]["defaults"]["x_column"] == "Time"
    assert second["csv"]["defaults"]["columns"] == [
        "Time",
        "Voltage",
        "Current(mA)",
        "Charge_Capacity(mAh)",
        "Discharge_Capacity(mAh)",
    ]


@pytest.mark.parametrize(
    ("mutate", "expected_message"),
    [
        (
            lambda config: config["plot"].pop("palette"),
            r"plot\.palette",
        ),
        (
            lambda config: config["paths"].pop("output_dir"),
            r"paths\.output_dir",
        ),
        (
            lambda config: config["plot"].pop("defaults"),
            r"plot\.defaults",
        ),
        (
            lambda config: config["plot"]["defaults"].pop("x_column"),
            r"plot\.defaults\.x_column",
        ),
        (
            lambda config: config["plot"]["defaults"].pop("y_column"),
            r"plot\.defaults\.y_column",
        ),
        (
            lambda config: config["csv"]["defaults"].pop("columns"),
            r"csv\.defaults\.columns",
        ),
        (
            lambda config: config.pop("comparison_table"),
            r"comparison_table",
        ),
        (
            lambda config: config["comparison_table"].pop("extrema_detection"),
            r"comparison_table\.extrema_detection",
        ),
        (
            lambda config: config["comparison_table"]["extrema_detection"].pop(
                "window_points"
            ),
            r"comparison_table\.extrema_detection\.window_points",
        ),
        (
            lambda config: config["comparison_table"]["extrema_detection"].pop(
                "zero_threshold"
            ),
            r"comparison_table\.extrema_detection\.zero_threshold",
        ),
        (
            lambda config: config["comparison_table"]["extrema_detection"].pop(
                "min_zone_points"
            ),
            r"comparison_table\.extrema_detection\.min_zone_points",
        ),
        (
            lambda config: config["comparison_table"]["extrema_detection"].pop(
                "min_extrema_separation_points"
            ),
            r"comparison_table\.extrema_detection\.min_extrema_separation_points",
        ),
    ],
)
def test_load_project_config_fails_fast_for_missing_nested_required_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: object,
    expected_message: str,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    mutate(config)
    config_path = tmp_path / "project_config.yaml"
    _write_config(config_path, config)

    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    with pytest.raises(KeyError, match=expected_message):
        project_config_module.load_project_config()


@pytest.mark.parametrize(
    ("mutate", "expected_message"),
    [
        (
            lambda config: config["plot"].__setitem__("palette", "not-a-list"),
            r"plot\.palette",
        ),
        (
            lambda config: config["plot"].__setitem__("defaults", []),
            r"plot\.defaults",
        ),
        (
            lambda config: config["plot"]["defaults"].__setitem__(
                "x_column", ["Time"]
            ),
            r"plot\.defaults\.x_column",
        ),
        (
            lambda config: config["plot"]["defaults"].__setitem__(
                "y_column", {"name": "Voltage"}
            ),
            r"plot\.defaults\.y_column",
        ),
        (
            lambda config: config["paths"].__setitem__(
                "output_dir", {"value": "output"}
            ),
            r"paths\.output_dir",
        ),
        (
            lambda config: config.__setitem__("comparison_table", []),
            r"comparison_table",
        ),
        (
            lambda config: config["comparison_table"].__setitem__(
                "extrema_detection", []
            ),
            r"comparison_table\.extrema_detection",
        ),
    ],
)
def test_load_project_config_rejects_wrong_shape_for_required_plot_label_and_path_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: object,
    expected_message: str,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    mutate(config)
    config_path = tmp_path / "project_config.yaml"
    _write_config(config_path, config)

    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    with pytest.raises(ValueError, match=expected_message):
        project_config_module.load_project_config()


@pytest.mark.parametrize(
    ("mutate", "expected_message"),
    [
        (
            lambda config: config["plot"].__setitem__(
                "palette", ["#1718FE", 42]
            ),
            r"plot\.palette",
        ),
        (
            lambda config: config["csv"]["defaults"].__setitem__(
                "columns", ["Time", 42]
            ),
            r"csv\.defaults\.columns",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("window_points", 2),
            r"comparison_table\.extrema_detection\.window_points",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("window_points", 4),
            r"comparison_table\.extrema_detection\.window_points",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("window_points", "9"),
            r"comparison_table\.extrema_detection\.window_points",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("zero_threshold", -1.0),
            r"comparison_table\.extrema_detection\.zero_threshold",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("min_zone_points", 0),
            r"comparison_table\.extrema_detection\.min_zone_points",
        ),
        (
            lambda config: config["comparison_table"][
                "extrema_detection"
            ].__setitem__("min_extrema_separation_points", False),
            r"comparison_table\.extrema_detection\.min_extrema_separation_points",
        ),
    ],
)
def test_load_project_config_rejects_non_string_container_members(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: object,
    expected_message: str,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    mutate(config)
    config_path = tmp_path / "project_config.yaml"
    _write_config(config_path, config)

    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    with pytest.raises(ValueError, match=expected_message):
        project_config_module.load_project_config()


def test_load_project_config_accepts_config_without_labels_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config_path = tmp_path / "project_config.yaml"
    _write_config(
        config_path,
        {
            "paths": _valid_config()["paths"],
            "plot": _valid_config()["plot"],
            "csv": _valid_config()["csv"],
            "comparison_table": _valid_config()["comparison_table"],
        },
    )
    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    config = project_config_module.load_project_config()

    assert "labels" not in config


def test_load_project_config_raises_for_missing_config_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config_path = tmp_path / "project_config.yaml"
    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    with pytest.raises(FileNotFoundError):
        project_config_module.load_project_config()


def test_load_project_config_raises_for_malformed_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from table_data_extraction import project_config as project_config_module

    config_path = tmp_path / "project_config.yaml"
    config_path.write_text(
        """
paths: [examples/example1_1.ndax, output
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)

    with pytest.raises(yaml.YAMLError):
        project_config_module.load_project_config()


def test_config_module_exports_values_from_yaml_loader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import importlib

    from table_data_extraction import config as config_module
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    config["paths"]["output_dir"] = "artifacts"
    config["plot"]["defaults"]["x_column"] = "Cycle"
    config["plot"]["defaults"]["y_column"] = "Current(mA)"
    config["csv"]["defaults"]["columns"] = ["Cycle", "Current(mA)"]

    with monkeypatch.context() as context:
        context.setattr(project_config_module, "ROOT_DIR", tmp_path)
        context.setattr(
            project_config_module, "load_project_config", lambda: config
        )

        importlib.reload(config_module)

        assert config_module.ROOT_DIR == tmp_path
        assert config_module.OUTPUT_DIR == tmp_path / "artifacts"
        assert not hasattr(config_module, "PLOT_OUTPUT")
        assert not hasattr(config_module, "CSV_OUTPUT")
        assert config_module.PLOT_X_COLUMN == "Cycle"
        assert config_module.PLOT_Y_COLUMN == "Current(mA)"
        assert isinstance(config_module.CSV_COLUMNS, list)
        assert config_module.CSV_COLUMNS == ["Cycle", "Current(mA)"]
        assert config_module.EXTREMA_WINDOW_POINTS == 9
        assert config_module.EXTREMA_ZERO_THRESHOLD == 5.0
        assert config_module.MIN_ZONE_POINTS == 5
        assert config_module.MIN_EXTREMA_SEPARATION_POINTS == 5
        assert not hasattr(config_module, "AXIS_LABEL_OVERRIDES")

    importlib.reload(config_module)


def test_config_module_does_not_export_source_file() -> None:
    import table_data_extraction.config as config_module

    assert not hasattr(config_module, "SOURCE_FILE")


def test_config_module_exports_read_only_snapshots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import importlib

    from table_data_extraction import config as config_module
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    config["paths"]["output_dir"] = "artifacts"
    config["csv"]["defaults"]["columns"] = ["Cycle", "Current(mA)"]

    with monkeypatch.context() as context:
        context.setattr(project_config_module, "ROOT_DIR", tmp_path)
        context.setattr(
            project_config_module, "load_project_config", lambda: config
        )

        importlib.reload(config_module)

        with pytest.raises(TypeError):
            config_module.CSV_COLUMNS.append("Injected")

        config["csv"]["defaults"]["columns"].append("Injected")

        assert config_module.CSV_COLUMNS == ["Cycle", "Current(mA)"]

    importlib.reload(config_module)


def test_plot_style_palette_is_loaded_from_yaml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    from table_data_extraction import plot_style as plot_style_module
    from table_data_extraction import project_config as project_config_module

    config = _valid_config()
    config["plot"]["palette"] = [
        "#111111",
        "#222222",
        "#333333",
        "#444444",
        "#555555",
        "#666666",
        "#777777",
        "#888888",
    ]

    with monkeypatch.context() as context:
        context.setattr(
            project_config_module, "load_project_config", lambda: config
        )

        importlib.reload(plot_style_module)

        assert plot_style_module.PLOT_COLOR_PALETTE == tuple(
            config["plot"]["palette"]
        )
        assert plot_style_module.resolve_plot_colors(0) == []
        assert plot_style_module.resolve_plot_colors(3) == [
            "#111111",
            "#222222",
            "#333333",
        ]

    importlib.reload(plot_style_module)
