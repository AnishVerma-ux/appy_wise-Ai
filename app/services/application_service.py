from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationStatus,
)
from app.models.application_history import ApplicationHistory
from app.repositories.application_repository import (
    ApplicationRepository,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationNotesUpdate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.services.matching_service import MatchingService


ALLOWED_STATUS_TRANSITIONS = {
    ApplicationStatus.SAVED: {
        ApplicationStatus.APPLIED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.APPLIED: {
        ApplicationStatus.ONLINE_ASSESSMENT,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFERED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.ONLINE_ASSESSMENT: {
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFERED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.INTERVIEW: {
        ApplicationStatus.OFFERED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.OFFERED: {
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.WITHDRAWN: set(),
}


class DuplicateApplicationError(Exception):
    """Raised when the same job is already being tracked."""


class ApplicationNotFoundError(Exception):
    """Raised when an owned application cannot be found."""


class InvalidStatusTransitionError(Exception):
    """Raised when an application status change is invalid."""


class ApplicationStorageError(Exception):
    """Raised when application data cannot be stored."""


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.applications = ApplicationRepository(db)
        self.matching = MatchingService(db)

    def create_application(
        self,
        user_id: int,
        application_data: ApplicationCreate,
    ) -> Application:
        try:
            existing_application = (
                self.applications.get_by_user_and_job(
                    user_id=user_id,
                    job_id=application_data.job_id,
                )
            )

        except SQLAlchemyError as exc:
            raise ApplicationStorageError(
                "Application data could not be checked"
            ) from exc

        if existing_application is not None:
            raise DuplicateApplicationError(
                "An application for this job already exists"
            )

        match_result = self.matching.analyze(
            user_id=user_id,
            resume_id=application_data.resume_id,
            job_id=application_data.job_id,
        )

        try:
            return self.applications.create(
                user_id=user_id,
                job_id=application_data.job_id,
                resume_id=application_data.resume_id,
                match_score=Decimal(
                    str(match_result.match_score)
                ),
                notes=application_data.notes,
            )

        except IntegrityError as exc:
            self.db.rollback()

            raise DuplicateApplicationError(
                "An application for this job already exists"
            ) from exc

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise ApplicationStorageError(
                "The application could not be created"
            ) from exc

    def get_application(
        self,
        application_id: int,
        user_id: int,
    ) -> Application:
        try:
            application = (
                self.applications.get_by_id_and_user(
                    application_id=application_id,
                    user_id=user_id,
                )
            )

        except SQLAlchemyError as exc:
            raise ApplicationStorageError(
                "The application could not be retrieved"
            ) from exc

        if application is None:
            raise ApplicationNotFoundError(
                "Application not found"
            )

        return application

    def list_applications(
        self,
        user_id: int,
    ) -> list[Application]:
        try:
            return self.applications.list_by_user(user_id)

        except SQLAlchemyError as exc:
            raise ApplicationStorageError(
                "Applications could not be retrieved"
            ) from exc

    def get_application_detail(
        self,
        application_id: int,
        user_id: int,
    ) -> ApplicationDetailResponse:
        application = self.get_application(
            application_id=application_id,
            user_id=user_id,
        )

        history = self.list_history(
            application_id=application_id,
            user_id=user_id,
        )

        application_data = (
            ApplicationResponse
            .model_validate(application)
            .model_dump()
        )

        return ApplicationDetailResponse(
            **application_data,
            history=history,
        )

    def list_history(
        self,
        application_id: int,
        user_id: int,
    ) -> list[ApplicationHistory]:
        self.get_application(
            application_id=application_id,
            user_id=user_id,
        )

        try:
            return self.applications.list_history(
                application_id
            )

        except SQLAlchemyError as exc:
            raise ApplicationStorageError(
                "Application history could not be retrieved"
            ) from exc

    def update_status(
        self,
        application_id: int,
        user_id: int,
        status_data: ApplicationStatusUpdate,
    ) -> Application:
        application = self.get_application(
            application_id=application_id,
            user_id=user_id,
        )

        current_status = ApplicationStatus(
            application.status
        )

        new_status = status_data.status

        allowed_statuses = ALLOWED_STATUS_TRANSITIONS[
            current_status
        ]

        if new_status not in allowed_statuses:
            raise InvalidStatusTransitionError(
                f"Cannot change status from "
                f"{current_status.value} to "
                f"{new_status.value}"
            )

        applied_at = None

        if (
            new_status == ApplicationStatus.APPLIED
            and application.applied_at is None
        ):
            applied_at = datetime.now(UTC)

        try:
            return self.applications.update_status(
                application=application,
                new_status=new_status,
                applied_at=applied_at,
            )

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise ApplicationStorageError(
                "Application status could not be updated"
            ) from exc

    def update_notes(
        self,
        application_id: int,
        user_id: int,
        notes_data: ApplicationNotesUpdate,
    ) -> Application:
        application = self.get_application(
            application_id=application_id,
            user_id=user_id,
        )

        try:
            return self.applications.update_notes(
                application=application,
                notes=notes_data.notes,
            )

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise ApplicationStorageError(
                "Application notes could not be updated"
            ) from exc

    def delete_application(
        self,
        application_id: int,
        user_id: int,
    ) -> None:
        application = self.get_application(
            application_id=application_id,
            user_id=user_id,
        )

        try:
            self.applications.delete(application)

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise ApplicationStorageError(
                "The application could not be deleted"
            ) from exc