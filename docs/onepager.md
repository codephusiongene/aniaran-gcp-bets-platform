
# Aniaran – GCP Betting Analytics: 1‑Pager

**Goal**: Real‑time betting analytics with robust governance, and a *Talk to Your Data* (RAG) module for natural‑language insights.

**Core Flow**: App → Pub/Sub → Dataflow (DLQ + errors) → BigQuery (partitioned/clustered) → Looker Studio/Looker.

**Ops & Governance**: Cloud Composer (snapshots, DQ, alerts), RLS/CLS in BigQuery, Terraform + CI.

**RAG** (*Talk to Your Data*): GCS docs → BigQuery vectors → Vertex AI (embeddings + LLM) → Cloud Run API → Slack/Teams/Streamlit.

**Why it wins**  
- Time‑to‑insight with governed reporting (Looker Studio/Looker).  
- Operational reliability (DLQ, error tables, DQ, alerts).  
- Cost‑aware analytics (BQ partitions/clusters).  
- AI‑ready without disruption (RAG overlays facts + docs).

**Tech Map (GCP)**  
- Ingest: Pub/Sub  
- Transform: Dataflow (Apache Beam)  
- Orchestrate: Cloud Composer  
- Store: BigQuery, GCS  
- Serve: Looker Studio/Looker  
- AI: Vertex AI + Cloud Run  
- Sec: IAM, BigQuery RLS/CLS

**Interview Soundbite**  
> “We deliver live analytics in BigQuery with governed dashboards and add a *Talk to Your Data* layer so teams can query the truth via natural language — grounded in our data, not LLM guesses.”
