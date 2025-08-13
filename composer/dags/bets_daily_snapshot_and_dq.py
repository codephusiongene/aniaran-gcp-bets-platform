from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

PROJECT = "{{ var.value.gcp_project_id }}"
DATASET = "bets_dataset"
TABLE = "live_bets"
SNAP_TABLE = "live_bets_snapshot"

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "bets_daily_snapshot_and_dq",
    default_args=default_args,
    schedule_interval="0 2 * * *",  # 02:00 UTC daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["bets","dq","snapshot"],
) as dag:

    # 1) Create or append daily snapshot partition (by snapshot_date)
    create_snapshot = BigQueryInsertJobOperator(
        task_id="create_snapshot",
        configuration={
            "query": {
                "query": f"""
                CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.{SNAP_TABLE}`
                PARTITION BY DATE(snapshot_ts) AS
                SELECT CURRENT_TIMESTAMP() AS snapshot_ts, t.*
                FROM `{PROJECT}.{DATASET}.{TABLE}` t
                WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);
                """,
                "useLegacySql": False,
            }
        },
    )

    # 2) Data Quality: freshness and non-null checks
    dq_checks = BigQueryInsertJobOperator(
        task_id="dq_checks",
        configuration={
            "query": {
                "query": f"""
                DECLARE anomalies ARRAY<STRING>;
                SET anomalies = [];

                -- Freshness: at least 1 row in last 2 hours
                IF (SELECT COUNT(*) FROM `{PROJECT}.{DATASET}.{TABLE}`
                    WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)) = 0 THEN
                  SET anomalies = ARRAY_CONCAT(anomalies, ["no_recent_data"]);
                END IF;

                -- Non-null critical columns
                IF (SELECT COUNT(*) FROM `{PROJECT}.{DATASET}.{TABLE}` WHERE bet_id IS NULL OR user_id IS NULL) > 0 THEN
                  SET anomalies = ARRAY_CONCAT(anomalies, ["null_keys"]);
                END IF;

                -- Write results to a tiny DQ log table
                CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.dq_log`
                (ts TIMESTAMP, status STRING, findings ARRAY<STRING>);

                INSERT INTO `{PROJECT}.{DATASET}.dq_log` (ts, status, findings)
                VALUES (CURRENT_TIMESTAMP(), IF(ARRAY_LENGTH(anomalies)=0, "OK", "WARN"), anomalies);
                """,
                "useLegacySql": False,
            }
        },
    )

    create_snapshot >> dq_checks
