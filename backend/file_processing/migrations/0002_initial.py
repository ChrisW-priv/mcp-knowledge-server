import django.db.models.deletion
import file_processing.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("file_processing", "0001_enable_pgvector"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeSourceContentAccessPermission",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("content_access_control.contentaccesspermission",),
        ),
        migrations.CreateModel(
            name="KnowledgeSource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="")),
                (
                    "owner",
                    models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ChunkVector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="")),
                ("vector", file_processing.models.VectorField(blank=False, null=True)),
                (
                    "knowledge_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="file_processing.knowledgesource",
                    ),
                ),
            ],
        ),
    ]
