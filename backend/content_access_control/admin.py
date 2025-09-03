from casbin_adapter.models import CasbinRule
from django.contrib import admin
from django.contrib.admin.models import ContentType

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


admin.site.register(*AccessPermissionBuilder(Feature, ['access'])())
