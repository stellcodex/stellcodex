import uuid
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

log = structlog.get_logger()

def register_exception_handlers(app):
    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):
        error_id = str(uuid.uuid4())
        log.error(
            "unhandled_exception",
            error_id=error_id,
            path=str(request.url),
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "error": {"message": "Unexpected error", "error_id": error_id},
                "meta": {},
            },
        )
