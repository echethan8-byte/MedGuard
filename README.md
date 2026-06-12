# ⚕ MedGuard — Healthcare Compliance RAG System

A full-stack, production-ready healthcare policy violation detection system using Retrieval-Augmented Generation (RAG), Chain-of-Thought reasoning, and a modern dark-terminal UI.

---

## 🏗 Architecture

```
React Frontend (Vite + TypeScript)
    ↓ HTTPS / JWT Auth
Django Backend (REST API + Celery)
    ├── Document Ingestion   → PyMuPDF / python-docx → Chunking → Embedding
    ├── ChromaDB             → Persistent vector store (policies + documents)
    ├── Retriever            → Similarity search (top-20) → FlashRank rerank (top-8)
    ├── LLM Analyzer         → Gemini 2.5 Flash / GPT-4o (Chain-of-Thought)
    ├── Guardrails           → Input PII scan + output validation
    ├── Report Generator     → ReportLab PDF with citations
    └── PostgreSQL           → Metadata, reports, audit logs
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (for Celery) — `brew install redis` / `sudo apt install redis-server`
- (Optional) PostgreSQL — SQLite works for dev

---

### Backend Setup

```bash
cd backend

# 1. Virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY or OPENAI_API_KEY
# Set USE_SQLITE=True for quick local dev

# 4. Create log directory
mkdir -p logs

# 5. Database migrations
python manage.py makemigrations core documents rag corpus guardrails
python manage.py migrate

# 6. Create superuser (for Django admin)
python manage.py createsuperuser

# 7. Start Django dev server
python manage.py runserver

# 8. Start Celery worker (separate terminal)
celery -A healthcare_rag worker --loglevel=info

# 9. (Optional) Load policy corpus
# Download PDFs to backend/corpus/policies/ then:
python manage.py shell -c "from corpus.loader import load_all_corpus; load_all_corpus()"
# If you have a separate folder such as the project root `pe/` with additional policy PDFs, load it directly:
python manage.py shell -c "from corpus.loader import load_all_corpus; load_all_corpus(corpus_dir=r'../pe')"
```

**Backend runs at:** `http://localhost:8000`
**API docs:** `http://localhost:8000/api/docs/`
**Admin panel:** `http://localhost:8000/admin/`

---

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
```

**Frontend runs at:** `http://localhost:5173`

> **Note:** The frontend includes rich mock data so you can explore the full UI without a backend connection. Just open it in the browser!

---

## 📁 Project Structure

```
healthcare-rag/
├── frontend/                       # React + TypeScript + Vite
│   └── src/
│       ├── App.tsx                 # Root with routing
│       ├── App.css                 # Dark medical terminal design system
│       ├── components/
│       │   ├── Sidebar.tsx         # Navigation
│       │   └── ScoreRing.tsx       # Animated compliance score ring
│       ├── pages/
│       │   ├── Dashboard.tsx       # Overview + stats + activity
│       │   ├── DocumentsPage.tsx   # Upload + document management
│       │   ├── AuditPage.tsx       # RAG audit pipeline + results
│       │   └── ReportsPage.tsx     # Report viewer + export
│       └── utils/
│           └── mockData.ts         # Types + realistic demo data
│
└── backend/                        # Django + DRF
    ├── manage.py
    ├── requirements.txt
    ├── .env.example
    ├── healthcare_rag/             # Project config
    │   ├── settings.py
    │   ├── urls.py
    │   └── celery.py
    ├── core/                       # Shared models + utilities
    │   ├── models.py               # Document, ComplianceReport, Violation, AuditLog
    │   ├── utils.py                # Chunking, embedding, ChromaDB helpers
    │   └── admin.py
    ├── documents/                  # Document CRUD + async indexing
    │   ├── views.py
    │   ├── serializers.py
    │   └── tasks.py                # Celery: extract → chunk → embed
    ├── rag/                        # Core RAG pipeline
    │   ├── retriever.py            # Similarity search + FlashRank reranking
    │   ├── analyzer.py             # CoT prompt + LLM call (Gemini/OpenAI)
    │   ├── report_generator.py     # ReportLab PDF generation
    │   ├── views.py                # Audit endpoint + download
    │   └── serializers.py
    ├── corpus/                     # Policy corpus management
    │   └── loader.py               # WHO/CDC/HHS/OSHA/TJC indexing
    └── guardrails/
        └── validator.py            # PII redaction + output validation
```

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token/` | Get JWT token |
| POST | `/api/auth/token/refresh/` | Refresh token |
| GET | `/api/documents/` | List documents |
| POST | `/api/documents/` | Upload document |
| DELETE | `/api/documents/{id}/` | Delete document |
| POST | `/api/documents/{id}/reindex/` | Re-index document |
| GET | `/api/documents/stats/` | Document statistics |
| POST | `/api/rag/audit/` | Run compliance audit |
| GET | `/api/rag/reports/` | List reports |
| GET | `/api/rag/reports/{id}/` | Get report detail |
| GET | `/api/rag/reports/{id}/download/` | Download PDF |
| GET | `/api/corpus/stats/` | Policy corpus stats |
| POST | `/api/corpus/reindex/` | Admin: reindex corpus |
| GET | `/api/core/audit-logs/` | System audit trail |
| GET | `/api/core/profile/` | Current user info |

---

## 🧠 RAG Pipeline

```
1. Document Upload
   ├── PyMuPDF / python-docx extraction
   ├── Text cleaning (noise removal)
   ├── Sentence-aware chunking (800 tokens, 100 overlap)
   └── Embedding (all-MiniLM-L6-v2) → ChromaDB

