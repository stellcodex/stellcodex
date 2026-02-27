from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.api.v1.routes.share import resolve_share as resolve_share_token
from app.db.session import get_db
from app.startup import register_startup

app = FastAPI()
register_startup(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/s/{token}")
def resolve_share_short(token: str, db: Session = Depends(get_db)):
    return resolve_share_token(token=token, db=db)


@app.get("/share/{token}")
def resolve_share_alias(token: str, db: Session = Depends(get_db)):
    return resolve_share_token(token=token, db=db)
