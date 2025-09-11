from django.urls import path
from .views.eventarc import EventarcHandler
from .views.signed_urls import SignedURLUploadView

urlpatterns = [
    path("", EventarcHandler.as_view()),
    path("signed-url/", SignedURLUploadView.as_view(), name="signed-url-upload"),
]
