"""
Progress tracking routes for GramOthi
Provides endpoints for students to track their progress and teachers to analyze performance
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models import User, Class, StudentProgress, SlideProgress, RecordingProgress
from ..schemas import (
    StudentProgressResponse, SlideProgressResponse, RecordingProgressResponse,
    LearningObjectiveCreate, LearningObjectiveResponse, ProgressUpdateRequest,
    ProgressAnalyticsRequest, StudentProgressSummary, ClassProgressSummary,
    PerformanceAnalyticsResponse
)
from ..routes.auth import get_current_user, get_current_teacher
from ..services.progress_service import ProgressService
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["progress-tracking"])

# Learning Objectives Management (Teachers only)
@router.post("/objectives", response_model=LearningObjectiveResponse)
def create_learning_objective(
    objective: LearningObjectiveCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new learning objective for a class."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == objective.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can create learning objectives"
        )
    
    learning_objective = ProgressService.create_learning_objective(
        db, objective.class_id, objective.title, 
        objective.description, objective.order_no, objective.is_required
    )
    
    return learning_objective

@router.get("/objectives/class/{class_id}", response_model=List[LearningObjectiveResponse])
def get_class_objectives(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all learning objectives for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    objectives = db.query(LearningObjective).filter(
        LearningObjective.class_id == class_id
    ).order_by(LearningObjective.order_no).all()
    
    return objectives

# Student Progress Tracking
@router.post("/initialize/{class_id}")
def initialize_student_progress(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize progress tracking for a student in a class."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can initialize their progress"
        )
    
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    progress_records = ProgressService.initialize_student_progress(
        db, current_user.id, class_id
    )
    
    return {
        "message": f"Progress tracking initialized for {len(progress_records)} learning objectives",
        "objectives_count": len(progress_records)
    }

@router.get("/student/{class_id}", response_model=List[StudentProgressResponse])
def get_student_progress(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student's progress in a specific class."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their own progress"
        )
    
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    progress = db.query(StudentProgress).filter(
        and_(
            StudentProgress.student_id == current_user.id,
            StudentProgress.class_id == class_id
        )
    ).all()
    
    # Load related data
    for p in progress:
        db.refresh(p.student)
        db.refresh(p.class_)
        if p.learning_objective:
            db.refresh(p.learning_objective)
    
    return progress

@router.get("/student/summary", response_model=StudentProgressSummary)
def get_student_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive progress summary for the current student."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their progress summary"
        )
    
    summary = ProgressService.get_student_progress_summary(db, current_user.id)
    return summary

# Slide Progress Tracking
@router.post("/slides/{slide_id}")
def update_slide_progress(
    slide_id: int,
    status: str,
    time_spent: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update slide progress for a student."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update slide progress"
        )
    
    # Verify slide exists
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide not found"
        )
    
    progress = ProgressService.update_slide_progress(
        db, current_user.id, slide_id, status, time_spent
    )
    
    return {
        "message": "Slide progress updated successfully",
        "slide_id": slide_id,
        "status": status,
        "time_spent": progress.time_spent
    }

@router.get("/slides/{slide_id}", response_model=SlideProgressResponse)
def get_slide_progress(
    slide_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student's progress on a specific slide."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their slide progress"
        )
    
    progress = db.query(SlideProgress).filter(
        and_(
            SlideProgress.student_id == current_user.id,
            SlideProgress.slide_id == slide_id
        )
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide progress not found"
        )
    
    db.refresh(progress.slide)
    return progress

# Recording Progress Tracking
@router.post("/recordings/{recording_id}")
def update_recording_progress(
    recording_id: int,
    status: str,
    time_listened: int = 0,
    total_duration: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update recording progress for a student."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update recording progress"
        )
    
    # Verify recording exists
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    progress = ProgressService.update_recording_progress(
        db, current_user.id, recording_id, status, time_listened, total_duration
    )
    
    return {
        "message": "Recording progress updated successfully",
        "recording_id": recording_id,
        "status": status,
        "progress_percentage": progress.progress_percentage
    }

@router.get("/recordings/{recording_id}", response_model=RecordingProgressResponse)
def get_recording_progress(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student's progress on a specific recording."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their recording progress"
        )
    
    progress = db.query(RecordingProgress).filter(
        and_(
            RecordingProgress.student_id == current_user.id,
            RecordingProgress.recording_id == recording_id
        )
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording progress not found"
        )
    
    db.refresh(progress.recording)
    return progress

# Learning Sessions
@router.post("/sessions/start")
def start_learning_session(
    class_id: int,
    session_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new learning session."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can start learning sessions"
        )
    
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    session = ProgressService.start_learning_session(
        db, current_user.id, class_id, session_type
    )
    
    return {
        "message": "Learning session started",
        "session_id": session.id,
        "started_at": session.started_at
    }

@router.put("/sessions/{session_id}/end")
def end_learning_session(
    session_id: int,
    activities_completed: int = 0,
    engagement_score: float = 0.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a learning session."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can end learning sessions"
        )
    
    session = ProgressService.end_learning_session(
        db, session_id, activities_completed, engagement_score
    )
    
    return {
        "message": "Learning session ended",
        "session_id": session.id,
        "duration_minutes": session.duration_minutes,
        "activities_completed": session.activities_completed,
        "engagement_score": session.engagement_score
    }

# Teacher Analytics and Progress Monitoring
@router.get("/class/{class_id}/summary", response_model=ClassProgressSummary)
def get_class_progress_summary(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get comprehensive progress summary for a class (teacher view)."""
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
            detail="Only the class teacher can view class progress"
        )
    
    summary = ProgressService.get_class_progress_summary(db, class_id)
    return summary

