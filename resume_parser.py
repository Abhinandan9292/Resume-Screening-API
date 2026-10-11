"""Resume text parsing for the /ai_parse endpoint.

main.py extracts the text of an uploaded PDF with PyMuPDF and passes it to
parse_resume_text(), which returns the fields used to pre-fill a student
profile: name, email, GitHub link, skills and a summary. Everything here is
plain text processing, so it can be tested without a PDF or a database.
"""

import re
import unicodedata

# Canonical skill name -> patterns (matched case-insensitively as whole words).
# The first nine names are the ones the original keyword parser produced, so
# existing profiles and recruiter searches keep matching.
SKILL_PATTERNS = {
    "python": [r"python ?3?"],
    "cpp": [r"c\+\+", r"cpp"],
    "java": [r"java"],
    "sql": [r"sql"],
    "react": [r"react(?:\.?js)?"],
    "ml": [r"machine learning", r"ml"],
    "ai": [r"artificial intelligence", r"ai"],
    "dsa": [r"data structures(?: ?(?:and|&) ?algorithms)?", r"dsa"],
    "javascript": [r"javascript", r"js", r"es6"],
    "typescript": [r"typescript"],
    "c#": [r"c#"],
    "html": [r"html5?"],
    "css": [r"css3?"],
    "node.js": [r"node\.?js"],
    "express.js": [r"express\.?js"],
    "next.js": [r"next\.?js"],
    "angular": [r"angular(?:js)?"],
    "vue.js": [r"vue(?:\.?js)?"],
    "django": [r"django"],
    "flask": [r"flask"],
    "fastapi": [r"fastapi"],
    "spring boot": [r"spring ?boot"],
    "mysql": [r"mysql"],
    "postgresql": [r"postgre(?:sql|s)"],
    "mongodb": [r"mongo ?db"],
    "sqlite": [r"sqlite"],
    "redis": [r"redis"],
    "firebase": [r"firebase"],
    "git": [r"git"],
    "github": [r"github"],
    "docker": [r"docker"],
    "kubernetes": [r"kubernetes", r"k8s"],
    "aws": [r"aws", r"amazon web services"],
    "azure": [r"azure"],
    "gcp": [r"gcp", r"google cloud(?: platform)?"],
    "linux": [r"linux"],
    "bash": [r"bash", r"shell scripting"],
    "pandas": [r"pandas"],
    "numpy": [r"numpy"],
    "scikit-learn": [r"scikit[- ]learn", r"sklearn"],
    "tensorflow": [r"tensorflow"],
    "pytorch": [r"pytorch"],
    "keras": [r"keras"],
    "opencv": [r"open ?cv"],
    "nlp": [r"nlp", r"natural language processing"],
    "deep learning": [r"deep learning"],
    "computer vision": [r"computer vision"],
    "data analysis": [r"data analy(?:sis|tics)"],
    "power bi": [r"power ?bi"],
    "tableau": [r"tableau"],
    "matlab": [r"matlab"],
    "kotlin": [r"kotlin"],
    "php": [r"php"],
    "dart": [r"dart"],
    "flutter": [r"flutter"],
    "android": [r"android"],
    "rest api": [r"rest(?:ful)? apis?"],
    "graphql": [r"graphql"],
    "tailwind css": [r"tailwind(?: ?css)?"],
    "bootstrap": [r"bootstrap"],
    "figma": [r"figma"],
    "arduino": [r"arduino"],
    "oop": [r"oops?", r"object[- ]oriented programming"],
    "dbms": [r"dbms"],
    "operating systems": [r"operating systems?"],
    "computer networks": [r"computer networks?"],
    "postman": [r"postman"],
    "jira": [r"jira"],
    "selenium": [r"selenium"],
    "jenkins": [r"jenkins"],
    "ci/cd": [r"ci ?/ ?cd"],
    "verilog": [r"verilog"],
    "autocad": [r"autocad"],
    "golang": [r"golang"],
}

# Short or everyday words that only count as skills inside a Skills section.
SECTION_ONLY_PATTERNS = {
    "c": [r"c"],
    "r": [r"r"],
    "go": [r"go"],
    "swift": [r"swift"],
    "rust": [r"rust"],
    "excel": [r"(?:ms |microsoft )?excel"],
}

# A skill must not touch letters, digits or the symbols used in names such as
# C++, C#, emails and file names; "github.com" style links are excluded too.
_LEFT = r"(?<![A-Za-z0-9+#.\-_@])"
_RIGHT = r"(?![A-Za-z0-9+#_@])(?!\.\w)"


def _compile(patterns):
    return {
        name: re.compile(_LEFT + "(?:" + "|".join(alts) + ")" + _RIGHT, re.IGNORECASE)
        for name, alts in patterns.items()
    }


