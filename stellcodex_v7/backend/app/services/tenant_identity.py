from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from app.models.master_contract import Tenant


def tenant_code_for_owner(owner_sub: str) -> str:
    token = (owner_sub or "").strip() or "anonymous"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]
    return f"owner-{digest}"


def resolve_or_create_tenant_id(db: Session, owner_sub: str) -> int:
    code = tenant_code_for_owner(owner_sub)
    row = db.query(Tenant).filter(Tenant.code == code).first()
    if row is not None:
        return int(row.id)

    row = Tenant(code=code, name=f"Owner {code[-8:]}")
    db.add(row)
    db.flush()
    return int(row.id)
