terraform {
  backend "remote" {}
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.20.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "1.21.4"
    }
  }
}
