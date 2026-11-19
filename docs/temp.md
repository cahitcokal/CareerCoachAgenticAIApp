# Lokal Kurulum Rehberi / Local Setup Guide

## Türkçe

Bu belge, CareerCoachAgenticAIApp projesini Docker Compose ile lokal ortamda çalıştırmak için hazırlanmıştır.

### Güvenlik uyarısı

`.env`, API anahtarları ve şifreler Git'e commit edilmemelidir. Eğer bir API anahtarı GitHub'a, sohbete veya başka bir ortak ortama yanlışlıkla gönderildiyse hemen iptal edilip yenisi oluşturulmalıdır.

### Ön koşullar

- Docker Desktop
- Docker Compose desteği (`docker compose`)

Kontrol:

PowerShell:
```powershell
docker --version
docker compose version
```
Command Prompt:
```cmd
docker --version
docker compose version
```

### 1. Ortam dosyasını oluşturma

PowerShell ile proje klasörüne gidin:

```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
Copy-Item .env.example .env
notepad .env
```
Command Prompt ile proje klasörüne gidin:

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

### Veritabanı sağlayıcısını seçme

Veritabanı seçimi servis kodundan ayrılmıştır. `infra/.env` içindeki aşağıdaki
değerlerle her veritabanı sahibi servis için SQLite, PostgreSQL, Supabase veya
Neon seçebilirsiniz:

```env
USER_MANAGEMENT_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_users
PERSONAL_ADMIN_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_personal
SYSTEM_ADMIN_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_system
OPPORTUNITY_SERVICE_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_opportunities
```

SQLite için servis başına ayrı bir URL kullanın; örneğin
`sqlite:///./runtime/user-management.db`. Supabase ve Neon için sağlayıcının
verdiği `postgresql://` URL'si kullanılabilir; ortak adapter bunu otomatik
olarak `psycopg` sürücüsüne uyarlar. Ajan servisleri veritabanına doğrudan
bağlanmaz; veritabanı sahibi servislerin API'lerini kullanır.

### 2. Secret değerlerini üretme

Proje kökünde bulunan sanal ortamı kullanarak iki rastgele değer üretin:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Komutu iki kez çalıştırın. İlk çıktıyı `JWT_SECRET`, ikinci çıktıyı `INTERNAL_API_KEY` için kullanın.

Fernet encryption key üretmek için:

PowerShell:
```powershell
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```

İlk çalıştırma sırasında yapılandırılan veritabanı bağlantıları kullanılır ve
servisler kendi tablolarını başlatır. Varsayılan Compose ayarları PostgreSQL'i
kullanır.

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

İlk kullanıcıyı system admin yapmak için yeni bir terminal penceresinde PostgreSQL konsolunu açın:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose exec postgres psql -U career -d career_users
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```

Tek bir servisin loglarını görmek için:

PowerShell:
```powershell
docker compose logs -f user-management
```
Command Prompt:
```cmd
docker compose logs -f user-management
```

### 7. Testleri çalıştırma

Backend testleri:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pytest services\shared\tests -q
.venv\Scripts\python.exe -m pytest services\user-management\tests -q
.venv\Scripts\python.exe -m pytest services\personal-admin\tests -q
.venv\Scripts\python.exe -m pytest services\system-admin\tests -q
.venv\Scripts\python.exe -m pytest services\opportunity-service\tests -q
.venv\Scripts\python.exe -m pytest services\scout-agent\tests -q
.venv\Scripts\python.exe -m pytest services\relocation-agent\tests -q
.venv\Scripts\python.exe -m pytest services\application-coach-agent\tests -q
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npx tsc --noEmit
npm run build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npx tsc --noEmit
npm run build
```

### Docker olmadan tamamen lokal çalıştırma

Uygulama Docker olmadan da çalıştırılabilir; ancak Docker Compose'un yönettiği
işlemlerin manuel yapılması gerekir. Python 3.12, Node.js 20, Python
bağımlılıkları, yedi FastAPI servisi ve Next.js frontend gereklidir. PyCharm
veya `scripts\run_service.py` kullanıldığında SQLite varsayılan olduğu için
lokal PostgreSQL kurulumu zorunlu değildir.

