from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import UserRole, FileVisibility

# User schemas
class UserBase(BaseModel):
    username: str
    role: UserRole
    department_id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    department_id: Optional[int] = None

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

# Department schemas
class DepartmentBase(BaseModel):
    name: str

class DepartmentResponse(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True

# File schemas
class FileBase(BaseModel):
    visibility: FileVisibility

class FileCreate(FileBase):
    pass

class FileResponse(FileBase):
    id: int
    owner_id: int
    department_id: int
    file_path: str
    filename: str
    size: int
    created_at: datetime
    downloads_count: int
    
    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int

# Auth schemas
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Response schemas
class MessageResponse(BaseModel):
    message: str 