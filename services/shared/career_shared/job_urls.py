from urllib.parse import urlsplit
from pydantic import HttpUrl, TypeAdapter


def validate_job_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    TypeAdapter(HttpUrl).validate_python(value)
    parsed = urlsplit(value)
    if parsed.username is not None or parsed.password is not None or any(c.isspace() for c in value):
        raise ValueError("Use a public HTTP(S) job URL without credentials or whitespace")
    return value


def is_complete_job_analysis(jobs, job_url: str) -> bool:
    """Validate a single report before persisting provider-generated values."""
    if not isinstance(jobs, list) or len(jobs) != 1 or not isinstance(jobs[0], dict):
        return False
    job = jobs[0]

    def nonempty_text(value):
        return isinstance(value, str) and bool(value.strip())

    def bilingual_text(value):
        return isinstance(value, dict) and all(nonempty_text(value.get(lang)) for lang in ("en", "tr"))

    if (job.get("job_url") != job_url
            or not all(nonempty_text(job.get(key)) for key in ("company_name", "job_title"))
            or not isinstance(job.get("is_eligible"), bool)
            or not bilingual_text(job.get("summary"))):
        return False
    score = job.get("match_score")
    if type(score) not in (int, float) or not 0 <= score <= 100:
        return False
    if job.get("country") is not None and not isinstance(job["country"], str):
        return False
    for key in ("missing_skills", "recommended_certifications"):
        items = job.get(key)
        if not isinstance(items, list) or not all(bilingual_text(item) for item in items):
            return False
    return True
