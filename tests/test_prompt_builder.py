import json

from app.ai.prompt_builder import (
    MAX_JOB_DESCRIPTION_CHARACTERS,
    MAX_RESUME_CHARACTERS,
    build_suggestion_prompt,
    redact_contact_information,
)


def test_redact_contact_information() -> None:
    text = (
        "Contact anish@example.com or "
        "+91 9876543210 for information.\n"
        "Education: 2023 - 2027."
    )

    result = redact_contact_information(text)

    assert "anish@example.com" not in result
    assert "9876543210" not in result
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_PHONE]" in result

    # Date ranges must not be mistaken for phone numbers.
    assert "2023 - 2027" in result

def test_prompt_redacts_and_limits_input() -> None:
    resume_text = (
        "anish@example.com +91 9876543210 "
        + ("R" * (MAX_RESUME_CHARACTERS + 100))
    )

    job_description = (
        "J" * (MAX_JOB_DESCRIPTION_CHARACTERS + 100)
    )

    prompt = build_suggestion_prompt(
        resume_text=resume_text,
        job_title="Backend Developer",
        job_description=job_description,
        match_score=75.0,
        required_skill_count=3,
        matched_skills=["Python", "FastAPI"],
        missing_skills=["AWS"],
    )

    assert "anish@example.com" not in prompt
    assert "9876543210" not in prompt
    assert "[REDACTED_EMAIL]" in prompt
    assert "[REDACTED_PHONE]" in prompt

    serialized_context = prompt.split(
        "UNTRUSTED_CONTEXT:\n",
        maxsplit=1,
    )[1]

    context = json.loads(serialized_context)

    assert (
        len(context["resume_text"])
        == MAX_RESUME_CHARACTERS
    )

    assert (
        len(context["job_description"])
        == MAX_JOB_DESCRIPTION_CHARACTERS
    )

    assert context["resume_text"].endswith("R")
    assert context["job_description"].endswith("J")

    assert context["required_skill_count"] == 3
    assert context["analysis_date"]
    assert context["score_type"] == (
        "detected_skill_overlap_percentage"
    )