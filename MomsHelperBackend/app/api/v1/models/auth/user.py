from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class UserCreate(BaseModel):
    username: str
    lastName: str
    firstName: str
    middleName: str
    password: str


class UserCreateResponse(BaseModel):
    id: str
    username: str
    lastName: str
    firstName: str
    middleName: str
    is_active: bool
    is_superuser: bool
    role_id: Optional[str] = None
    created_at: datetime


class UserBase(BaseModel):
    username: str
    lastName: str
    firstName: str
    middleName: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserInDB(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    role_id: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_temporary_password: bool = False
    password_changed_at: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleInUser(BaseModel):
    id: str
    name: str
    description: str
    permissions: List[str]


class UserInDBWithRole(UserInDB):
    role: Optional[RoleInUser] = None
