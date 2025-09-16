from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from google.cloud import storage
from google.auth import default, impersonated_credentials
from django.conf import settings

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

        source_credentials, _ = default()
        service_account_email = source_credentials.service_account_email

        target_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=service_account_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # Use impersonated credentials (no extra parameters needed)
        try:
            storage_client = storage.Client(credentials=target_credentials)
            bucket = storage_client.bucket(settings.UPLOAD_BUCKET_NAME)
            blob_name = generate_upload_blob_name(user.id, filename)
            blob = bucket.blob(blob_name)
        except Exception as e:
            return Response(
                {"error": f"GCS client initialization failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Generate the signed URL with the x-goog-if-generation-match header
        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=3600,  # URL expires in 1 hour
                method="PUT",
                headers={
                    "x-goog-if-generation-match": "0",
                },
                content_type="application/octet-stream",
            )
            return Response(
                {"signed_url": signed_url},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to generate signed URL: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
