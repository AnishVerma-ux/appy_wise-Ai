# ApplyWise AI

ApplyWise AI is a FastAPI backend for comparing a resume with a job description
and tracking job applications. The current checkpoint contains the application
foundation, MySQL integration, and JWT-based user authentication.

## Current checkpoint

- Clean FastAPI package structure
- Environment-based configuration
- SQLAlchemy 2 database setup
- MySQL connection through PyMySQL
- Application and database health endpoints
- User registration and duplicate-email protection
- Bcrypt password hashing
- Login with signed JWT access tokens
- Protected current-user endpoint
- Alembic database migrations
- Swagger/OpenAPI documentation
- Automated health and authentication tests
- Secure PDF and DOCX resume uploads
- Maximum 5 MB file-size validation
- PDF and DOCX content-signature validation
- Resume text extraction
- Authenticated resume listing and retrieval
- Resume deletion from database and file storage
- User ownership protection
- 16 automated tests
- Authenticated job-description management
- Create, list, view, update and delete job records
- Partial job updates with Pydantic validation
- User ownership protection for every job
- 25 passing automated tests
- Resume and job-description skill extraction
- Skill alias and normalization support
- Implied-skill detection
- Resume-to-job match score
- Matched, missing and additional skill results
- Ownership-protected matching endpoint
- 39 passing automated tests
## Project structure

```text
applywise-ai/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   └── health.py
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   └── user.py
│   ├── repositories/
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── health.py
│   │   └── user.py
│   ├── services/
│   │   └── auth_service.py
│   └── main.py
├── alembic/
│   └── versions/
│       └── 20260914_0001_create_users_table.py
├── tests/
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

## 1. Create the MySQL database

Open MySQL Workbench or the MySQL command line and run:

```sql
CREATE DATABASE applywise_ai
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

## 2. Set up the Python environment

Use Python 3.11 or newer. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Open `.env`, replace `change_me` with your local MySQL password, and replace
the sample JWT secret with a long random value. Do not commit `.env`; it is
ignored by Git.

## 3. Create the users table

Run the included Alembic migration after creating the database:

```powershell
python -m alembic upgrade head
```

## 4. Run the API

```powershell
python -m uvicorn app.main:app --reload
```

Open:

- API root: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs
- App health: http://127.0.0.1:8000/api/v1/health
- Database health: http://127.0.0.1:8000/api/v1/health/database

Expected database health response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

If the database credentials are incorrect or MySQL is stopped, the endpoint
returns HTTP `503` with `Database connection failed`.

## Authentication endpoints

### Register

`POST /api/v1/auth/register`

```json
{
  "full_name": "Anish Kumar Verma",
  "email": "anish@example.com",
  "password": "StrongPass123"
}
```

### Login

`POST /api/v1/auth/login`

```json
{
  "email": "anish@example.com",
  "password": "StrongPass123"
}
```

The login response contains an access token. Send it to protected endpoints:

```http
Authorization: Bearer <access_token>
```

### Current user

`GET /api/v1/auth/me`

This route returns the authenticated user and rejects missing, invalid, or
expired access tokens.
## Resume endpoints

All resume endpoints require a JWT access token.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/resumes` | Upload and process a resume |
| GET | `/api/v1/resumes` | List the authenticated user's resumes |
| GET | `/api/v1/resumes/{resume_id}` | Get one owned resume |
| DELETE | `/api/v1/resumes/{resume_id}` | Delete an owned resume |

Supported formats:

- PDF
- DOCX

Maximum file size: `5 MB`

Uploaded files are validated, renamed with a UUID, stored securely and parsed to extract text.
## Job endpoints

All job endpoints require JWT authentication.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/jobs` | Save a job description |
| GET | `/api/v1/jobs` | List the authenticated user's jobs |
| GET | `/api/v1/jobs/{job_id}` | View one owned job |
| PATCH | `/api/v1/jobs/{job_id}` | Partially update an owned job |
| DELETE | `/api/v1/jobs/{job_id}` | Delete an owned job |

Each job stores:

- Company name
- Job title
- Job description
- Location
- Job URL


Analyze an authenticated user's resume against one of their saved jobs:

```http
POST /api/v1/matching/analyze
## 5. Run tests

```powershell
python -m pytest
```

The tests use a temporary SQLite database and do not require a running MySQL server. The database health
endpoint is checked manually against your own MySQL installation.


Replace `## Next checkpoint` with:

```markdown
## Next checkpoint

The next feature is application tracking:

1. Link a resume with a saved job.
2. Store the match-score snapshot.
3. Track Saved, Applied, Interview, Offer and Rejected statuses.
4. Record application dates and notes.
5. Maintain status-change history.