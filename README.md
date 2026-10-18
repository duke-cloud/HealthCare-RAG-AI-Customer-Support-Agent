# 🏥 HealthCare RAG — AI Customer Support Agent

A production-ready **Retrieval-Augmented Generation (RAG)** system for healthcare customer support, built with Django, FAISS, scikit-learn, and Anthropic Claude AI. Answers patient and staff questions from your knowledge base with full source citations, PHI protection, and clinical query escalation.

---

## 🚀 Quick Start

```bash
git clone <repo> && cd healthcare_rag
chmod +x setup_and_run.sh && ./setup_and_run.sh
# → http://127.0.0.1:8000
```

**Demo credentials:**

| Role    | Username  | Password    | Access |
|---------|-----------|-------------|--------|
| Admin   | `admin`   | `admin123`  | Full admin + monitoring |
| Staff   | `agent1`  | `agent123`  | Staff + monitoring dashboard |
| Patient | `patient1`| `patient123`| Chat + tickets |
| Patient | `patient2`| `patient123`| Chat + tickets |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HealthCare RAG                        │
├───────────────────┬─────────────────────────────────────┤
│  Django Backend   │  RAG Engine                         │
│  ─────────────    │  ──────────                         │
│  accounts/        │  1. PHI Detection & Redaction        │
│  documents/       │     (regex patterns, HIPAA-aware)    │
│  chat/            │  2. Clinical Query Escalation        │
│  monitoring/      │     (keyword classifier → safe resp) │
│  dashboard/       │  3. TF-IDF + SVD Embeddings          │
│                   │     (LocalEmbedder, sklearn pipeline) │
├───────────────────┤  4. FAISS IndexFlatIP Vector Store   │
│  Frontend         │     (cosine similarity search)       │
│  ─────────────    │  5. TF-IDF Reranker                  │
│  HTML + CSS       │     (cross-encoder style reranking)  │
│  Vanilla JS       │  6. Anthropic Claude API Generation  │
│  Fetch API (AJAX) │     (grounded answers + citations)   │
│  Chart.js         │  7. Extractive Fallback              │
│                   │     (no API key required)            │
└───────────────────┴─────────────────────────────────────┘
```

---

## 🤖 RAG Pipeline (Query Flow)

```
User Question
     │
     ▼
┌─────────────────┐
│ PHI Detection   │ ──► PHI found → Block + guide to secure channel
│ (regex + HIPAA) │
└────────┬────────┘
         │ Safe
         ▼
┌─────────────────┐
│ Clinical Check  │ ──► Clinical intent → Escalate to care team
│ (keyword class) │
└────────┬────────┘
         │ Safe
         ▼
┌─────────────────┐
│ PHI Redaction   │  Redact any residual PHI from query text
└────────┬────────┘
         ▼
┌─────────────────┐
│ TF-IDF + SVD    │  Embed query → 384-dim vector
│ Embedding       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ FAISS Search    │  Top-K=6 nearest neighbours (cosine similarity)
│ (IndexFlatIP)   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ TF-IDF Reranker │  Cross-encoder style reranking → Top-3 chunks
└────────┬────────┘
         ▼
┌─────────────────┐
│ Answer Generator│  Claude API (grounded) OR Extractive fallback
│ + Citations     │  [Source: doc-id] for every factual claim
└────────┬────────┘
         ▼
┌─────────────────┐
│ Audit Log       │  Log to QueryLog (redacted, no PHI stored)
│ (HIPAA-aware)   │
└────────┬────────┘
         ▼
    JSON Response
```

---

## 🔒 Privacy & Safety Features

| Feature | Implementation |
|---------|---------------|
| **PHI Detection** | Regex patterns: SSN, phone, email, DOB, MRN, NPI, DEA |
| **PHI Redaction** | Auto-redact from documents before indexing & from query logs |
| **Clinical Escalation** | 30+ clinical keywords → automatic safe escalation response |
| **No PHI in Vectors** | All content redacted before embedding |
| **Audit Logging** | Every query logged with redacted text, method, latency |
| **Role-Based Access** | Patients, Staff, Admin with different capabilities |
| **Secure Responses** | Claude system prompt enforces no medical advice |

---

## 📦 Knowledge Base (14 Pre-loaded Documents)

| Type | Documents |
|------|-----------|
| FAQ | Appointment Scheduling, Billing & Insurance, Portal Troubleshooting |
| Policy | Patient Rights, Medical Records, COVID Protocols |
| Guideline | Emergency vs Urgent Care, Telehealth, Mental Health, Insurance, Lab Tests |
| Procedure | Prescription Refills |
| Onboarding | New Patient Registration |

---

## ⚙️ Manual Setup

```bash
# 1. Virtual environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Optionally add ANTHROPIC_API_KEY to .env

