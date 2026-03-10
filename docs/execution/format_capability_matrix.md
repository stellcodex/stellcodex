# STELLCODEX Format Capability Matrix

Updated: 2026-03-10 (UTC)

This document is the product-truth matrix for format handling in the hardened backend.

## Contract Rules

- Public identity remains `file_id` only.
- User-facing payloads must not expose `storage_key`, `object_key`, bucket names, provider URLs, `revision_id`, encoded locators, or parser internals.
- A format is not "supported" unless deterministic extraction is implemented and covered by tests.
- `accepted_only` means upload acceptance only. It does not imply preview, metadata extraction, geometry extraction, or DFM support.

## Support Tier Meanings

| Support tier | Meaning |
|---|---|
| `unsupported` | Rejected at the format registry layer. |
| `accepted_only` | Accepted by current repo truth, but no deterministic extraction is implemented. |
| `preview_supported` | Accepted and preview-oriented, but no deterministic engineering extraction is implemented. |
| `metadata_extracted` | Deterministic metadata extraction exists. |
| `geometry_extracted` | Deterministic geometry extraction exists. |
| `dfm_supported` | Deterministic extraction exists and baseline engineering rules run on extracted facts. |

## Real Deterministic Support

| Extension / format | Support tier | Exact implemented behavior | Exact non-supported behavior |
|---|---|---|---|
| `stl` | `dfm_supported` | `trimesh`-based mesh extraction: bbox, watertight, unique vertex count, face/triangle count, surface area, volume where determinable, deterministic mesh rules | No native CAD topology or feature-tree extraction |
| `obj` | `dfm_supported` | `trimesh`-based mesh extraction: bbox, watertight, unique vertex count, face/triangle count, surface area, volume where determinable, deterministic mesh rules | No native CAD topology or feature-tree extraction |
| `step`, `stp` | `dfm_supported` | Existing deterministic STEP parser: units, bbox, assembly hints, part/body counts, volume estimate, holes, component names, baseline deterministic rules | No native CAD kernel, no Parasolid-grade B-Rep interrogation |
| `dxf` | `dfm_supported` | `ezdxf`-based extraction: entity/layer/block/text counts, dimension-like text, title-block-like fields, bounds, units, deterministic 2D rules | No full drafting-intent reconstruction |
| `pdf` | `dfm_supported` | Deterministic baseline document extraction: page count, text, preview text, keyword/material/tolerance/process/revision mentions, deterministic document rules | No full PDF layout engine or guaranteed drawing semantics |
| `docx` | `dfm_supported` | Deterministic ZIP/XML text extraction: text, preview, keyword/material/tolerance/process/revision mentions, deterministic document rules | No full Word layout or embedded CAD parsing |

## Preview-Supported Only

| Extension / format | Support tier | Exact implemented behavior | Exact non-supported behavior |
|---|---|---|---|
| `gltf`, `glb` | `preview_supported` | Existing visual/preview pipeline remains available | No deterministic engineering extraction, no geometry extraction, no DFM support |
| `xlsx`, `pptx`, `odt`, `ods`, `odp`, `rtf`, `txt`, `csv`, `html`, `htm` | `preview_supported` | Existing document acceptance/preview path remains available | No deterministic extraction layer in this pass |
| `png`, `jpg`, `jpeg`, `webp`, `bmp`, `gif`, `tif`, `tiff` | `preview_supported` | Existing image acceptance/preview path remains available | No deterministic engineering extraction in this pass |

## Accepted Only

| Extension / format | Support tier | Exact implemented behavior | Exact non-supported behavior |
|---|---|---|---|
| `iges`, `igs` | `accepted_only` | Accepted under current repo truth | No deterministic extraction, no geometry extraction, no DFM support |
| `x_t`, `x_b` | `accepted_only` | Accepted under current repo truth | No deterministic Parasolid extraction |
| `sat`, `sab` | `accepted_only` | Accepted under current repo truth | No deterministic ACIS extraction |
| `jt`, `ifc` | `accepted_only` | Accepted under current repo truth | No deterministic extraction in this pass |
| `ply`, `3mf`, `amf`, `off`, `wrl`, `vrml`, `dae` | `accepted_only` | Accepted under current repo truth | No deterministic extraction in this pass |
| `svg` | `accepted_only` | Accepted under current repo truth | No structured SVG extraction in this pass |

## Unsupported

| Extension / format | Support tier | Exact implemented behavior | Exact non-supported behavior |
|---|---|---|---|
| `dwg` | `unsupported` | Rejected by registry | STEP/DXF export required |
| `fcstd` | `unsupported` | Rejected by registry | STEP export required |

## Exposure Rules

- Extraction results are persisted internally in `meta["extraction_result"]`.
- Existing file detail and status routes expose only safe extraction summary fields.
- Failed extraction remains explicit and fail-closed.
- Unsupported and preview-only tiers must not be described as DFM-ready.

## Verification Anchors

- Contract/no-leak coverage: `/root/workspace/stellcodex_v7/backend/tests/test_upload_contracts.py`
- Contract/no-leak coverage: `/root/workspace/stellcodex_v7/backend/tests/test_public_contract_leaks.py`
- Capability registry coverage: `/root/workspace/stellcodex_v7/backend/tests/test_format_registry_contract.py`
- Deterministic extraction coverage: `/root/workspace/stellcodex_v7/backend/tests/test_format_intelligence.py`
- Full backend suite gate: `/root/workspace/stellcodex_v7/backend/tests`
