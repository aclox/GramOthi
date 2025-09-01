from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Class, Slide, Recording
from ..schemas import (
    ClassCreate, ClassResponse, SlideCreate, SlideResponse,
    RecordingCreate, RecordingResponse
)
from ..routes.auth import get_current_user, get_current_teacher
from ..services.compression_service import CompressionService, BandwidthDetector
import os
import uuid
import tempfile
from datetime import datetime

router = APIRouter(prefix="/classes", tags=["classes"])

# File upload settings
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".jpg", ".jpeg", ".png", ".mp3", ".wav", ".m4a"}

def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def is_valid_file_extension(filename: str) -> bool:
    """Check if file has valid extension."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def save_file(file: UploadFile, subdirectory: str, request: Request = None, compress: bool = True) -> str:
    """Save uploaded file with optional compression and return file URL."""
    ensure_upload_dir()
    
    if not is_valid_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )
    
    # Create unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create subdirectory
    subdir_path = os.path.join(UPLOAD_DIR, subdirectory)
    os.makedirs(subdir_path, exist_ok=True)
    
    # Save original file
    original_file_path = os.path.join(subdir_path, f"original_{unique_filename}")
    with open(original_file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Compress file if requested and supported
    if compress:
        # Detect bandwidth profile from request
        user_agent = request.headers.get("user-agent", "") if request else ""
        connection_type = request.headers.get("x-connection-type", "") if request else ""
        bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
        
        # Create compressed version
        compressed_file_path = os.path.join(subdir_path, unique_filename)
        success, compression_info = CompressionService.compress_file(
            original_file_path, 
            compressed_file_path, 
            bandwidth_profile
        )
        
        if success:
            # Log compression results
            print(f"File compressed: {compression_info}")
            # Remove original file to save space
            os.remove(original_file_path)
            return f"/uploads/{subdirectory}/{unique_filename}"
        else:
            # If compression failed, use original file
            os.rename(original_file_path, os.path.join(subdir_path, unique_filename))
            return f"/uploads/{subdirectory}/{unique_filename}"
    else:
        # No compression, use original file
        os.rename(original_file_path, os.path.join(subdir_path, unique_filename))
        return f"/uploads/{subdirectory}/{unique_filename}"

@router.post("/", response_model=ClassResponse)
def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new class."""
    db_class = Class(
        title=class_data.title,
        teacher_id=current_user.id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    
    # Fetch teacher info for response
    db.refresh(db_class.teacher)
    return db_class

@router.get("/", response_model=List[ClassResponse])
def get_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all classes for the current user."""
    if current_user.role == "teacher":
        classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    else:
        # For students, return all classes (you might want to add enrollment logic later)
        classes = db.query(Class).all()
    
    # Ensure teacher info is loaded
    for cls in classes:
        db.refresh(cls.teacher)
    
    return classes

@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific class by ID."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db.refresh(db_class.teacher)
    return db_class

@router.put("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update a class (only by the teacher who created it)."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can update this class"
        )
    
    db_class.title = class_data.title
    db.commit()
    db.refresh(db_class)
    db.refresh(db_class.teacher)
    
    return db_class

@router.delete("/{class_id}")
def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a class (only by the teacher who created it)."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can delete this class"
        )
    
    db.delete(db_class)
    db.commit()
    
    return {"message": "Class deleted successfully"}

# Slide management
@router.post("/{class_id}/slides", response_model=SlideResponse)
def upload_slide(
    class_id: int,
    file: UploadFile = File(...),
    order_no: int = 1,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Upload a slide for a class with automatic compression."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can upload slides"
        )
    
    # Save file with compression
    file_url = save_file(file, "slides", request, compress=True)
    
    # Create slide record
    db_slide = Slide(
        class_id=class_id,
        file_url=file_url,
        order_no=order_no
    )
    db.add(db_slide)
    db.commit()
    db.refresh(db_slide)
    
    return db_slide

@router.get("/{class_id}/slides", response_model=List[SlideResponse])
def get_slides(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all slides for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    slides = db.query(Slide).filter(Slide.class_id == class_id).order_by(Slide.order_no).all()
    return slides

# Recording management
@router.post("/{class_id}/recordings", response_model=RecordingResponse)
def upload_recording(
    class_id: int,
    audio_file: UploadFile = File(...),
    bundle_file: UploadFile = File(None),
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Upload a recording for a class with audio compression."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can upload recordings"
        )
    
    # Save audio file with compression (audio-first approach)
    audio_url = save_file(audio_file, "recordings/audio", request, compress=True)
    
    # Save bundle file if provided (with compression)
    bundle_url = None
    if bundle_file:
        bundle_url = save_file(bundle_file, "recordings/bundles", request, compress=True)
    
    # Create recording record
    db_recording = Recording(
        class_id=class_id,
        audio_url=audio_url,
        bundle_url=bundle_url
    )
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    
    return db_recording

@router.get("/{class_id}/recordings", response_model=List[RecordingResponse])
def get_recordings(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all recordings for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    recordings = db.query(Recording).filter(Recording.class_id == class_id).all()
    return recordings
