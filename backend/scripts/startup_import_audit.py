#!/usr/bin/env python3
"""Collect import-time third-party dependencies loaded by app.main."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/stellcodex")
os.environ.setdefault("JWT_SECRET", "change-this-secret-min-32-characters")

import app.main  # noqa: F401  pylint: disable=unused-import

third_party: set[str] = set()
for name, module in list(sys.modules.items()):
    mod_file = getattr(module, "__file__", "") or ""
    if "site-packages" in mod_file:
        third_party.add(name.split(".")[0])

for item in sorted(third_party):
    print(item)
