from rispacs_demo.contracts import load_contract, validate_contract
from rispacs_demo.synthetic import DemoSpec, generate_demo_dataset


def test_contract_warns_on_unknown_modality():
    df = generate_demo_dataset(DemoSpec(rows=2000, seed=13))
    contract = load_contract("config/data_contract.yml")
    result = validate_contract(df, contract)
    assert result["status"] == "WARN"
    assert not result["missing_columns"]
