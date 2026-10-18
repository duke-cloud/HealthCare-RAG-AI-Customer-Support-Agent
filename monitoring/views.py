import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import QueryLog
from chat.models import ChatMessage, MessageFeedback, SupportTicket
from documents.models import KnowledgeDocument

is_admin = lambda u: u.is_staff

@login_required
@user_passes_test(is_admin)
def monitoring_dashboard(request):
    now  = timezone.now()
    week = now - timedelta(days=7)

    logs     = QueryLog.objects.filter(created_at__gte=week)
    total_q  = logs.count()
    escalated= logs.filter(escalated=True).count()
    phi_block= logs.filter(risk_level='phi').count()
    avg_conf = logs.filter(confidence__isnull=False).aggregate(a=Avg('confidence'))['a'] or 0
    avg_lat  = logs.filter(latency_ms__isnull=False).aggregate(a=Avg('latency_ms'))['a'] or 0

    fb       = MessageFeedback.objects.filter(created_at__gte=week)
    thumbs_up= fb.filter(rating=1).count()
    thumbs_dn= fb.filter(rating=-1).count()

    # Daily query trend (7 days)
    trend = []
    for i in range(6,-1,-1):
        day = now - timedelta(days=i)
        cnt = QueryLog.objects.filter(
            created_at__date=day.date()).count()
        trend.append({'date': day.strftime('%b %d'), 'count': cnt})

    # Method breakdown
    methods = list(logs.values('method').annotate(c=Count('id')).order_by('-c'))

    # Risk breakdown
    risks = list(logs.values('risk_level').annotate(c=Count('id')))

    # Recent logs
    recent_logs = logs.order_by('-created_at')[:20]

    tickets = SupportTicket.objects.filter(status='open').count()
    docs    = KnowledgeDocument.objects.filter(is_active=True).count()
    indexed = KnowledgeDocument.objects.filter(is_active=True, is_indexed=True).count()

    return render(request, 'monitoring/dashboard.html', {
        'total_q': total_q, 'escalated': escalated, 'phi_block': phi_block,
        'avg_conf': round(avg_conf*100, 1), 'avg_lat': round(avg_lat),
        'thumbs_up': thumbs_up, 'thumbs_dn': thumbs_dn,
        'trend_json': json.dumps(trend),
        'methods_json': json.dumps(methods),
        'risks_json': json.dumps(risks),
        'recent_logs': recent_logs,
        'open_tickets': tickets, 'docs': docs, 'indexed': indexed,
    })