@router.get("/class/{class_id}/students")
def get_class_student_progress(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed progress for all students in a class."""
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
            detail="Only the class teacher can view student progress"
        )
    
    # Get all students with their progress
    students = db.query(User).filter(User.role == "student").all()
    
    student_progress = []
    for student in students:
        # Get student's progress in this class
        progress = db.query(StudentProgress).filter(
            and_(
                StudentProgress.student_id == student.id,
                StudentProgress.class_id == class_id
            )
        ).all()
        
        if progress:
            avg_progress = sum(p.progress_percentage for p in progress) / len(progress)
            
            # Get performance analytics
            analytics = db.query(PerformanceAnalytics).filter(
                and_(
                    PerformanceAnalytics.student_id == student.id,
                    PerformanceAnalytics.class_id == class_id
                )
            ).first()
            
            student_progress.append({
                "student": student,
                "progress_percentage": round(avg_progress, 2),
                "average_score": analytics.average_score if analytics else 0,
                "total_points": analytics.total_points if analytics else 0,
                "attendance_rate": analytics.attendance_rate if analytics else 0,
                "engagement_score": analytics.engagement_score if analytics else 0
            })
    
    return {
        "class_id": class_id,
        "class_title": db_class.title,
        "total_students": len(student_progress),
        "student_progress": student_progress
    }

@router.get("/analytics", response_model=Dict[str, Any])
def get_progress_analytics(
    request: ProgressAnalyticsRequest = Depends(),
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed progress analytics (teacher only)."""
    analytics = ProgressService.get_progress_analytics(db, request)
    return analytics

# Performance Analytics
@router.get("/performance/{student_id}/{class_id}", response_model=PerformanceAnalyticsResponse)
def get_student_performance(
    student_id: int,
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed performance analytics for a specific student in a class."""
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
            detail="Only the class teacher can view student performance"
        )
    
    # Calculate or get performance analytics
    analytics = ProgressService.calculate_performance_analytics(db, student_id, class_id)
    
    # Load related data
    db.refresh(analytics.student)
    db.refresh(analytics.class_)
    
    return analytics

# Achievement System
@router.post("/achievements/award")
def award_achievement(
    student_id: int,
    achievement_type: str,
    title: str,
    description: str = None,
    points: int = 0,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Award an achievement to a student (teacher only)."""
    # Verify student exists
    student = db.query(User).filter(
        and_(
            User.id == student_id,
            User.role == "student"
        )
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    achievement = ProgressService.award_achievement(
        db, student_id, achievement_type, title, description, points
    )
    
    return {
        "message": f"Achievement '{title}' awarded to {student.name}",
        "achievement": {
            "id": achievement.id,
            "title": achievement.title,
            "points_awarded": achievement.points_awarded
        }
    }

@router.get("/achievements/student/{student_id}")
def get_student_achievements(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get achievements for a student."""
    # Students can only view their own achievements
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own achievements"
        )
    
    # Teachers can view any student's achievements
    if current_user.role == "teacher":
        # Verify student exists
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.role == "student"
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
    
    achievements = db.query(Achievement).filter(
        Achievement.student_id == student_id
    ).order_by(Achievement.earned_at.desc()).all()
    
    # Load student info
    for achievement in achievements:
        db.refresh(achievement.student)
    
    return {
        "student_id": student_id,
        "achievements_count": len(achievements),
        "achievements": achievements
    }
