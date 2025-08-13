output "pubsub_topic" {
  value = google_pubsub_topic.bets.name
}

output "pubsub_subscription" {
  value = google_pubsub_subscription.bets_sub.name
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.bets_ds.dataset_id
}

output "bigquery_table" {
  value = google_bigquery_table.live_bets.table_id
}

output "dataflow_bucket" {
  value = google_storage_bucket.dataflow_staging.name
}
