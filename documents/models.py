from django.db import models
from django.contrib.auth.models import User

DOC_TYPES = [
    ('faq','FAQ'),('policy','Policy'),('guideline','Clinical Guideline'),
    ('procedure','Procedure'),('form','Form'),('general','General'),
    ('onboarding','Onboarding'),('release_note','Release Note'),
]

class KnowledgeDocument(models.Model):
    title         = models.CharField(max_length=300)
    doc_type      = models.CharField(max_length=30, choices=DOC_TYPES, default='general')
    source_id     = models.CharField(max_length=100, unique=True)
    content       = models.TextField()
    file          = models.FileField(upload_to='documents/', null=True, blank=True)
    author        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    version       = models.CharField(max_length=20, default='1.0')
    is_active     = models.BooleanField(default=True)
    is_indexed    = models.BooleanField(default=False)
    confidence    = models.FloatField(default=1.0)
    tags          = models.CharField(max_length=300, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    indexed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.doc_type.upper()}] {self.title}"

class DocumentChunk(models.Model):
    document   = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name='chunks')
    chunk_idx  = models.IntegerField()
    content    = models.TextField()
    token_count= models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_idx']
