from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Import routers once they are created
from app.api.health import router as health_router
from app.api.investigate import router as investigate_router

# Import middleware
from app.middleware.error_handler import global_exception_handler
from app.middleware.security import add_security_headers

app = FastAPI(
    title=settings.app_name,
    description="TraceIQ Backend API",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)

# Middleware
@app.middleware("http")
async def security_headers_middleware(request, call_next):
    return await add_security_headers(request, call_next)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(investigate_router, prefix="/api/v1", tags=["Investigation"])

@app.on_event("startup")
async def startup_event():
    import structlog
    logger = structlog.get_logger()
    logger.info("Application starting up", env=settings.app_env, demo_mode=settings.demo_mode)
