import httpx
from cachetools import TTLCache

from app.config import CACHE_TTL_SECONDS, GITHUB_TOKEN, GITHUB_USERNAME

_cache: TTLCache = TTLCache(maxsize=1, ttl=CACHE_TTL_SECONDS)
_CACHE_KEY = "repos"

GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"


def _shape_repo(repo: dict) -> dict:
    return {
        "name": repo["name"],
        "description": repo.get("description"),
        "url": repo["html_url"],
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "topics": repo.get("topics", []),
        "updated_at": repo.get("updated_at"),
        "fork": repo.get("fork", False),
    }


async def fetch_public_repos() -> list[dict]:
    if _CACHE_KEY in _cache:
        return _cache[_CACHE_KEY]

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    params = {"type": "public", "sort": "updated", "per_page": 100}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(GITHUB_API_URL, headers=headers, params=params)
        response.raise_for_status()
        repos = response.json()

    shaped = [_shape_repo(repo) for repo in repos if not repo.get("fork")]
    shaped.sort(key=lambda r: r["updated_at"] or "", reverse=True)

    _cache[_CACHE_KEY] = shaped
    return shaped


def is_cached() -> bool:
    return _CACHE_KEY in _cache
