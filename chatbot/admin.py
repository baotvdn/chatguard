from django.contrib import admin

from chatbot.models import Conversation, Message


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