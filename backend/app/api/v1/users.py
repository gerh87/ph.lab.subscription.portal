from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.user import UserRead, UserUpdate
from app.schemas.auth import UserCreate
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password
from app.core.database import SessionLocal
from app.core.admin_auth import require_admin

router = APIRouter()


@router.get('/', response_model=List[UserRead])
async def list_users(_admin=Depends(require_admin)):
    return UserService.list_all()


@router.post('/', response_model=UserRead)
async def create_user(user: UserCreate, _admin=Depends(require_admin)):
    db = SessionLocal()
    try:
        existing = UserRepository.get_by_email(db, user.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
        from app.models.user import User
        u = User(email=user.email, password_hash=hash_password(user.password), full_name=user.full_name)
        return UserRepository.create(db, u)
    finally:
        db.close()


@router.get('/{user_id}', response_model=UserRead)
async def get_user(user_id: int, _admin=Depends(require_admin)):
    user = UserService.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return user


@router.put('/{user_id}', response_model=UserRead)
async def update_user(user_id: int, changes: UserUpdate, _admin=Depends(require_admin)):
    updated = UserService.update(user_id, {k: v for k, v in changes.model_dump().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return updated


@router.delete('/{user_id}')
async def delete_user(user_id: int, _admin=Depends(require_admin)):
    ok = UserService.delete(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return {'deleted': True}
