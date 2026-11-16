# User Guide / Kullanıcı Rehberi

## Türkçe

### Giriş ve kayıt

- `/register` ile hesap oluşturun; `/login` ile giriş yapın. Şifrenizi unuttuysanız `/forgot-password` sayfasını kullanın (geliştirmede sıfırlama token'ı sunucu loglarına yazılır).
- Çıkış yapmak için sağ üstteki "Çıkış" düğmesini kullanın; JWT localStorage'dan silinir.

### Panel (Dashboard)

- **İş İlanı Ara**: profil seçin, serbest metin sorgu ve lokasyon girin; "Aramayı Başlat" scout ajanını asenkron tetikler. Bir arama sürerken form devre dışıdır (409).
- **URL Analiz Et**: tek bir iş ilanı URL'si yapıştırıp scout'a analiz ettirin.
- Fırsat kartlarında şirket, lokasyon, eşleşme skoru ve bağlı profil görünür. Durum sekmeleri (new/active/archived/applied/rejected/interview) ve profil/ülke/şirket/min-skor filtreleri ile listeleyebilirsiniz.
- Her fırsatta "Rapor Oluştur" (relocation ajanı) ve "Adım Oluştur" (başvuru koçu ajanı) düğmeleri vardır; ajanlar çalışırken durum 5 saniyede bir yenilenir ve "running" görünür.
- Pasif veya silinmiş bir profile ait fırsatlar listelerde görünmez.

### Kişisel Yönetim (/admin)

- Dil tercihinizi seçin — sistem varsayılanını ezer.
- Sınırsız profil oluşturun/güncelleyin. Silme soft-delete'tir; silinen profiller "Silinmiş" rozetiyle listede kalır ve "Geri Yükle" ile aktifleşir.
- Hedef ülkeler, hedef roller ve kariyer platformları için sınırsız CRUD.

### Sistem Yönetimi (/system-admin, yalnızca sistem admin)

- **Diller**: varsayılan dili seçin, dilleri etkin/pasif yapın (en az biri etkin kalmalı).
- **Sağlayıcılar**: her LLM için base URL, API key (şifreli saklanır) ve etkinlik durumu.
- **Modeller**: her provider için model listesi ve öncelik sırası.
- **Ajan Ayarları**: ajan bazlı enable/disable, provider sıralaması, max deneme, retry gecikmesi ve max sonuç sayısı.
- **Kullanıcılar**: kullanıcıları listeleyin, sistem admin rolü verin/alın.

## English

### Login & registration

- Create an account at `/register`, sign in at `/login`. Use `/forgot-password` if you forgot your password (in development the reset token is written to server logs).
- Log out via the "Log Out" button; the JWT is removed from localStorage.

### Dashboard

- **Search Jobs**: pick a profile, enter a free-text query and locations, then "Start Search" triggers the scout agent asynchronously. The form is disabled while a search runs (409).
- **Analyze URL**: paste a single job posting URL for the scout to analyze.
- Opportunity cards show company, location, match score and the linked profile. Filter by status tabs (new/active/archived/applied/rejected/interview), profile, country, company and minimum score.
- Each card has "Generate Report" (relocation agent) and "Generate Steps" (application coach); agent state refreshes every 5 seconds and shows "running".
- Opportunities of inactive or deleted profiles are hidden from lists.

### Personal Admin (/admin)

- Choose your language preference — it overrides the system default.
- Create/edit unlimited profiles. Deletion is a soft delete; deleted profiles remain listed with a "Deleted" badge and can be restored.
- Unlimited CRUD for target countries, target roles and career platforms.

### System Admin (/system-admin, system admins only)

- **Languages**: pick the default, enable/disable languages (at least one must stay enabled).
- **Providers**: base URL, API key (stored encrypted) and enabled state per LLM.
- **Models**: per-provider model list and priority order.
- **Agent Settings**: per-agent enable/disable, provider ordering, max attempts, retry delay and max results.
- **Users**: list users and grant/revoke the system-admin role.
