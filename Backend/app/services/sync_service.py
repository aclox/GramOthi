"""
Offline sync service for GramOthi
Handles offline activities, conflict resolution, and synchronization
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models import (
    User, OfflineActivity, SyncSession, StudentProgress, SlideProgress,
    RecordingProgress, LearningSession, Response, Quiz
)
from ..schemas import (
    OfflineActivityCreate, OfflineActivityResponse, OfflineSyncRequest,
    OfflineSyncResponse, ConflictResolutionRequest
)
from ..services.progress_service import ProgressService

logger = logging.getLogger(__name__)

class OfflineSyncService:
    """Service for managing offline activities and synchronization."""
    
    @staticmethod
    def _validate_activity_data(activity_type: str, activity_data: Dict[str, Any]) -> bool:
        """Validate activity data based on type."""
        if not isinstance(activity_data, dict):
            return False
        
        if activity_type == "slide_progress":
            required_fields = ["slide_id", "status"]
            return all(field in activity_data for field in required_fields)
        
        elif activity_type == "recording_progress":
            required_fields = ["recording_id", "status"]
            return all(field in activity_data for field in required_fields)
        
        elif activity_type == "quiz_response":
            required_fields = ["quiz_id", "answer"]
            return all(field in activity_data for field in required_fields)
        
        elif activity_type == "learning_session":
            required_fields = ["class_id", "session_type"]
            return all(field in activity_data for field in required_fields)
        
        elif activity_type == "student_progress":
            required_fields = ["class_id", "status"]
            return all(field in activity_data for field in required_fields)
        
        return False
    
    @staticmethod
    def store_offline_activity(db: Session, user_id: int, activity_type: str,
                              activity_data: Dict[str, Any], offline_id: str) -> OfflineActivity:
        """Store an offline activity for later synchronization."""
        offline_activity = OfflineActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data,
            offline_id=offline_id,
            sync_status="pending"
        )
        
        db.add(offline_activity)
        db.commit()
        db.refresh(offline_activity)
        return offline_activity
    
    @staticmethod
    def sync_offline_activities(db: Session, user_id: int, device_id: str,
                               activities: List[OfflineActivityCreate]) -> OfflineSyncResponse:
        """Synchronize offline activities with the server."""
        # Start sync session
        sync_session = SyncSession(
            user_id=user_id,
            device_id=device_id,
            session_start=datetime.now(timezone.utc)
        )
        db.add(sync_session)
        db.commit()
        
        synced_count = 0
        conflict_count = 0
        conflicts = []
        server_activities = []
        
        try:
            for activity in activities:
                try:
                    # Process the activity
                    result = OfflineSyncService._process_offline_activity(
                        db, user_id, activity
                    )
                    
                    if result["success"]:
                        synced_count += 1
                        
                        # Mark offline activity as synced
                        offline_activity = db.query(OfflineActivity).filter(
                            and_(
                                OfflineActivity.user_id == user_id,
                                OfflineActivity.offline_id == activity.offline_id
                            )
                        ).first()
                        
                        if offline_activity:
                            offline_activity.sync_status = "synced"
                            offline_activity.synced_at = datetime.now(timezone.utc)
                        
                    elif result["conflict"]:
                        conflict_count += 1
                        conflicts.append({
                            "offline_activity": activity.dict(),
                            "server_data": result["server_data"],
                            "conflict_type": result["conflict_type"],
                            "resolution": "pending"
                        })
                        
                        # Mark offline activity as conflicted
                        offline_activity = db.query(OfflineActivity).filter(
                            and_(
                                OfflineActivity.user_id == user_id,
                                OfflineActivity.offline_id == activity.offline_id
                            )
                        ).first()
                        
                        if offline_activity:
                            offline_activity.sync_status = "conflict"
                            offline_activity.conflict_resolution = "pending"
                    
                    else:
                        # Mark as failed
                        offline_activity = db.query(OfflineActivity).filter(
                            and_(
                                OfflineActivity.user_id == user_id,
                                OfflineActivity.offline_id == activity.offline_id
                            )
                        ).first()
                        
                        if offline_activity:
                            offline_activity.sync_status = "failed"
                            offline_activity.error_message = result["error"]
                            offline_activity.retry_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to process offline activity: {e}")
                    conflict_count += 1
                    conflicts.append({
                        "offline_activity": activity.dict(),
                        "error": str(e),
                        "resolution": "failed"
                    })
            
            # Get server activities that might have been created while offline
            server_activities = OfflineSyncService._get_server_activities(db, user_id)
            
            # Update sync session
            sync_session.activities_synced = synced_count
            sync_session.conflicts_resolved = conflict_count
            sync_session.sync_status = "completed" if conflict_count == 0 else "completed_with_conflicts"
            sync_session.session_end = datetime.now(timezone.utc)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Sync session failed: {e}")
            sync_session.sync_status = "failed"
            sync_session.session_end = datetime.now(timezone.utc)
            db.commit()
            
            return OfflineSyncResponse(
                success=False,
                message=f"Sync failed: {str(e)}",
                synced_count=synced_count,
                conflict_count=conflict_count,
                conflicts=conflicts,
                server_activities=[]
            )
        
        return OfflineSyncResponse(
            success=True,
            message=f"Sync completed. {synced_count} synced, {conflict_count} conflicts",
            synced_count=synced_count,
            conflict_count=conflict_count,
            conflicts=conflicts,
            server_activities=server_activities
        )
    
    @staticmethod
    def _process_offline_activity(db: Session, user_id: int, 
                                 activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process a single offline activity."""
        try:
            if activity.activity_type == "slide_progress":
                return OfflineSyncService._process_slide_progress(db, user_id, activity)
            elif activity.activity_type == "recording_progress":
                return OfflineSyncService._process_recording_progress(db, user_id, activity)
            elif activity.activity_type == "quiz_response":
                return OfflineSyncService._process_quiz_response(db, user_id, activity)
            elif activity.activity_type == "learning_session":
                return OfflineSyncService._process_learning_session(db, user_id, activity)
            elif activity.activity_type == "student_progress":
                return OfflineSyncService._process_student_progress(db, user_id, activity)
            else:
                return {
                    "success": False,
                    "conflict": False,
                    "error": f"Unknown activity type: {activity.activity_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to process {activity.activity_type}: {e}")
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_slide_progress(db: Session, user_id: int, 
                               activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process offline slide progress."""
        data = activity.activity_data
        slide_id = data.get("slide_id")
        status = data.get("status")
        time_spent = data.get("time_spent", 0)
        
        if not slide_id or not status:
            return {
                "success": False,
                "conflict": False,
                "error": "Missing required slide progress data"
            }
        
        # Check for conflicts with existing server data
        existing_progress = db.query(SlideProgress).filter(
            and_(
                SlideProgress.student_id == user_id,
                SlideProgress.slide_id == slide_id
            )
        ).first()
        
        if existing_progress:
            # Check if server data is newer
            if existing_progress.updated_at and existing_progress.updated_at > data.get("created_at", datetime.min):
                return {
                    "success": False,
                    "conflict": True,
                    "server_data": {
                        "status": existing_progress.status,
                        "time_spent": existing_progress.time_spent,
                        "updated_at": existing_progress.updated_at
                    },
                    "conflict_type": "server_newer"
                }
        
        # Apply the offline activity
        try:
            from ..services.progress_service import ProgressService
            progress = ProgressService.update_slide_progress(
                db, user_id, slide_id, status, time_spent
            )
            
            return {
                "success": True,
                "conflict": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_recording_progress(db: Session, user_id: int,
                                   activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process offline recording progress."""
        data = activity.activity_data
        recording_id = data.get("recording_id")
        status = data.get("status")
        time_listened = data.get("time_listened", 0)
        total_duration = data.get("total_duration")
        
        if not recording_id or not status:
            return {
                "success": False,
                "conflict": False,
                "error": "Missing required recording progress data"
            }
        
        # Check for conflicts
        existing_progress = db.query(RecordingProgress).filter(
            and_(
                RecordingProgress.student_id == user_id,
                RecordingProgress.recording_id == recording_id
            )
        ).first()
        
        if existing_progress:
            if existing_progress.updated_at and existing_progress.updated_at > data.get("created_at", datetime.min):
                return {
                    "success": False,
                    "conflict": True,
                    "server_data": {
                        "status": existing_progress.status,
                        "time_listened": existing_progress.time_listened,
                        "progress_percentage": existing_progress.progress_percentage,
                        "updated_at": existing_progress.updated_at
                    },
                    "conflict_type": "server_newer"
                }
        
        # Apply the offline activity
        try:
            from ..services.progress_service import ProgressService
            progress = ProgressService.update_recording_progress(
                db, user_id, recording_id, status, time_listened, total_duration
            )
            
            return {
                "success": True,
                "conflict": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_quiz_response(db: Session, user_id: int,
                              activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process offline quiz response."""
        data = activity.activity_data
        quiz_id = data.get("quiz_id")
        answer = data.get("answer")
        
        if not quiz_id or answer is None:
            return {
                "success": False,
                "conflict": False,
                "error": "Missing required quiz response data"
            }
        
        # Check if quiz response already exists
        existing_response = db.query(Response).filter(
            and_(
                Response.quiz_id == quiz_id,
                Response.student_id == user_id
            )
        ).first()
        
        if existing_response:
            return {
                "success": False,
                "conflict": True,
                "server_data": {
                    "answer": existing_response.answer,
                    "is_correct": existing_response.is_correct,
                    "points_earned": existing_response.points_earned,
                    "timestamp": existing_response.timestamp
                },
                "conflict_type": "duplicate_response"
            }
        
        # Apply the offline activity
        try:
            # Get quiz details
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if not quiz:
                return {
                    "success": False,
                    "conflict": False,
                    "error": "Quiz not found"
                }
            
            # Check if answer is correct and calculate points
            is_correct = answer == quiz.correct_option
            points_earned = quiz.points if is_correct else 0
            
            # Create response
            response = Response(
                quiz_id=quiz_id,
                student_id=user_id,
                answer=answer,
                is_correct=is_correct,
                points_earned=points_earned
            )
            
            db.add(response)
            db.commit()
            
            # Update performance analytics
            try:
                ProgressService.calculate_performance_analytics(db, user_id, quiz.class_id)
            except Exception as e:
                logger.warning(f"Failed to update performance analytics: {e}")
            
            return {
                "success": True,
                "conflict": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_learning_session(db: Session, user_id: int,
                                 activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process offline learning session."""
        data = activity.activity_data
        class_id = data.get("class_id")
        session_type = data.get("session_type")
        started_at = data.get("started_at")
        ended_at = data.get("ended_at")
        activities_completed = data.get("activities_completed", 0)
        engagement_score = data.get("engagement_score", 0.0)
        
        if not class_id or not session_type:
            return {
                "success": False,
                "conflict": False,
                "error": "Missing required learning session data"
            }
        
        try:
            from ..services.progress_service import ProgressService
            
            # Start session
            session = ProgressService.start_learning_session(
                db, user_id, class_id, session_type
            )
            
            # If session ended, update it
            if ended_at:
                session.ended_at = ended_at
                session.activities_completed = activities_completed
                session.engagement_score = engagement_score
                
                # Calculate duration
                if started_at and ended_at:
                    duration = ended_at - started_at
                    session.duration_minutes = int(duration.total_seconds() / 60)
                
                db.commit()
            
            return {
                "success": True,
                "conflict": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_student_progress(db: Session, user_id: int,
                                 activity: OfflineActivityCreate) -> Dict[str, Any]:
        """Process offline student progress."""
        data = activity.activity_data
        class_id = data.get("class_id")
        objective_id = data.get("learning_objective_id")
        status = data.get("status")
        progress_percentage = data.get("progress_percentage", 0.0)
        
        if not class_id or not status:
            return {
                "success": False,
                "conflict": False,
                "error": "Missing required student progress data"
            }
        
        try:
            # Check for conflicts
            existing_progress = db.query(StudentProgress).filter(
                and_(
                    StudentProgress.student_id == user_id,
                    StudentProgress.class_id == class_id,
                    StudentProgress.learning_objective_id == objective_id
                )
            ).first()
            
            if existing_progress:
                if existing_progress.updated_at and existing_progress.updated_at > data.get("created_at", datetime.min):
                    return {
                        "success": False,
                        "conflict": True,
                        "server_data": {
                            "status": existing_progress.status,
                            "progress_percentage": existing_progress.progress_percentage,
                            "updated_at": existing_progress.updated_at
                        },
                        "conflict_type": "server_newer"
                    }
            
            # Update or create progress
            if existing_progress:
                existing_progress.status = status
                existing_progress.progress_percentage = progress_percentage
                existing_progress.last_activity = datetime.now(timezone.utc)
            else:
                # Create new progress record
                progress = StudentProgress(
                    student_id=user_id,
                    class_id=class_id,
                    learning_objective_id=objective_id,
                    status=status,
                    progress_percentage=progress_percentage
                )
                db.add(progress)
            
            db.commit()
            
            return {
                "success": True,
                "conflict": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": str(e)
            }
    
    @staticmethod
    def _get_server_activities(db: Session, user_id: int) -> List[OfflineActivityResponse]:
        """Get server activities that might have been created while offline."""
        # Get recent activities from the last 24 hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        server_activities = []
        
        # Get recent slide progress
        slide_progress = db.query(SlideProgress).filter(
            and_(
                SlideProgress.student_id == user_id,
                SlideProgress.updated_at >= cutoff_time
            )
        ).all()
        
        for progress in slide_progress:
            server_activities.append(OfflineActivityResponse(
                id=progress.id,
                user_id=user_id,
                activity_type="slide_progress",
                activity_data={
                    "slide_id": progress.slide_id,
                    "status": progress.status,
                    "time_spent": progress.time_spent,
                    "updated_at": progress.updated_at.isoformat() if progress.updated_at else None
                },
                offline_id=f"server_{progress.id}",
                sync_status="synced",
                created_at=progress.created_at,
                synced_at=progress.updated_at
            ))
        
        # Get recent recording progress
        recording_progress = db.query(RecordingProgress).filter(
            and_(
                RecordingProgress.student_id == user_id,
                RecordingProgress.updated_at >= cutoff_time
            )
        ).all()
        
        for progress in recording_progress:
            server_activities.append(OfflineActivityResponse(
                id=progress.id,
                user_id=user_id,
                activity_type="recording_progress",
                activity_data={
                    "recording_id": progress.recording_id,
                    "status": progress.status,
                    "time_listened": progress.time_listened,
                    "progress_percentage": progress.progress_percentage,
                    "updated_at": progress.updated_at.isoformat() if progress.updated_at else None
                },
                offline_id=f"server_{progress.id}",
                sync_status="synced",
                created_at=progress.created_at,
                synced_at=progress.updated_at
            ))
        
        return server_activities
    
    @staticmethod
    def resolve_conflict(db: Session, user_id: int, offline_activity_id: int,
                        resolution: str, client_data: Dict[str, Any] = None) -> bool:
        """Resolve a sync conflict."""
        offline_activity = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.id == offline_activity_id,
                OfflineActivity.user_id == user_id
            )
        ).first()
        
        if not offline_activity:
            return False
        
        try:
            if resolution == "server_wins":
                # Keep server data, mark offline activity as resolved
                offline_activity.sync_status = "resolved"
                offline_activity.conflict_resolution = "server_wins"
                offline_activity.synced_at = datetime.now(timezone.utc)
                
            elif resolution == "client_wins":
                # Apply client data
                result = OfflineSyncService._process_offline_activity(
                    db, user_id, OfflineActivityCreate(**offline_activity.activity_data)
                )
                
                if result["success"]:
                    offline_activity.sync_status = "resolved"
                    offline_activity.conflict_resolution = "client_wins"
                    offline_activity.synced_at = datetime.now(timezone.utc)
                else:
                    offline_activity.sync_status = "failed"
                    offline_activity.error_message = result.get("error", "Failed to apply client data")
                    
            elif resolution == "manual":
                # Apply custom resolution data
                if client_data:
                    # Merge client data with server data
                    merged_data = {**offline_activity.activity_data, **client_data}
                    offline_activity.activity_data = merged_data
                    
                    # Try to apply the merged data
                    result = OfflineSyncService._process_offline_activity(
                        db, user_id, OfflineActivityCreate(**merged_data)
                    )
                    
                    if result["success"]:
                        offline_activity.sync_status = "resolved"
                        offline_activity.conflict_resolution = "manual"
                        offline_activity.synced_at = datetime.now(timezone.utc)
                    else:
                        offline_activity.sync_status = "failed"
                        offline_activity.error_message = result.get("error", "Failed to apply merged data")
                else:
                    offline_activity.sync_status = "failed"
                    offline_activity.error_message = "Manual resolution requires client data"
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            offline_activity.sync_status = "failed"
            offline_activity.error_message = str(e)
            db.commit()
            return False
    
    @staticmethod
    def get_sync_status(db: Session, user_id: int) -> Dict[str, Any]:
        """Get synchronization status for a user."""
        # Get pending activities
        pending_count = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.user_id == user_id,
                OfflineActivity.sync_status == "pending"
            )
        ).count()
        
        # Get conflicted activities
        conflict_count = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.user_id == user_id,
                OfflineActivity.sync_status == "conflict"
            )
        ).count()
        
        # Get failed activities
        failed_count = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.user_id == user_id,
                OfflineActivity.sync_status == "failed"
            )
        ).count()
        
        # Get last sync session
        last_sync = db.query(SyncSession).filter(
            SyncSession.user_id == user_id
        ).order_by(SyncSession.session_start.desc()).first()
        
        return {
            "pending_activities": pending_count,
            "conflicted_activities": conflict_count,
            "failed_activities": failed_count,
            "last_sync": last_sync.session_start if last_sync else None,
            "last_sync_status": last_sync.sync_status if last_sync else None,
            "needs_sync": pending_count > 0 or conflict_count > 0 or failed_count > 0
        }
    
    @staticmethod
    def retry_failed_activities(db: Session, user_id: int) -> Dict[str, int]:
        """Retry failed offline activities."""
        failed_activities = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.user_id == user_id,
                OfflineActivity.sync_status == "failed"
            )
        ).all()
        
        retry_count = 0
        success_count = 0
        
        for activity in failed_activities:
            try:
                # Reset status and retry
                activity.sync_status = "pending"
                activity.retry_count += 1
                
                # Process the activity again
                result = OfflineSyncService._process_offline_activity(
                    db, user_id, OfflineActivityCreate(**activity.activity_data)
                )
                
                if result["success"]:
                    activity.sync_status = "synced"
                    activity.synced_at = datetime.now(timezone.utc)
                    success_count += 1
                elif result["conflict"]:
                    activity.sync_status = "conflict"
                    activity.conflict_resolution = "pending"
                else:
                    activity.sync_status = "failed"
                    activity.error_message = result.get("error", "Retry failed")
                
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Failed to retry activity {activity.id}: {e}")
                activity.sync_status = "failed"
                activity.error_message = str(e)
                retry_count += 1
        
        db.commit()
        
        return {
            "retried": retry_count,
            "successful": success_count,
            "still_failed": retry_count - success_count
        }
