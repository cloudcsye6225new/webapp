from pydantic import BaseModel, EmailStr, HttpUrl, UUID4
from datetime import datetime


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr 
    password: str

class UserPostOut(BaseModel):
    first_name: str
    last_name: str
    email: str
class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    account_created: datetime
    account_updated: datetime
    is_verified: bool
    token: str
    expires_at: datetime

    class Config:
        orm_mode = True
    
class UserCredentials(BaseModel):
    first_name: str
    password: str

class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    password: str = None
    email: str = None
