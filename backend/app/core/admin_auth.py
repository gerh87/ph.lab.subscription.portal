from fastapi import Depends, HTTPException, Request, status

from app.api.v1.auth import _bearer_token
from app.core.database import SessionLocal
from app.core.oidc import get_oidc_profile
from app.repositories.user_repository import UserRepository


async def require_user(request: Request):
    token = _bearer_token(request)
    claims = get_oidc_profile(token)
    provider_sub = claims.get("sub")
    email = claims.get("email")

    db = SessionLocal()
    try:
        user = UserRepository.get_by_provider_sub(db, provider_sub) if provider_sub else None
        if not user and email:
            user = UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not synced")
        return user
    finally:
        db.close()


async def require_admin(request: Request):
    token = _bearer_token(request)
    claims = get_oidc_profile(token)
    provider_sub = claims.get("sub")
    email = claims.get("email")

    db = SessionLocal()
    try:
        user = UserRepository.get_by_provider_sub(db, provider_sub) if provider_sub else None
        if not user and email:
            user = UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not synced")
        if not user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        return user
    finally:
        db.close()


User = Depends(require_user)
AdminUser = Depends(require_admin)
