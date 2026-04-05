from pathlib import Path


def sample_ndax_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "example1_1.ndax"
