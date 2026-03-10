# Frontend Deploy Bridge

The workspace repository keeps the STELLCODEX frontend source as a source-only
tree under `frontend/`.

The live server currently runs a full Next.js application from:

- `/var/www/stellcodex/frontend`

The live tree keeps its deploy-specific files outside the workspace source:

- `package.json`
- `node_modules/`
- `.next/`
- `next.config.*`
- environment files

## Source mapping

Workspace source:

- `frontend/app`
- `frontend/components`
- `frontend/content`
- `frontend/context`
- `frontend/data`
- `frontend/lib`
- `frontend/security`
- `frontend/services`
- `frontend/types`

Live deploy source target:

- `/var/www/stellcodex/frontend/src/...`

## Safe update rule

When publishing the latest UI:

1. Back up `/var/www/stellcodex/frontend/src`
2. Sync the workspace frontend source tree into `/var/www/stellcodex/frontend/src`
3. Run a low-load `npm run build`
4. Restart `pm2` process `stellcodex-next`
5. Run lightweight smoke checks

Do not overwrite deploy-only files in the live root unless the deployment
metadata itself is being intentionally changed.
