from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import asyncio
from pathlib import Path
import zipfile
import json
from datetime import datetime

from ..app.database import get_db
from ..app.models import User, Class
from ..app.services.auth_service import get_current_user
from .models import (
    LectureBundle, BundleDownload, SlideTimeline, 
    OfflineSession, ProcessingQueue
)
from .schemas import (
    LectureUploadRequest, LectureBundleResponse, BundleDownloadResponse,
    SlideTimelineResponse, OfflineSessionResponse, ProcessingProgressResponse,
    BundleMetadataResponse, DownloadProgressResponse, ProcessingStatus
)
from .media_processor import MediaProcessor
from .download_manager import DownloadManager
from .background_tasks import process_lecture_bundle_task

router = APIRouter(prefix="/offline", tags=["Offline Recording & Download"])

# Initialize services
media_processor = MediaProcessor()
download_manager = DownloadManager()

@router.post("/lectures/upload", response_model=LectureBundleResponse)
async def upload_lecture(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(..., description="Video file of the lecture"),
    slides_file: UploadFile = File(..., description="ZIP file containing slides"),
    title: str = Form(..., description="Title of the lecture"),
    description: Optional[str] = Form(None, description="Description of the lecture"),
    class_id: int = Form(..., description="ID of the class"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a lecture video and slides for offline processing
    """
    try:
        # Verify user is a teacher
        if current_user.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can upload lectures"
            )
        
        # Verify class exists and user owns it
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        if class_obj.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload to this class"
            )
        
        # Create upload directories
        upload_dir = Path("uploads") / "lectures" / str(class_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded files
        video_path = upload_dir / f"video_{video_file.filename}"
        slides_path = upload_dir / f"slides_{slides_file.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await video_file.read()
            buffer.write(content)
        
        with open(slides_path, "wb") as buffer:
            content = await slides_file.read()
            buffer.write(content)
        
        # Create lecture bundle record
        lecture_bundle = LectureBundle(
            title=title,
            description=description,
            class_id=class_id,
            teacher_id=current_user.id,
            original_video_path=str(video_path),
            original_slides_path=str(slides_path),
            processing_status=ProcessingStatus.PENDING
        )
        
        db.add(lecture_bundle)
        db.commit()
        db.refresh(lecture_bundle)
        
        # Add background task for processing
        background_tasks.add_task(
            process_lecture_bundle_task,
            lecture_bundle.id,
            str(video_path),
            str(slides_path)
        )
        
        return LectureBundleResponse.from_orm(lecture_bundle)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading lecture: {str(e)}"
        )

@router.get("/lectures/{bundle_id}", response_model=LectureBundleResponse)
async def get_lecture_bundle(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get lecture bundle details
    """
    bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture bundle not found"
        )
    
    # Check if user has access to this bundle
    if current_user.role == "student":
        # Check if student is enrolled in the class
        class_obj = db.query(Class).filter(Class.id == bundle.class_id).first()
        if not class_obj or current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    elif current_user.role == "teacher":
        if bundle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    
    return LectureBundleResponse.from_orm(bundle)

@router.get("/lectures/class/{class_id}", response_model=List[BundleMetadataResponse])
async def get_class_lecture_bundles(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all lecture bundles for a class
    """
    # Verify class exists and user has access
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if current_user.role == "student":
        # Check if student is enrolled
        if current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this class"
            )
    elif current_user.role == "teacher":
        if class_obj.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this class"
            )
    
    bundles = db.query(LectureBundle).filter(LectureBundle.class_id == class_id).all()
    return [BundleMetadataResponse.from_orm(bundle) for bundle in bundles]

@router.get("/lectures/{bundle_id}/progress", response_model=ProcessingProgressResponse)
async def get_processing_progress(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get processing progress for a lecture bundle
    """
    bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture bundle not found"
        )
    
    # Check access permissions
    if current_user.role == "student":
        class_obj = db.query(Class).filter(Class.id == bundle.class_id).first()
        if not class_obj or current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    elif current_user.role == "teacher":
        if bundle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    
    # Get processing tasks
    tasks = db.query(ProcessingQueue).filter(ProcessingQueue.bundle_id == bundle_id).all()
    completed_tasks = len([t for t in tasks if t.task_status == "completed"])
    total_tasks = len(tasks)
    
    return ProcessingProgressResponse(
        bundle_id=bundle_id,
        overall_progress=bundle.processing_progress,
        current_task=bundle.processing_status,
        tasks_completed=completed_tasks,
        total_tasks=total_tasks,
        estimated_time_remaining=None,  # Could be calculated based on processing speed
        status=bundle.processing_status
    )

@router.post("/downloads/{bundle_id}", response_model=BundleDownloadResponse)
async def start_bundle_download(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start downloading a lecture bundle
    """
    # Verify bundle exists and is processed
    bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture bundle not found"
        )
    
    if bundle.processing_status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bundle is not ready for download yet"
        )
    
    # Check if user has access
    if current_user.role == "student":
        class_obj = db.query(Class).filter(Class.id == bundle.class_id).first()
        if not class_obj or current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    
    # Check if download already exists
    existing_download = db.query(BundleDownload).filter(
        BundleDownload.bundle_id == bundle_id,
        BundleDownload.student_id == current_user.id
    ).first()
    
    if existing_download:
        if existing_download.download_status == "completed":
            return BundleDownloadResponse.from_orm(existing_download)
        else:
            # Resume existing download
            existing_download.download_status = "downloading"
            db.commit()
            return BundleDownloadResponse.from_orm(existing_download)
    
    # Create new download record
    download = BundleDownload(
        bundle_id=bundle_id,
        student_id=current_user.id,
        total_size=bundle.bundle_size,
        download_status="downloading"
    )
    
    db.add(download)
    db.commit()
    db.refresh(download)
    
    # Start background download
    asyncio.create_task(
        download_manager.download_bundle(download.id, bundle.bundle_zip_path)
    )
    
    return BundleDownloadResponse.from_orm(download)

@router.get("/downloads/{download_id}/progress", response_model=DownloadProgressResponse)
async def get_download_progress(
    download_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get download progress for a bundle
    """
    download = db.query(BundleDownload).filter(BundleDownload.id == download_id).first()
    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )
    
    if download.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this download"
        )
    
    # Calculate download speed (simplified)
    download_speed = None
    estimated_time = None
    
    if download.download_status == "downloading" and download.downloaded_size > 0:
        # This is a simplified calculation - in production you'd track actual speed
        download_speed = 1000000  # 1MB/s placeholder
        if download.total_size and download_speed:
            remaining_bytes = download.total_size - download.downloaded_size
            estimated_time = int(remaining_bytes / download_speed)
    
    return DownloadProgressResponse(
        download_id=download.id,
        bundle_id=download.bundle_id,
        download_status=download.download_status,
        download_progress=download.download_progress,
        downloaded_size=download.downloaded_size,
        total_size=download.total_size,
        download_speed=download_speed,
        estimated_time_remaining=estimated_time
    )

