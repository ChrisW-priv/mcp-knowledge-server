from dataclasses import dataclass, asdict
import logging
from typing import Iterable
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.conf import settings
from django.contrib.auth.models import User
from content_extraction.process import process_file
import uuid_utils as uuid

from file_processing.models import KnowledgeSource, QueryVector
from file_processing.utils import embed_content
import json
from functools import partial
from pathlib import Path
import os


logger = logging.getLogger(__name__)


class EventarcMessageSerializer(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.CharField()
    selfLink = serializers.URLField()
    name = serializers.CharField()  # Name of the object within the bucket
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


PROCESS_RESULTS_FOLDER = "process-results"


class EventarcHandler(APIView):
    def post(self, request, format=None):
        serializer = EventarcMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # You can process the validated data here
        # For demonstration, just return the validated data
        object_name: str = serializer.validated_data["name"]
        logger.info(f"Recieived request to process {object_name=}")
        if object_name.endswith("/"):
            """
            If the object is a folder, do nothing
            """
            return Response(status=status.HTTP_204_NO_CONTENT)
        if object_name.startswith(settings.UPLOAD_FOLDER_NAME):
            process_file_to_sections(object_name)
            return Response(status=status.HTTP_204_NO_CONTENT)
        if (
            object_name.startswith(PROCESS_RESULTS_FOLDER)
            and object_name.endswith(".json")
            and "chunks" in object_name
        ):
            index_chunk(object_name)
            return Response(status=status.HTTP_204_NO_CONTENT)
        if (
            object_name.startswith(PROCESS_RESULTS_FOLDER)
            and object_name.endswith(".json")
            and "queries" in object_name
        ):
            process_query(object_name)
            return Response(status=status.HTTP_204_NO_CONTENT)

        """
        In all other cases, do nothing,
        for the object is neither a folder nor a file in the correct folder
        """
        return Response(status=status.HTTP_204_NO_CONTENT)


def process_file_to_sections(object_name: str):
    file_id = str(uuid.uuid7())
    output_dir = settings.PRIVATE_MOUNT / PROCESS_RESULTS_FOLDER / file_id

    _, owner_username, filename = object_name.split("/")
    file_db_name = "/".join((owner_username, filename))
    if not KnowledgeSource.objects.filter(file=file_db_name).exists():
        """
        It is possible for the file to have been uploaded by a user in an admin panel.
        If that is the case, we already have a KnowledgeSource object for it.
        But if not, we need to create one:
        """
        ks = KnowledgeSource(owner=User.objects.get(username=owner_username))
        ks.file.name = file_db_name
        ks.save()

    os.makedirs(output_dir, exist_ok=True)
    with open(output_dir / "METADATA", "w") as f:
        f.write(f"Original Filename: {object_name}\n")
        f.write(f"Original Owner ID: {owner_username}\n")

    process_file(
        input_path=str(settings.PRIVATE_MOUNT / object_name), output_dir=output_dir
    )

    section_digest_file = output_dir / "sections.jsonl"
    logger.info(f"We should now try to process the {section_digest_file=}")


def insert_vector(object_name, knowledge_source, content_embedding):
    logger.info(f"Started Inserting vector for {object_name=}")
    vector = content_embedding.values
    cv = QueryVector(
        knowledge_source=knowledge_source,
        vector=vector,
        embedding_model="text-embedding-3-large",
    )  # Hardcoded embedding model for now (TODO: FIX)
    cv.file.name = object_name
    cv.save()
    logger.info(f"Done Inserting vector for {object_name=}")


def index_chunk(object_name: str):
    """
    Indexes a chunk of data by generating queries and saving them to a file.
    """
    logger.info(f"Started indexing {object_name=}")
    queries = generate_queries(object_name)
    path_to_file_processing_root = (
        settings.PRIVATE_MOUNT / Path(object_name).parent.parent
    )
    path_to_queries = path_to_file_processing_root / "queries"
    os.mkdir(path_to_queries, exist_ok=True)
    logger.info(f"Created {path_to_queries=}")
    for i, query in enumerate(queries):
        with open(path_to_queries / f"{i}.json", "w") as f:
            json.dump(asdict(query), f)
            logger.info(f"Saved query {i} to {path_to_queries}")
    logger.info(f"Finished indexing {object_name=}")


@dataclass
class Query:
    query: str
    answer: str


def generate_queries(object_name: str) -> Iterable[Query]:
    """
    Returns an Iterable[dict] of query and answer for a given object_name.
    """
    file_path = str(settings.PRIVATE_MOUNT / object_name)
    with open(file_path, "r") as f:
        data = json.load(f)
    title = data.get("title")
    if not title:
        raise ValueError(f"Title not found in {object_name}")
    text = data.get("text")
    if not text:
        raise ValueError(f"Text not found in {object_name}")

    if title and text:
        yield Query(title, text)
        yield Query(text, text)


def process_query(object_name: str):
    file_path = str(settings.PRIVATE_MOUNT / object_name)
    with open(file_path, "r") as f:
        data: dict[str, str] = json.load(f)

    query = data.get("query")
    if not query:
        raise ValueError(f"Query not found in {object_name}")

    path_to_metadata = (
        settings.PRIVATE_MOUNT / Path(object_name).parent.parent / "METADATA"
    )
    with open(path_to_metadata, "r") as f:
        metadata = f.read()
    text_to_find = "Original Filename: "
    position_start = metadata.find(text_to_find)
    filename = metadata[position_start + len(text_to_find) : metadata.find("\n")]
    ks_filename = filename[len("django-uploads/") :]
    ks = KnowledgeSource.objects.get(file=ks_filename)
    embeddings = embed_content(query)
    insert_vector_to_chunk = partial(insert_vector, object_name, ks)
    any(map(insert_vector_to_chunk, embeddings))

    logger.info(f"Done indexing {object_name=}")
