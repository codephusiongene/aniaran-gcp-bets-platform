# GCP Real-Time Betting Analytics (Pub/Sub → Dataflow → BigQuery → Looker/Looker Studio)

A minimal, production-flavored scaffold to ingest streaming betting events into **BigQuery**
using **Pub/Sub** and **Dataflow (Apache Beam)**, with dashboards in **Looker Studio** or **Looker**.

## Architecture
- **Pub/Sub** topic `bets-topic` for JSON bet events.
- **Dataflow (Apache Beam)** streaming job parses, validates, and writes to BigQuery.
- **BigQuery** dataset `bets_dataset` and table `live_bets` (partitioned on `event_ts`, clustered by `game_id`, `user_id`).
- **Looker Studio** connects directly to BigQuery for dashboards.
- **Looker** (optional) via LookML model in `looker/`.

## Prerequisites
- GCP project with billing enabled
- `gcloud` SDK installed and authenticated
- Terraform >= 1.4
- Python 3.10+
- (Optional) Looker access for LookML deployment

## Quickstart

### 0) Configure gcloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 1) Provision infra with Terraform
```bash
cd terraform
terraform init
terraform apply -auto-approve -var="project_id=YOUR_PROJECT_ID" -var="region=europe-west1" -var="location=EU"
```

**Outputs you'll see:**
- Pub/Sub topic: `bets-topic`
- Subscription: `bets-sub`
- BigQuery dataset: `bets_dataset`
- BigQuery table: `live_bets`
- GCS bucket for Dataflow staging/temp

### 2) Start the streaming Dataflow job
Option A — run from your machine (DataflowRunner):
```bash
cd ../dataflow
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python pipeline.py   --project YOUR_PROJECT_ID   --region europe-west1   --runner DataflowRunner   --streaming   --input_subscription projects/YOUR_PROJECT_ID/subscriptions/bets-sub   --output_table YOUR_PROJECT_ID:bets_dataset.live_bets   --temp_location gs://YOUR_STAGING_BUCKET/temp   --staging_location gs://YOUR_STAGING_BUCKET/staging   --num_workers 2
```

> TIP: Replace `YOUR_STAGING_BUCKET` with the bucket printed by Terraform (output `dataflow_bucket`).

### 3) Publish sample events
In a second terminal:
```bash
cd publisher
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python publish.py --project YOUR_PROJECT_ID --topic bets-topic --rate 15
```
This will publish ~15 events/second (adjust with `--rate`).

### 4) Verify in BigQuery
Open BigQuery console and run:
```sql
SELECT
  TIMESTAMP_TRUNC(event_ts, MINUTE) AS minute,
  game_id, COUNT(*) AS bets, SUM(stake_amount) AS stake, SUM(payout) AS payout
FROM `YOUR_PROJECT_ID.bets_dataset.live_bets`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE)
GROUP BY minute, game_id
ORDER BY minute DESC, bets DESC;
```

### 5) Looker Studio
1. Open Looker Studio and **Create → Report**.
2. Choose **BigQuery** connector → your project → `bets_dataset` → `live_bets`.
3. Build visuals (scorecards for total bets/stake, time series by minute, table by game/country).

### 6) (Optional) Looker (LookML)
- Import the `looker/` folder into your Looker project.
- Configure a **connection** that points to BigQuery in Looker admin.
- Validate & deploy the model. Explore `bets`.

---

## Teardown
```bash
cd terraform
terraform destroy -auto-approve -var="project_id=YOUR_PROJECT_ID" -var="region=europe-west1" -var="location=EU"
```

## Notes
- All resources default to **EU** locations for GDPR friendliness.
- For production, consider **dead-letter topics**, **BigQuery Data Quality checks**, and **Cloud Composer** DAGs for backfills and governance.
- You can adapt worker sizing with `--max_num_workers` and autoscaling options.

Generated: 2025-08-13
