# Data dictionary

| Field | Meaning |
|---|---|
| accession_alias | Synthetic non-PHI study/accession alias |
| exam_datetime | Synthetic requested/performed date-time anchor |
| modality | CT, MR, US, CR or DX |
| room | Synthetic acquisition room |
| patient_class | OUTPATIENT, INPATIENT or EMERGENCY |
| acquisition_start | Synthetic acquisition start timestamp |
| acquisition_end | Synthetic acquisition end timestamp |
| pacs_available_at | Synthetic time study becomes available for reporting |
| report_signed_at | Synthetic final report timestamp; null if pending |
| report_status | PENDING or SIGNED |
| ges_flag | Synthetic demo label only |
| safety_check_complete | Synthetic aggregate safety/checklist flag |
| procedure_group | High-level synthetic procedure family |
