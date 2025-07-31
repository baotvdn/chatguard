from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.models import TimeStampedModel


class Conversation(TimeStampedModel):
    """Model to store chat conversations."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations", help_text="User who owns this conversation"
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Conversation {self.id} - {self.created}"


class Message(TimeStampedModel):
    """Model to store individual messages in conversations."""

    class RoleChoices(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=RoleChoices.choices, default=RoleChoices.USER)
    content = models.TextField()

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
