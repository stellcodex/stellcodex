WEB SİTE ARAYÜZÜ (UI/UX) — V1+V2 KAPSAMI (BAĞLAYICI)

ARAYÜZ PRENSİPLERİ (DEĞİŞTİRİLEMEZ)

Ürün “CAD değildir”; UI hiçbir ekranda geometri düzenleme (edit) vaadi vermez.

Her ekran “yükle → önizle → paylaş → sunum/yorum” aksına hizmet eder.

Her işlemde görünür durum: (a) işlem adı (b) ilerleme (c) hata kodu/error_id (d) geri deneme.

Yetkisiz durumda: içerik sızdırma yok; “var/yok” bile belli etmeyecek şekilde davranış (RBAC fail-safe).

Mobil uyumluluk zorunlu: viewer dahil temel iş akışları çalışır.

WEB BİLGİ MİMARİSİ (SAYFA HARİTASI)
2.1) Public (girişsiz)

/ Ana sayfa (ürün tanıtımı + CTA: giriş/kayıt)

/pricing (varsa) [ASKIDA — net paket/plan yoksa bu sayfa pasif]

/features Özellikler (2D/3D viewer, sunum, paylaşım, community)

/community Community vitrin (girişsiz sadece “public” içerikler)

/status Sistem durumu (servis health özet; detay log yok)

/docs Yardım / kullanım rehberi (bağlayıcı değil, türev doküman)

/privacy, /terms

2.2) Auth

/auth/login

/auth/register [ASKIDA — kayıt açık mı, davet/approval mı?]

/auth/forgot, /auth/reset

2.3) Kullanıcı (girişli)

/app Dashboard (özet)

/app/library Kütüphane (dosyalar, klasörler, etiketler)

/app/upload Yükleme (drag-drop + format doğrulama + queue)

/app/file/[id] Dosya detay (metadata, versiyonlar, preview)

/app/viewer-2d/[id] 2D Viewer

/app/viewer-3d/[id] 3D Viewer

/app/presentations Sunumlar listesi

/app/presentations/[id] Sunum oynatıcı (adımlar + anotasyon)

/app/shares Paylaşımlar (giden/gelen)

/app/notifications Bildirimler

/app/account Profil/ayarlar

2.4) Admin (V2, girişli + RBAC)

/admin Admin dashboard (sistem özeti)

/admin/users kullanıcılar

/admin/roles roller & yetkiler

/admin/approvals approval_requests kuyruğu

/admin/audit audit log görüntüleme (PII maskeli)

/admin/system servis/queue/storage durumları

/admin/content community moderation (gerekirse)

ANA EKRANLAR VE KULLANICIYA SUNULACAK FONKSİYONLAR
3.1) Ana Sayfa (/)
Kullanıcıya sunulanlar:

“Upload & Preview” anlatımı (2D/3D)

Örnek akış: Upload → Viewer → Share → Presentation

Community vitrin teaser

Sistem durumu linki

3.2) Dashboard (/app)

Son açılan dosyalar

Devam eden işleme kuyruğu (conversion jobs)

Son paylaşımlar

Bildirimler (approval gerektiren olaylar dahil)

3.3) Library (/app/library)
Kullanıcının yapabilecekleri:

Dosya listeleme / arama / filtreleme (etiket, format, tarih)

Klasörleme (opsiyonel) [ASKIDA — klasör modeli net değilse etiketle sınırlı]

Çoklu seçim: indir / paylaş / sil (yetkiye bağlı)

Her dosya kartında: thumbnail + format + boyut + durum

3.4) Upload (/app/upload)

Drag & drop / file picker

Anında doğrulama: uzantı, boyut limiti, virüs taraması status

İşlem kuyruğuna alma ve progress

Hata yönetimi: kullanıcıya “neden reddedildi” (güvenli mesaj)

3.5) File Detail (/app/file/[id])

Metadata: ad, format, boyut, upload tarihi, owner, etiketler

Önizleme: 2D/3D viewer linkleri (format uygunsa)

Paylaşım: SCX-ID ile link üretme, izin seviyesi seçme (view/comment/download)

Versiyonlar: aynı dosyanın yeni sürümü yüklenirse versiyon zinciri

Audit: kullanıcı kendi işlem geçmişini görür (kısıtlı)

