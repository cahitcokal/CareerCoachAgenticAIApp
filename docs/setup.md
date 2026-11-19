# Kurulum ve Dağıtım / Setup & Deployment

## Türkçe

Bu belge CareerCoachAgenticAIApp'in hem lokalde hem Google Cloud'da nasıl ayağa kaldırılacağını, ilk kullanıcı/profil oluşturmayı ve API anahtarlarının nasıl yönetileceğini açıklar.

### Ön koşullar

- Docker Desktop (docker compose için) **veya** Python 3.12 + Node.js 20 (yerel geliştirme için)
- gcloud CLI (Google Cloud dağıtımı için)

### 1. Lokal kurulum — Docker Compose (önerilen)

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
Copy-Item .env.example .env
# .env dosyasını düzenleyin: JWT_SECRET, INTERNAL_API_KEY ve SETTINGS_ENCRYPTION_KEY zorunludur.
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
# .env dosyasını düzenleyin: JWT_SECRET, INTERNAL_API_KEY ve SETTINGS_ENCRYPTION_KEY zorunludur.
```

Veritabanı sağlayıcısını değiştirmek için `infra/.env` içindeki
`USER_MANAGEMENT_DATABASE_URL`, `PERSONAL_ADMIN_DATABASE_URL`,
`SYSTEM_ADMIN_DATABASE_URL` ve `OPPORTUNITY_SERVICE_DATABASE_URL` değerlerini
değiştirin. Dört servis aynı ortak adapter'ı kullanır; SQLite için servis başına
ayrı `sqlite:///...` URL'si, PostgreSQL/Supabase/Neon için sağlayıcının
`postgresql://` URL'si verilebilir.

`SETTINGS_ENCRYPTION_KEY` üretmek için:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Ardından:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
docker compose up --build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
docker compose up --build
```

Servisler:

| Servis | Adres |
|---|---|
| Frontend | http://localhost:3000 |
| user-management | http://localhost:8001 |
| personal-admin | http://localhost:8002 |
| system-admin | http://localhost:8003 |
| opportunity-service | http://localhost:8004 |
| scout-agent | http://localhost:8005 |
| relocation-agent | http://localhost:8006 |
| application-coach-agent | http://localhost:8007 |

İlk açılışta postgres konteyneri `postgres-init/01-databases.sql` ile `career_users`, `career_personal`, `career_system`, `career_opportunities` veritabanlarını oluşturur; her servis kendi tablolarını startup'ta oluşturur ve system-admin varsayılan dilleri (tr/en) ile provider/ajan kayıtlarını seed eder.

### 2. Lokal kurulum — Docker'sız (geliştirme)

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements-dev.txt
```

PostgreSQL'i lokalde çalıştırıp her servis için `DATABASE_URL` ayarlayın (örn. `postgresql+psycopg://career:career@localhost:5432/career_users`). Ortak env değişkenleri `career_shared.config.ServiceSettings` üzerinden okunur: `JWT_SECRET`, `INTERNAL_API_KEY`, `*_URL` servis adresleri, `SETTINGS_ENCRYPTION_KEY`.

Her servisi ayrı terminalde çalıştırın:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
$env:PYTHONPATH="..\shared"
$env:DATABASE_URL="postgresql+psycopg://career:career@localhost:5432/career_users"
uvicorn app.main:app --port 8001
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
uvicorn app.main:app --port 8001
```

Aynı şekilde diğer servisleri 8002–8007 portlarında başlatın. Frontend için:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```

`NEXT_PUBLIC_*_URL` değişkenleri ile servis adreslerini frontend'e bildirin (varsayılanlar localhost portlarıdır).

### 2a. PyCharm ile Docker'sız çalıştırma

Proje kökünü PyCharm'da açın ve Python interpreter olarak kökteki
`.venv\Scripts\python.exe` dosyasını seçin. `scripts/run_service.py` için bir
**Python** run configuration oluşturun; **Script path** olarak bu dosyayı,
**Working directory** olarak proje kökünü ve **Parameters** olarak örneğin
`user-management` girin. Yapılandırmayı kopyalayıp yalnızca servis adını
değiştirerek diğer servisleri çalıştırabilirsiniz: `personal-admin`,
`system-admin`, `opportunity-service`, `scout-agent`, `relocation-agent` ve
`application-coach-agent`.

