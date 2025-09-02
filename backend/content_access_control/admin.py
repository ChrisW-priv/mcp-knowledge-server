from casbin_adapter.models import CasbinRule
from django.contrib import admin

from .models import (
    Feature,
    PolicySubject,
    PolicySubjectGroup,
    SubjectToGroup,
)
from .admin_permission import AccessPermissionBuilder


class SubjectToGroupInline(admin.TabularInline):
    model = SubjectToGroup
    extra = 0


@admin.register(CasbinRule)
class CasbinRuleAdmin(admin.ModelAdmin): ...


@admin.register(PolicySubject)
class MemberAdmin(admin.ModelAdmin):
    inlines = [SubjectToGroupInline]


@admin.register(PolicySubjectGroup)
class NetworkAdmin(admin.ModelAdmin):
    inlines = [SubjectToGroupInline]


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin): ...


feature_control_permission = AccessPermissionBuilder(Feature, ['access'])
FeatureContentAccessPermission, FeatureAccessAdminForm  = feature_control_permission()

@admin.register(FeatureContentAccessPermission)
class FeatureContentAccessPermissionAdmin(admin.ModelAdmin):
    form = FeatureAccessAdminForm
