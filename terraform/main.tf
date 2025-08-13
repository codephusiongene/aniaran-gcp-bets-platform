resource "google_pubsub_topic" "bets" {
  name = "bets-topic"
}

resource "google_pubsub_subscription" "bets_sub" {
  name  = "bets-sub"
  topic = google_pubsub_topic.bets.name

  ack_deadline_seconds = 20

  expiration_policy {
    ttl = ""
  }
}

resource "google_storage_bucket" "dataflow_staging" {
  name     = "${var.project_id}-df-staging-${replace(var.region, "-", "")}"
  location = var.location
  force_destroy = true

  uniform_bucket_level_access = true
  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 30 }
  }
}

resource "google_bigquery_dataset" "bets_ds" {
  dataset_id  = "bets_dataset"
  location    = var.location
  description = "Dataset for live betting events"
  delete_contents_on_destroy = true
}

resource "google_bigquery_table" "live_bets" {
  dataset_id = google_bigquery_dataset.bets_ds.dataset_id
  table_id   = "live_bets"

  schema = file("${path.module}/schemas/bq_bets_schema.json")

  time_partitioning {
    type  = "DAY"
    field = "event_ts"
  }

  clustering = ["game_id", "user_id"]

  deletion_protection = false
}

# Service Account for Dataflow
resource "google_service_account" "dataflow_sa" {
  account_id   = "dataflow-sa"
  display_name = "Dataflow Worker SA"
}

# IAM bindings for the SA
resource "google_project_iam_member" "df_worker_role" {
  project = var.project_id
  role    = "roles/dataflow.worker"
  member  = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

resource "google_project_iam_member" "df_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

resource "google_bigquery_dataset_iam_member" "df_bq_editor" {
  dataset_id = google_bigquery_dataset.bets_ds.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

resource "google_storage_bucket_iam_member" "df_bucket_admin" {
  bucket = google_storage_bucket.dataflow_staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dataflow_sa.email}"
}


# === Cloud Run & Artifact Registry ===

# Artifact Registry for containers
resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "containers"
  description   = "Containers for talk-api and teams-relay"
  format        = "DOCKER"
}

# Cloud Run: Talk API
resource "google_cloud_run_service" "talk_api" {
  name     = "talk-api"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/containers/talk-api:latest"
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        env { name="LOCATION" value=var.region }
        env { name="BETS_DATASET" value="bets_dataset" }
        env { name="BETS_TABLE" value="live_bets" }
      }
      service_account_name = google_service_account.rag_api_sa.email
    }
  }
}

resource "google_cloud_run_service_iam_member" "talk_api_invoker" {
  location = google_cloud_run_service.talk_api.location
  service  = google_cloud_run_service.talk_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run: Teams relay
resource "google_cloud_run_service" "teams_relay" {
  name     = "teams-relay"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/containers/teams-relay:latest"
        env { name="API_URL" value = "https://${google_cloud_run_service.talk_api.status[0].url}/ask" }
        env { name="TEAMS_WEBHOOK" value = var.teams_webhook }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "teams_relay_invoker" {
  location = google_cloud_run_service.teams_relay.location
  service  = google_cloud_run_service.teams_relay.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

variable "teams_webhook" {
  description = "Optional Teams incoming webhook URL for relay service"
  type        = string
  default     = ""
}

output "talk_api_url" {
  value = google_cloud_run_service.talk_api.status[0].url
}
output "teams_relay_url" {
  value = google_cloud_run_service.teams_relay.status[0].url
}
