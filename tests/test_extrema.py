import pandas as pd

from table_data_extraction.extrema import find_six_extrema_indices


def test_find_six_extrema_indices_returns_expected_points_for_synthetic_curve() -> (
    None
):
    x_series = pd.Series(range(17), dtype=float)
    y_series = pd.Series(
        [1, 3, 2, 4, 3, 5, 4, 6, 5, 4, 5, 3, 4, 2, 3, 1, 2], dtype=float
    )

    result = find_six_extrema_indices(x_series, y_series, anchor_x=8.4)

    assert result == {
        "+U_l": 5,
        "+U_m": 6,
        "+U_r": 7,
        "-U_l": 9,
        "-U_m": 10,
        "-U_r": 11,
    }


def test_find_six_extrema_indices_returns_none_when_points_are_missing() -> (
    None
):
    x_series = pd.Series([0, 1, 2, 3, 4, 5], dtype=float)
    y_series = pd.Series([0, 1, 2, 3, 4, 5], dtype=float)

    result = find_six_extrema_indices(x_series, y_series, anchor_x=2.5)

    assert result == {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }


def test_find_six_extrema_indices_uses_nearest_x_for_anchor() -> None:
    x_series = pd.Series([0.0, 1.0, 2.0, 10.0, 20.0, 30.0, 40.0], dtype=float)
    y_series = pd.Series([0.0, 2.0, 1.0, 0.0, 1.0, 0.0, 1.0], dtype=float)

    result = find_six_extrema_indices(x_series, y_series, anchor_x=9.0)

    assert result["-U_l"] == 5
    assert result["+U_r"] == 1


def test_find_six_extrema_indices_prefers_first_plateau_point_in_search_direction() -> (
    None
):
    x_series = pd.Series(range(9), dtype=float)
    y_series = pd.Series(
        [0.0, 1.0, 0.0, 1.0, 3.0, 3.0, 1.0, 0.0, 1.0], dtype=float
    )

    result = find_six_extrema_indices(x_series, y_series, anchor_x=7.0)

    assert result["+U_r"] == 5
