# Talk to Your Data (RAG)

- Vectorize docs from GCS using Vertex AI embeddings:
  - `rag_talk_to_your_data/ingest/index_gcs_to_bq_vectors.py`
- Query vectors in BigQuery using cosine distance.
- Cloud Run API (`/ask`) assembles context + BigQuery facts and calls Vertex AI.
- Integrations: Slack bot, Teams webhook relay, Streamlit UI.

PlantUML model:

```plantuml
!include ../plantuml/rag_module.puml
```
