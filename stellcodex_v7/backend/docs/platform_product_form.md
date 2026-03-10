# STELLCODEX Product Form

This note records the canonical product form that sits on top of the stabilized
V7 core. It is a scope lock for implementation work; it is not a prompt or
marketing document.

See also:

- `docs/reference/engineering_pipeline_reference.md`
- `docs/reference/language_conventions.md`
- `docs/reference/platform_app_inventory.md`

## Core platform

The hidden platform layer remains shared infrastructure:

- `core/orchestrator`
- `core/engineering`
- `core/ai`
- `core/storage`
- `core/share`
- `core/event_bus`
- `core/workers`

This layer owns:

- orchestrator state machine enforcement
- artifact storage and persistence
- engineering pipeline execution
- event bus discipline
- worker compute grid
- deterministic rule engine
- knowledge engine
- share security

## Canonical product surfaces

The platform grows through a small set of top-level product surfaces. These are
the user-facing forms that should guide future module naming and integration
work:

- `StellView`: 2D/3D engineering visualization, assembly tree, preview, viewer
  preparation, and `assembly_meta` production
- `StellShare`: controlled viewing, share links, expiration, policy-based
  download control, and watermarking
- `StellDoc`: engineering document indexing, AI-assisted retrieval, notes, and
  project-linked files
- `StellMesh`: image/scan to mesh, point cloud, and reconstruction helpers
- `STELL-AI`: planning, tool orchestration, reasoning, and report narration on
  top of deterministic engineering outputs

`MoldCodes` is not a standalone platform identity. It is the manufacturing
decision engine surface that consumes geometry metrics, feature extraction, rule
evaluation, and DFM outputs.

## Suite rule

STELLCODEX is the whole product. The applications are focused surfaces inside
the product, not disconnected brands.

Experience rules:

- the entry shell stays simple and trust-building
- uploads route users into the responsible application automatically
- 3D, 2D, and document workspaces must not reuse the same crowded layout
- files, projects, and sharing remain suite-level services
- mobile or store-distributed app packages may expose one focused surface, but
  they must still map back to the same STELLCODEX platform model

## Implementation mapping

The repository currently contains extra marketplace entries and split viewer
surfaces such as `StellViewer2D`, `StellViewer3D`, and `StellMoldCodes`. Treat
these as implementation surfaces, experiments, or registry entries, not as the
canonical platform breakdown.

The canonical mapping is:

- `StellViewer2D` and `StellViewer3D` roll up under `StellView`
- share-specific screens roll up under `StellShare`
- `StellMoldCodes` rolls up under `MoldCodes`
- AI runtime modules remain under `STELL-AI`

The full registry inventory remains accessible through the workspace
Applications catalog. That catalog is an implementation inventory, not a
product identity override.

## Engineering-first build order

The platform should not prioritize chat or cosmetic surfaces ahead of the
engineering core. The locked implementation order is:

1. geometry metrics engine
2. feature extraction engine
3. manufacturing rule engine
4. DFM report generation
5. cost estimation
6. manufacturing planning
7. engineering report packaging
8. STELL-AI planner / agent / tool runtime
9. evaluator, replanner, and self-evaluation loops

This ordering preserves the V7 deterministic decision boundary:

`geometry_metrics -> feature_extraction -> rule_engine -> dfm_report -> AI`

## Guardrails

- Do not let STELL-AI become the manufacturing decision authority.
- Do not expose marketplace naming drift as canonical product identity.
- Do not treat mesh-only analysis as B-Rep-grade certainty.
- Do not bypass the shared core for app-specific shortcuts.
