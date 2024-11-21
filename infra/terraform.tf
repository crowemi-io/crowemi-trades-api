terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "crowemi-io"
    workspaces {
      name = "${var.service_account}-${var.env}"
    }
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.20.0"
    }
  }
}