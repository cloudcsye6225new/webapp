from pydantic import BaseModel, EmailStr, HttpUrl, UUID4
from datetime import datetime


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr 
    password: str

class UserOut(BaseModel):
    first_name: str
    last_name: str
    email: str
    
class UserCredentials(BaseModel):
    first_name: str
    password: str

class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    password: str = None
    email: str = None
