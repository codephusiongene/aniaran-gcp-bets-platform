# Runbook

1. **Terraform apply** to provision core infra.
2. **Start Dataflow** streaming job (`pipeline_dlq.py`).
3. **Publish events** using `publisher/publish.py`.
4. **Verify** in BigQuery with queries in `sql/queries.sql`.
5. **Set up Composer**: upload DAGs, set Variables.
6. **Create vector table** and **index docs** for Talk to Your Data.
7. **Build & push** images to Artifact Registry.
8. **Deploy Cloud Run** services via Terraform (or gcloud).
9. **Connect reporting**: Looker Studio / Looker.
10. **Test** Slack/Teams/Streamlit integrations.

## Useful Commands

```bash
# Build & push Talk API
gcloud builds submit rag_talk_to_your_data/cloudrun_api   --tag europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/containers/talk-api:latest

# Build & push Teams relay
gcloud builds submit integrations/teams_webhook   --tag europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/containers/teams-relay:latest

# Re-apply Terraform to wire Cloud Run services
cd terraform
terraform apply -auto-approve -var="project_id=YOUR_PROJECT_ID" -var="region=europe-west1" -var="location=EU"
```
