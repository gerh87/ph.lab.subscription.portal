from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRead(BaseModel):
    id: int
    email: EmailStr
    auth0_sub: Optional[str] = None
    full_name: Optional[str] = None
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_admin: Optional[bool] = None
