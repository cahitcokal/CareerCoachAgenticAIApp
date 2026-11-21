# Google Cloud Deployment Rehberi / Google Cloud Deployment Guide

## Türkçe

Bu belge, CareerCoachAgenticAIApp projesini Google Cloud Platform (GCP) üzerinde adım adım nasıl deploy edeceğinizi açıklar. Proje ID'niz: `careercoachagenticaiapp`.

### Ön koşullar

- Google Cloud proje oluşturulmuş ve erişilebilir durumda
- gcloud CLI yüklü ve yapılandırılmış
- Cloud SQL Proxy bileşeni yüklü:

PowerShell:
```powershell
gcloud components install cloud-sql-proxy
```

Command Prompt:
```cmd
gcloud components install cloud-sql-proxy
```

- psql client yüklü (Cloud SQL bağlantısı için):
  - Windows için PostgreSQL'i indirip kurun: https://www.postgresql.org/download/windows/
  - Veya Cloud Console > SQL > Databases > Query Editor kullanın
- Docker Desktop yüklü (yerel build için)
- Proje kök dizini: `C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp`

### 1. gcloud CLI Kurulumu ve Proje Yapılandırması

gcloud CLI'yi yükleyin ve projenizi yapılandırın:

PowerShell:
```powershell
gcloud auth login
gcloud config set project careercoachagenticaiapp
```

Command Prompt:
```cmd
gcloud auth login
gcloud config set project careercoachagenticaiapp
```

Gerekli API'leri etkinleştirin:

PowerShell:
```powershell
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

Command Prompt:
```cmd
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### 2. Cloud SQL for PostgreSQL Oluşturma

Tek bir PostgreSQL instance oluşturun ve 4 veritabanı oluşturun:

PowerShell:
```powershell
gcloud sql instances create careercoach-db `
  --database-version=POSTGRES_16 `
  --tier=db-perf-optimized-N-2 `
  --region=europe-west1 `
  --storage-auto-increase `
  --storage-size=10GB
```

Command Prompt:
```cmd
gcloud sql instances create careercoach-db ^
  --database-version=POSTGRES_16 ^
  --tier=db-perf-optimized-N-2 ^
  --region=europe-west1 ^
  --storage-auto-increase ^
  --storage-size=10GB
```

Veritabanlarını oluşturun:

PowerShell:
```powershell
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

Command Prompt:
```cmd
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

PostgreSQL kullanıcı şifresini ayarlayın (not edin, daha sonra kullanacaksınız):

PowerShell:
```powershell
gcloud sql users set-password career --instance=careercoach-db --prompt-for-password
```

Command Prompt:
```cmd
gcloud sql users set-password career --instance=careercoach-db --prompt-for-password
```

### 3. Secret Manager ile Gizli Anahtarlar Oluşturma

JWT secret, internal API key ve settings encryption key oluşturun:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))" | Out-Null
# Yukarıdaki komutun çıktısını JWT_SECRET olarak kullanın
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# Yukarıdaki komutun çıktısını JWT_SECRET olarak kullanın
```

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# Yukarıdaki komutun çıktısını INTERNAL_API_KEY olarak kullanın
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# Yukarıdaki komutun çıktısını INTERNAL_API_KEY olarak kullanın
```

Secret'ları oluşturun:

PowerShell:
```powershell
echo "your-jwt-secret-here" | gcloud secrets create jwt-secret --data-file=-
echo "your-internal-api-key-here" | gcloud secrets create internal-api-key --data-file=-
```

Command Prompt:
```cmd
echo your-jwt-secret-here | gcloud secrets create jwt-secret --data-file=-
echo your-internal-api-key-here | gcloud secrets create internal-api-key --data-file=-
```

Fernet encryption key oluşturun:

PowerShell:
```powershell
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | gcloud secrets create settings-encryption-key --data-file=-
```

Command Prompt:
```cmd
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | gcloud secrets create settings-encryption-key --data-file=-
```

İsteğe bağlı: Provider API key'leri (System Admin UI'dan da yapılandırabilirsiniz):

PowerShell:
```powershell
echo "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
```

Command Prompt:
```cmd
echo your-gemini-api-key | gcloud secrets create gemini-api-key --data-file=-
```

### 4. Artifact Registry Oluşturma (Opsiyonel ama önerilir)

Docker imajlarını saklamak için Artifact Registry oluşturun:

PowerShell:
```powershell
gcloud artifacts repositories create careercoach-repo `
  --repository-format=docker `
  --location=europe-west1 `
  --description="CareerCoach Docker repository"
```

