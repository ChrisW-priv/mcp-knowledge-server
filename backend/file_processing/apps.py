import os
from django.apps import AppConfig
import dspy


class FileProcessingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "file_processing"

    def ready(self):
        key = os.environ.get("OPENAI_API_KEY")
        lm = dspy.LM("openai/gpt-4o-mini", api_key=key)
        dspy.configure(lm=lm)
