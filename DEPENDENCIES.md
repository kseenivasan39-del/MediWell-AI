# MediWell AI — Full Project Dependencies & Requirements

This document provides a clean overview of the required system, backend, and frontend dependencies needed to run **MediWell AI**.

---

## 🖥️ System Prerequisites
- **Python**: `3.11+` (Tested on `3.13.5`)
- **Node.js**: `v20.x` or higher (Tested on `v22.17.0`)
- **npm**: `v10.x` or higher (Tested on `10.9.2`)
- **Git**: Installed and configured

---

## 🐍 1. Backend Dependencies (`backend/requirements.txt`)

Install in backend directory:
```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Core Libraries:
| Package | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **`fastapi`** | `>=0.115.0` | Asynchronous REST API framework |
| **`uvicorn[standard]`** | `>=0.30.0` | High-performance ASGI web server |
| **`SQLAlchemy`** | `>=2.0.30` | 2.x ORM, database engine & relationships |
| **`pydantic`** | `>=2.9.0` | Data modeling & runtime schema validation |
| **`pydantic-settings`** | `>=2.5.0` | Environment variable & `.env` management |
| **`python-dotenv`** | `>=1.0.1` | Local configuration loading |
| **`httpx`** | `>=0.27.0` | Async HTTP client for OAuth code exchange & testing |
| **`pandas`** | `>=2.2.0` | Mathematical data processing for drift analysis |
| **`numpy`** | `>=1.26.0` | Numerical calculations |
| **`cryptography`** | `>=42.0.0` | Fernet authenticated encryption for OAuth refresh tokens |
| **`google-genai`** | `>=2.0.0` | Official Google Gemini AI SDK with schema enforcement |
| **`google-auth`** | `>=2.30.0` | Google OAuth token handling |
| **`groq`** | `>=0.9.0` | Alternative AI provider for Llama-3.3 70B inference |
| **`tenacity`** | `>=8.5.0` | Bounded retries and resilience for network operations |
| **`python-dateutil`** | `>=2.9.0` | Timezone and calendar timestamp parsing |
| **`tzdata`** | `>=2024.1` | Timezone database (`Asia/Kolkata` calculations) |
| **`pytest`** | `>=8.0.0` | Automated test runner (65 tests) |
| **`pytest-asyncio`** | `>=0.24.0` | Async test fixtures & event loop management |

---

## ⚛️ 2. Frontend Dependencies (`frontend/package.json`)

Install in frontend directory:
```bash
cd frontend
npm install
```

### Core Libraries:
| Package | Version | Purpose |
| :--- | :--- | :--- |
| **`next`** | `^16.4.2` | React framework with Turbopack & App Router |
| **`react`** | `^19.0.0` | React 19 UI library |
| **`react-dom`** | `^19.0.0` | React DOM bindings |
| **`tailwindcss`** | `^3.4.1` | Utility-first responsive CSS styling |
| **`lucide-react`** | `^0.475.0` | SVG iconography suite |
| **`recharts`** | `^2.15.1` | Responsive biometric & adherence trend visualization |
| **`zod`** | `^3.24.2` | Runtime API response schema validation |
| **`typescript`** | `^5` | Strict static typing across components and adapters |
| **`@types/node`** | `^20` | Node.js TypeScript typings |
| **`@types/react`** | `^19` | React 19 TypeScript typings |

---

## ⚙️ 3. Optional Cloud & External Services
- **Google Gemini API Key**: For live AI Wellness Coach responses (free tier available via Google AI Studio).
- **Google Cloud Console OAuth 2.0 Client**: For live Google Calendar reminder event synchronization.
- *Note: MediWell AI includes a 100% offline fallback mode if cloud keys are omitted.*
