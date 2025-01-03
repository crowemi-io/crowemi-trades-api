locals {
  region       = var.google_region
  service      = var.service_name
  project      = var.google_project_id
  env          = lower(var.env)
  display_name = local.env == "paper" ? "srv_${replace(local.service, "-", "_")}_${local.env}" : "srv_${replace(local.service, "-", "_")}"
  name         = local.env == "paper" ? "${local.service}-${local.env}" : local.service
}

resource "google_service_account" "this" {
  account_id   = "srv-${local.service}-${local.env}"
  display_name = local.display_name
  description  = "A service account for ${local.service} ${local.env}"
}

resource "google_cloud_run_domain_mapping" "this" {
    count = local.env == "prod" ? 1 : 0
    location = "us-west1"
    name     = "api-trades.crowemi.com"

    metadata {
        namespace = local.project
    }

    spec {
        route_name = google_cloud_run_v2_service.this.name
    }
}

resource "google_cloud_run_v2_service" "this" {
  name         = local.name
  project      = local.project
  location     = local.region
  launch_stage = "BETA"
  ingress      = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    containers {
      image = "us-west1-docker.pkg.dev/${local.project}/crowemi-io/${local.service}:${var.docker_image_tag}"
      env {
        name = "CONFIG"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.this.secret_id
            version = "latest"
          }
        }
      }
    }
    scaling {
      max_instance_count = 1
    }
    vpc_access {
      network_interfaces {
        network    = "crowemi-io-network"
        subnetwork = "crowemi-io-subnet-01"
      }
      egress = "ALL_TRAFFIC"
    }
    service_account = google_service_account.this.email
  }
}

data "google_iam_policy" "private" {
  binding {
    role = "roles/run.invoker"
    members = [
      "serviceAccount:${google_service_account.this.email}",
    ]
  }
}
resource "google_cloud_run_service_iam_policy" "private" {
  location = google_cloud_run_v2_service.this.location
  project  = google_cloud_run_v2_service.this.project
  service  = google_cloud_run_v2_service.this.name

  policy_data = data.google_iam_policy.private.policy_data
}


resource "google_cloud_scheduler_job" "this" {
  name             = local.name
  region           = local.region
  project          = local.project
  schedule         = "*/5 9-16 * * *"
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
}
