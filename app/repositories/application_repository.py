from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.application_history import ApplicationHistory


class ApplicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_job(
        self,
        user_id: int,
        job_id: int,
    ) -> Application | None:
        statement = select(Application).where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )

        return self.db.scalar(statement)

    def get_by_id_and_user(
        self,
        application_id: int,
        user_id: int,
    ) -> Application | None:
        statement = select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
        )

        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Application]:
        statement = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def create(
        self,
        user_id: int,
        resume_id: int,
        job_id: int,
        match_score: Decimal | float,
        notes: str | None = None,
    ) -> Application:
        application = Application(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            status=ApplicationStatus.SAVED.value,
            match_score=match_score,
            notes=notes,
        )

        self.db.add(application)
        self.db.flush()

        initial_history = ApplicationHistory(
            application_id=application.id,
            old_status=None,
            new_status=ApplicationStatus.SAVED.value,
        )

        self.db.add(initial_history)
        self.db.commit()
        self.db.refresh(application)

        return application

    def update_status(
        self,
        application: Application,
        new_status: ApplicationStatus | str,
        applied_at: datetime | None = None,
    ) -> Application:
        status_value = (
            new_status.value
            if isinstance(new_status, ApplicationStatus)
            else new_status
        )

        old_status = (
            application.status.value
            if isinstance(application.status, ApplicationStatus)
            else application.status
        )

        application.status = status_value
        application.applied_at = applied_at

        history = ApplicationHistory(
            application_id=application.id,
            old_status=old_status,
            new_status=status_value,
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(application)

        return application

    def update_notes(
        self,
        application: Application,
        notes: str | None,
    ) -> Application:
        application.notes = notes

        self.db.commit()
        self.db.refresh(application)

        return application

    def list_history(
        self,
        application_id: int,
    ) -> list[ApplicationHistory]:
        statement = (
            select(ApplicationHistory)
            .where(
                ApplicationHistory.application_id
                == application_id
            )
            .order_by(
                ApplicationHistory.changed_at.asc(),
                ApplicationHistory.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def delete(
        self,
        application: Application,
    ) -> None:
        self.db.delete(application)
        self.db.commit()