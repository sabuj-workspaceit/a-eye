from fastapi import FastAPI, Response

from app.api.v1.schemas.common import APIResponse

from app.api.v1.endpoints import health
from app.api.v1.endpoints.analysis import router as analysis_router
from app.api.v1.endpoints.practitioner import router as practitioner_router
from app.core.config import settings
from app.db.base import Base, engine

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)


@app.on_event("startup")
def startup_event() -> None:
    """Ensure database tables exist before the app starts."""
    Base.metadata.create_all(bind=engine)

app.include_router(health.router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(practitioner_router, prefix="/api/v1")


@app.get("/", tags=["Root"], include_in_schema=False)
async def read_root() -> APIResponse[dict[str, str]]:
    return APIResponse(status=True, message="Success", data={"message": "Welcome to the A-EYE AI Analysis Service"})


@app.get("/health", tags=["Health"], response_model=APIResponse[dict])
async def health(response: Response) -> APIResponse[dict]:
    try:
        data = {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
        return APIResponse(status=True, message="Success", data=data)
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="Health check failed", errors={"detail": str(exc)})
