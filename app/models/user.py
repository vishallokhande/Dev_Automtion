from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    additional_details: Optional[str] = None
    linkedin_cookie: Optional[str] = None

class UserProfileResponse(UserProfileUpdate):
    id: str
    user_id: str
    resume_path: Optional[str] = None
    linkedin_cookie: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: str
    created_at: datetime
    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
