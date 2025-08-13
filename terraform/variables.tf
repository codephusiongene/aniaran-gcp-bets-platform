variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Default GCP region (e.g., europe-west1)"
  type        = string
  default     = "europe-west1"
}

variable "location" {
  description = "BigQuery & GCS location (e.g., EU)"
  type        = string
  default     = "EU"
}
