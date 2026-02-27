# Phase-2 Evidence: ChatGPT-like Layout + Viewer/Share UX (UI only)

## Scope
- Branch: `feat/ui-viewer-sprint-2`
- Backend/API contract changes: **None**
- Focus: Frontend layout, upload-to-view flow, viewer UX polish, public share UX, mobile drawer behavior.

## Changed Files
- `frontend/src/app/page.tsx`
- `frontend/src/components/upload/UploadDrop.tsx`
- `frontend/src/app/(public)/upload/page.tsx`
- `frontend/src/app/(viewer)/layout.tsx`
- `frontend/src/app/(viewer)/view/[scx_id]/page.tsx`
- `frontend/src/app/(viewer)/share/[token]/page.tsx`
- `frontend/src/components/layout/SiteHeader.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/public/site.webmanifest`
- `frontend/public/manifest.webmanifest`
- `frontend/public/stellcodex-logo.png`

## Product Flow (Implemented)
1. `/` is now a ChatGPT-like minimal workspace:
   - Left sidebar (desktop), mobile drawer.
   - Center composite panel with clear upload CTA and drag/drop.
   - Optional recent uploads list from `listFiles()`.
2. Upload flow:
   - `UploadDrop` now does `uploadDirect(file)` and polls `getFileStatus(file_id)`.
   - On `succeeded/ready`, UI shows `Viewer’a yönlendiriliyor...` and triggers redirect.
   - Redirect target is `/view/{scx_id}`.
3. Viewer route `/view/{scx_id}`:
   - Existing 1920-count fix preserved (`Parts: manifest.part_count`, assembly tree from manifest state).
   - Part operations remain disabled when mapping unavailable.
   - Mobile panel behavior updated to overlay drawers (Assembly / Tools).
4. Share route `/share/{token}`:
   - Read-only shared viewer frame.
   - No upload action.
   - Invalid/expired token handled with clear error and return link.

## Mobile Fix Summary
- Home page uses full-height shell (`100dvh`) with one internal scroll container.
- Viewer layout switched to no-footer frame and internal scroll container.
- Viewer left/right controls moved to mobile overlay drawers.
- Header kept compact on mobile (logo-only text behavior).

## Branding / Favicon
- Header logo switched to image from `src/app/gorsel/logo.png`.
- Public logo copy added: `frontend/public/stellcodex-logo.png`.
- Metadata icons updated to include the logo-based icon.
- `site.webmanifest` and `manifest.webmanifest` updated to include logo icon entry.

## Build Evidence
Command:
```bash
cd /var/www/stellcodex/frontend
npm run build
```
Result: **PASS**
- Next.js production build completed successfully.
- Static/dynamic routes generated without TypeScript errors.

## Manual Acceptance Checklist
- [ ] `/` opens ChatGPT-like minimal layout; mobile has no blank side gaps.
- [ ] Upload from `/` completes and auto-redirects to `/view/{scx_id}`.
- [ ] Viewer shows `Parts: {partCount}` (manifest-based), not GLTF traverse count.
- [ ] If mapping unavailable, part operations stay disabled.
- [ ] Share creation in viewer returns `/share/{token}` and copy works.
- [ ] `/share/{token}` opens read-only view; invalid/expired token shows clear error.