2. Compliance Audit
   ├── Query: "healthcare regulations infection control {doc_name}"
   ├── ChromaDB similarity search → top-20 policy chunks
   ├── FlashRank cross-encoder reranking → top-8
   ├── Context assembly (12,000 char limit)
   ├── Chain-of-Thought prompt → Gemini 2.5 Flash
   │   Step 1: Summarize hospital procedures
   │   Step 2: Map to each policy chunk
   │   Step 3: Identify gaps and mismatches
   │   Step 4: Assess risk (Critical/High/Medium/Low)
   │   Step 5: Generate corrective actions
   │   Step 6: Calculate compliance score (0–100)
   ├── Output guardrails validation
   └── PDF report generation (ReportLab)
```

---

## 🎨 UI Design System

- **Background:** `#05080F` — deep space black
- **Surface:** `#0A0F1E` — dark navy  
- **Accent:** `#00C9B8` — medical teal with glow
- **Critical:** `#EF4444` red · **High:** `#F59E0B` amber · **Low:** `#10B981` green
- **Fonts:** Space Grotesk (display) · Inter (body) · JetBrains Mono (data/code)
- **Aesthetic:** Medical diagnostic terminal — scan lines, monospace data, glowing rings

---

## 🔒 Security Features

- JWT authentication with refresh tokens
- Role-based permissions (Admin, Auditor, Viewer via Django groups)
- Rate limiting (100 req/hour authenticated, 20 anon)
- PII redaction in document text
- Prompt injection detection
- Audit trail for all actions
- CORS configuration
- File type validation (PDF/DOCX/TXT only, 50 MB max)

---

## 🗺 Development Roadmap

- **Phase 1 (Done):** Core RAG pipeline + React UI + PDF export
- **Phase 2:** WebSocket progress updates (Django Channels), hybrid search
- **Phase 3:** Multi-document comparison, feedback loop, fine-tuning
- **Phase 4:** HIPAA compliance mode, SSO/OAuth2, Pinecone migration

---

## 📋 Policy Corpus Sources

Download PDFs and place in `backend/corpus/policies/`:

| Organization | Document |
|---|---|
| WHO | Hand Hygiene Guidelines 2022 |
| WHO | IPC Core Components 2016 |
| CDC | NHSN Patient Safety Manual 2024 |
| CDC | HAP Prevention Guidelines |
| CDC | MDRO Management Guidelines |
| OSHA | Bloodborne Pathogens 29 CFR 1910.1030 |
| HHS | Hospital-Acquired Condition Reduction Program |
| TJC | Infection Control Standards 2024 |
| AHRQ | CUSP Safety Toolkit |

All documents are publicly available from their respective organizations' websites.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Custom CSS (no framework) — dark terminal design system |
| Backend | Django 5, Django REST Framework |
| Auth | JWT (simplejwt) |
| Async | Celery + Redis |
| Vector DB | ChromaDB (persistent) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Reranker | FlashRank (ms-marco-MiniLM-L-12-v2) |
| LLM | Gemini 2.5 Flash (primary) / GPT-4o (fallback) |
| PDF Extract | PyMuPDF (fitz), python-docx |
| PDF Reports | ReportLab |
| Database | PostgreSQL / SQLite (dev) |
| Guardrails | Custom regex + structural validation |