Command Prompt:
```cmd
gcloud artifacts repositories create careercoach-repo ^
  --repository-format=docker ^
  --location=europe-west1 ^
  --description="CareerCoach Docker repository"
```

### Secret Manager İzinleri

Cloud Run servisinin secret'lara erişebilmesi için compute service account'a Secret Manager Secret Accessor rolü verin:

PowerShell:
```powershell
$PROJECT_NUMBER = gcloud projects describe careercoachagenticaiapp --format="value(projectNumber)"
gcloud projects add-iam-policy-binding careercoachagenticaiapp `
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

Command Prompt:
```cmd
for /f "delims=" %i in ('gcloud projects describe careercoachagenticaiapp --format="value(projectNumber)"') do set PROJECT_NUMBER=%i
gcloud projects add-iam-policy-binding careercoachagenticaiapp ^
  --member="serviceAccount:%PROJECT_NUMBER%-compute@developer.gserviceaccount.com" ^
  --role="roles/secretmanager.secretAccessor"
```

### 5. Backend Servislerini Deploy Etme

Her Python servisini Cloud Run'a deploy edin. Önce user-management:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/user-management/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\user-management\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/user-management .
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/user-management .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy user-management `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/user-management `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_users?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db"
```

Command Prompt:
```cmd
set DB_PASSWORD=your-db-password-here
gcloud run deploy user-management ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_users?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db"
```

Deploy tamamlandığında URL'yi not edin (örn: `https://user-management-xxxxx.run.app`).

personal-admin deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/personal-admin/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\personal-admin\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/personal-admin .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/personal-admin .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy personal-admin `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/personal-admin `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_personal?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy personal-admin ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/personal-admin ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_personal?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

system-admin deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/system-admin/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\system-admin\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/system-admin .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/system-admin .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy system-admin `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/system-admin `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_system?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy system-admin ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/system-admin ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_system?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

opportunity-service deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/opportunity-service/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\opportunity-service\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/opportunity-service .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/opportunity-service .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy opportunity-service `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/opportunity-service `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_opportunities?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy opportunity-service ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/opportunity-service ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_opportunities?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

scout-agent deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/scout-agent/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\scout-agent\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/scout-agent .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/scout-agent .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy scout-agent `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/scout-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy scout-agent ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/scout-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

relocation-agent deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/relocation-agent/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\relocation-agent\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/relocation-agent .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/relocation-agent .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy relocation-agent `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/relocation-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy relocation-agent ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/relocation-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

application-coach-agent deploy:

Önce Dockerfile'ı proje köküne kopyalayın:

PowerShell:
```powershell
Copy-Item services/application-coach-agent/Dockerfile Dockerfile
```

Command Prompt:
```cmd
copy services\application-coach-agent\Dockerfile Dockerfile
```

Sonra Docker imajını build edin:

PowerShell:
```powershell
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/application-coach-agent .
```

Command Prompt:
```cmd
gcloud builds submit --tag europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/application-coach-agent .
```

Build tamamlandıktan sonra Dockerfile'ı silebilirsiniz:

PowerShell:
```powershell
Remove-Item Dockerfile
```

Command Prompt:
```cmd
del Dockerfile
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy application-coach-agent `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/application-coach-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy application-coach-agent ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/application-coach-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

### 6. Frontend Deploy Etme

