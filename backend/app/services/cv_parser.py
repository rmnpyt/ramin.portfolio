import io
import json

from fastapi import UploadFile

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.translator import _get_client

MAX_TEXT_CHARS = 20_000

CV_JSON_SCHEMA = """
{
  "basics": {
    "name": "Full name",
    "title": "Job title",
    "summary": "Professional summary paragraph",
    "location": "City, Province/State, Country",
    "email": "email@example.com",
    "phone": "+1 000-000-0000",
    "links": {
      "github": "https://github.com/username",
      "linkedin": "https://linkedin.com/in/username",
      "website": "https://example.com"
    }
  },
  "experience": [
    {
      "company": "Company Name",
      "role": "Job Title",
      "location": "City, Country",
      "startDate": "YYYY-MM",
      "endDate": "YYYY-MM or null if current position",
      "highlights": ["Achievement or responsibility as a full sentence"]
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Degree Name in Field",
      "startDate": "YYYY",
      "endDate": "YYYY"
    }
  ],
  "skills": [
    {"category": "Category Name", "items": ["Skill1", "Skill2"]}
  ],
  "certifications": [
    {"name": "Certification Name", "issuer": "Issuer", "date": "YYYY-MM"}
  ],
  "languages": [
    {"name": "Language", "level": "Proficiency level"}
  ],
  "softSkills": ["Soft skill 1", "Soft skill 2"]
}
"""


async def _extract_text_pdf(data: bytes) -> str:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


async def _extract_text_docx(data: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


async def extract_text(file: UploadFile) -> str:
    data = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf") or file.content_type == "application/pdf":
        text = await _extract_text_pdf(data)
    elif filename.endswith(".docx") or file.content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        text = await _extract_text_docx(data)
    else:
        text = data.decode("utf-8", errors="replace")

    return text[:MAX_TEXT_CHARS]


async def parse_cv_to_json(text: str) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    prompt = (
        "Parse the following CV/resume text into this exact JSON structure.\n"
        "Rules:\n"
        "- Dates in YYYY-MM format (year-only dates use YYYY).\n"
        "- Use null for endDate when a position is current.\n"
        "- Group technical skills into logical categories.\n"
        "- Write each highlight as a complete, self-contained sentence.\n"
        "- If a field is not found in the text, use an empty string or empty list.\n"
        "- Do not invent information that is not in the source text.\n\n"
        f"Expected JSON structure:\n{CV_JSON_SCHEMA}\n\n"
        f"CV text:\n{text}"
    )

    response = await _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at parsing CV/resume documents into structured JSON. "
                    "Return only valid JSON matching the schema exactly. "
                    "Never add keys that are not in the schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    return json.loads(response.choices[0].message.content)
