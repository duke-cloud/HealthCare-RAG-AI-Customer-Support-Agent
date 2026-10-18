#!/bin/bash
# ═══════════════════════════════════════════════════════
#  HealthCare RAG — One-Command Setup & Run
#  Usage: chmod +x setup_and_run.sh && ./setup_and_run.sh
# ═══════════════════════════════════════════════════════
set -e
echo ""
echo "🏥  HealthCare RAG — AI Customer Support Agent"
echo "================================================"

# 1. Python version check
python3 -c "import sys; assert sys.version_info>=(3,10), 'Python 3.10+ required'" \
  && echo "✅ Python OK"

# 2. Virtual environment
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate

# 3. Dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# 4. Env file
[ ! -f ".env" ] && cp .env.example .env && \
  echo "⚙️  .env created — optionally add ANTHROPIC_API_KEY for Claude AI answers"

# 5. Database migrations
echo "🗄️  Applying migrations..."
python manage.py makemigrations --no-input -q
python manage.py migrate --no-input -q
echo "✅ Database ready"

# 6. Create superuser
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    u=User.objects.create_superuser('admin','admin@healthcare.com','admin123')
    u.first_name='Admin'; u.last_name='User'; u.save()
    print('✅ Admin: admin / admin123')
else:
    print('ℹ️  Admin already exists')
"

# 7. Seed demo data
python manage.py shell -c "
from django.contrib.auth.models import User
from documents.models import KnowledgeDocument
if not KnowledgeDocument.objects.exists():
    exec(open('seed_knowledge_base.py').read())
    print('✅ Knowledge base seeded')
else:
    print(f'ℹ️  {KnowledgeDocument.objects.count()} documents already in KB')
"

# 8. Build RAG index
echo "🤖 Building FAISS vector index..."
python manage.py build_index
echo "✅ RAG index ready"

# 9. Static files
python manage.py collectstatic --no-input -v 0

echo ""
echo "══════════════════════════════════════════════════"
echo "🚀  Starting HealthCare RAG Server..."
echo "══════════════════════════════════════════════════"
echo ""
echo "   URL       : http://127.0.0.1:8000"
echo "   Admin     : http://127.0.0.1:8000/admin"
echo ""
echo "   👤 Admin  : admin    / admin123"
echo "   👤 Agent  : agent1   / agent123  (staff, can see monitoring)"
echo "   👤 Patient: patient1 / patient123"
echo "   👤 Patient: patient2 / patient123"
echo ""
echo "   💡 Set ANTHROPIC_API_KEY in .env for Claude AI answers"
echo "      Without it, extractive RAG answers are used (still fully functional)"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
python manage.py runserver 0.0.0.0:8000
