# Healthcare RIS/PACS Analytics Demo

**Healthcare Analytics | Medical Imaging | RIS/PACS | Workflow Analytics | Data Quality**

A reproducible public portfolio project showing how synthetic radiology workflow data can be transformed into management-oriented operational evidence.

The project follows imaging studies across acquisition, PACS availability and reporting. It lets users explore workload, reporting pressure, workflow latency, data quality and synthetic safety-check metadata from one analytical interface.

This is a public demonstration project. It does not connect to a real hospital system, contain patient information, or make clinical decisions.

## Why this project exists

Radiology information systems generate operational timestamps throughout the imaging workflow. Individually, those timestamps describe events. Combined into a consistent analytical model, they can help healthcare managers and technical teams understand how work moves through a service.

The central analytical questions are:

- How is the imaging service performing under the selected analytical context?
- Where is workload concentrated across modalities, rooms and patient classes?
- Which pending reports require operational attention?
- Where is time being consumed across the technical and reporting workflow?
- Can the analytical slice be trusted before management conclusions are made?

The project demonstrates how those questions can be translated into reproducible metrics, visualizations, validation rules and management signals.

## Workflow represented

```text
Exam timestamp
      |
      v
Acquisition start
      |
      v
Acquisition end
      |
      v
PACS available
      |
      v
Report signed
```

The workflow is intentionally divided into two analytical paths:

```text
TECHNICAL PATH
Exam timestamp -> Acquisition start -> Acquisition end -> PACS available

REPORTING PATH
PACS available -> Report signed
```

Latency is summarized primarily with robust percentiles such as P50 and P90. This distinguishes typical performance from the longer tail of operational delays.

## What managers can explore

### Executive

A high-level view of activity and operational status under the currently applied filters.

### Operations

Workload distribution by modality, room, procedure category, patient class and time period. This supports investigation of where activity is concentrated and where capacity questions may require further analysis.

### Reporting

Pending reporting workload is classified relative to a configurable synthetic reporting target. The dashboard separates active states such as Normal, Warning, Critical and Breached, and summarizes historical reporting performance.

These thresholds are operational demonstration parameters. They are not universal legal, regulatory or clinical deadlines.

### Workflow

The workflow view shows where time is consumed between acquisition stages, PACS availability and report signature. The purpose is not merely to display turnaround time; it is to make bottlenecks visible and support questions about process design, capacity, staffing and operational follow-up.

### Quality & Safety

Operational analytics are useful only when the underlying data can be trusted. The demo therefore includes a minimal data contract, schema/domain validation, data-quality checks, timestamp consistency checks and synthetic checklist-completion indicators.

The safety indicators represent synthetic operational metadata only. They are not evidence of clinical safety, accreditation, regulatory compliance or patient eligibility.

## From data to management evidence

```text
synthetic workflow events
        |
        v
data contract
        |
        v
quality validation
        |
        v
operational metrics
        |
        v
workflow and reporting analysis
        |
        v
management-oriented visualization
        |
        v
human interpretation and decision support
```

The dashboard does not automate management or clinical decisions. It provides structured evidence that can support further investigation.

## What this repository demonstrates technically

The public implementation demonstrates selected capabilities in:

- healthcare and radiology workflow analytics;
- Python analytical engineering;
- synthetic data generation;
- data contracts and schema validation;
- data-quality engineering;
- configurable reporting SLA logic;
- workflow latency analysis;
- executive data visualization;
- Streamlit application development;
- reproducible configuration;
- automated testing;
- release security and secret scanning;
- cross-platform continuous integration.

The repository intentionally exposes only a curated public analytical layer.

## For recruiters and technical reviewers

A useful review path is:

```text
README.md
   ->
ui_app_v3.py
   ->
src/rispacs_demo/
   ->
tests/
   ->
.github/workflows/ci.yml
```

The project demonstrates the combination of healthcare-domain knowledge, analytical reasoning and software-engineering discipline rather than dashboard construction alone.

Suggested implementation files to review:

```text
src/rispacs_demo/contracts.py
src/rispacs_demo/quality.py
src/rispacs_demo/reporting_sla.py
src/rispacs_demo/ui_state.py
src/rispacs_demo/visualization_v3.py
```

## Public data strategy

All included analytical data are synthetic. The repository contains no real patient identifiers, protected health information, institutional databases, clinical records, production credentials or hospital configuration.

Synthetic anomalies are deliberately included so contract and data-quality behavior can be tested rather than demonstrated only against perfect data.

## Public / private boundary

This repository is a deliberately curated public demonstration. It excludes production integration logic, institution-specific configuration, real RIS/HIS/PACS/VNA connectors, private operational data, production credentials and proprietary analytical components.

The objective is to demonstrate transferable engineering and analytical principles without exposing private systems or confidential implementation details.

## Repository structure

```text
.github/workflows/       Cross-platform continuous integration
config/                  Demo configuration and data contract
data/                    Synthetic demonstration data
docs/                    Architecture, dictionary and publication boundary
scripts/                 Reproducible generation and validation commands
src/rispacs_demo/        Analytical and application components
tests/                   Contract, quality, privacy and analytics tests
ui_app_v3.py             Current certified Streamlit dashboard
README.md                Public project orientation
```

## Quick start

The validated runtime targets Python 3.11.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
streamlit run ui_app_v3.py
```

The repository already includes a synthetic demo dataset. To regenerate it:

```powershell
python scripts\generate_demo_data.py --rows 50000
```

## Validation

```powershell
python -m pytest -q
```

Current certified local release evidence:

```text
83 passing automated tests
Ruff                         PASS
Compileall                   PASS
Public release preflight     PASS
Gitleaks                     PASS
Clean installation           PASS
Streamlit health check       PASS
Runtime dependency audit     PASS
```

GitHub Actions reproduces the core quality gate on Windows and Ubuntu using Python 3.11.

## Engineering principles

```text
1. COMMUNICATE
   context + management questions + analytical interpretation

2. DEMONSTRATE
   synthetic workflow + interactive dashboard + visible evidence

3. ENGINEER
   reusable Python components + configuration + contracts

4. VALIDATE
   automated tests + CI + release security gates
```

The guiding principle is that a dashboard should not merely display numbers. It should make the analytical question, data assumptions, limitations and decision context explicit.

## Decision-support boundary

This software is a portfolio and demonstration artifact. It is not a medical device, clinical decision support, a production hospital information system, a legal GES compliance engine, or a substitute for clinical or managerial judgement.

## Rights and use

Copyright (c) 2026 Inteligencia Hospitalaria.

The source is published for portfolio, demonstration and evaluation purposes under the terms described in `LICENSE.txt`.
