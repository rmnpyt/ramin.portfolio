from fastapi import Cookie, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import ADMIN_USERNAME, API_KEY, JWT_SECRET

JWT_ALGORITHM = "HS256"


def require_api_key(x_api_key: str = Header(...)):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server",
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def require_admin(
    x_api_key: str | None = Header(None),
    admin_token: str | None = Cookie(None),
):
    # API key path — used by external agents
    if x_api_key is not None:
        if not API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key not configured on server",
            )
        if x_api_key != API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return

    # JWT cookie path — used by admin UI
    if admin_token is not None:
        try:
            payload = jwt.decode(admin_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session — please log in again",
            )
        if payload.get("sub") != ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token subject mismatch",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (X-API-Key header or admin session cookie)",
    )
