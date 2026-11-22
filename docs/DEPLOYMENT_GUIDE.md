# CareerCoachAgenticAIApp — Prodüksiyon Dağıtım (Deployment) Rehberi

Bu doküman, **CareerCoachAgenticAIApp** mikroservis mimarisinin **Hetzner Cloud (Ubuntu VPS)** ve **Coolify (PaaS)** kullanılarak canlı ortama (production) alınması için gereken altyapı hazırlığı, kod düzenleme, GitHub versiyonlama, ilk kurulum ve sonraki otomatik güncellemelerin adımlarını içerir.

## İçindekiler

1. [Altyapı Hazırlığı ve Sunucu Kurulumu](#1-altyapı-hazırlığı-ve-sunucu-kurulumu)
2. [Lokalde Yapılacak Kod Değişiklikleri (LLM Prompt)](#2-lokalde-yapılacak-kod-değişiklikleri-llm-prompt)
3. [GitHub Üzerinde Versiyonlama](#3-github-üzerinde-versiyonlama)
4. [Sunucu Kurulumu ve İlk Canlıya Çıkış (Manuel Zorunlu Adımlar)](#4-sunucu-kurulumu-ve-ilk-canlıya-çıkış-manuel-zorunlu-adımlar)
5. [İlk Kurulum Sonrası Güncellemeler (Otomatik CI/CD Süreci)](#5-ilk-kurulum-sonrası-güncellemeler-otomatik-cicd-süreci)
6. [Canlıya Çıktıktan Sonra Kontrol Listesi](#6-canlıya-çıktıktan-sonra-kontrol-listesi)

---

## 1. Altyapı Hazırlığı ve Sunucu Kurulumu

Canlıya çıkış için yalnızca **1 adet Hetzner Cloud Sunucusu (VPS)** yeterlidir. Alan adı için aşağıdaki üç seçenekten birini tercih edebilirsiniz.

### Adım 1.1: Alan Adı Seçimi (Ücretsiz veya Ücretli Alternatifler)

#### Seçenek A (Ücretsiz): DuckDNS ile Ücretsiz Subdomain Alma
1. [duckdns.org](https://www.duckdns.org/) adresine gidin ve **GitHub** (veya Google) hesabınızla giriş yapın. *(Not: Türkiye'deki bazı ISS'lerde site açılmazsa tarayıcıda Güvenli DNS / `1.1.1.1` kullanabilir veya doğrudan **Seçenek C (`sslip.io`)** ile devam edebilirsiniz.)*
2. **domains** bölümüne istediğiniz alt alan adını yazıp **add domain** butonuna tıklayın (örnek: `careercoachapp` → adresiniz `careercoachapp.duckdns.org` olur).
3. DuckDNS wildcard desteği sunduğu için ekstra kayıt açmadan şu 3 adresi doğrudan kullanabilirsiniz:
   * Frontend: `https://careercoachapp.duckdns.org`
   * API Gateway: `https://api.careercoachapp.duckdns.org`
   * Yönetim Paneli: `https://coolify.careercoachapp.duckdns.org`

#### Seçenek B (Ücretli): Özel Alan Adı Satın Alma
* **Cloudflare Registrar** (~$10–$12/yıl) üzerinden özel bir domain satın alabilir ve DNS kayıtlarını Cloudflare üzerinden yönetebilirsiniz.

#### Seçenek C (En Pratik & Kayıt Gerektirmeyen Ücretsiz Çözüm): Coolify Dahili `sslip.io` Kullanımı
Hiçbir dış web sitesine kayıt olmadan, doğrudan Hetzner sunucunuzun Public IPv4 adresini (örnek: `49.12.xx.xx`) kullanarak ücretsiz alt alan adı ve otomatik HTTPS (Let's Encrypt SSL) alabilirsiniz:
1. Herhangi bir DNS sitesine girmenize gerek yoktur; `sslip.io` adresteki IP'yi otomatik olarak sunucunuza çözer.
2. Hetzner sunucunuzu oluşturduktan sonra aldığınız Public IP adresini (örneğin `49.12.xx.xx`) araya yazarak şu 3 adresi doğrudan Coolify'da tanımlayabilirsiniz:
   * Yönetim Paneli: `https://coolify.49.12.xx.xx.sslip.io`
   * Frontend: `https://careercoach.49.12.xx.xx.sslip.io`
   * API Gateway: `https://api.49.12.xx.xx.sslip.io`

### Adım 1.2: Lokal Bilgisayarda SSH Anahtarı Üretme
Sunucuya şifresiz ve güvenli bağlanmak için SSH anahtar çifti oluşturun.

**PowerShell:**
```powershell
ssh-keygen -t ed25519 -C "careercoach-prod"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

**CMD (Komut İstemi):**
```cmd
ssh-keygen -t ed25519 -C "careercoach-prod"
type "%USERPROFILE%\.ssh\id_ed25519.pub"
```
*(Ekrana yazdırılan `ssh-ed25519 AAAA...` ile başlayan tek satırlık metni kopyalayın.)*

### Adım 1.3: Hetzner Cloud Hesabı Açma ve Sunucu (VPS) Oluşturma
1. [console.hetzner.cloud](https://console.hetzner.cloud/) adresinden hesap oluşturun ve kimlik/kart doğrulamasını tamamlayın.
2. **New Project** diyerek yeni proje açın ve **Add Server** butonuna tıklayın:
   * **Location:** `Falkenstein` veya `Nuremberg` (Almanya — düşük gecikme ve en uygun fiyat).
   * **Image (İşletim Sistemi):** `Ubuntu 24.04 LTS`.
   * **Type:** `Shared vCPU` → `Cost-Optimized` sekmesinden **`CX22`** seçin *(2 vCPU, 4 GB RAM, 40 GB NVMe SSD — ~€4.51/ay)*.
   * **Networking:** `Public IPv4` seçili olsun.
   * **SSH Keys:** Bir önceki adımda kopyaladığınız `.pub` anahtarını buraya yapıştırın.
   * **Name:** `careercoach-prod` yazıp **Create & Buy Now** butonuna tıklayın.
3. Oluşturulan sunucunun **Public IPv4** adresini (örnek: `49.12.xx.xx`) not alın.

### Adım 1.4: DNS / IP Yönlendirmesini Tamamlama
* **Seçenek C (`sslip.io`) Kullanıyorsanız:** Hiçbir DNS ayarı yapmanıza gerek yoktur; doğrudan Bölüm 2'ye geçin.
* **Seçenek A (DuckDNS) Kullanıyorsanız:** [duckdns.org](https://www.duckdns.org/) paneline girip `careercoachapp` satırındaki IP kutusuna Hetzner Public IPv4 adresinizi (`49.12.xx.xx`) yazın ve **update ip** butonuna basın.
* **Seçenek B (Cloudflare) Kullanıyorsanız:** Cloudflare DNS paneline aşağıdaki 3 adet `A` kaydını girin:
  * `A` | `@` | `49.12.xx.xx`
  * `A` | `api` | `49.12.xx.xx`
  * `A` | `coolify` | `49.12.xx.xx`

---

## 2. Lokalde Yapılacak Kod Değişiklikleri (LLM Prompt)

PyCharm içindeki AI asistanınıza (veya kullandığınız kodlama LLM'ine) aşağıdaki prompt'u doğrudan yapıştırarak projenizi prodüksiyon ortamına uyumlu hale getirin.

```text
Rolün: Kıdemli DevOps ve Mikroservis Mimarı.
Görev: Mevcut `CareerCoachAgenticAIApp` projemi Hetzner Cloud (Ubuntu VPS) üzerinde Docker Compose ile prodüksiyon ortamına (Coolify / Caddy Reverse Proxy arkasına) hazır hale getir.

Mevcut Mimari Bilgileri:
- 7 FastAPI mikroservisi: user-management (8001), personal-admin (8002), system-admin (8003), opportunity-service (8004), scout-agent (8005), relocation-agent (8006), application-coach-agent (8007).
- 1 Next.js 14 SPA frontend (3000).
- Ortak kütüphane: `services/shared/career_shared`.
- Her servis kendi bağımsız PostgreSQL veritabanına bağlanıyor.

Lütfen projede aşağıdaki 5 değişikliği eksiksiz ve çalışır şekilde oluştur/güncelle:

1. **Çoklu PostgreSQL Başlatma Scripti (`deploy/postgres/init-dbs.sql`):**
   - Tek bir PostgreSQL 16 konteyneri ayağa kalktığında `/docker-entrypoint-initdb.d/init-dbs.sql` üzerinden şu 7 veritabanını otomatik oluşturan SQL dosyasını yaz:
     `user_management_db`, `personal_admin_db`, `system_admin_db`, `opportunity_db`, `scout_agent_db`, `relocation_agent_db`, `coach_agent_db`.

2. **Reverse Proxy / API Gateway Yapılandırması (`deploy/caddy/Caddyfile`):**
   - Frontend'in prodüksiyonda 7 farklı porta değil, tek bir domain (`{$API_DOMAIN}`) üzerinden path bazlı yönlendirmeyle erişebilmesi için Caddyfile yaz:
     - `/api/users/*` -> `reverse_proxy user-management:8001` (servislerin mevcut route yapısına uygun olarak prefix strip veya yönlendirme kurallarını ayarla)
     - `/api/personal/*` -> `reverse_proxy personal-admin:8002`
     - `/api/system/*` -> `reverse_proxy system-admin:8003`
     - `/api/opportunities/*` -> `reverse_proxy opportunity-service:8004`
     - `/api/agents/scout/*` -> `reverse_proxy scout-agent:8005`
     - `/api/agents/relocation/*` -> `reverse_proxy relocation-agent:8006`
     - `/api/agents/coach/*` -> `reverse_proxy application-coach-agent:8007`
   - CORS başlıklarını ve preflight (`OPTIONS`) isteklerini destekleyecek şekilde yapılandır.

3. **Frontend API İstemci Güncellemesi (`frontend`):**
   - Frontend kod tabanında `localhost:8001` .. `localhost:8007` şeklinde sabit (hardcoded) tanımlanmış tüm servis URL'lerini bul.
   - Bunları ortam değişkenlerinden (`NEXT_PUBLIC_USER_API_URL`, `NEXT_PUBLIC_PERSONAL_API_URL`, `NEXT_PUBLIC_SYSTEM_API_URL`, `NEXT_PUBLIC_OPPORTUNITY_API_URL`, `NEXT_PUBLIC_SCOUT_API_URL`, `NEXT_PUBLIC_RELOCATION_API_URL`, `NEXT_PUBLIC_COACH_API_URL`) okuyacak şekilde güncelle. Lokal geliştirme için fallback olarak `http://localhost:800X` değerlerini koru.

4. **Yarım Kalan Ajan İşlemleri İçin Startup Recovery (`opportunity-service`):**
   - `opportunity-service` uygulamasının FastAPI `lifespan` (startup) event'ine bir temizlik fonksiyonu ekle: Uygulama yeniden başladığında `agent_runs` tablosunda status değeri `running` olan ve oluşturulma/güncellenme zamanı 10 dakikadan eski olan kayıtları otomatik olarak `failed` durumuna çeksin ve hata mesajına `"Process restarted during execution"` yazsın.

5. **Prodüksiyon Docker Compose ve Ortam Değişkenleri (`docker-compose.prod.yml` ve `.env.prod.example`):**
   - Tüm 7 mikroservisi, tek PostgreSQL 16 konteynerini (`init-dbs.sql` mount edilmiş ve kalıcı volume tanımlı), Next.js frontend'i (production build) ve Caddy servisini içeren `docker-compose.prod.yml` dosyasını yaz.
   - Tüm servisleri `career_internal_net` adlı izole bir Docker bridge ağına bağla.
   - PostgreSQL ve FastAPI servislerinin portlarını (`8001-8007`, `5432`) host makineye (`ports:`) AÇMA.
   - Servis içi haberleşme URL'lerini (`USER_SERVICE_URL=http://user-management:8001` vb.) iç ağ isimleriyle tanımla.
   - Tüm konteynerlere `restart: unless-stopped` ve sağlık kontrolleri (`healthcheck`) ekle.
```

---

## 3. GitHub Üzerinde Versiyonlama

Kod değişikliklerini tamamladıktan sonra yerel testinizi yapıp değişiklikleri güvenli şekilde GitHub'a aktarın.

### Adım 3.1: Hassas Dosyaların Kontrolü (`.gitignore`)
Proje kök dizinindeki `.gitignore` dosyasında aşağıdaki satırların bulunduğundan emin olun:
```gitignore
.env
.env.local
.env.prod
__pycache__/
.next/
postgres_data/
```

### Adım 3.2: Yeni Dal (Branch) Açma, Commit ve Push İşlemleri

**PowerShell:**
```powershell
git checkout -b feat/production-deployment
git status
git add .
git commit -m "chore: add production docker-compose, caddy gateway, multi-db init and startup recovery"
git push -u origin feat/production-deployment
```

**CMD (Komut İstemi):**
```cmd
git checkout -b feat/production-deployment
git status
git add .
git commit -m "chore: add production docker-compose, caddy gateway, multi-db init and startup recovery"
git push -u origin feat/production-deployment
```

### Adım 3.3: Pull Request ve Merge
1. GitHub üzerinde `CareerCoachAgenticAIApp` reponuza gidin.
2. **Compare & pull request** butonuna tıklayın.
3. Değişiklikleri kontrol edip `main` dalına **Merge pull request** yapın.

> **Önemli Not:** Değişiklikleri GitHub'da `main` dalına birleştirmek tek başına canlıya çıkış için yeterli değildir. İlk seferde aşağıdaki **Bölüm 4** adımlarını manuel olarak tamamlamanız gerekir.

---

## 4. Sunucu Kurulumu ve İlk Canlıya Çıkış (Manuel Zorunlu Adımlar)

### Adım 4.1: Hetzner Sunucusuna SSH Bağlantısı
Lokal bilgisayarınızdan sunucunuza bağlanın (`49.12.xx.xx` yerine kendi sunucu IP adresinizi yazın):

**PowerShell:**
```powershell
ssh root@49.12.xx.xx
```

**CMD (Komut İstemi):**
```cmd
ssh root@49.12.xx.xx
```

### Adım 4.2: Sunucu Güncelleme ve Güvenlik Duvarı (UFW)
*(Aşağıdaki komutlar uzak Ubuntu sunucusunun SSH terminalinde çalıştırılır.)*
```bash
apt update && apt upgrade -y
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### Adım 4.3: Coolify Kurulumu
*(Uzak Ubuntu sunucusunun SSH terminalinde çalıştırılır; kurulum yaklaşık 2-3 dakika sürer.)*
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```
1. Kurulum bittiğinde tarayıcınızdan `http://49.12.xx.xx:8000` adresine girin ve ilk yönetici (admin) hesabınızı oluşturun.
2. Coolify arayüzünde **Settings** menüsüne girip **Instance Domain** alanına seçtiğiniz alan adını yazın ve kaydedin:
   * **Seçenek C (`sslip.io`):** `https://coolify.49.12.xx.xx.sslip.io`
   * **Seçenek A (DuckDNS):** `https://coolify.careercoachapp.duckdns.org`

### Adım 4.4: GitHub Repoyu Coolify'a Bağlama
1. Coolify panelinde **Sources → Add** yolunu izleyerek **GitHub App** oluşturun.
2. Yönlendirilen GitHub ekranında yalnızca `CareerCoachAgenticAIApp` reposuna erişim izni verin.

### Adım 4.5: Projeyi ve Docker Compose Yapısını Tanımlama
1. Coolify'da **Projects → New Project** (`CareerCoachProd`) oluşturun.
2. **+ New Resource → Docker Compose** seçeneğine tıklayın.
3. Bağladığınız `CareerCoachAgenticAIApp` reposunu ve `main` dalını seçin.
4. **Docker Compose Location** alanına `/docker-compose.prod.yml` yazın.
5. **Domains** bölümünde seçtiğiniz yönteme göre alan adlarını tanımlayın:
   * **Seçenek C (`sslip.io`) Kullanıyorsanız:**
     * `frontend`: `https://careercoach.49.12.xx.xx.sslip.io`
     * `caddy`: `https://api.49.12.xx.xx.sslip.io`
   * **Seçenek A (DuckDNS) Kullanıyorsanız:**
     * `frontend`: `https://careercoachapp.duckdns.org`
     * `caddy`: `https://api.careercoachapp.duckdns.org`

### Adım 4.6: Ortam Değişkenleri (Environment Variables) ve İlk Deploy
1. Coolify'daki **Environment Variables** sekmesine `.env.prod.example` dosyanızdaki tüm değişkenleri ve gizli anahtarları (`JWT_SECRET`, `INTERNAL_API_KEY`, `FERNET_KEY`, `POSTGRES_PASSWORD` vb.) girin *(Örnekler `sslip.io` formatındadır; kendi IP veya domaininize göre güncelleyin)*:
   * `NEXT_PUBLIC_USER_API_URL=https://api.49.12.xx.xx.sslip.io/api/users`
   * `NEXT_PUBLIC_PERSONAL_API_URL=https://api.49.12.xx.xx.sslip.io/api/personal`
   * `NEXT_PUBLIC_SYSTEM_API_URL=https://api.49.12.xx.xx.sslip.io/api/system`
   * `NEXT_PUBLIC_OPPORTUNITY_API_URL=https://api.49.12.xx.xx.sslip.io/api/opportunities`
   * `NEXT_PUBLIC_SCOUT_API_URL=https://api.49.12.xx.xx.sslip.io/api/agents/scout`
   * `NEXT_PUBLIC_RELOCATION_API_URL=https://api.49.12.xx.xx.sslip.io/api/agents/relocation`
   * `NEXT_PUBLIC_COACH_API_URL=https://api.49.12.xx.xx.sslip.io/api/agents/coach`
2. Sağ üstteki **Deploy** butonuna basın.
   *(PostgreSQL konteyneri ilk kez bu adımda ayağa kalktığı için `init-dbs.sql` otomatik çalışır ve 7 veritabanını oluşturur.)*
3. Tüm konteynerler `Running (Healthy)` durumuna geçtiğinde `https://careercoach.49.12.xx.xx.sslip.io` adresinden uygulamanıza erişebilirsiniz.

---

## 5. İlk Kurulum Sonrası Güncellemeler (Otomatik CI/CD Süreci)

**Bölüm 4** bir kez tamamlandıktan sonra uygulamanızda yapacağınız kod güncellemeleri için sunucuya tekrar bağlanmanıza gerek yoktur:

1. **Standart Kod Güncellemeleri (Otomatik):**
   * Coolify'da **Auto Deploy** özelliği varsayılan olarak aktiftir.
   * Lokalinizde yaptığınız değişiklikleri GitHub'da **`main` dalına push veya merge ettiğiniz anda** GitHub, Coolify'a webhook sinyali gönderir; Coolify değişen servislerin imajını otomatik yeniden derler ve sıfır kesintiyle (zero-downtime) canlıya alır.
2. **İstisnai Durumlar (Manuel Müdahale Gerektiren Değişiklikler):**
   * **Yeni `.env` Değişkeni Eklendiyse:** Önce Coolify panelindeki **Environment Variables** sekmesine yeni değişkeni ekleyin, ardından sağ üstteki **Redeploy** butonuna basın.
   * **Yeni Veritabanı Eklendiyse:** `init-dbs.sql` yalnızca PostgreSQL ilk kez sıfırdan yaratılırken çalışır. Mevcut veritabanına sonradan yeni bir DB eklemek isterseniz Coolify'da PostgreSQL servisinin **Terminal** sekmesinden `psql -U postgres -c "CREATE DATABASE yeni_db;"` komutunu çalıştırmanız gerekir.

---

## 6. Canlıya Çıktıktan Sonra Kontrol Listesi

* [ ] **İlk Admin Kullanıcısı:** `user-management` üzerinden kayıt olun, veritabanından veya seed script ile hesabınıza `system_admin` rolü atayın.
* [ ] **LLM Sağlayıcıları:** `system-admin` arayüzüne giriş yaparak Gemini / Groq / OpenAI API anahtarlarınızı ekleyin ve ajan öncelik sıralamalarını aktif edin.
* [ ] **Otomatik Yedekleme:** Hetzner Console üzerinden sunucunuz için **Backups** özelliğini (~€0.90/ay) aktif ederek 7 PostgreSQL veritabanının her gece otomatik imaj yedeğinin alınmasını sağlayın.
* [ ] **SSL Doğrulaması:** Tarayıcıdan uygulama adresinizi açtığınızda adres çubuğunda kilit (HTTPS) simgesinin aktif olduğunu kontrol edin.