from rispacs_demo.synthetic import DemoSpec, generate_demo_dataset


def test_demo_contains_aliases_not_patient_identifiers():
    df = generate_demo_dataset(DemoSpec(rows=100, seed=17))
    forbidden = {"patient_name", "rut", "mrn", "patient_id", "accession_number"}
    assert forbidden.isdisjoint({c.lower() for c in df.columns})
    assert df["accession_alias"].str.startswith("ACC-").all()
