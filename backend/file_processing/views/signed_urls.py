from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from google.cloud import storage
from google.auth import default
from google.auth.transport import requests as auth_requests
from django.conf import settings
import requests
from datetime import timedelta

from ..utils import generate_upload_blob_name


class EventarcMessageSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)


class SignedURLUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EventarcMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        filename = serializer.validated_data["filename"]

        try:
            credentials, _ = default()

            # Refresh credentials to get access token
            auth_request = auth_requests.Request()
            credentials.refresh(auth_request)

            # Get service account email from metadata service
            metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
            headers = {"Metadata-Flavor": "Google"}
            response = requests.get(metadata_url, headers=headers, timeout=5)
            service_account_email = response.text.strip()

            storage_client = storage.Client(credentials=credentials)
            bucket = storage_client.bucket(settings.UPLOAD_BUCKET_NAME)
            blob_name = generate_upload_blob_name(user.username, filename)
            blob = bucket.blob(blob_name)

            # Use IAM-based signing instead
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="PUT",
                headers={
                    "x-goog-if-generation-match": "0",
                },
                content_type="application/octet-stream",
                service_account_email=service_account_email,
                access_token=credentials.token,
            )

            return Response({"signed_url": signed_url}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
