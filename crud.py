from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from models import User, File, Department, UserRole, FileVisibility
from schemas import UserCreate, FileCreate
from auth import get_password_hash

# User CRUD operations
def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        department_id=user.department_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users_by_department(db: Session, department_id: int) -> List[User]:
    """Get all users in a department."""
    return db.query(User).filter(User.department_id == department_id).all()

def get_all_users(db: Session) -> List[User]:
    """Get all users."""
    return db.query(User).all()

def update_user_role(db: Session, user_id: int, new_role: UserRole) -> Optional[User]:
    """Update user role."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
    return user

# Department CRUD operations
def create_department(db: Session, name: str) -> Department:
    """Create a new department."""
    db_dept = Department(name=name)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

def get_department_by_id(db: Session, dept_id: int) -> Optional[Department]:
    """Get department by ID."""
    return db.query(Department).filter(Department.id == dept_id).first()

def get_department_by_name(db: Session, name: str) -> Optional[Department]:
    """Get department by name."""
    return db.query(Department).filter(Department.name == name).first()

# File CRUD operations
def create_file(db: Session, file: FileCreate, owner_id: int, department_id: int, 
                file_path: str, filename: str, size: int) -> File:
    """Create a new file record."""
    db_file = File(
        owner_id=owner_id,
        department_id=department_id,
        visibility=file.visibility,
        file_path=file_path,
        filename=filename,
        size=size
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file_by_id(db: Session, file_id: int) -> Optional[File]:
    """Get file by ID."""
    return db.query(File).filter(File.id == file_id).first()

def get_accessible_files(db: Session, current_user: User) -> List[File]:
    """Get files accessible to the current user based on role and visibility."""
    if current_user.role == UserRole.ADMIN:
        # Admin can see all files
        return db.query(File).all()
    elif current_user.role == UserRole.MANAGER:
        # Manager can see all files
        return db.query(File).all()
    else:
        # USER role: can see PUBLIC files, DEPARTMENT files from same department, and own PRIVATE files
        return db.query(File).filter(
            or_(
                File.visibility == FileVisibility.PUBLIC,
                and_(File.visibility == FileVisibility.DEPARTMENT, 
                     File.department_id == current_user.department_id),
                and_(File.visibility == FileVisibility.PRIVATE, 
                     File.owner_id == current_user.id)
            )
        ).all()

def delete_file(db: Session, file_id: int) -> bool:
    """Delete a file record."""
    file = db.query(File).filter(File.id == file_id).first()
    if file:
        db.delete(file)
        db.commit()
        return True
    return False

def increment_download_count(db: Session, file_id: int) -> bool:
    """Increment file download count."""
    file = db.query(File).filter(File.id == file_id).first()
    if file:
        file.downloads_count += 1
        db.commit()
        return True
    return False 