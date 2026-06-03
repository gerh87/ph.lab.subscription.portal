from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.models import Base


class CourseFile(Base):
    __tablename__ = "course_files"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    guid = Column(String(36), nullable=False, unique=True, index=True)
    storage_key = Column(String(128), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    resource_type = Column(String(40), nullable=False, default="public_resource")
    content_type = Column(String(255), nullable=True)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    checksum_sha256 = Column(String(64), nullable=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course")
    uploaded_by = relationship("User")
