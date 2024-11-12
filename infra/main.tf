locals {
  region  = var.google_region
  service = var.service_name
  project = var.google_project_id
}


resource "google_cloud_run_v2_service" "this" {
  name     = local.service
  location = local.region
  template {
    containers {
      image = "us-west1-docker.pkg.dev/${local.project}/crowemi-io/${local.service}:${var.docker_image_tag}"
    }
    vpc_access{
      network_interfaces {
        network = "crowemi-io-network" # TODO: ref data
        subnetwork = "crowemi-io-subnet-01" # TODO: ref data
        tags = ["crowemi-io-api"]
      }
      egress = "ALL_TRAFFIC"
    }
    service_account = google_service_account.this.email
  }
}

resource "google_cloud_scheduler_job" "crowemi-trades-scheduler" {
  name             = local.project
  region           = local.region
  schedule         = "*/30 * * * *"
  time_zone        = "America/New_York"
  attempt_deadline = "320s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = google_cloud_run_v2_service.this.uri

    oidc_token {
      service_account_email = google_service_account.this.email
    }
  }

  # Use an explicit depends_on clause to wait until API is enabled
  depends_on = [
    google_project_service.scheduler_api
  ]
}
