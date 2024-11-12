terraform {
  backend "remote" {
    hostname = "app.terraform.io"
    organization = "crowemi-io"
    workspaces {
      name = "crowemi-trades"
    }
  }
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "5.20.0"
    }
  }
}