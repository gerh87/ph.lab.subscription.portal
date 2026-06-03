from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CourseFileRead(BaseModel):
    id: int
    course_id: int
    guid: str
    original_filename: str
    resource_type: str
    content_type: Optional[str] = None
    size_bytes: int
    checksum_sha256: Optional[str] = None
    uploaded_by_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