_SKILL_RE = _compile(SKILL_PATTERNS)
_SECTION_ONLY_RE = _compile(SECTION_ONLY_PATTERNS)
_FULL_RE = {
    name: re.compile("(?:" + "|".join(alts) + ")", re.IGNORECASE)
    for name, alts in {**SKILL_PATTERNS, **SECTION_ONLY_PATTERNS}.items()
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))", re.IGNORECASE)
URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|\b[\w.-]+\.(?:com|in|io|org|net|dev|me|app|co|ai)(?:/\S*)?",
    re.IGNORECASE,
)

SUMMARY_HEADINGS = {
    "summary", "professional summary", "profile", "profile summary", "career summary",
    "executive summary", "professional profile", "objective", "career objective",
    "about", "about me", "personal statement",
}
EDUCATION_HEADINGS = {
    "education", "academic background", "academics", "educational qualifications",
    "education and training", "qualifications", "academic details",
}
SKILL_HEADINGS = {
    "skills", "technical skills", "key skills", "core skills", "skill set", "skillset",
    "skills and interests", "skills and abilities", "technical proficiency", "technologies",
    "tech stack", "tools", "tools and technologies", "technical expertise",
    "programming languages", "skills and tools", "technical skills and tools",
}
OTHER_HEADINGS = {
    "experience", "work experience", "professional experience", "internship", "internships",
    "internship experience", "employment", "employment history", "work history", "projects",
    "academic projects", "personal projects", "key projects", "languages", "certifications",
    "certificates", "courses", "coursework", "relevant coursework", "achievements", "awards",
    "honors", "honours", "honors and awards", "awards and achievements", "accomplishments",
    "extracurricular activities", "extra curricular activities", "extracurriculars",
    "activities", "positions of responsibility", "leadership", "volunteering",
    "volunteer experience", "publications", "research", "interests", "hobbies",
    "hobbies and interests", "personal details", "personal information", "declaration",
    "references", "contact", "contact information", "competitive programming",
    "coding profiles",
}
ALL_HEADINGS = SUMMARY_HEADINGS | EDUCATION_HEADINGS | SKILL_HEADINGS | OTHER_HEADINGS

NAME_STOPWORDS = {
    "resume", "curriculum", "vitae", "cv", "biodata", "profile", "summary", "engineer",
    "developer", "student", "intern", "university", "institute", "college", "school",
    "india", "contact", "email", "phone", "mobile", "address", "linkedin", "github",
    "portfolio", "objective", "education", "experience", "skills", "projects",
}

DEGREE_RE = re.compile(
    r"\b(?:B\. ?Tech|BTech|B\.E\.|\bBE\b|B\. ?Sc|BSc|BCA|B\. ?Com|BBA|M\. ?Tech|MTech|M\.E\.|"
    r"M\. ?Sc|MSc|MCA|MBA|Ph\. ?D|PhD|Bachelor|Master|Diploma)"
)
INSTITUTION_RE = re.compile(r"Institute|University|College|School|Academy|Vidyalaya|\bIIT\b|\bNIT\b|\bIIIT\b")
YEARS_RE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|Present|present|Current|current)")

SUMMARY_LIMIT = 700
MAX_SKILLS = 30


def clean_text(text):
    """Normalise PDF text: unify characters, drop icon glyphs and blank lines."""
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[-]", " ", text)  # icon fonts use the private-use area
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if line and re.search(r"[A-Za-z0-9]", line):
            lines.append(line)
    return lines


