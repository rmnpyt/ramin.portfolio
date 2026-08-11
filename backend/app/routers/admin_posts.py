import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.post import Post
from app.schemas.post import PostCreate, PostCreateResponse, PostDetailOut, PostOut, PostUpdate
from app.services.translator import translate_post_content

ALL_LOCALES = ("en", "fr", "fa")

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/posts", response_model=list[PostOut])
def list_all_posts(
    locale: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Post)
    if locale:
        stmt = stmt.where(Post.locale == locale)
    posts = db.execute(stmt).scalars().all()
    return sorted(posts, key=lambda p: p.created_at, reverse=True)


def _insert_post(db: Session, slug: str, locale: str, title: str, excerpt: str,
                 content: str, tags: list, published: bool) -> Post:
    post = Post(
        slug=slug,
        locale=locale,
        title=title,
        excerpt=excerpt,
        content=content,
        tags=json.dumps(tags),
        published=published,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.post("/admin/posts", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_post(body: PostCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(Post).where(Post.slug == body.slug, Post.locale == body.locale)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post '{body.slug}' already exists for locale '{body.locale}'",
        )

    source_post = _insert_post(
        db, body.slug, body.locale, body.title, body.excerpt,
        body.content, body.tags, body.published,
    )

    translations: list[Post] = []
    translation_errors: list[str] = []

    for target_locale in ALL_LOCALES:
        if target_locale == body.locale:
            continue

        already_exists = db.execute(
            select(Post).where(Post.slug == body.slug, Post.locale == target_locale)
        ).scalar_one_or_none()
        if already_exists:
            continue

        try:
            translated = await translate_post_content(
                title=body.title,
                excerpt=body.excerpt,
                content=body.content,
                source_locale=body.locale,
                target_locale=target_locale,
            )
            translated_post = _insert_post(
                db, body.slug, target_locale,
                translated["title"], translated["excerpt"], translated["content"],
                body.tags, False,  # always draft until reviewed
            )
            translations.append(translated_post)
        except Exception as exc:
            translation_errors.append(f"{target_locale}: {exc}")

    return PostCreateResponse(
        source=PostDetailOut.model_validate(source_post),
        translations=[PostDetailOut.model_validate(p) for p in translations],
        translation_errors=translation_errors,
    )


@router.put("/admin/posts/{slug}/{locale}", response_model=PostDetailOut)
def update_post(slug: str, locale: str, body: PostUpdate, db: Session = Depends(get_db)):
    post = db.execute(
        select(Post).where(Post.slug == slug, Post.locale == locale)
    ).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    if body.title is not None:
        post.title = body.title
    if body.excerpt is not None:
        post.excerpt = body.excerpt
    if body.content is not None:
        post.content = body.content
    if body.tags is not None:
        post.tags = json.dumps(body.tags)
    if body.published is not None:
        post.published = body.published

    post.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/admin/posts/{slug}/publish")
def set_publish_status(slug: str, published: bool, db: Session = Depends(get_db)):
    posts = db.execute(select(Post).where(Post.slug == slug)).scalars().all()
    if not posts:
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.now(timezone.utc)
    for post in posts:
        post.published = published
        post.updated_at = now
    db.commit()

    return {"slug": slug, "published": published, "locales_updated": len(posts)}


@router.delete("/admin/posts/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(slug: str, db: Session = Depends(get_db)):
    result = db.execute(delete(Post).where(Post.slug == slug))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    db.commit()
