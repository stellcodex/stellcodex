from __future__ import annotations

"""Canonical STELL-AI identity strings.

Keep these strings English-first so response safety, contract tests, and
cross-channel behavior stay predictable.
"""

STELL_IDENTITY_NAME = "STELL-AI"
STELL_IDENTITY_FULL = "STELL-AI — Stellcodex Engineering Intelligence"

RUNTIME_UNAVAILABLE_TEXT = f"{STELL_IDENTITY_NAME} is temporarily unavailable."
PLANNER_UNAVAILABLE_TEXT = f"{STELL_IDENTITY_NAME} cannot reach the planning module right now."
TOOL_LAYER_UNAVAILABLE_TEXT = f"{STELL_IDENTITY_NAME} cannot reach the tool layer right now."
GENERAL_FAILURE_TEXT = f"{STELL_IDENTITY_NAME} could not complete this request right now."
ANALYSIS_UNAVAILABLE_TEXT = f"{STELL_IDENTITY_NAME} cannot reach this analysis tool right now."
RESPONSE_BLOCKED_TEXT = f"{STELL_IDENTITY_NAME} could not answer this request safely."
ENGINEERING_ASYNC_ACCEPTED_TEXT = f"{STELL_IDENTITY_NAME} started the engineering analysis job."


def stell_identity() -> str:
    return STELL_IDENTITY_FULL
