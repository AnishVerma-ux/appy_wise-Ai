import pymupdf
from fastapi.testclient import TestClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
RESUMES_URL = "/api/v1/resumes"
JOBS_URL = "/api/v1/jobs"
APPLICATIONS_URL = "/api/v1/applications"
DASHBOARD_URL = "/api/v1/analytics/dashboard"


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


def upload_resume(
    client: TestClient,
    headers: dict[str, str],
) -> int:
    response = client.post(
        RESUMES_URL,
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                create_pdf(
                    "Python FastAPI MySQL SQL Git Docker REST API"
                ),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_application(
    client: TestClient,
    headers: dict[str, str],
    resume_id: int,
    job_number: int,
    job_description: str,
) -> tuple[int, float]:
    job_response = client.post(
        JOBS_URL,
        headers=headers,
        json={
            "company_name": f"Company {job_number}",
            "job_title": "Backend Developer",
            "job_description": job_description,
            "location": "Gurugram",
        },
    )

    assert job_response.status_code == 201

    application_response = client.post(
        APPLICATIONS_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": job_response.json()["id"],
        },
    )

    assert application_response.status_code == 201

    body = application_response.json()

    return body["id"], body["match_score"]


def update_statuses(
    client: TestClient,
    headers: dict[str, str],
    application_id: int,
    statuses: list[str],
) -> None:
    for new_status in statuses:
        response = client.patch(
            (
                f"{APPLICATIONS_URL}/"
                f"{application_id}/status"
            ),
            headers=headers,
            json={"status": new_status},
        )

        assert response.status_code == 200
        assert response.json()["status"] == new_status


def test_dashboard_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 401


def test_empty_dashboard_returns_zeroes(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "empty@example.com",
    )

    response = client.get(
        DASHBOARD_URL,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_applications": 0,
        "interviews": 0,
        "offers": 0,
        "rejections": 0,
        "average_match_score": 0.0,
    }


def test_dashboard_returns_application_summary(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    resume_id = upload_resume(client, headers)

    descriptions = [
        (
            "Python and FastAPI are required for "
            "backend development."
        ),
        (
            "Python, FastAPI, MySQL, Docker, AWS "
            "and Redis experience is required."
        ),
        (
            "MySQL, SQL, Docker and Git experience "
            "is required for this position."
        ),
        (
            "Python, REST APIs and AWS experience "
            "is required for this backend role."
        ),
    ]

    application_ids: list[int] = []
    match_scores: list[float] = []

    for number, description in enumerate(
        descriptions,
        start=1,
    ):
        application_id, match_score = create_application(
            client=client,
            headers=headers,
            resume_id=resume_id,
            job_number=number,
            job_description=description,
        )

        application_ids.append(application_id)
        match_scores.append(match_score)

    update_statuses(
        client,
        headers,
        application_ids[0],
        ["APPLIED", "INTERVIEW"],
    )

    update_statuses(
        client,
        headers,
        application_ids[1],
        ["APPLIED", "OFFERED"],
    )

    update_statuses(
        client,
        headers,
        application_ids[2],
        ["APPLIED", "REJECTED"],
    )

    response = client.get(
        DASHBOARD_URL,
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_applications"] == 4
    assert body["interviews"] == 1
    assert body["offers"] == 1
    assert body["rejections"] == 1
    assert body["average_match_score"] == round(
        sum(match_scores) / len(match_scores),
        2,
    )


def test_dashboard_only_uses_current_users_data(
    client: TestClient,
) -> None:
    first_headers = register_and_login(
        client,
        "first@example.com",
    )

    first_resume_id = upload_resume(
        client,
        first_headers,
    )

    create_application(
        client=client,
        headers=first_headers,
        resume_id=first_resume_id,
        job_number=1,
        job_description=(
            "Python, FastAPI and MySQL experience "
            "is required for this position."
        ),
    )

    second_headers = register_and_login(
        client,
        "second@example.com",
    )

    response = client.get(
        DASHBOARD_URL,
        headers=second_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_applications": 0,
        "interviews": 0,
        "offers": 0,
        "rejections": 0,
        "average_match_score": 0.0,
    }