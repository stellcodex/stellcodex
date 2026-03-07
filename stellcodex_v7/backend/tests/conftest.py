"""
conftest.py — pre-seed required env vars before any test module is imported.

pydantic BaseSettings calls get_settings() at module-level import time in
several app modules. The required vars (DATABASE_URL, JWT_SECRET) must be
present in os.environ before those imports happen. pytest loads conftest.py
before collecting/importing test modules, so this is the correct place.
"""
import os

_TEST_DEFAULTS = {
    # Required by pydantic BaseSettings field validation
    "DATABASE_URL": "postgresql://test:test@localhost:5432/test_stellcodex",
    # Required by _ensure_jwt_secret model_validator (min_length=32)
    "JWT_SECRET": "test-secret-key-for-unit-tests-only-32chars!!",
}

for _key, _val in _TEST_DEFAULTS.items():
    os.environ.setdefault(_key, _val)
