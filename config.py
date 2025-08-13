import os
from typing import Optional

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    
    # File upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    MAX_FILE_SIZE_USER: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE_MANAGER: int = 50 * 1024 * 1024  # 50MB
    MAX_FILE_SIZE_ADMIN: int = 100 * 1024 * 1024  # 100MB
    
    # Allowed file types for USER role
    ALLOWED_FILE_TYPES_USER = [".pdf"]

settings = Settings() 