from datetime import datetime
from pydantic import BaseModel, field_validator
import json


class PostOut(BaseModel):
    slug: str
    locale: str
    title: str
    excerpt: str
    tags: list[str]
    published: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return []
        return v

    model_config = {"from_attributes": True}


class PostDetailOut(PostOut):
    content: str


class PostCreate(BaseModel):
    slug: str
    locale: str
    title: str
    excerpt: str = ""
    content: str = ""
    tags: list[str] = []
    published: bool = False


class PostUpdate(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    published: bool | None = None


class PostCreateResponse(BaseModel):
    source: PostDetailOut
    translations: list[PostDetailOut]
    translation_errors: list[str] = []
