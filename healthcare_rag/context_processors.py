def global_context(request):
    ctx = {}
    if not request.user.is_authenticated:
        return ctx
    try:
        from chat.models import ChatSession
        ctx['active_sessions'] = ChatSession.objects.filter(
            user=request.user, is_active=True).count()
    except Exception:
        ctx['active_sessions'] = 0
    try:
        from rag_engine.pipeline import RAGPipeline
        p = RAGPipeline.get()
        ctx['rag_ready']   = p.is_ready()
        ctx['index_total'] = p.store.total if p.is_ready() else 0
    except Exception:
        ctx['rag_ready']   = False
        ctx['index_total'] = 0
    return ctx
