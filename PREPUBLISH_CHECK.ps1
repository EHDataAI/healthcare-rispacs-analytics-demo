$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Missing .venv. Create the environment and install the project first."
}

& .\.venv\Scripts\Activate.ps1

python .\scripts\public_release_preflight.py
python -m ruff check .
python -m pytest -q

Write-Host "PASS: public repository pre-publication checks completed."
