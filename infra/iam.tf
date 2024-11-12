resource "google_service_account" "service_account" {
  account_id   = "srv-${local.service}"
  display_name = "srv_crowemi_trades"
  description  = "A service account for ${local.service}"
}

resource "google_secret_manager_secret_iam_member" "aws_access_key_id" {
  secret_id = data.google_secret_manager_secret.aws_access_key_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.service_account.email}"
}
resource "google_secret_manager_secret_iam_member" "aws_secret_access_key" {
  secret_id = data.google_secret_manager_secret.aws_secret_access_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.service_account.email}"
}