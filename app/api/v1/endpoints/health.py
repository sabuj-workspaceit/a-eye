from fastapi import APIRouter, Response

from app.api.v1.schemas.common import APIResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"], response_model=APIResponse[dict])
async def health_check(response: Response) -> APIResponse[dict]:
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
