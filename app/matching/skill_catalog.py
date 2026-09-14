SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    # Programming languages
    "Python": (
        r"\bpython\b",
    ),
    "Java": (
        r"\bjava\b",
    ),
    "JavaScript": (
        r"\bjavascript\b",
        r"\bjava[\s-]?script\b",
        r"\bjs\b",
    ),
    "TypeScript": (
        r"\btypescript\b",
        r"\btype[\s-]?script\b",
    ),
    "C++": (
        r"(?<!\w)c\+\+(?!\w)",
    ),
    "C#": (
        r"(?<!\w)c#(?!\w)",
    ),
    "Go": (
        r"\bgolang\b",
        r"\bgo\s+language\b",
    ),

    # Backend development
    "FastAPI": (
        r"\bfastapi\b",
        r"\bfast\s+api\b",
    ),
    "Django": (
        r"\bdjango\b",
    ),
    "Flask": (
        r"\bflask\b",
    ),
    "Spring Boot": (
        r"\bspring[\s-]*boot\b",
    ),
    "Node.js": (
        r"\bnode(?:\.js|js)\b",
    ),
    "Express.js": (
        r"\bexpress(?:\.js|js)?\b",
    ),
    "REST API": (
        r"\brest(?:ful)?\s*apis?\b",
    ),
    "GraphQL": (
        r"\bgraphql\b",
    ),
    "Microservices": (
        r"\bmicro[\s-]?services?\b",
    ),
    "SQLAlchemy": (
        r"\bsqlalchemy\b",
    ),
    "Hibernate": (
        r"\bhibernate\b",
    ),
    "JPA": (
        r"\bjpa\b",
        r"\bjava\s+persistence\s+api\b",
    ),

    # Databases and messaging
    "SQL": (
        r"\bsql\b",
    ),
    "MySQL": (
        r"\bmysql\b",
    ),
    "PostgreSQL": (
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ),
    "SQLite": (
        r"\bsqlite\b",
    ),
    "MongoDB": (
        r"\bmongodb\b",
        r"\bmongo\s*db\b",
    ),
    "Redis": (
        r"\bredis\b",
    ),
    "Kafka": (
        r"\bapache\s+kafka\b",
        r"\bkafka\b",
    ),
    "RabbitMQ": (
        r"\brabbitmq\b",
        r"\brabbit\s*mq\b",
    ),
    "Celery": (
        r"\bcelery\b",
    ),

    # Cloud and DevOps
    "AWS": (
        r"\baws\b",
        r"\bamazon\s+web\s+services\b",
    ),
    "Azure": (
        r"\bazure\b",
        r"\bmicrosoft\s+azure\b",
    ),
    "GCP": (
        r"\bgcp\b",
        r"\bgoogle\s+cloud(?:\s+platform)?\b",
    ),
    "Docker": (
        r"\bdocker\b",
    ),
    "Kubernetes": (
        r"\bkubernetes\b",
        r"\bk8s\b",
    ),
    "Git": (
        r"\bgit\b",
    ),
    "GitHub": (
        r"\bgithub\b",
    ),
    "CI/CD": (
        r"\bci\s*/\s*cd\b",
        r"\bcontinuous\s+integration\b",
    ),
    "Jenkins": (
        r"\bjenkins\b",
    ),
    "Linux": (
        r"\blinux\b",
    ),
    "Maven": (
        r"\bmaven\b",
    ),
    "Gradle": (
        r"\bgradle\b",
    ),

    # Frontend
    "React": (
        r"\breact(?:\.js|js)?\b",
    ),
    "HTML": (
        r"\bhtml5?\b",
    ),
    "CSS": (
        r"\bcss3?\b",
    ),

    # Data and AI
    "Pandas": (
        r"\bpandas\b",
    ),
    "NumPy": (
        r"\bnumpy\b",
    ),
    "Scikit-learn": (
        r"\bscikit[\s-]?learn\b",
        r"\bsklearn\b",
    ),
    "Machine Learning": (
        r"\bmachine\s+learning\b",
        r"\bml\b",
    ),
    "NLP": (
        r"\bnlp\b",
        r"\bnatural\s+language\s+processing\b",
    ),
    "LLM": (
        r"\bllms?\b",
        r"\blarge\s+language\s+models?\b",
    ),
    "RAG": (
        r"\brag\b",
        r"\bretrieval[\s-]+augmented\s+generation\b",
    ),

    # Security and testing
    "JWT": (
        r"\bjwt\b",
        r"\bjson\s+web\s+tokens?\b",
    ),
    "OAuth2": (
        r"\boauth\s*2(?:\.0)?\b",
    ),
    "Pytest": (
        r"\bpytest\b",
    ),
}


IMPLIED_SKILLS: dict[str, tuple[str, ...]] = {
    "FastAPI": ("Python", "REST API"),
    "Django": ("Python",),
    "Flask": ("Python",),
    "Spring Boot": ("Java", "REST API"),
    "Hibernate": ("Java",),
    "JPA": ("Java",),
    "MySQL": ("SQL",),
    "PostgreSQL": ("SQL",),
    "SQLite": ("SQL",),
    "Node.js": ("JavaScript",),
    "Express.js": ("JavaScript", "Node.js"),
    "GitHub": ("Git",),
}