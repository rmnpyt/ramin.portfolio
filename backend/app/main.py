from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import CORS_ORIGINS
from app.database import init_db
from app.routers import repos, posts, admin_posts, cv, admin_cv, admin_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Portfolio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(repos.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(admin_posts.router, prefix="/api")
app.include_router(cv.router, prefix="/api")
app.include_router(admin_cv.router, prefix="/api")
app.include_router(admin_auth.router, prefix="/api")


_ADMIN_HTML = Path(__file__).parent / "admin" / "index.html"


@app.get("/admin", include_in_schema=False)
async def admin_panel():
    return FileResponse(_ADMIN_HTML, media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok"}
