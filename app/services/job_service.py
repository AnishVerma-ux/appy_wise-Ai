from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobUpdate


class JobNotFoundError(Exception):
    """Raised when the authenticated user's job cannot be found."""


class JobStorageError(Exception):
    """Raised when a job database operation fails."""


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)

    def create_job(
        self,
        user_id: int,
        job_data: JobCreate,
    ) -> Job:
        job_url = (
            str(job_data.job_url)
            if job_data.job_url is not None
            else None
        )

        try:
            return self.jobs.create(
                user_id=user_id,
                company_name=job_data.company_name,
                job_title=job_data.job_title,
                job_description=job_data.job_description,
                location=job_data.location,
                job_url=job_url,
            )

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise JobStorageError(
                "The job could not be created"
            ) from exc

    def list_jobs(
        self,
        user_id: int,
    ) -> list[Job]:
        try:
            return self.jobs.list_by_user(user_id)

        except SQLAlchemyError as exc:
            raise JobStorageError(
                "Jobs could not be retrieved"
            ) from exc

    def get_job(
        self,
        job_id: int,
        user_id: int,
    ) -> Job:
        try:
            job = self.jobs.get_by_id_and_user(
                job_id=job_id,
                user_id=user_id,
            )

        except SQLAlchemyError as exc:
            raise JobStorageError(
                "The job could not be retrieved"
            ) from exc

        if job is None:
            raise JobNotFoundError(
                "Job not found"
            )

        return job

    def update_job(
        self,
        job_id: int,
        user_id: int,
        job_data: JobUpdate,
    ) -> Job:
        job = self.get_job(
            job_id=job_id,
            user_id=user_id,
        )

        changes = job_data.model_dump(
            exclude_unset=True
        )

        if (
            "job_url" in changes
            and changes["job_url"] is not None
        ):
            changes["job_url"] = str(
                changes["job_url"]
            )

        try:
            return self.jobs.update(
                job=job,
                changes=changes,
            )

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise JobStorageError(
                "The job could not be updated"
            ) from exc

    def delete_job(
        self,
        job_id: int,
        user_id: int,
    ) -> None:
        job = self.get_job(
            job_id=job_id,
            user_id=user_id,
        )

        try:
            self.jobs.delete(job)

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise JobStorageError(
                "The job could not be deleted"
            ) from exc