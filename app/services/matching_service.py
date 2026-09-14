from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.matching.skill_extractor import extract_skills
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.matching import MatchResponse


class MatchResourceNotFoundError(Exception):
    """Raised when an owned resume or job cannot be found."""


class ResumeNotReadyError(Exception):
    """Raised when the resume has not been processed."""


class NoSkillsDetectedError(Exception):
    """Raised when no recognizable skills are found."""


class MatchingStorageError(Exception):
    """Raised when matching data cannot be retrieved."""


class MatchingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.resumes = ResumeRepository(db)
        self.jobs = JobRepository(db)

    def analyze(
        self,
        user_id: int,
        resume_id: int,
        job_id: int,
    ) -> MatchResponse:
        try:
            resume = self.resumes.get_by_id_and_user(
                resume_id=resume_id,
                user_id=user_id,
            )

            job = self.jobs.get_by_id_and_user(
                job_id=job_id,
                user_id=user_id,
            )

        except SQLAlchemyError as exc:
            raise MatchingStorageError(
                "Matching data could not be retrieved"
            ) from exc

        if resume is None:
            raise MatchResourceNotFoundError(
                "Resume not found"
            )

        if job is None:
            raise MatchResourceNotFoundError(
                "Job not found"
            )

        if (
            resume.processing_status != "PROCESSED"
            or not resume.extracted_text
        ):
            raise ResumeNotReadyError(
                "Resume has not been processed"
            )

        resume_skills = extract_skills(
            resume.extracted_text
        )

        job_text = (
            f"{job.job_title}\n"
            f"{job.job_description}"
        )

        required_skills = extract_skills(job_text)

        if not resume_skills:
            raise NoSkillsDetectedError(
                "No recognizable skills were found in the resume"
            )

        if not required_skills:
            raise NoSkillsDetectedError(
                "No recognizable skills were found in the job description"
            )

        resume_skill_set = set(resume_skills)
        required_skill_set = set(required_skills)

        matched_skills = sorted(
            resume_skill_set & required_skill_set,
            key=str.casefold,
        )

        missing_skills = sorted(
            required_skill_set - resume_skill_set,
            key=str.casefold,
        )

        additional_resume_skills = sorted(
            resume_skill_set - required_skill_set,
            key=str.casefold,
        )

        match_score = round(
            (
                len(matched_skills)
                / len(required_skills)
            )
            * 100,
            2,
        )

        return MatchResponse(
            resume_id=resume.id,
            job_id=job.id,
            match_score=match_score,
            required_skill_count=len(required_skills),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            additional_resume_skills=additional_resume_skills,
            resume_skills=resume_skills,
            required_skills=required_skills,
        )