Betiğin varsayılanı, PostgreSQL gerektirmeyen servis başına bir SQLite dosyasını
`runtime\` altında oluşturur. PostgreSQL, Supabase veya Neon kullanmak için
run configuration içindeki **Environment variables** alanına ilgili
`DATABASE_URL` değerini ekleyin. `postgresql://` ve `postgres://` URL'leri ortak
adapter tarafından `psycopg` sürücüsüne çevrilir. Servis portları 8001–8007 arasındadır.

Frontend için `frontend` klasörünü PyCharm'da ayrı bir Node.js projesi olarak
açın; `npm install` çalıştırın ve `package.json` içindeki `dev` script'ini
çalıştırın. API adresleri varsayılan olarak `http://localhost:8001`–`8007`'dir.

### 3. İlk kullanıcı ve sistem admin oluşturma

1. http://localhost:3000/register adresinden ilk kullanıcıyı kaydedin — kayıt sırasında `personal-admin`'e varsayılan hedef ülke/site/rol listeleri seed edilir.
2. İlk kullanıcıyı sistem admin yapmak için (veritabanına doğrudan erişim gerekiyor):

```sql
-- career_users veritabanında
INSERT INTO system_admins (user_id) VALUES (<user_id>);
```

veya user-management API'si ile (token sahibi zaten admin olmalı — tavuk-yumurta durumu nedeniyle ilk atama SQL ile yapılır):

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
curl -X PATCH http://localhost:8001/admin/users/<id> -H "Authorization: Bearer <admin-token>" -H "Content-Type: application/json" -d '{"is_system_admin": true}'
```
Command Prompt:
```cmd
set USER_ID=123
set ADMIN_TOKEN=your-admin-token

curl -X PATCH http://localhost:8001/admin/users/%USER_ID% ^
  -H "Authorization: Bearer %ADMIN_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"is_system_admin\":true}"
```

3. `/system-admin` sayfasından dilleri, provider API key'lerini, model listelerini ve ajan ayarlarını yapılandırın.
4. `/admin` (Personal Admin) sayfasından profiller oluşturun. Profil silme soft-delete'tir; pasif/silinmiş profilin fırsatları listelerde görünmez, "Geri Yükle" ile aktifleşir.

### 4. API anahtarları ve ortam değişkenleri

| Değişken | Nerede | Açıklama |
|---|---|---|
| `JWT_SECRET` | tüm servisler | JWT imzalama anahtarı (32+ karakter, rastgele) |
| `INTERNAL_API_KEY` | tüm servisler | Servis-servis `X-Internal-Key` header'ı |
| `SETTINGS_ENCRYPTION_KEY` | system-admin | Provider API key'lerini DB'de şifrelemek için Fernet anahtarı |
| `DATABASE_URL` | DB'li servisler | `postgresql+psycopg://user:pass@host:5432/db` |
| `GEMINI_API_KEY` vb. | opsiyonel fallback | System Admin DB'sinde key tanımlı değilse env fallback |
| `NEXT_PUBLIC_*_URL` | frontend | Servis base URL'leri (build-time inline edilir) |

