locals {
  region  = var.google_region
  service = var.service_name
  project = var.google_project_id
}


resource "google_cloud_run_v2_service" "crowemi_io_api" {
  name     = local.service
  location = local.region
  launch_stage = "BETA"
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    containers {
      image = "us-west1-docker.pkg.dev/${local.project}/crowemi-io/${local.service}:${var.docker_image_tag}"
      env {
        name  = "AWS_ACCESS_KEY_ID"
        value_source {
          secret_key_ref {
            secret = data.google_secret_manager_secret.aws_access_key_id.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "AWS_SECRET_ACCESS_KEY"
        value_source {
          secret_key_ref {
            secret = data.google_secret_manager_secret.aws_secret_access_key.secret_id
            version = "latest"
          }
        }
      }
    }
    vpc_access{
      network_interfaces {
        network = "crowemi-io-network" # TODO: ref data
        subnetwork = "crowemi-io-subnet-01" # TODO: ref data
        tags = ["crowemi-io-api"]
      }
      egress = "ALL_TRAFFIC"
    }
    service_account = google_service_account.service_account.email
  }
}

data "google_service_account" "srv_crowemi_io" {
  account_id = "srv-crowemi-io"
  project = local.project
}
data "google_iam_policy" "private" {
  binding {
    role = "roles/run.invoker"
    members = [
      "serviceAccount:${data.google_service_account.srv_crowemi_io.email}",
    ]
  }
}
resource "google_cloud_run_service_iam_policy" "private" {
  location = google_cloud_run_v2_service.crowemi_io_api.location
  project  = google_cloud_run_v2_service.crowemi_io_api.project
  service  = google_cloud_run_v2_service.crowemi_io_api.name

  policy_data = data.google_iam_policy.private.policy_data
}