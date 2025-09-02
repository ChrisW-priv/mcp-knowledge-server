from typing import Iterable
import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.utils import IntegrityError, ProgrammingError
from django.urls import reverse, NoReverseMatch


logger = logging.getLogger(__name__)


def get_features():
    content_access_control = getattr(settings, 'CONTENT_ACCESS_CONTROL', None)
    if not content_access_control:
        return
    default_features_to_setup = settings.CONTENT_ACCESS_CONTROL.get('DEFAULT', None)
    if not default_features_to_setup:
        return
    features_to_setup = default_features_to_setup.get('FEATURES', None)
    return features_to_setup


def add_features_from_settings(features_to_setup: Iterable[dict] | None):
    from .models import Feature  # noqa
    from dauthz.core import enforcer  # noqa

    for feat in features_to_setup or []:
        feat_name = feat.get('name')
        logger.debug(f'Configuring feature: "{feat_name}"')
        feat_endpoints = feat.get('endpoints', None)
        try:
            feat_instance, _ = Feature.objects.get_or_create(name=feat_name)
            logger.debug(f'Inserted feature: "{feat_name}" to Feature table')
        except IntegrityError:
            logger.debug(f'Integrity error on feature insert: "{feat_name}"')
            """
            Fail silently: do nothing if it already exists
            """
        for endpoint_name in feat_endpoints or []:
            try:
                # Attempt to resolve the URL normally
                endpoint = reverse(endpoint_name)
            except NoReverseMatch:
                # Handle cases where the URL requires arguments
                try:
                    endpoint = reverse(endpoint_name, kwargs={'path': ''})  # Provide default values
                except NoReverseMatch:
                    logger.warning(f'Could not resolve URL for endpoint "{endpoint_name}"')
                    continue  # Skip this endpoint if it cannot be resolved
            logger.debug(f'Adding "{endpoint=}", to feature "{feat_instance.unique_object_instance_identifier}"')
            enforcer.add_grouping_policy(endpoint, feat_instance.unique_object_instance_identifier)
        logger.debug(f'Done configuring feature: {feat_name}')


class ContentAccessControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content_access_control'

    def ready(self):
        features_to_setup = get_features()
        try:
            add_features_from_settings(features_to_setup)
        except ProgrammingError:
            return
