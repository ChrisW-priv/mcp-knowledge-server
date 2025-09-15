from django.urls import path
from .views.eventarc import EventarcHandler
from .views.retrieve_chunks import RetrieveChunksAPIView
from .views.signed_urls import SignedURLUploadView

urlpatterns = [
    path("", EventarcHandler.as_view()),
    path("get-chunks/", RetrieveChunksAPIView.as_view(), name="retrieve-chunks"),
    path("signed-url/", SignedURLUploadView.as_view(), name="signed-url-upload"),
]
