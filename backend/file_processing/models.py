from django.db import models
from django.conf import settings
from content_access_control.policy_mixins import (
    ResourceAccessPermissionMixin,
    ObjectIdentifierMixin,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

import json


class VectorField(models.Field):
    """A field that adapts to the database backend"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            return "ArrayField"
        return "TextField"

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "vector"  # Will be handled by pgvector
        return "TEXT"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if connection.vendor == "postgresql":
            return value
        # For SQLite, parse JSON
        return json.loads(value) if value else None

    def to_python(self, value):
        if isinstance(value, list) or value is None:
            return value
        return json.loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            return value
        return json.dumps(value)


def upload_to(instance, filename):
    """Function that returns the path to upload the file to, based on who is uploading the file"""
    return f"{instance.owner.username}/{filename}"


class KnowledgeSource(
    ResourceAccessPermissionMixin, ObjectIdentifierMixin, models.Model
):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, default=1, on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=upload_to)


class QueryVector(ObjectIdentifierMixin, models.Model):
    knowledge_source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE)
    file = models.FileField()
    vector = VectorField(null=True, blank=False)
    embedding_model = models.CharField(max_length=255)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
