import pymupdf
from fastapi.testclient import TestClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
RESUMES_URL = "/api/v1/resumes"
JOBS_URL = "/api/v1/jobs"
APPLICATIONS_URL = "/api/v1/applications"


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
                    "Python FastAPI MySQL Git Docker"
                ),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_job(
    client: TestClient,
    headers: dict[str, str],
) -> int:
    response = client.post(
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

    assert response.status_code == 201

    return response.json()["id"]


def prepare_application(
    client: TestClient,
    email: str = "anish@example.com",
):
    headers = register_and_login(client, email)
    resume_id = upload_resume(client, headers)
    job_id = create_job(client, headers)

    response = client.post(
        APPLICATIONS_URL,
        headers=headers,
        json={
            "job_id": job_id,
            "resume_id": resume_id,
            "notes": "Initial application note.",
        },
    )

    assert response.status_code == 201

    return headers, resume_id, job_id, response


def test_create_application_with_match_score_and_history(
    client: TestClient,
) -> None:
    headers, resume_id, job_id, response = (
        prepare_application(client)
    )

    body = response.json()

    assert body["id"] == 1
    assert body["job_id"] == job_id
    assert body["resume_id"] == resume_id
    assert body["status"] == "SAVED"
    assert body["match_score"] == 75.0
    assert body["notes"] == "Initial application note."
    assert body["applied_at"] is None

    history_response = client.get(
        f"{APPLICATIONS_URL}/1/history",
        headers=headers,
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["old_status"] is None
    assert history[0]["new_status"] == "SAVED"


def test_application_creation_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        APPLICATIONS_URL,
        json={
            "job_id": 1,
            "resume_id": 1,
        },
    )

    assert response.status_code == 401


def test_duplicate_application_is_rejected(
    client: TestClient,
) -> None:
    headers, resume_id, job_id, _ = prepare_application(
        client
    )

    duplicate_response = client.post(
        APPLICATIONS_URL,
        headers=headers,
        json={
            "job_id": job_id,
            "resume_id": resume_id,
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": (
            "An application for this job already exists"
        )
    }


def test_list_and_get_application(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    list_response = client.get(
        APPLICATIONS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == application_id

    detail_response = client.get(
        f"{APPLICATIONS_URL}/{application_id}",
        headers=headers,
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["id"] == application_id
    assert detail["status"] == "SAVED"
    assert len(detail["history"]) == 1


def test_status_updates_applied_date_and_history(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    applied_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/status",
        headers=headers,
        json={
            "status": "APPLIED"
        },
    )

    assert applied_response.status_code == 200
    assert applied_response.json()["status"] == "APPLIED"
    assert applied_response.json()["applied_at"] is not None

    interview_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/status",
        headers=headers,
        json={
            "status": "INTERVIEW"
        },
    )

    assert interview_response.status_code == 200
    assert interview_response.json()["status"] == "INTERVIEW"

    history_response = client.get(
        f"{APPLICATIONS_URL}/{application_id}/history",
        headers=headers,
    )

    history = history_response.json()

    assert [
        item["new_status"]
        for item in history
    ] == [
        "SAVED",
        "APPLIED",
        "INTERVIEW",
    ]

    assert [
        item["old_status"]
        for item in history
    ] == [
        None,
        "SAVED",
        "APPLIED",
    ]


def test_invalid_status_transition_is_rejected(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/status",
        headers=headers,
        json={
            "status": "INTERVIEW"
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Cannot change status from SAVED to INTERVIEW"
        )
    }


def test_update_and_clear_application_notes(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    update_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/notes",
        headers=headers,
        json={
            "notes": (
                "Technical interview scheduled for Monday."
            )
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["notes"] == (
        "Technical interview scheduled for Monday."
    )

    clear_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/notes",
        headers=headers,
        json={
            "notes": None
        },
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["notes"] is None


def test_empty_notes_update_is_rejected(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/notes",
        headers=headers,
        json={},
    )

    assert response.status_code == 422


def test_user_cannot_access_another_users_application(
    client: TestClient,
) -> None:
    first_headers, _, _, creation_response = (
        prepare_application(
            client,
            email="first@example.com",
        )
    )

    application_id = creation_response.json()["id"]

    assert first_headers is not None

    second_headers = register_and_login(
        client,
        "second@example.com",
    )

    detail_response = client.get(
        f"{APPLICATIONS_URL}/{application_id}",
        headers=second_headers,
    )

    history_response = client.get(
        f"{APPLICATIONS_URL}/{application_id}/history",
        headers=second_headers,
    )

    status_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/status",
        headers=second_headers,
        json={
            "status": "APPLIED"
        },
    )

    notes_response = client.patch(
        f"{APPLICATIONS_URL}/{application_id}/notes",
        headers=second_headers,
        json={
            "notes": "Unauthorized update"
        },
    )

    delete_response = client.delete(
        f"{APPLICATIONS_URL}/{application_id}",
        headers=second_headers,
    )

    assert detail_response.status_code == 404
    assert history_response.status_code == 404
    assert status_response.status_code == 404
    assert notes_response.status_code == 404
    assert delete_response.status_code == 404


def test_delete_application(
    client: TestClient,
) -> None:
    headers, _, _, creation_response = (
        prepare_application(client)
    )

    application_id = creation_response.json()["id"]

    delete_response = client.delete(
        f"{APPLICATIONS_URL}/{application_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    detail_response = client.get(
        f"{APPLICATIONS_URL}/{application_id}",
        headers=headers,
    )

    assert detail_response.status_code == 404

    list_response = client.get(
        APPLICATIONS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_application_creation_rejects_missing_resources(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    missing_resume_response = client.post(
        APPLICATIONS_URL,
        headers=headers,
        json={
            "resume_id": 999,
            "job_id": 999,
        },
    )

    assert missing_resume_response.status_code == 404
    assert missing_resume_response.json() == {
        "detail": "Resume not found"
    }

    resume_id = upload_resume(client, headers)

    missing_job_response = client.post(
        APPLICATIONS_URL,
        headers=headers,
        json={
            "resume_id": resume_id,
            "job_id": 999,
        },
    )

    assert missing_job_response.status_code == 404
    assert missing_job_response.json() == {
        "detail": "Job not found"
    }