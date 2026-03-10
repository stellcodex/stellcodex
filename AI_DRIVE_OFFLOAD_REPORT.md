# AI Drive Offload Report

Timestamp: 2026-03-10T13:57:00+03:00
Drive test status: PASS
Drive evidence root: `gdrive:stellcodex/evidence/executions/20260310`
Reports target root: `gdrive:stellcodex/reports/executions/20260310`
Archive policy: upload -> size verify -> record -> delete local archive/source -> verify deletion

Post-offload storage state
- Disk: `24G` available on `/root/workspace` (`56%` used)
- Inodes: `3291281` free (`12%` used)

Uploaded evidence bundles
- `preflight_schema_20260310T091237Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_schema_20260310T091237Z.tar.009bc45a78748e1db40f09fe594e34b3281ea341a6cb5ba1edf3078499b1c38a.gz` (`1486` bytes, local deleted=true)
- `preflight_contracts_20260310T091237Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_contracts_20260310T091237Z.tar.ae9023df155a6bf284595290cc2f4f4e583b9c9aa9837bf396a38fa12036fbb8.gz` (`1043` bytes, local deleted=true)
- `preflight_smoke_retry_20260310T091524Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_smoke_retry_20260310T091524Z.tar.a088d354212deb61334d590e9741b199cfad9945cbb5841176b3d4552da7ba38.gz` (`7680` bytes, local deleted=true)
- `preflight_smoke_fixed_20260310T091938Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_smoke_fixed_20260310T091938Z.tar.fcda8a497fd31ab28586ee92fe353d6c635808386ede435baa9aee06c17fe34e.gz` (`7712` bytes, local deleted=true)
- `preflight_smoke_20260310T091237Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_smoke_20260310T091237Z.tar.603d03e5ab566e653174fac1c461466d70a286b85a29557802c6b54399e47df6.gz` (`7114` bytes, local deleted=true)
- `preflight_smoke_execfix_20260310T092348Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_smoke_execfix_20260310T092348Z.tar.b4aebb91363b247ae78d60c374625c8e69cf98bdca12b29f10ae705545749511.gz` (`7832` bytes, local deleted=true)
- `preflight_backup_20260310T092634Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/preflight_backup_20260310T092634Z.tar.6d68ba1c4a07ab54a128e5816da224a5256968a12441598d8d2db9c6bd4af494.gz` (`2953053` bytes, local deleted=true)
- `release_gate_e7488ec_20260310T102037Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/release_gate_e7488ec_20260310T102037Z.tar.43e01d881c229b9dd01f1e1cc6beeb142c55dc6809e89d82cc32e7c5e933df08.gz` (`474` bytes, local deleted=true)
- `release_gate_e7488ec_env_20260310T102057Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/release_gate_e7488ec_env_20260310T102057Z.tar.e22951a3867387b4d37958fcd0b7bd633e718e9a1b637d774c22f0ad3fbac20a.gz` (`5045` bytes, local deleted=true)
- `release_gate_ab3153d_20260310T1028Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/release_gate_ab3153d_20260310T1028Z.tar.8522c4b728cb518f074d4488d8f3020a3d6111ac663752d75b3da34da15e997b.gz` (`109243` bytes, local deleted=true)
- `release_gate_ab3153d_rerun_20260310T1045Z` -> `gdrive:stellcodex/evidence/executions/20260310/archive/release_gate_ab3153d_rerun_20260310T1045Z.tar.9533054b7fed642ce21e33fe59609724adf983255c1ffcd88f032e8d26ff4f92.gz` (`110442` bytes, local deleted=true)

Verification
- All uploaded archives had exact remote size matches against local archives before deletion.
- Local evidence directories created during this execution were deleted after upload and no longer exist under `/root/workspace/evidence`.
- AI cache paths intentionally remain local:
  - `/root/workspace/_models`
  - `/root/workspace/_vector_store`
  - `/root/workspace/AI/logs`
