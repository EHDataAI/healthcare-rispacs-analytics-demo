# GitHub publication checklist

Run this checklist before making the repository public.

1. Confirm the repository contains synthetic data only.
2. Confirm `.env`, credentials, tokens, connection strings and local database files are absent.
3. Confirm no real patient, employee, hospital or institutional identifiers are present.
4. Confirm no production RIS/HIS/PACS/VNA endpoint or vendor credential is present.
5. Run `python scripts/public_release_preflight.py`.
6. Run `python -m ruff check .`.
7. Run `python -m pytest -q`.
8. Generate a fresh synthetic dataset and launch Streamlit locally.
9. Review README screenshots/text before publication.
10. Inspect `git diff --cached` before the first public commit.

Suggested first tag: `v0.1.0-demo`.
