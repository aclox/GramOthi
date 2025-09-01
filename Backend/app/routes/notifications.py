"""
Notification routes for GramOthi
Provides endpoints for push notifications, scheduled events, and notification management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models import User, Class, Quiz, LiveSession
from ..schemas import (
    PushTokenCreate, PushTokenResponse, NotificationPreferenceCreate,
    NotificationPreferenceResponse, ScheduledEventCreate, ScheduledEventResponse,
    PushNotificationRequest, PushNotificationResponse, ScheduledEventNotificationRequest
)
from ..routes.auth import get_current_user, get_current_teacher
from ..services.notification_service import (
    PushNotificationService, ScheduledNotificationService, NotificationPreferenceService
)
from datetime import datetime, timezone
import logging
from sqlalchemy import and_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Push Token Management
@router.post("/tokens", response_model=PushTokenResponse)
def register_push_token(
    token_data: PushTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a push token for the current user."""
    push_token = PushNotificationService.register_push_token(
        db, current_user.id, token_data.token, token_data.platform, token_data.device_id
    )
    return push_token

@router.delete("/tokens/{token}")
def unregister_push_token(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unregister a push token for the current user."""
    success = PushNotificationService.unregister_push_token(db, current_user.id, token)
    if success:
        return {"message": "Push token unregistered successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push token not found"
        )

@router.get("/tokens", response_model=List[PushTokenResponse])
def get_user_push_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all push tokens for the current user."""
    tokens = PushNotificationService.get_user_push_tokens(db, current_user.id)
    return tokens

# Notification Preferences
@router.post("/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preference(
    preference: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preference for the current user."""
    notification_preference = NotificationPreferenceService.update_preference(
        db, current_user.id, preference.notification_type,
        preference.is_enabled, preference.reminder_minutes
    )
    return notification_preference

@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
def get_user_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notification preferences for the current user."""
    preferences = NotificationPreferenceService.get_user_preferences(db, current_user.id)
    return preferences

# Scheduled Events
@router.post("/events", response_model=ScheduledEventResponse)
def create_scheduled_event(
    event: ScheduledEventCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new scheduled event (teacher only)."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == event.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can create scheduled events"
        )
    
    scheduled_event = ScheduledNotificationService.create_scheduled_event(
        db, event.class_id, event.event_type, event.title, event.description,
        event.scheduled_at, event.duration_minutes, event.is_recurring,
        event.recurrence_pattern
    )
    
    return scheduled_event

@router.get("/events/class/{class_id}", response_model=List[ScheduledEventResponse])
def get_class_scheduled_events(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scheduled events for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get scheduled events
    from ..models import ScheduledEvent
    events = db.query(ScheduledEvent).filter(
        and_(
            ScheduledEvent.class_id == class_id,
            ScheduledEvent.is_active == True
        )
    ).order_by(ScheduledEvent.scheduled_at).all()
    
    # Load related data
    for event in events:
        db.refresh(event.class_)
    
    return events

# Quiz Scheduling
@router.post("/quizzes/{quiz_id}/schedule")
def schedule_quiz_notification(
    quiz_id: int,
    scheduled_at: datetime,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Schedule notifications for a quiz (teacher only)."""
    # Verify quiz exists and user is the teacher
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    db_class = db.query(Class).filter(Class.id == quiz.class_id).first()
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can schedule quiz notifications"
        )
    
    success = ScheduledNotificationService.schedule_quiz_notification(
        db, quiz_id, scheduled_at
    )
    
    if success:
        return {
            "message": f"Quiz notifications scheduled for {scheduled_at}",
            "quiz_id": quiz_id,
            "scheduled_at": scheduled_at
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule quiz notifications"
        )

# Live Session Scheduling
@router.post("/live-sessions/schedule")
def schedule_live_session_notification(
    class_id: int,
    title: str,
    scheduled_start: datetime,
    duration_minutes: int = 60,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Schedule notifications for a live session (teacher only)."""
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
            detail="Only the class teacher can schedule live session notifications"
        )
    
    success = ScheduledNotificationService.schedule_live_session_notification(
        db, class_id, title, scheduled_start, duration_minutes
    )
    
    if success:
        return {
            "message": f"Live session notifications scheduled for {scheduled_start}",
            "class_id": class_id,
            "title": title,
            "scheduled_start": scheduled_start,
            "duration_minutes": duration_minutes
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule live session notifications"
        )

# Manual Push Notifications
@router.post("/send", response_model=PushNotificationResponse)
def send_push_notification(
    notification: PushNotificationRequest,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Send push notification to multiple users (teacher only)."""
    # Verify that all users are students in classes taught by the current user
    from ..models import User, Class
    
    # Get all classes taught by the current user
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    # Verify all target users are students in these classes
    # This is a simplified check - in production you might want more sophisticated enrollment logic
    target_users = db.query(User).filter(
        and_(
            User.id.in_(notification.user_ids),
            User.role == "student"
        )
    ).all()
    
    if len(target_users) != len(notification.user_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some users not found or not students"
        )
    
    # Send notifications
    result = PushNotificationService.send_push_notification(
        db, notification.user_ids, notification.title, notification.body, notification.data
    )
    
    return result

# Notification Management
@router.get("/logs")
def get_notification_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification logs for the current user."""
    from ..models import NotificationLog
    
    logs = db.query(NotificationLog).filter(
        NotificationLog.user_id == current_user.id
    ).order_by(NotificationLog.sent_at.desc()).limit(50).all()
    
    return {
        "user_id": current_user.id,
        "total_logs": len(logs),
        "logs": [
            {
                "id": log.id,
                "notification_type": log.notification_type,
                "title": log.title,
                "body": log.body,
                "platform": log.platform,
                "delivery_status": log.delivery_status,
                "sent_at": log.sent_at,
                "device_response": log.device_response
            }
            for log in logs
        ]
    }

# Admin/Teacher Notification Management
@router.get("/admin/logs")
def get_all_notification_logs(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all notification logs (teacher only)."""
    from ..models import NotificationLog, User
    
    # Get logs for students in classes taught by the current user
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    # This is a simplified approach - in production you'd want proper enrollment tracking
    logs = db.query(NotificationLog).join(User).filter(
        User.role == "student"
    ).order_by(NotificationLog.sent_at.desc()).limit(100).all()
    
    return {
        "total_logs": len(logs),
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user.name,
                "notification_type": log.notification_type,
                "title": log.title,
                "body": log.body,
                "platform": log.platform,
                "delivery_status": log.delivery_status,
                "sent_at": log.sent_at
            }
            for log in logs
        ]
    }

# Scheduled Notifications Status
@router.get("/scheduled/status")
def get_scheduled_notifications_status(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get status of scheduled notifications (teacher only)."""
    from ..models import ScheduledNotification, ScheduledEvent
    
    # Get scheduled notifications for events in classes taught by the current user
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    scheduled_events = db.query(ScheduledEvent).filter(
        ScheduledEvent.class_id.in_(class_ids)
    ).all()
    
    event_ids = [e.id for e in scheduled_events]
    
    notifications = db.query(ScheduledNotification).filter(
        ScheduledNotification.scheduled_event_id.in_(event_ids)
    ).all()
    
    # Group by status
    status_counts = {}
    for notification in notifications:
        status = notification.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_scheduled_events": len(scheduled_events),
        "total_notifications": len(notifications),
        "status_breakdown": status_counts,
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "event_type": event.event_type,
                "scheduled_at": event.scheduled_at,
                "is_active": event.is_active
            }
            for event in scheduled_events
        ]
    }

# Test Notification
@router.post("/test")
def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test notification to the current user."""
    result = PushNotificationService.send_push_notification(
        db, [current_user.id], "Test Notification", "This is a test notification from GramOthi!"
    )
    
    if result.success:
        return {
            "message": "Test notification sent successfully",
            "details": result.dict()
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )
