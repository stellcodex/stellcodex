from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.files import router as files_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.jobs import router as jobs_router
from app.api.v1.routes.product import router as product_router
from app.api.v1.routes.share import router as share_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(product_router, tags=["product"])
api_router.include_router(share_router, prefix="/share", tags=["share"])
