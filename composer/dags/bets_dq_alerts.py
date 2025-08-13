from datetime import datetime, timedelta
import json, requests, os
from airflow import DAG
from airflow.models import Variable
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.operators.python import PythonOperator

PROJECT = "{{ var.value.gcp_project_id }}"
DATASET = "bets_dataset"

SLACK_WEBHOOK = Variable.get("slack_webhook", default_var=None)
TEAMS_WEBHOOK = Variable.get("teams_webhook", default_var=None)

default_args = {"owner":"data-eng","retries":1,"retry_delay":timedelta(minutes=5)}

def notify(**context):
    bq = context["ti"].xcom_pull(task_ids="check_dq_status")
    # bq is a list of rows from BigQueryInsertJobOperator; we will encode status in XCom via Python task

def post_alert(msg: str):
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": msg}, timeout=10)
        except Exception as e:
            print("Slack error:", e)
    if TEAMS_WEBHOOK:
        try:
            card = {
                "@type": "MessageCard", "@context": "http://schema.org/extensions",
                "summary": "DQ Alert", "themeColor":"FF0000", "title":"DQ Alert", "text": msg
            }
            requests.post(TEAMS_WEBHOOK, data=json.dumps(card), headers={"Content-Type":"application/json"}, timeout=10)
        except Exception as e:
            print("Teams error:", e)

def evaluate_and_alert(**kwargs):
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT)
    sql = f"""
    SELECT ts, status, findings FROM `{PROJECT}.{DATASET}.dq_log`
    WHERE ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    ORDER BY ts DESC
    LIMIT 1
    """
    rows = list(client.query(sql).result())
    if not rows:
        return
    r = rows[0]
    status = r["status"]
    findings = r["findings"]
    if status != "OK":
        msg = f"*DQ WARNING*: status={status}, findings={findings}"
        post_alert(msg)

with DAG(
    "bets_dq_alerts",
    default_args=default_args,
    schedule_interval="15 2 * * *",  # after dq finishes
    start_date=datetime(2025,1,1),
    catchup=False,
    tags=["bets","dq","alerts"],
) as dag:
    evaluate = PythonOperator(
        task_id="evaluate_and_alert",
        python_callable=evaluate_and_alert,
        provide_context=True,
    )