@router.get("/downloads/{download_id}/bundle")
async def download_bundle_file(
    download_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the actual bundle file
    """
    download = db.query(BundleDownload).filter(BundleDownload.id == download_id).first()
    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )
    
    if download.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this download"
        )
    
    if download.download_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download is not completed yet"
        )
    
    bundle = db.query(LectureBundle).filter(LectureBundle.id == download.bundle_id).first()
    if not bundle or not bundle.bundle_zip_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle file not found"
        )
    
    if not os.path.exists(bundle.bundle_zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle file not found on disk"
        )
    
    # Update access tracking
    download.last_accessed = datetime.now()
    download.access_count += 1
    download.is_offline_available = True
    db.commit()
    
    return FileResponse(
        bundle.bundle_zip_path,
        media_type="application/zip",
        filename=f"lecture_bundle_{download.bundle_id}.zip"
    )

@router.get("/downloads/student/{student_id}", response_model=List[BundleDownloadResponse])
async def get_student_downloads(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all downloads for a student
    """
    if current_user.id != student_id and current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own downloads"
        )
    
    downloads = db.query(BundleDownload).filter(
        BundleDownload.student_id == student_id
    ).all()
    
    return [BundleDownloadResponse.from_orm(download) for download in downloads]

@router.get("/lectures/{bundle_id}/timeline", response_model=SlideTimelineResponse)
async def get_slide_timeline(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get slide timeline for a lecture bundle
    """
    bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture bundle not found"
        )
    
    # Check access permissions
    if current_user.role == "student":
        class_obj = db.query(Class).filter(Class.id == bundle.class_id).first()
        if not class_obj or current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    
    timeline = db.query(SlideTimeline).filter(SlideTimeline.bundle_id == bundle_id).first()
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline not found for this bundle"
        )
    
    return SlideTimelineResponse.from_orm(timeline)

@router.post("/sessions/start", response_model=OfflineSessionResponse)
async def start_offline_session(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start an offline learning session
    """
    # Verify bundle exists and user has access
    bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture bundle not found"
        )
    
    if current_user.role == "student":
        class_obj = db.query(Class).filter(Class.id == bundle.class_id).first()
        if not class_obj or current_user.id not in [s.id for s in class_obj.students]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lecture bundle"
            )
    
    # Check if bundle is downloaded
    download = db.query(BundleDownload).filter(
        BundleDownload.bundle_id == bundle_id,
        BundleDownload.student_id == current_user.id,
        BundleDownload.download_status == "completed"
    ).first()
    
    if not download:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bundle must be downloaded before starting offline session"
        )
    
    # Create offline session
    session = OfflineSession(
        student_id=current_user.id,
        bundle_id=bundle_id,
        slides_viewed=[],
        completion_percentage=0.0
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return OfflineSessionResponse.from_orm(session)

@router.put("/sessions/{session_id}/progress")
async def update_session_progress(
    session_id: int,
    completion_percentage: float,
    last_position: float,
    slides_viewed: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update offline session progress
    """
    session = db.query(OfflineSession).filter(OfflineSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own sessions"
        )
    
    # Update session progress
    session.completion_percentage = completion_percentage
    session.last_position = last_position
    session.slides_viewed = slides_viewed
    
    db.commit()
    
    return {"message": "Session progress updated successfully"}

@router.put("/sessions/{session_id}/end")
async def end_offline_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End an offline learning session
    """
    session = db.query(OfflineSession).filter(OfflineSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only end your own sessions"
        )
    
    # Calculate session duration
    if session.started_at:
        duration = (datetime.now() - session.started_at).total_seconds()
        session.session_duration = duration
    
    session.ended_at = datetime.now()
    db.commit()
    
    return {"message": "Session ended successfully"}

@router.get("/sessions/student/{student_id}", response_model=List[OfflineSessionResponse])
async def get_student_sessions(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all offline sessions for a student
    """
    if current_user.id != student_id and current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sessions"
        )
    
    sessions = db.query(OfflineSession).filter(
        OfflineSession.student_id == student_id
    ).all()
    
    return [OfflineSessionResponse.from_orm(session) for session in sessions]