# 3. Database
python manage.py migrate

# 4. Build RAG index
python manage.py build_index

# 5. Create admin
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

---

## 🔧 Key Management Commands

```bash
# Rebuild FAISS index from all active documents
python manage.py build_index

# With custom chunk settings
python manage.py build_index --chunk-size 300 --overlap 60
```

---

## 💡 Adding Documents via Admin UI

1. Log in as `admin` or `agent1`
2. Go to **Knowledge Base → Add Document**
3. Enter title, type, and content
4. Click **Re-index All Documents** button
5. New content is immediately searchable in chat

---

## 📊 Monitoring Dashboard

Access at `/monitoring/` (staff only):
- Query volume trend (7 days)
- Answer method breakdown (Claude API / Extractive)
- Risk level distribution (Safe / Clinical / PHI)
- Full audit log with latency, confidence, sources
- User satisfaction (thumbs up/down)

---

## 📁 Project Structure

```
healthcare_rag/
├── manage.py
├── requirements.txt
├── setup_and_run.sh           # One-command setup
├── .env.example
├── healthcare_rag/            # Django project settings
├── accounts/                  # Auth, user profiles (Patient/Staff/Admin)
├── documents/                 # Knowledge base management + indexing UI
├── rag_engine/                # Core RAG pipeline
│   ├── phi_detector.py        # PHI detection & redaction
│   ├── embeddings.py          # TF-IDF + SVD local embedder
│   ├── vector_store.py        # FAISS IndexFlatIP wrapper
│   ├── retriever.py           # Semantic search + TF-IDF reranker
│   ├── generator.py           # Claude API + extractive fallback
│   ├── pipeline.py            # Orchestrator (singleton)
│   └── management/commands/
│       └── build_index.py     # CLI: python manage.py build_index
├── chat/                      # Chat sessions, messages, feedback, tickets
├── monitoring/                # Query logs, metrics, audit dashboard
├── dashboard/                 # Landing page + main user dashboard
├── media/indexes/             # FAISS index files (auto-generated)
│   ├── embedder.pkl           # Serialized TF-IDF + SVD pipeline
│   └── faiss_store/           # FAISS index + metadata
│       ├── index.faiss
│       ├── docs.pkl
│       └── meta.json
├── static/css/style.css       # Complete CSS design system
├── static/js/
│   ├── chat.js                # Real-time AJAX chat + feedback
│   └── admin.js               # Reindex button + Chart.js helpers
└── templates/                 # All HTML templates
```

---

## 🔌 Claude API Integration

When `ANTHROPIC_API_KEY` is set:
- Answers are generated by **Claude Sonnet** using retrieved context
- System prompt enforces: citations, no medical advice, max 150 words
- Temperature = 0 for maximum factual accuracy

Without API key:
- **Extractive fallback**: best-matching sentences from top chunk
- Still cites sources, still safe — fully functional for testing

---

## 🚀 Production Deployment

```bash
# Use gunicorn + nginx for production
pip install gunicorn
gunicorn healthcare_rag.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Set in .env for production:
DEBUG=False
DJANGO_SECRET_KEY=<long-random-key>
ALLOWED_HOSTS=yourdomain.com
```

**HIPAA Compliance Notes:**
- Use HTTPS in production (TLS certificate required)
- Enable database encryption for PHI fields
- Sign BAA with any cloud vendor (AWS HIPAA, Google Cloud HIPAA)
- Run PHI detection audit logs through SIEM
- Implement MFA for staff/admin accounts

---

Built for healthcare customer support 🏥 — Adaptable for any industry.
