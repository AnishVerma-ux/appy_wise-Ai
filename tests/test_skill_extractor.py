from app.matching.skill_extractor import extract_skills


def test_extract_common_backend_skills() -> None:
    text = """
    Developed APIs using Python, FastAPI and MySQL.
    Used Redis caching, Docker and AWS deployment.
    """

    skills = extract_skills(text)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "REST API" in skills
    assert "MySQL" in skills
    assert "SQL" in skills
    assert "Redis" in skills
    assert "Docker" in skills
    assert "AWS" in skills


def test_extract_aliases_case_insensitively() -> None:
    text = """
    Experience with RESTful APIs, Postgres,
    Amazon Web Services, K8s and CI/CD.
    """

    skills = extract_skills(text)

    assert "REST API" in skills
    assert "PostgreSQL" in skills
    assert "SQL" in skills
    assert "AWS" in skills
    assert "Kubernetes" in skills
    assert "CI/CD" in skills


def test_frameworks_add_implied_skills() -> None:
    text = "Built services using Spring Boot and Hibernate."

    skills = extract_skills(text)

    assert "Spring Boot" in skills
    assert "Hibernate" in skills
    assert "Java" in skills
    assert "REST API" in skills


def test_does_not_match_substrings() -> None:
    text = """
    JavaScript developer who will go through
    the application requirements.
    """

    skills = extract_skills(text)

    assert "JavaScript" in skills
    assert "Java" not in skills
    assert "Go" not in skills


def test_does_not_return_duplicate_skills() -> None:
    text = "Python python PYTHON FastAPI fastapi"

    skills = extract_skills(text)

    assert skills.count("Python") == 1
    assert skills.count("FastAPI") == 1
    assert skills == sorted(skills, key=str.casefold)


def test_empty_text_returns_empty_list() -> None:
    assert extract_skills("") == []
    assert extract_skills(None) == []