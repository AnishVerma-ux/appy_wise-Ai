from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.matching import (
    MatchRequest,
    MatchResponse,
)
from app.services.matching_service import (
    MatchingService,
    MatchingStorageError,
    MatchResourceNotFoundError,
    NoSkillsDetectedError,
    ResumeNotReadyError,
)


router = APIRouter(
    prefix="/matching",
    tags=["Matching"],
)


@router.post(
    "/analyze",
    response_model=MatchResponse,
)
def analyze_resume_for_job(
    match_request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchResponse:
    try:
        return MatchingService(db).analyze(
            user_id=current_user.id,
            resume_id=match_request.resume_id,
            job_id=match_request.job_id,
        )

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

    except MatchingStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc