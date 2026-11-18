# CareerCoachAgenticAIApp

Modular, microservice-based AI career coach — successor to the monolithic
PersonalCareerAgenticAIApp. FastAPI services (one PostgreSQL DB each), a
Next.js SPA frontend, JWT auth, and a provider-agnostic LLM router with
admin-configurable fallback (Gemini, OpenAI, Anthropic, Groq, Ollama).

## Quickstart

```powershell
cd infra
copy .env.example .env    # set JWT_SECRET, INTERNAL_API_KEY, SETTINGS_ENCRYPTION_KEY
docker compose up --build
```

CMD equivalent:

```cmd
cd infra
copy .env.example .env
notepad .env
docker compose up --build
```

Frontend: http://localhost:3000 — see [docs/setup.md](docs/setup.md) for local
and Google Cloud deployment, first-user bootstrap and API key management.

## Docs

- [Architecture](docs/architecture.md) — service map, auth model, LLM router
- [Setup & Deployment](docs/setup.md) — local + GCP, first user/profile, secrets
- [User guide](docs/user_guide.md)

## Layout

```
services/    8 FastAPI services + shared/career_shared library + tests
frontend/    Next.js 14 SPA (TR/EN)
infra/       docker-compose + postgres init + .env.example
docs/        documentation (bilingual where applicable)
```

## Tests

Each service has its own `tests/` suite (SQLite fixtures):

```powershell
cd services\<service-name>
..\..\.venv\Scripts\python.exe -m pytest tests -q
```
