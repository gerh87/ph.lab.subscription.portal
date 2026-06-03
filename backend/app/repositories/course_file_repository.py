from sqlalchemy.orm import Session

from app.models.course_file import CourseFile


class CourseFileRepository:
    @staticmethod
    def create(db: Session, course_file: CourseFile):
        db.add(course_file)
        db.commit()
        db.refresh(course_file)
        return course_file

    @staticmethod
    def list_by_course(db: Session, course_id: int):
        return (
            db.query(CourseFile)
            .filter(CourseFile.course_id == course_id)
            .order_by(CourseFile.created_at.desc(), CourseFile.id.desc())
            .all()
        )

    @staticmethod
    def list_by_course_and_type(db: Session, course_id: int, resource_type: str):
        return (
            db.query(CourseFile)
            .filter(
                CourseFile.course_id == course_id,
                CourseFile.resource_type == resource_type,
            )
            .order_by(CourseFile.created_at.desc(), CourseFile.id.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, file_id: int):
        return db.query(CourseFile).filter(CourseFile.id == file_id).first()

    @staticmethod
    def delete(db: Session, course_file: CourseFile):
        db.delete(course_file)
        db.commit()
        return True
