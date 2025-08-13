# Composer & Data Quality

- Snapshot + DQ: `composer/dags/bets_daily_snapshot_and_dq.py`
- Alerts (Slack/Teams): `composer/dags/bets_dq_alerts.py`
- Backfill: `composer/dags/bets_backfill_from_gcs.py`

## Airflow Variables
- `gcp_project_id` – your project
- `slack_webhook` – Slack Incoming Webhook URL (optional)
- `teams_webhook` – MS Teams Incoming Webhook URL (optional)
- `backfill_bucket` – GCS bucket for backfill files
