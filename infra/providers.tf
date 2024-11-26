provider "google" {
  credentials = var.google_credentials
  project     = var.google_project_id
  region      = "us-west1"
}

provider "mongodbatlas" {
  public_key  = var.atlas_public_key
  private_key = var.atlas_private_key
}
