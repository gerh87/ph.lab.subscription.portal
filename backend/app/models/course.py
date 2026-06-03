from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, func
from app.models import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), default=0)
    max_students = Column(Integer, default=0)
    scheduled_date = Column(Date, nullable=True)
    zoom_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
