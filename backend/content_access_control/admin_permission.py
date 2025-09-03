from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from content_access_control.model_conversion import str_to_instance, instance_to_str
from content_access_control.models import (
    ContentAccessPermission,
    PolicySubject,
    PolicySubjectGroup,
)


class AccessPermissionBuilder:
    def __init__(
        self,
        resource_model,
        actions: list[str],
        app_label: str | None = None
    ):
        self.subject_models   = [(PolicySubject, 'PolicySubject'), (PolicySubjectGroup, 'SubjectGroup')]
        self.resource_model   = resource_model
        self.resource_label   = resource_model.__name__
        self.actions          = actions
        self.app_label        = app_label or resource_model._meta.app_label

        # define the raw form fields
        self.form_fields = {
            'subject_obj':  forms.ChoiceField(label='Subject',  required=True),
            'resource_obj': forms.ChoiceField(label='Resource', required=True),
        }
        if len(self.actions) > 1:
            self.form_fields['action'] = forms.ChoiceField(
                label='Action',
                choices=[(a, a.capitalize()) for a in self.actions],
                required=True,
            )

    def __call__(self):
        return self._build_content_access_permission_proxy(), self._build_admin_model_for_model_proxy()

    def _build_content_access_permission_proxy(self):
        """
        Dynamically creates a proxy of the permission_model.
        """
        class Meta:
            proxy     = True
            app_label = self.app_label

        # make a name by concatenating the subject class names
        name = f"{self.resource_label}ContentAccessPermission"

        attrs = {
            '__module__': self.resource_model.__module__,
            'Meta':       Meta,
            '__doc__':   f"Proxy for {self.resource_model.__name__} access permision model in {self.app_label}",
        }
        return type(name, (ContentAccessPermission,), attrs)

    def _build_admin_form_for_model_proxy(self):
        """
        Dynamically builds a ModelForm tied to the proxy model.
        """
        proxy_model = self._build_content_access_permission_proxy()
        class_name  = proxy_model.__name__ + "AdminForm"

        # Capture into locals to avoid late binding
        subject_models = self.subject_models
        resource_model = self.resource_model
        resource_label = self.resource_label
        actions        = self.actions

        # Copy the base fields
        form_fields = dict(self.form_fields)

        # __init__ will populate choices and handle initial/action defaults
        def __init__(form_self, *args, **kwargs):
            forms.ModelForm.__init__(form_self, *args, **kwargs)

            # build subject choices
            subj_choices = []
            for model, prefix in subject_models:
                subj_choices += [
                    (instance_to_str(obj), f"{prefix}: {obj}")
                    for obj in model.objects.all()
                ]
            form_self.fields['subject_obj'].choices = subj_choices

            # build resource choices
            res_choices = [
                (instance_to_str(obj), f"{resource_label}: {obj}")
                for obj in resource_model.objects.all()
            ]
            form_self.fields['resource_obj'].choices = res_choices

            # if editing an existing instance, set initial values
            if form_self.instance.pk:
                form_self.fields['subject_obj'].initial  = instance_to_str(form_self.instance.subject)
                form_self.fields['resource_obj'].initial = instance_to_str(form_self.instance.resource)
                if len(actions) > 1:
                    form_self.fields['action'].initial = getattr(
                        form_self.instance, 'action', actions[0]
                    )

            # if exactly one action, force it onto the instance
            if len(actions) == 1:
                form_self.instance.action = actions[0]
            elif len(actions) == 0:
                form_self.instance.action = ""

        def clean(form_self):
            chosen_sub = str_to_instance(form_self.cleaned_data['subject_obj'])
            sub_ct = ContentType.objects.get_for_model(type(chosen_sub))
            form_self.instance.subject_content_type = sub_ct
            form_self.instance.subject_id           = chosen_sub.pk

            chosen_res = str_to_instance(form_self.cleaned_data['resource_obj'])
            res_ct = ContentType.objects.get_for_model(type(chosen_res))
            form_self.instance.resource_content_type = res_ct
            form_self.instance.resource_id           = chosen_res.pk

            # if there are multiple actions, pick up the selected one
            if len(actions) > 1:
                form_self.instance.action = form_self.cleaned_data['action']
            elif len(actions) == 1:
                form_self.instance.action = actions[0]
            else:
                form_self.instance.action = ''

            cleaned_data = forms.ModelForm.clean(form_self)

            if ContentAccessPermission.objects.filter(
                subject_content_type=sub_ct,
                subject_id=chosen_sub.pk,
                resource_content_type=res_ct,
                resource_id=chosen_res.pk,
                action=form_self.instance.action,
            ).exclude(pk=form_self.instance.pk).exists():
                raise ValidationError("This Access Permission already exists.")

            return cleaned_data

        # build Meta inner class
        Meta = type(
            'Meta',
            (),
            {
                'model':  proxy_model,
                'fields': list(form_fields.keys()),
            }
        )

        # assemble all attrs into the dynamic form class
        attrs = {
            **form_fields,
            'Meta':   Meta,
            '__init__': __init__,
            'clean':     clean,
            '__module__': self.resource_model.__module__,
        }

        return type(class_name, (forms.ModelForm,), attrs)

    def _build_admin_model_for_model_proxy(self):
        class_name = f'{self.resource_label}ContentAccessPermissionAdmin'

        def get_queryset(_self, request):
            ct = ContentType.objects.get_for_model(self.resource_model)
            qs = admin.ModelAdmin.get_queryset(_self, request)
            return qs.filter(resource_content_type=ct)

        attrs = {
            'form': self._build_admin_form_for_model_proxy(),
            'get_queryset': get_queryset
        }

        return type(class_name, (admin.ModelAdmin, ), attrs)