Frontend için environment variables'ları build-time'da gömmeniz gerekir. cloudbuild.yaml dosyası substitutions kullanır:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
gcloud builds submit --config cloudbuild.yaml ^
  --substitutions=_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp\frontend
gcloud builds submit --config cloudbuild.yaml ^
  --substitutions=_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app
```

Sonra Cloud Run'a deploy edin:

PowerShell:
```powershell
gcloud run deploy frontend `
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/frontend `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,NEXT_PUBLIC_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,NEXT_PUBLIC_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,NEXT_PUBLIC_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,NEXT_PUBLIC_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy frontend ^
  --image europe-west1-docker.pkg.dev/careercoachagenticaiapp/careercoach-repo/frontend ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,NEXT_PUBLIC_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,NEXT_PUBLIC_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,NEXT_PUBLIC_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,NEXT_PUBLIC_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app"
```

### 7. İlk Kullanıcı ve System Admin Oluşturma

Frontend URL'sini açın (örn: `https://frontend-xxxxx.run.app/register`) ve ilk kullanıcıyı kaydedin.

System admin yapmak için Cloud SQL'e bağlanın:

PowerShell:
```powershell
gcloud sql connect careercoach-db --user=career --database=career_users
```

Command Prompt:
```cmd
gcloud sql connect careercoach-db --user=career --database=career_users
```

Kullanıcı ID'sini bulun:

```sql
SELECT id, email FROM users;
```

System admin olarak atayın:

```sql
INSERT INTO system_admins (user_id) VALUES ('USER_ID_HERE');
```

Çıkış:

```sql
\q
```

### 8. System Admin Yapılandırması

1. Frontend'de `/system-admin` sayfasına gidin
2. Dilleri ekleyin (tr, en vb.)
3. Provider API key'lerini girin (Gemini, OpenAI, Anthropic, Groq vb.)
4. Model listelerini yapılandırın
5. Ajan ayarlarını düzenleyin

### 9. İlk Profil Oluşturma

1. `/admin` (Personal Admin) sayfasına gidin
2. İlk profili oluşturun
3. Hedef ülkeleri, siteleri ve rolleri yapılandırın

### 10. Deploy Durumunu Kontrol Etme

Tüm servislerin durumunu kontrol edin:

PowerShell:
```powershell
gcloud run services list --region europe-west1
```

Command Prompt:
```cmd
gcloud run services list --region europe-west1
```

Logları görüntüleyin:

PowerShell:
```powershell
gcloud run services logs tail user-management --region europe-west1
```

Command Prompt:
```cmd
gcloud run services logs tail user-management --region europe-west1
```

### 11. IAM İzinleri

Gerekirse IAM rollerini ayarlayın:

PowerShell:
```powershell
gcloud projects add-iam-policy-binding careercoachagenticaiapp `
  --member="allUsers" `
  --role="roles/run.invoker"
```

Command Prompt:
```cmd
gcloud projects add-iam-policy-binding careercoachagenticaiapp ^
  --member="allUsers" ^
  --role="roles/run.invoker"
```

### 12. Maliyet Optimizasyonu

Maliyetleri optimize etmek için:

- Min instances 0 ayarlayın (cold start kabul ediyorsanız)
- Concurrency ayarlarını optimize edin
- CPU ve memory allocation'ları ihtiyaca göre ayarlayın

Min instance 0 ayarlama örneği:

PowerShell:
```powershell
gcloud run services update user-management `
  --region europe-west1 `
  --min-instances=0 `
  --max-instances=10
```

Command Prompt:
```cmd
gcloud run services update user-management ^
  --region europe-west1 ^
  --min-instances=0 ^
  --max-instances=10
```

### 13. Domain Ayarlama (Opsiyonel)

Kendi domain'inizi bağlamak için:

1. Cloud Run servisine domain mapping ekleyin:

PowerShell:
```powershell
gcloud run domain mappings create api.careercoach.com `
  --service=user-management `
  --region europe-west1
