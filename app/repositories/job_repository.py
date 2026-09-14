from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: int,
        company_name: str,
        job_title: str,
        job_description: str,
        location: str | None,
        job_url: str | None,
    ) -> Job:
        job = Job(
            user_id=user_id,
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            location=location,
            job_url=job_url,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    def list_by_user(self, user_id: int) -> list[Job]:
        statement = (
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_by_id_and_user(
        self,
        job_id: int,
        user_id: int,
    ) -> Job | None:
        statement = select(Job).where(
            Job.id == job_id,
            Job.user_id == user_id,
        )

        return self.db.scalar(statement)

    def update(
        self,
        job: Job,
        changes: dict[str, object],
    ) -> Job:
        for field_name, field_value in changes.items():
            setattr(job, field_name, field_value)

        self.db.commit()
        self.db.refresh(job)

        return job

    def delete(self, job: Job) -> None:
        self.db.delete(job)
        self.db.commit()