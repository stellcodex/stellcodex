# CANONICAL STORAGE RULES

## Purpose

This document defines the canonical storage model of the STELLCODEX ecosystem.

The storage model is strict and non-overlapping.

## Canonical Sources of Truth

### GitHub

GitHub is the canonical source of truth for:

- application code
- infrastructure code
- deployment definitions
- Dockerfiles
- compose files
- migrations
- scripts
- contracts
- tests
- runbooks
- system documentation

### Google Drive

Google Drive is the canonical source of truth for:

- backups
- memory
- evidence
- archives
- reports
- release bundles
- operational records
- historical artifacts

### Server

The server is **not** a canonical source of truth.

The server exists only as:

- runtime
- execution environment
- temporary working surface

## Non-Negotiable Rules

- Code truth must live in GitHub.
- Long-lived operational memory must live in Google Drive.
- The server must be replaceable.
- The system must be rebuildable from GitHub without trusting the previous server filesystem.
- Drive must be reattached after runtime recovery, not before code truth is restored.

## What Must Never Happen

- permanent source code only on the server
- permanent backup lineage only on the server
- memory/evidence stored only in runtime paths
- undocumented dependence on server residue
- treating local server folders as canonical archive

## Recovery Logic

When a runtime is lost:

1. recover code and runtime structure from GitHub
2. restore service availability
3. reattach Drive-managed state
4. verify health, evidence, and memory continuity

## Storage Summary

- **GitHub** = code truth
- **Google Drive** = backup/memory/evidence truth
- **Server** = disposable runtime
