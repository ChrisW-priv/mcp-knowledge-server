from django.db import models
from django.contrib.auth.models import User


class Chat(models.Model):
    name = models.TextField(blank=False)

    def __str__(self):
        return self.name


class ChatMessage(models.Model):
    chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="chat_messages"
    )
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="user")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Latest messages appear first from the most recent chats
        ordering = ["-chat", "-timestamp"]
