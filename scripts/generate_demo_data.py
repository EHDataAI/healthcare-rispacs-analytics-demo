from __future__ import annotations

import argparse
from pathlib import Path

from rispacs_demo.synthetic import DemoSpec, write_demo_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic RIS/PACS demo data")
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260928)
    parser.add_argument("--output", default="data/demo_radiology.parquet")
    args = parser.parse_args()

    path = write_demo_dataset(Path(args.output), DemoSpec(rows=args.rows, seed=args.seed))
    print(f"Generated: {path}")


if __name__ == "__main__":
    main()
