# Frontend Surface Wiring

This reference records which frontend surfaces are active entry points and
which data sources are intentionally wired into runtime routes.

## Active entry surfaces

- `frontend/app/page.tsx`
  Purpose: redirects into the active workspace shell through
  `components/workspace/WorkspaceRedirect.tsx`.
- `frontend/components/platform/PlatformClient.tsx`
  Purpose: canonical workspace application shell for files, projects, library,
  settings, admin, applications catalog, manifest-backed modules, and runner
  views.
- `frontend/app/workspace/[workspaceId]/[[...slug]]/page.tsx`
  Purpose: canonical workspace route resolver for `/apps`, `/app/:id`, files,
  projects, admin, and viewer open routes.
- `frontend/app/(viewer)/view/[scx_id]/page.tsx`
  Purpose: canonical viewer surface for 2D and 3D file inspection.
- `frontend/app/s/[token]/page.tsx`
  Purpose: public share entry surface.

## Wired data sources

- `marketplace/catalog.json`
  Runtime path: served through `backend/app/api/v1/routes/apps.py`.
  Status: wired, not silent.
- `backend/apps/*/app.manifest.json`
  Runtime path: served through `backend/app/api/v1/routes/apps.py`.
  Status: wired into the Applications catalog and manifest-backed module pages.
- `backend/app/data/render-presets.json`
  Runtime path: feeds the generated frontend render preset data.
  Status: wired, not silent.

## UI rule

- One visible action should have one canonical button cluster per screen.
- Helper panels may explain the action, but should not duplicate the same
  controls unless the screen is in a clearly different mode.
- Root `/apps` routes must redirect into the workspace shell instead of opening
  a second UI system.
- Legacy prototype components that are not imported by active routes should be
  retired instead of left as disconnected surfaces.
