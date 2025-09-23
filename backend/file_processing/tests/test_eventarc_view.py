import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status

from file_processing.views import eventarc


@pytest.fixture
def mock_serializer():
    serializer = MagicMock()
    serializer.is_valid.return_value = True
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
