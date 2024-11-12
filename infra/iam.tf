resource "google_service_account" "this" {
  account_id   = "srv-${local.service}"
  display_name = "srv_crowemi_trades"
  description  = "A service account for ${local.service}"
}
resource "google_cloud_run_service_iam_member" "this" {
  location = google_cloud_run_v2_service.this.location
  service  = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.this.email}"
}
