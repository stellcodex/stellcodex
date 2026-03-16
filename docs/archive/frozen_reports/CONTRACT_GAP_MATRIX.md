## Archive Note

- Reason retired: This gap matrix is a dated historical assessment, not active contract authority.
- Replaced by: `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`, and `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- Historical value: Yes. It records the observed drift that V10 consolidation resolved or tracked.

# STELLCODEX Contract Gap Matrix

## Purpose

Bu dokuman, binding anayasa ve destekleyici contract'lar ile mevcut repo uygulamasi arasindaki farklari tek yerde toplar.
Sonraki fazlar bu bosluklari kapatmak icin kullanilir.

## Status Legend

- `OK`: gozlenen uygulama contract ile uyumlu
- `PARTIAL`: kismen uyumlu, ama kapatilmasi gereken fark veya kanit eksigi var
- `GAP`: contract beklentisi ile mevcut uygulama arasinda acik fark var

## Matrix

| Area | Requirement | Observed Implementation | Status | References |
| --- | --- | --- | --- | --- |
| Identity | Public contract `file_id` ustunden akmali | `files.py` ve `frontend/src/services/api.ts` agirlikli olarak `file_id` kullaniyor | `PARTIAL` | `backend/app/api/v1/routes/files.py`, `frontend/src/services/api.ts` |
| Identity | `revision_id` public contract olmamali | Legacy `product.py` halen `/status/{revision_id}` ve `RenderRequest.revision_id` yuzeyi aciyor | `GAP` | `backend/app/api/v1/routes/product.py` |
| Identity | `storage_key` public response body'de gorunmemeli | Incelenen route serializer'larinda dogrudan `storage_key` donulmuyor; ancak legacy product route presigned artifact url'lari uretiyor, runtime proof sonraki fazda gerekli | `PARTIAL` | `backend/app/api/v1/routes/product.py`, `backend/app/api/v1/routes/files.py` |
| Share | Public share URL `/s/{token}` olmali | Root app ve share router altinda `/s/{token}` mevcut | `OK` | `backend/app/main.py`, `backend/app/api/v1/routes/share.py` |
| Share | Expired share `410` donmeli | `_resolve_active_share()` expired durumda `HTTP_410_GONE` donuyor | `OK` | `backend/app/api/v1/routes/share.py` |
| Share | Create route `POST /api/v1/shares` olmali | Canonical create route `/api/v1/shares` eklendi; legacy file-scoped path hidden compatibility alias olarak tutuluyor | `OK` | `backend/app/api/v1/routes/share.py`, `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md` |
| Share | Revoke route `POST /api/v1/shares/{share_id}/revoke` olmali | Revoke route mevcut | `OK` | `backend/app/api/v1/routes/share.py` |
| Share | Token uzunlugu `>= 64 random` olmali | Token uretimi `secrets.token_hex(40)` ile 80 karaktere cikti | `OK` | `backend/app/api/v1/routes/share.py`, `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md` |
| Share | Rate limit `30 req / 60s / IP`, key format `rl:{scope}:{identifier}:{window_start_epoch}` olmali | Rate limit 30/60/IP ve key `rl:share_resolve:{identifier}:{window_start_epoch}` formatina cekildi | `OK` | `backend/app/api/v1/routes/share.py`, `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md` |
| Share | Rate limit audit event spec'e uymali | Audit event `RATE_LIMIT` ve endpoint metadata alanlariyla yaziliyor | `OK` | `backend/app/api/v1/routes/share.py`, `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md` |
| Data Model | `orchestrator_sessions` ve `decision_json NOT NULL` migration'da olmali | SQL template vardi; artik ORM model, runtime upsert service ve alembic migration da mevcut | `PARTIAL` | `db/migrations/0001_create_orchestrator_sessions.sql`, `backend/app/models/orchestrator.py`, `backend/app/services/orchestrator_sessions.py`, `backend/alembic/versions/b7e1c2d3f4a5_v7_orchestrator_rule_configs.py` |
| Data Model | `rule_configs` tablo olarak olmali | SQL migration mevcut | `OK` | `db/migrations/0002_create_rule_configs.sql` |
| Data Model | `rule_configs` runtime rule engine tarafindan kullanilmali | Hybrid V1 config artik DB-backed loader ile `rule_configs` tablosundan okunabiliyor; aktif kullanim worker pipeline'a baglandi | `PARTIAL` | `backend/app/services/rule_configs.py`, `backend/app/workers/tasks.py`, `db/migrations/README.md` |
| Data Model | `decision_json` runtime akista baglanmali | Upload ve worker artik schema-shaped `decision_json` uretiyor ve orchestrator session'a yazabiliyor; ancak public orchestrator API halen eksik | `PARTIAL` | `backend/app/services/orchestrator_sessions.py`, `backend/app/api/v1/routes/files.py`, `backend/app/workers/tasks.py` |
| Viewer Meta | `assembly_meta` olmadan ready yasak | Worker `assembly_meta_key` uretiyor, files route ve viewer bunu kullaniyor | `PARTIAL` | `backend/app/workers/tasks.py`, `backend/app/api/v1/routes/files.py`, `frontend/src/app/(viewer)/view/[scx_id]/page.tsx` |
| Orchestrator | `/api/v1/orchestrator/start|decision|required-inputs` yuzeyi olmali | Contract route'lari eklendi ve compile/smoke proof alindi; tam canli E2E proof sonraki fazda gerekli | `PARTIAL` | `backend/app/api/v1/routes/orchestrator.py`, `backend/app/api/v1/router.py`, `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md` |
| Approvals | `/api/v1/approvals/{session_id}/approve|reject` minimum endpoint setinde olmali | Approve/reject route'lari eklendi ve orchestrator session state'ine baglandi; admin UI henuz bu route'lara bagli degil | `PARTIAL` | `backend/app/api/v1/routes/approvals.py`, `frontend/src/app/(app)/admin/approvals/page.tsx`, `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md` |
| Approvals UI | Admin approvals ekrani backend'e bagli olmali | Admin approvals list/approve/reject surface'i eklendi ve frontend page buna baglandi; tam Next.js build proof'u environment bagimlilik eksigine takildi | `PARTIAL` | `frontend/src/app/(app)/admin/approvals/page.tsx`, `frontend/src/services/admin.ts`, `backend/app/api/v1/routes/admin.py`, `docs/ops/evidence/PHASE_04_ADMIN_APPROVALS_UI.md` |
| DFM | `/api/v1/dfm/report?file_id=...` endpoint'i olmali | Route eklendi ve mevcut `dfm_findings`/`geometry_report` payload'larini public contract yuzeyine tasiyor | `PARTIAL` | `backend/app/api/v1/routes/dfm.py`, `backend/app/workers/tasks.py`, `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md` |
| UI Map | Public landing `/` olmali | Root route workspace redirect yapiyor; public landing `/home` altinda | `GAP` | `frontend/src/app/page.tsx`, `frontend/src/app/(public)/home/page.tsx`, `docs/STELLCODEX_MASTER_V1.3.md` |
| UI Map | Public pages `/features`, `/community`, `/status`, `/docs`, `/privacy`, `/terms` olmali | Bu public sayfalar mevcut | `OK` | `frontend/src/app/(public)/` |
| UI Map | Auth pages `/auth/login`, `/auth/register`, `/auth/forgot`, `/auth/reset` olmali | Mevcut frontend `login`, `register`, `forgot`, `reset` route'larini root altinda aciyor; `/auth/*` hiyerarsisi yok | `GAP` | `frontend/src/app/(public)/login/page.tsx`, `frontend/src/app/(public)/register/page.tsx`, `frontend/src/app/(public)/forgot/page.tsx`, `frontend/src/app/(public)/reset/page.tsx` |
| UI Map | User pages `/app/dashboard`, `/app/library`, `/app/upload`, `/app/file/[id]`, `/app/viewer-2d/[id]`, `/app/viewer-3d/[id]`, `/app/presentations`, `/app/shares`, `/app/notifications`, `/app/account` olmali | Mevcut tree agirlikla `/dashboard`, `/library`, `/upload`, `/shares`, `/view/[scx_id]`, workspace alt rotalar ve app katalog yonlendirmeleri kullaniyor | `GAP` | `frontend/src/app/`, `docs/STELLCODEX_MASTER_V1.3.md` |
| UI Map | Admin route'lari RBAC ile korunmali | Middleware `/admin*` icin token ve admin role kontrolu yapiyor | `OK` | `frontend/middleware.ts` |
| Admin Surface | UI route listesi ve backend admin endpointleri birbirini karsilamali | Health/files/shares/users/audit/queues ve approvals list/approve/reject var; content/roles/settings gibi beklentiler halen eksik | `PARTIAL` | `frontend/src/security/admin-ui.routes.generated.ts`, `backend/app/api/v1/routes/admin.py`, `docs/ops/evidence/PHASE_04_ADMIN_APPROVALS_UI.md` |
| Infra Hygiene | Server rebuildable data otomatik temizlenmeli ve Drive'a tasinmali | `cleanup.sh` Drive sync + local prune uygular; gece cron tanimi ve kurulum helper'i eklendi, runtime install proof'u alindi | `OK` | `ops/scripts/cleanup.sh`, `ops/cron/stellcodex-cleanup.cron`, `ops/scripts/install_cleanup_cron.sh`, `docs/ops/evidence/PHASE_05_STORAGE_HYGIENE.md` |
| Infra Hygiene | GitHub repo build artefakti ile sisirilmemeli | `.gitignore` rebuildable cache'leri ignore ediyor; cleanup her kosuda remote, pack size ve en buyuk tracked file audit'ini logluyor | `OK` | `.gitignore`, `ops/scripts/cleanup.sh`, `docs/ops/evidence/PHASE_05_STORAGE_HYGIENE.md` |

## Immediate Build Order Impact

Phase 02 ve sonrasi su sirayla ilerlemeli:

1. Legacy `revision_id` public surface'ini ya kaldir ya da acik deprecation duvarina cek.
2. Yeni backend route surface'ini canli environment smoke ile dogrula.
3. Frontend approvals ve route haritasini binding UI map ile yeniden esle.
4. Admin/generated permission artefaktlarini yeni route setiyle senkronize et.
5. Phase 05'te runtime topology, restore proof ve delivery chain kanitlarini kapat.

## Evidence Link

Bu matrix'in ilk kaniti:

- `docs/ops/evidence/PHASE_01_CONTRACT_FREEZE.md`
- `docs/ops/evidence/PHASE_02_DATA_MODEL_RUNTIME.md`
- `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md`
- `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md`
- `docs/ops/evidence/PHASE_04_ADMIN_APPROVALS_UI.md`
- `docs/ops/evidence/PHASE_05_STORAGE_HYGIENE.md`
