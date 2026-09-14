from fastapi.testclient import TestClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
JOBS_URL = "/api/v1/jobs"


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

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }


def create_job(
    client: TestClient,
    headers: dict[str, str],
):
    return client.post(
        JOBS_URL,
        headers=headers,
        json={
            "company_name": "Cloud Analogy",
            "job_title": "Software Trainee",
            "job_description": (
                "Looking for a motivated software trainee "
                "with knowledge of Python, APIs, databases, "
                "cloud technologies and problem solving."
            ),
            "location": "Noida",
            "job_url": (
                "https://example.com/jobs/software-trainee"
            ),
        },
    )


def test_create_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    response = create_job(client, headers)

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["company_name"] == "Cloud Analogy"
    assert body["job_title"] == "Software Trainee"
    assert body["location"] == "Noida"
    assert body["job_url"] == (
        "https://example.com/jobs/software-trainee"
    )


def test_create_job_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        JOBS_URL,
        json={
            "company_name": "Cloud Analogy",
            "job_title": "Software Trainee",
            "job_description": (
                "This is a sufficiently long job description."
            ),
            "location": "Noida",
        },
    )

    assert response.status_code == 401


def test_list_and_get_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    create_response = create_job(client, headers)
    job_id = create_response.json()["id"]

    list_response = client.get(
        JOBS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == job_id

    get_response = client.get(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == job_id
    assert get_response.json()["company_name"] == "Cloud Analogy"


def test_update_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    create_response = create_job(client, headers)
    job_id = create_response.json()["id"]

    update_response = client.patch(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
        json={
            "location": "Gurugram",
            "job_title": "Python Software Trainee",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["location"] == "Gurugram"
    assert body["job_title"] == "Python Software Trainee"
    assert body["company_name"] == "Cloud Analogy"


def test_clear_optional_job_location(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    create_response = create_job(client, headers)
    job_id = create_response.json()["id"]

    response = client.patch(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
        json={
            "location": None
        },
    )

    assert response.status_code == 200
    assert response.json()["location"] is None


def test_reject_empty_job_update(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    create_response = create_job(client, headers)
    job_id = create_response.json()["id"]

    response = client.patch(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
        json={},
    )

    assert response.status_code == 422


def test_get_nonexistent_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    response = client.get(
        f"{JOBS_URL}/999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found"
    }


def test_user_cannot_access_another_users_job(
    client: TestClient,
) -> None:
    first_user_headers = register_and_login(
        client,
        "first@example.com",
    )

    create_response = create_job(
        client,
        first_user_headers,
    )

    job_id = create_response.json()["id"]

    second_user_headers = register_and_login(
        client,
        "second@example.com",
    )

    get_response = client.get(
        f"{JOBS_URL}/{job_id}",
        headers=second_user_headers,
    )

    update_response = client.patch(
        f"{JOBS_URL}/{job_id}",
        headers=second_user_headers,
        json={
            "location": "Delhi"
        },
    )

    delete_response = client.delete(
        f"{JOBS_URL}/{job_id}",
        headers=second_user_headers,
    )

    second_user_list = client.get(
        JOBS_URL,
        headers=second_user_headers,
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert second_user_list.status_code == 200
    assert second_user_list.json() == []


def test_delete_job(
    client: TestClient,
) -> None:
    headers = register_and_login(
        client,
        "anish@example.com",
    )

    create_response = create_job(client, headers)
    job_id = create_response.json()["id"]

    delete_response = client.delete(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(
        f"{JOBS_URL}/{job_id}",
        headers=headers,
    )

    assert get_response.status_code == 404

    list_response = client.get(
        JOBS_URL,
        headers=headers,
    )

    assert list_response.json() == []