from django.contrib import admin
from .models import Chat, ChatMessage


class MessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    inlines = (MessageInline,)
    search_fields = ["id"]
