from django.contrib import admin
from .models import KnowledgeDocument, DocumentChunk

@admin.register(KnowledgeDocument)
class DocAdmin(admin.ModelAdmin):
    list_display  = ["title","doc_type","source_id","is_indexed","is_active","created_at"]
    list_filter   = ["doc_type","is_indexed","is_active"]
    search_fields = ["title","source_id","content"]
    list_editable = ["is_active"]
    readonly_fields = ["created_at","updated_at","indexed_at"]

@admin.register(DocumentChunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ["document","chunk_idx","token_count"]
