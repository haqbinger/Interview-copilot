# Interview Copilot

> Turn your GitHub project into an interview simulator.

A production-grade AI interview tool that analyzes your GitHub repository, asks you to explain it in your own words, then conducts an adaptive technical interview grounded in your actual code.

## Live Demo

https://interview-copilot-49i7.onrender.com

> ⏱ Note: First load may take 30 seconds — free tier backend spins down after inactivity.

## How it works

1. Paste your GitHub repository URL
2. Choose an interview mode (Beginner / Technical / Deep Dive / Stress)
3. The system analyzes your repo — tech stack, architecture, data flows
4. Explain your project in your own words
5. Answer adaptive questions grounded in your actual code
6. Receive a scored diagnostic report with a revision plan

## Interview Modes

- **Beginner** — Project overview, high-level architecture, core technologies
- **Technical** — Implementation decisions, design choices, trade-offs
- **Deep Dive** — Failure modes, scalability, production concerns
- **Stress** — Skeptical staff engineer persona, challenges every decision

## Architecture

```
React Frontend (Vite)
        ↓
FastAPI Backend
        ↓
LangGraph State Machine (INGESTING → EXPLAINING → INTERVIEWING → EVALUATING → REPORTING)
        ↓
LLM Provider Gateway (Groq → Gemini fallback)
        ↓
GitHub REST API
```

## Tech Stack

**Backend:** Python, FastAPI, LangGraph, in-memory session state (no database)
**Frontend:** React, Vite, Nginx
**LLM:** Groq (Llama), Gemini fallback
**Infra:** Docker, Render

## Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your keys
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| GITHUB_TOKEN | GitHub personal access token (no scopes needed for public repos) |
| GROQ_API_KEY | Groq API key (console.groq.com) |
| GROQ_MODEL | Groq model ID (e.g. openai/gpt-oss-120b) |
| GEMINI_API_KEY | Google AI Studio key (fallback provider) |
| GEMINI_MODEL | Gemini model ID (e.g. gemini-3.6-flash) |
| LLM_PROVIDER | Legacy setting, currently unused — provider selection is driven by PROVIDER_PRIORITY |
| PROVIDER_PRIORITY | Fallback chain, in order (e.g. groq,gemini) |

## Docker

```bash
docker compose up --build
```

Frontend: http://localhost:5173
Backend: http://localhost:8000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/session/start | Start interview session |
| POST | /api/v1/session/{id}/explain | Submit project explanation |
| POST | /api/v1/session/{id}/answer | Submit answer to question |
| GET | /api/v1/session/{id}/status | Get session status |
| POST | /api/v1/ingest | Direct repo ingestion |
| POST | /api/v1/questions | Generate question set |
| POST | /api/v1/evaluate | Evaluate single answer |
| POST | /api/v1/report | Generate final report |

## Milestones

- M1: Repository ingestion and briefing generation
- M2: Adaptive question generation with four interview modes
- M3: Real-time answer evaluation with scoring and difficulty adjustment
- M4: Diagnostic report with category scores and revision plan
- M5a: Stress mode with skeptical staff engineer persona
- M5b: LangGraph agentic orchestrator with session state machine
