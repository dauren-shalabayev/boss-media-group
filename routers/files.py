import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_user
from dependencies import can_access_file, can_delete_file, require_role_or_higher
from models import User, UserRole, FileVisibility
from schemas import FileCreate, FileResponse as FileResponseSchema, FileListResponse
from crud import create_file, get_accessible_files, delete_file, increment_download_count
from config import settings

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileResponseSchema)
async def upload_file(
    file: UploadFile = File(...),
    visibility: FileVisibility = FileVisibility.PRIVATE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file with specified visibility level.
    
    - **file**: File to upload (multipart/form-data)
    - **visibility**: File visibility level (PRIVATE/DEPARTMENT/PUBLIC)
    
    File size and type restrictions apply based on user role.
    USER role can only create PRIVATE files.
    MANAGER and ADMIN roles can create files with any visibility level.
    """
    # Check file size based on user role
    max_size = settings.MAX_FILE_SIZE_USER
    if current_user.role == UserRole.MANAGER:
        max_size = settings.MAX_FILE_SIZE_MANAGER
    elif current_user.role == UserRole.ADMIN:
        max_size = settings.MAX_FILE_SIZE_ADMIN
    
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size for your role"
        )
    
    # Check file type based on user role
    file_extension = os.path.splitext(file.filename)[1].lower()
    if current_user.role == UserRole.USER:
        if file_extension not in settings.ALLOWED_FILE_TYPES_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed for USER role"
            )
    elif current_user.role == UserRole.MANAGER:
        if file_extension not in settings.ALLOWED_FILE_TYPES_MANAGER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed for MANAGER role"
            )
    elif current_user.role == UserRole.ADMIN:
        if file_extension not in settings.ALLOWED_FILE_TYPES_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed for ADMIN role"
            )
    
    # Check visibility restrictions - only USER role is restricted to PRIVATE
    if current_user.role == UserRole.USER and visibility != FileVisibility.PRIVATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="USER role can only create PRIVATE files"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create file record in database
    file_record = create_file(
        db=db,
        file=FileCreate(visibility=visibility),
        owner_id=current_user.id,
        department_id=current_user.department_id,
        file_path=file_path,
        filename=file.filename,
        size=len(content)
    )
    
    return file_record

@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_info(
    file_id: int,
    file: File = Depends(can_access_file)
):
    """
    Get information about a specific file.
    
    - **file_id**: ID of the file to retrieve
    
    Access is controlled based on file visibility and user permissions.
    """
    return file

@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    file: File = Depends(can_access_file),
    db: Session = Depends(get_db)
):
    """
    Download a file.
    
    - **file_id**: ID of the file to download
    
    Access is controlled based on file visibility and user permissions.
    Downloads count is incremented on successful download.
    """
    # Increment download count
    increment_download_count(db, file_id)
    
    # Return file for download
    return FileResponse(
        path=file.file_path,
        filename=file.filename,
        media_type='application/octet-stream'
    )

@router.delete("/{file_id}")
async def delete_file_endpoint(
    file_id: int,
    file: File = Depends(can_delete_file),
    db: Session = Depends(get_db)
):
    """
    Delete a file.
    
    - **file_id**: ID of the file to delete
    
    Deletion rights are controlled based on user role and file ownership.
    """
    # Delete file from disk
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file from disk: {str(e)}"
        )
    
    # Delete file record from database
    if delete_file(db, file_id):
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file record"
        )

@router.get("/", response_model=FileListResponse)
async def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files accessible to the current user.
    
    Returns files based on user role and file visibility settings.
    """
    files = get_accessible_files(db, current_user)
    return FileListResponse(files=files, total=len(files)) 