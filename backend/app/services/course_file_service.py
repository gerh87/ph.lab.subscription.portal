import hashlib
import tempfile
from uuid import uuid4

from fastapi import UploadFile

from app.core.database import SessionLocal
from app.core.storage import storage_client
from app.models.course import Course
from app.models.course_file import CourseFile
from app.models.enrollment import Enrollment
from app.repositories.course_file_repository import CourseFileRepository
from app.repositories.subscriber_repository import SubscriberRepository


class CourseFileService:
    ALLOWED_RESOURCE_TYPES = {"public_resource", "private_material"}

    @staticmethod
    def _clean_filename(filename: str | None) -> str:
        clean_name = (filename or "course-file").replace("\\", "/").split("/")[-1].strip()
        return clean_name or "course-file"

    @staticmethod
    async def upload(course_id: int, upload: UploadFile, user, resource_type: str = "public_resource"):
        db = SessionLocal()
        storage_key = None
        try:
            if resource_type not in CourseFileService.ALLOWED_RESOURCE_TYPES:
                return "invalid_resource_type"

            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None

            guid = str(uuid4())
            storage_key = guid
            original_filename = CourseFileService._clean_filename(upload.filename)
            content_type = upload.content_type or "application/octet-stream"
            digest = hashlib.sha256()
            size_bytes = 0

            with tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024) as temp_file:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    digest.update(chunk)
                    temp_file.write(chunk)

                temp_file.seek(0)
                storage_client.upload_fileobj(temp_file, storage_key, content_type)

            course_file = CourseFile(
                course_id=course_id,
                guid=guid,
                storage_key=storage_key,
                original_filename=original_filename,
                resource_type=resource_type,
                content_type=content_type,
                size_bytes=size_bytes,
                checksum_sha256=digest.hexdigest(),
                uploaded_by_user_id=user.id if user else None,
            )
            return CourseFileRepository.create(db, course_file)
        except Exception:
            if storage_key:
                try:
                    storage_client.delete_object(storage_key)
                except Exception:
                    pass
            raise
        finally:
            await upload.close()
            db.close()

    @staticmethod
    async def list_public_resources(course_id: int):
        db = SessionLocal()
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None
            return CourseFileRepository.list_by_course_and_type(db, course_id, "public_resource")
        finally:
            db.close()

    @staticmethod
    async def get_public_resource_download(course_id: int, file_id: int):
        db = SessionLocal()
        try:
            course_file = CourseFileRepository.get_by_id(db, file_id)
            if (
                not course_file
                or course_file.course_id != course_id
                or course_file.resource_type != "public_resource"
            ):
                return None
            return {
                "file": course_file,
                "object": storage_client.get_object(course_file.storage_key),
            }
        finally:
            db.close()

    @staticmethod
    async def list_for_course(course_id: int, user):
        db = SessionLocal()
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None
            if not CourseFileService._can_access_course_files(db, course_id, user):
                return "forbidden"
            return CourseFileRepository.list_by_course(db, course_id)
        finally:
            db.close()

    @staticmethod
    async def get_download(course_id: int, file_id: int, user):
        db = SessionLocal()
        try:
            course_file = CourseFileRepository.get_by_id(db, file_id)
            if not course_file or course_file.course_id != course_id:
                return None
            if not CourseFileService._can_access_course_files(db, course_id, user):
                return "forbidden"
            return {
                "file": course_file,
                "object": storage_client.get_object(course_file.storage_key),
            }
        finally:
            db.close()

    @staticmethod
    async def delete(course_id: int, file_id: int):
        db = SessionLocal()
        try:
            course_file = CourseFileRepository.get_by_id(db, file_id)
            if not course_file or course_file.course_id != course_id:
                return False
            storage_client.delete_object(course_file.storage_key)
            return CourseFileRepository.delete(db, course_file)
        finally:
            db.close()

    @staticmethod
    def _can_access_course_files(db, course_id: int, user) -> bool:
        if user and user.is_admin:
            return True
        if not user:
            return False
        subscriber = SubscriberRepository.get_by_user_id(db, user.id)
        if not subscriber:
            return False
        return (
            db.query(Enrollment)
            .filter(
                Enrollment.course_id == course_id,
                Enrollment.subscriber_id == subscriber.id,
                Enrollment.status == "active",
            )
            .first()
            is not None
        )
