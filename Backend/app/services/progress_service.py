"""
Progress tracking service for GramOthi
Handles student progress, learning analytics, and performance tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from ..models import (
    User, Class, StudentProgress, SlideProgress, RecordingProgress,
    LearningSession, SessionAttendance, Achievement, PerformanceAnalytics,
    LearningObjective, Quiz, Response, Slide, Recording
)
from ..schemas import (
    StudentProgressCreate, SlideProgressCreate, RecordingProgressCreate,
    LearningSessionCreate, SessionAttendanceCreate, AchievementCreate,
    ProgressUpdateRequest, ProgressAnalyticsRequest
)
import logging

logger = logging.getLogger(__name__)

class ProgressService:
    """Service for managing student progress and learning analytics."""
    
    @staticmethod
    def create_learning_objective(db: Session, class_id: int, title: str, 
                                description: str = None, order_no: int = 1, 
                                is_required: bool = True) -> LearningObjective:
        """Create a new learning objective for a class."""
        learning_objective = LearningObjective(
            class_id=class_id,
            title=title,
            description=description,
            order_no=order_no,
            is_required=is_required
        )
        db.add(learning_objective)
        db.commit()
        db.refresh(learning_objective)
        return learning_objective
    
    @staticmethod
    def initialize_student_progress(db: Session, student_id: int, class_id: int) -> List[StudentProgress]:
        """Initialize progress tracking for a student in a class."""
        # Get all learning objectives for the class
        objectives = db.query(LearningObjective).filter(
            LearningObjective.class_id == class_id
        ).order_by(LearningObjective.order_no).all()
        
        progress_records = []
        for objective in objectives:
            # Check if progress record already exists
            existing = db.query(StudentProgress).filter(
                and_(
                    StudentProgress.student_id == student_id,
                    StudentProgress.class_id == class_id,
                    StudentProgress.learning_objective_id == objective.id
                )
            ).first()
            
            if not existing:
                progress = StudentProgress(
                    student_id=student_id,
                    class_id=class_id,
                    learning_objective_id=objective.id,
                    status="not_started",
                    progress_percentage=0.0
                )
                db.add(progress)
                progress_records.append(progress)
        
        if progress_records:
            db.commit()
            for record in progress_records:
                db.refresh(record)
        
        return progress_records
    
    @staticmethod
    def update_slide_progress(db: Session, student_id: int, slide_id: int, 
                            status: str, time_spent: int = 0) -> SlideProgress:
        """Update or create slide progress for a student."""
        # Get or create slide progress record
        progress = db.query(SlideProgress).filter(
            and_(
                SlideProgress.student_id == student_id,
                SlideProgress.slide_id == slide_id
            )
        ).first()
        
        if not progress:
            progress = SlideProgress(
                student_id=student_id,
                slide_id=slide_id,
                status=status,
                time_spent=time_spent
            )
            db.add(progress)
        else:
            progress.status = status
            progress.time_spent += time_spent
        
        # Update timestamps
        if status == "viewed" and not progress.viewed_at:
            progress.viewed_at = datetime.now(timezone.utc)
        elif status == "completed" and not progress.completed_at:
            progress.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def update_recording_progress(db: Session, student_id: int, recording_id: int,
                                status: str, time_listened: int = 0, 
                                total_duration: int = None) -> RecordingProgress:
        """Update or create recording progress for a student."""
        # Get or create recording progress record
        progress = db.query(RecordingProgress).filter(
            and_(
                RecordingProgress.student_id == student_id,
                RecordingProgress.recording_id == recording_id
            )
        ).first()
        
        if not progress:
            progress = RecordingProgress(
                student_id=student_id,
                recording_id=recording_id,
                status=status,
                time_listened=time_listened,
                total_duration=total_duration
            )
            db.add(progress)
        else:
            progress.status = status
            progress.time_listened += time_listened
            if total_duration:
                progress.total_duration = total_duration
        
        # Calculate progress percentage
        if progress.total_duration and progress.total_duration > 0:
            progress.progress_percentage = min(100.0, (progress.time_listened / progress.total_duration) * 100)
        
        # Update timestamps
        if status == "listening" and not progress.started_at:
            progress.started_at = datetime.now(timezone.utc)
        elif status == "completed" and not progress.completed_at:
            progress.completed_at = datetime.now(timezone.utc)
            progress.progress_percentage = 100.0
        
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def start_learning_session(db: Session, student_id: int, class_id: int, 
                             session_type: str) -> LearningSession:
        """Start a new learning session for a student."""
        session = LearningSession(
            student_id=student_id,
            class_id=class_id,
            session_type=session_type,
            started_at=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def end_learning_session(db: Session, session_id: int, 
                           activities_completed: int = 0, 
                           engagement_score: float = 0.0) -> LearningSession:
        """End a learning session and calculate metrics."""
        session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
        if not session:
            raise ValueError("Learning session not found")
        
        session.ended_at = datetime.now(timezone.utc)
        session.activities_completed = activities_completed
        session.engagement_score = engagement_score
        
        # Calculate duration
        if session.started_at and session.ended_at:
            duration = session.ended_at - session.started_at
            session.duration_minutes = int(duration.total_seconds() / 60)
        
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def record_session_attendance(db: Session, student_id: int, live_session_id: int,
                                action: str, participation_level: str = "passive") -> SessionAttendance:
        """Record student attendance in live sessions."""
        if action == "join":
            # Create new attendance record
            attendance = SessionAttendance(
                student_id=student_id,
                live_session_id=live_session_id,
                joined_at=datetime.now(timezone.utc),
                participation_level=participation_level
            )
            db.add(attendance)
            db.commit()
            db.refresh(attendance)
            return attendance
        
        elif action == "leave":
            # Update existing attendance record
            attendance = db.query(SessionAttendance).filter(
                and_(
                    SessionAttendance.student_id == student_id,
                    SessionAttendance.live_session_id == live_session_id,
                    SessionAttendance.left_at.is_(None)
                )
            ).first()
            
            if attendance:
                attendance.left_at = datetime.now(timezone.utc)
                if attendance.joined_at:
                    duration = attendance.left_at - attendance.joined_at
                    attendance.duration_minutes = int(duration.total_seconds() / 60)
                
                db.commit()
                db.refresh(attendance)
                return attendance
        
        return None
    
    @staticmethod
    def award_achievement(db: Session, student_id: int, achievement_type: str,
                         title: str, description: str = None, points: int = 0) -> Achievement:
        """Award an achievement to a student."""
        # Check if achievement already exists
        existing = db.query(Achievement).filter(
            and_(
                Achievement.student_id == student_id,
                Achievement.achievement_type == achievement_type
            )
        ).first()
        
        if existing:
            return existing  # Don't award duplicate achievements
        
        achievement = Achievement(
            student_id=student_id,
            achievement_type=achievement_type,
            title=title,
            description=description,
            points_awarded=points
        )
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement
    
    @staticmethod
    def update_quiz_response(db: Session, response_id: int, is_correct: bool, 
                           points_earned: int) -> Response:
        """Update quiz response with correctness and points."""
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise ValueError("Quiz response not found")
        
        response.is_correct = is_correct
        response.points_earned = points_earned
        
        db.commit()
        db.refresh(response)
        return response
    
    @staticmethod
    def calculate_performance_analytics(db: Session, student_id: int, class_id: int) -> PerformanceAnalytics:
        """Calculate comprehensive performance analytics for a student in a class."""
        # Get or create analytics record
        analytics = db.query(PerformanceAnalytics).filter(
            and_(
                PerformanceAnalytics.student_id == student_id,
                PerformanceAnalytics.class_id == class_id
            )
        ).first()
        
        if not analytics:
            analytics = PerformanceAnalytics(
                student_id=student_id,
                class_id=class_id
            )
            db.add(analytics)
        
        # Calculate quiz performance
        quiz_stats = db.query(
            func.count(Response.id).label('total_quizzes'),
            func.sum(Response.is_correct.cast(Integer)).label('correct_quizzes'),
            func.sum(Response.points_earned).label('total_points'),
            func.avg(Response.is_correct.cast(Float)).label('average_score')
        ).filter(
            and_(
                Response.student_id == student_id,
                Quiz.class_id == class_id
            )
        ).join(Quiz, Response.quiz_id == Quiz.id).first()
        
        if quiz_stats:
            analytics.quizzes_taken = quiz_stats.total_quizzes or 0
            analytics.quizzes_passed = quiz_stats.correct_quizzes or 0
            analytics.total_points = quiz_stats.total_points or 0
            analytics.average_score = (quiz_stats.average_score or 0.0) * 100
        
        # Calculate study time
        study_time = db.query(
            func.sum(LearningSession.duration_minutes)
        ).filter(
            and_(
                LearningSession.student_id == student_id,
                LearningSession.class_id == class_id
            )
        ).scalar()
        
        analytics.total_study_time = study_time or 0
        
        # Calculate attendance rate
        total_sessions = db.query(LiveSession).filter(
            LiveSession.class_id == class_id
        ).count()
        
        if total_sessions > 0:
            attended_sessions = db.query(SessionAttendance).filter(
                and_(
                    SessionAttendance.student_id == student_id,
                    SessionAttendance.live_session_id.in_(
                        db.query(LiveSession.id).filter(LiveSession.class_id == class_id)
                    )
                )
            ).count()
            
            analytics.attendance_rate = (attended_sessions / total_sessions) * 100
        
        # Calculate engagement score
        engagement_scores = db.query(LearningSession.engagement_score).filter(
            and_(
                LearningSession.student_id == student_id,
                LearningSession.class_id == class_id,
                LearningSession.engagement_score > 0
            )
        ).all()
        
        if engagement_scores:
            total_engagement = sum(score[0] for score in engagement_scores)
            analytics.engagement_score = total_engagement / len(engagement_scores)
        
        analytics.last_updated = datetime.now(timezone.utc)
        db.commit()
        db.refresh(analytics)
        
        return analytics
    
    @staticmethod
    def get_student_progress_summary(db: Session, student_id: int) -> Dict[str, Any]:
        """Get comprehensive progress summary for a student across all classes."""
        # Get basic student info
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("Student not found")
        
        # Get progress across all classes
        class_progress = db.query(
            Class.title,
            StudentProgress.status,
            StudentProgress.progress_percentage
        ).join(StudentProgress, Class.id == StudentProgress.class_id).filter(
            StudentProgress.student_id == student_id
        ).all()
        
        # Calculate overall metrics
        total_classes = len(class_progress)
        completed_classes = sum(1 for _, status, _ in class_progress if status == "completed")
        overall_progress = sum(percentage for _, _, percentage in class_progress) / total_classes if total_classes > 0 else 0
        
        # Get total points and achievements
        total_points = db.query(func.sum(Response.points_earned)).filter(
            Response.student_id == student_id
        ).scalar() or 0
        
        achievements_count = db.query(Achievement).filter(
            Achievement.student_id == student_id
        ).count()
        
        # Calculate study time
        total_study_time = db.query(func.sum(LearningSession.duration_minutes)).filter(
            LearningSession.student_id == student_id
        ).scalar() or 0
        
        # Calculate attendance rate
        total_sessions = db.query(LiveSession).count()
        if total_sessions > 0:
            attended_sessions = db.query(SessionAttendance).filter(
                SessionAttendance.student_id == student_id
            ).count()
            attendance_rate = (attended_sessions / total_sessions) * 100
        else:
            attendance_rate = 0
        
        # Calculate current streak (simplified - can be enhanced)
        current_streak = 0  # This would need more complex logic
        
        return {
            "student_id": student_id,
            "student_name": student.name,
            "total_classes": total_classes,
            "completed_classes": completed_classes,
            "overall_progress": round(overall_progress, 2),
            "total_points": total_points,
            "total_study_time_hours": round(total_study_time / 60, 2),
            "overall_attendance_rate": round(attendance_rate, 2),
            "achievements_count": achievements_count,
            "current_streak_days": current_streak,
            "class_progress": [
                {
                    "class_title": title,
                    "status": status,
                    "progress_percentage": progress_percentage
                }
                for title, status, progress_percentage in class_progress
            ]
        }
    
    @staticmethod
    def get_class_progress_summary(db: Session, class_id: int) -> Dict[str, Any]:
        """Get comprehensive progress summary for a class (teacher view)."""
        # Get class info
        class_info = db.query(Class).filter(Class.id == class_id).first()
        if not class_info:
            raise ValueError("Class not found")
        
        # Get all students in the class
        students = db.query(User).filter(
            User.role == "student"
        ).all()  # This could be enhanced with enrollment logic
        
        # Calculate class-wide metrics
        total_students = len(students)
        active_students = 0
        total_progress = 0
        total_score = 0
        completed_students = 0
        
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
                student_avg_progress = sum(p.progress_percentage for p in progress) / len(progress)
                total_progress += student_avg_progress
                
                if student_avg_progress > 0:
                    active_students += 1
                
                if student_avg_progress >= 100:
                    completed_students += 1
                
                # Get student's performance analytics
                analytics = db.query(PerformanceAnalytics).filter(
                    and_(
                        PerformanceAnalytics.student_id == student.id,
                        PerformanceAnalytics.class_id == class_id
                    )
                ).first()
                
                if analytics:
                    total_score += analytics.average_score
                
                student_progress.append({
                    "student": student,
                    "progress_percentage": student_avg_progress,
                    "average_score": analytics.average_score if analytics else 0
                })
        
        # Calculate averages
        average_progress = total_progress / total_students if total_students > 0 else 0
        average_score = total_score / total_students if total_students > 0 else 0
        completion_rate = (completed_students / total_students) * 100 if total_students > 0 else 0
        
        # Get top performers
        top_performers = sorted(student_progress, key=lambda x: x['progress_percentage'], reverse=True)[:5]
        
        return {
            "class_id": class_id,
            "class_title": class_info.title,
            "total_students": total_students,
            "active_students": active_students,
            "average_progress": round(average_progress, 2),
            "average_score": round(average_score, 2),
            "completion_rate": round(completion_rate, 2),
            "top_performers": [p['student'] for p in top_performers],
            "student_progress": student_progress
        }
    
    @staticmethod
    def get_progress_analytics(db: Session, request: ProgressAnalyticsRequest) -> Dict[str, Any]:
        """Get detailed progress analytics based on filters."""
        query = db.query(StudentProgress)
        
        # Apply filters
        if request.student_id:
            query = query.filter(StudentProgress.student_id == request.student_id)
        
        if request.class_id:
            query = query.filter(StudentProgress.class_id == request.class_id)
        
        if request.date_from:
            query = query.filter(StudentProgress.last_activity >= request.date_from)
        
        if request.date_to:
            query = query.filter(StudentProgress.last_activity <= request.date_to)
        
        # Group by date
        if request.group_by == "day":
            query = query.group_by(
                func.date(StudentProgress.last_activity)
            ).with_entities(
                func.date(StudentProgress.last_activity).label('date'),
                func.count(StudentProgress.id).label('total_activities'),
                func.avg(StudentProgress.progress_percentage).label('avg_progress')
            )
        elif request.group_by == "week":
            query = query.group_by(
                func.date_trunc('week', StudentProgress.last_activity)
            ).with_entities(
                func.date_trunc('week', StudentProgress.last_activity).label('week'),
                func.count(StudentProgress.id).label('total_activities'),
                func.avg(StudentProgress.progress_percentage).label('avg_progress')
            )
        elif request.group_by == "month":
            query = query.group_by(
                func.date_trunc('month', StudentProgress.last_activity)
            ).with_entities(
                func.date_trunc('month', StudentProgress.last_activity).label('month'),
                func.count(StudentProgress.id).label('total_activities'),
                func.avg(StudentProgress.progress_percentage).label('avg_progress')
            )
        
        results = query.all()
        
        return {
            "group_by": request.group_by,
            "total_records": len(results),
            "data": [
                {
                    "period": str(result[0]),
                    "total_activities": result[1],
                    "average_progress": round(result[2], 2) if result[2] else 0
                }
                for result in results
            ]
        }
