from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from .routes import auth, quiz, live
import importlib
class_routes = importlib.import_module('.routes.class', package='app')
from .database import get_db
from .init_db import init_db

# Create FastAPI app
app = FastAPI(
    title="GramOthi - Low-Bandwidth Virtual Classroom",
    description="A virtual classroom platform designed for low-bandwidth rural areas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(class_routes.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(live.router, prefix="/api/v1")

# Import and include media router
from .routes import media
app.include_router(media.router, prefix="/api/v1")

# Import and include progress router
from .routes import progress
app.include_router(progress.router, prefix="/api/v1")

# Import and include notification router
from .routes import notifications
app.include_router(notifications.router, prefix="/api/v1")

# Import and include sync router
from .routes import sync
app.include_router(sync.router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "GramOthi Backend",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to GramOthi - Low-Bandwidth Virtual Classroom",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# File download endpoint with bandwidth optimization
@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file with optional compression for low-bandwidth scenarios."""
    full_path = os.path.join(uploads_dir, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check file size
    file_size = os.path.getsize(full_path)
    
    # For large files, you might want to implement chunked transfer
    # or compression based on user's bandwidth preference
    
    return FileResponse(
        full_path,
        media_type="application/octet-stream",
        filename=os.path.basename(full_path)
    )

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Resource not found", "detail": str(exc)}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "Something went wrong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
