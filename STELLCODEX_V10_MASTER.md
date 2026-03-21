# STELLCODEX V10 MASTER

## A. STATUS

- Status: Active Canonical Source of Truth
- Date: 2026-03-21
- Replaces prior active reference set for ongoing implementation decisions

## B. PRODUCT IDENTITY

STELLCODEX is a deterministic manufacturing decision platform.

Viewer is a module, not the product.
Share is a module, not the product.
Assistant is a supporting module, not the product.

Product core remains workflow, rules, risk, and controlled delivery.

## C. ACTIVE ARCHITECTURE RULE

Frontend, backend, worker, database, storage, and queue remain one coordinated product stack.

No random product split.
No fake surfaces.
No runtime hot patch as product truth.
Repo state is authoritative.

## D. PUBLIC CONTRACT RULES

Public file identity = file_id only.
Share identity = token only.

Forbidden in user-facing UI and API surfaces:
- storage_key
- object_key
- bucket
- provider URLs
- filesystem paths
- revision_id as public identity
- raw stack traces
- internal provider/model labels

## E. UI LOCK

V10 UI freeze is accepted.
Unified white minimal interface is the accepted production UI.
Single app shell is mandatory.
Admin is role-based visibility inside the same shell.
No separate admin product surface.
No fake buttons for unsupported backend actions.
Backend-backed actions only.
Unsupported actions must fail closed.

## F. VIEWER LOCK

Viewer must rely on assembly_meta or equivalent repo-truth metadata.
No assembly_meta => fail-closed.
No fake degraded viewer state.
Part and component identity must not be derived from raw mesh or render-node counts.
Selection and visibility must follow occurrence and component truth when metadata exists.

## G. SHARE LOCK

Public share uses the token route.
Expired, revoked, and invalid states must be terminal and explicit.
No internal navigation leakage.
No internal metadata leakage.
Public page remains minimal.

## H. CURRENT ACCEPTED UI FREEZE RECORD

- Accepted freeze commit: `a177eb64068ab86dc4490615c62454c8038b2bc8`
- Accepted freeze tag: `v10-ui-freeze-20260321`
- Accepted live route proof summary:
  - `/dashboard`
  - `/projects`
  - `/files/{file_id}`
  - `/files/{file_id}/viewer`
  - `/viewer?id={file_id}`
  - `/shares`
  - `/admin`
  - `/s/{token}`
- UI is frozen and must not be casually reworked.

## I. KNOWN BACKEND GAPS

- recent-jobs endpoint missing
- version upload/history support missing
- any UI depending on unsupported backend must remain fail-closed

## J. IMPLEMENTATION RULE FOR FUTURE WORK

Future work continues from V10 only.
UI rework is forbidden unless a new explicit freeze-breaking task is opened.
Backend gap closure must preserve the frozen UI contract.
When backend features become available, connect them into the existing frozen UI instead of redesigning the UI.

## K. DECISION

V10 is active.
Prior versions are historical only.
Implementation decisions must follow V10 from this point onward.
