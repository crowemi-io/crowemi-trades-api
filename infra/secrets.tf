data "google_secret_manager_secret" "alpaca_api_key" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_KEY"
}
data "google_secret_manager_secret" "alpaca_api_secret_key" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_SECRET_KEY"
}
data "google_secret_manager_secret" "alpaca_url_base" {
  secret_id = "CROWEMI_TRADES_ALPACA_API_URL_BASE"
}
data "google_secret_manager_secret" "alpaca_data_url_base" {
  secret_id = "CROWEMI_TRADES_ALPACA_DATA_API_URL_BASE"
}
data "google_secret_manager_secret" "mongodb_uri" {
  secret_id = "CROWEMI_TRADES_MONGODB_URI"
}