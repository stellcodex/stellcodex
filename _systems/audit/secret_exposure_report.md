# Secret Exposure Report (Redacted)

Generated: 2026-03-06T23:21:08Z

Total findings (path-level): 98

## Findings (sample)
- /root/workspace/.env:2 -> UPSTASH_REDIS_REST_TOKEN=REDACTED
- /root/workspace/ops/orchestra/.env.example:1 -> OPENAI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/.env.example:2 -> ANTHROPIC_API_KEY=REDACTED
- /root/workspace/ops/orchestra/.env.example:3 -> GEMINI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/.env.example:4 -> ABACUSAI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/.env.example:15 -> LLM_API_KEY=REDACTED
- /root/workspace/ops/orchestra/.env.example:32 -> WHATSAPP_TOKEN=REDACTED
- /root/workspace/ops/orchestra/discover_keys.py:155 ->         f"OPENAI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/discover_keys.py:156 ->         f"ANTHROPIC_API_KEY=REDACTED
- /root/workspace/ops/orchestra/discover_keys.py:157 ->         f"GEMINI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/discover_keys.py:158 ->         f"ABACUSAI_API_KEY=REDACTED
- /root/workspace/ops/orchestra/discover_keys.py:167 ->         f"LLM_API_KEY=REDACTED
- /root/workspace/ops/orchestra/orchestrator/app.py:36 -> LLM_API_KEY =REDACTED
- /root/workspace/ops/orchestra/docker-compose.yml:28 ->       LLM_API_KEY
- /root/workspace/ops/orchestra/docker-compose.yml:61 ->       WHATSAPP_TOKEN
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:31 -> WHATSAPP_TOKEN =REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:33 -> VERIFY_TOKEN =REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:35 -> WHATSAPP_APP_SECRET =REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:39 -> if not WHATSAPP_APP_SECRET
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:86 ->     if not WHATSAPP_APP_SECRET
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/stell/webhook/main.py:387 ->     if params.get("hub.mode") =REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/workspace/ops/orchestra/orchestrator/app.py:30 -> LLM_API_KEY =REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/.env.example:8 -> JWT_SECRET=REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/.env:13 -> JWT_SECRET=REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.local.yml:10 ->       POSTGRES_PASSWORD
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.local.yml:38 ->       MINIO_ROOT_PASSWORD
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.local.yml:69 ->       JWT_SECRET
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.local.yml:86 ->       ADMIN_TOKEN
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.local.yml:111 ->       JWT_SECRET
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.yml:11 ->       POSTGRES_PASSWORD
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.yml:41 ->       MINIO_ROOT_PASSWORD
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.yml:71 ->       JWT_SECRET
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.yml:88 ->       ADMIN_TOKEN
- /root/workspace/stellcodex_v7/infrastructure/deploy/docker-compose.yml:115 ->       JWT_SECRET
- /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_v7.sh:36 -> TOKEN=REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_v7.sh:140 -> SHARE_TOKEN=REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_v7.sh:159 -> EXPIRED_TOKEN=REDACTED
- /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_v7.sh:174 -> RATE_TOKEN=REDACTED
- /root/workspace/stellcodex_v7/backend/app/services/email.py:13 -> RESEND_API_KEY =REDACTED
- /root/workspace/stellcodex_v7/backend/app/services/email.py:20 ->     if not RESEND_API_KEY
- /root/workspace/stellcodex_v7/backend/.env:1 -> GOOGLE_API_KEY=REDACTED
- /root/workspace/stellcodex_v7/backend/.env:2 -> RESEND_API_KEY=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env:10 -> CLOUDFLARE_API_TOKEN=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env:12 -> # CF_API_TOKEN=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env:20 -> VERCEL_TOKEN=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/monthly_prompt_audit.sh:60 -> if env | rg -q '^VERCEL_TOKEN=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/provider_live_audit.sh:57 -> cf_token=REDACTED
- /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/provider_live_audit.sh:73 -> vercel_token=REDACTED
- /root/workspace/audit/scripts/monthly_prompt_audit.sh:60 -> if env | rg -q '^VERCEL_TOKEN=REDACTED
- /root/workspace/audit/scripts/provider_live_audit.sh:57 -> cf_token=REDACTED
- /root/workspace/audit/scripts/provider_live_audit.sh:73 -> vercel_token=REDACTED
- /root/workspace/audit/output/focused_inventory.csv:383 -> "focused_fs","/root/stell/webhook/.env",".env","env","text/plain","508","a8e846050d72c9168f551df4aaad3bde66a126d35a04d030e8e4f3dcc16f5b84","2026-03-04T04
- /root/workspace/audit/output/focused_inventory.csv:384 -> "focused_fs","/root/stell/webhook/.env.example",".env.example","example","text/plain","362","9ac02d0a0e3b612ca5654a5e4bd2ede58f1cdb444e96f35f4d2c5bd0534b1029","2026-02-28T12
- /root/workspace/audit/output/focused_inventory.csv:385 -> "focused_fs","/root/stell/webhook/.env.save",".env.save","save","text/plain","490","66faac95c69478af3503e90a29dc8a9edae1e42139d3fb06f9a18f76774b6ad3","2026-02-28T17
- /root/workspace/audit/output/focused_inventory.csv:681 -> "focused_fs","/root/workspace/_backups/20260304_212236_platform_stability/stell_webhook/.env",".env","env","text/plain","508","a8e846050d72c9168f551df4aaad3bde66a126d35a04d030e8e4f3dcc16f5b84","2026-03-04T18
- /root/workspace/audit/output/focused_inventory.csv:682 -> "focused_fs","/root/workspace/_backups/20260304_212236_platform_stability/stell_webhook/.env.example",".env.example","example","text/plain","362","9ac02d0a0e3b612ca5654a5e4bd2ede58f1cdb444e96f35f4d2c5bd0534b1029","2026-03-04T18
- /root/workspace/audit/output/focused_inventory.csv:683 -> "focused_fs","/root/workspace/_backups/20260304_212236_platform_stability/stell_webhook/.env.save",".env.save","save","text/plain","490","66faac95c69478af3503e90a29dc8a9edae1e42139d3fb06f9a18f76774b6ad3","2026-03-04T18
- /root/workspace/audit/output/focused_inventory.csv:825 -> "focused_fs","/root/workspace/stellcodex_v7/backend/.env",".env","env","text/plain","151","3dcf92359eec961e2ce8940815e56a4d6724705b45b4c822d280e2cdcd6920c3","2026-03-05T13
- /root/workspace/audit/output/focused_inventory.csv:879 -> "focused_fs","/var/www/stellcodex/backend/.env",".env","env","text/plain","151","3dcf92359eec961e2ce8940815e56a4d6724705b45b4c822d280e2cdcd6920c3","2026-03-02T07
- /root/workspace/audit/output/focused_inventory.csv:890 -> "focused_fs","/var/www/stellcodex/docker/.env.example",".env.example","example","text/plain","337","700e2adb2d6e1a1b5d6dd4465add6d7eaeb851d94dbb021becee05801a9ab7b8","2026-02-27T08
- /root/workspace/scripts/daily_report.py:10 -> RESEND_API_KEY   =REDACTED
- /root/workspace/scripts/daily_report.py:12 -> WHATSAPP_TOKEN   =REDACTED
- /root/workspace/scripts/daily_report.py:70 ->     if not RESEND_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:8 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:9 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:13 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:16 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:25 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:33 ->       WHATSAPP_TOKEN
- /root/workspace/evidence/docker_compose_config_final.txt:44 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:45 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:47 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:49 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:56 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:80 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:81 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:83 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:85 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_final.txt:92 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:8 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:9 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:17 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:20 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:29 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:37 ->       WHATSAPP_TOKEN
- /root/workspace/evidence/docker_compose_config_after_patch.txt:48 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:49 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:56 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:58 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:65 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:71 ->       WHATSAPP_TOKEN
- /root/workspace/evidence/docker_compose_config_after_patch.txt:93 ->       ABACUSAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:94 ->       ANTHROPIC_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:101 ->       GEMINI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:103 ->       LLM_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:110 ->       OPENAI_API_KEY
- /root/workspace/evidence/docker_compose_config_after_patch.txt:117 ->       WHATSAPP_TOKEN
- /root/workspace/.github/workflows/stell-worker.yml:38 ->           UPSTASH_REDIS_REST_TOKEN

## Recommendation
1. Rotate credentials found in plain .env or compose files.
2. Replace inline secrets with secret manager references.
3. Add CI secret scanning gate to block new exposures.
