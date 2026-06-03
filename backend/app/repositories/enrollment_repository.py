from sqlalchemy.orm import Session
from app.models.enrollment import Enrollment


class EnrollmentRepository:
    @staticmethod
    def create(db: Session, enrollment: Enrollment):
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def list_all(db: Session):
        return db.query(Enrollment).all()
    
    @staticmethod
    def get_by_id(db: Session, id: int):
        return db.query(Enrollment).filter(Enrollment.id == id).first()

    @staticmethod
    def find_by_subscriber(db: Session, subscriber_id: int):
        return db.query(Enrollment).filter(Enrollment.subscriber_id == subscriber_id).all()

    @staticmethod
    def find_by_course(db: Session, course_id: int):
        return db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    @staticmethod
    def update(db: Session, enrollment: Enrollment):
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def delete(db: Session, enrollment: Enrollment):
        db.delete(enrollment)
        db.commit()
