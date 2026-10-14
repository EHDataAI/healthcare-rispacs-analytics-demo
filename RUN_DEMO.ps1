$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .

if (-not (Test-Path ".\data\demo_radiology.parquet")) {
    python .\scripts\generate_demo_data.py --rows 50000
}

streamlit run .\ui_app.py
