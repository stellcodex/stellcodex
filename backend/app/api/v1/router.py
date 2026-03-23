from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.bootstrap import router as bootstrap_router
from app.api.v1.routes.me import router as me_router
from app.api.v1.routes.admin import router as admin_router
from app.api.v1.routes.files import router as files_router
from app.api.v1.routes.explorer import router as explorer_router
from app.api.v1.routes.formats import router as formats_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.jobs import router as jobs_router
from app.api.v1.routes.ownership import router as ownership_router
from app.api.v1.routes.orchestrator import router as orchestrator_router
from app.api.v1.routes.approvals import router as approvals_router
from app.api.v1.routes.product import router as product_router
from app.api.v1.routes.share import router as share_router
from app.api.v1.routes.dfm import router as dfm_router
from app.api.v1.routes.library import router as library_router
from app.api.v1.routes.platform_contract import router as platform_contract_router
from app.api.v1.routes.quotes import router as quotes_router
from app.api.v1.routes.stell import router as stell_router
from app.api.v1.routes.stell_ai import router as stell_ai_router
from app.api.v1.routes.internal_runtime import router as internal_runtime_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(formats_router, tags=["formats"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(bootstrap_router, tags=["bootstrap"])
api_router.include_router(me_router, tags=["me"])
api_router.include_router(platform_contract_router, tags=["platform-contract"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(explorer_router, tags=["explorer"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(ownership_router, tags=["ownership"])
api_router.include_router(orchestrator_router, tags=["orchestrator"])
api_router.include_router(approvals_router, tags=["approvals"])
api_router.include_router(dfm_router, tags=["dfm"])
api_router.include_router(product_router, tags=["product"])
api_router.include_router(share_router, tags=["share"])
api_router.include_router(library_router, tags=["library"])
api_router.include_router(quotes_router, prefix="/quotes", tags=["quotes"])
api_router.include_router(admin_router, tags=["admin"])
api_router.include_router(stell_router, tags=["stell"])
api_router.include_router(stell_ai_router, tags=["stell-ai"])
api_router.include_router(internal_runtime_router, tags=["internal-runtime"])
