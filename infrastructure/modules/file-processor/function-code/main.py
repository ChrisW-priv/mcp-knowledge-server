import functions_framework
from google.cloud import tasks_v2
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_REGION")
QUEUE_NAME = os.environ.get("QUEUE_NAME")
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "").rstrip("/")
CLOUD_RUN_AUDIENCE = os.environ.get("CLOUD_RUN_AUDIENCE", CLOUD_RUN_URL)
CLOUD_TASKS_SA_EMAIL = os.environ.get("CLOUD_TASKS_SA_EMAIL")


@functions_framework.cloud_event
def process_gcs_event(cloud_event):
    data = cloud_event.data
    object_name = data.get("name", "")
    bucket_name = data.get("bucket", "")

    logger.info(f"Processing file: {object_name} from bucket: {bucket_name}")

    if object_name.endswith("/"):
        logger.info(f"Skipping folder: {object_name}")
        return "OK"

    if not (
        object_name.startswith("django-uploads/")
        or object_name.startswith("process-results/")
    ):
        logger.info(f"Skipping file not in target folders: {object_name}")
        return "OK"

    try:
        enqueue_processing_task(data)
        logger.info(f"Successfully enqueued task for {object_name}")
    except Exception as e:
        logger.error(f"Failed to enqueue task for {object_name}: {e}")
        raise

    return "OK"


def enqueue_processing_task(gcs_data):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)

    task_payload = {
        "kind": gcs_data.get("kind"),
        "id": gcs_data.get("id"),
        "selfLink": gcs_data.get("selfLink"),
        "name": gcs_data.get("name"),
        "bucket": gcs_data.get("bucket"),
        "generation": gcs_data.get("generation"),
        "metageneration": gcs_data.get("metageneration"),
        "contentType": gcs_data.get("contentType"),
        "timeCreated": gcs_data.get("timeCreated"),
        "updated": gcs_data.get("updated"),
        "storageClass": gcs_data.get("storageClass"),
        "timeStorageClassUpdated": gcs_data.get("timeStorageClassUpdated"),
        "size": gcs_data.get("size"),
        "md5Hash": gcs_data.get("md5Hash"),
        "mediaLink": gcs_data.get("mediaLink"),
        "crc32c": gcs_data.get("crc32c"),
        "etag": gcs_data.get("etag"),
    }

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": CLOUD_RUN_URL,  # must be actual run.app service URL
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(task_payload).encode("utf-8"),
            "oidc_token": {
                "service_account_email": CLOUD_TASKS_SA_EMAIL,
                "audience": CLOUD_RUN_AUDIENCE,
            },
        }
    }

    response = client.create_task(request={"parent": parent, "task": task})
    logger.info(f"Created task: {response.name}")
    return response
