"""Stockage des fichiers (CV importés, photos). Les noms sont générés (uuid) : pas de traversée de chemin possible."""
import uuid
from pathlib import Path

from app.core.config import settings


def _dir(sub: str) -> Path:
    p = Path(settings.upload_dir) / sub
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_bytes(sub: str, ext: str, data: bytes) -> str:
    name = f"{uuid.uuid4().hex}.{ext}"
    (_dir(sub) / name).write_bytes(data)
    return name


def path_of(sub: str, name: str) -> Path | None:
    p = _dir(sub) / Path(name).name  # .name neutralise tout "../"
    return p if p.is_file() else None


def delete(sub: str, name: str | None) -> None:
    if name:
        p = _dir(sub) / Path(name).name
        if p.is_file():
            p.unlink()
