import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.conf import settings
from content_extraction.process import process_file


logger = logging.getLogger(__name__)


class EventarcMessageSerializer(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.CharField()
    selfLink = serializers.URLField()
    name = serializers.CharField()
    bucket = serializers.CharField()
    generation = serializers.CharField()
    metageneration = serializers.CharField()
    contentType = serializers.CharField()
    timeCreated = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    storageClass = serializers.CharField()
    timeStorageClassUpdated = serializers.DateTimeField()
    size = serializers.CharField()
    md5Hash = serializers.CharField()
    mediaLink = serializers.URLField()
    crc32c = serializers.CharField()
    etag = serializers.CharField()


class EventarcHandler(APIView):
    def post(self, request, format=None):
        serializer = EventarcMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # You can process the validated data here
        # For demonstration, just return the validated data
        filename: str = serializer.validated_data['name']
        logger.info(f'Recieived request to process {filename=}')
        if not filename.startswith(settings.UPLOAD_FOLDER_NAME) or filename == f'{settings.UPLOAD_FOLDER_NAME}/':
            """
            Do not process files that were uploaded to a diff folder than the upload folder
            """
            return Response(status=status.HTTP_204_NO_CONTENT)

        full_name = str(settings.PRIVATE_MOUNT / filename)
        output_dir = settings.PRIVATE_MOUNT / 'process-results'
        process_file(full_name, output_dir)
        section_digest_file = output_dir / 'sections.jsonl'
        logger.info(f'We should now try to process the {section_digest_file=}')
        return Response(status=status.HTTP_204_NO_CONTENT)
