from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.schemas.post import PostDetailOut, PostOut

router = APIRouter()


@router.get("/posts", response_model=list[PostOut])
def list_posts(
    locale: str = Query("en", pattern="^(en|fr|fa)$"),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Post).where(Post.published == True, Post.locale == locale)  # noqa: E712
    posts = db.execute(stmt).scalars().all()

    if tag:
        posts = [p for p in posts if tag in p.tags_list()]

    posts = sorted(posts, key=lambda p: p.created_at, reverse=True)
    return posts


@router.get("/posts/{slug}", response_model=PostDetailOut)
def get_post(
    slug: str,
    locale: str = Query("en", pattern="^(en|fr|fa)$"),
    db: Session = Depends(get_db),
):
    stmt = select(Post).where(
        Post.slug == slug,
        Post.locale == locale,
        Post.published == True,  # noqa: E712
    )
    post = db.execute(stmt).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
