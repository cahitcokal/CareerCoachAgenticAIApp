# Proje Çalışma Kuralları / Project Working Instructions

## Türkçe

Bu depoda davranış değiştiren her görevde dokümantasyon etkisini değerlendirin.

- Ekran, form, düğme, iş akışı, doğrulama veya kullanıcıya görünen hata değişirse `docs/user_guide.md` dosyasının ilgili bölümünü aynı değişiklikte güncelleyin.
- LLM, audit, test veya URL arama davranışı değişirse ilgili `docs/*.md` belgesini de güncelleyin.
- `README.md` ve `troubleshooting.md` adları (büyük/küçük harften bağımsız) iki dillilik şartından muaftır. Diğer proje Markdown belgeleri aynı dosyada `## Türkçe` ve `## English` bölümleri içermeli; iki bölüm eşdeğer bilgi vermelidir. Bağımlılık, sanal ortam, Git, IDE ve üretilmiş rapor dosyalarını değiştirmeyin.
- Menü/düğme adlarını, varsayılanları ve kısıtları koddan doğrulayın. Planlanan özelliği uygulanmış gibi yazmayın. Gözden geçirme tarihini gerçek inceleme tarihine göre güncelleyin.
- Test sayısı/kapsamı yazacaksanız çalıştırılan raporu kaynak alın; yeniden ölçmeden eski sayıları yeni sonuç gibi sunmayın.
- `.venv\Scripts\python.exe scripts/check_docs.py` çalıştırın. Bu kontrol dil başlıklarını ve yerel dosya bağlantılarını denetler; çevirinin doğruluğunu veya belgelerin kodla uyumunu otomatik doğrulamaz.
- Kullanıcı akışını değiştirmeyen bir görevde rehber değişikliği gerekmeyebilir; dokümantasyon etkisini sonuçta kısaca belirtin. Sırf tarih yenilemek için içerik değiştirmeyin.

## English

Assess documentation impact for every task that changes behavior in this repository.

- If a screen, form, button, workflow, validation or user-visible error changes, update the relevant section of `docs/user_guide.md` in the same change.
- If LLM, audit, testing or URL-search behavior changes, update the corresponding `docs/*.md` document too.
- Files named `README.md` or `troubleshooting.md` (case-insensitive) are exempt from bilingual content. Other project Markdown documents must contain `## Türkçe` and `## English` sections in the same file with equivalent information. Do not modify dependency, virtual-environment, Git, IDE or generated-report files.
- Verify menu/button names, defaults and limitations against code. Do not document planned features as implemented. Use the actual review date when updating review metadata.
- When documenting test counts or coverage, use an executed report; do not present historical figures as a fresh measurement.
- Run `.venv\Scripts\python.exe scripts/check_docs.py`. This checks language headings and local file links; it cannot automatically verify translation quality or alignment with code.
- Tasks that do not change user workflows may not require guide edits; briefly state their documentation impact in the outcome. Do not edit content merely to refresh a date.
