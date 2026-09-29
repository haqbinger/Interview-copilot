# Interview Copilot

AI interview simulator that reads your GitHub repo and conducts an
adaptive technical interview grounded in your actual code.

**Live:** https://interview-copilot-49i7.onrender.com
> First load takes ~30s — free tier backend spins down after inactivity.

## What it does

You paste a GitHub URL. The system fetches the repo, maps the architecture,
and asks you to explain it in your own words. Then it interviews you —
questions grounded in your actual files, not generic prep material. Each
answer is scored, missing concepts identified, difficulty adjusted. At the
end you get a diagnostic report with category scores and a concrete revision
plan.

Four modes: Beginner, Technical, Deep Dive, and Stress (skeptical staff
engineer persona that escalates pressure each exchange).

## How it works

GitHub REST API → repo tree + file contents
↓
TF-IDF index built per session (no vector DB needed)
↓
LangGraph state machine
INGESTING → EXPLAINING → INTERVIEWING → EVALUATING → REPORTING
(human-in-the-loop interrupts at explanation and answer submission)
↓
LLM Provider Gateway
7 providers: OpenAI · Gemini · Claude · Groq · DeepSeek · OpenRouter · Mistral
Automatic fallback chain · BYOK · per-session key registry
↓
FastAPI + React/Vite/Nginx · Docker · Render


## Why TF-IDF instead of a vector database

Full repo context overflowed the context window on large repos. I tried
sentence-transformers + ChromaDB first — worked locally, OOM'd on Render's
512MB free tier (torch alone is ~1.5GB). Switched to sklearn TfidfVectorizer.
No model download, no GPU, starts instantly, stays under 100MB. Good enough
for code chunk retrieval where keyword overlap matters more than semantic
similarity.

## Production hardening

- **Guardrails** — input validation, prompt injection scanning on free-text
  fields, JSON output validation on every LLM response
- **Rate limiting** — slowapi, per-endpoint limits (5 req/min on session
  start, 20 req/min on answer submission)
- **Observability** — latency tracked per LLM call, token count and estimated
  cost returned per request, RAG retrieval precision logged per session
- **BYOK** — users bring their own API key for any of 7 providers. Keys live
  in React state during the session, never stored anywhere. Primary key
  exhausted? Falls back to backup key automatically.

## Stack

**Backend:** Python 3.11 · FastAPI · LangGraph · scikit-learn (TF-IDF) · tiktoken · slowapi
**Frontend:** React · Vite · Nginx
**LLM:** 7-provider gateway with automatic fallback
**Infra:** Docker · Render (Web Service + Static Site)
**No database** — session state in LangGraph MemorySaver

## Local setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Environment variables

| Variable | Description |
|----------|-------------|
| GITHUB_TOKEN | GitHub PAT — no scopes needed for public repos |
| GROQ_API_KEY | console.groq.com/keys |
| GROQ_MODEL | e.g. openai/gpt-oss-120b |
| GEMINI_API_KEY | aistudio.google.com/apikey |
| GEMINI_MODEL | e.g. gemini-3.6-flash |
| OPENAI_API_KEY | platform.openai.com/api-keys |
| ANTHROPIC_API_KEY | console.anthropic.com/settings/keys |
| DEEPSEEK_API_KEY | platform.deepseek.com/api_keys |
| OPENROUTER_API_KEY | openrouter.ai/keys |
| MISTRAL_API_KEY | console.mistral.ai/api-keys |
| PROVIDER_PRIORITY | Fallback order e.g. groq,gemini,openai |

## Docker

```bash
docker compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

## API

Session-based:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/session/start | Start session, returns briefing |
| POST | /api/v1/session/{id}/explain | Submit explanation, returns first question |
| POST | /api/v1/session/{id}/answer | Submit answer, returns evaluation + next question or report |
| GET | /api/v1/session/{id}/status | Current state and progress |

Stateless:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/ingest | Repo ingestion and briefing |
| POST | /api/v1/questions | Generate question set |
| POST | /api/v1/evaluate | Evaluate single answer |
| POST | /api/v1/report | Generate diagnostic report |
| POST | /api/v1/stress/followup | Stress mode follow-up challenge |
