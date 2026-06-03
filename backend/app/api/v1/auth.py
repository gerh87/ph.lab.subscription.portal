from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status
from jose import jwt, JWTError
from app.schemas.auth import TokenSchema, UserCreate
from app.schemas.user import UserRead
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.core.config import settings
from app.core.oidc import get_oidc_profile

router = APIRouter()


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return auth.split(" ", 1)[1]


@router.post("/register", response_model=TokenSchema)
async def register(user: UserCreate):
    token = await AuthService.register(user)
    return token


@router.post("/login", response_model=TokenSchema)
async def login(form_data: UserCreate):
    token = await AuthService.login(form_data.email, form_data.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return token


@router.get('/me')
async def me(request: Request):
    token = _bearer_token(request)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get('sub')
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        user = UserService.get(int(sub))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')


@router.post("/sync", response_model=UserRead)
async def sync_external_user(request: Request):
    token = _bearer_token(request)
    claims = get_oidc_profile(token)
    user = UserService.sync_external_user(claims)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identity provider profile is incomplete")
    return user
