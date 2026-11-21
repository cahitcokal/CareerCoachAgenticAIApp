# CareerCoachAgenticAIApp — Prodüksiyon Dağıtım (Deployment) Rehberi

Bu doküman, **CareerCoachAgenticAIApp** mikroservis mimarisinin **Hetzner Cloud (Ubuntu VPS)** ve **Coolify (PaaS)** kullanılarak canlı ortama (production) alınması için gereken altyapı hazırlığı, kod düzenleme, GitHub versiyonlama ve sunucu kurulum adımlarını içerir.

## İçindekiler

1. [Altyapı Hazırlığı ve Sunucu Kurulumu](#1-altyapı-hazırlığı-ve-sunucu-kurulumu)
2. [Lokalde Yapılacak Kod Değişiklikleri (LLM Prompt)](#2-lokalde-yapılacak-kod-değişiklikleri-llm-prompt)
3. [GitHub Üzerinde Versiyonlama](#3-github-üzerinde-versiyonlama)
4. [Sunucu Kurulumu ve Canlıya Çıkış (Coolify)](#4-sunucu-kurulumu-ve-canlıya-çıkış-coolify)
5. [Canlıya Çıktıktan Sonra Kontrol Listesi](#5-canlıya-çıktıktan-sonra-kontrol-listesi)

---

## 1. Altyapı Hazırlığı ve Sunucu Kurulumu

Canlıya çıkış için yalnızca **1 adet Hetzner Cloud Sunucusu (VPS)** ve alan adı için **ücretsiz DuckDNS** (veya ücretli özel alan adı) yeterlidir.

### Adım 1.1: Alan Adı Seçimi (Ücretsiz DuckDNS veya Ücretli Domain)

#### Seçenek A (Önerilen — Ücretsiz): DuckDNS ile Ücretsiz Subdomain Alma
Hiçbir ücret ödemeden ücretsiz SSL (HTTPS) alabileceğiniz bir alan adı oluşturmak için:
1. [duckdns.org](https://www.duckdns.org/) adresine gidin ve **GitHub** (veya Google) hesabınızla giriş yapın.
2. **domains** bölümüne istediğiniz alt alan adını yazıp **add domain** butonuna tıklayın (örnek: `careercoachapp` → adresiniz `careercoachapp.duckdns.org` olur).
3. **Önemli Bilgi (Wildcard Desteği):** DuckDNS, oluşturduğunuz ana alt alan adının tüm alt uzantılarını (`*.careercoachapp.duckdns.org`) otomatik olarak aynı IP'ye yönlendirir. Bu sayede ekstra kayıt açmadan şu 3 adresi doğrudan kullanabilirsiniz:
   * Frontend: `https://careercoachapp.duckdns.org`
   * API Gateway: `https://api.careercoachapp.duckdns.org`
   * Yönetim Paneli: `https://coolify.careercoachapp.duckdns.org`
4. Sunucuyu oluşturduktan sonra Hetzner'in vereceği **Public IPv4** adresini DuckDNS sayfasındaki **current ip** kutucuğuna yazıp **update ip** butonuna basmanız yeterlidir.

#### Seçenek B (Alternatif — Ücretli): Özel Alan Adı Satın Alma
* **Cloudflare Registrar** (~$10–$12/yıl) üzerinden özel bir domain satın alabilir ve DNS kayıtlarını Cloudflare üzerinden yönetebilirsiniz.

---

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

---

### Adım 1.3: Hetzner Cloud Hesabı Açma ve Sunucu (VPS) Oluşturma

1. [console.hetzner.cloud](https://console.hetzner.cloud/) adresinden hesap oluşturun ve kimlik/kart doğrulamasını tamamlayın.
2. **New Project** diyerek yeni proje açın ve **Add Server** butonuna tıklayın:
   * **Location:** `Falkenstein` veya `Nuremberg` (Almanya — düşük gecikme ve en uygun fiyat).
   * **Image (İşletim Sistemi):** `Ubuntu 24.04 LTS`.
   * **Type:** `Shared vCPU` → `Cost-Optimized` sekmesinden **`CX22`** seçin *(2 vCPU, 4 GB RAM, 40 GB NVMe SSD — \~€4.51/ay)*.
   * **Networking:** `Public IPv4` seçili olsun.
   * **SSH Keys:** Bir önceki adımda kopyaladığınız `.pub` anahtarını buraya yapıştırın.
   * **Name:** `careercoach-prod` yazıp **Create & Buy Now** butonuna tıklayın.
3. Oluşturulan sunucunun **Public IPv4** adresini (örnek: `49.12.xx.xx`) not alın.

---

### Adım 1.4: DNS / IP Yönlendirmesini Tamamlama

* **DuckDNS (Seçenek A) Kullanıyorsanız:**
  1. [duckdns.org](https://www.duckdns.org/) paneline geri dönün.
  2. Oluşturduğunuz `careercoachapp` satırındaki IP kutusuna Hetzner'in verdiği Public IPv4 adresini (`49.12.xx.xx`) yazın ve **update ip** butonuna tıklayın.
  3. Birkaç dakika içinde `careercoachapp.duckdns.org`, `api.careercoachapp.duckdns.org` ve `coolify.careercoachapp.duckdns.org` adreslerinin tamamı sunucunuza yönlenmiş olacaktır.

* **Ücretli Domain + Cloudflare (Seçenek B) Kullanıyorsanız:**
  Cloudflare DNS paneline aşağıdaki 3 adet `A` kaydını girin:
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

Proje kök dizinindeki `.gitignore` dosyasında aşağıdaki satırların bulunduğundan emin olun (hiçbir gizli anahtar GitHub'a gitmemelidir):

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

---

## 4. Sunucu Kurulumu ve Canlıya Çıkış (Coolify)

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
2. Coolify arayüzünde **Settings** menüsüne girip **Instance Domain** alanına DuckDNS adresinizi (`https://coolify.careercoachapp.duckdns.org`) yazın ve kaydedin. Coolify otomatik olarak ücretsiz Let's Encrypt SSL sertifikası oluşturacaktır.

### Adım 4.4: GitHub Repoyu Coolify'a Bağlama

1. Coolify panelinde **Sources → Add** yolunu izleyerek **GitHub App** oluşturun.
2. Yönlendirilen GitHub ekranında yalnızca `CareerCoachAgenticAIApp` reposuna erişim izni verin. *(Bu sayede private repo olsa dahi otomatik çekilir ve her push işleminde otomatik deploy tetiklenir.)*

### Adım 4.5: Projeyi ve Docker Compose Yapısını Deploy Etme

1. Coolify'da **Projects → New Project** (`CareerCoachProd`) oluşturun.
2. **+ New Resource → Docker Compose** seçeneğine tıklayın.
3. Bağladığınız `CareerCoachAgenticAIApp` reposunu ve `main` dalını seçin.
4. **Docker Compose Location** alanına `/docker-compose.prod.yml` yazın.
5. **Domains** bölümünde DuckDNS alan adlarınızı tanımlayın:
   * `frontend` servisi için: `https://careercoachapp.duckdns.org`
   * `caddy` (API Gateway) servisi için: `https://api.careercoachapp.duckdns.org`

### Adım 4.6: Ortam Değişkenleri (Environment Variables) ve Başlatma

1. Coolify'daki **Environment Variables** sekmesine `.env.prod.example` dosyanızdaki tüm değişkenleri ve gizli anahtarları girin. DuckDNS adreslerinize göre API URL'lerini şu şekilde tanımlayın:
   * `NEXT_PUBLIC_USER_API_URL=https://api.careercoachapp.duckdns.org/api/users`
   * `NEXT_PUBLIC_PERSONAL_API_URL=https://api.careercoachapp.duckdns.org/api/personal`
   * `NEXT_PUBLIC_SYSTEM_API_URL=https://api.careercoachapp.duckdns.org/api/system`
   * `NEXT_PUBLIC_OPPORTUNITY_API_URL=https://api.careercoachapp.duckdns.org/api/opportunities`
   * `NEXT_PUBLIC_SCOUT_API_URL=https://api.careercoachapp.duckdns.org/api/agents/scout`
   * `NEXT_PUBLIC_RELOCATION_API_URL=https://api.careercoachapp.duckdns.org/api/agents/relocation`
   * `NEXT_PUBLIC_COACH_API_URL=https://api.careercoachapp.duckdns.org/api/agents/coach`
2. Sağ üstteki **Deploy** butonuna basın.
3. Tüm konteynerler `Running (Healthy)` durumuna geçtiğinde `https://careercoachapp.duckdns.org` adresinden uygulamanıza HTTPS üzerinden güvenle erişebilirsiniz.

---

## 5. Canlıya Çıktıktan Sonra Kontrol Listesi

* [ ] **İlk Admin Kullanıcısı:** `user-management` üzerinden kayıt olun, veritabanından veya seed script ile hesabınıza `system_admin` rolü atayın.
* [ ] **LLM Sağlayıcıları:** `system-admin` arayüzüne giriş yaparak Gemini / Groq / OpenAI API anahtarlarınızı ekleyin ve ajan öncelik sıralamalarını aktif edin.
* [ ] **Otomatik Yedekleme:** Hetzner Console üzerinden sunucunuz için **Backups** özelliğini (\~€0.90/ay) aktif ederek 7 PostgreSQL veritabanının her gece otomatik imaj yedeğinin alınmasını sağlayın.
* [ ] **SSL Doğrulaması:** Tarayıcıdan `https://careercoachapp.duckdns.org` adresini açtığınızda adres çubuğunda kilit (HTTPS) simgesinin aktif olduğunu kontrol edin *(Not: DuckDNS üzerinde aynı saat içinde çok fazla subdomain denemesi yaparsanız Let's Encrypt hız sınırına takılmamak için sadece yukarıdaki 3 subdomain'i kullanın).*