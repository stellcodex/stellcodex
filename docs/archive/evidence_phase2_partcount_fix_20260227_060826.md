# Phase-2 Evidence: Part Count Source Switch (GLTF Traverse -> Manifest)

## Scope
- Branch: `feat/ui-viewer-sprint-2`
- Goal: Close 35/1920 counting bug by removing GLTF traverse node list from assembly UI and using manifest data (`part_count`, `assembly_tree`).

## Root Cause (Confirmed)
- `frontend/src/components/viewer/ThreeViewer.tsx` generated UI node list via `scene.traverse` and `nodes.push({ id: obj.uuid, ... })`.
- `frontend/src/app/(viewer)/view/[scx_id]/page.tsx` consumed that list as assembly tree.
- Result: mesh/Object3D count was presented as "parts" (inflated count e.g. 1920).

## Manifest Reality (Runtime Probe)
- Endpoint used: `/api/v1/files/{file_id}/manifest`
- Probe result from runtime upload:
  - `file_id=scx_cae72964-7388-4b3e-a598-7197b9a00790`
  - `part_count=null`
  - `assembly_tree_len=0`
- Conclusion: current runtime sample has no usable assembly mapping payload; UI must not fake part operations from GLTF nodes.

## Code Changes
- `frontend/src/app/(viewer)/view/[scx_id]/page.tsx`
  - Added `getFileManifest(fileId)` to load flow.
  - Replaced old `nodes/filteredNodes` (from ThreeViewer traverse) with manifest-driven state:
    - `assemblyTree = manifest.assembly_tree ?? []`
    - `partCount = manifest.part_count ?? 0`
  - Left panel now shows `Parts: {partCount}`.
  - If `assembly_tree` is empty, shows:
    - `Assembly tree not available for this model yet.`
  - Selection/Hide/Show/Isolate controls are disabled when mapping is unavailable.
  - Removed dependency on `ThreeViewer` traverse nodes for assembly panel rendering.

- `frontend/src/components/viewer/ThreeViewer.tsx`
  - Added `EMIT_TRAVERSE_NODES = false`.
  - Traverse-to-`onNodes` emission now gated behind debug flag and callback presence.
  - Render/bounds/interactions remain intact.

- `frontend/src/services/api.ts`
  - Added manifest-related types:
    - `AssemblyTreeNode`
    - `FileManifest`
  - Typed `getFileManifest(fileId): Promise<FileManifest>`.

## Build / Validation Evidence
- Command:
  - `cd /var/www/stellcodex/frontend && npm run build`
- Result: **PASS**
  - Next.js production build completed successfully.

## Manual Verification Checklist
1. Open viewer page for any 3D file: `/view/{file_id}`.
2. Confirm left panel part label comes from manifest (`Parts: X`) and is not derived from GLTF traverse.
3. If manifest `assembly_tree` is empty, confirm info box appears:
   - `Assembly tree not available for this model yet.`
4. Confirm part operation buttons (`Select`, `Hide/Show`, `Isolate`) are disabled with mapping-unavailable behavior.
5. Confirm viewer still renders model and camera/display tools continue working.

## Changed Files
- `frontend/src/app/(viewer)/view/[scx_id]/page.tsx`
- `frontend/src/components/viewer/ThreeViewer.tsx`
- `frontend/src/services/api.ts`
