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

    def get_conversation_history(self):
        """Get all messages formatted for template display and chatbot processing."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages.all()]


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


class ComplianceStatus(models.IntegerChoices):
    APPROVED = 1, "Approved"
    REJECTED = 2, "Rejected"


class ViolationType(models.IntegerChoices):
    JAILBREAK = 1, "Jailbreak"
    HARMFUL = 2, "Harmful Content"
    ABUSE = 3, "Abuse"


class ComplianceCheck(TimeStampedModel):
    message = models.ForeignKey(
        "Message",
        on_delete=models.CASCADE,
        related_name="compliance_checks",
    )
    status = models.IntegerField(choices=ComplianceStatus.choices, default=ComplianceStatus.APPROVED)
    violation_type = models.IntegerField(choices=ViolationType.choices, null=True, blank=True)
    reason = models.TextField(max_length=2000)

    def __str__(self):
        return f"ComplianceCheck {self.id} - {self.get_status_display()}"


class SafetyEvent(TimeStampedModel):
    class EventType(models.IntegerChoices):
        QUERY_BLOCKED = 1, "Query Blocked"
        POLICY_VIOLATION = 2, "Policy Violation"
        SUSPICIOUS_PATTERN = 3, "Suspicious Pattern"

    event_type = models.IntegerField(choices=EventType.choices)
    compliance_check = models.ForeignKey(
        ComplianceCheck,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="safety_events",
    )

    def __str__(self):
        return f"SafetyEvent {self.id} - {self.get_event_type_display()}"
