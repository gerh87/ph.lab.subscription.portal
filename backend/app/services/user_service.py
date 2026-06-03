from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.database import SessionLocal


class UserService:
    @staticmethod
    def sync_external_user(claims: dict):
        provider_sub = claims.get("sub")
        email = claims.get("email")
        if not provider_sub or not email:
            return None

        db = SessionLocal()
        try:
            user = UserRepository.get_by_provider_sub(db, provider_sub)
            if not user:
                user = UserRepository.get_by_email(db, email)

            changes = {
                "auth0_sub": provider_sub,
                "email": email,
                "full_name": claims.get("name") or claims.get("nickname") or email,
                "picture": claims.get("picture"),
            }

            if user:
                return UserRepository.update(db, user, changes)

            user = User(
                email=email,
                password_hash="EXTERNAL_IDP",
                auth0_sub=provider_sub,
                full_name=changes["full_name"],
                picture=changes["picture"],
                is_admin=False,
            )
            return UserRepository.create(db, user)
        finally:
            db.close()

    sync_auth0_user = sync_external_user

    @staticmethod
    def list_all():
        db = SessionLocal()
        try:
            return db.query(User).all()
        finally:
            db.close()

    @staticmethod
    def get(user_id: int):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    @staticmethod
    def update(user_id: int, changes: dict):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            for k, v in changes.items():
                setattr(user, k, v)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    @staticmethod
    def delete(user_id: int):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        finally:
            db.close()
