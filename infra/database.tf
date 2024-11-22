resource "google_firestore_database" "this" {
  project     = var.google_project_id
  name        = "${local.service}-${local.env}"
  location_id = "us-west1"
  type        = "FIRESTORE_NATIVE"
}

resource "google_project_iam_member" "firestore_service_account_role" {
  project = var.google_project_id
  role    = "roles/datastore.user" 
  member  = "serviceAccount:${google_service_account.this.email}"
}
