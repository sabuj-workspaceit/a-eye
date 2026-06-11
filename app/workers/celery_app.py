from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "a_eye_worker",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=["app.workers.tasks"],
)
