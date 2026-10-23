# MediWell AI — Full-Stack Condition-Aware Preventive Wellness Platform

**MediWell AI** is a condition-aware personalized preventive wellness web application built for **CodeYGen Hacktoberfest 2026**. It delivers personalized lifestyle, nutrition, hydration, and habit recommendations tailored to individual health conditions while maintaining strict privacy and clinical safety boundaries.

---

## Architecture Overview

MediWell AI follows a decoupled, resilient full-stack architecture:

- **Frontend (`frontend/`)**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide React icons, Recharts for biometric analytics, and Zod for response validation.
  - Features dedicated responsive form-factors: Desktop (1440×900, 1920×1080), Laptop (1366×768, 1280×800), Tablet with bottom navigation (768×1024, 820×1180, 1024×768), and Mobile (375×812, 390×844).
  - Centralized typed API client (`src/lib/api.ts`) connecting to FastAPI with graceful fallback to local synthetic profiles if offline.
- **Backend (`backend/`)**: Python FastAPI asynchronous REST API, SQLAlchemy 2.x with SQLite for persistence, Pydantic v2 validation, deterministic mathematical analytics, and multi-provider AI architecture (Google Gemini, Groq, and offline deterministic safety fallback).
- **Data (`data/`)**: Purely synthetic, labeled patient datasets (no real protected health information).
- **Documentation (`docs/`)**: Architecture diagrams, API specifications, and competition submission materials.

---

## Prerequisites

- **Node.js**: v20.x or higher (Tested on `v22.17.0`)
- **npm**: v10.x or higher (Tested on `10.9.2`)
- **Python**: 3.12+ or 3.13+ (Tested on `Python 3.13.5`)
- **Git**: Installed and accessible

---

## Quick Start (Local Demo)

### 1. Backend Setup & Run

Open a terminal:
```powershell
cd d:\Programs\mediwell-ai\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# (Optional) Run schema migrations & synthetic database seed
python -m app.db.migrate
python -m app.seed

# Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Frontend Setup & Run

In a second terminal:
```powershell
cd d:\Programs\mediwell-ai\frontend

# Install dependencies (if not already installed)
npm install

# Start development server (or 'npm run build' && 'npx next start -p 3000')
npm run dev
```
- Open application: [http://localhost:3000](http://localhost:3000)

---

## End-to-End Demonstration Flow

1. **Synthetic Patient Selection**:
   - In the top header dropdown, switch between synthetic profiles:
     - **Eleanor Vance** (`SYNTH-T2D-8841`): Type 2 Diabetes Mellitus with high profile completeness and reviewed glycemic protocol.
     - **Marcus Chen** (`SYNTH-HTN-4219`): Hypertension with active cardiovascular & blood pressure habits.
     - **Robert Taylor** (`SYNTH-DFT-9905`): Multi-week declining habit adherence demonstrating genuine clinical drift.
     - **Sarah Jenkins** (`SYNTH-NEW-1092`): Newly enrolled patient with sparse telemetry and plan under review.
2. **Real-Time Habit Logging**:
   - Click completion checkboxes under **Today's Wellness Plan**.
   - Triggers `POST /api/v1/patients/{id}/habits/logs` or `PATCH /api/v1/habit-logs/{id}`, persisting real habit telemetry and dynamically recalculating adherence and momentum.
3. **Wellness Drift Detector & Non-Destructive Recovery**:
   - Select **Robert Taylor** (`SYNTH-DFT-9905`). Notice the **Wellness Drift Detected** card (-30.2% variance vs 21-day baseline).
   - Click **Review Recovery Suggestions** to view root-cause analysis and cited user-reported barriers (`Fatigue / prolonged workday`).
   - Click **Generate Adaptive Proposal** to generate an adaptive protocol with eased targets (e.g. 20 min walk $\to$ 14 min).
   - Review proposed adjustments, customize targets if desired, and click **Accept Eased Targets** (triggers atomic goal updates and acknowledges the drift event).
4. **Interactive AI Wellness Coach**:
   - Navigate to `/coach` in the sidebar or tablet bottom bar.
   - Test regular habit reflections: *"How is my adherence trending?"*
   - Test emergency red-flag pre-screening: *"I have severe chest pain and dizziness"* $\to$ immediate emergency triage redirection to `911`.
   - Test prescription boundary: *"Should I stop taking metformin?"* $\to$ polite refusal redirecting to prescribing clinician.

---

## Test Suites & Verification

### Backend Pytest Suite (58 automated tests)
```powershell
cd d:\Programs\mediwell-ai\backend
.\.venv\Scripts\pytest.exe -v
```
- 8 Foundation tests (health, listing, idempotency)
- 21 Core Wellness tests (dashboard, plans, paginated logs, 409 conflict, validation)
- 16 Drift Detector tests (non-overlapping windows, threshold math, recovery proposals)
- 13 AI Coach tests (red-flag triage, drug refusal, offline fallback, mock timeouts)

### Frontend Verification
```powershell
cd d:\Programs\mediwell-ai\frontend
npx tsc --noEmit
npm run build
```

---

## Real vs Fallback Status

| Feature | Execution Engine | Status |
|---|---|---|
| Synthetic Patient Listing & Profiles | SQLite / SQLAlchemy (`GET /api/v1/patients`) | Real |
| Dashboard Telemetry & Metric Cards | Unified API (`GET /api/v1/patients/{id}/dashboard`) | Real |
| Daily Goal Completion & Logs | Habit Log CRUD (`POST /habits/logs`, `PATCH /habit-logs/{id}`) | Real |
| Adherence & Momentum Math | Deterministic Formulas (`/analytics/adherence`, `/trends`) | Real |
| Wellness Drift Detection | 7-day vs 21-day non-overlapping window math | Real |
| Recovery Proposal Review & Decision | Non-destructive proposals (`accepted`, `edited`, `rejected`) | Real |
| AI Wellness Coach Dialogue | Gemini / Groq with offline deterministic safety fallback | Real + Fallback |

---

## Clinical Safety & Regulatory Boundary

MediWell AI is a **preventive wellness adherence aid and educational habit-tracking platform**, not a medical diagnostic device or clinical decision-support system. It does not diagnose medical conditions, recommend medication changes, or alter medical treatment plans.
