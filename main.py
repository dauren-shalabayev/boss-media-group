from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base
from routers import auth, files, users
from crud import create_department, create_user
from models import UserRole, FileVisibility
from auth import get_password_hash
from config import settings
import os

# Database initialization will be done in startup event

app = FastAPI(
    title="File Storage API",
    description="REST API для управления файлами в системе электронного документооборота",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(users.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database with demo data on startup."""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        db = next(get_db())
        
        try:
            # Create departments if they don't exist
            dept1 = create_department(db, "dept1")
            dept2 = create_department(db, "dept2")
            
            # Create demo users if they don't exist
            from schemas import UserCreate
            
            # Check if users already exist
            from models import User
            existing_users = db.query(User).count()
            if existing_users == 0:
                # Create demo users
                demo_users = [
                    UserCreate(
                        username="user1",
                        password="password",
                        role=UserRole.USER,
                        department_id=dept1.id
                    ),
                    UserCreate(
                        username="manager1",
                        password="password",
                        role=UserRole.MANAGER,
                        department_id=dept1.id
                    ),
                    UserCreate(
                        username="admin1",
                        password="password",
                        role=UserRole.ADMIN,
                        department_id=dept1.id
                    ),
                    UserCreate(
                        username="user2",
                        password="password",
                        role=UserRole.USER,
                        department_id=dept2.id
                    )
                ]
                
                for user_data in demo_users:
                    create_user(db, user_data)
                
                print("Demo data created successfully!")
            else:
                print("Demo data already exists.")
                
        except Exception as e:
            print(f"Error creating demo data: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Continue without demo data

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "File Storage API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "ui": "/static/index.html"
    }

@app.get("/ui")
async def get_ui():
    """Redirect to the web interface."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 