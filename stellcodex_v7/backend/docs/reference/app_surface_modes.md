## App Surface Modes

STELLCODEX uses one platform shell, but not one generic application surface.

The shell should feel as simple as a single-entry assistant product, while the
actual work happens in specialized applications.

Each catalog application is assigned a `surface` contract in
`frontend/data/platformCatalog.ts`.

Surface rules:

- `catalog`: full application inventory with grouped registry cards
- `viewer3d`: large 3D stage, short action rail, model-first wording
- `viewer2d`: drawing-first stage, layer and drawing review wording
- `docviewer`: document-first stage, file status and document handoff wording
- `job`: sequential workflow for source file -> run -> progress -> output
- `configurator`: validated parameter entry plus worker output
- `records`: project-bound record editor with saved entries
- `route`: focused handoff into another live platform route

UI constraints:

- Do not reuse one generic tab runner for all application types.
- Do not create copy pages that repeat the same entry flow in multiple places.
- Do not show the same primary action twice on the same surface.
- Do let the left rail collapse so the active app gets the widest stage.
- Keep viewer actions to the minimum working set: open, share, download.
- Keep wording English-first and task-specific.
- Keep each file or app surface readable without extra repo context.
- Keep STELL-AI secondary to the active application surface.

When adding a new app:

1. Assign a `surface` in `platformCatalog.ts`.
2. Make `PlatformClient.tsx` render that surface intentionally.
3. Keep the route documented in `frontend_surface_wiring.md`.
4. Keep language audit and platform surface contract tests passing.
