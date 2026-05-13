"""
Synchronous OCR for report uploads: images via pytesseract, PDFs via pdf2image + pytesseract.

Requires system Tesseract on PATH. PDFs require Poppler (pdf2image); optional POPPLER_PATH
for Windows when Poppler is not on PATH.
"""

from __future__ import annotations

import os
from typing import List, Optional


def extract_report_text(absolute_path: str, mime_type: str) -> str:
    """
    Return UTF-8 text extracted from the file at absolute_path.
    Raises Exception on missing deps, Poppler/Tesseract errors, or unsupported MIME.
    """
    normalized = (mime_type or "").split(";")[0].strip().lower()

    if normalized == "application/pdf":
        return _extract_pdf(absolute_path)
    if normalized in ("image/png", "image/jpeg", "image/jpg"):
        return _extract_image(absolute_path)

    raise ValueError(f"Unsupported MIME for OCR: {mime_type!r}")


def _extract_image(path: str) -> str:
    from PIL import Image
    import pytesseract

    with Image.open(path) as img:
        text = pytesseract.image_to_string(img)
    return (text or "").strip()


def _extract_pdf(path: str) -> str:
    from pdf2image import convert_from_path
    import pytesseract

    poppler: Optional[str] = os.getenv("POPPLER_PATH") or None
    kwargs = {"dpi": 200}
    if poppler:
        kwargs["poppler_path"] = poppler

    pages = convert_from_path(path, **kwargs)
    parts: List[str] = []
    for page in pages:
        parts.append((pytesseract.image_to_string(page) or "").strip())
    return "\n\n".join(p for p in parts if p).strip()
