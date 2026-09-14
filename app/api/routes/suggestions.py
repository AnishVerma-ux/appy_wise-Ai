from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.gemini_suggestion_generator import (
    GeminiSuggestionGenerator,
    SuggestionGenerator,
    SuggestionProviderError,
    SuggestionProviderNotConfiguredError,
)
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.suggestion import (
    SuggestionRequest,
    SuggestionResponse,
)
from app.services.matching_service import (
    MatchingStorageError,
    MatchResourceNotFoundError,
    NoSkillsDetectedError,
    ResumeNotReadyError,
)
from app.services.suggestion_service import (
    SuggestionService,
    SuggestionStorageError,
)


router = APIRouter(
    prefix="/suggestions",
    tags=["AI Suggestions"],
)


def get_suggestion_generator() -> SuggestionGenerator:
    return GeminiSuggestionGenerator()


@router.post(
    "/generate",
    response_model=SuggestionResponse,
)
def generate_suggestions(
    suggestion_request: SuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    generator: SuggestionGenerator = Depends(
        get_suggestion_generator
    ),
) -> SuggestionResponse:
    try:
        return SuggestionService(
            db=db,
            generator=generator,
        ).generate_suggestions(
            user_id=current_user.id,
            suggestion_request=suggestion_request,
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

    except SuggestionProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except SuggestionProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except (
        MatchingStorageError,
        SuggestionStorageError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc