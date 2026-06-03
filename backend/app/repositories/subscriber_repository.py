from sqlalchemy.orm import Session
from app.models.subscriber import Subscriber


class SubscriberRepository:
    @staticmethod
    def get_by_id(db: Session, subscriber_id: int):
        return db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(Subscriber).filter(Subscriber.email == email).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int):
        return db.query(Subscriber).filter(Subscriber.user_id == user_id).first()

    @staticmethod
    def create(db: Session, subscriber: Subscriber):
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)
        return subscriber

    @staticmethod
    def update(db: Session, subscriber: Subscriber, changes: dict):
        for key, value in changes.items():
            setattr(subscriber, key, value)
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)
        return subscriber

    @staticmethod
    def list_all(db: Session):
        return db.query(Subscriber).all()
