from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.models import Variable

PROJECT = "{{ var.value.gcp_project_id }}"
DATASET = "bets_dataset"
TABLE = "live_bets"
BUCKET = Variable.get("backfill_bucket", default_var="{{ var.value.backfill_bucket if var.value.backfill_bucket else '' }}")
PREFIX = Variable.get("backfill_prefix", default_var="backfill/")  # e.g., backfill/2025-08-01/*.json
LOCATION = "EU"

default_args = {"owner": "data-eng", "depends_on_past": False, "retries": 0}

with DAG(
    "bets_backfill_from_gcs",
    default_args=default_args,
    schedule_interval=None,  # trigger manually with conf
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["bets","backfill"],
) as dag:

    gcs_to_bq = GCSToBigQueryOperator(
        task_id="gcs_to_bq",
        bucket=BUCKET,
        source_objects=["{{ dag_run.conf.get('pattern', 'backfill/*.json') }}"],
        destination_project_dataset_table=f"{PROJECT}.{DATASET}.{TABLE}",
        source_format="NEWLINE_DELIMITED_JSON",
        write_disposition="WRITE_APPEND",
        autodetect=False,
        schema_fields=[
            {"name":"event_ts","type":"TIMESTAMP","mode":"REQUIRED"},
            {"name":"bet_id","type":"STRING","mode":"REQUIRED"},
            {"name":"user_id","type":"STRING","mode":"REQUIRED"},
            {"name":"game_id","type":"STRING","mode":"REQUIRED"},
            {"name":"sport","type":"STRING","mode":"NULLABLE"},
            {"name":"country","type":"STRING","mode":"NULLABLE"},
            {"name":"channel","type":"STRING","mode":"NULLABLE"},
            {"name":"stake_amount","type":"NUMERIC","mode":"REQUIRED"},
            {"name":"odds","type":"FLOAT","mode":"REQUIRED"},
            {"name":"payout","type":"NUMERIC","mode":"NULLABLE"},
            {"name":"status","type":"STRING","mode":"NULLABLE"},
            {"name":"ingest_id","type":"STRING","mode":"NULLABLE"},
            {"name":"load_ts","type":"TIMESTAMP","mode":"NULLABLE"}
        ],
    )
