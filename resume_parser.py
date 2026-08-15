"""Small, deterministic helpers for extracting safe profile drafts from resumes."""

import re
from collections.abc import Iterable


# Keep this list explicit so the application does not pretend to infer skills it cannot support.
SKILL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Python", r"\bpython\b"),
    ("Java", r"(?<!script)\bjava\b"),
    ("C++", r"\bc\+\+\b|\bc plus plus\b"),
    ("C#", r"\bc#\b|\bc sharp\b"),
    ("JavaScript", r"\bjavascript\b|\bjs\b"),
    ("TypeScript", r"\btypescript\b|\bts\b"),
    ("HTML", r"\bhtml(?:5)?\b"),
    ("CSS", r"\bcss(?:3)?\b"),
    ("React", r"\breact(?:\.js)?\b"),
    ("Angular", r"\bangular\b"),
    ("Vue", r"\bvue(?:\.js)?\b"),
    ("Node.js", r"\bnode(?:\.js|js)?\b"),
    ("SQL", r"\bsql\b"),
    ("PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("MySQL", r"\bmysql\b"),
    ("MongoDB", r"\bmongo(?:db)?\b"),
    ("Git", r"\bgit\b"),
    ("GitHub", r"\bgithub\b"),
    ("Linux", r"\blinux\b"),
    ("Docker", r"\bdocker\b"),
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("AWS", r"\baws\b|\bamazon web services\b"),
    ("Azure", r"\bazure\b"),
    ("GCP", r"\bgcp\b|\bgoogle cloud\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Django", r"\bdjango\b"),
    ("Flask", r"\bflask\b"),
    ("REST APIs", r"\brest(?:ful)?\s+apis?\b"),
    ("Pandas", r"\bpandas\b"),
    ("NumPy", r"\bnumpy\b"),
    ("Scikit-learn", r"\bscikit[- ]learn\b|\bsklearn\b"),
    ("TensorFlow", r"\btensorflow\b"),
    ("PyTorch", r"\bpytorch\b"),
    ("Machine Learning", r"\bmachine learning\b|\bml\b"),
    ("Deep Learning", r"\bdeep learning\b|\bdl\b"),
    ("Artificial Intelligence", r"\bartificial intelligence\b|\bai\b"),
    ("NLP", r"\bnlp\b|\bnatural language processing\b"),
    ("Data Analysis", r"\bdata analys(?:is|tics)\b"),
    ("Data Structures & Algorithms", r"\bdata structures? (?:and|&) algorithms?\b|\bdsa\b"),
    ("Power BI", r"\bpower ?bi\b"),
    ("Tableau", r"\btableau\b"),
    ("Excel", r"\b(?:microsoft )?excel\b"),
)

SUMMARY_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "personal profile",
    "career objective",
    "objective",
    "about",
    "about me",
}

SECTION_HEADINGS = SUMMARY_HEADINGS | {
    "education",
    "academic background",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "internships",
    "projects",
    "technical projects",
    "skills",
    "technical skills",
    "certifications",
    "achievements",
    "awards",
    "positions of responsibility",
    "languages",
    "interests",
    "publications",
    "volunteering",
}

CONTACT_PATTERN = re.compile(
    r"(?:[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d\s().-]{7,}\d|\b(?:linkedin|github|portfolio|www\.)\b)",
    re.IGNORECASE,
)


def _normalise_heading(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^[\W_]+|[\W_]+$", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _clean_line(value: str) -> str:
    value = re.sub(r"^[•*\-–—\s]+", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _looks_like_contact(value: str) -> bool:
    return bool(CONTACT_PATTERN.search(value))


def _trim_summary(value: str, limit: int = 600) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value

    sentences = re.split(r"(?<=[.!?])\s+", value)
    kept: list[str] = []
    current_length = 0
    for sentence in sentences:
        if current_length + len(sentence) + (1 if kept else 0) > limit:
            break
        kept.append(sentence)
        current_length += len(sentence) + (1 if kept else 0)
    return " ".join(kept).strip() or value[:limit].rsplit(" ", 1)[0].strip()


def _extract_summary(lines: Iterable[str]) -> str:
    cleaned_lines = [_clean_line(line) for line in lines]

    for index, line in enumerate(cleaned_lines):
        if _normalise_heading(line) not in SUMMARY_HEADINGS:
            continue

        summary_lines: list[str] = []
        for candidate in cleaned_lines[index + 1 :]:
            heading = _normalise_heading(candidate)
            if heading in SECTION_HEADINGS:
                break
            if candidate and not _looks_like_contact(candidate):
                summary_lines.append(candidate)

        summary = _trim_summary(" ".join(summary_lines))
        if summary:
            return summary

    return ""


def _extract_skills(text: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    for skill, pattern in SKILL_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            matches.append((match.start(), skill))
    return [skill for _, skill in sorted(matches)]


def parse_resume_text(text: str) -> dict[str, object]:
    """Return a conservative skills draft and a summary only when one is present."""
    normalised_text = text.replace("\u00a0", " ").replace("\r", "\n")
    skills = _extract_skills(normalised_text)
    summary = _extract_summary(normalised_text.splitlines())

    return {
        "suggested_skills": ", ".join(skills),
        "bio_preview": summary,
        "skills_count": len(skills),
        "summary_found": bool(summary),
    }