Provider API key'leri **tercihen System Admin arayüzünden** girilir; Fernet ile şifrelenip `provider_credentials.encrypted_api_key` alanına yazılır ve asla frontend'e dönmez (`has_api_key` flag'i dışında).

### 5. Google Cloud (GCP) dağıtımı

Mimari öneri: **Cloud Run** (her servis için ayrı servis) + **Cloud SQL for PostgreSQL** (tek instance, 4 veritabanı) + **Secret Manager** + frontend için Cloud Run (Next.js standalone) veya Firebase Hosting.

Adımlar:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

**Veritabanı:**

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud sql instances create careercoach-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=europe-west1
gcloud sql databases create career_users --instance=careercoach-db
# career_personal, career_system, career_opportunities için tekrarlayın
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud sql instances create careercoach-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=europe-west1
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

**Secret'lar:**

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud secrets create jwt-secret --data-file=-   # uzun rastgele string
gcloud secrets create internal-api-key --data-file=-
gcloud secrets create settings-encryption-key --data-file=-   # Fernet key
# Provider key'leri System Admin UI'dan da girilebilir; env fallback isterseniz:
gcloud secrets create gemini-api-key --data-file=-
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
# Uzun rastgele string girmeniz istenir.
gcloud secrets create jwt-secret --data-file=-
gcloud secrets create internal-api-key --data-file=-
# Fernet anahtarı girmeniz istenir.
gcloud secrets create settings-encryption-key --data-file=-
# Provider anahtarları System Admin UI üzerinden de girilebilir.
gcloud secrets create gemini-api-key --data-file=-
```

**Servis hesapları ve deploy:** Her Python servisi için Cloud Run'a deploy edin. Örnek (user-management):

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy user-management `
  --source services/user-management `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:<pwd>@/<db>?host=/cloudsql/<PROJECT>:europe-west1:careercoach-db","JWT_SECRET=<from-secret>","INTERNAL_API_KEY=<from-secret>","PERSONAL_ADMIN_URL=<personal-admin-url>" `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set PROJECT_ID=your-project-id
set DB_PASSWORD=your-db-password
set PERSONAL_ADMIN_URL=https://personal-admin-url
gcloud run deploy user-management ^
  --source services/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_users?host=/cloudsql/%PROJECT_ID%:europe-west1:careercoach-db,PERSONAL_ADMIN_URL=%PERSONAL_ADMIN_URL%" ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest"
```

Alternatif daha temiz yol: Cloud SQL Auth Proxy sidecar yerine Cloud Run'ın `--add-cloudsql-instances` bayrağı + `--set-env-vars DATABASE_URL=...@localhost...` (unix socket) kullanın. Tüm servis URL'lerini (`*_URL`) deploy sonrası gerçek Cloud Run URL'leriyle güncelleyin.

**Frontend:** `NEXT_PUBLIC_*_URL` değişkenleri build-time gömüldüğü için image'ı doğru env ile build edin:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy frontend --source frontend --region europe-west1 `
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxx.run.app",...
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy frontend --source frontend --region europe-west1 ^
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxx.run.app",...
```

veya `gcloud builds submit` ile build argümanı olarak verin. Frontend'i `--allow-unauthenticated` yapın; API'ler JWT ile korunur.

**Cloud attribute notları:**

- Her servise ayrı `DATABASE_URL` verin (aynı Cloud SQL instance, farklı veritabanı).
- `INTERNAL_API_KEY` ve `JWT_SECRET` tüm servislerde aynı olmalı.
- `FRONTEND_URL`'i CORS için frontend'in public URL'sine ayarlayın.
- Cloud Run'da `PORT` env'ini servis kendisi okur (varsayılan 8001–8007); Cloud Run `PORT=8080` inject eder — `app.main`'deki `if __name__ == "__main__"` bloğu yerine `uvicorn app.main:app` CMD'si kullanıyorsanız `--port`'u `$PORT`'a bağlayın veya Dockerfile CMD'sinde `"$PORT"` kullanın. Mevcut Dockerfile'lar sabit port kullanır; Cloud Run için `CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]` gibi güncelleyin.
- Min instance 0 + concurrency ayarı maliyet için önerilir; ajanlar BackgroundTasks kullandığından uzun isteklerde timeout'a dikkat edin (Cloud Run request timeout max 60 dk).

### 6. Testler

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\<service-name>
..\..\.venv\Scripts\python.exe -m pytest tests -q
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\<service-name>
..\..\.venv\Scripts\python.exe -m pytest tests -q
```

Frontend: `cd frontend; npm install; npx tsc --noEmit; npm run build`

### CMD command equivalents

The commands above are also available for Windows Command Prompt (CMD). Docker, Python, `npm`, `uvicorn`, `curl`, and `gcloud` commands are otherwise the same in both shells.

PowerShell environment-variable assignments:

```powershell
$env:PYTHONPATH="..\shared"
$env:DATABASE_URL="postgresql+psycopg://career:career@localhost:5432/career_users"
```

CMD equivalents:

```cmd
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
```

