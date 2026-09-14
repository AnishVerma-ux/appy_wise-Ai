from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.utils.resume_parser import (
    ResumeParsingError,
    extract_resume_text,
)


ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Protects against a compressed DOCX expanding into a very large file.
MAX_DOCX_UNCOMPRESSED_SIZE = 25 * 1024 * 1024


class UnsupportedResumeTypeError(Exception):
    """Raised when the uploaded file is not PDF or DOCX."""


class ResumeFileTooLargeError(Exception):
    """Raised when the uploaded file exceeds the size limit."""


class InvalidResumeFileError(Exception):
    """Raised when the file content does not match its extension."""


class ResumeStorageError(Exception):
    """Raised when a resume cannot be stored or deleted."""


class ResumeNotFoundError(Exception):
    """Raised when the user's resume cannot be found."""


def _validate_pdf(content: bytes) -> None:
    if b"%PDF-" not in content[:1024]:
        raise InvalidResumeFileError(
            "The uploaded file is not a valid PDF"
        )


def _validate_docx(content: bytes) -> None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            filenames = set(archive.namelist())

            required_files = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            if not required_files.issubset(filenames):
                raise InvalidResumeFileError(
                    "The uploaded file is not a valid DOCX document"
                )

            uncompressed_size = sum(
                file_info.file_size
                for file_info in archive.infolist()
            )

            if uncompressed_size > MAX_DOCX_UNCOMPRESSED_SIZE:
                raise InvalidResumeFileError(
                    "The DOCX document is too large after extraction"
                )

    except BadZipFile as exc:
        raise InvalidResumeFileError(
            "The uploaded file is not a valid DOCX document"
        ) from exc


def _validate_file_content(
    extension: str,
    content: bytes,
) -> None:
    if extension == ".pdf":
        _validate_pdf(content)

    elif extension == ".docx":
        _validate_docx(content)


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.resumes = ResumeRepository(db)

    async def upload_resume(
        self,
        user_id: int,
        uploaded_file: UploadFile,
    ) -> Resume:
        filename = (uploaded_file.filename or "").strip()

        if not filename:
            raise InvalidResumeFileError(
                "The uploaded file must have a filename"
            )

        # Removes paths such as C:\fakepath\resume.pdf.
        original_filename = (
            filename.replace("\\", "/").split("/")[-1]
        )

        if len(original_filename) > 255:
            raise InvalidResumeFileError(
                "The filename must not exceed 255 characters"
            )

        extension = Path(original_filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise UnsupportedResumeTypeError(
                "Only PDF and DOCX resumes are supported"
            )

        try:
            content = await uploaded_file.read(
                settings.max_resume_size_bytes + 1
            )
        finally:
            await uploaded_file.close()

        if not content:
            raise InvalidResumeFileError(
                "The uploaded file is empty"
            )

        if len(content) > settings.max_resume_size_bytes:
            raise ResumeFileTooLargeError(
                "Resume size must not exceed 5 MB"
            )

        _validate_file_content(
            extension=extension,
            content=content,
        )

        stored_filename = f"{uuid4().hex}{extension}"

        relative_path = Path(str(user_id)) / stored_filename

        upload_root = settings.resume_upload_dir.resolve()

        actual_file_path = (
            upload_root / relative_path
        ).resolve()

        # Prevents the generated path from leaving the upload directory.
        if not actual_file_path.is_relative_to(upload_root):
            raise InvalidResumeFileError(
                "Invalid resume storage path"
            )

        actual_file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            actual_file_path.write_bytes(content)

            extracted_text = extract_resume_text(
                file_path=actual_file_path,
                file_type=extension,
            )

            return self.resumes.create(
                user_id=user_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=relative_path.as_posix(),
                file_type=extension.lstrip("."),
                file_size=len(content),
                extracted_text=extracted_text,
            )

        except ResumeParsingError:
            actual_file_path.unlink(missing_ok=True)
            raise

        except (OSError, SQLAlchemyError) as exc:
            self.db.rollback()
            actual_file_path.unlink(missing_ok=True)

            raise ResumeStorageError(
                "The resume could not be stored"
            ) from exc

    def list_resumes(
        self,
        user_id: int,
    ) -> list[Resume]:
        return self.resumes.list_by_user(user_id)

    def get_resume(
        self,
        resume_id: int,
        user_id: int,
    ) -> Resume:
        resume = self.resumes.get_by_id_and_user(
            resume_id=resume_id,
            user_id=user_id,
        )

        if resume is None:
            raise ResumeNotFoundError(
                "Resume not found"
            )

        return resume

    def delete_resume(
        self,
        resume_id: int,
        user_id: int,
    ) -> None:
        resume = self.get_resume(
            resume_id=resume_id,
            user_id=user_id,
        )

        upload_root = settings.resume_upload_dir.resolve()

        actual_file_path = (
            upload_root / resume.file_path
        ).resolve()

        if not actual_file_path.is_relative_to(upload_root):
            raise ResumeStorageError(
                "Invalid resume storage path"
            )

        try:
            actual_file_path.unlink(missing_ok=True)
            self.resumes.delete(resume)

        except (OSError, SQLAlchemyError) as exc:
            self.db.rollback()

            raise ResumeStorageError(
                "The resume could not be deleted"
            ) from exc