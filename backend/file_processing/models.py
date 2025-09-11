from django.db import models
from django.conf import settings
from content_access_control.policy_mixins import ResourceAccessPermissionMixin
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


class KnowledgeSource(ResourceAccessPermissionMixin, models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, default=1, on_delete=models.CASCADE
    )
    file = models.FileField()


class ChunkVector(models.Model):
    knowledge_source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE)
    file = models.FileField()
    vector = VectorField(null=True, blank=False)
