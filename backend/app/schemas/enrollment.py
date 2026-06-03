from pydantic import BaseModel
from datetime import datetime


class EnrollmentCreate(BaseModel):
    subscriber_id: int
    course_id: int


class EnrollmentRead(EnrollmentCreate):
    id: int
    status: str
    payment_status: str
    created_at: datetime

    class Config:
        orm_mode = True
