from django.apps import apps
from django.db import models


def instance_to_str(instance: models.Model) -> str:
    """
    Convert a model instance into a unique string of the form:
    "app_label:model_name:pk"
    """
    assert instance is not None, 'This function cannot accept NoneType, pass models.Model instead'
    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    pk = instance.pk
    return f'{app_label}:{model_name}:{pk}'


def str_to_instance(instance_str: str) -> models.Model:
    """
    Given a string of the form "app_label:model_name:pk", return the corresponding model instance.
    Raises DoesNotExist if the object does not exist.
    """
    try:
        app_label, model_name, pk_str = instance_str.split(':')
    except ValueError:
        raise ValueError("String format must be 'app_label:model_name:pk'")

    model = apps.get_model(app_label=app_label, model_name=model_name)
    return model.objects.get(pk=pk_str)


class ObjectIdentifierMixin:
    @property
    def unique_object_instance_identifier(self) -> str:
        return instance_to_str(self)
