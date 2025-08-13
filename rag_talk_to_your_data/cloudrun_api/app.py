import os, json
from flask import Flask, request, jsonify
from google.cloud import bigquery
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel, TextGenerationModel
from google.cloud import bigquery
import yaml
from .utils import sha256, truncate_sentences, format_citations, assemble_prompt_jinja

def get_cache(q_hash: str):
    sql = f"""
SELECT answer, context_json, facts_json
FROM `{PROJECT}.talk_data.qa_cache`
WHERE q_hash = @h
ORDER BY created_ts DESC
LIMIT 1
"""
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("h", "STRING", q_hash)]
    )
    rows = list(bq.query(sql, job_config=job_config).result())
    if rows:
        r = rows[0]
        return r["answer"], json.loads(r["context_json"]), json.loads(r["facts_json"])
    return None

def put_cache(q_hash: str, question: str, answer: str, context, facts):
    table = f"{PROJECT}.talk_data.qa_cache"
    row = {
        "q_hash": q_hash,
        "question": question,
        "answer": answer,
        "context_json": json.dumps(context, ensure_ascii=False),
        "facts_json": json.dumps(facts, ensure_ascii=False),
    }
    bq.insert_rows_json(table, [row])


PROJECT = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION", "europe-west1")
DATASET = os.environ.get("DATASET", "talk_data")
INDEX_TABLE = os.environ.get("INDEX_TABLE", "docs_index")
BETS_DATASET = os.environ.get("BETS_DATASET", "bets_dataset")
BETS_TABLE = os.environ.get("BETS_TABLE", "live_bets")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-004")
GEN_MODEL = os.environ.get("GEN_MODEL", "text-bison")

app = Flask(__name__)

# Load prompt templates
PROMPT_PATH = os.environ.get("PROMPT_PATH", "/app/prompt_templates.yaml")
try:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        PROMPTS = yaml.safe_load(f)
except Exception:
    PROMPTS = {"default": {"system": "", "user": "", "postprocess": {"max_sentences": 10}}}

bq = bigquery.Client(project=PROJECT)
vertexai.init(project=PROJECT, location=LOCATION)

def embed_text(text: str):
    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL)
    return model.get_embeddings([text])[0].values

def retrieve_context(question: str, k: int = 5):
    q_vec = embed_text(question)
    # Parameterized vector for BigQuery similarity search
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("q", "FLOAT64", q_vec)
        ]
    )
    query = f"""
SELECT content, source_uri, COSINE_DISTANCE(embedding, @q) AS dist
FROM `{PROJECT}.{DATASET}.{INDEX_TABLE}`
ORDER BY dist ASC
LIMIT {k}
"""
    rows = list(bq.query(query, job_config=job_config).result())
    docs = [{"content": r["content"], "source": r["source_uri"], "distance": r["dist"]} for r in rows]
    return docs

def fetch_recent_facts():
    sql = f"""
SELECT game_id, COUNT(*) AS bets, SUM(stake_amount) AS stake, AVG(odds) AS avg_odds
FROM `{PROJECT}.{BETS_DATASET}.{BETS_TABLE}`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
GROUP BY game_id
ORDER BY stake DESC
LIMIT 5
"""
    rows = list(bq.query(sql).result())
    return [dict(r) for r in rows]



@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    question = data.get("question", "")[:2000]
    if not question:
        return jsonify({"error": "Missing question"}), 400

    # Cache check
    q_hash = sha256(question)
    cached = get_cache(q_hash)
    if cached:
        answer, ctx, facts = cached
        return jsonify({"answer": answer, "context": ctx, "facts": facts, "cached": True})

    # Retrieve & assemble
    docs = retrieve_context(question, k=5)
    facts = fetch_recent_facts()

    # Build prompt via template
    tpl = PROMPTS.get("default", {})
    prompt = assemble_prompt_jinja(tpl.get("system",""), tpl.get("user",""), question, docs, json.dumps(facts, ensure_ascii=False))

    # Generate
    model = TextGenerationModel.from_pretrained(GEN_MODEL)
    resp = model.predict(prompt, temperature=0.2, max_output_tokens=512)
    raw_answer = resp.text or ""

    # Post-process: truncate & add citations
    max_s = tpl.get("postprocess",{}).get("max_sentences",10)
    answer = truncate_sentences(raw_answer, max_sentences=max_s)
    citations = format_citations(docs)
    answer = answer.strip() + "

Sources:
" + citations

    # Save cache
    put_cache(q_hash, question, answer, docs, facts)

    return jsonify({"answer": answer, "context": docs, "facts": facts, "cached": False})


@app.route("/healthz", methods=["GET"])\
def health():
    return "ok", 200
