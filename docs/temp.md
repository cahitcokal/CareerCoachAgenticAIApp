# Lokal Kurulum Rehberi / Local Setup Guide

## Türkçe

Bu belge, CareerCoachAgenticAIApp projesini Docker Compose ile lokal ortamda çalıştırmak için hazırlanmıştır.

### Güvenlik uyarısı

`.env`, API anahtarları ve şifreler Git'e commit edilmemelidir. Eğer bir API anahtarı GitHub'a, sohbete veya başka bir ortak ortama yanlışlıkla gönderildiyse hemen iptal edilip yenisi oluşturulmalıdır.

### Ön koşullar

- Docker Desktop
- Docker Compose desteği (`docker compose`)

Kontrol:

```cmd
docker --version
docker compose version
```

### 1. Ortam dosyasını oluşturma

CMD ile proje klasörüne gidin:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
notepad .env
```

`.env` içinde aşağıdaki zorunlu değerleri değiştirin:

```env
JWT_SECRET=<rastgele-uzun-deger>
INTERNAL_API_KEY=<rastgele-uzun-deger>
SETTINGS_ENCRYPTION_KEY=<fernet-degeri>
```

Lokal frontend URL'leri varsayılan değerleriyle bırakılabilir:

```env
NEXT_PUBLIC_USER_MANAGEMENT_URL=http://localhost:8001
NEXT_PUBLIC_PERSONAL_ADMIN_URL=http://localhost:8002
NEXT_PUBLIC_SYSTEM_ADMIN_URL=http://localhost:8003
NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=http://localhost:8004
NEXT_PUBLIC_SCOUT_AGENT_URL=http://localhost:8005
NEXT_PUBLIC_RELOCATION_AGENT_URL=http://localhost:8006
NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=http://localhost:8007
```

### 2. Secret değerlerini üretme

Proje kökünde bulunan sanal ortamı kullanarak iki rastgele değer üretin:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Komutu iki kez çalıştırın. İlk çıktıyı `JWT_SECRET`, ikinci çıktıyı `INTERNAL_API_KEY` için kullanın.

Fernet encryption key üretmek için:

```cmd
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Çıktıyı `SETTINGS_ENCRYPTION_KEY` olarak kullanın.

### 3. Provider API anahtarları

Aşağıdaki anahtarlar lokal başlangıç için zorunlu değildir:

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
```

Provider anahtarları tercihen `/system-admin` ekranından yapılandırılmalıdır. Uygulama bunları Fernet ile şifreleyerek veritabanında saklar. Ortam değişkenleri yalnızca sistem yöneticisi veritabanında bir provider anahtarı bulunmadığında fallback olarak kullanılır.

### 4. Uygulamayı başlatma

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```

İlk çalıştırma sırasında PostgreSQL veritabanları oluşturulur ve servisler kendi tablolarını başlatır.

Servis adresleri:

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

Uygulamayı durdurmak için Compose penceresinde `Ctrl+C` kullanın.

### 5. İlk kullanıcı ve system admin

İlk kullanıcıyı şu adresten oluşturun:

```text
http://localhost:3000/register
```

İlk kullanıcıyı system admin yapmak için yeni bir CMD penceresinde PostgreSQL konsolunu açın:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose exec postgres psql -U career -d career_users
```

Kullanıcı ID'sini bulun:

```sql
SELECT id, email FROM users;
```

Ardından ilgili ID ile admin kaydı oluşturun:

```sql
INSERT INTO system_admins (user_id) VALUES ('KULLANICI_ID');
```

PostgreSQL'den çıkmak için:

```sql
\q
```

Daha sonra `http://localhost:3000/system-admin` adresinden provider anahtarlarını, modelleri ve ajan ayarlarını yapılandırabilirsiniz.

### 6. Servis durumunu ve logları kontrol etme

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```

Tek bir servisin loglarını görmek için:

```cmd
docker compose logs -f user-management
```

### 7. Testleri çalıştırma

Backend testleri:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pytest services\shared\tests -q
.venv\Scripts\python.exe -m pytest services\user-management\tests -q
.venv\Scripts\python.exe -m pytest services\personal-admin\tests -q
.venv\Scripts\python.exe -m pytest services\system-admin\tests -q
.venv\Scripts\python.exe -m pytest services\opportunity-service\tests -q
.venv\Scripts\python.exe -m pytest services\scout-agent\tests -q
.venv\Scripts\python.exe -m pytest services\relocation-agent\tests -q
.venv\Scripts\python.exe -m pytest services\application-coach-agent\tests -q
```

