import os
from passlib.context import CryptContext

from app.db.session import SessionLocal
from app.models.user import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin():
    db = SessionLocal()

    try:
        email = os.getenv("ADMIN_EMAIL", "admin@stellcodex.com")
        password = os.getenv("ADMIN_PASSWORD", "123456")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            new_user = User(
                email=email,
                password_hash=pwd.hash(password),
                auth_provider="local",
                role="admin",
                is_active=True,
                is_suspended=False,
            )
            db.add(new_user)
            db.commit()
            print("ADMIN CREATED")
        else:
            print("ADMIN EXISTS")
    finally:
        db.close()
