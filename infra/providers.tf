provider "google" {
  credentials = var.google_credentials
  project     = "crowemi-io-417402"
  region      = "us-west1"
}

provider "mongodbatlas" {
  public_key = var.atlas_public_key
  private_key  = var.atlas_private_key
}
