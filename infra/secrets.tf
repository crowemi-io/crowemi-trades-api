locals {
  secret_name = local.env == "paper" ? "CROWEMI_${local.service}_${upper(local.env)}" : "CROWEMI_TRADES_API"
}

data "google_secret_manager_secret" "this" {
  secret_id = local.secret_name
}
resource "google_secret_manager_secret_iam_member" "this" {
  secret_id = data.google_secret_manager_secret.this.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}
