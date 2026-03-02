# Stellcodex — Claude Code Context

Detaylı bağlam: `/root/workspace/PROJECT.md`

## Mimari Özet

- **Backend:** FastAPI → `backend/app/`
- **Frontend:** Next.js → `frontend/src/app/`
- **Docker:** `docker/docker-compose.yml`

## V7 Constitution (Bağlayıcı)

- `storage_key` hiçbir zaman public response'a girmez
- State machine S0→S1→S2→S3→S4→S5→S6→S7 — atlama yasak
- `decision_json` her `file_id` için zorunlu
- Hardcoded threshold yasak → `rule_configs` tablosundan alınır
- LLM ile üretim kararı yasak

## Sık Kullanılan

```bash
docker logs stellcodex-backend --tail=50
docker logs stellcodex-worker --tail=50
docker exec stellcodex-postgres psql -U stellcodex -d stellcodex -c "\dt"
pm2 restart stellcodex-next
nginx -t && systemctl reload nginx
```

## Dil

Kullanıcı Türkçe — yanıtlar Türkçe olmalı.
