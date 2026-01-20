from __future__ import annotations

import os
import uuid
from typing import Tuple

from app.core.settings import settings

def ensure_dirs():
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)

def save_local_file(content: bytes, filename: str) -> Tuple[str, str]:
    ensure_dirs()
    ext = os.path.splitext(filename)[1].lower() or ".bin"
    asset_id = uuid.uuid4().hex
    path = os.path.join(settings.STORAGE_LOCAL_DIR, f"{asset_id}{ext}")
    with open(path, "wb") as f:
        f.write(content)
    return asset_id, path

def get_local_path(asset_id_or_path: str) -> str:
    """Return an absolute path for a stored asset.

    Historical versions stored either:
    - asset_id (uuid hex) in DB, or
    - an absolute path in DB.

    This function supports both for backward compatibility.
    """
    ensure_dirs()

    s = (asset_id_or_path or "").strip()
    if not s:
        raise FileNotFoundError("<empty>")

    # If it's already an existing file path, return it.
    if os.path.isabs(s) and os.path.exists(s):
        return s

    # If it's a file inside the storage dir (relative), use it.
    candidate = os.path.join(settings.STORAGE_LOCAL_DIR, s)
    if os.path.exists(candidate):
        return candidate

    # Otherwise treat it as asset_id prefix.
    for fn in os.listdir(settings.STORAGE_LOCAL_DIR):
        if fn.startswith(s):
            return os.path.join(settings.STORAGE_LOCAL_DIR, fn)
    raise FileNotFoundError(s)
