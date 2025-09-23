import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from rest_framework import status
import json
import logging
from pathlib import Path

from file_processing.views import eventarc
from file_processing.views.eventarc import Query


logger = logging.getLogger(__name__)


@pytest.fixture
def mock_serializer():
    serializer = MagicMock()
    serializer.is_valid.returnvalue = True
    return serializer


@patch("file_processing.views.eventarc.process_file_to_sections")
def test_process_eventarc_message_uploads(mock_process_file, mock_serializer):
    mock_serializer.validated_data = {"name": "django-uploads/user/file.txt"}
    response = eventarc.process_eventarc_message(mock_serializer)
    mock_process_file.assert_called_once_with("django-uploads/user/file.txt")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@patch("file_processing.views.eventarc.index_chunk")
def test_process_eventarc_message_chunks(mock_index_chunk, mock_serializer):
    object_name = "process-results/some-id/chunks.json"
    mock_serializer.validated_data = {"name": object_name}
    response = eventarc.process_eventarc_message(mock_serializer)
    mock_index_chunk.assert_called_once_with(object_name)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@patch("file_processing.views.eventarc.process_query")
def test_process_eventarc_message_queries(mock_process_query, mock_serializer):
    object_name = "process-results/some-id/queries.json"
    mock_serializer.validated_data = {"name": object_name}
    response = eventarc.process_eventarc_message(mock_serializer)
    mock_process_query.assert_called_once_with(object_name)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_process_eventarc_message_folder(mock_serializer):
    mock_serializer.validated_data = {"name": "django-uploads/user/"}
    response = eventarc.process_eventarc_message(mock_serializer)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_process_eventarc_message_other(mock_serializer):
    mock_serializer.validated_data = {"name": "other/file.txt"}
    response = eventarc.process_eventarc_message(mock_serializer)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@patch("file_processing.views.eventarc.generate_queries")
@patch("file_processing.views.eventarc.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
@patch("file_processing.views.eventarc.settings")
def test_index_chunk(
    mock_settings, mock_open_file, mock_makedirs, mock_generate_queries
):
    object_name = "process-results/some-id/chunks/chunk1.json"
    mock_settings.PRIVATE_MOUNT = Path("/fake/mount")
    queries_dict = [
        {"query": "q1", "answer": 'foo"}bar{"baz'},
        {"query": "q2", "answer": 'baz"}bar{"foo'},
    ]
    queries = [Query(**query) for query in queries_dict]
    mock_generate_queries.return_value = queries

    eventarc.index_chunk(object_name)

    path_to_queries = Path("/fake/mount/process-results/some-id/queries")
    mock_makedirs.assert_called_once_with(path_to_queries, exist_ok=True)

    # Check that we open and write to the correct files
    expected_calls = [
        call(path_to_queries / "0.json", "w", encoding="utf-8"),
        call(path_to_queries / "1.json", "w", encoding="utf-8"),
    ]
    mock_open_file.assert_has_calls(expected_calls, any_order=True)

    write_args = [c.args[0] for c in mock_open_file().write.call_args_list]

    # Reconstruct the two json strings
    json_str1 = "".join(write_args[: len(write_args) // 2])
    json_str2 = "".join(write_args[len(write_args) // 2 :])
    logger.info("JSON string 1: %s", json_str1)
    logger.info("JSON string 2: %s", json_str2)

    written_json_1 = json.loads(json_str1)
    written_json_2 = json.loads(json_str2)

    assert [written_json_1, written_json_2] == queries_dict


@patch("file_processing.views.eventarc.insert_vector")
@patch("file_processing.views.eventarc.embed_content")
@patch("file_processing.views.eventarc.KnowledgeSource.objects.get")
@patch("builtins.open", new_callable=mock_open)
@patch("file_processing.views.eventarc.settings")
def test_process_query(
    mock_settings, mock_open_file, mock_ks_get, mock_embed_content, mock_insert_vector
):
    object_name = "process-results/some-id/queries/0.json"
    mock_settings.PRIVATE_MOUNT = Path("/fake/mount")

    # Mock file contents
    query_content = '{"query": "test query"}'
    metadata_content = "Original Filename: django-uploads/user/file.txt\n"
    mock_open_file.side_effect = [
        mock_open(read_data=query_content).return_value,
        mock_open(read_data=metadata_content).return_value,
    ]

    mock_embed_content.return_value = [[0.1, 0.2, 0.3]]
    mock_ks = MagicMock()
    mock_ks_get.return_value = mock_ks

    eventarc.process_query(object_name)

    mock_ks_get.assert_called_once_with(file="user/file.txt")
    mock_embed_content.assert_called_once_with("test query")
    mock_insert_vector.assert_called_once_with(object_name, mock_ks, [0.1, 0.2, 0.3])
