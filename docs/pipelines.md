# Data Pipelines

## Streaming (Pub/Sub → Dataflow → BigQuery)
- `dataflow/pipeline_dlq.py` handles JSON parsing, validation, DLQ routing, and writes to `bets_dataset.live_bets`.
- Errors go to `bets_dataset.bets_errors` and optionally to Pub/Sub DLQ.

## Backfill (GCS → BigQuery)
- DAG: `composer/dags/bets_backfill_from_gcs.py`
- Trigger with run config: `{"pattern":"backfill/2025-08-01/*.json"}`
