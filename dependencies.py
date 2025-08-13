from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User, UserRole, File, FileVisibility
from auth import get_current_user
from database import get_db
from crud import get_file_by_id

def require_role(required_role: UserRole):
    """Dependency to require a specific user role."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return current_user
    return role_checker

def require_role_or_higher(required_role: UserRole):
    """Dependency to require a specific role or higher."""
    def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} or higher required"
            )
        return current_user
    return role_checker

def can_access_file(file_id: int, current_user: User = Depends(get_current_user), 
                   db: Session = Depends(get_db)):
    """Check if user can access a specific file."""
    file = get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Admin can access all files
    if current_user.role == UserRole.ADMIN:
        return file
    
    # Manager can access all files
    if current_user.role == UserRole.MANAGER:
        return file
    
    # User access rules
    if current_user.role == UserRole.USER:
        # Can access PUBLIC files
        if file.visibility == FileVisibility.PUBLIC:
            return file
        
        # Can access DEPARTMENT files from same department
        if (file.visibility == FileVisibility.DEPARTMENT and 
            file.department_id == current_user.department_id):
            return file
        
        # Can access own PRIVATE files
        if (file.visibility == FileVisibility.PRIVATE and 
            file.owner_id == current_user.id):
            return file
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this file"
        )
    
    return file

def can_delete_file(file_id: int, current_user: User = Depends(get_current_user), 
                   db: Session = Depends(get_db)):
    """Check if user can delete a specific file."""
    file = get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Admin can delete any file
    if current_user.role == UserRole.ADMIN:
        return file
    
    # Manager can delete files from their department
    if current_user.role == UserRole.MANAGER:
        if file.department_id == current_user.department_id:
            return file
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete files from your department"
        )
    
    # User can only delete their own files
    if current_user.role == UserRole.USER:
        if file.owner_id == current_user.id:
            return file
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own files"
        )
    
    return file 