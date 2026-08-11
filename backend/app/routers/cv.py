import json
import pathlib

from fastapi import APIRouter, HTTPException

from app.config import CV_DATA_DIR
from app.schemas.cv import CVData

router = APIRouter()

_SEED_DIR = pathlib.Path(__file__).parent.parent / "data" / "cv"


def _cv_path(locale: str) -> pathlib.Path:
    return pathlib.Path(CV_DATA_DIR) / f"cv_data.{locale}.json"


def _load_cv(locale: str) -> dict:
    path = _cv_path(locale)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    seed = _SEED_DIR / f"cv_data.{locale}.json"
    if seed.exists():
        return json.loads(seed.read_text(encoding="utf-8"))

    raise FileNotFoundError(f"No CV data found for locale '{locale}'")


@router.get("/cv/{locale}", response_model=CVData)
def get_cv(locale: str):
    if locale not in ("en", "fr", "fa"):
        raise HTTPException(status_code=400, detail="Locale must be one of: en, fr, fa")
    try:
        return _load_cv(locale)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
