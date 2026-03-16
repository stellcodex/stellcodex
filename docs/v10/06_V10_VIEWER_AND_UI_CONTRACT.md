# STELLCODEX V10 Viewer And UI Contract

- Document ID: `V10-06`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Viewer capabilities, UI behavior, and locked non-editing rules`
- Replacement rule: `Viewer or UI contract changes must update this file and the frontend surface contract together.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Locked Viewer Principle

STELLCODEX viewers are read-only review surfaces.
They may inspect, annotate, present, and share artifacts.
They may not promise CAD editing, parametric editing, or back-to-CAD authoring.

## 3D Viewer Minimum Contract

- orbit, pan, zoom
- model tree and part visibility controls
- highlight and inspection
- render mode controls
- screenshot and presentation-safe viewing

## 2D Viewer Minimum Contract

- pan and zoom
- page or layer navigation where supported
- DXF viewing through the controlled server-side path
- no browser-side DXF source-of-truth parsing requirement

## Readiness Rule

Viewer-ready status depends on deterministic artifacts:
- valid file metadata
- preview or viewer outputs
- `assembly_meta` for assembly-aware workflows

## UI Behavior Rules

- upload and status flows must expose visible progress and errors
- share and viewer routes must not leak backend storage internals
- admin routes must be RBAC-protected
- hidden product surfaces are forbidden
