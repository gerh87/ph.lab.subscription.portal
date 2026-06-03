from pydantic import BaseModel, EmailStr
from typing import Optional


class SubscriberBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None


class SubscriberCreate(SubscriberBase):
    pass


class SubscriberRead(SubscriberBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        orm_mode = True
