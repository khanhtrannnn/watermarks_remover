"""File-type classification by extension + magic bytes."""

from __future__ import annotations

import os
import zipfile
from io import BytesIO

TEXT_EXTS = {".txt", ".md", ".markdown", ".csv", ".json", ".html", ".htm", ".xml", ".yaml", ".yml"}
OFFICE_EXTS = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}

_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image",
    b"\xff\xd8\xff": "image",
    b"GIF87a": "image",
    b"GIF89a": "image",
    b"BM": "image",
    b"%PDF": "pdf",
}


def _looks_like_text(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:8192]
    if b"\x00" in sample:
        return False
    control = sum(1 for b in sample if b < 9 or (13 < b < 32))
    return control / max(1, len(sample)) < 0.01


def classify(name: str, data: bytes) -> str:
    """Return one of: text, image, pdf, office, zip_unknown, unknown."""
    ext = os.path.splitext(name)[1].lower()

    for magic, kind in _MAGIC.items():
        if data.startswith(magic):
            return kind
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image"

    if data[:2] == b"PK":
        if ext in OFFICE_EXTS:
            return "office"
        try:
            with zipfile.ZipFile(BytesIO(data)) as zf:
                names = zf.namelist()
            if "[Content_Types].xml" in names or any(n.startswith("mimetype") for n in names):
                return "office"
        except zipfile.BadZipFile:
            return "unknown"
        return "zip_unknown"

    if ext in TEXT_EXTS and _looks_like_text(data):
        return "text"
    if ext in IMAGE_EXTS:
        return "image"

    if _looks_like_text(data):
        return "text"
    return "unknown"
