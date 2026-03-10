# PROMPT_CONFLICT_REPORT

- Generated: 2026-03-06T17:15:42Z
- Updated: 2026-03-06T18:30:22Z
- Inventory rows (filtered): 856
- Active rows: 242
- Legacy rows: 614
- Duplicate hash groups: 61
- Conflict groups: 11

## Classification Counts

- Constitution: 5
- Global policies: 9
- Identity/Core: 13
- Output contracts: 31
- Playbooks: 7
- Role definitions: 3
- Task prompts: 30
- Tool policies: 12
- Unknown/Unclassified: 735
- Worker prompts: 11

## High-Impact Conflicts

1. `_truth/STELLCODEX_MASTER_PROMPT_v8.0.md` vs `_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md` differ.
2. V7 constitution is binding, but V6 constitution/mega prompt still exists under deployed docs.
3. `webhook/main.py` and `webhook_main.py` are duplicate runtime entrypoints with identical hashes.
4. Orchestrator instructions were embedded in code (`orchestrator/app.py`); now externalized to centralized `prompt_templates.json` with strict template enforcement.

## Post-Rewire Runtime Status

- Rewired to central manifest: `/root/stell/stell_brain.py`, `/root/stell/stell_ai_memory.py`, `/root/stell/stell_ai_planner.py`
- Rewired to centralized prompt templates: `/root/workspace/ops/orchestra/orchestrator/app.py`, `/root/workspace/ops/orchestra/orchestrator/profiler.py`
- CI guard active for drift control: `/root/stell/scripts/prompt_drift_guard.py` wired into `/root/stell/.github/workflows/ci.yml`
- Verified: `stell_brain` manifest resolver loads 40 active source→destination mappings.
- Remaining conflict surface: non-template operational instruction text (e.g. `_default_sub_tasks`) still exists in code by design.

## Duplicate Hash Samples

- sha256 `cd9fc582cb40f643cf31f78ab0b95f2a4857cb9aba80dac998f42d16acf4cdb4` count=12
  - /root/workspace/_backups/20260304_173003_stage0_discovery_map/STELLCODEX_SYSTEM_MAP.md
  - /root/workspace/_backups/20260304_173044_stage1_canonical_repo_and_deploy_proof/STELLCODEX_SYSTEM_MAP.md
  - /root/workspace/_backups/20260304_173110_stage2_ingress_stabilization/STELLCODEX_SYSTEM_MAP.md
  - /root/workspace/_backups/20260304_173149_stage3_ui_rebuild/STELLCODEX_SYSTEM_MAP.md
  - /root/workspace/_backups/20260304_173217_stage4_core_flows/STELLCODEX_SYSTEM_MAP.md
- sha256 `7dbe893310da3c626c900444cb6a1c80b478c2c6e28711bf69a289c9e921cdaa` count=8
  - /root/workspace/_backups/20260304_034500_v62_post_fullpack_state/handoff/stell-ai-v8-5-final-consolidation-complete-autonomy-achieved-status.md
  - /root/workspace/_backups/20260304_075500_sev0_post_fix_state/handoff/stell-ai-v8-5-final-consolidation-complete-autonomy-achieved-status.md
  - /root/workspace/_backups/20260304_080000_whatsapp_secret_active/handoff/stell-ai-v8-5-final-consolidation-complete-autonomy-achieved-status.md
  - /root/workspace/handoff/backups/session_20260304_130658/backups/session_20260304_130658/stell-ai-v8-5-final-consolidation-complete-autonomy-achieved-status.md
  - /root/workspace/handoff/backups/session_20260304_130658/stell-ai-v8-5-final-consolidation-complete-autonomy-achieved-status.md
- sha256 `a8b8dc14034dad0608fb28f3fa884f52f5c48adfb26e6936f7c05bef0bfa218e` count=6
  - /root/stell/genois/05_whatsapp_ingest/20260301_194131_610101__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194132_786505__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194133_713893__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194135_789933__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194154_329609__event.json
- sha256 `3e8e23748865f48e4cd52da63d9ccb7ac0c4fecc6ca4fd77994c7c582c24d918` count=6
  - /root/stell/genois/05_whatsapp_ingest/20260301_194131_761990__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194132_577875__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194133_419027__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194134_880569__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194155_808693__event.json
- sha256 `f258d05bc3d6bf918250c2cfceb352a3c93a55e6b048f08c79ccf2f928c50d93` count=6
  - /root/stell/genois/05_whatsapp_ingest/20260301_194240_507827__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194240_915041__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194241_600209__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194242_433685__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194246_709766__event.json
- sha256 `fdb53e1dec9c592de2d3a62f2ae65e03426fad22d5b38f43eab5fc9a5b0a347f` count=5
  - /root/stell/genois/05_whatsapp_ingest/20260301_194239_420173__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194240_194630__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194241_012897__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194242_038359__event.json
  - /root/stell/genois/05_whatsapp_ingest/20260301_194759_761275__event.json
- sha256 `1b6840ae4fb926e6c5b8d7b28e936a7c1663fb953cd4e33356474c86dad70942` count=5
  - /root/workspace/_backups/20260304_033000_v62_fullpack_complete/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_034500_v62_post_fullpack_state/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_074000_sev0_triple_fix/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_075500_sev0_post_fix_state/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_080000_whatsapp_secret_active/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md
