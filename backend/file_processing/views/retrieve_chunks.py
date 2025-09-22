from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from file_processing.utils import retrieve_relevant_queries_subject_filtered


class RetrieveChunkSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=20, min_value=1, max_value=100)


class RetrieveChunksAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RetrieveChunkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        query = serializer.validated_data["query"]
        top_k = serializer.validated_data["top_k"]

        filtered_non_empty = retrieve_relevant_queries_subject_filtered(
            user.username, query, top_k
        )
        return Response(
            {
                "contents": filtered_non_empty,
            },
            status=status.HTTP_200_OK,
        )
