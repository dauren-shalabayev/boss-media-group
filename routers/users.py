from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_user
from dependencies import require_role_or_higher
from models import User, UserRole
from schemas import UserCreate, UserResponse, UserUpdate, MessageResponse
from crud import create_user, get_user_by_id, get_users_by_department, get_all_users, update_user_role

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_new_user(
    user: UserCreate,
    current_user: User = Depends(require_role_or_higher(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    - **username**: New user's username
    - **password**: New user's password
    - **role**: New user's role (USER/MANAGER/ADMIN)
    - **department_id**: New user's department ID
    
    Only MANAGER and ADMIN users can create new users.
    """
    # Check if username already exists
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check role restrictions
    if current_user.role == UserRole.MANAGER:
        # Manager can only create USER role users
        if user.role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MANAGER role can only create USER role users"
            )
    
    new_user = create_user(db, user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_info(
    user_id: int,
    current_user: User = Depends(require_role_or_higher(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Get information about a specific user.
    
    - **user_id**: ID of the user to retrieve
    
    Only MANAGER and ADMIN users can view user information.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check access restrictions for MANAGER role
    if current_user.role == UserRole.MANAGER:
        if user.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view users from your department"
            )
    
    return user

@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role_endpoint(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_role_or_higher(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Update a user's role.
    
    - **user_id**: ID of the user to update
    - **new_role**: New role for the user
    
    Only MANAGER and ADMIN users can change user roles.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check access restrictions for MANAGER role
    if current_user.role == UserRole.MANAGER:
        if user.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update users from your department"
            )
        # Manager can only change to USER role
        if new_role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MANAGER role can only change users to USER role"
            )
    
    updated_user = update_user_role(db, user_id, new_role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )
    
    return updated_user

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_role_or_higher(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    List users based on current user's role and permissions.
    
    - MANAGER: Can see users from their department only
    - ADMIN: Can see all users
    """
    if current_user.role == UserRole.ADMIN:
        users = get_all_users(db)
    else:
        # MANAGER role
        users = get_users_by_department(db, current_user.department_id)
    
    return users 