PowerShell multi-line `gcloud` commands use a backtick (`). CMD uses a caret (`^`) instead:

```cmd
gcloud run deploy user-management ^
  --source services/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest"
```

The local Docker Compose flow in CMD is:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
notepad .env
docker compose up --build
```

## English

This document explains how to run CareerCoachAgenticAIApp locally and on Google Cloud, how to create the first user/profile, and how API keys are managed.

### Prerequisites

- Docker Desktop (for docker compose) **or** Python 3.12 + Node.js 20 (local dev)
- gcloud CLI (for Google Cloud deployment)

### 1. Local setup — Docker Compose (recommended)

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
Copy-Item .env.example .env
# Edit .env: JWT_SECRET, INTERNAL_API_KEY and SETTINGS_ENCRYPTION_KEY are required.
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
# Edit .env: JWT_SECRET, INTERNAL_API_KEY and SETTINGS_ENCRYPTION_KEY are required.
```

To change database providers, edit `USER_MANAGEMENT_DATABASE_URL`,
`PERSONAL_ADMIN_DATABASE_URL`, `SYSTEM_ADMIN_DATABASE_URL`, and
`OPPORTUNITY_SERVICE_DATABASE_URL` in `infra/.env`. All four services use the
same shared adapter: provide one `sqlite:///...` URL per service for SQLite, or
the provider's `postgresql://` URL for PostgreSQL, Supabase, or Neon.

Generate `SETTINGS_ENCRYPTION_KEY`:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
docker compose up --build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| user-management | http://localhost:8001 |
| personal-admin | http://localhost:8002 |
| system-admin | http://localhost:8003 |
| opportunity-service | http://localhost:8004 |
| scout-agent | http://localhost:8005 |
| relocation-agent | http://localhost:8006 |
| application-coach-agent | http://localhost:8007 |

On first start the postgres container creates `career_users`, `career_personal`, `career_system`, `career_opportunities` via `postgres-init/01-databases.sql`; each service creates its tables on startup and system-admin seeds default languages (tr/en) plus provider/agent records.

### 2. Local setup — without Docker (development)

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements-dev.txt
```

Run PostgreSQL locally and set `DATABASE_URL` per service (e.g. `postgresql+psycopg://career:career@localhost:5432/career_users`). For SQLite use `sqlite:///./runtime/service.db`; for Supabase or Neon use the provider's PostgreSQL connection URL. The shared adapter normalizes `postgresql://` and `postgres://` URLs to the psycopg driver. Shared env vars are read via `career_shared.config.ServiceSettings`: `JWT_SECRET`, `INTERNAL_API_KEY`, `*_URL` service addresses, and `SETTINGS_ENCRYPTION_KEY`.

Run each service in its own terminal:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
$env:PYTHONPATH="..\shared"
$env:DATABASE_URL="postgresql+psycopg://career:career@localhost:5432/career_users"
uvicorn app.main:app --port 8001
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
uvicorn app.main:app --port 8001
```

Repeat for the other services on ports 8002–8007. Frontend:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```

Point the frontend at your services via `NEXT_PUBLIC_*_URL` (defaults are the localhost ports).

### 2a. Run without Docker from PyCharm

Open the project root in PyCharm and select the root `.venv\Scripts\python.exe`
as the Python interpreter. Create a **Python** run configuration for
`scripts/run_service.py`, using the project root as **Working directory** and,
for example, `user-management` as **Parameters**. Duplicate the configuration
and change only the service name for `personal-admin`, `system-admin`,
`opportunity-service`, `scout-agent`, `relocation-agent`, and
`application-coach-agent`.

By default, the script creates one SQLite file per service under `runtime/`, so
PostgreSQL is not required for local startup. To use PostgreSQL, Supabase, Neon,
or another SQLAlchemy-compatible database, set `DATABASE_URL` in the run
configuration's **Environment variables**. The shared adapter normalizes
`postgresql://` and `postgres://` URLs to the `psycopg` driver. Service ports are
8001–8007.

For the frontend, open the `frontend` directory as a separate Node.js project
in PyCharm, run `npm install`, and run the `dev` script from `package.json`. The
default API URLs are `http://localhost:8001`–`8007`.

### 3. First user and system admin

1. Register the first user at http://localhost:3000/register — registration seeds default target countries/sites/roles in personal-admin.
2. To make the first user a system admin (requires direct DB access — chicken-and-egg for the very first admin):

```sql
-- inside the career_users database
INSERT INTO system_admins (user_id) VALUES (<user_id>);
```

or via the API once any admin token exists:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
curl -X PATCH http://localhost:8001/admin/users/<id> -H "Authorization: Bearer <admin-token>" -H "Content-Type: application/json" -d '{"is_system_admin": true}'
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set USER_ID=123
set ADMIN_TOKEN=your-admin-token

curl -X PATCH http://localhost:8001/admin/users/%USER_ID% ^
  -H "Authorization: Bearer %ADMIN_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"is_system_admin\":true}"
```

3. On `/system-admin`, configure languages, provider API keys, model lists and agent settings.
4. On `/admin` (Personal Admin), create profiles. Profile deletion is a soft delete; opportunities of inactive/deleted profiles are hidden and can be restored via "Restore".

### 4. API keys and environment variables

| Variable | Where | Description |
|---|---|---|
| `JWT_SECRET` | all services | JWT signing key (32+ random chars) |
| `INTERNAL_API_KEY` | all services | Service-to-service `X-Internal-Key` header |
| `SETTINGS_ENCRYPTION_KEY` | system-admin | Fernet key encrypting provider API keys at rest |
| `DATABASE_URL` | DB-backed services | `sqlite:///./runtime/service.db` or a PostgreSQL/Supabase/Neon URL |
| `GEMINI_API_KEY` etc. | optional fallback | Used only when no key is stored in the System Admin DB |
| `NEXT_PUBLIC_*_URL` | frontend | Service base URLs (inlined at build time) |

Provider API keys should preferably be entered through the System Admin UI; they are Fernet-encrypted into `provider_credentials.encrypted_api_key` and never returned to the frontend (only a `has_api_key` flag).

### 5. Google Cloud (GCP) deployment

Recommended architecture: **Cloud Run** (one service per module) + **Cloud SQL for PostgreSQL** (single instance, 4 databases) + **Secret Manager** + Cloud Run for the Next.js frontend.

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

**Database:**

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud sql instances create careercoach-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=europe-west1
gcloud sql databases create career_users --instance=careercoach-db
# repeat for career_personal, career_system, career_opportunities
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud sql instances create careercoach-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=europe-west1
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

**Secrets:**

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud secrets create jwt-secret --data-file=-
gcloud secrets create internal-api-key --data-file=-
gcloud secrets create settings-encryption-key --data-file=-   # Fernet key
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
# You will be prompted to enter a long random string.
gcloud secrets create jwt-secret --data-file=-
gcloud secrets create internal-api-key --data-file=-
# You will be prompted to enter a Fernet key.
gcloud secrets create settings-encryption-key --data-file=-
```

**Deploy:** deploy each Python service to Cloud Run, e.g. user-management:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy user-management `
  --source services/user-management `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances <PROJECT>:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:<pwd>@localhost/career_users?host=/cloudsql/<PROJECT>:europe-west1:careercoach-db","PERSONAL_ADMIN_URL=<personal-admin-url>"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set PROJECT_ID=your-project-id
set DB_PASSWORD=your-db-password
set PERSONAL_ADMIN_URL=https://personal-admin-url
gcloud run deploy user-management ^
  --source services/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances %PROJECT_ID%:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@localhost/career_users?host=/cloudsql/%PROJECT_ID%:europe-west1:careercoach-db,PERSONAL_ADMIN_URL=%PERSONAL_ADMIN_URL%"
```

Give every service its own `DATABASE_URL` (same Cloud SQL instance, different database). After deploy, update all `*_URL` variables to the real Cloud Run URLs. Set `FRONTEND_URL` to the frontend's public URL for CORS.

**Frontend:** `NEXT_PUBLIC_*_URL` values are inlined at build time, so build the image with the correct env:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy frontend --source frontend --region europe-west1 `
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxx.run.app",...
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy frontend --source frontend --region europe-west1 ^
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxx.run.app,..."
```

Deploy the frontend with `--allow-unauthenticated`; APIs stay protected by JWT.

**Cloud notes:**

- The service Dockerfiles use fixed ports (8001–8007). Cloud Run injects `PORT=8080`; update the CMD to `sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"` or similar per service before deploying.
- Agents use FastAPI `BackgroundTasks`; keep Cloud Run request timeout in mind for long LLM runs (max 60 min).
- Min instances 0 is fine for cost; expect cold starts.

### 6. Tests

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\<service-name>
..\..\.venv\Scripts\python.exe -m pytest tests -q
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\<service-name>
..\..\.venv\Scripts\python.exe -m pytest tests -q
```

Frontend: `cd frontend; npm install; npx tsc --noEmit; npm run build`

### CMD command equivalents

The commands above are also available for Windows Command Prompt (CMD). Docker, Python, `npm`, `uvicorn`, `curl`, and `gcloud` commands are otherwise the same in both shells.

PowerShell environment-variable assignments:

```powershell
$env:PYTHONPATH="..\shared"
$env:DATABASE_URL="postgresql+psycopg://career:career@localhost:5432/career_users"
```

CMD equivalents:

```cmd
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
```

PowerShell multi-line `gcloud` commands use a backtick (`). CMD uses a caret (`^`) instead:

```cmd
gcloud run deploy user-management ^
  --source services/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest"
```

The local Docker Compose flow in CMD is:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
notepad .env
docker compose up --build
```
