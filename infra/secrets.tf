locals {
  secret_id = local.env == "paper" ? "CROWEMI_${local.service}_${local.env}" : "CROWEMI_TRADES_API"
}

data "google_secret_manager_secret" "this" {
  secret_id = local.secret_id
}
resource "google_secret_manager_secret_iam_member" "this" {
  secret_id = data.google_secret_manager_secret.this.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}
