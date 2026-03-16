## Archive Note

- Reason retired: This dated root-level evidence file is historical proof, not active protocol or active reporting authority.
- Replaced by: `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` and `docs/manifests/FINAL_CONSOLIDATION_REPORT.md`
- Historical value: Yes. It preserves the `2026-02-27` UI and smoke-gate evidence context.

# STELLCODEX FINAL EVIDENCE

Date: 2026-02-27
Repo: /var/www/stellcodex
Branch: feat/ui-viewer-sprint-2

## 1) Sorun Listesi (Before)

1. Upload sonrası bazı akışlarda kullanıcı `Viewer’a yönlendiriliyor...` metninde kalıyordu.
2. Share link (`/share/{token}`) frontendde 404 oluyordu.
3. Viewer assembly panelinde part operasyonları (select/hide/isolate) fiilen çalışmıyordu.
4. DXF bazen boş/çok zor görünür çıkıyordu.
5. Büyük dosyalarda progress/stage görünürlüğü zayıftı; timeout/ux kontrolleri sınırlıydı.
6. Console’da route 404 spam (`/upload`, `/dashboard`, `/login`, `/docs`, `/community`, `/share/{token}`) vardı.
7. Passive listener / WebGL context recovery tarafında stabilite eksikleri vardı.

Before route kanıtı: `evidence/network_traces_before.md`, `evidence/console_errors_before.txt`

## 2) Kök Nedenler

- `frontend/middleware.ts` allowlist gerçek route setinden dardı; birden çok valid route middleware seviyesinde 404’e düşüyordu.
- `UploadDrop` callback davranışı sayfa bazlı farklıydı; home ekranında callback redirect yapmıyordu.
- Share API resolve çalışsa da frontend token route’a middleware izin vermediği için link açılmıyordu.
- Assembly tree için backend manifestte data boş olabiliyor; frontendde runtime fallback ve operasyon bağları eksikti.
- DXF render’da Y-flip transformu eksik translate ile uygulanıyordu; ayrıca ACI7 beyaz çizgi beyaz zeminde kayboluyordu.
- Status API sadece metinsel hint dönüyor, numerik progress/stage dönmüyordu.

## 3) Yapılan Fixler (Dosya Listesi)

### Routing / Share
- `frontend/middleware.ts`
- `backend/app/api/v1/routes/share.py`
- `frontend/src/services/api.ts`

### Upload / Viewer geçiş
- `frontend/src/components/upload/UploadDrop.tsx`
- `frontend/src/app/(public)/upload/page.tsx`
- `frontend/src/app/page.tsx`

### Viewer stabilite / assembly / 2D etkileşim
- `frontend/src/app/(viewer)/view/[scx_id]/page.tsx`
- `frontend/src/components/viewer/ThreeViewer.tsx`
- `frontend/src/components/viewer/DxfViewer.tsx`
- `frontend/src/components/viewer/viewer-quality-config.ts`

### Pipeline / status / manifest
- `backend/app/api/v1/routes/files.py`
- `backend/app/workers/tasks.py`
- `backend/app/services/dxf.py`
- `backend/app/core/config.py`

### Infra / timeout / upload limit
- `infrastructure/deploy/docker-compose.yml`
- `infrastructure/nginx/stellcodex.conf`

### Regression gate
- `scripts/smoke_gate.sh`
- `scripts/README.md`

## 4) Test Komutları

### Build / servis
1. `cd /var/www/stellcodex/frontend && npm run build`
2. `pm2 restart stellcodex-next && pm2 list`
3. `cd /var/www/stellcodex/infrastructure/deploy && ./compose-safe.sh up -d --build minio backend worker`
4. `./compose-safe.sh ps`
5. `nginx -t`

### Route doğrulama
1. `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/upload`
2. `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/dashboard`
3. `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/login`
4. `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/docs`
5. `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/community`

### E2E regression gate
1. `cd /var/www/stellcodex && ./scripts/smoke_gate.sh`

## 5) Sonuçlar

- Frontend build: PASS
- Backend/worker rebuild: PASS
- Nginx config test: PASS
- Route 404 spam target yolları: PASS (`200`)
- Smoke gate: PASS
  - jpg upload/status/view: PASS
  - dxf upload/manifest/render/view: PASS
  - step upload/status/manifest(part_count>0)/view: PASS
  - share create/resolve/frontend share route: PASS

Kanıt: `evidence/smoke_gate_output.txt`

## 6) Kanıt Dosyaları

- `evidence/repro_notes.md`
- `evidence/console_errors_before.txt`
- `evidence/network_traces_before.md`
- `evidence/upload_redirect_fix.md`
- `evidence/share_fix.md`
- `evidence/routes_fix.md`
- `evidence/viewer_stability.md`
- `evidence/assembly_tree.md`
- `evidence/dxf_fix.md`
- `evidence/large_file.md`
- `evidence/smoke_gate_output.txt`

Ayrıca fix sonrası ham örnek JSON/SVG:
- `evidence/after_step_status_20260227_092323.json`
- `evidence/after_step_manifest_20260227_092323.json`
- `evidence/after_share_resolve_20260227_092323.json`
- `evidence/after_dxf_render_20260227_092355.svg`

## 7) Kalan Riskler / Notlar

1. Bu turda gerçek browser devtools ile manuel “ileri/geri 10 kez” testi CLI içinde otomatikleştirilemedi; buna karşılık route/view smoke testleri ve kod seviyesinde context-lost + non-passive wheel düzeltmeleri uygulandı.
2. STEP için backend `assembly_tree` hâlâ bazı dosyalarda boş olabilir; runtime fallback ile viewer tarafında ağaç/part operasyonu çalışır hale getirildi ve manifest `part_count` fallback’i eklendi.
3. Nginx aktif dosyası ortamda symlink/kopya farkı gösterebildiği için canlı dosya ayrıca senkronlandı ve servis yeniden başlatıldı.
