from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from chat.models import ChatSession, SupportTicket
from documents.models import KnowledgeDocument
from monitoring.models import QueryLog
from rag_engine.pipeline import RAGPipeline

@login_required
def dashboard(request):
    profile  = request.user.profile
    pipeline = RAGPipeline.get()
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    tickets  = SupportTicket.objects.filter(user=request.user)
    recent   = QueryLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    is_ready = pipeline.is_ready()
    stats = {
        'sessions':      sessions.count(),
        'tickets':       tickets.count(),
        'docs_indexed':  KnowledgeDocument.objects.filter(is_active=True, is_indexed=True).count(),
        'rag_ready':     is_ready,
        'total_indexed': pipeline.store.total if is_ready else 0,
    }
    return render(request, 'dashboard/dashboard.html', {
        'profile': profile, 'sessions': sessions[:5],
        'tickets': tickets[:5], 'recent_queries': recent, 'stats': stats,
    })

def landing(request):
    if request.user.is_authenticated: return redirect('dashboard')
    return render(request, 'dashboard/landing.html')
