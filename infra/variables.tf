variable "google_credentials" {
  description = "GCP credentials"
  type        = string
}
variable "google_project_id" {
  description = "GCP project id"
  type        = string
}
variable "google_region" {
  description = "GCP region"
  type        = string
  default     = "us-west-2"
}

variable "docker_image_tag" {
  description = "The docker image tage to deploy"
  type        = string
  default     = "latest"
}
variable "service_name" {
  description = "The service name"
  type        = string
}
variable "env" {
  description = "The env name"
  type        = string
}