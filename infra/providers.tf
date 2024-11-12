provider "google" {
  credentials = var.google_credentials
  project     = "crowemi-io-417402"
  region      = "us-west1"
}