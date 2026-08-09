from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler to return a standardized JSON error
    without leaking internal stack traces.
    """
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        }
    )
