import pymupdf
from fastapi.testclient import TestClient

from app.ai.gemini_suggestion_generator import (
    SuggestionProviderError,
    SuggestionProviderNotConfiguredError,
)
from app.api.routes.suggestions import (
    get_suggestion_generator,
)
from app.main import app
from app.schemas.suggestion import SuggestionContent


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
RESUMES_URL = "/api/v1/resumes"
JOBS_URL = "/api/v1/jobs"
SUGGESTIONS_URL = "/api/v1/suggestions/generate"


class FakeSuggestionGenerator:
    provider = "fake"
    model = "test-model"

    def __init__(self) -> None:
        self.received_prompt: str | None = None

    def generate(
        self,
        prompt: str,
    ) -> SuggestionContent:
        self.received_prompt = prompt

        return SuggestionContent(
            overall_assessment=(
                "The resume matches the core backend skills."
            ),
            strengths=[
                "Python and FastAPI are present in the resume.",
                "The resume includes relational database skills.",
            ],
            resume_improvements=[
                (
                    "Describe the existing backend project "
                    "responsibilities more clearly."
                )
            ],
            learning_recommendations=[
                (
                    "Build a small AWS deployment before "
                    "claiming cloud experience."
                ),
                "Practise Redis using a caching project.",
            ],
        )


class MissingConfigurationGenerator:
    provider = "gemini"
    model = "test-model"

    def generate(
        self,
        prompt: str,
    ) -> SuggestionContent:
        raise SuggestionProviderNotConfiguredError(
            "Gemini API key is not configured"
        )


class FailingSuggestionGenerator:
    provider = "gemini"
    model = "test-model"

    def generate(
        self,
        prompt: str,
    ) -> SuggestionContent:
        raise SuggestionProviderError(
            "AI suggestion service is unavailable"
        )


def create_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)

    content = document.tobytes()
    document.close()

    return content


def register_and_login(
    client: TestClient,
    email: str,
) -> dict[str, str]:
    register_response = client.post(
        REGISTER_URL,
        json={
            "full_name": "Anish Kumar Verma",
            "email": email,
            "password": "StrongPass123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        LOGIN_URL,
        json={
            "email": email,
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }


def prepare_resources(
    client: TestClient,
    email: str = "anish@example.com",
) -> tuple[dict[str, str], int, int]:
    headers = register_and_login(client, email)

    resume_response = client.post(
        RESUMES_URL,
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                create_pdf(
                    "anish@example.com\n"
                    "+91 9876543210\n"
                    "Python FastAPI MySQL SQL Git Docker "
                    "REST API"
                ),
                "application/pdf",
            )
        },
    )

    assert resume_response.status_code == 201

    job_response = client.post(
        JOBS_URL,
        headers=headers,
        json={
            "company_name": "Example Technologies",
            "job_title": "Python Backend Developer",
            "job_description": (
                "We need Python, FastAPI, MySQL, REST APIs, "
                "Docker, AWS and Redis experience."
            ),
            "location": "Gurugram",
        },
    )

    assert job_response.status_code == 201

    return (
        headers,
        resume_response.json()["id"],
        job_response.json()["id"],
    )


def test_generate_suggestions_with_mocked_provider(
    client: TestClient,
) -> None:
    headers, resume_id, job_id = prepare_resources(
        client
    )

    fake_generator = FakeSuggestionGenerator()

    app.dependency_overrides[
        get_suggestion_generator
    ] = lambda: fake_generator

    try:
        response = client.post(
            SUGGESTIONS_URL,
            headers=headers,
            json={
                "resume_id": resume_id,
                "job_id": job_id,
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_suggestion_generator,
            None,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["resume_id"] == resume_id
    assert body["job_id"] == job_id
    assert 0 <= body["match_score"] <= 100
    assert body["provider"] == "fake"
    assert body["model"] == "test-model"
    assert body["missing_skills"] == ["AWS", "Redis"]

    assert body["overall_assessment"] == (
        "The resume matches the core backend skills."
    )

    assert len(body["strengths"]) == 2
    assert len(body["resume_improvements"]) == 1
    assert len(body["learning_recommendations"]) == 2

    assert fake_generator.received_prompt is not None
    assert (
        "anish@example.com"
        not in fake_generator.received_prompt
    )
    assert (
        "9876543210"
        not in fake_generator.received_prompt
    )
    assert (
        "[REDACTED_EMAIL]"
        in fake_generator.received_prompt
    )
    assert (
        "[REDACTED_PHONE]"
        in fake_generator.received_prompt
    )


def test_suggestions_require_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        SUGGESTIONS_URL,
        json={
            "resume_id": 1,
            "job_id": 1,
        },
    )

    assert response.status_code == 401


def test_suggestions_reject_invalid_identifiers(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "invalid@example.com",
    )

    response = client.post(
        SUGGESTIONS_URL,
        headers=headers,
        json={
            "resume_id": 0,
            "job_id": -1,
        },
    )

    assert response.status_code == 422


def test_suggestions_return_404_for_missing_resume(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "missing@example.com",
    )

    response = client.post(
        SUGGESTIONS_URL,
        headers=headers,
        json={
            "resume_id": 999,
            "job_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resume not found"
    }


def test_user_cannot_use_another_users_resources(
    client: TestClient,
) -> None:
    _, resume_id, job_id = prepare_resources(
        client,
        email="first@example.com",
    )

    second_headers = register_and_login(
        client,
        "second@example.com",
    )

    response = client.post(
        SUGGESTIONS_URL,
        headers=second_headers,
        json={
            "resume_id": resume_id,
            "job_id": job_id,
        },
    )

    assert response.status_code == 404


def test_missing_provider_configuration_returns_503(
    client: TestClient,
) -> None:
    headers, resume_id, job_id = prepare_resources(
        client
    )

    generator = MissingConfigurationGenerator()

    app.dependency_overrides[
        get_suggestion_generator
    ] = lambda: generator

    try:
        response = client.post(
            SUGGESTIONS_URL,
            headers=headers,
            json={
                "resume_id": resume_id,
                "job_id": job_id,
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_suggestion_generator,
            None,
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Gemini API key is not configured"
    }


def test_provider_failure_returns_502(
    client: TestClient,
) -> None:
    headers, resume_id, job_id = prepare_resources(
        client
    )

    generator = FailingSuggestionGenerator()

    app.dependency_overrides[
        get_suggestion_generator
    ] = lambda: generator

    try:
        response = client.post(
            SUGGESTIONS_URL,
            headers=headers,
            json={
                "resume_id": resume_id,
                "job_id": job_id,
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_suggestion_generator,
            None,
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "AI suggestion service is unavailable"
    }