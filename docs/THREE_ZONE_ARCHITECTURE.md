# STELLCODEX Three-Zone Architecture

## Zones

### Zone A: STELL.AI
- Purpose: primary intelligence layer.
- Scope: conversation intelligence, reasoning, synthesis, learning, AI memory, planning.
- Out of scope: infrastructure ownership and product deployment.

### Zone B: ORCHESTRA
- Purpose: execution and training operations layer.
- Scope: workers, queues, automation pipelines, watchdogs, training workflows.
- Out of scope: end-user product surface.

### Zone C: STELLCODEX
- Purpose: commercial software and platform layer.
- Scope: product applications, platform APIs, deployment infrastructure.

## Relationship
- `STELL.AI -> plans`.
- `ORCHESTRA -> executes`.
- `STELLCODEX -> delivers products`.

No zone may absorb another zone's responsibilities.