- sha256 `aafd2666229e36947cad9b4c291060745f20493948598cf291794740f9d76239` count=4
  - /root/stellcodex_output/evidence/smoke_20260306_160035/smoke/status_last.json
  - /root/stellcodex_output/evidence/smoke_20260306_162811/smoke/status_last.json
  - /root/stellcodex_output/evidence/smoke_retry_20260306_160338/smoke/status_last.json
  - /root/stellcodex_output/evidence/smoke_retry_20260306_160445/smoke/status_last.json
- sha256 `dc13fae631ee088c36f3be8f5209cb6d9ed93f1626f3678b5357a4b7e8cb4dd2` count=4
  - /root/workspace/_backups/20260304_022800_ai_engine_ssot_guard/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_024921_gemini_fix_state/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_backups/20260304_225931_ui_ai_megafix/snapshots/knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md
  - /root/workspace/_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md
- sha256 `a0fad2d4acffa560a1f919228516afe09e66d6ebdee56a91e0e2e43dbf8e1331` count=4
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070400/storage_key_grep.txt
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070400/storage_key_grep_after_upload.txt
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070626/storage_key_grep.txt
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070759/storage_key_grep.txt
- sha256 `e41656eb2ba6c6293bf6dd928e5a88cdbc50535cab661c1969e0f598e497ed62` count=4
  - /var/www/stellcodex/evidence/v6_exec_check_20260226_233407/upload.json
  - /var/www/stellcodex/evidence/v6_exec_followup_20260226_233733/upload_attempt_body.txt
  - /var/www/stellcodex/evidence/v6_fix_04_share_contract_20260227_003420/expire.json
  - /var/www/stellcodex/evidence/v6_fix_04_share_contract_20260227_003420/revoke_before.json
- sha256 `98efee72e56f11192644d690787ce4606673437568066fee9670e369b37416a0` count=3
  - /root/stellcodex_output/evidence/smoke_20260306_162811/smoke/share_expired_410.json
  - /root/stellcodex_output/evidence/smoke_retry_20260306_160445/smoke/share_expired_410.json
  - /var/www/stellcodex/evidence/v6_fix_04_share_contract_20260227_003753/expire.json
- sha256 `e14516c02093ef128065fb54d2525fb22a91cafa4be506176c280f3f48f1e411` count=3
  - /root/workspace/_backups/20260304_034500_v62_post_fullpack_state/handoff/stell-judge-status.md
  - /root/workspace/_backups/20260304_075500_sev0_post_fix_state/handoff/stell-judge-status.md
  - /root/workspace/_backups/20260304_080000_whatsapp_secret_active/handoff/stell-judge-status.md
- sha256 `b7c3490c6d8114cc2f73375f4c8a555cc791111bf084b89fd0fe63efcf3f03f6` count=3
  - /root/workspace/_jobs/backups/20260305_134618/stellai/requirements.txt
  - /root/workspace/_jobs/backups/20260305_134720/stellai/requirements.txt
  - /root/workspace/ops/stellai/requirements.txt
- sha256 `73fd6fccdd802c419a6b2d983d6c3173b7da97558ac4b589edec2dfe443db9ad` count=3
  - /root/workspace/stellcodex_v7/backend/.pytest_cache/README.md
  - /var/www/stellcodex/.pytest_cache/README.md
  - /var/www/stellcodex/backend/.pytest_cache/README.md
- sha256 `c11e3f4837efde2441e23a7b9da02131f53bf59fddeb7147c4ab81afe400460f` count=3
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070400/upload_status.txt
  - /var/www/stellcodex/evidence/recent_files_fix_20260227_070759/upload_status.txt
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_080236/view_route_status.txt
- sha256 `5b4769f7a5c11a6953ff72768b8394abc8b909de5670a3a62052c9f539b359d9` count=3
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_075526/curl_guest.json
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_075601/curl_guest.json
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_080236/curl_guest.json
- sha256 `61444db1c3ccfa49d943f01d42d65a85de5938171cf69a1e3ea4677184ff95ad` count=3
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_075526/leak_check.txt
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_075601/leak_check.txt
  - /var/www/stellcodex/evidence/ui_viewer_fix_20260227_080236/leak_check.txt
- sha256 `9ac3754eba1fd9706053855d7a70376080ac3376979894cbc2effe645bd030ec` count=3
  - /var/www/stellcodex/evidence/v6_exec_followup_20260226_233733/share1_resolve_after.json
  - /var/www/stellcodex/evidence/v6_exec_followup_20260226_233733/share1_resolve_before.json
  - /var/www/stellcodex/evidence/v6_exec_followup_20260226_233733/share2_resolve_expired.json
- sha256 `a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288` count=3
  - /var/www/stellcodex/evidence/v6_fix_03_v6_data_model_migration_20260227_002737/health.json
  - /var/www/stellcodex/evidence/v6_fix_04_share_contract_20260227_003420/revoke_response.json
  - /var/www/stellcodex/evidence/v6_fix_04_share_contract_20260227_003753/revoke_response.json

## Recommended Actions

- Keep `_truth` files authoritative for STELLCODEX core governance and master prompt.
- Keep `/root/stell/prompts/system/stell-core.md` as channel-specific identity for webhook/assistant stack.
- Archive V6 constitutional docs and manuals copies under legacy with explicit superseded notes.
- Remove runtime ambiguity by deprecating `/root/stell/webhook_main.py` and keeping `/root/stell/webhook/main.py`.
- Keep fallback prompt literals synchronized with `prompt_templates.json` and fail CI on unauthorized template drift.
