from __future__ import annotations

from pathlib import Path

import pandas as pd

from rispacs_demo.contracts import load_contract, validate_contract
from rispacs_demo.quality import quality_summary


def main() -> None:
    data_path = Path("data/demo_radiology.parquet")
    if not data_path.exists():
        raise SystemExit("Generate demo data first: python scripts/generate_demo_data.py")

    df = pd.read_parquet(data_path)
    contract = load_contract("config/data_contract.yml")
    result = validate_contract(df, contract)
    print("Contract:", result)
    print("Quality checks:")
    print(quality_summary(df).to_string(index=False))


if __name__ == "__main__":
    main()
