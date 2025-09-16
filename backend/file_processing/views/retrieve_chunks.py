from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.conf import settings
import json

from file_processing.utils import (
    embed_content,
    filter_chunks_by_subject_access,
    sort_chunks_by_relevance,
)


class RetrieveChunkSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=20, min_value=1, max_value=100)


def chunk_content(chunk_name: str):
    path = settings.PRIVATE_MOUNT / chunk_name
    with open(path) as f:
        file = json.load(f)
    return file.get("text", "")


class RetrieveChunksAPIView(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RetrieveChunkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        query = serializer.validated_data["query"]
        top_k = serializer.validated_data["top_k"]

        chunks_accessible = filter_chunks_by_subject_access(user.username)
        embedding = embed_content(query)
        sorted = sort_chunks_by_relevance(chunks_accessible, embedding)
        file_names = [chunk.file.name for chunk in sorted[:top_k]]
        contents = map(chunk_content, file_names)
        filtered_non_empty = list(map(lambda chunk: chunk, contents))
        return Response(
            {
                "contents": filtered_non_empty,
            },
            status=status.HTTP_200_OK,
        )
