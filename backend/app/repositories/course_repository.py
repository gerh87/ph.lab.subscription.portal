from sqlalchemy.orm import Session
from app.models.course import Course


class CourseRepository:
    @staticmethod
    def create(db: Session, course: Course):
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def list_all(db: Session):
        return db.query(Course).all()

    @staticmethod
    def get_by_id(db: Session, course_id: int):
        return db.query(Course).filter(Course.id == course_id).first()

    @staticmethod
    def update(db: Session, course: Course, changes: dict):
        for k, v in changes.items():
            setattr(course, k, v)
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete(db: Session, course: Course):
        db.delete(course)
        db.commit()
        return True
