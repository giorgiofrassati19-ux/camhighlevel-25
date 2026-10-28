import os, uuid, shutil
from .config import settings

def _ensure_dir():
    os.makedirs(settings.local_storage_dir, exist_ok=True)

async def save_upload(file_bytes: bytes, filename: str) -> str:
    """Enregistre un fichier et renvoie sa clé (chemin relatif)."""
    _ensure_dir()
    ext = os.path.splitext(filename)[1] or ".bin"
    key = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.local_storage_dir, key)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return key

def public_url(key: str) -> str:
    if settings.storage == "s3":
        return f"{settings.s3_public_base.rstrip('/')}/{key}"
    return f"{settings.app_base_url.rstrip('/')}/files/{key}"