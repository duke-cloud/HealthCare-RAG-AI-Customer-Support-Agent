from django.db import models
from django.contrib.auth.models import User

class ChatSession(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title      = models.CharField(max_length=200, default='New Conversation')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

class ChatMessage(models.Model):
    ROLES = [('user','User'),('assistant','Assistant')]
    session     = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role        = models.CharField(max_length=20, choices=ROLES)
    content     = models.TextField()
    risk_level  = models.CharField(max_length=20, default='safe')
    escalated   = models.BooleanField(default=False)
    confidence  = models.FloatField(null=True, blank=True)
    method      = models.CharField(max_length=50, blank=True)
    sources     = models.JSONField(default=list)
    chunks_used = models.IntegerField(default=0)
    latency_ms  = models.IntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class MessageFeedback(models.Model):
    message   = models.OneToOneField(ChatMessage, on_delete=models.CASCADE, related_name='feedback')
    rating    = models.IntegerField()  # 1=thumbs up, -1=thumbs down
    comment   = models.TextField(blank=True)
    created_at= models.DateTimeField(auto_now_add=True)

class SupportTicket(models.Model):
    STATUS = [('open','Open'),('in_progress','In Progress'),('resolved','Resolved')]
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    session     = models.ForeignKey(ChatSession, on_delete=models.SET_NULL, null=True, blank=True)
    subject     = models.CharField(max_length=200)
    description = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='assigned_tickets', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
