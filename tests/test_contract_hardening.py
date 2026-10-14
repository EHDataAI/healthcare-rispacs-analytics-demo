from rispacs_demo.contracts import load_contract, validate_contract
from rispacs_demo.synthetic import DemoSpec, generate_demo_dataset

ALLOWED_MODALITIES = [
    "CT",
    "MR",
    "US",
    "CR",
    "DX",
]


def _known_domain_frame(
    seed: int,
):
    df = generate_demo_dataset(
        DemoSpec(
            rows=3000,
            seed=seed,
        )
    )

    return df[df["modality"].isin(ALLOWED_MODALITIES)].copy()


def test_hardened_contract_passes_known_domain_and_types():
    df = _known_domain_frame(seed=801)

    contract = load_contract("config/data_contract.yml")

    result = validate_contract(
        df,
        contract,
    )

    assert contract["version"] == "1.1.0"
    assert result["status"] == "PASS"
    assert result["missing_columns"] == []
    assert result["type_violations"] == []
    assert result["domain_violations"] == []


def test_hardened_contract_fails_missing_runtime_column():
    df = _known_domain_frame(seed=802).drop(
        columns=[
            "pacs_available_at",
        ]
    )

    contract = load_contract("config/data_contract.yml")

    result = validate_contract(
        df,
        contract,
    )

    assert result["status"] == "FAIL"

    assert "pacs_available_at" in result["missing_columns"]


def test_hardened_contract_fails_boolean_type_mismatch():
    df = _known_domain_frame(seed=803)

    df["safety_check_complete"] = df["safety_check_complete"].astype(str)

    contract = load_contract("config/data_contract.yml")

    result = validate_contract(
        df,
        contract,
    )

    assert result["status"] == "FAIL"

    assert any(
        violation.startswith("safety_check_complete:") for violation in result["type_violations"]
    )


def test_hardened_contract_fails_datetime_type_mismatch():
    df = _known_domain_frame(seed=804)

    df["pacs_available_at"] = df["pacs_available_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

    contract = load_contract("config/data_contract.yml")

    result = validate_contract(
        df,
        contract,
    )

    assert result["status"] == "FAIL"

    assert any(
        violation.startswith("pacs_available_at:") for violation in result["type_violations"]
    )
