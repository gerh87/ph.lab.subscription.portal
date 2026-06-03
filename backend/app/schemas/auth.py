from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
