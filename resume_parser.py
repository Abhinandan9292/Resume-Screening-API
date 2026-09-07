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
    "contact",
    "contact information",
    "personal details",
}

CONTACT_PATTERN = re.compile(
    r"(?:[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d\s().-]{7,}\d|\b(?:linkedin|github|portfolio|www\.)\b)",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}")

# GitHub profile/repo links. We only want the profile handle (github.com/<user>),
# not a link to a specific repository, so we stop at the first path segment.
GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)",
    re.IGNORECASE,
)
GITHUB_RESERVED_PATHS = {
    "settings", "notifications", "login", "join", "marketplace", "sponsors",
    "topics", "collections", "trending", "explore", "about", "pricing",
}

# CGPA/GPA on a 10-point scale only. We deliberately do not convert 4.0-scale
# GPAs, since silently rescaling a number without being told the source scale
# would be an assumption the student did not make themselves - if a resume
# clearly states a /4 scale (or any scale other than 10), we skip it rather
# than guess.
CGPA_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\bc?gpa\b\s*(?:\(.*?\))?\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*(\d{1,2}(?:\.\d{1,2})?)\b)?", re.IGNORECASE),
    re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*/\s*(\d{1,2}(?:\.\d{1,2})?)\s*\bc?gpa\b", re.IGNORECASE),
)

NAME_LINE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z.'\-]*(?:\s+[A-Za-z][A-Za-z.'\-]*){1,3}$")


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


def _extract_email(text: str) -> str:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else ""


def _extract_github(text: str) -> str:
    for match in GITHUB_PATTERN.finditer(text):
        handle = match.group(1)
        if handle.lower() in GITHUB_RESERVED_PATHS:
            continue
        return f"https://github.com/{handle}"
    return ""


def _extract_cgpa(text: str) -> float | None:
    for pattern in CGPA_PATTERNS:
        for match in pattern.finditer(text):
            try:
                value = float(match.group(1))
            except (ValueError, IndexError):
                continue

            scale_text = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            if scale_text is not None:
                try:
                    scale = float(scale_text)
                except ValueError:
                    continue
                if round(scale) != 10:
                    # A GPA on any scale other than /10 (e.g. /4) is not a
                    # CGPA we can prefill without silently rescaling it.
                    continue

            # A 10-point CGPA/GPA is never above 10, and anything under ~2 in
            # this position is more likely a stray year, page, or table number.
            if 2.0 <= value <= 10.0:
                return round(value, 2)
    return None


def _split_name(line: str) -> dict[str, str]:
    words = line.split()
    if len(words) < 2:
        return {}

    def normalise(word: str) -> str:
        return word if not word.isupper() else word.capitalize()

    first_name = normalise(words[0])
    last_name = " ".join(normalise(word) for word in words[1:])
    return {"first_name": first_name, "last_name": last_name}


def _extract_name(lines: list[str]) -> dict[str, str]:
    for raw_line in lines[:8]:
        line = _clean_line(raw_line)
        if not line:
            continue
        if _looks_like_contact(line):
            continue
        if _normalise_heading(line) in SECTION_HEADINGS:
            continue
        if any(char.isdigit() for char in line):
            continue
        if len(line) > 45:
            continue
        if not NAME_LINE_PATTERN.match(line):
            continue
        name = _split_name(line)
        if name:
            return name
    return {}


def parse_resume_text(text: str) -> dict[str, object]:
    """Return a conservative profile draft. Every field is either extracted
    with a plain, explainable rule or left blank/None - nothing here is
    inferred by a model, and the caller should always treat the result as a
    suggestion the student reviews, not a value that is auto-submitted."""
    normalised_text = text.replace(" ", " ").replace("\r", "\n")
    lines = normalised_text.splitlines()

    skills = _extract_skills(normalised_text)
    summary = _extract_summary(lines)
    email = _extract_email(normalised_text)
    github = _extract_github(normalised_text)
    cgpa = _extract_cgpa(normalised_text)
    name = _extract_name(lines)

    return {
        "suggested_skills": ", ".join(skills),
        "bio_preview": summary,
        "skills_count": len(skills),
        "summary_found": bool(summary),
        "suggested_first_name": name.get("first_name", ""),
        "suggested_last_name": name.get("last_name", ""),
        "name_found": bool(name),
        "suggested_email": email,
        "email_found": bool(email),
        "suggested_github": github,
        "github_found": bool(github),
        "suggested_cgpa": cgpa,
        "cgpa_found": cgpa is not None,
    }
