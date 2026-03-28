from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT_DIR / "example_1.ndax"
OUTPUT_DIR = ROOT_DIR / "output"
PLOT_OUTPUT = OUTPUT_DIR / "poc_plot.jpg"
CSV_OUTPUT = OUTPUT_DIR / "poc_table.csv"

PLOT_X_COLUMN = "Time"
PLOT_Y_COLUMN = "Voltage"
CSV_COLUMNS = [
    "Time",
    "Voltage",
    "Current(mA)",
    "Charge_Capacity(mAh)",
    "Discharge_Capacity(mAh)",
]

X_LIMITS = None
Y_LIMITS = None

AXIS_LABEL_OVERRIDES = {
    "Time": "Time (s)",
    "Voltage": "Voltage (V)",
    "Current(mA)": "Current (mA)",
    "Charge_Capacity(mAh)": "Charge Capacity (mAh)",
    "Discharge_Capacity(mAh)": "Discharge Capacity (mAh)",
    "Charge_Energy(mWh)": "Charge Energy (mWh)",
    "Discharge_Energy(mWh)": "Discharge Energy (mWh)",
}
