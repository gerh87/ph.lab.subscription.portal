from app.repositories.course_repository import CourseRepository
from app.schemas.course import CourseCreate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.core.database import SessionLocal


class CourseService:
    @staticmethod
    def _with_capacity(db, course, include_zoom=False):
        active_count = db.query(Enrollment).filter(
            Enrollment.course_id == course.id,
            Enrollment.status == "active",
        ).count()
        capacity = int(course.max_students or 0)
        available = None if capacity <= 0 else max(capacity - active_count, 0)
        payload = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "max_students": course.max_students,
            "scheduled_date": course.scheduled_date,
            "scheduled_time": course.scheduled_time,
            "active_enrollments": active_count,
            "available_seats": available,
        }
        if include_zoom:
            payload["zoom_url"] = course.zoom_url
        return payload

    @staticmethod
    async def create(course_in: CourseCreate):
        db = SessionLocal()
        try:
            course = Course(**course_in.model_dump())
            return CourseService._with_capacity(db, CourseRepository.create(db, course))
        finally:
            db.close()

    @staticmethod
    async def list_all():
        db = SessionLocal()
        try:
            return [CourseService._with_capacity(db, course) for course in CourseRepository.list_all(db)]
        finally:
            db.close()

    @staticmethod
    async def get(course_id: int):
        db = SessionLocal()
        try:
            course = CourseRepository.get_by_id(db, course_id)
            return CourseService._with_capacity(db, course) if course else None
        finally:
            db.close()

    @staticmethod
    async def list_all_admin():
        db = SessionLocal()
        try:
            return [CourseService._with_capacity(db, course, include_zoom=True) for course in CourseRepository.list_all(db)]
        finally:
            db.close()

    @staticmethod
    async def update(course_id: int, changes: dict):
        db = SessionLocal()
        try:
            course = CourseRepository.get_by_id(db, course_id)
            if not course:
                return None
            return CourseService._with_capacity(db, CourseRepository.update(db, course, changes))
        finally:
            db.close()

    @staticmethod
    async def delete(course_id: int):
        db = SessionLocal()
        try:
            course = CourseRepository.get_by_id(db, course_id)
            if not course:
                return False
            return CourseRepository.delete(db, course)
        finally:
            db.close()
