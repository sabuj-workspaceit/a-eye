from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def save_upload_file(upload_file: UploadFile, subdir: str | None = None) -> str:
    base_path = Path(settings.LOCAL_STORAGE_PATH)
    if subdir:
        base_path = base_path / subdir
    base_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}_{upload_file.filename}"
    file_path = base_path / filename

    with file_path.open("wb") as buffer:
        buffer.write(upload_file.file.read())

    return str(file_path)
