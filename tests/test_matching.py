import pymupdf
from fastapi.testclient import TestClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
RESUMES_URL = "/api/v1/resumes"
JOBS_URL = "/api/v1/jobs"
MATCHING_URL = "/api/v1/matching/analyze"


def create_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()

    page.insert_text(
        (72, 72),
        text,
    )

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


def upload_resume(
    client: TestClient,
    headers: dict[str, str],
    resume_text: str,
) -> int:
    response = client.post(
        RESUMES_URL,
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                create_pdf(resume_text),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_job(
    client: TestClient,
    headers: dict[str, str],
    job_title: str = "Python Backend Developer",
    job_description: str = (
        "We need Python, FastAPI, MySQL, REST APIs, "
        "Docker, AWS and Redis experience."
    ),
) -> int:
    response = client.post(
        JOBS_URL,
        headers=headers,
        json={
            "company_name": "Example Technologies",
            "job_title": job_title,
            "job_description": job_description,
            "location": "Gurugram",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_analyze_resume_job_match(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    resume_id = upload_resume(
        client,
        headers,
        (
            "Anish Kumar Verma\n"
            "Python FastAPI MySQL Git Docker"
        ),
    )

    job_id = create_job(client, headers)

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": job_id,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resume_id"] == resume_id
    assert body["job_id"] == job_id
    assert body["match_score"] == 75.0
    assert body["required_skill_count"] == 8
    assert body["algorithm"] == "keyword_and_alias"

    assert set(body["matched_skills"]) == {
        "Docker",
        "FastAPI",
        "MySQL",
        "Python",
        "REST API",
        "SQL",
    }

    assert set(body["missing_skills"]) == {
        "AWS",
        "Redis",
    }

    assert set(body["additional_resume_skills"]) == {
        "Git",
    }


def test_matching_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        MATCHING_URL,
        json={
            "resume_id": 1,
            "job_id": 1,
        },
    )

    assert response.status_code == 401


def test_matching_rejects_invalid_identifiers(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": 0,
            "job_id": -1,
        },
    )

    assert response.status_code == 422


def test_matching_returns_404_for_missing_resume(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    job_id = create_job(client, headers)

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": 999,
            "job_id": job_id,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resume not found"
    }


def test_matching_returns_404_for_missing_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    resume_id = upload_resume(
        client,
        headers,
        "Python FastAPI MySQL Docker",
    )

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found"
    }


def test_user_cannot_match_another_users_resources(
    client: TestClient,
) -> None:
    first_user_headers = register_and_login(
        client,
        "first@example.com",
    )

    first_resume_id = upload_resume(
        client,
        first_user_headers,
        "Python FastAPI MySQL Docker",
    )

    first_job_id = create_job(
        client,
        first_user_headers,
    )

    second_user_headers = register_and_login(
        client,
        "second@example.com",
    )

    response = client.post(
        MATCHING_URL,
        headers=second_user_headers,
        json={
            "resume_id": first_resume_id,
            "job_id": first_job_id,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resume not found"
    }

    second_resume_id = upload_resume(
        client,
        second_user_headers,
        "Python FastAPI MySQL",
    )

    response = client.post(
        MATCHING_URL,
        headers=second_user_headers,
        json={
            "resume_id": second_resume_id,
            "job_id": first_job_id,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found"
    }


def test_matching_rejects_job_without_detectable_skills(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    resume_id = upload_resume(
        client,
        headers,
        "Python FastAPI MySQL Docker",
    )

    job_id = create_job(
        client,
        headers,
        job_title="Office Coordinator",
        job_description=(
            "Coordinate schedules and communicate "
            "with candidates every working day."
        ),
    )

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": job_id,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "No recognizable skills were found "
            "in the job description"
        )
    }


def test_matching_rejects_resume_without_detectable_skills(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    resume_id = upload_resume(
        client,
        headers,
        (
            "Strong communication, teamwork "
            "and problem solving abilities."
        ),
    )

    job_id = create_job(client, headers)

    response = client.post(
        MATCHING_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": job_id,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "No recognizable skills were found "
            "in the resume"
        )
    }