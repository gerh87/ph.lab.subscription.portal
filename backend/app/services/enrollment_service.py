from datetime import datetime, timezone

from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.enrollment import EnrollmentCreate
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.core.database import SessionLocal

PAYMENT_METHODS = {"manual", "mercadopago"}


def _enrollment_payload(enrollment: Enrollment):
    return {
        "id": enrollment.id,
        "subscriber_id": enrollment.subscriber_id,
        "course_id": enrollment.course_id,
        "status": enrollment.status,
        "payment_status": enrollment.payment_status,
        "payment_method": enrollment.payment_method,
        "payment_reference": enrollment.payment_reference,
        "payment_provider_id": enrollment.payment_provider_id,
        "payment_provider_status": enrollment.payment_provider_status,
        "manual_payment_notes": enrollment.manual_payment_notes,
        "payment_requested_at": enrollment.payment_requested_at,
        "paid_at": enrollment.paid_at,
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
            existing = db.query(Enrollment).filter(
                Enrollment.course_id == enrollment_in.course_id,
                Enrollment.subscriber_id == subscriber_id,
                Enrollment.status.in_(["active", "pending_payment"]),
            ).first()
            if existing:
                requested_method = EnrollmentService.normalize_payment_method(enrollment_in.payment_method)
                if existing.status == "pending_payment" and requested_method:
                    existing.payment_method = requested_method
                    existing.payment_requested_at = existing.payment_requested_at or datetime.now(timezone.utc)
                    return EnrollmentRepository.update(db, existing)
                return existing

            capacity = int(course.max_students or 0)
            if capacity > 0:
                active_count = db.query(Enrollment).filter(
                    Enrollment.course_id == enrollment_in.course_id,
                    Enrollment.status == "active",
                ).count()
                if active_count >= capacity:
                    return "full"
            price = float(course.price or 0)
            payment_method = "free"
            payment_requested_at = None
            paid_at = datetime.now(timezone.utc)
            if price > 0:
                payment_method = EnrollmentService.normalize_payment_method(enrollment_in.payment_method) or "manual"
                payment_requested_at = datetime.now(timezone.utc)
                paid_at = None
            e = Enrollment(
                subscriber_id=subscriber_id,
                course_id=enrollment_in.course_id,
                status="pending_payment" if price > 0 else "active",
                payment_status="pending" if price > 0 else "paid",
                payment_method=payment_method,
                payment_requested_at=payment_requested_at,
                paid_at=paid_at,
            )
            return EnrollmentRepository.create(db, e)
        finally:
            db.close()

    @staticmethod
    def normalize_payment_method(method: str | None):
        if not method:
            return None
        normalized = str(method).strip().lower()
        return normalized if normalized in PAYMENT_METHODS else None

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
    async def mark_paid(
        id: int,
        payment_method: str | None = None,
        payment_reference: str | None = None,
        manual_payment_notes: str | None = None,
        payment_provider_id: str | None = None,
        payment_provider_status: str | None = None,
    ):
        db = SessionLocal()
        try:
            e = EnrollmentRepository.get_by_id(db, id)
            if not e:
                return None
            if e.status != "active":
                course = db.query(Course).filter(Course.id == e.course_id).first()
                capacity = int(course.max_students or 0) if course else 0
                if capacity > 0:
                    active_count = db.query(Enrollment).filter(
                        Enrollment.course_id == e.course_id,
                        Enrollment.status == "active",
                        Enrollment.id != e.id,
                    ).count()
                    if active_count >= capacity:
                        return "full"
            e.payment_status = 'paid'
            e.status = 'active'
            e.paid_at = datetime.now(timezone.utc)
            if payment_method:
                e.payment_method = payment_method
            elif not e.payment_method:
                e.payment_method = "manual"
            if payment_reference is not None:
                e.payment_reference = payment_reference
            if manual_payment_notes is not None:
                e.manual_payment_notes = manual_payment_notes
            if payment_provider_id is not None:
                e.payment_provider_id = payment_provider_id
            if payment_provider_status is not None:
                e.payment_provider_status = payment_provider_status
            return EnrollmentRepository.update(db, e)
        finally:
            db.close()

    @staticmethod
    async def update_payment_attempt(
        id: int,
        payment_method: str | None = None,
        payment_provider_id: str | None = None,
        payment_provider_status: str | None = None,
        payment_reference: str | None = None,
    ):
        db = SessionLocal()
        try:
            e = EnrollmentRepository.get_by_id(db, id)
            if not e:
                return None
            if payment_method:
                e.payment_method = payment_method
            if payment_provider_id is not None:
                e.payment_provider_id = payment_provider_id
            if payment_provider_status is not None:
                e.payment_provider_status = payment_provider_status
            if payment_reference is not None:
                e.payment_reference = payment_reference
            e.payment_requested_at = datetime.now(timezone.utc)
            return EnrollmentRepository.update(db, e)
        finally:
            db.close()
