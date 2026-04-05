from pathlib import Path

import pandas as pd
import pytest

from table_data_extraction import extrema as extrema_module
from table_data_extraction.columns import resolve_column_name
from table_data_extraction.preprocess import prepare_x_series, trim_leading_rest_rows
from table_data_extraction.reader import load_ndax_dataframe


def _configure_detection(
    monkeypatch: pytest.MonkeyPatch,
    *,
    window_points: int = 3,
    zero_threshold: float = 0.5,
    min_zone_points: int = 3,
    min_extrema_separation_points: int = 1,
) -> None:
    monkeypatch.setattr(
        extrema_module,
        "EXTREMA_WINDOW_POINTS",
        window_points,
        raising=False,
    )
    monkeypatch.setattr(
        extrema_module,
        "EXTREMA_ZERO_THRESHOLD",
        zero_threshold,
        raising=False,
    )
    monkeypatch.setattr(
        extrema_module,
        "MIN_ZONE_POINTS",
        min_zone_points,
        raising=False,
    )
    monkeypatch.setattr(
        extrema_module,
        "MIN_EXTREMA_SEPARATION_POINTS",
        min_extrema_separation_points,
        raising=False,
    )


def test_find_six_extrema_indices_returns_expected_points_for_anchor_between_positive_and_negative_zones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_detection(monkeypatch)
    x_series = pd.Series(range(15), dtype=float)
    y_series = pd.Series(
        [0, 1, 4, 2, 5, 1, 0, -1, -4, -2, -5, -1, 0, 0, 0], dtype=float
    )

    result = extrema_module.find_six_extrema_indices(
        x_series, y_series, anchor_x=6.0
    )

    assert result == {
        "+U_l": 2,
        "+U_m": 3,
        "+U_r": 4,
        "-U_l": 8,
        "-U_m": 9,
        "-U_r": 10,
    }


def test_find_six_extrema_indices_uses_anchor_inside_negative_zone_to_pick_previous_positive_zone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_detection(monkeypatch)
    x_series = pd.Series(range(19), dtype=float)
    y_series = pd.Series(
        [
            0,
            1,
            4,
            2,
            5,
            1,
            0,
            -1,
            -4,
            -2,
            -5,
            -1,
            0,
            1,
            3,
            1,
            -1,
            -3,
            -1,
        ],
        dtype=float,
    )

    result = extrema_module.find_six_extrema_indices(
        x_series, y_series, anchor_x=9.0
    )

    assert result == {
        "+U_l": 2,
        "+U_m": 3,
        "+U_r": 4,
        "-U_l": 8,
        "-U_m": 9,
        "-U_r": 10,
    }


def test_find_six_extrema_indices_returns_none_when_no_positive_negative_pair_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_detection(monkeypatch)
    x_series = pd.Series([0, 1, 2, 3, 4, 5], dtype=float)
    y_series = pd.Series([0, 1, 2, 3, 4, 5], dtype=float)

    result = extrema_module.find_six_extrema_indices(
        x_series, y_series, anchor_x=2.5
    )

    assert result == {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }


def test_find_six_extrema_indices_ignores_small_noisy_wiggles_with_windowed_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_detection(
        monkeypatch,
        window_points=5,
        zero_threshold=0.5,
        min_zone_points=3,
        min_extrema_separation_points=1,
    )
    x_series = pd.Series(range(25), dtype=float)
    y_series = pd.Series(
        [
            0.0,
            0.5,
            4.0,
            3.8,
            5.0,
            0.6,
            0.2,
            -0.3,
            -0.6,
            -4.0,
            -3.8,
            -5.0,
            -0.4,
            0.0,
            0.1,
            0.2,
            0.0,
            -0.1,
            0.0,
            0.1,
            0.0,
            0.0,
            0.1,
            0.0,
            0.0,
        ],
        dtype=float,
    )

    result = extrema_module.find_six_extrema_indices(
        x_series, y_series, anchor_x=10.0
    )

    assert result == {
        "+U_l": 2,
        "+U_m": 3,
        "+U_r": 4,
        "-U_l": 9,
        "-U_m": 10,
        "-U_r": 11,
    }


def test_find_six_extrema_indices_respects_min_extrema_separation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_detection(
        monkeypatch,
        window_points=3,
        zero_threshold=0.5,
        min_zone_points=3,
        min_extrema_separation_points=2,
    )
    x_series = pd.Series(range(9), dtype=float)
    y_series = pd.Series(
        [0.0, 5.0, 1.0, 6.0, 0.0, -5.0, -1.0, -6.0, 0.0], dtype=float
    )

    result = extrema_module.find_six_extrema_indices(
        x_series, y_series, anchor_x=4.5
    )

    assert result == {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }


def test_find_six_extrema_indices_matches_example_4_with_approximate_anchor() -> (
    None
):
    path = Path(__file__).resolve().parents[1] / "examples" / "example4_4.ndax"
    dataframe = load_ndax_dataframe(path)
    trimmed = trim_leading_rest_rows(dataframe)
    x_series = prepare_x_series(trimmed, resolve_column_name(trimmed, "Time"))
    y_series = trimmed[resolve_column_name(trimmed, "Voltage")] * 1000

    result = extrema_module.find_six_extrema_indices(
        x_series=x_series,
        y_series=y_series,
        anchor_x=47.0 * 3600,
    )
    values = {
        label: round(float(y_series.iloc[index]), 1)
        for label, index in result.items()
        if index is not None
    }

    assert values == {
        "+U_l": 81.9,
        "+U_m": 31.8,
        "+U_r": 87.3,
        "-U_l": -70.5,
        "-U_m": -25.8,
        "-U_r": -81.4,
    }
