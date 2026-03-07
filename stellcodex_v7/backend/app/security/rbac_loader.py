from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import redis

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "security" / "rbac.policy.json"
CACHE_KEY = "rbac:policy:v1"
CACHE_TTL = 300

_memory_cache: dict[str, Any] | None = None
_memory_expiry: float = 0.0


def _redis_client() -> redis.Redis | None:
    if not settings.redis_url:
        return None
    return redis.Redis.from_url(str(settings.redis_url), decode_responses=True)


def _load_from_disk() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def get_policy() -> dict:
    global _memory_cache, _memory_expiry

    now = time.time()
    if _memory_cache and now < _memory_expiry:
        return _memory_cache

    r = _redis_client()
    if r is not None:
        cached = r.get(CACHE_KEY)
        if cached:
            policy = json.loads(cached)
            _memory_cache = policy
            _memory_expiry = now + CACHE_TTL
            return policy

    policy = _load_from_disk()
    if r is not None:
        r.setex(CACHE_KEY, CACHE_TTL, json.dumps(policy))
    _memory_cache = policy
    _memory_expiry = now + CACHE_TTL
    return policy


def permissions_for_roles(role_names: list[str]) -> list[str]:
    policy = get_policy()
    roles = {r["name"]: r.get("permissions", []) for r in policy.get("roles", [])}
    perms: set[str] = set()
    for rn in role_names:
        p = roles.get(rn, [])
        if "*" in p:
            return ["*"]
        perms.update(p)
    return sorted(perms)


def api_permissions() -> list[dict]:
    return get_policy().get("api_endpoint_permissions", [])


def ui_permissions() -> list[dict]:
    return get_policy().get("ui_prefix_permissions", [])