3.6) 2D Viewer (/app/viewer-2d/[id])
Amaç: hızlı pan/zoom, ölçüm, anotasyon, çıktı.

Pan/Zoom, sayfa/katman gezinme (varsa)

Ölçüm araçları (pixel/ölçek) [ASKIDA — ölçek kaynağı net değilse “yaklaşık/ölçeksiz” uyarısı]

Anotasyon: pin, çizim üstü not, yorum thread’i

Export: anotasyonlu görüntü/PDF (yetkiye bağlı)

DXF native okuma:

Parser PIN: ezdxf==1.4.3 (bağlayıcı)

Not: DXF render stratejisi kilitlidir: DXF → parse (ezdxf) → scene → SVG render (tek çıktı).

3.7) 3D Viewer (/app/viewer-3d/[id])
Amaç: gör, incele, sun, paylaş (edit yok).

Orbit/pan/zoom

View modes: shaded / wireframe / hidden-line (V1 minimum set)

Section cut / clipping (V2)

Explode view (V2)

Model tree (assembly/part list) (V2)

Malzeme/ışık kontrolleri (V1 basic)

Performans: büyük modelde LOD/mesh optimizasyon (pipeline)

Not: Web tarafı Three.js + R3F “ana”dır (bağlayıcı).

3.8) Presentations (/app/presentations + /app/presentations/[id])
Amaç: “Composer benzeri” sunum akışı.

Adım listesi (step 1..n)

Her adımda kamera pozisyonu + görünürlük seti + anotasyonlar

Paylaşılabilir sunum linki (RBAC ile)

Yorumlar: adım bazlı thread

3.9) Shares (/app/shares)

Paylaşım oluşturma: SCX-ID, link, süre (opsiyon), izin seviyesi

Gelen paylaşımlar: kimden, ne zaman, izinler

İptal/yenileme (yetkiye bağlı)

3.10) Community (/community ve /app/community opsiyon)

Public vitrin: sadece “public” işaretli içerikler

Girişli kullanıcı: içerik yükleyebilir/ paylaşabilir [ASKIDA — community içerik modeli ve moderasyon kuralları net değilse salt vitrin]

ADMIN ARAYÜZÜ (V2) — NELER YAPILACAK

Admin giriş: RBAC zorunlu

Kullanıcı yönetimi: oluşturma/askıya alma/rol atama (approval gerekli işlemler tanımlanacak)

RBAC yönetimi: permission key set “tek kaynak JSON”

Approval ekranı: kritik işlemler onay kuyruğu

Audit log: filtreleme + PII redaction (mask)

Sistem durumu: queue, worker, storage, error rate, uptime (gösterim; müdahale “yetkili action” ile ve audit’li)

UI BİLEŞEN STANDARTLARI

Sol panel / sağ panel düzeni (viewer’larda):

Sol: dosya listesi + model tree / sayfa listesi

Sağ: properties + anotasyonlar + paylaşım paneli

Tüm kritik aksiyonlarda “confirm + reason” (admin’de zorunlu)

Global arama: library üstünden

Bildirim merkezi: job tamamlandı, paylaşım alındı, approval bekliyor

“MERKEZDE TAM YÖNETİMLİ AI” İÇİN UI BAĞLAYICI KURALI

Merkez AI (Codex dahil) yeni UI ekranı/route eklerken bu sayfa haritasıyla çelişemez.

Yeni ekran ihtiyacı doğarsa: önce bu dosyaya (README_MASTER.md) değişiklik önerisi + gerekçe + etkiler yazılmadan kod eklenmez.

RBAC olmayan hiçbir admin UI route deploy edilmez.

[ASKIDA — NET VE BAĞLAYICI GİRDİ BEKLENİYOR] (UI’yi kilitlemek için kalan netleştirmeler)

Kayıt akışı: açık kayıt mı, davet mi, admin onayı mı?

“Klasör” var mı, yoksa sadece etiket mi?

Community içerik modeli (public/private, moderasyon, telif)

RBAC Validation

Run: cd /var/www/stellcodex/frontend && npm run gen:access
Run: cd /var/www/stellcodex/frontend && npm run rbac:validate
Run: cd /var/www/stellcodex/frontend && npm run rbac:validate-routes
