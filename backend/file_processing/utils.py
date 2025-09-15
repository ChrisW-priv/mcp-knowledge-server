from openai import OpenAI
from content_access_control import core
from django.db.models.query import QuerySet
from django.db.models.expressions import RawSQL

from file_processing.models import ChunkVector


def generate_upload_blob_name(user_id, file_name):
    return f"django-uploads/{user_id}/{file_name}"


def embed_content(content: str | list[str]) -> list[float]:
    client = OpenAI()

    response = client.embeddings.create(input=content, model="text-embedding-3-large")

    return response.data[0].embedding


def embed_content_gemini(content: str | list[str]) -> list[float]:
    from google import genai

    client = genai.Client()
    result = client.models.embed_content(model="gemini-embedding-001", contents=content)
    return result.embeddings


def policies_assigned_to_subject(subject_identifier: str) -> list[list[str]]:
    """
    Function that retrieves all permission policies assigned to a subject.

    Args:
        subject_identifier (str): The identifier of the subject. Could be
        `unique_object_instance_identifier` if object implements the
        ObjectIdentifierMixin, or simply a username, if the Django User object
        is linked to a subject as it should.
    """
    if not isinstance(subject_identifier, str):
        raise ValueError("subject_identifier must be a string")
    policies = core.enforcer.get_implicit_permissions_for_user(subject_identifier)
    return policies


def subject_accessible_knowledge_sources(subject_identifier: str):
    def filter_predicate(policy: list[str]):
        return policy[1].startswith("file_processing:knowledgesource")

    def get_knowledge_source_id(policy: list[str]):
        return policy[1].split(":")[-1]

    policies = policies_assigned_to_subject(subject_identifier)
    filtered_policies = filter(filter_predicate, policies)
    ks_ids = map(get_knowledge_source_id, filtered_policies)

    return ks_ids


def filter_chunks_by_subject_access(subject_identifier: str) -> QuerySet[ChunkVector]:
    ks_ids = subject_accessible_knowledge_sources(subject_identifier)
    chunks = ChunkVector.objects.filter(knowledge_source__id__in=ks_ids)
    return chunks


def sort_chunks_by_relevance(
    chunks: QuerySet[ChunkVector], embedding: list[float]
) -> QuerySet[ChunkVector]:
    return chunks.annotate(distance=RawSQL("vector <=> %s", [str(embedding)])).order_by(
        "distance"
    )
