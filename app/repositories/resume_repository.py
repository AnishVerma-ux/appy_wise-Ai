from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: int,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        extracted_text: str,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text,
            processing_status="PROCESSED",
        )

        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)

        return resume

    def list_by_user(self, user_id: int) -> list[Resume]:
        statement = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_by_id_and_user(
        self,
        resume_id: int,
        user_id: int,
    ) -> Resume | None:
        statement = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )

        return self.db.scalar(statement)

    def delete(self, resume: Resume) -> None:
        self.db.delete(resume)
        self.db.commit()