from __future__ import annotations

import re
from io import BytesIO

from fastapi import UploadFile


async def extract_text_from_upload(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename or "uploaded-material"

    if filename.lower().endswith(".pdf"):
        return _extract_pdf_text(content)

    return clean_extracted_text(_decode_text(content))


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page.strip() for page in pages if page.strip())
        if text:
            return clean_extracted_text(text)
    except Exception:
        pass

    return clean_extracted_text(_decode_text(content))


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def clean_extracted_text(text: str) -> str:
    """Normalize PDF/text extraction output before validation and storage."""

    safe_text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    safe_text = safe_text.replace("\x00", " ")
    safe_text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", safe_text)
    return re.sub(r"[ \t]+", " ", safe_text).strip()
