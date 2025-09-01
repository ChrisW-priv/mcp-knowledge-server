from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.cloud import storage
from django.conf import settings

import uuid_utils as uuid


class SignedURLUploadView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user

        # Generate a unique ID for the file to be uploaded
        # Using uuid4 as uuidv7 is not standard in Python's uuid module
        file_id = str(uuid.uuid7())

        # Construct the full path in GCS bucket
        # Assuming user.id is a suitable identifier for folder structure
        full_path = f'{user.id}/{file_id}'

        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(settings.UPLOAD_BUCKET_NAME)
            blob = bucket.blob(full_path)
        except Exception as e:
            return Response({"error": f"GCS client initialization failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate the signed URL with the x-goog-if-generation-match header
        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=3600,  # URL expires in 1 hour
                method="PUT",
                headers={"x-goog-if-generation-match": "0"},
                content_type="application/octet-stream" # Or whatever content type you expect
            )
            return Response({"signed_url": signed_url, "file_id": file_id}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to generate signed URL: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