```

Command Prompt:
```cmd
gcloud run domain mappings create api.careercoach.com ^
  --service=user-management ^
  --region europe-west1
```

2. DNS kayıtlarını Google Cloud'dan aldığınız CNAME ile güncelleyin

### 14. Monitoring ve Alerting

Cloud Monitoring'i etkinleştirin:

PowerShell:
```powershell
gcloud logging settings update --enable-storage-log
gcloud monitoring app-settings create
```

Command Prompt:
```cmd
gcloud logging settings update --enable-storage-log
gcloud monitoring app-settings create
```

### Sorun Giderme

**Servis başlamıyor:**
- Logları kontrol edin: `gcloud run services logs tail <service-name> --region europe-west1`
- Environment variables'ları doğrulayın
- Secret erişimini kontrol edin

**Veritabanı bağlantı hatası:**
- Cloud SQL instance'ın çalıştığını doğrulayın
- Connection string'i kontrol edin
- IP whitelisting'i kontrol edin (socket kullanıyorsanız gerekli değil)

**Secret erişim hatası:**
- Secret'ların oluşturulduğunu doğrulayın: `gcloud secrets list`
- IAM izinlerini kontrol edin

## English

This document explains how to deploy CareerCoachAgenticAIApp to Google Cloud Platform (GCP) step by step. Your project ID: `careercoachagenticaiapp`.

### Prerequisites

- Google Cloud project created and accessible
- gcloud CLI installed and configured
- Docker Desktop installed (for local builds)
- Project root: `C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp`

### 1. gcloud CLI Setup and Project Configuration

Install gcloud CLI and configure your project:

PowerShell:
```powershell
gcloud auth login
gcloud config set project careercoachagenticaiapp
```

Command Prompt:
```cmd
gcloud auth login
gcloud config set project careercoachagenticaiapp
```

Enable required APIs:

PowerShell:
```powershell
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

Command Prompt:
```cmd
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### 2. Create Cloud SQL for PostgreSQL

Create a single PostgreSQL instance and 4 databases:

PowerShell:
```powershell
gcloud sql instances create careercoach-db `
  --database-version=POSTGRES_16 `
  --tier=db-perf-optimized-N-2 `
  --region=europe-west1 `
  --storage-auto-increase `
  --storage-size=10GB
```

Command Prompt:
```cmd
gcloud sql instances create careercoach-db ^
  --database-version=POSTGRES_16 ^
  --tier=db-perf-optimized-N-2 ^
  --region=europe-west1 ^
  --storage-auto-increase ^
  --storage-size=10GB
```

Create databases:

PowerShell:
```powershell
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

Command Prompt:
```cmd
gcloud sql databases create career_users --instance=careercoach-db
gcloud sql databases create career_personal --instance=careercoach-db
gcloud sql databases create career_system --instance=careercoach-db
gcloud sql databases create career_opportunities --instance=careercoach-db
```

Set PostgreSQL user password (note it down, you'll need it later):

PowerShell:
```powershell
gcloud sql users set-password career --instance=careercoach-db --prompt-for-password
```

Command Prompt:
```cmd
gcloud sql users set-password career --instance=careercoach-db --prompt-for-password
```

### 3. Create Secrets with Secret Manager

Create JWT secret, internal API key, and settings encryption key:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))" | Out-Null
# Use the output of the above command as JWT_SECRET
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# Use the output of the above command as JWT_SECRET
```

Create secrets:

PowerShell:
```powershell
echo "your-jwt-secret-here" | gcloud secrets create jwt-secret --data-file=-
echo "your-internal-api-key-here" | gcloud secrets create internal-api-key --data-file=-
```

Command Prompt:
```cmd
echo your-jwt-secret-here | gcloud secrets create jwt-secret --data-file=-
echo your-internal-api-key-here | gcloud secrets create internal-api-key --data-file=-
```

Create Fernet encryption key:

PowerShell:
```powershell
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | gcloud secrets create settings-encryption-key --data-file=-
```

