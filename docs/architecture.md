# Architecture / Mimari

## Türkçe

CareerCoachAgenticAIApp, eski monolitik `PersonalCareerAgenticAIApp` uygulamasının bağımsız modüllere ayrıştırılmış halidir. Her servis kendi PostgreSQL veritabanına sahiptir ve birbirleriyle JWT bearer token + `X-Internal-Key` header'ı ile haberleşir.

### Servisler

| Servis | Port | Sorumluluk |
|---|---|---|
| `user-management` | 8001 | Kayıt/giriş/çıkış, şifre sıfırlama, `auth/me`, admin kullanıcı CRUD, sistem admin rolü, JWT üretimi. `IdentityProvider` arayüzü ile IDP değiştirilebilir (ileride Supabase). |
| `personal-admin` | 8002 | Profil CRUD (soft delete: `is_active` + `deleted_at`, restore endpoint'i), hedef ülke/site/rol CRUD, kullanıcı dil tercihi. |
| `system-admin` | 8003 | Dil yönetimi (default + enabled, en az 1 zorunlu), LLM provider'ları (gemini/openai/anthropic/groq/ollama), model öncelikleri, ajan bazlı enable/disable + provider sıralaması + retry/delay/max sonuç, Fernet ile şifreli API key'ler, audit log. |
| `opportunity-service` | 8004 | Fırsatlar + durum makinesi, başvuru adımları, `agent_runs` registry (ongoing takibi), prompt audit. Pasif/silinmiş profillere ait fırsatları gizler. |
| `scout-agent` | 8005 | Async iş ilanı arama + URL analizi. Tek ongoing run kısıtı. Sonuçları opportunity-service'e yazar. |
| `relocation-agent` | 8006 | Async relocation raporu üretimi. |
| `application-coach-agent` | 8007 | Async başvuru adımı + doküman taslağı üretimi. |
| `frontend` | 3000 | Next.js 14 SPA. TR/EN i18n, JWT ile tüm servislere doğrudan erişim. |

### Ortak kütüphane: `services/shared/career_shared`

- `llm/router.py` — **LLM Router**: `invoke_json(agent_name, prompt)` sistem-admin'den ajan config'ini çekip provider → model → retry sırasıyla fallback yapar. Ajanlar hiçbir zaman provider adını bilmez.
- `llm/providers.py` — Gemini, OpenAI-compatible (OpenAI/Groq/Ollama), Anthropic implementasyonları.
- `security.py` — bcrypt + JWT (HS256).
- `auth.py` — `get_current_user_id` (bearer), `verify_internal_key` (servis-servis).
- `client.py` — `ServiceClient`: internal key + opsiyonel bearer forward.
- `idp/` — `IdentityProvider` protokolü.

### Veri akışı

1. Frontend → `user-management` ile login → JWT alır.
2. Frontend diğer tüm servislere `Authorization: Bearer <jwt>` ile istek atar (CORS izinli).
3. Ajan servisleri LLM çağrısı öncesi `system-admin /internal/agents/{name}/config` üzerinden provider/model sıralaması, API key (şifresi çözülmüş), retry ayarlarını alır.
4. Ajanlar sonucu `opportunity-service /internal/*` üzerinden yazar; her LLM denemesi `prompt_audit_logs`'a kaydedilir.
5. `opportunity-service`, listeleme sırasında `personal-admin /internal/profiles/status` ile profil aktifliğini kontrol eder; pasif/silinmiş profilin fırsatları frontend'e dönmez.

### Bilinen sınırlar

- Ajanlar FastAPI `BackgroundTasks` ile çalışır; process restart'ında `running` durumunda kalabilir (dayanıklı kuyruk roadmap).
- Şifre sıfırlama token'ı SMTP yerine log'a yazılır (geliştirme).
- Scout web araması yalnızca Gemini'de desteklenir.
- Supabase IDP implementasyonu henüz yok; arayüz hazır.

## English

CareerCoachAgenticAIApp is the modular decomposition of the former monolithic `PersonalCareerAgenticAIApp`. Every service owns its own PostgreSQL database and communicates via JWT bearer tokens plus an `X-Internal-Key` header.

### Services

| Service | Port | Responsibility |
|---|---|---|
| `user-management` | 8001 | Register/login/logout, password reset, `auth/me`, admin user CRUD, system-admin role, JWT issuance. Swappable `IdentityProvider` (Supabase-ready). |
| `personal-admin` | 8002 | Profile CRUD (soft delete via `is_active` + `deleted_at`, restore endpoint), target country/site/role CRUD, per-user language preference. |
| `system-admin` | 8003 | Language management (default + enabled, at least one required), LLM providers (gemini/openai/anthropic/groq/ollama), per-model priorities, per-agent enable/disable + provider ordering + retry/delay/max results, Fernet-encrypted API keys, audit log. |
| `opportunity-service` | 8004 | Opportunities + state machine, application steps, `agent_runs` registry (ongoing tracking), prompt audit. Hides opportunities of inactive/deleted profiles. |
| `scout-agent` | 8005 | Async job search + URL analysis. Single ongoing-run constraint. Persists via opportunity-service. |
| `relocation-agent` | 8006 | Async relocation report generation. |
| `application-coach-agent` | 8007 | Async application steps + document drafts. |
| `frontend` | 3000 | Next.js 14 SPA. TR/EN i18n, calls all services directly with JWT. |

### Shared library: `services/shared/career_shared`

- `llm/router.py` — **LLM Router**: `invoke_json(agent_name, prompt)` fetches the agent config from system-admin and falls back across providers → models → retries. Agents never know the vendor.
- `llm/providers.py` — Gemini, OpenAI-compatible (OpenAI/Groq/Ollama), Anthropic implementations.
- `security.py` — bcrypt + JWT (HS256).
- `auth.py` — `get_current_user_id` (bearer), `verify_internal_key` (service-to-service).
- `client.py` — `ServiceClient`: internal key + optional bearer forwarding.
- `idp/` — `IdentityProvider` protocol.

### Data flow

1. Frontend logs in via `user-management` → receives a JWT.
2. Frontend calls every other service with `Authorization: Bearer <jwt>` (CORS allowed).
3. Before each LLM call, agents fetch provider/model ordering, decrypted API keys and retry settings from `system-admin /internal/agents/{name}/config`.
4. Agents persist results through `opportunity-service /internal/*`; every LLM attempt is written to `prompt_audit_logs`.
5. `opportunity-service` checks profile status via `personal-admin /internal/profiles/status` when listing; opportunities of inactive/deleted profiles are hidden from the frontend.

### Known limitations

- Agents run on FastAPI `BackgroundTasks`; a process restart can leave runs stuck in `running` (durable queue is on the roadmap).
- Password-reset tokens are logged instead of emailed (development).
- Scout web search is only supported on Gemini.
- Supabase IDP is not implemented yet; the interface is ready.
