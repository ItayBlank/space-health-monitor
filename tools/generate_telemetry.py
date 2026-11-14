"""Regenerate the packaged, deterministic ten-minute fictional recording."""
from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hal2030.config import DATA_PATH
from hal2030.telemetry import generate_dataset


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DATA_PATH)
    args = parser.parse_args()
    output = generate_dataset(args.output)
    print(f"Generated 3,600 fictional records: 6 crew × 600 seconds.\n{output}")
