# Platform App Inventory

STELLCODEX currently registers 45 application modules through the shared
marketplace catalog and per-app manifests.

Inventory sources:

- `marketplace/catalog.json`
- `backend/apps/*/app.manifest.json`

Delivery model:

- Core workflows stay in the workspace shell as dedicated surfaces.
- The full inventory is exposed through the workspace Applications catalog.
- Modules without a dedicated runner use a manifest-backed module surface.
- Root `/apps` routes redirect into the workspace shell to avoid a duplicate UI
  system.

Integrated core aliases:

- `stellview`, `stellviewer3d` -> `viewer3d`
- `stelldraw`, `stellviewer2d` -> `viewer2d`
- `stellmesh` -> `mesh2d3d`
- `stellmoldcodes` -> `moldcodes`
- `stellconvert` -> `convert`
- `stelllibrary` -> `library`
- `stelldrive`, `stellexplorer`, `stellshare`, `stellupload` -> `drive`
- `stellproject` -> `projects`
- `stellstatus` -> `status`
- `stelladmin-lite` -> `admin`

Manifest-backed modules:

- manufacturing modules not yet promoted into the shell, such as `stelldfm`,
  `stellquote`, `stellbom`, `stellnest`, `stellcut`, `stellsheet`,
  `stellcam-basic`, and `stellreport`
- simulation modules, such as `stellsim`, `stellthermal`, `stelloptimize`,
  `stelltopology`, `stellfea`, and `stellcfd`
- AI and enterprise modules, such as `stellai`, `stellvision`,
  `stellcopilot`, `stellautoplan`, `stellerp-sync`,
  `stellcompliance-pro`, `stellsecurity-pro`, and `stellenterprise-hub`

UI rules:

- Keep the suite home simple; do not mirror the full 45-module inventory on the first screen.
- Keep the sidebar focused on core surfaces and the Applications hub.
- Keep the full inventory in the Applications catalog.
- Keep all descriptions English-first and task-specific.
- Keep each module accessible through one canonical workspace route.
