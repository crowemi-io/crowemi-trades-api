resource "mongodbatlas_serverless_instance" "this" {
  project_id   = var.atlas_project_id
  name         = "${local.service}-${local.env}"

  provider_settings_backing_provider_name = "GCP"
  provider_settings_provider_name = "SERVERLESS"
  provider_settings_region_name = "us-central1"
}
