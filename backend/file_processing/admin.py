from django.contrib import admin
from .models import KnowledgeSource
from content_access_control.admin_permission import register_permission_admin


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin): ...


register_permission_admin(KnowledgeSource, [])