PostgreSQL, Supabase veya Neon kullanacaksanız her veritabanı sahibi servis
için ayrı bir `DATABASE_URL` ayarlayın. SQLite ile başlamak için servisleri
proje kökünden şu ortak giriş noktasıyla çalıştırın:

```text
scripts\run_service.py user-management
scripts\run_service.py personal-admin
scripts\run_service.py system-admin
scripts\run_service.py opportunity-service
```

Backend bağımlılıklarını yükleyin:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```

Her backend servisini ayrı bir terminal penceresinde çalıştırın. `user-management` örneği:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
$env:DATABASE_URL="sqlite:///./runtime/user-management.db"
$env:JWT_SECRET="..."
$env:INTERNAL_API_KEY="..."
$env:SETTINGS_ENCRYPTION_KEY="..."
.venv\Scripts\python.exe scripts\run_service.py user-management
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set DATABASE_URL=sqlite:///./runtime/user-management.db
set JWT_SECRET=...
set INTERNAL_API_KEY=...
set SETTINGS_ENCRYPTION_KEY=...
.venv\Scripts\python.exe scripts\run_service.py user-management
```

Servis ve port eşleşmeleri:

| Servis | Port | Veritabanı |
|---|---:|---|
| user-management | 8001 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase veya Neon |
| personal-admin | 8002 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase veya Neon |
| system-admin | 8003 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase veya Neon |
| opportunity-service | 8004 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase veya Neon |
| scout-agent | 8005 | servise özel yapılandırma |
| relocation-agent | 8006 | servise özel yapılandırma |
| application-coach-agent | 8007 | servise özel yapılandırma |

Frontend'i başka bir terminal penceresinde çalıştırın:

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

Ardından `http://localhost:3000` adresini açın. PostgreSQL çalışır durumda kalmalı, her backend servisi aktif olmalı ve tüm servislerde aynı `JWT_SECRET`, `INTERNAL_API_KEY` ve `SETTINGS_ENCRYPTION_KEY` kullanılmalıdır. Frontend'deki `NEXT_PUBLIC_*_URL` değerleri lokal servis adreslerini göstermelidir. AI özelliklerini kullanmak için `/system-admin` üzerinden veya ortam fallback'i olarak en az bir provider API anahtarı tanımlanmalıdır.

Bu yöntem mümkündür; ancak servisler, terminaller, veritabanları ve ortam değişkenleri manuel yönetildiği için Docker Compose'a göre daha zahmetlidir.

## English

This document explains how to run CareerCoachAgenticAIApp locally with Docker Compose.

### Running fully locally without Docker

The application can run without Docker, but Docker Compose's orchestration work
must be performed manually. You need Python 3.12, Node.js 20, the Python
dependencies, seven FastAPI services, and the Next.js frontend. A local
PostgreSQL installation is not required when PyCharm or `scripts\run_service.py`
is used because SQLite is the default.

If you use PostgreSQL, Supabase, or Neon, set a separate `DATABASE_URL` for
each database-owning service. To start with SQLite, run services from the
project root through the shared entry point:

```text
scripts\run_service.py user-management
scripts\run_service.py personal-admin
scripts\run_service.py system-admin
scripts\run_service.py opportunity-service
```

Install the backend dependencies:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pip install -r services\requirements-dev.txt
```

Run each backend service in a separate terminal window. Example for `user-management`:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
$env:DATABASE_URL="sqlite:///./runtime/user-management.db"
$env:JWT_SECRET="..."
$env:INTERNAL_API_KEY="..."
$env:SETTINGS_ENCRYPTION_KEY="..."
.venv\Scripts\python.exe scripts\run_service.py user-management
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set DATABASE_URL=sqlite:///./runtime/user-management.db
set JWT_SECRET=...
set INTERNAL_API_KEY=...
set SETTINGS_ENCRYPTION_KEY=...
.venv\Scripts\python.exe scripts\run_service.py user-management
```

