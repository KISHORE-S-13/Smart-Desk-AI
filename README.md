# SmartDesk AI – Generative AI Powered Unified Service Management (USM)

SmartDesk AI is an enterprise-grade IT Service Management (ITSM) and Unified Service Management platform powered by Google Gemini AI (`gemini-3.8-flash`) and Python Flask with a modern React + Vite frontend. It automates incident classification, priority detection, support team assignment, resolution suggestions, and knowledge retrieval through RAG.

---

## 🌟 Key Features

* **Intelligent Ticket Triage with Gemini AI**: Analyzes incident titles and descriptions to automatically extract category (`Network`, `Hardware`, `Software`, `Email`, `Access Management`, `Other`), calculate priority (`Low`, `Medium`, `High`, `Critical`), justify priority, assign the appropriate support team, and provide actionable troubleshooting checklists.
* **Deterministic Fallback Engine**: If Gemini is temporarily offline, rate-limited, or unavailable, SmartDesk AI automatically switches to a deterministic keyword-and-impact rule engine. Output source is clearly tagged (`gemini` vs `rule_based_fallback`).
* **Interactive IT Knowledge Assistant (RAG)**: Chatbot powered by Gemini and grounded in company standard operating procedures (SOPs). Retrieves matching company documentation (VPN, Wi-Fi, Password Reset, Outlook, Software Installation) to answer questions without inventing internal policies.
* **Document Ingestion with PyPDF**: Administrators can upload company SOPs or policy PDFs; text is extracted and indexed into the knowledge base for RAG queries.
* **Complete USM Lifecycle Automation**: Full transition management (`New` → `Triaged` → `Assigned` → `In Progress` → `Resolved` → `Closed`) with human-in-the-loop approvals, resolution notes, and audit history.
* **Enterprise Operations Dashboard**: Real-time KPI metrics, category breakdowns, team workload distribution, and recent incidents.
* **Vercel & Cloud Ready**: Single Page Application (SPA) frontend ready for Vercel, Flask serverless entrypoint (`api/index.py`), PostgreSQL-ready SQLAlchemy configuration, and local SQLite support.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite, JavaScript (ES6+), Vanilla CSS (Enterprise Navy & Light Blue) |
| **Backend** | Python 3.11+, Flask REST API, Flask-CORS, PyJWT |
| **Generative AI** | Google Gemini API via official `google-genai` SDK (`gemini-3.8-flash`) |
| **Database** | SQLite (development) / PostgreSQL (production) via SQLAlchemy ORM |
| **Document Processing** | PyPDF |
| **Deployment Target** | Vercel (Frontend & Serverless Python functions), PostgreSQL (Neon / Supabase / AWS RDS) |

---

## 🔐 Demo Credentials

The database automatically initializes demo accounts upon first startup:

| Role | Email | Password | Department |
|---|---|---|---|
| **Employee** | `employee@smartdesk.ai` | `Employee@123` | Engineering |
| **IT Administrator** | `admin@smartdesk.ai` | `Admin@123` | IT Operations |

> **Note on Demo Authentication:** SmartDesk AI uses PBKDF2 password hashing via Werkzeug and stateless JWT bearer tokens. For enterprise production, SAML 2.0 / Okta / Azure Active Directory SSO integration is recommended.

---

## 🚀 Getting Started (Local Development)

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 2. Backend Setup
1. Navigate to `backend`:
   ```bash
   cd backend
   ```
2. Create and configure environment variables in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-flash
   SECRET_KEY=your_flask_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key_min_32_bytes
   PORT=5000
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask server:
   ```bash
   python app.py
   ```
   *The backend will run on `http://127.0.0.1:5000` and automatically seed the database and knowledge base.*

### 3. Frontend Setup
1. Open a new terminal in `frontend`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure `frontend/.env`:
   ```env
   # Leave blank if using the built-in Vite development proxy:
   VITE_API_BASE_URL=
   ```
4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   *The frontend will run on `http://127.0.0.1:5173`.*

---

## 🧪 Testing

SmartDesk AI includes both unit and end-to-end integration test suites:

### Run Full Test Suite (10 Core Scenarios)
```bash
python backend/tests/test_full_suite.py
```
*Tests: Employee Login, Admin Login, Ticket Creation, Gemini Classification, Fallback Classification, Database Persistence, Support Team Assignment, Status Updates, Knowledge Assistant RAG, and Dashboard Metrics.*

### Run Live HTTP End-to-End Test
```bash
python backend/tests/test_live_api.py
```

---

## 📡 REST API Reference

### Authentication
* `POST /api/login` - Authenticate with email/password; returns JWT token and profile.
* `GET /api/me` - Retrieve current user profile (requires Bearer token).

### Ticket Management
* `POST /api/tickets` - Create a ticket with real-time Gemini AI triage and classification.
* `GET /api/tickets` - List tickets (filtered by user role for employees; all tickets for admins with filters for `status`, `category`, `priority`, and `search`).
* `GET /api/tickets/<id>` - Retrieve ticket details, troubleshooting checklist, and audit history.
* `PATCH /api/tickets/<id>` - Update ticket lifecycle status, assigned team, priority, or resolution notes.

### Generative AI Copilot
* `POST /api/ai/analyze` - Pre-submission AI triage preview (generates category, priority, steps without saving).
* `POST /api/ai/chat` - RAG-grounded IT Knowledge Assistant chatbot answering queries with company SOPs.

### Knowledge Base & Documents
* `GET /api/knowledge/articles` - List company knowledge articles.
* `POST /api/knowledge/upload` - Ingest enterprise PDF document via PyPDF (Admin only).

### Operations Dashboard & Health
* `GET /api/dashboard/stats` - Retrieve executive operations metrics and team workload (Admin only).
* `GET /api/health` - System health, database connection, and Gemini AI status.

---

## ☁️ Vercel Deployment Preparation

SmartDesk AI is structured for easy deployment on Vercel:

1. **Frontend**: The Vite frontend can be deployed directly to Vercel with output directory set to `dist`.
2. **Backend**: The Flask backend is configured with `api/index.py` and `vercel.json` for Vercel Python Serverless Functions.
3. **Database**: Provide a PostgreSQL connection string in the `DATABASE_URL` environment variable (e.g. Neon, Supabase, AWS RDS). The application automatically translates `postgres://` to `postgresql://` and adapts SQLAlchemy models.
4. **Environment Variables on Vercel**:
   * `GEMINI_API_KEY`: Your Google Gemini API Key.
   * `GEMINI_MODEL`: `gemini-3.8-flash`.
   * `DATABASE_URL`: Your production PostgreSQL connection URL.
   * `SECRET_KEY`: Production secret key.
   * `JWT_SECRET_KEY`: Minimum 32-character JWT secret key.
   * `VITE_API_BASE_URL`: Base URL of your deployed backend service.
