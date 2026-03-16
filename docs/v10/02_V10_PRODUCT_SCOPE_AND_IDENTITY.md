# STELLCODEX V10 Product Scope And Identity

- Document ID: `V10-02`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Product identity, boundaries, modules, and non-goals`
- Replacement rule: `Product identity changes require a new V10 revision and aligned updates to all surface contracts.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Product Definition

STELLCODEX is a deterministic manufacturing decision platform.

The platform accepts engineering artifacts, processes them through a controlled pipeline, and produces:
- assembly metadata
- deterministic manufacturing decisions
- DFM findings
- secure viewer outputs
- shareable evidence artifacts

## Core Modules

- Orchestrator
- State machine enforcement
- Deterministic rule engine
- DFM risk engine
- Secure share engine
- Audit and evidence operations layer

## Included Modules

- Viewer
- Shares
- Dashboard and admin surfaces
- STELL-AI assistant and reporting helpers

These are modules of the same platform, not separate products.

## Locked Non-Goals

STELLCODEX is not:
- a general AI shell
- a CAD editing product
- a family of separate products split across multiple brand identities

AI may support planning, reporting, and operator assistance, but it may not invent manufacturing decisions outside the deterministic rule system.
