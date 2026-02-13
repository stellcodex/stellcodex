# STELLCODEX — MASTER TEKNİK VE ÜRÜN ÇERÇEVESİ (V1.3)
> Bu belge STELLCODEX projesinin değiştirilemez ana sözleşmesidir.
> Çelişki durumunda bu belge tek kaynaktır. Varsayım yapılmaz.
> STELLCODEX bir CAD yazılımı değildir (geometri düzenleme yoktur).

## 0) BAĞLAYICI KARARLAR (Kilitli)
- Ürün: Read-only 2D/3D görüntüleme + inceleme + not + yetkili paylaşım.
- Geometri düzenleme / parametrik edit: YOK.
- Backend: FastAPI (Python)
- DB: PostgreSQL
- Storage: MinIO (S3 uyumlu)
- Queue: Redis + RQ (Celery/RabbitMQ KULLANILMAZ)
- Cache: Redis (oturum + geçici veriler)
- 3D CAD çekirdek: OpenCASCADE
- Parametrik/özel CAD import: FreeCAD headless
- Mesh import/unify: Assimp
- Mesh kalite/analiz: CGAL + MeshLab (gerektiğinde)
- Render: Blender headless (Eevee/Cycles preset)
- Viewer: Three.js + @react-three/fiber
- Sunum formatı: GLTF/GLB tek hedef
- 2D: DXF zorunlu; DWG yok.
- Performans: Dosya yüklemeden sonra kullanıcı 10 sn içinde ekranda “görüntü” görür (skeleton/preview dahil).

## 1) Ürün Tanımı ve Sınırlar
STELLCODEX; 2D çizim, 3D model ve render çıktılarının:
- anlaşılır şekilde sunulması,
- ölçüm ve not alınması (kapsamı ayrı maddelerde),
- yetkili paylaşım ile review yapılması
için tasarlanmıştır.

Kesin sınırlar:
- Geometri değişikliği yok.
- DWG desteği yok.
- Kapalı kaynak çekirdek yok.

## 2) Çekirdekler ve Sürüm Sabitliği (Pinned)
- OpenCASCADE: 7.9.3
- FreeCAD headless: 1.0.2
- CGAL: 6.1.1
- MeshLab: 2025.07
- Blender: 4.5.6 LTS
- Assimp: 6.0.4

Sürüm değişimi yalnızca “test planı + regresyon raporu” ile yapılır.

## 3) Dosya Pipeline — Kaynak → GLB
Amaç: Her dosya türü normalize edilerek GLB üretir.

### 3.1 3D Parametrik / B-Rep
- STEP/IGES/BREP → OpenCASCADE → GLB
- FCStd/IFC vb. → FreeCAD headless → mesh/ara format → Assimp/normalize → GLB

### 3.2 Mesh
- STL/OBJ/PLY/OFF/3MF/AMF/DAE vb. → Assimp → GLB
- Gerektiğinde MeshLab/CGAL: delik doldurma, self-intersection tespiti, normal düzeltme.

### 3.3 2D (Bağlayıcı)
- DXF: Native 2D Viewer (vektörel gösterim)
- PDF/PNG/JPG: direkt görüntüleme
- DWG: desteklenmez

Not (kapsam):
- DXF TEXT/DIM/MTEXT desteği kademeli olabilir; ancak gösterim yolu raster’a çevrilmez (native kalır).

## 4) Asenkron İş Modeli (Queue)
- Ağır işler API içinde çalışmaz: dönüşüm, render, thumbnail, metadata ağır işleri queue üzerinden yürür.
- Queue motoru: RQ (Redis)
- İş durumları: queued → running → succeeded/failed
- Retry: max 3; kalıcı fail: failed registry + admin alarm

## 5) Kimlik, Yetki ve Paylaşım
- Varsayılan gizlilik: PRIVATE (yükleyen + admin + davetliler)
- Paylaşım linki: süreli / yetkili / iptal edilebilir
- Yetki seviyeleri: view / comment / download (download opsiyonel kapatılabilir)

## 6) SCX-ID (Kilitli Format)
- SCX-ID formatı: UUID v4 tabanlı, `scx_` prefix’li string.
- Örnek: `scx_550e8400-e29b-41d4-a716-446655440000`
- DB’de birincil anahtar olarak UUID tutulabilir; UI/API’da `scx_...` olarak gösterilir.

## 7) Anonymous Upload Lifecycle (Kilitli)
- Anonymous upload retention: 24 saat.
- Kullanıcı bu süre içinde login olursa: “sahiplik devri” yapılır (dosya, login olan kullanıcıya bağlanır).
- 24 saat sonunda ve sahiplik devri yoksa: orijinal dosya + türev çıktılar (GLB/thumbnail/render) otomatik silinir.
- Silme işlemi queue üzerinden yürür ve audit log’a yazılır.

## 8) UI/UX — Modlar ve Akış
Modlar:
- 3D Model
- 2D Model (DXF)
- Patlatma
- Render

Kurallar:
- Yükleme sonrası otomatik doğru moda geçiş.
- Maksimum sahne alanı prensibi.
- Mobilde kalite korunur; ileri ayarlar azaltılabilir (işlev kaybı olmadan).

## 9) Render Sistemi (Preset’ler Kilitli)
- Blender headless.
- Eevee hızlı önizleme; Cycles yüksek kalite.
- Kullanıcı serbest ayar görmez; preset seçer.

Preset listesi (bağlayıcı):
1) preview_low
2) studio_soft
3) technical_white
4) exploded_shadow

Not: Preset parametreleri (çözünürlük, engine, sampling, light rig) “Render Preset Spec” dosyasında tek kaynakta tanımlanır ve backend/worker aynı kaynağı okur (single-source).

## 10) STELLCODEX AI (Kilitli Yetki Sınırı)
AI iki amaçla vardır:
1) Kullanıcı destek ve akış iyileştirme (hata sınıflandırma, tıkanma analizi)
2) Admin dashboard önerileri (performans, hata kümeleri, UX önerileri)

Kesin sınır:
- AI sadece önerir.
- AI otomatik uygulama / otomatik değişiklik yapmaz.
- AI kullanıcı içeriğini yayımlamaz.

## 11) Admin Dashboard (Tek Kontrol Merkezi)
- Kullanıcılar, dosyalar, paylaşımlar, işlem kuyrukları
- Sistem sağlık: worker, redis, db, storage
- Log/telemetri görünümü
- Güvenlik olayları / rate limit / abuse

## 12) Değişiklik Kaydı (V1.2 → V1.3)
- Render preset: B seçildi (4 preset kilitlendi)
- SCX-ID: A seçildi (UUID v4 + scx_ prefix)
- Anonymous retention: A seçildi (24h + login sonrası devralma)
- AI yetkisi: A seçildi (sadece öneri, otomasyon yok)
