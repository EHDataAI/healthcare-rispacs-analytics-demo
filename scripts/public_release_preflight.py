from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".example"}
FORBIDDEN_FILENAMES = {"rispacs.duckdb", ".env"}
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
}
SENSITIVE_FIELD_PATTERNS = {
    "patient_name": re.compile(r"\bpatient_name\b", re.IGNORECASE),
    "rut_field": re.compile(r"\b(?:rut|dni|national_id)\b", re.IGNORECASE),
    "mrn_field": re.compile(r"\bmrn\b", re.IGNORECASE),
}


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    for path in iter_files():
        rel = path.relative_to(ROOT)
        if path.name in FORBIDDEN_FILENAMES:
            failures.append(f"Forbidden file: {rel}")
            continue

        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"Potential {label}: {rel}")

        if path.name not in {
            "SECURITY.md",
            "GITHUB_PUBLISH_CHECKLIST.md",
            "public_release_preflight.py",
            "test_privacy.py",
            ".gitignore",
        }:
            for label, pattern in SENSITIVE_FIELD_PATTERNS.items():
                if pattern.search(text):
                    warnings.append(f"Review {label}: {rel}")

    if warnings:
        print("WARNINGS")
        for item in sorted(set(warnings)):
            print(" -", item)

    if failures:
        print("FAIL")
        for item in sorted(set(failures)):
            print(" -", item)
        raise SystemExit(1)

    print("PASS: no forbidden files or obvious secret patterns detected")


if __name__ == "__main__":
    main()
