from django.contrib import admin

from chatbot.models import ComplianceCheck, Conversation, Message, SafetyEvent


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "created", "modified"]
    list_filter = ["created", "modified"]
    search_fields = ["user__username", "user__email"]
    ordering = ["-created"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "content_preview", "created"]
    list_filter = ["role", "created"]
    search_fields = ["content"]
    ordering = ["-created"]

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ["id", "get_conversation", "message", "status", "violation_type", "created"]
    list_filter = ["status", "violation_type", "created"]
    search_fields = ["reason", "message__content"]
    ordering = ["-created"]
    readonly_fields = ["created", "modified"]

    def get_conversation(self, obj):
        return obj.message.conversation

    get_conversation.short_description = "Conversation"
    get_conversation.admin_order_field = "message__conversation"


@admin.register(SafetyEvent)
class SafetyEventAdmin(admin.ModelAdmin):
    list_display = ["id", "event_type", "compliance_check", "created"]
    list_filter = ["event_type", "created"]
    ordering = ["-created"]
    readonly_fields = ["created", "modified"]
