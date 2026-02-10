# Format Uyumluluk Matrisi (V1+V2)

Amaç: “Açar” ifadesini teknik olarak kilitlemek.
Her format için upload kabulü, native viewer, conversion pipeline ve sınırlamalar net olarak tanımlanır.

Sütunlar:
- Upload kabul
- Native viewer
- Conversion pipeline
- Sınırlamalar
- Test dosyası (repo içi örnek yolu)

## 3D / B-Rep / Parametrik

| Format | Upload kabul | Native viewer | Conversion pipeline | Sınırlamalar | Test dosyası |
|---|---|---|---|---|---|
| STEP/STP | Evet | Hayır | OCCT → GLB | B-Rep, edit yok | [ASKIDA — repo sample yok] |
| IGES/IGS | Evet | Hayır | OCCT → GLB | B-Rep, edit yok | [ASKIDA — repo sample yok] |
| BREP/BRP | Evet | Hayır | OCCT → GLB | B-Rep, edit yok | [ASKIDA — repo sample yok] |
| FCStd | Evet | Hayır | FreeCAD → Mesh → Assimp → GLB | FreeCAD 1.0.2 AppImage | [ASKIDA — repo sample yok] |
| IFC | Evet | Hayır | FreeCAD → Mesh → Assimp → GLB | IFC versiyonuna bağlı | [ASKIDA — repo sample yok] |

## 3D / Mesh

| Format | Upload kabul | Native viewer | Conversion pipeline | Sınırlamalar | Test dosyası |
|---|---|---|---|---|---|
| STL | Evet | Hayır | Assimp → GLB | Mesh, color sınırlı | [ASKIDA — repo sample yok] |
| OBJ | Evet | Hayır | Assimp → GLB | MTL destekli | [ASKIDA — repo sample yok] |
| PLY | Evet | Hayır | Assimp → GLB | Color varsa korunur | [ASKIDA — repo sample yok] |
| OFF | Evet | Hayır | Assimp → GLB | Mesh | [ASKIDA — repo sample yok] |
| 3MF | Evet | Hayır | Assimp → GLB | Mesh | [ASKIDA — repo sample yok] |
| AMF | Evet | Hayır | Assimp → GLB | Mesh | [ASKIDA — repo sample yok] |
| DAE | Evet | Hayır | Assimp → GLB | Collada | [ASKIDA — repo sample yok] |
| GLB/GLTF | Evet | Evet (3D Viewer) | Passthrough | Dönüşüm yok | [ASKIDA — repo sample yok] |

## 2D

| Format | Upload kabul | Native viewer | Conversion pipeline | Sınırlamalar | Test dosyası |
|---|---|---|---|---|---|
| PDF | Evet | Evet (2D Viewer) | Yok | Sayfa bazlı | [ASKIDA — repo sample yok] |
| PNG/JPG | Evet | Evet (2D Viewer) | Yok | Görsel | [ASKIDA — repo sample yok] |
| DXF | Evet | Evet (DXF Native 2D) | DXF → Scene JSON → SVG render | Units belirsizse unitless | [ASKIDA — repo sample yok] |
| SVG | Hayır | Hayır | Yok | Şimdilik reddedilir | N/A |
| DWG | Hayır | Hayır | Yok | DXF/PDF önerilir | N/A |

## Notlar
- “Native viewer” = doğrudan web viewer ile görüntüleme.
- “Conversion pipeline” = GLB/GLTF veya SVG üretimi.
- Test dosyaları repo içine eklendiğinde tablo güncellenecektir.
