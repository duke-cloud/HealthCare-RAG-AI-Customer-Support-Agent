import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import KnowledgeDocument
from rag_engine.pipeline import ingest_documents
from rag_engine.phi_detector import redact_phi

is_admin = lambda u: u.is_staff

@login_required
@user_passes_test(is_admin)
def doc_list(request):
    docs = KnowledgeDocument.objects.filter(is_active=True)
    return render(request, 'documents/doc_list.html', {'docs': docs})

@login_required
@user_passes_test(is_admin)
def doc_add(request):
    from .models import DOC_TYPES
    if request.method == 'POST':
        title    = request.POST.get('title','').strip()
        content  = request.POST.get('content','').strip()
        doc_type = request.POST.get('doc_type','general')
        tags     = request.POST.get('tags','')

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return redirect('doc_add')

        # Auto-generate source_id
        base = title.lower().replace(' ','-')[:40]
        source_id = f"{doc_type}-{base}-{KnowledgeDocument.objects.count()+1}"

        doc = KnowledgeDocument.objects.create(
            title=title, content=redact_phi(content),
            doc_type=doc_type, source_id=source_id,
            author=request.user, tags=tags,
        )
        messages.success(request, f'Document "{title}" added. Click "Re-index" to make it searchable.')
        return redirect('doc_list')
    from .models import DOC_TYPES
    return render(request, 'documents/doc_add.html', {'doc_types': DOC_TYPES})

@login_required
@user_passes_test(is_admin)
def reindex_all(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    docs = KnowledgeDocument.objects.filter(is_active=True)
    records = [{'id': d.id, 'title': d.title, 'content': d.content,
                'doc_type': d.doc_type, 'source_id': d.source_id,
                'date': d.created_at.strftime('%Y-%m-%d')} for d in docs]
    result = ingest_documents(records)
    if result['status'] == 'success':
        docs.update(is_indexed=True, indexed_at=timezone.now())
        return JsonResponse(result)
    return JsonResponse(result, status=500)

@login_required
@user_passes_test(is_admin)
def doc_delete(request, pk):
    doc = get_object_or_404(KnowledgeDocument, pk=pk)
    if request.method == 'POST':
        doc.is_active = False; doc.save()
        messages.success(request, 'Document removed.')
    return redirect('doc_list')
