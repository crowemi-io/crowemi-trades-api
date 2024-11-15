data "google_secret_manager_secret" "alpaca_api_key" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_KEY"
}
resource "google_secret_manager_secret_iam_member" "alpaca_api_key" {
  secret_id = data.google_secret_manager_secret.alpaca_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}

data "google_secret_manager_secret" "alpaca_api_secret_key" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_SECRET_KEY"
}
resource "google_secret_manager_secret_iam_member" "alpaca_api_secret_key" {
  secret_id = data.google_secret_manager_secret.alpaca_api_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}

data "google_secret_manager_secret" "alpaca_url_base" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_URL_BASE"
}
resource "google_secret_manager_secret_iam_member" "alpaca_url_base" {
  secret_id = data.google_secret_manager_secret.alpaca_url_base.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}

data "google_secret_manager_secret" "alpaca_data_url_base" {
  secret_id = "CROWEMI_TRADES_ALPACA_DATA_API_URL_BASE"
}
resource "google_secret_manager_secret_iam_member" "alpaca_data_url_base" {
  secret_id = data.google_secret_manager_secret.alpaca_data_url_base.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}

data "google_secret_manager_secret" "mongodb_uri" {
  secret_id = "CROWEMI_TRADES_MONGODB_URI"
}
resource "google_secret_manager_secret_iam_member" "mongodb_uri" {
  secret_id = data.google_secret_manager_secret.mongodb_uri.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}

data "google_secret_manager_secret" "bot" {
  secret_id = "CROWEMI_TRADES_BOT"
}
resource "google_secret_manager_secret_iam_member" "bot" {
  secret_id = data.google_secret_manager_secret.bot.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.this.email}"
}