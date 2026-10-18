from django.contrib import admin
from .models import ChatSession, ChatMessage, MessageFeedback, SupportTicket

@admin.register(ChatSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["user","title","is_active","created_at"]
    list_filter  = ["is_active"]

@admin.register(ChatMessage)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ["session","role","risk_level","escalated","confidence","latency_ms","created_at"]
    list_filter   = ["role","risk_level","escalated"]
    readonly_fields = ["created_at"]

@admin.register(MessageFeedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["message","rating","created_at"]

@admin.register(SupportTicket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ["user","subject","status","created_at"]
    list_filter   = ["status"]
    list_editable = ["status"]
