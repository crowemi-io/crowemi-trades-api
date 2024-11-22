resource "google_firestore_database" "this" {
  project     = var.google_project_id
  name        = "${local.service}-${local.env}"
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"
}