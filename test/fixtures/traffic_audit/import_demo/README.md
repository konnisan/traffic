# Traffic Audit Import Demo

This folder is designed for manual frontend import testing.

Use these files in the traffic audit detail page:

1. Create a case from `/audit`.
2. Use one case from `cases_to_create.json`.
3. Set the time window to `2026-01-02 07:50:00` through `2026-01-02 09:10:00`.
4. Upload the three datasets:
   - dataset type `vehicles`: `vehicles.csv`
   - dataset type `transactions`: `transactions.csv`
   - dataset type `passages`: `passages.csv`
5. Click `开始分析`.

Recommended quick checks:

- `DEMO0001`: normal route, no anomaly.
- `DEMO0002`: missing entry.
- `DEMO0004`: time conflict.
- `DEMO0006`: fee mismatch.
- `DEMO0008`: combined anomalies.

All records are synthetic. They are for deterministic audit testing only and should not be imported into RAG or graph extraction.
