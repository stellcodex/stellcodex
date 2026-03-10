## App Surface Modes

STELLCODEX uses one platform shell, but not one generic application surface.

Each catalog application is assigned a `surface` contract in
`frontend/data/platformCatalog.ts`.

Surface rules:

- `viewer3d`: large 3D stage, short action rail, model-first wording
- `viewer2d`: drawing-first stage, layer and drawing review wording
- `docviewer`: document-first stage, file status and document handoff wording
- `job`: sequential workflow for source file -> run -> progress -> output
- `configurator`: validated parameter entry plus worker output
- `records`: project-bound record editor with saved entries
- `route`: focused handoff into another live platform route

UI constraints:

- Do not reuse one generic tab runner for all application types.
- Do not show the same primary action twice on the same surface.
- Keep viewer actions to the minimum working set: open, share, download.
- Keep wording English-first and task-specific.
- Keep each file or app surface readable without extra repo context.

When adding a new app:

1. Assign a `surface` in `platformCatalog.ts`.
2. Make `PlatformClient.tsx` render that surface intentionally.
3. Keep the route documented in `frontend_surface_wiring.md`.
4. Keep language audit and platform surface contract tests passing.