Command Prompt:
```cmd
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | gcloud secrets create settings-encryption-key --data-file=-
```

Optional: Provider API keys (can also be configured via System Admin UI):

PowerShell:
```powershell
echo "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
```

Command Prompt:
```cmd
echo your-gemini-api-key | gcloud secrets create gemini-api-key --data-file=-
```

### 4. Create Artifact Registry (Optional but recommended)

Create Artifact Registry to store Docker images:

PowerShell:
```powershell
gcloud artifacts repositories create careercoach-repo `
  --repository-format=docker `
  --location=europe-west1 `
  --description="CareerCoach Docker repository"
```

Command Prompt:
```cmd
gcloud artifacts repositories create careercoach-repo ^
  --repository-format=docker ^
  --location=europe-west1 ^
  --description="CareerCoach Docker repository"
```

### 5. Deploy Backend Services

Deploy each Python service to Cloud Run. First, user-management:

PowerShell:
```powershell
cd C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
gcloud run deploy user-management `
  --source services/user-management `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_users?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db"
```

Command Prompt:
```cmd
cd /d C:\Users\cahitcokal\PycharmProjects\CareerCoachAgenticAIApp
set DB_PASSWORD=your-db-password-here
gcloud run deploy user-management ^
  --source services/user-management ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_users?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db"
```

Note the URL when deployment completes (e.g., `https://user-management-xxxxx.run.app`).

Deploy personal-admin:

PowerShell:
```powershell
gcloud run deploy personal-admin `
  --source services/personal-admin `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_personal?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy personal-admin ^
  --source services/personal-admin ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_personal?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Deploy system-admin:

PowerShell:
```powershell
gcloud run deploy system-admin `
  --source services/system-admin `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_system?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy system-admin ^
  --source services/system-admin ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest,SETTINGS_ENCRYPTION_KEY=settings-encryption-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_system?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app"
```

Deploy opportunity-service:

PowerShell:
```powershell
gcloud run deploy opportunity-service `
  --source services/opportunity-service `
  --region europe-west1 `
  --allow-unauthenticated `
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:YOUR_DB_PASSWORD@/career_opportunities?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db","USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy opportunity-service ^
  --source services/opportunity-service ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --add-cloudsql-instances careercoachagenticaiapp:europe-west1:careercoach-db ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg://career:%DB_PASSWORD%@/career_opportunities?host=/cloudsql/careercoachagenticaiapp:europe-west1:careercoach-db,USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Deploy scout-agent:

PowerShell:
```powershell
gcloud run deploy scout-agent `
  --source services/scout-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy scout-agent ^
  --source services/scout-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Deploy relocation-agent:

PowerShell:
```powershell
gcloud run deploy relocation-agent `
  --source services/relocation-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy relocation-agent ^
  --source services/relocation-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Deploy application-coach-agent:

PowerShell:
```powershell
gcloud run deploy application-coach-agent `
  --source services/application-coach-agent `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" `
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app","OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app","SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy application-coach-agent ^
  --source services/application-coach-agent ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-secrets "JWT_SECRET=jwt-secret:latest,INTERNAL_API_KEY=internal-api-key:latest" ^
  --set-env-vars "USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app"
```

### 6. Deploy Frontend

For frontend, you need to embed environment variables at build time:

PowerShell:
```powershell
gcloud run deploy frontend `
  --source frontend `
  --region europe-west1 `
  --allow-unauthenticated `
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,NEXT_PUBLIC_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,NEXT_PUBLIC_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,NEXT_PUBLIC_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,NEXT_PUBLIC_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app"
```

Command Prompt:
```cmd
gcloud run deploy frontend ^
  --source frontend ^
  --region europe-west1 ^
  --allow-unauthenticated ^
  --set-env-vars "NEXT_PUBLIC_USER_MANAGEMENT_URL=https://user-management-xxxxx.run.app,NEXT_PUBLIC_PERSONAL_ADMIN_URL=https://personal-admin-xxxxx.run.app,NEXT_PUBLIC_SYSTEM_ADMIN_URL=https://system-admin-xxxxx.run.app,NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL=https://opportunity-service-xxxxx.run.app,NEXT_PUBLIC_SCOUT_AGENT_URL=https://scout-agent-xxxxx.run.app,NEXT_PUBLIC_RELOCATION_AGENT_URL=https://relocation-agent-xxxxx.run.app,NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL=https://application-coach-agent-xxxxx.run.app"
