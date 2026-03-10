from __future__ import annotations

"""Runtime message classifier.

Keyword matching remains multilingual so Turkish and English prompts can route
to the same deterministic workflows, while the implementation stays documented
in English.
"""

from enum import Enum


class MessageMode(str, Enum):
    SYSTEM_STATUS = "SYSTEM_STATUS"
    ENGINEERING = "ENGINEERING"
    GENERAL_CHAT = "GENERAL_CHAT"


_SYSTEM_STATUS_HINTS = (
    "status",
    "health",
    "runtime",
    "system",
    "queue",
    "job",
    "worker",
    "uptime",
    "process",
    "service",
    "durum",
    "sistem",
    "kuyruk",
    "çalışıyor",
    "calisiyor",
    "servis",
)

_ENGINEERING_HINTS = (
    "analyze",
    "analysis",
    "engineering",
    "cad",
    "dfm",
    "mesh",
    "geometry",
    "feature",
    "step",
    "stp",
    "stl",
    "obj",
    "ply",
    "gltf",
    "glb",
    "dxf",
    "iges",
    "igs",
    "volume",
    "surface area",
    "bounding box",
    "hacim",
    "yuzey",
    "yüzey",
    "geometri",
    "analiz",
    "mühendis",
    "muhendis",
)

_IDENTITY_HINTS = (
    "sen kimsin",
    "kimsin",
    "kendini tanit",
    "kendini tanıt",
    "who are you",
    "what are you",
)


def is_identity_prompt(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(token in lowered for token in _IDENTITY_HINTS)


def detect_mode(message: str) -> MessageMode:
    lowered = str(message or "").strip().lower()
    if any(token in lowered for token in _SYSTEM_STATUS_HINTS):
        return MessageMode.SYSTEM_STATUS
    if any(token in lowered for token in _ENGINEERING_HINTS):
        return MessageMode.ENGINEERING
    return MessageMode.GENERAL_CHAT
