"""
Healthcare RAG — Answer Generator
Uses Anthropic Claude API when available; falls back to extractive summarization.
"""
import os, re
from typing import List, Dict, Tuple
from django.conf import settings

SYSTEM_PROMPT = """You are a helpful customer support assistant for HealthCare Solutions.
Your role is to help patients and staff with administrative, operational, and policy-related questions.

STRICT RULES:
1. Answer ONLY using information from the retrieved documents provided.
2. For every factual claim, add a citation in brackets: [Source: doc_id]
3. Keep answers concise (max 150 words) with 1-3 actionable steps when relevant.
4. If the documents do not contain the answer, say exactly: "I couldn't find relevant information in our knowledge base. Please contact our support team at support@healthcare.com or call 1-800-HEALTH."
5. NEVER provide medical diagnoses, treatment recommendations, or prescription advice.
6. NEVER reproduce or reference any PHI (patient names, SSNs, DOBs, medical record numbers).
7. For any clinical/medical advice question, respond: "I'm not able to provide medical advice. If you are experiencing a medical emergency, call 911. For clinical questions, please contact your healthcare provider or our clinical support line."
8. Be empathetic, professional, and clear.
"""

CLINICAL_RESPONSE = (
    "⚕️ I'm not able to provide medical advice or clinical guidance. "
    "If you are experiencing a **medical emergency**, please call **911** immediately.\n\n"
    "For clinical questions:\n"
    "• Contact your **healthcare provider**\n"
    "• Call our **clinical support line**: 1-800-HEALTH-1\n"
    "• Visit the **nearest emergency room** if urgent\n\n"
    "I can help you with appointment scheduling, billing questions, policy information, and general support."
)

PHI_RESPONSE = (
    "🔒 Your message appears to contain sensitive personal health information (PHI). "
    "For your privacy and security, I cannot process requests containing personal identifiers.\n\n"
    "Please:\n"
    "• **Remove personal information** (name, SSN, date of birth, medical record number) from your question\n"
    "• Contact our **secure support portal** at portal.healthcare.com\n"
    "• Call **1-800-HEALTH** to speak with a secure support representative"
)


def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into LLM context."""
    parts = []
    for i, c in enumerate(chunks):
        sid   = c.get('source_id', f'doc_{i+1}')
        title = c.get('title', 'Unknown')
        dtype = c.get('doc_type', 'document')
        parts.append(
            f"[Source: {sid}] [{dtype.upper()}] {title}\n{c['content'][:800]}"
        )
    return "\n\n---\n\n".join(parts)


def generate_extractive(query: str, chunks: List[Dict]) -> Tuple[str, float]:
    """Fallback: extract most relevant sentence from best chunk."""
    if not chunks:
        return ("I couldn't find relevant information in our knowledge base. "
                "Please contact our support team.", 0.0)
    best     = chunks[0]
    content  = best.get('content', '')
    sid      = best.get('source_id', 'doc_1')
    title    = best.get('title', 'Healthcare Documentation')

    # Score sentences by query word overlap
    sentences = re.split(r'(?<=[.!?])\s+', content)
    q_words   = set(query.lower().split())
    scored    = [(sum(1 for w in s.lower().split() if w in q_words), s) for s in sentences if len(s) > 20]
    scored.sort(reverse=True)
    top_sents = [s for _, s in scored[:3]] if scored else sentences[:3]
    answer    = ' '.join(top_sents)
    if len(answer) > 400:
        answer = answer[:400] + '…'

    conf = min(0.95, best.get('score', 0.5))
    return f"{answer}\n\n[Source: {sid}] — {title}", conf


def generate_answer(
    query: str,
    chunks: List[Dict],
    risk_level: str = 'safe',
) -> Dict:
    """Main generation function. Returns answer dict with metadata."""

    # Safety gates
    if risk_level == 'phi':
        return {'answer': PHI_RESPONSE, 'confidence': 0.0,
                'sources': [], 'method': 'blocked_phi', 'escalated': True}
    if risk_level == 'clinical':
        return {'answer': CLINICAL_RESPONSE, 'confidence': 0.0,
                'sources': [], 'method': 'escalated_clinical', 'escalated': True}

    # Prepare sources list
    sources = [{'id': c.get('source_id'), 'title': c.get('title'),
                'score': round(c.get('score',0), 3)} for c in chunks]

    # Try Anthropic API
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or os.environ.get('ANTHROPIC_API_KEY', '')
    if api_key and chunks:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            context = build_context(chunks)
            user_msg = (
                f"User question: {query}\n\n"
                f"Retrieved documents:\n{context}\n\n"
                "Instructions:\n"
                "1. Answer using ONLY the information from the retrieved documents above.\n"
                "2. Add citations [Source: doc_id] for each factual claim.\n"
                "3. If not found in documents, say so and suggest contacting support.\n"
                "4. Do NOT provide medical advice or diagnoses.\n\n"
                "Answer:"
            )
            msg = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=getattr(settings, 'LLM_MAX_TOKENS', 600),
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            answer = msg.content[0].text
            return {'answer': answer, 'confidence': 0.92,
                    'sources': sources, 'method': 'claude_api', 'escalated': False}
        except Exception as e:
            pass  # Fall through to extractive

    # Extractive fallback
    if not chunks:
        return {
            'answer': ("I couldn't find relevant information in our knowledge base. "
                       "Please contact our support team at support@healthcare.com or call 1-800-HEALTH."),
            'confidence': 0.0, 'sources': [], 'method': 'no_results', 'escalated': False
        }
    answer, conf = generate_extractive(query, chunks)
    return {'answer': answer, 'confidence': conf,
            'sources': sources, 'method': 'extractive', 'escalated': False}