Service and port mapping:

| Service | Port | Database |
|---|---:|---|
| user-management | 8001 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase, or Neon |
| personal-admin | 8002 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase, or Neon |
| system-admin | 8003 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase, or Neon |
| opportunity-service | 8004 | `DATABASE_URL` / SQLite, PostgreSQL, Supabase, or Neon |
| scout-agent | 8005 | service-specific configuration |
| relocation-agent | 8006 | service-specific configuration |
| application-coach-agent | 8007 | service-specific configuration |

Run the frontend in another terminal window:

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

Open `http://localhost:3000`. PostgreSQL must remain running, each backend service must remain active, and all services must use the same `JWT_SECRET`, `INTERNAL_API_KEY`, and `SETTINGS_ENCRYPTION_KEY`. The frontend `NEXT_PUBLIC_*_URL` values must point to the local service URLs. At least one provider API key must be configured through `/system-admin` or as an environment fallback to use AI features.

This setup is possible but more labor-intensive than Docker Compose because services, terminals, databases, and environment variables are managed manually.

### Security warning

Do not commit `.env` files, API keys, or passwords to Git. If an API key is accidentally exposed in GitHub, a chat, or another shared location, revoke it immediately and create a replacement.

### Prerequisites

- Docker Desktop
- Docker Compose support (`docker compose`)

Check the installation:

PowerShell:
```powershell
docker --version
docker compose version
```
Command Prompt:
```cmd
docker --version
docker compose version
```

### 1. Create the environment file

Open a terminal and go to the infrastructure directory:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
Copy-Item .env.example .env
notepad .env
```
Command Prompt:
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

### Selecting a database provider

Database selection is isolated from service code. In `infra/.env`, change the
following values to choose SQLite, PostgreSQL, Supabase, or Neon for each
database-owning service:

```env
USER_MANAGEMENT_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_users
PERSONAL_ADMIN_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_personal
SYSTEM_ADMIN_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_system
OPPORTUNITY_SERVICE_DATABASE_URL=postgresql+psycopg://career:career@postgres:5432/career_opportunities
```

Use a separate URL per service for SQLite, such as
`sqlite:///./runtime/user-management.db`. For Supabase and Neon, use the
provider's `postgresql://` URL; the shared adapter normalizes it to the
`psycopg` driver. Agent services do not connect to a database directly; they
use the APIs of the database-owning services.

### 2. Generate secret values

Use the virtual environment in the project root to generate two random values:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run the command twice. Use the first output for `JWT_SECRET` and the second for `INTERNAL_API_KEY`.

Generate the Fernet encryption key with:

PowerShell:
```powershell
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose up --build
```

On the first start, the configured database URLs are used and each service
initializes its own tables. The default Compose configuration uses PostgreSQL.

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

Open the PostgreSQL console from a new terminal window:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose exec postgres psql -U career -d career_users
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\infra
docker compose ps
docker compose logs -f
```

To view one service's logs:

PowerShell:
```powershell
docker compose logs -f user-management
```
Command Prompt:
```cmd
docker compose logs -f user-management
```

### 7. Run tests

Backend tests:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -m pytest services\shared\tests -q
.venv\Scripts\python.exe -m pytest services\user-management\tests -q
.venv\Scripts\python.exe -m pytest services\personal-admin\tests -q
.venv\Scripts\python.exe -m pytest services\system-admin\tests -q
.venv\Scripts\python.exe -m pytest services\opportunity-service\tests -q
.venv\Scripts\python.exe -m pytest services\scout-agent\tests -q
.venv\Scripts\python.exe -m pytest services\relocation-agent\tests -q
.venv\Scripts\python.exe -m pytest services\application-coach-agent\tests -q
```
Command Prompt:
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

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npx tsc --noEmit
npm run build
```
Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
npm install
npx tsc --noEmit
npm run build
```
