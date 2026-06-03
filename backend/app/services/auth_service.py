from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import UserCreate, TokenSchema
from app.models.user import User
from app.core.database import SessionLocal


class AuthService:
    @staticmethod
    async def register(user_in: UserCreate) -> TokenSchema:
        db = SessionLocal()
        try:
            existing = UserRepository.get_by_email(db, user_in.email)
            if existing:
                raise ValueError("User already exists")
            user = User(email=user_in.email, password_hash=hash_password(user_in.password), full_name=user_in.full_name)
            user = UserRepository.create(db, user)
            token = create_access_token(subject=str(user.id))
            return TokenSchema(access_token=token)
        finally:
            db.close()

    @staticmethod
    async def login(email: str, password: str) -> TokenSchema | None:
        db = SessionLocal()
        try:
            user = UserRepository.get_by_email(db, email)
            if not user:
                return None
            if not verify_password(password, user.password_hash):
                return None
            token = create_access_token(subject=str(user.id))
            return TokenSchema(access_token=token)
        finally:
            db.close()

    @staticmethod
    async def dev_token() -> TokenSchema | None:
        """Return token for first user (dev helper)."""
        db = SessionLocal()
        try:
            user = db.query(User).order_by(User.id.asc()).first()
            if not user:
                return None
            token = create_access_token(subject=str(user.id))
            return TokenSchema(access_token=token)
        finally:
            db.close()
