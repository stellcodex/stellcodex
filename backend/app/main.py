from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.api.v1.routes.health import health as api_health
from app.api.v1.routes.share import resolve_share as resolve_share_token
from app.db.session import get_db
from app.startup import register_startup

app = FastAPI()
register_startup(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
def root_health():
    return api_health()


@app.get("/stell/health", include_in_schema=False)
def root_stell_health():
    return {"status": "ok", "service": "stell"}


@app.get("/s/{token}")
def resolve_share_short(token: str, db: Session = Depends(get_db)):
    return resolve_share_token(token=token, db=db)


@app.get("/share/{token}")
def resolve_share_alias(token: str, db: Session = Depends(get_db)):
    return resolve_share_token(token=token, db=db)


@app.api_route("/stell-ai/agents/run", methods=["POST", "OPTIONS"], include_in_schema=False)
def compat_stell_ai_agents_run(request: Request):
    target = "/api/v1/stell-ai/agents/run"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(url=target, status_code=307)