def _heading(line):
    """Return (heading, inline_content) when a line is a section heading."""
    candidate = line.replace("&", " and ")
    match = re.match(r"^\W*([A-Za-z][A-Za-z ]*?)\s*(?::|-|–|—)\s*(.+)$", candidate)
    if match:
        label = re.sub(r"\s+", " ", match.group(1)).lower()
        if label in SUMMARY_HEADINGS | SKILL_HEADINGS | EDUCATION_HEADINGS:
            return label, match.group(2).strip()
        return None, ""
    key = re.sub(r"\s+", " ", re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", candidate)).lower()
    if key in ALL_HEADINGS and len(line) <= 45:
        return key, ""
    return None, ""


def split_sections(lines):
    """Group lines under their headings; text before the first heading is 'header'."""
    sections = [("header", [])]
    for line in lines:
        key, inline = _heading(line)
        if key == "languages" and sections[-1][0] in SKILL_HEADINGS:
            key = None
        if key:
            sections.append((key, [inline] if inline else []))
        else:
            sections[-1][1].append(line)
    return sections


def _title_case(word):
    return "-".join(part[:1].upper() + part[1:].lower() for part in word.split("-"))


def extract_name(header_lines):
    for raw in header_lines[:8]:
        line = re.split(r"\s[|•·,]\s|\s{2,}", raw)[0].strip()
        words = line.split()
        if not 2 <= len(words) <= 4:
            continue
        if not all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*\.?", word) for word in words):
            continue
        if any(word.lower().strip(".") in NAME_STOPWORDS for word in words):
            continue
        if line.isupper() or line.islower():
            words = [_title_case(word) for word in words]
        return " ".join(words)
    return ""


def extract_email(text):
    match = EMAIL_RE.search(text)
    return match.group(0).lower() if match else ""


def extract_github(text):
    for match in GITHUB_RE.finditer(text):
        user = match.group(1)
        if user.lower() not in {"orgs", "features", "about", "login"}:
            return "https://github.com/" + user
    return ""


def _canonical(item):
    for name, pattern in _FULL_RE.items():
        if pattern.fullmatch(item):
            return name
    return None


def _section_items(lines):
    """Free-text items listed in a Skills section (e.g. 'Languages: C++, Python')."""
    items = []
    for line in lines:
        line = re.sub(r"^[\W_]+", "", line)
        if ":" in line and len(line.split(":", 1)[0].split()) <= 4:
            line = line.split(":", 1)[1]
        for item in re.split(r"[,;|•·▪●◦/]", line):
            item = item.strip(" .-–()[]\t")
            canonical = _canonical(item)
            if not canonical:
                words = item.split()
                if not 1 <= len(words) <= 3 or not 3 <= len(item) <= 30:
                    continue
                if not re.match(r"[A-Za-z]", item) or re.search(r"\d{3,}", item):
                    continue
            items.append(canonical or item.lower())
    return items


def _vocabulary_hits(text, patterns):
    hits = []
    for name, pattern in patterns.items():
        match = pattern.search(text)
        if match:
            hits.append((match.start(), name))
    return [name for _, name in sorted(hits)]


def extract_skills(lines, sections):
    def strip_links(text):
        return URL_RE.sub(" ", EMAIL_RE.sub(" ", text))

    skills = []
    for key, section_lines in sections:
        if key in SKILL_HEADINGS:
            section_text = strip_links("\n".join(section_lines))
            skills += _section_items(section_lines)
            skills += _vocabulary_hits(section_text, _SECTION_ONLY_RE)
            skills += _vocabulary_hits(section_text, _SKILL_RE)
    skills += _vocabulary_hits(strip_links("\n".join(lines)), _SKILL_RE)

    unique = []
    for skill in skills:
        if skill and skill not in unique:
            unique.append(skill)
    return unique[:MAX_SKILLS]


def _paragraph(lines):
    text = ""
    for line in lines:
        line = line.lstrip(" •▪●◦-–\t").rstrip()
        if not line:
            continue
        if text.endswith("-") and not text.endswith(" -"):
            text = text[:-1] + line
        else:
            text = (text + " " + line).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= SUMMARY_LIMIT:
        return text
    cut = text[:SUMMARY_LIMIT]
    end = cut.rfind(". ")
    return cut[: end + 1] if end > SUMMARY_LIMIT // 2 else cut.rsplit(" ", 1)[0]


def extract_summary(sections):
    """Prefer the resume's own summary; otherwise describe the latest education entry."""
    for key, section_lines in sections:
        if key in SUMMARY_HEADINGS and section_lines:
            summary = _paragraph(section_lines[:15])
            if summary:
                return summary, "summary"

    for key, section_lines in sections:
        if key not in EDUCATION_HEADINGS:
            continue
        degree = next((line for line in section_lines if DEGREE_RE.search(line)), "")
        institution = next((line for line in section_lines if INSTITUTION_RE.search(line)), "")
        years = next((YEARS_RE.search(line) for line in section_lines if YEARS_RE.search(line)), None)
        parts = [degree.strip(" ,;")]
        if institution and institution not in degree:
            parts.append(institution.strip(" ,;"))
        text = ", ".join(part for part in parts if part)
        if text:
            if years:
                text += " (%s–%s)" % (years.group(1), years.group(2))
            return text + ".", "education"
    return "", ""


def parse_resume_text(text):
    lines = clean_text(text)
    sections = split_sections(lines)
    header = sections[0][1] if sections[0][1] else lines[:8]
    joined = "\n".join(lines)

    name = extract_name(header)
    first, _, last = name.partition(" ")
    summary, summary_source = extract_summary(sections)
    return {
        "name": name,
        "first_name": first,
        "last_name": last,
        "email": extract_email(joined),
        "github": extract_github(joined),
        "skills": extract_skills(lines, sections),
        "summary": summary,
        "summary_source": summary_source,
    }
