resource "mongodbatlas_cluster" "this" {
  project_id              = var.atlas_project_id
  name                    = "${local.service}-${local.env}"

  provider_name = "TENANT"
  backing_provider_name = "GCP"
  provider_region_name = "US_CENTRAL_1"
  provider_instance_size_name = "M0"
}