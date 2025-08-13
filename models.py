from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class FileVisibility(str, enum.Enum):
    PRIVATE = "PRIVATE"
    DEPARTMENT = "DEPARTMENT"
    PUBLIC = "PUBLIC"

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    users = relationship("User", back_populates="department")
    files = relationship("File", back_populates="department")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    department = relationship("Department", back_populates="users")
    files = relationship("File", back_populates="owner")

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    visibility = Column(Enum(FileVisibility), default=FileVisibility.PRIVATE)
    file_path = Column(String)
    filename = Column(String)
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    downloads_count = Column(Integer, default=0)
    
    owner = relationship("User", back_populates="files")
    department = relationship("Department", back_populates="files") 