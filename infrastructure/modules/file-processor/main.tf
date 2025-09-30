locals {
  # service-account creation flag & email
  is_creating_pubsub_sa        = var.pubsub_service_account_email == ""
  pubsub_service_account_email = local.is_creating_pubsub_sa ? google_service_account.pubsub_sa[0].email : var.pubsub_service_account_email
  run_service_name             = basename(var.cloudrun_application_id)
  cloud_run_url                = "https://${local.run_service_name}-${var.google_project_number}.${var.google_region}.run.app/"
}

# ─────────────────────────────── Service Accounts ─────────────────────────────────
# Original service account for Eventarc/Pub/Sub
resource "google_service_account" "pubsub_sa" {
  count        = local.is_creating_pubsub_sa ? 1 : 0
  account_id   = "eventarc-workflows-sa"
  display_name = "Eventarc Workflows Service Account"
}

# Cloud Function service account
resource "google_service_account" "cloud_function_sa" {
  account_id   = "gcs-processor-function-sa"
  display_name = "GCS Processor Cloud Function Service Account"
}

# Cloud Tasks service account
resource "google_service_account" "cloud_tasks_sa" {
  account_id   = "file-processing-tasks-sa"
  display_name = "File Processing Cloud Tasks Service Account"
}

# ─────────────────────────────── IAM for Eventarc SA ─────────────────────────────────
# Allow SA to read from input bucket and receive events
resource "google_storage_bucket_iam_member" "input_sa_viewer" {
  bucket = var.existing_input_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${local.pubsub_service_account_email}"
}

resource "google_project_iam_member" "eventarc_permissions" {
  for_each = toset([
    "roles/eventarc.eventReceiver",
    "roles/logging.logWriter",
  ])
  project = var.google_project_id
  role    = each.value
  member  = "serviceAccount:${local.pubsub_service_account_email}"
}

# ─────────────────────────────── IAM for Cloud Function SA ─────────────────────────────────
resource "google_project_iam_member" "function_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/cloudtasks.enqueuer",
  ])
  project = var.google_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Function needs to read from input bucket to get file metadata
resource "google_storage_bucket_iam_member" "function_bucket_viewer" {
  bucket = var.existing_input_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Allow Cloud Function SA to impersonate Cloud Tasks SA for OIDC token creation
resource "google_service_account_iam_member" "function_impersonate_tasks_sa" {
  service_account_id = google_service_account.cloud_tasks_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# ─────────────────────────────── IAM for Cloud Tasks SA ─────────────────────────────────
resource "google_project_iam_member" "tasks_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
  ])
  project = var.google_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_tasks_sa.email}"
}

# Cloud Tasks SA needs to invoke Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "tasks_run_invoker" {
  project  = var.google_project_id
  location = var.google_region
  name     = data.google_cloud_run_v2_service.existing_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_tasks_sa.email}"
}

# ─────────────────────────────── GCS Pub/Sub Integration ─────────────────────────────────
data "google_storage_project_service_account" "gcs_account" {}
resource "google_project_iam_member" "pubsubpublisher" {
  project = var.google_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

# ─────────────────────────────── Cloud Tasks OIDC Authentication ─────────────────────────────────
# Allow Cloud Tasks SERVICE AGENT to mint ID tokens for the tasks SA
resource "google_service_account_iam_member" "cloudtasks_agent_token_creator" {
  service_account_id = google_service_account.cloud_tasks_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${var.google_project_number}@gcp-sa-cloudtasks.iam.gserviceaccount.com"
}

# ─────────────────────────────── Cloud Function Setup ─────────────────────────────────
# Create zip from local directory
data "archive_file" "function_source" {
  type        = "zip"
  output_path = "${path.module}/function-source.zip"
  source_dir  = "${path.module}/function-code"
}

# Temporary bucket for function deployment
resource "google_storage_bucket" "temp_function_bucket" {
  name                        = "${var.google_project_id}-function-deployment"
  location                    = var.google_region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "function-${filemd5(data.archive_file.function_source.output_path)}.zip"
  bucket = google_storage_bucket.temp_function_bucket.name
  source = data.archive_file.function_source.output_path
}

# Ref to a Cloud Run service
data "google_cloud_run_v2_service" "existing_service" {
  name     = local.run_service_name
  location = var.google_region
  project  = var.google_project_id
}

# Cloud Function
resource "google_cloudfunctions2_function" "gcs_processor" {
  name        = "gcs-file-processor"
  location    = var.google_region
  description = "Process GCS events and enqueue tasks"

  build_config {
    runtime     = "python313"
    entry_point = "process_gcs_event"

    source {
      storage_source {
        bucket = google_storage_bucket.temp_function_bucket.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 100
    min_instance_count = 0
    available_memory   = "256Mi"
    timeout_seconds    = 60

    environment_variables = {
      GCP_PROJECT          = var.google_project_id
      GCP_REGION           = "europe-west1"
      QUEUE_NAME           = google_cloud_tasks_queue.file_processing_queue.name
      CLOUD_RUN_URL        = local.cloud_run_url
      CLOUD_TASKS_SA_EMAIL = google_service_account.cloud_tasks_sa.email
    }

    # Use dedicated Cloud Function service account
    service_account_email = google_service_account.cloud_function_sa.email
  }

  event_trigger {
    trigger_region = var.google_region
    event_type     = "google.cloud.storage.object.v1.finalized"
    retry_policy   = "RETRY_POLICY_RETRY"

    event_filters {
      attribute = "bucket"
      value     = var.existing_input_bucket_name
    }
  }

  depends_on = [
    google_storage_bucket_object.function_zip,
    google_cloud_tasks_queue.file_processing_queue,
    google_project_iam_member.function_permissions
  ]
}

# ─────────────────────────────── Cloud Tasks Queue ─────────────────────────────────
resource "google_cloud_tasks_queue" "file_processing_queue" {
  name     = "file-processing"
  location = "europe-west1"

  rate_limits {
    max_concurrent_dispatches = 5
    max_dispatches_per_second = 2.0
  }

  retry_config {
    max_attempts       = 5
    max_backoff        = "300s"
    min_backoff        = "5s"
    max_doublings      = 3
    max_retry_duration = "1800s" # 30 minutes
  }

  depends_on = [
    google_service_account.cloud_tasks_sa,
    google_project_iam_member.tasks_permissions
  ]
}
