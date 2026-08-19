from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Response, status
from jose import jwt
from pydantic import BaseModel

from app.config import (
    ADMIN_PASSWORD,
    ADMIN_PASSWORD_HASH,
    ADMIN_USERNAME,
    COOKIE_SECURE,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)
from app.dependencies import JWT_ALGORITHM

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


def _verify_password(plain: str) -> bool:
    if ADMIN_PASSWORD_HASH:
        return bcrypt.checkpw(plain.encode(), ADMIN_PASSWORD_HASH.encode())
    if ADMIN_PASSWORD:
        return plain == ADMIN_PASSWORD
    return False


def _create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/admin/login")
def login(body: LoginRequest, response: Response):
    if not ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin credentials not configured",
        )
    if body.username != ADMIN_USERNAME or not _verify_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = _create_token(body.username)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=JWT_EXPIRE_MINUTES * 60,
    )
    return {"token": token, "expires_in": JWT_EXPIRE_MINUTES * 60}


@router.post("/admin/logout")
def logout(response: Response):
    response.delete_cookie("admin_token", samesite="strict", secure=COOKIE_SECURE)
    return {"status": "logged out"}
