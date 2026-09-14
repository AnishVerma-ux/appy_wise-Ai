from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.application_history import ApplicationHistory
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationHistoryResponse,
    ApplicationNotesUpdate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.services.application_service import (
    ApplicationNotFoundError,
    ApplicationService,
    ApplicationStorageError,
    DuplicateApplicationError,
    InvalidStatusTransitionError,
)
from app.services.matching_service import (
    MatchingStorageError,
    MatchResourceNotFoundError,
    NoSkillsDetectedError,
    ResumeNotReadyError,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    try:
        return ApplicationService(db).create_application(
            user_id=current_user.id,
            application_data=application_data,
        )

    except DuplicateApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except MatchResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (
        ResumeNotReadyError,
        NoSkillsDetectedError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except (
        ApplicationStorageError,
        MatchingStorageError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[ApplicationResponse],
)
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Application]:
    try:
        return ApplicationService(db).list_applications(
            user_id=current_user.id
        )

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
)
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationDetailResponse:
    try:
        return ApplicationService(db).get_application_detail(
            application_id=application_id,
            user_id=current_user.id,
        )

    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationHistoryResponse],
)
def get_application_history(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApplicationHistory]:
    try:
        return ApplicationService(db).list_history(
            application_id=application_id,
            user_id=current_user.id,
        )

    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    try:
        return ApplicationService(db).update_status(
            application_id=application_id,
            user_id=current_user.id,
            status_data=status_data,
        )

    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{application_id}/notes",
    response_model=ApplicationResponse,
)
def update_application_notes(
    application_id: int,
    notes_data: ApplicationNotesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    try:
        return ApplicationService(db).update_notes(
            application_id=application_id,
            user_id=current_user.id,
            notes_data=notes_data,
        )

    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        ApplicationService(db).delete_application(
            application_id=application_id,
            user_id=current_user.id,
        )

    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ApplicationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)