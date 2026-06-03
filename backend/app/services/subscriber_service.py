from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.subscriber import SubscriberCreate
from app.models.subscriber import Subscriber
from app.core.database import SessionLocal


class SubscriberService:
    @staticmethod
    async def create(sub_in: SubscriberCreate, user=None):
        db = SessionLocal()
        try:
            if user:
                existing = SubscriberRepository.get_by_user_id(db, user.id)
                changes = {
                    "full_name": sub_in.full_name,
                    "email": sub_in.email,
                    "phone": sub_in.phone,
                    "user_id": user.id,
                }
                if existing:
                    return SubscriberRepository.update(db, existing, changes)

                existing = SubscriberRepository.get_by_email(db, user.email)
                if existing and existing.user_id is None:
                    return SubscriberRepository.update(db, existing, changes)

            sub = Subscriber(**sub_in.model_dump(), user_id=user.id if user else None)
            return SubscriberRepository.create(db, sub)
        finally:
            db.close()

    @staticmethod
    async def list_all():
        db = SessionLocal()
        try:
            return SubscriberRepository.list_all(db)
        finally:
            db.close()
