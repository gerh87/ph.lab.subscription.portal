from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.enrollment import EnrollmentCreate
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.core.database import SessionLocal


def _enrollment_payload(enrollment: Enrollment):
    return {
        "id": enrollment.id,
        "subscriber_id": enrollment.subscriber_id,
        "course_id": enrollment.course_id,
        "status": enrollment.status,
        "payment_status": enrollment.payment_status,
        "created_at": enrollment.created_at,
    }


class EnrollmentService:
    @staticmethod
    async def create(enrollment_in: EnrollmentCreate, user=None):
        db = SessionLocal()
        try:
            subscriber_id = enrollment_in.subscriber_id
            if user and not user.is_admin:
                subscriber = SubscriberRepository.get_by_user_id(db, user.id)
                if not subscriber:
                    return None
                subscriber_id = subscriber.id

            course = db.query(Course).filter(Course.id == enrollment_in.course_id).first()
            if not course:
                return None
            capacity = int(course.max_students or 0)
            if capacity > 0:
                active_count = db.query(Enrollment).filter(
                    Enrollment.course_id == enrollment_in.course_id,
                    Enrollment.status == "active",
                ).count()
                if active_count >= capacity:
                    return "full"
            e = Enrollment(subscriber_id=subscriber_id, course_id=enrollment_in.course_id)
            return EnrollmentRepository.create(db, e)
        finally:
            db.close()

    @staticmethod
    async def list_all():
        db = SessionLocal()
        try:
            return EnrollmentRepository.list_all(db)
        finally:
            db.close()
    
    @staticmethod
    async def get(id: int):
        db = SessionLocal()
        try:
            return EnrollmentRepository.get_by_id(db, id)
        finally:
            db.close()

    @staticmethod
    async def list_by_subscriber(subscriber_id: int):
        db = SessionLocal()
        try:
            return EnrollmentRepository.find_by_subscriber(db, subscriber_id)
        finally:
            db.close()

    @staticmethod
    async def list_by_course(course_id: int):
        db = SessionLocal()
        try:
            return EnrollmentRepository.find_by_course(db, course_id)
        finally:
            db.close()

    @staticmethod
    async def cancel(id: int):
        db = SessionLocal()
        try:
            e = EnrollmentRepository.get_by_id(db, id)
            if not e:
                return None
            payload = _enrollment_payload(e)
            EnrollmentRepository.delete(db, e)
            return payload
        finally:
            db.close()

    @staticmethod
    async def cancel_for_user(id: int, user):
        db = SessionLocal()
        try:
            e = EnrollmentRepository.get_by_id(db, id)
            if not e:
                return None
            if not user.is_admin:
                subscriber = SubscriberRepository.get_by_id(db, e.subscriber_id)
                if not subscriber or subscriber.user_id != user.id:
                    return "forbidden"
            payload = _enrollment_payload(e)
            EnrollmentRepository.delete(db, e)
            return payload
        finally:
            db.close()

    @staticmethod
    async def mark_paid(id: int):
        db = SessionLocal()
        try:
            e = EnrollmentRepository.get_by_id(db, id)
            if not e:
                return None
            e.payment_status = 'paid'
            e.status = 'active'
            return EnrollmentRepository.update(db, e)
        finally:
            db.close()
