resource "google_service_account" "this" {
  account_id   = "srv-${local.service}"
  display_name = "srv_crowemi_trades"
  description  = "A service account for ${local.service}"
}
