from __future__ import annotations

from io import BytesIO

from fastapi import UploadFile


async def extract_text_from_upload(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename or "uploaded-material"

    if filename.lower().endswith(".pdf"):
        return _extract_pdf_text(content)

    return _decode_text(content)


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page.strip() for page in pages if page.strip())
        if text:
            return text
    except Exception:
        pass

    return _decode_text(content)


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")