```

### 7. Create First User and System Admin

Open the frontend URL (e.g., `https://frontend-xxxxx.run.app/register`) and register the first user.

To make them a system admin, connect to Cloud SQL:

PowerShell:
```powershell
gcloud sql connect careercoach-db --user=career --database=career_users
```

Command Prompt:
```cmd
gcloud sql connect careercoach-db --user=career --database=career_users
```

Find the user ID:

```sql
SELECT id, email FROM users;
```

Assign as system admin:

```sql
INSERT INTO system_admins (user_id) VALUES ('USER_ID_HERE');
```

Exit:

```sql
\q
```

### 8. System Admin Configuration

1. Navigate to `/system-admin` in the frontend
2. Add languages (tr, en, etc.)
3. Enter provider API keys (Gemini, OpenAI, Anthropic, Groq, etc.)
4. Configure model lists
5. Edit agent settings

### 9. Create First Profile

1. Navigate to `/admin` (Personal Admin)
2. Create the first profile
3. Configure target countries, sites, and roles

### 10. Check Deployment Status

Check status of all services:

PowerShell:
```powershell
gcloud run services list --region europe-west1
```

Command Prompt:
```cmd
gcloud run services list --region europe-west1
```

View logs:

PowerShell:
```powershell
gcloud run services logs tail user-management --region europe-west1
```

Command Prompt:
```cmd
gcloud run services logs tail user-management --region europe-west1
```

### 11. IAM Permissions

If needed, set up IAM roles:

PowerShell:
```powershell
gcloud projects add-iam-policy-binding careercoachagenticaiapp `
  --member="allUsers" `
  --role="roles/run.invoker"
```

Command Prompt:
```cmd
gcloud projects add-iam-policy-binding careercoachagenticaiapp ^
  --member="allUsers" ^
  --role="roles/run.invoker"
```

### 12. Cost Optimization

To optimize costs:

- Set min instances to 0 (if you accept cold starts)
- Optimize concurrency settings
- Adjust CPU and memory allocation based on needs

Example to set min instances to 0:

PowerShell:
```powershell
gcloud run services update user-management `
  --region europe-west1 `
  --min-instances=0 `
  --max-instances=10
```

Command Prompt:
```cmd
gcloud run services update user-management ^
  --region europe-west1 ^
  --min-instances=0 ^
  --max-instances=10
```

### 13. Domain Setup (Optional)

To connect your own domain:

1. Add domain mapping to Cloud Run service:

PowerShell:
```powershell
gcloud run domain mappings create api.careercoach.com `
  --service=user-management `
  --region europe-west1
```

Command Prompt:
```cmd
gcloud run domain mappings create api.careercoach.com ^
  --service=user-management ^
  --region europe-west1
```

2. Update DNS records with the CNAME provided by Google Cloud

### 14. Monitoring and Alerting

Enable Cloud Monitoring:

PowerShell:
```powershell
gcloud logging settings update --enable-storage-log
gcloud monitoring app-settings create
```

Command Prompt:
```cmd
gcloud logging settings update --enable-storage-log
gcloud monitoring app-settings create
```

### Troubleshooting

**Service not starting:**
- Check logs: `gcloud run services logs tail <service-name> --region europe-west1`
- Verify environment variables
- Check secret access

**Database connection error:**
- Verify Cloud SQL instance is running
- Check connection string
- Check IP whitelisting (not needed if using socket)

**Secret access error:**
- Verify secrets are created: `gcloud secrets list`
- Check IAM permissions
