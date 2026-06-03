from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_auth0_sub(db: Session, auth0_sub: str):
        return db.query(User).filter(User.auth0_sub == auth0_sub).first()

    @staticmethod
    def get_by_provider_sub(db: Session, provider_sub: str):
        return UserRepository.get_by_auth0_sub(db, provider_sub)

    @staticmethod
    def create(db: Session, user: User):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User, changes: dict):
        for key, value in changes.items():
            setattr(user, key, value)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