Frontend kontrolü:

```cmd
cd frontend
npm install
npx tsc --noEmit
npm run build
```

### Docker olmadan tamamen lokal çalıştırma

Uygulama Docker olmadan da çalıştırılabilir; ancak Docker Compose'un yönettiği işlemlerin manuel yapılması gerekir. Python 3.12, Node.js 20, çalışan bir PostgreSQL kurulumu, Python bağımlılıkları, yedi FastAPI servisi ve Next.js frontend gereklidir.

Şu PostgreSQL veritabanlarını oluşturun:

```text
career_users
career_personal
career_system
career_opportunities
```

Proje kökünden veritabanı başlangıç SQL'ini çalıştırabilirsiniz:

```cmd
psql -U postgres -f infra\postgres-init\01-databases.sql
```

Aynı SQL'i pgAdmin üzerinden de çalıştırabilirsiniz.

Backend bağımlılıklarını yükleyin:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```

Her backend servisini ayrı bir CMD penceresinde çalıştırın. `user-management` örneği:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
set JWT_SECRET=...
set INTERNAL_API_KEY=...
set SETTINGS_ENCRYPTION_KEY=...
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Servis ve port eşleşmeleri:

| Servis | Port | Veritabanı |
|---|---:|---|
| user-management | 8001 | `career_users` |
| personal-admin | 8002 | `career_personal` |
| system-admin | 8003 | `career_system` |
| opportunity-service | 8004 | `career_opportunities` |
| scout-agent | 8005 | servise özel yapılandırma |
| relocation-agent | 8006 | servise özel yapılandırma |
| application-coach-agent | 8007 | servise özel yapılandırma |

Frontend'i başka bir CMD penceresinde çalıştırın:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```

Ardından `http://localhost:3000` adresini açın. PostgreSQL çalışır durumda kalmalı, her backend servisi aktif olmalı ve tüm servislerde aynı `JWT_SECRET`, `INTERNAL_API_KEY` ve `SETTINGS_ENCRYPTION_KEY` kullanılmalıdır. Frontend'deki `NEXT_PUBLIC_*_URL` değerleri lokal servis adreslerini göstermelidir. AI özelliklerini kullanmak için `/system-admin` üzerinden veya ortam fallback'i olarak en az bir provider API anahtarı tanımlanmalıdır.

Bu yöntem mümkündür; ancak servisler, terminaller, veritabanları ve ortam değişkenleri manuel yönetildiği için Docker Compose'a göre daha zahmetlidir.

## English

This document explains how to run CareerCoachAgenticAIApp locally with Docker Compose.

### Running fully locally without Docker

The application can run without Docker, but Docker Compose's orchestration work must be performed manually. You need Python 3.12, Node.js 20, a running PostgreSQL installation, the Python dependencies, seven FastAPI services, and the Next.js frontend.

Create these PostgreSQL databases:

```text
career_users
career_personal
career_system
career_opportunities
```

From the project root, the database initialization script can be applied with:

```cmd
psql -U postgres -f infra\postgres-init\01-databases.sql
```

The same SQL can also be run through pgAdmin.

Install the backend dependencies:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```

Run each backend service in a separate CMD window. Example for `user-management`:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\services\user-management
set PYTHONPATH=..\shared
set DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_users
set JWT_SECRET=...
set INTERNAL_API_KEY=...
set SETTINGS_ENCRYPTION_KEY=...
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Service and port mapping:

| Service | Port | Database |
|---|---:|---|
| user-management | 8001 | `career_users` |
| personal-admin | 8002 | `career_personal` |
| system-admin | 8003 | `career_system` |
| opportunity-service | 8004 | `career_opportunities` |
| scout-agent | 8005 | service-specific configuration |
| relocation-agent | 8006 | service-specific configuration |
| application-coach-agent | 8007 | service-specific configuration |

Run the frontend in another CMD window:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npm run dev
```

Open `http://localhost:3000`. PostgreSQL must remain running, each backend service must remain active, and all services must use the same `JWT_SECRET`, `INTERNAL_API_KEY`, and `SETTINGS_ENCRYPTION_KEY`. The frontend `NEXT_PUBLIC_*_URL` values must point to the local service URLs. At least one provider API key must be configured through `/system-admin` or as an environment fallback to use AI features.

This setup is possible but more labor-intensive than Docker Compose because services, terminals, databases, and environment variables are managed manually.

