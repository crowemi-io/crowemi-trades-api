locals {
  secret_name = local.env == "paper" ? "CROWEMI_TRADES_API_PAPER" : "CROWEMI_TRADES_API"
}

data "google_secret_manager_secret" "this" {
  secret_id = local.secret_name
}
resource "google_secret_manager_secret_iam_member" "this" {
  secret_id = data.google_secret_manager_secret.this.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}
