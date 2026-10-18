from django.contrib import admin
from .models import QueryLog, SystemMetric

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display  = ["user","query_text","risk_level","escalated","method","confidence","latency_ms","created_at"]
    list_filter   = ["risk_level","escalated","method"]
    readonly_fields = ["created_at"]
    search_fields = ["query_text"]

@admin.register(SystemMetric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ["date","total_queries","escalated","phi_blocked","avg_confidence"]
