import re

from app.matching.skill_catalog import (
    IMPLIED_SKILLS,
    SKILL_PATTERNS,
)


COMPILED_SKILL_PATTERNS = {
    skill: tuple(
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in patterns
    )
    for skill, patterns in SKILL_PATTERNS.items()
}


def extract_skills(text: str | None) -> list[str]:
    if not text:
        return []

    normalized_text = (
        text
        .replace("–", "-")
        .replace("—", "-")
    )

    detected_skills: set[str] = set()

    for skill, patterns in COMPILED_SKILL_PATTERNS.items():
        if any(
            pattern.search(normalized_text)
            for pattern in patterns
        ):
            detected_skills.add(skill)

    # Add foundational skills implied by specific technologies.
    for detected_skill in tuple(detected_skills):
        implied_skills = IMPLIED_SKILLS.get(
            detected_skill,
            (),
        )

        detected_skills.update(implied_skills)

    return sorted(
        detected_skills,
        key=str.casefold,
    )