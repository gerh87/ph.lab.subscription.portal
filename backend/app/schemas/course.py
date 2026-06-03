from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[Decimal] = 0
    max_students: Optional[int] = 0
    scheduled_date: Optional[date] = None


class CourseCreate(CourseBase):
    zoom_url: Optional[str] = None


class CourseRead(CourseBase):
    id: int
    active_enrollments: int = 0
    available_seats: Optional[int] = None

    class Config:
        orm_mode = True


class CourseAdminRead(CourseRead):
    zoom_url: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    max_students: Optional[int] = None
    scheduled_date: Optional[date] = None
    zoom_url: Optional[str] = None
