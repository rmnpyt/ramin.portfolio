from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.services.github import fetch_public_repos, is_cached

router = APIRouter()


@router.get("/repos")
async def get_repos():
    cached_before = is_cached()
    try:
        repos = await fetch_public_repos()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch GitHub repos: {exc}") from exc

    return JSONResponse(
        content=repos,
        headers={"X-Cache": "HIT" if cached_before else "MISS"},
    )