### Security warning

Do not commit `.env` files, API keys, or passwords to Git. If an API key is accidentally exposed in GitHub, a chat, or another shared location, revoke it immediately and create a replacement.

### Prerequisites

- Docker Desktop
- Docker Compose support (`docker compose`)

Check the installation:

```cmd
docker --version
docker compose version
```

### 1. Create the environment file

Open CMD and go to the infrastructure directory:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
copy .env.example .env
notepad .env
```

Change these required values in `.env`:

```env
JWT_SECRET=<long-random-value>
INTERNAL_API_KEY=<long-random-value>
SETTINGS_ENCRYPTION_KEY=<fernet-value>
```

The local frontend URLs can remain unchanged:

```env
NEXT_PUBLIC_USER_MANAGEMENT_URL=http://localhost:8001
NEXT_PUBLIC_PERSONAL_ADMIN_URL=http://localhost:8002
NEXT_PUBLIC_SYSTEM_ADMIN_URL=http://localhost:8003
NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=http://localhost:8004
NEXT_PUBLIC_SCOUT_AGENT_URL=http://localhost:8005
NEXT_PUBLIC_RELOCATION_AGENT_URL=http://localhost:8006
NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=http://localhost:8007
```

### 2. Generate secret values

Use the virtual environment in the project root to generate two random values:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run the command twice. Use the first output for `JWT_SECRET` and the second for `INTERNAL_API_KEY`.

Generate the Fernet encryption key with:

```cmd
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use the output for `SETTINGS_ENCRYPTION_KEY`.

### 3. Provider API keys

The following keys are not required to start the application locally:

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
```

Provider keys should preferably be configured through `/system-admin`. The application encrypts and stores them in the database using Fernet. Environment variables are fallback values used only when no provider key exists in the system-admin database.

### 4. Start the application

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```

On the first start, PostgreSQL databases are created and each service initializes its tables.

Service addresses:

| Service | Address |
|---|---|
| Frontend | http://localhost:3000 |
| user-management | http://localhost:8001 |
| personal-admin | http://localhost:8002 |
| system-admin | http://localhost:8003 |
| opportunity-service | http://localhost:8004 |
| scout-agent | http://localhost:8005 |
| relocation-agent | http://localhost:8006 |
| application-coach-agent | http://localhost:8007 |

Stop the application with `Ctrl+C` in the Compose window.

### 5. Create the first user and system admin

Create the first user at:

```text
http://localhost:3000/register
```

Open the PostgreSQL console from a new CMD window:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose exec postgres psql -U career -d career_users
```

Find the user ID:

```sql
SELECT id, email FROM users;
```

Create the admin record with that ID:

```sql
INSERT INTO system_admins (user_id) VALUES ('USER_ID');
```

Exit PostgreSQL with:

```sql
\q
```

Then use `http://localhost:3000/system-admin` to configure provider keys, models, and agent settings.

### 6. Check service status and logs

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```

To view one service's logs:

```cmd
docker compose logs -f user-management
```

### 7. Run tests

Backend tests:

```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pytest services\shared\tests -q
.venv\Scripts\python.exe -m pytest services\user-management\tests -q
.venv\Scripts\python.exe -m pytest services\personal-admin\tests -q
.venv\Scripts\python.exe -m pytest services\system-admin\tests -q
.venv\Scripts\python.exe -m pytest services\opportunity-service\tests -q
.venv\Scripts\python.exe -m pytest services\scout-agent\tests -q
.venv\Scripts\python.exe -m pytest services\relocation-agent\tests -q
.venv\Scripts\python.exe -m pytest services\application-coach-agent\tests -q
```

Frontend checks:

```cmd
cd frontend
npm install
npx tsc --noEmit
npm run build
```

### PowerShell equivalents

The CMD commands above can also be run in PowerShell. For commands that differ between shells, use these PowerShell forms:

```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
Copy-Item .env.example .env
notepad .env
docker compose up --build
```

PowerShell environment-variable assignments use `$env:`:

```powershell
$env:PYTHONPATH="..\shared"
$env:DATABASE_URL="postgresql+psycopg://career:career@localhost:5432/career_users"
```

For multi-line `gcloud` commands, PowerShell uses a backtick (`) at the end of each continued line, while CMD uses a caret (`^`). Docker, Python, `npm`, `uvicorn`, `curl`, and `gcloud` commands otherwise have the same syntax in both shells.
