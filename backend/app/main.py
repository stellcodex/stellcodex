from fastapi import FastAPI

from app.api.v1.router import api_router
from app.startup import register_startup

app = FastAPI()
register_startup(app)
app.include_router(api_router, prefix="/api/v1")
