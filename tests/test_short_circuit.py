import importlib
import importlib.util

import pandas as pd
import pytest


def _import_short_circuit_module():
    spec = importlib.util.find_spec("table_data_extraction.short_circuit")
    assert spec is not None, "table_data_extraction.short_circuit must exist"
    return importlib.import_module("table_data_extraction.short_circuit")


def _build_raw_dataframe(
    hours: list[float],
    voltage_mv: list[float],
    *,
    include_timestamp: bool,
) -> pd.DataFrame:
    timestamps = [
        pd.Timestamp("2026-01-01 00:00:00") + pd.to_timedelta(hour, unit="h")
        for hour in [0.0, *hours]
    ]
    dataframe = pd.DataFrame({
        "Status": ["Rest", *(["CC_DChg"] * len(hours))],
        "Time": [0.0, *[hour * 3600 for hour in hours]],
        "Voltage": [0.0, *[value / 1000 for value in voltage_mv]],
    })
    if include_timestamp:
        dataframe["Timestamp"] = [
            timestamp.isoformat(sep=" ") for timestamp in timestamps
        ]
    return dataframe


def _build_waveform_dataframe(
    amplitudes_by_bin: dict[int, float],
    *,
    threshold_peak_hour: int | None = None,
) -> pd.DataFrame:
    hours = list(range(40))
    phase_pattern = [0.0, 0.5, -0.5, 0.5, 0.0]
    voltage_mv = [
        amplitudes_by_bin[(hour // 5) * 5] * phase_pattern[hour % 5]
        for hour in hours
    ]
    if threshold_peak_hour is not None:
        voltage_mv[threshold_peak_hour] = 220.0
    return _build_raw_dataframe(hours, voltage_mv, include_timestamp=False)


def _build_mixed_timestamp_dataframe() -> pd.DataFrame:
    timestamps = [
        "2026-01-01 00:00:00",
        "01/01/2026 01:00:00",
        "January 1, 2026 06:00:00",
        "2026-01-01T11:00:00",
        "2026/01/01 16:00:00",
        "Jan 01 2026 21:00:00",
        "2026-01-02 02:00:00",
        "01/02/2026 07:00:00",
    ]
    return pd.DataFrame({
        "Status": ["Rest", *(["CC_DChg"] * 7)],
        "Time": [
            0.0,
            3600.0,
            21600.0,
            39600.0,
            57600.0,
            75600.0,
            93600.0,
            111600.0,
        ],
        "Voltage": [0.0, 0.0, 0.1, 0.22, 0.1, 0.0, 0.1, 0.0],
        "Timestamp": timestamps,
    })


def test_detect_short_circuit_time_hours_returns_threshold_event_time() -> (
    None
):
    module = _import_short_circuit_module()
    dataframe = _build_raw_dataframe(
        hours=[1, 6, 11, 16, 21, 26, 31],
        voltage_mv=[0, 100, 220, 100, 0, 100, 0],
        include_timestamp=True,
    )

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected == pytest.approx(5.0)


def test_detect_short_circuit_time_hours_handles_mixed_timestamp_formats() -> (
    None
):
    module = _import_short_circuit_module()
    dataframe = _build_mixed_timestamp_dataframe()

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected == pytest.approx(5.0)


def test_detect_short_circuit_time_hours_ignores_long_startup_tail() -> None:
    module = _import_short_circuit_module()
    dataframe = _build_raw_dataframe(
        hours=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        voltage_mv=[-300, -250, -200, -150, -100, -50, -60, 220, 0],
        include_timestamp=True,
    )

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected == pytest.approx(1.0)


def test_detect_short_circuit_time_hours_returns_collapse_bin_start() -> None:
    module = _import_short_circuit_module()
    dataframe = _build_waveform_dataframe({
        0: 120.0,
        5: 120.0,
        10: 120.0,
        15: 120.0,
        20: 70.0,
        25: 40.0,
        30: 40.0,
        35: 40.0,
    })

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected == pytest.approx(15.0)


def test_detect_short_circuit_time_hours_prefers_earlier_candidate_when_both_fire() -> (
    None
):
    module = _import_short_circuit_module()
    dataframe = _build_waveform_dataframe(
        {
            0: 120.0,
            5: 120.0,
            10: 120.0,
            15: 120.0,
            20: 70.0,
            25: 40.0,
            30: 40.0,
            35: 40.0,
        },
        threshold_peak_hour=11,
    )

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected == pytest.approx(11.0)


def test_detect_short_circuit_time_hours_returns_none_without_threshold_or_collapse() -> (
    None
):
    module = _import_short_circuit_module()
    dataframe = _build_waveform_dataframe({
        0: 120.0,
        5: 120.0,
        10: 120.0,
        15: 120.0,
        20: 120.0,
        25: 120.0,
        30: 120.0,
        35: 120.0,
    })

    detected = module.detect_short_circuit_time_hours(dataframe)

    assert detected is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (180.0, 180),
        (182.0, 180),
        (182.5, 185),
        (183.0, 185),
        (177.5, 180),
    ],
)
def test_round_short_circuit_hours_rounds_to_nearest_five_half_up(
    value: float | None, expected: int | None
) -> None:
    module = _import_short_circuit_module()

    rounded = module.round_short_circuit_hours(value)

    assert rounded == expected
