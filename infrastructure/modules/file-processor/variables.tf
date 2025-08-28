variable "google_project_id" {
  type        = string
  description = "GCP project to deploy into"
}

variable "google_project_number" {
  type        = string
  description = "GCP project number to deploy into"
}

variable "google_region" {
  type        = string
  description = "GCP region"
}

variable "cloudrun_application_id" {
  type        = string
  description = "ID of an application that we want to link to Event Arc"
}

variable "existing_input_bucket_name" {
  type        = string
  description = "If non-empty, use this bucket instead of creating a new one for inputs"
}

variable "service_account_email" {
  description = "The email of an existing service account to be used for Cloud Run."
  type        = string
}

variable "pubsub_service_account_email" {
  description = "The email of an existing service account to be used for pubsub topics. If provided, creation is skipped and this existing account is used. If empty, a new service account with a default name based on application_name will be created."
  type        = string
  default     = ""
}

variable "pubsub_topic_name" {
  type        = string
  default     = ""
  description = "Pub/Sub topic name for Eventarc to publish into (default: <app>-eventarc-topic)"
}
