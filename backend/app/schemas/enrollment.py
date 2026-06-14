from pydantic import BaseModel
from datetime import datetime


class EnrollmentCreate(BaseModel):
    subscriber_id: int
    course_id: int
    payment_method: str | None = None


class EnrollmentRead(EnrollmentCreate):
    id: int
    status: str
    payment_status: str
    payment_reference: str | None = None
    payment_provider_id: str | None = None
    payment_provider_status: str | None = None
    manual_payment_notes: str | None = None
    payment_requested_at: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime

    class Config:
        orm_mode = True
