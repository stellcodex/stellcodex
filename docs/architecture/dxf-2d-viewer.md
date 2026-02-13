# DXF Native 2D Viewer — Teknik Tasarım (ezdxf==1.4.3)

Bu doküman docs/STELLCODEX_MASTER_V1.3.md içindeki “DXF native 2D viewer” kararını uygulamak için teknik tasarımı kilitler.
Amaç: DXF dosyası yüklenince web’de native 2D viewer ile pan/zoom, katman görünürlük ve anotasyon altyapısına uyumlu önizleme.

## DXF “açmak” tanımı
DXF açma akışı bağlayıcı olarak şu şekilde tanımlanır:

1) DXF parse (ezdxf==1.4.3)
2) Scene modeli üretimi (layer listesi, bbox, entity sayımları, unit bilgisi)
3) Render katmanı (tek çıktı formatı)

## Render stratejisi (KİLİTLİ KARAR)
**Tek çıktı formatı: SVG**

Gerekçe:
- DXF vektör doğası SVG ile doğrudan korunur.
- Katman görünürlüğü SVG grupları ile yönetilebilir.
- Browser tarafında hızlı preview sağlar, raster kalite kaybı yoktur.
- Tek format şartını bozmadan ilerler.

Not:
- Bu aşamada SVG tek çıktıdır; tile PNG veya PDF kullanılmaz.
- Büyük DXF’lerde render süresi ve SVG boyutu kontrol altına alınmalıdır (aşağıda performans hedefleri).

## Katman görünürlük modeli
- DXF layer → UI layer listesi birebir yansır.
- Backend manifest her layer için:
  - `name`
  - `color` (ACI → RGB)
  - `linetype`
  - `is_visible` (varsayılan true)
- Render endpoint’i `layers` query paramı ile görünür seti alır.
- Görünür olmayan layer’lar render edilmez.

## Ölçüm yaklaşımı
- DXF unit bilgisi `INSUNITS` üzerinden okunur.
- `units_code` ve mümkünse `units_name` manifest içinde gönderilir.
- Units belirsiz/0 ise:
  - UI uyarı gösterir: “Unit belirsiz, ölçümler birimsizdir.”
  - Ölçüm değerleri “unitless measure” olarak işaretlenir.

## Performans hedefleri
- 10 MB altı DXF için ilk render < 2s (p95).
- 50 MB üstü DXF için:
  - render timeout (backend) uygulanır
  - kullanıcıya “büyük dosya” uyarısı verilir
- Render SVG boyutu büyürse:
  - layer bazlı filtreleme önerilir
  - kullanıcıya “layer azalt” uyarısı gösterilir

## Güvenlik
- DXF dosyası yalnızca izinli uzantı (.dxf) ile kabul edilir.
- Max upload boyutu backend limitine tabidir.
- Render işlemi timeout ile sınırlandırılır.
- Sadece dosya sahibi (owner) render/manifest alabilir.

## Backend endpoint’leri
### GET /api/v1/files/{id}/dxf/manifest
Çıktı:
- `layers` (name/color/linetype/is_visible)
- `bbox` (min_x, min_y, max_x, max_y)
- `units` (code, name)
- `entity_counts` (LINE, LWPOLYLINE, CIRCLE, ARC, vb.)

### GET /api/v1/files/{id}/dxf/render
Query:
- `layers` (virgül ayrılmış layer listesi)

Çıktı:
- `image/svg+xml`

## Frontend davranışı
- `/app/viewer-2d/[id]` route’u DXF ise DXF renderer’a düşer.
- Manifest ile katman listesi gösterilir.
- Katman seçimi değişince render endpoint çağrılır.
- SVG render pan/zoom ile görüntülenir.

## Notlar ve sınırlamalar (V1)
- DXF TEXT/MTEXT ilk fazda render dışı kalabilir.
- Ölçüm doğruluğu unit belirsizse “yaklaşık” olarak işaretlenir.
- SVG output tek çıktı formatıdır; tile pipeline bu fazda yoktur.
