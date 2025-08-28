from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.conf import settings


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
        filename = serializer.validated_data['name']
        full_name = settings.PRIVATE_MOUNT / filename
        print(f'Received object {serializer.validated_data}')
        print(f'We expect to be able to open the file with {full_name=}')
        with open(full_name) as f:
            data = f.read()
        print(f'Opened the file and got {data=}')
        return Response(status=status.HTTP_204_NO_CONTENT)
