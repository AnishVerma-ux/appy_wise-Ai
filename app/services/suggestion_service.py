from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.gemini_suggestion_generator import (
    SuggestionGenerator,
)
from app.ai.prompt_builder import build_suggestion_prompt
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.suggestion import (
    SuggestionRequest,
    SuggestionResponse,
)
from app.services.matching_service import MatchingService


class SuggestionStorageError(Exception):
    """Raised when suggestion data cannot be retrieved."""


class SuggestionService:
    def __init__(
        self,
        db: Session,
        generator: SuggestionGenerator,
    ) -> None:
        self.db = db
        self.generator = generator
        self.matching = MatchingService(db)
        self.resumes = ResumeRepository(db)
        self.jobs = JobRepository(db)

    def generate_suggestions(
        self,
        user_id: int,
        suggestion_request: SuggestionRequest,
    ) -> SuggestionResponse:
        match_result = self.matching.analyze(
            user_id=user_id,
            resume_id=suggestion_request.resume_id,
            job_id=suggestion_request.job_id,
        )

        try:
            resume = self.resumes.get_by_id_and_user(
                resume_id=suggestion_request.resume_id,
                user_id=user_id,
            )

            job = self.jobs.get_by_id_and_user(
                job_id=suggestion_request.job_id,
                user_id=user_id,
            )

        except SQLAlchemyError as exc:
            raise SuggestionStorageError(
                "Suggestion data could not be retrieved"
            ) from exc

        if resume is None or job is None:
            raise SuggestionStorageError(
                "Suggestion resources became unavailable"
            )

        prompt = build_suggestion_prompt(
            resume_text=resume.extracted_text or "",
            job_title=job.job_title,
            job_description=job.job_description,
            match_score=match_result.match_score,
            required_skill_count=(
                match_result.required_skill_count
            ),
            matched_skills=match_result.matched_skills,
            missing_skills=match_result.missing_skills,
        )

        generated_content = self.generator.generate(prompt)

        return SuggestionResponse(
            resume_id=resume.id,
            job_id=job.id,
            match_score=match_result.match_score,
            required_skill_count=(
                match_result.required_skill_count
            ),
            matched_skills=match_result.matched_skills,
            missing_skills=match_result.missing_skills,
            provider=self.generator.provider,
            model=self.generator.model,
            **generated_content.model_dump(),
        )