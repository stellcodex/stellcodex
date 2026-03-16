## Archive Note

- Reason retired: This phased rebuild protocol was superseded by the GitHub canonical V10 package, evidence standard, and continuation protocol.
- Replaced by: `docs/v10/13_V10_EXECUTION_ROADMAP.md`, `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`, and `docs/v10/20_V10_FINAL_EXECUTION_CHECKLIST.md`
- Historical value: Yes. It captures the phase-based rebuild approach that led to the current V10 state.

# STELLCODEX Rebuild Execution Protocol

## Purpose

Bu repo bundan sonra sistemi sifirdan yeniden kuruyormus gibi ele alir.
Her is parcasi fazlara ayrilir, faz kapanmadan bir sonraki faz acilmaz, her kapanis kanit ile belgelenir.

## Binding References

Asagidaki belgeler ust referanstir:

- `STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md`
- `docs/constitution/STELLCODEX_V7_MASTER.md`
- `docs/constitution/HIERARCHY.md`
- `docs/constitution/V7_ENFORCEMENT_PROTOCOL.md`

Destekleyici referanslar:

- `docs/contracts/API_CONTRACTS_V7.md`
- `docs/contracts/RATE_LIMIT_AND_AUDIT_SPEC.md`
- `docs/contracts/DECISION_JSON_SCHEMA.md`
- `docs/data_model/SCHEMA_POLICY.md`
- `docs/STELLCODEX_MASTER_V1.3.md`
- `docs/security/permissions-catalog.md`
- `docs/security/role-permission-template.md`
- `docs/release_checklist.md`

## Operating Rules

1. Faz sirasi baglayicidir. Atlama yok.
2. "Bitti" demek icin dokuman, sozlesme, kod, config ve kanit ayni yone bakmalidir.
3. Hot patch yasak: repo -> degisiklik -> build/test -> proof.
4. Evidence olmadan PASS yok.
5. Kullaniciya ait mevcut degisiklikler silinmez; baseline icinde kayda alinir.
6. V10 veya ondan miras alinan V7 release-blocking ihlali gorulurse mevcut faz durur, once ihlal kapatilir.

## Evidence Standard

Her faz kapatisi su klasorde tutulur:

- `docs/ops/evidence/PHASE_XX_<slug>.md`

Her kanit dosyasi sunlari icerir:

- Scope
- Inputs
- Outputs
- Commands run
- Result
- Open items
- Next handoff

## Working Cadence

Her faz su donguyle ilerler:

1. Faz hedefini kilitle.
2. Ilgili protokol/sozlesme/kod degisikliklerini yap.
3. Faz kapanis komutlarini calistir.
4. Sonucu evidence dosyasina yaz.
5. Sonraki faza yalnizca handoff ile gec.

## Phase Map

### Phase 00 - Baseline Lock

Amac:
Mevcut repo durumunu, baglayici belgeleri, aktif bilesenleri ve acik riskleri kayda almak.

Inputs:

- Repo top-level yapisi
- Git durumu
- README ve master README
- Constitution, contracts, release checklist

Outputs:

- Baseline envanter kaniti
- Dirty worktree kaydi
- Faz sirasi icin ilk harita

Exit Criteria:

- Baglayici ve destekleyici belgeler listelenmis olmali
- Repo ana bilesenleri siniflanmis olmali
- Mevcut degisiklikler kayda alinmis olmali

Proof:

- `pwd`
- `ls -la`
- `git status --short`
- `rg --files ...`

### Phase 01 - Constitution and Contract Freeze

Amac:
Urunun ne oldugunu ve ne olmadigini koddan once kesinlestirmek.

Inputs:

- Constitution
- API contracts
- Rate limit and audit spec
- UI page map
- Security permission references

Outputs:

- ID/state/share/rate-limit/RBAC contract matrisi
- Belirsiz urun kararlarinin listesi
- Koddan once kapatilacak bosluk kaydi

Exit Criteria:

- Public identifier yalniz `file_id`
- S0..S7 state machine kod yoluyla eslenecek sekilde listelenmis
- Share expiry => `410`, revoke, audit ve rate limit kurallari net
- UI route sinirlari public/auth/app/admin olarak kilitli

Proof:

- Contract diff veya matrix
- `./scripts/leak_scan_repo.sh`
- Route/API inceleme notu

### Phase 02 - Data Model and Migration Floor

