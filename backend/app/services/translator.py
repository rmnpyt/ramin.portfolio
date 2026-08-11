import json
from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL

LOCALE_NAMES = {
    "en": "English",
    "fr": "French",
    "fa": "Persian (Farsi)",
}

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def translate_post_content(
    title: str,
    excerpt: str,
    content: str,
    source_locale: str,
    target_locale: str,
) -> dict:
    source_name = LOCALE_NAMES[source_locale]
    target_name = LOCALE_NAMES[target_locale]

    user_prompt = (
        f"Translate the following blog post from {source_name} to {target_name}.\n"
        "Preserve all Markdown formatting exactly (headings, bold, italic, code blocks, "
        "links, lists). Do not translate code snippets inside backticks.\n"
        'Return a JSON object with exactly these keys: "title", "excerpt", "content".\n\n'
        f"Source:\n{json.dumps({'title': title, 'excerpt': excerpt, 'content': content}, ensure_ascii=False)}"
    )

    response = await _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert translator. Output only valid JSON with keys "
                    '"title", "excerpt", and "content". Never add extra keys.'
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw = json.loads(response.choices[0].message.content)
    return {
        "title": raw.get("title") or title,
        "excerpt": raw.get("excerpt") or excerpt,
        "content": raw.get("content") or content,
    }


async def translate_cv_json(cv_data: dict, source_locale: str, target_locale: str) -> dict:
    source_name = LOCALE_NAMES[source_locale]
    target_name = LOCALE_NAMES[target_locale]

    user_prompt = (
        f"Translate this CV JSON from {source_name} to {target_name}.\n\n"
        "TRANSLATE these fields:\n"
        "- basics.title, basics.summary, basics.location (city/country names)\n"
        "- experience[].role, experience[].highlights (each bullet point)\n"
        "- education[].degree\n"
        "- skills[].category (keep items[] unchanged — they are technical terms)\n"
        "- languages[].name, languages[].level\n"
        "- softSkills[] (each entry)\n\n"
        "KEEP UNCHANGED:\n"
        "- basics.name, basics.email, basics.phone, basics.links\n"
        "- experience[].company, experience[].location (keep city names as-is)\n"
        "- experience[].startDate, experience[].endDate\n"
        "- education[].institution, education[].startDate, education[].endDate\n"
        "- skills[].items (technical terms, tool names, language names like Python, Docker)\n"
        "- certifications[].name, certifications[].issuer, certifications[].date\n\n"
        "Return the complete JSON object with the same structure.\n\n"
        f"CV JSON:\n{json.dumps(cv_data, ensure_ascii=False)}"
    )

    response = await _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert CV translator. Return only valid JSON with the same "
                    "structure as the input. Never add or remove keys."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)
