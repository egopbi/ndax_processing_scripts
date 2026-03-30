from pathlib import Path


def sample_ndax_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "example_1.ndax"
