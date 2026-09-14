from fastapi.testclient import TestClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


def test_register_user(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={
            "full_name": "Anish Kumar Verma",
            "email": "anish@example.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Anish Kumar Verma"
    assert body["email"] == "anish@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    payload = {
        "full_name": "Anish Verma",
        "email": "anish@example.com",
        "password": "StrongPass123",
    }
    first_response = client.post(REGISTER_URL, json=payload)
    duplicate_response = client.post(REGISTER_URL, json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "Email is already registered"}


def test_login_and_access_protected_profile(client: TestClient) -> None:
    client.post(
        REGISTER_URL,
        json={
            "full_name": "Anish Verma",
            "email": "anish@example.com",
            "password": "StrongPass123",
        },
    )

    login_response = client.post(
        LOGIN_URL,
        json={
            "email": "anish@example.com",
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200
    token_body = login_response.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]
    assert token_body["expires_in"] == 1800

    profile_response = client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "anish@example.com"


def test_login_with_wrong_password_is_rejected(client: TestClient) -> None:
    client.post(
        REGISTER_URL,
        json={
            "full_name": "Anish Verma",
            "email": "anish@example.com",
            "password": "StrongPass123",
        },
    )

    response = client.post(
        LOGIN_URL,
        json={
            "email": "anish@example.com",
            "password": "WrongPass999",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_profile_requires_token(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

