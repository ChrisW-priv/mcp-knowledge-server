from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

from content_access_control.policy_mixins import AddRemovePermissionPolicyMixin, AddRemoveGroupingPolicyMixin
from content_access_control.model_conversion import ObjectIdentifierMixin


class ExpectedModel(ObjectIdentifierMixin, models.Model): ...


class ContentAccessPermission(AddRemovePermissionPolicyMixin, models.Model):
    """
    Model used to encapsulate a generic link between
    "which *subject* can do which *action* on which *resource*"
    """
    subject_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='subject_type')
    subject_id = models.PositiveIntegerField()
    subject = GenericForeignKey('subject_content_type', 'subject_id')
    resource_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='resource_type')
    resource_id = models.PositiveIntegerField()
    resource = GenericForeignKey('resource_content_type', 'resource_id')
    action = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject_content_type', 'subject_id', 'resource_content_type', 'resource_id', 'action'],
                name='unique_subject_resource',
            )
        ]

    def get_identifiers(self):
        return (
            get_uuid_of_model(self.subject),
            get_uuid_of_model(self.resource),
            self.action,
        )

    def __str__(self):
        sub_type_str = self.subject._meta.model_name
        res_type_str = self.resource._meta.model_name
        return f'{sub_type_str} {self.subject} can do: {self.action} on {res_type_str} {self.resource}'

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.remove_policy()

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = ContentAccessPermission.objects.get(pk=self.pk)
            old_instance.remove_policy()

        super().save(*args, **kwargs)
        self.add_policy()


class PolicySubject(AddRemoveGroupingPolicyMixin, ObjectIdentifierMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    content_access_permission = GenericRelation(
        ContentAccessPermission,
        content_type_field='subject_content_type',
        object_id_field='subject_id',
    )

    def get_identifiers(self):
        return (self.user.username, self.unique_object_instance_identifier)

    def __str__(self):
        return self.user.username

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.remove_policy()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.add_policy()


class PolicySubjectGroup(AddRemoveGroupingPolicyMixin, ObjectIdentifierMixin, models.Model):
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    content_access_permission = GenericRelation(
        ContentAccessPermission,
        content_type_field='subject_content_type',
        object_id_field='subject_id',
    )

    def get_identifiers(self):
        return (self.unique_object_instance_identifier, self.parent_group.unique_object_instance_identifier)

    def __str__(self):
        parent = str(self.parent_group or '')
        SEP = ' - ' if parent else ''
        return f'{parent}{SEP}{self.name}'

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if not self.parent_group:
            return
        self.remove_policy()

    def save(self, *args, **kwargs):
        if self.pk:
            # Check if not self-referential
            assert self.parent_network_id != self.pk, (
                'Network parent cannot reference the network itself, choose different parent or set to null'
            )

            # Delete the old grouping policy
            old_instance = PolicySubjectGroup.objects.get(pk=self.pk)
            if old_instance.parent_network:
                old_instance.remove_policy()

        super().save(*args, **kwargs)
        if not self.parent_group:
            return
        self.add_policy()


class SubjectToGroup(AddRemoveGroupingPolicyMixin, ObjectIdentifierMixin, models.Model):
    subject = models.ForeignKey(PolicySubject, on_delete=models.CASCADE)
    subject_group = models.ForeignKey(PolicySubjectGroup, on_delete=models.CASCADE)

    def get_identifiers(self):
        return (self.subject.unique_object_instance_identifier, self.subject_group.unique_object_instance_identifier)

    def __str__(self):
        return f'Subject: "{self.subject}", assigned to: "{self.subject_group}"'

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.remove_policy()

    def save(self, *args, **kwargs):
        if self.pk:
            # Delete the old grouping policy
            old_instance = SubjectToGroup.objects.get(pk=self.pk)
            old_instance.remove_policy()
        super().save(*args, **kwargs)
        self.add_policy()


ModelType = models.Model | ExpectedModel


def get_uuid_of_model(model_instance: ModelType):
    if hasattr(model_instance, 'unique_object_instance_identifier'):
        return model_instance.unique_object_instance_identifier
    return str(model_instance)


class Feature(ObjectIdentifierMixin, models.Model):
    name = models.CharField(max_length=255)
    content_access_permission = GenericRelation(
        ContentAccessPermission,
        content_type_field='resource_content_type',
        object_id_field='resource_id',
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=['name'], name='unique_feature_name_constraint')]

    def __str__(self):
        return self.name