Amac:
V7 veri modelini tablo, kolon ve migration tabaninda dogrulamak.

Inputs:

- `docs/data_model/SCHEMA_POLICY.md`
- `db/`
- `backend/alembic/`
- `backend/app/`

Outputs:

- Required table coverage listesi
- Eksik tablo/kolon/migration gap listesi
- `decision_json`, `rule_configs`, `assembly_meta` zorunluluk haritasi

Exit Criteria:

- Required tablolar mevcut ya da acik gap olarak kayitli
- `decision_json NOT NULL` kurali net baglanmis
- Hardcoded threshold yerine `rule_configs` kaynagi gosterilmis

Proof:

- Migration envanteri
- Model/schema inceleme notu
- Varsa migration/test ciktilari

### Phase 03 - Backend Core and Worker Pipeline

Amac:
Upload, state transition, orchestrator, DFM, approval ve share davranisini arka ucta calisir hale getirmek.

Inputs:

- `backend/app/`
- `worker.py`
- `backend/tests/`
- API contracts

Outputs:

- Endpoint coverage listesi
- State transition enforcement notlari
- Worker/pipeline sorumluluk haritasi

Exit Criteria:

- Minimum V7 endpoint seti kodda karsilanmis
- State skip yasagi uygulanmis veya gap olarak kayitli
- `decision_json`, `assembly_meta`, expired share `410`, audit/rate-limit davranisi baglanmis

Proof:

- Backend testleri
- Health endpoint ciktilari
- `./scripts/smoke_gate.sh` veya hedefli curl kaniti

### Phase 04 - Frontend Routes and UX Contract

Amac:
Public, auth, app ve admin arayuzlerini baglayici sayfa haritasi ile uyumlu hale getirmek.

Inputs:

- `frontend/src/`
- `frontend/middleware.ts`
- `docs/STELLCODEX_MASTER_V1.3.md`
- RBAC policy dosyalari

Outputs:

- Route coverage listesi
- Kritik ekran tamamlanma listesi
- RBAC route/permission eslesmesi

Exit Criteria:

- Public/auth/app/admin ayrimi middleware ve route yapisinda acik
- Admin route'lari RBAC olmadan acilmiyor
- Upload -> preview/view -> share -> presentation akisi gorunur durumda

Proof:

- `cd frontend && npm run build`
- `cd frontend && npm run rbac:validate`
- `cd frontend && npm run rbac:validate-routes`
- Route smoke veya UI evidence

### Phase 05 - Infra, Runtime and Delivery Chain

Amac:
Sistemin container, nginx, env, backup ve restore yuzeyini calisir ve tekrar kurulabilir hale getirmek.

Inputs:

- `docker/`
- `infrastructure/`
- `ops/`
- `scripts/`

Outputs:

- Runtime topology ozeti
- Env/secret contract listesi
- Backup and restore akis notu
- Storage cleanup automation and Drive offload notu

Exit Criteria:

- Compose/nginx/deploy yuzeyi tutarli
- Health endpoint'ler tanimli
- Backup ve restore adimlari mevcut
- Rebuildable server data otomatik temizleniyor ve offload edilen artefaktlar lokalde birikmiyor
- Release gate hangi komutlarla kapanacagi net

Proof:

- `nginx -t`
- `docker ps`
- Health curl ciktilari
- `bash ops/scripts/cleanup.sh`
- `crontab -l`
- `./scripts/weekly_restore_gate.sh` veya esit kanit

### Phase 06 - Release Gate and Final Evidence

Amac:
Tum sistemin bastan sona toplu olarak dogrulandigini kanitlamak.

Inputs:

- Onceki tum faz evidence dosyalari
- Release checklist
- Smoke ve release gate scriptleri

Outputs:

- Final evidence bundle
- Kalan riskler listesi
- Devam veya deploy karari

Exit Criteria:

- Release checklist PASS
- Smoke gate PASS
- Kritik riskler ya kapali ya da acikca kabul edilmis

Proof:

- `./scripts/release_gate.sh`
- `./scripts/smoke_gate.sh`
- Gerekirse `./scripts/weekly_restore_gate.sh`

## Current Starting Point

Bu protokolun ilk uygulamasi `docs/ops/evidence/PHASE_00_BASELINE.md` dosyasidir.
Sonraki fiili calisma noktasi faz 01'dir: constitution -> contracts -> code eslestirmesi.
