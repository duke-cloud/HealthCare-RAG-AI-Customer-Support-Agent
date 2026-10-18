from django.db import models
from django.contrib.auth.models import User

class QueryLog(models.Model):
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    query_text = models.TextField()
    risk_level = models.CharField(max_length=20)
    escalated  = models.BooleanField(default=False)
    method     = models.CharField(max_length=50)
    confidence = models.FloatField(null=True)
    latency_ms = models.IntegerField(null=True)
    chunks_used= models.IntegerField(default=0)
    sources    = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']

class SystemMetric(models.Model):
    date           = models.DateField(auto_now_add=True)
    total_queries  = models.IntegerField(default=0)
    escalated      = models.IntegerField(default=0)
    phi_blocked    = models.IntegerField(default=0)
    avg_confidence = models.FloatField(default=0)
    avg_latency_ms = models.FloatField(default=0)
    thumbs_up      = models.IntegerField(default=0)
    thumbs_down    = models.IntegerField(default=0)
    docs_indexed   = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'
