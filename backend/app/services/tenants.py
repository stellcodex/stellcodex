from __future__ import annotations

from hashlib import sha256

from sqlalchemy import text
from sqlalchemy.orm import Session


def tenant_code_for_owner(owner_sub: str) -> str:
    normalized = (owner_sub or "").strip()
    if not normalized:
        raise ValueError("owner_sub required")
    return f"owner-{sha256(normalized.encode('utf-8')).hexdigest()[:24]}"


def ensure_owner_tenant_id(db: Session, owner_sub: str) -> int:
    code = tenant_code_for_owner(owner_sub)
    row = db.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).first()
    if row is not None:
        return int(row[0])

    inserted = db.execute(
        text(
            """
            INSERT INTO tenants (code, name, created_at, updated_at)
            VALUES (:code, :name, NOW(), NOW())
            ON CONFLICT (code)
            DO UPDATE SET updated_at = EXCLUDED.updated_at
            RETURNING id
            """
        ),
        {
            "code": code,
            "name": f"Owner {code[-8:]}",
        },
    )
    return int(inserted.scalar_one())
