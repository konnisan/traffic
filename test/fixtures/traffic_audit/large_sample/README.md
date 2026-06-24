# Traffic Audit Large Sample Dataset

This folder contains deterministic anonymized sample data for traffic audit acceptance tests.

Files:

- `vehicles.csv`: vehicle master data.
- `transactions.csv`: toll transaction records.
- `passages.csv`: entry, gantry, and exit passage events.
- `manifest.json`: scenario labels and expected anomaly types for each plate.

Scenario coverage:

- `normal`: complete route and matching fee.
- `missing_entry`: route starts without an entry event.
- `missing_exit`: route ends without an exit event.
- `time_conflict`: business sequence conflicts with event time order.
- `route_discontinuity`: adjacent passage nodes do not match the expected next node.
- `fee_mismatch`: charged amount differs from expected amount.
- `combined_anomalies`: multiple rule hits in one case.
- `green_review`: normal green-channel style sample for auxiliary review drafting.

All records are synthetic. Raw passage and transaction records should be processed by deterministic audit code only, not inserted into RAG or graph extraction.
