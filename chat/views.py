import json, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ChatSession, ChatMessage, MessageFeedback, SupportTicket
from rag_engine.pipeline import RAGPipeline
from monitoring.models import QueryLog

@login_required
def chat_home(request):
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    # Create default session if none
    if not sessions.exists():
        session = ChatSession.objects.create(user=request.user)
    else:
        session = sessions.first()
    return redirect('chat_session', pk=session.pk)

@login_required
def chat_session(request, pk):
    session  = get_object_or_404(ChatSession, pk=pk, user=request.user)
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    messages_qs = session.messages.all()
    pipeline = RAGPipeline.get()
    suggestions = [
        'How do I schedule an appointment?',
        'How do I reset my patient portal password?',
        'What are your billing and payment options?',
        'How do I request my medical records?',
        'What insurance plans do you accept?',
        'How do I contact my care team?',
    ]
    return render(request, 'chat/chat.html', {
        'session': session, 'sessions': sessions,
        'messages': messages_qs, 'is_ready': pipeline.is_ready(),
        'suggestions': suggestions,
    })

@login_required
def new_session(request):
    session = ChatSession.objects.create(user=request.user)
    return redirect('chat_session', pk=session.pk)

@login_required
@require_POST
def ask(request, pk):
    session = get_object_or_404(ChatSession, pk=pk, user=request.user)
    data    = json.loads(request.body)
    question= data.get('question','').strip()
    filters = data.get('filters', None)

    if not question:
        return JsonResponse({'error': 'Empty question'}, status=400)

    # Save user message
    user_msg = ChatMessage.objects.create(
        session=session, role='user', content=question)

    # Run RAG pipeline
    t0 = time.time()
    pipeline = RAGPipeline.get()
    result   = pipeline.query(question, user_id=str(request.user.id), filters=filters)
    latency  = int((time.time() - t0) * 1000)

    # Save assistant message
    asst_msg = ChatMessage.objects.create(
        session=session, role='assistant',
        content=result['answer'],
        risk_level=result['risk_level'],
        escalated=result['escalated'],
        confidence=result['confidence'],
        method=result['method'],
        sources=result['sources'],
        chunks_used=result['chunks_retrieved'],
        latency_ms=latency,
    )

    # Update session title from first question
    if session.messages.count() <= 2:
        session.title = question[:60] + ('…' if len(question)>60 else '')
        session.save()

    # Audit log
    QueryLog.objects.create(
        user=request.user,
        query_text=result['question'],  # redacted version
        risk_level=result['risk_level'],
        escalated=result['escalated'],
        method=result['method'],
        confidence=result['confidence'],
        latency_ms=latency,
        chunks_used=result['chunks_retrieved'],
        sources=result['sources'],
        session_id=str(session.id),
    )

    return JsonResponse({
        'msg_id':    asst_msg.id,
        'answer':    result['answer'],
        'sources':   result['sources'],
        'confidence':result['confidence'],
        'risk_level':result['risk_level'],
        'escalated': result['escalated'],
        'method':    result['method'],
        'latency_ms':latency,
    })

@login_required
@require_POST
def feedback(request, msg_id):
    msg  = get_object_or_404(ChatMessage, pk=msg_id, session__user=request.user)
    data = json.loads(request.body)
    rating  = int(data.get('rating', 0))
    comment = data.get('comment', '')
    MessageFeedback.objects.update_or_create(
        message=msg,
        defaults={'rating': rating, 'comment': comment},
    )
    return JsonResponse({'status': 'ok'})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        subject = request.POST.get('subject','').strip()
        desc    = request.POST.get('description','').strip()
        if subject and desc:
            SupportTicket.objects.create(
                user=request.user, subject=subject, description=desc)
            messages.success(request, 'Support ticket created! Our team will respond shortly.')
            return redirect('dashboard')
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    return render(request, 'chat/create_ticket.html', {'sessions': sessions})

@login_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(user=request.user)
    return render(request, 'chat/my_tickets.html', {'tickets': tickets})
