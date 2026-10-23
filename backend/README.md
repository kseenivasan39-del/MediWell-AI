# MediWell AI — Backend Wellness Platform (Phases 1–4)

This directory contains the Python FastAPI backend for **MediWell AI**, providing condition-aware personalized preventive wellness REST APIs, persistent SQLite storage, deterministic analytics engines, reproducible synthetic clinical datasets, and a context-aware AI Wellness Coach.

---

## Architecture Overview

```text
backend/
├── app/
│   ├── main.py              # FastAPI app instance, CORS middleware, lifespan seeder
│   ├── core/
│   │   └── config.py        # Pydantic Settings (environment configuration, drift thresholds & AI settings)
│   ├── db/
│   │   ├── database.py      # SQLAlchemy 2.x engine, SessionLocal, get_db dependency
│   │   └── migrate.py       # Safe schema migration script for local development
│   ├── models/
│   │   ├── __init__.py
│   │   └── wellness.py      # SQLAlchemy models: Patient, Habit, Plan, Goal, HabitLog, Measurement, DriftEvent, RecoveryProposal
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── wellness.py      # Pydantic v2 schemas: dashboard, drift analysis, proposals, habits, logs, analytics
│   ├── api/
│   │   └── routes/
│   │       ├── __init__.py  # Aggregated API router
│   │       ├── health.py    # Health check endpoint
│   │       ├── patients.py  # Patient list, retrieval, and unified /dashboard
│   │       ├── plans.py     # Plan and goal retrieval endpoints
│   │       ├── habits.py    # Habit listing, daily goals, paginated logs, CRUD & barriers
│   │       ├── analytics.py # Adherence analytics, trend points, and clinical measurements
│   │       ├── drift.py     # Drift analysis, history, and recovery plan proposal lifecycle
│   │       └── coach.py     # AI Wellness Coach endpoints (dialogue, summary, recovery suggestion)
│   ├── services/
│   │   ├── wellness_service.py # Core business logic, adherence formulas, habit momentum
│   │   ├── drift_detector.py   # Pure window calculations, drift detection, contributing factors
│   │   ├── recovery_service.py # Condition-aware, non-destructive recovery proposals & user review
│   │   └── ai/                 # AI Wellness Coach Architecture (Phase 4)
│   │       ├── base.py         # BaseAIProvider abstract interface
│   │       ├── schemas.py      # Pydantic output schemas (CoachResponse, ObservationType, etc.)
│   │       ├── context_builder.py # Context assembly service (sanitized, ground-truth database telemetry)
│   │       ├── fallback_provider.py # Offline deterministic rules & safety engine
│   │       ├── gemini_provider.py # Google Gemini provider (official google-genai SDK)
│   │       ├── groq_provider.py   # Groq provider (official groq SDK)
│   │       └── coach_service.py   # AICoachService orchestrator (provider fallback, bounded retries)
│   └── seed.py              # Repeatable, idempotent synthetic demo data generator (6 patient scenarios)
├── tests/
│   ├── conftest.py          # Pytest in-memory SQLite fixtures & isolated test client
│   ├── test_foundation.py   # Phase 1 test suite (8 tests)
│   ├── test_core_wellness.py# Phase 2 test suite for dashboard, plans, habits, analytics (21 tests)
│   ├── test_drift_detector.py# Phase 3 test suite for drift math, idempotency, proposals (16 tests)
│   └── test_coach.py        # Phase 4 test suite for AI coach, red flags, fallback, timeouts (13 tests)
├── mediwell.db              # Local SQLite database (git-ignored)
├── pytest.ini               # Pytest configuration
├── .env.example             # Safe placeholder environment configuration
├── requirements.txt         # Pinned backend dependencies
└── README.md
```

---

## 1. Setup & Installation

### Activate Virtual Environment

- **Windows (PowerShell)**:
  ```powershell
  cd d:\Programs\mediwell-ai\backend
  .\.venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  cd backend
  source .venv/bin/activate
  ```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration options:
