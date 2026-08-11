import json
import pathlib

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.config import CV_DATA_DIR
from app.dependencies import require_admin
from app.routers.cv import _load_cv
from app.schemas.cv import CVData, CVUploadPreview
from app.services.cv_parser import extract_text, parse_cv_to_json
from app.services.translator import translate_cv_json

ALL_LOCALES = ("en", "fr", "fa")

router = APIRouter(dependencies=[Depends(require_admin)])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _cv_path(locale: str) -> pathlib.Path:
    return pathlib.Path(CV_DATA_DIR) / f"cv_data.{locale}.json"


@router.post("/admin/cv/upload", response_model=CVUploadPreview)
async def upload_cv(file: UploadFile = File(...)):
    if file.size and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    filename = (file.filename or "").lower()
    allowed_extensions = (".pdf", ".docx", ".md", ".txt")
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    text = await extract_text(file)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the file")

    try:
        en_data = await parse_cv_to_json(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CV parsing failed: {exc}") from exc

    preview = CVUploadPreview()
    try:
        preview.en = CVData.model_validate(en_data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Parsed CV has invalid structure: {exc}") from exc

    for target_locale in ("fr", "fa"):
        try:
            translated = await translate_cv_json(en_data, "en", target_locale)
            setattr(preview, target_locale, CVData.model_validate(translated))
        except Exception as exc:
            preview.translation_errors.append(f"{target_locale}: {exc}")

    return preview


@router.post("/admin/cv/{locale}/save", status_code=status.HTTP_200_OK)
def save_cv(locale: str, cv: CVData):
    if locale not in ALL_LOCALES:
        raise HTTPException(status_code=400, detail="Locale must be one of: en, fr, fa")

    path = _cv_path(locale)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cv.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"saved": locale, "path": str(path)}


@router.get("/admin/cv/{locale}", response_model=CVData)
def get_cv_admin(locale: str):
    if locale not in ALL_LOCALES:
        raise HTTPException(status_code=400, detail="Locale must be one of: en, fr, fa")
    try:
        return _load_cv(locale)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
