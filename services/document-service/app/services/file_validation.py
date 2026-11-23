from io import BytesIO
from zipfile import BadZipFile, ZipFile

import hashlib
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class ValidatedFile:
    filename: str
    content_type: str
    file_size: int
    checksum: str
    content: bytes


async def validate_upload(file: UploadFile) -> ValidatedFile:
    filename = file.filename or ""

    if not filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed",
        )

    expected_content_type = ALLOWED_EXTENSIONS[extension]

    if file.content_type != expected_content_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type for the uploaded file",
        )


    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the maximum allowed size of 10 MB",
        )

    if not validate_file_signature(content, extension):
            raise HTTPException(
                status_code=400,
                detail="File content does not match the expected file type",
            )

    checksum = hashlib.sha256(content).hexdigest()

    return ValidatedFile(
        filename=filename,
        content_type=expected_content_type,
        file_size=len(content),
        checksum=checksum,
        content=content,
    )

def validate_file_signature(content: bytes, extension: str) -> bool:
    if extension == ".pdf":
        return content.startswith(b"%PDF-")

    if extension == ".docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())

                return (
                    "[Content_Types].xml" in names
                    and "word/document.xml" in names
                )
        except (BadZipFile, OSError):
            return False

    return False