```ini
# Application & Database
APP_ENV=development
DATABASE_URL=sqlite:///./mediwell.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Drift Detector Configuration
DRIFT_BASELINE_DAYS=21
DRIFT_RECENT_DAYS=7
DRIFT_MIN_OCCURRENCES=5
DRIFT_ALERT_THRESHOLD_PCT=15.0

# AI Wellness Coach Configuration (Phase 4)
AI_PROVIDER=auto                      # Options: 'auto', 'gemini', 'groq', 'deterministic_fallback'
GEMINI_API_KEY=                       # Optional: Google Gemini API key
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=                         # Optional: Groq Cloud API key
GROQ_MODEL=llama-3.3-70b-versatile
AI_REQUEST_TIMEOUT_SECONDS=12.0
AI_MAX_OUTPUT_TOKENS=1024
```

> **Note**: The application starts and runs tests completely offline without requiring any external API key. In the absence of an API key, the deterministic fallback provider automatically handles all coaching requests safely.

---

## 2. AI Wellness Coach Endpoints (Phase 4)

### Coach Dialogue
- `POST /api/v1/patients/{patient_id}/coach`
  - Accepts a patient message and returns structured wellness coaching feedback.
  - Assembles sanitized patient telemetry from the database (goals, adherence, momentum, drift, reported barriers).
  - Pre-screens for acute emergencies and out-of-scope medication advice.
  - Distinguishes `observed` (ground-truth facts), `possible_explanation` (hypotheses), and `suggestion` (non-prescriptive wellness options).

### Proactive Wellness Summary
- `GET /api/v1/patients/{patient_id}/coach/summary`
  - Returns a high-level educational summary of the patient's current wellness momentum and primary focus area.

### Recovery Suggestion with Formal Proposal
- `POST /api/v1/patients/{patient_id}/coach/recovery-suggestion`
  - Generates tailored coaching feedback and initiates a reviewable Phase 3 recovery proposal with eased targets.
  - **Does NOT automatically change active plans**; returns a proposal for explicit user approval.

---

## 3. Safety, Scope & Boundary Rules

1. **Emergency Red-Flag Filter**:
   - Queries containing emergency symptoms (`chest pain`, `shortness of breath`, `severe dizziness`, `stroke symptoms`) trigger immediate emergency direction (`911` / local emergency room). Sets `is_urgent_guidance: true`.
2. **Clinical & Medication Boundary**:
   - Requests for diagnosis or prescription medication adjustments are politely refused with explicit redirection to the patient's prescribing physician or pharmacist.
3. **No Invented Evidence (Strict Grounding)**:
   - External models are forbidden from hallucinating unrecorded metrics, dates, or barriers. All statements must cite ground-truth records present in the assembled context.
4. **Non-Destructive Recovery**:
   - The AI Coach cannot mutate a patient's active wellness plan. All adjustments are issued as reviewable proposals via Phase 3 APIs requiring explicit user acceptance or modification.

---

## 4. Running Tests

Run the complete backend automated test suite with pytest (58 tests across all 4 phases):

```powershell
pytest -v
```

Test coverage:
- **Phase 1 Foundation (8 tests)**: Health checks, scenario listings, synthetic idempotency, drift fixture checks.
- **Phase 2 Core Wellness (21 tests)**: Unified dashboard, plan retrieval, paginated logs, duplicate conflict prevention (`409`), validation rejections (`422`), 7d/28d adherence math.
- **Phase 3 Drift & Recovery (16 tests)**: Date window boundaries, threshold triggers, contributing observations, idempotency, proposal lifecycle (accepted/edited/rejected).
- **Phase 4 AI Wellness Coach (13 tests)**:
  - Context assembly (complete, sparse, and drift scenarios).
  - Emergency red flag pre-screening and immediate triage response.
  - Medication/diagnosis refusal and clinical redirection.
  - Prompt injection safety defense.
  - Deterministic fallback when API keys are absent.
  - Active drift coaching dialogue.
  - Coach summary endpoint.
  - Recovery suggestion endpoint with proposal creation in pending state.
  - Provider failure, timeout, and rate-limit fallback via mocks.

---

## 5. Starting the Server

```powershell
cd d:\Programs\mediwell-ai\backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
